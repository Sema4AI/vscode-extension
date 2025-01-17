import pytest


@pytest.fixture
def small_vs_sleep():
    from sema4ai_ls_core.workspace import _VirtualFSThread

    original = _VirtualFSThread.SLEEP_AMONG_SCANS
    _VirtualFSThread.SLEEP_AMONG_SCANS = 0.05
    yield
    _VirtualFSThread.SLEEP_AMONG_SCANS = original


def test_workspace_and_uris(tmpdir):
    import os
    import sys

    from sema4ai_ls_core import uris
    from sema4ai_ls_core.lsp import TextDocumentItem
    from sema4ai_ls_core.watchdog_wrapper import create_observer
    from sema4ai_ls_core.workspace import Workspace

    ws_root_path = str(tmpdir)
    root_uri = uris.from_fs_path(ws_root_path)
    ws = Workspace(
        root_uri,
        fs_observer=create_observer("dummy", ()),
        workspace_folders=[],
        track_file_extensions=(".py", ".txt"),
    )

    internal_my_uri = uris.from_fs_path(os.path.join(ws_root_path, "my.robot"))

    if sys.platform == "win32":

        def to_vscode_uri(initial_uri):
            assert initial_uri.startswith("file:///")
            # Make something as:
            # file:///c:/Users/f
            # into
            # file:///C%3A/Users/f
            # -- note: when normalized it's still the same
            uri = initial_uri[:8] + initial_uri[8].upper() + "%3A" + initial_uri[10:]
            assert uris.normalize_uri(uri) == initial_uri
            return uri

    else:

        def to_vscode_uri(uri):
            return uri

    uri_my = to_vscode_uri(internal_my_uri)
    text_document = TextDocumentItem(uri_my)
    doc = ws.put_document(text_document)
    assert ws.get_document(text_document.uri, accept_from_file=False) is doc
    assert (
        ws.get_document(uris.normalize_uri(text_document.uri), accept_from_file=False)
        is doc
    )


def test_workspace_memory_cache(tmpdir, small_vs_sleep) -> None:
    import os
    import typing

    from sema4ai_ls_core import uris, watchdog_wrapper
    from sema4ai_ls_core.basic import wait_for_condition
    from sema4ai_ls_core.lsp import WorkspaceFolder
    from sema4ai_ls_core.protocols import IWorkspaceFolder
    from sema4ai_ls_core.workspace import Workspace, _WorkspaceFolderWithVirtualFS

    root_uri = uris.from_fs_path(str(tmpdir))
    workspace_folders: list[IWorkspaceFolder] = [
        WorkspaceFolder(root_uri, os.path.basename(str(tmpdir)))
    ]
    fs_observer = watchdog_wrapper.create_observer(
        "watchdog", extensions=(".py", ".txt")
    )
    ws = Workspace(
        root_uri, fs_observer, workspace_folders, track_file_extensions=(".py", ".txt")
    )

    folders = list(ws.iter_folders())
    assert len(folders) == 1
    folder = typing.cast(_WorkspaceFolderWithVirtualFS, folders[0])
    vs = folder._vs

    wait_for_condition(
        lambda: list(ws.iter_all_doc_uris_in_workspace((".py", ".txt"))) == []
    )
    # If the change is too fast the mtime may end up being the same...

    f = tmpdir.join("my.txt")
    f.write_text("foo", "utf-8")

    wait_for_condition(
        lambda: list(ws.iter_all_doc_uris_in_workspace((".py", ".txt")))
        == [uris.from_fs_path(str(f))]
    )

    dir1 = tmpdir.join("dir1")
    dir1.mkdir()

    f2 = dir1.join("my.py")
    f2.write_text("foo", "utf-8")

    wait_for_condition(
        lambda: set(ws.iter_all_doc_uris_in_workspace((".py", ".txt")))
        == {uris.from_fs_path(str(f)), uris.from_fs_path(str(f2))}
    )

    wait_for_condition(
        lambda: set(ws.iter_all_doc_uris_in_workspace((".py", ".txt")))
        == {uris.from_fs_path(str(f)), uris.from_fs_path(str(f2))}
    )

    # If the change is too fast the mtime may end up being the same...
    f2.remove()

    wait_for_condition(
        lambda: set(ws.iter_all_doc_uris_in_workspace((".py", ".txt")))
        == {uris.from_fs_path(str(f))}
    )

    wait_for_condition(
        lambda: set(ws.iter_all_doc_uris_in_workspace((".py", ".txt")))
        == {uris.from_fs_path(str(f))}
    )

    ws.remove_folder(root_uri)
    assert set(ws.iter_all_doc_uris_in_workspace((".py", ".txt"))) == set()
    vs._virtual_fsthread.join(0.5)
    assert not vs._virtual_fsthread.is_alive()
