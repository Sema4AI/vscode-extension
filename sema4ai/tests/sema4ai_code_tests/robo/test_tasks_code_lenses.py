import os

import pytest
from sema4ai_code_tests.protocols import IRobocorpLanguageServerClient
from sema4ai_ls_core import uris
from sema4ai_ls_core.protocols import IWorkspace


def test_tasks_code_lenses(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path,
    initialization_options,
    data_regression,
):
    language_server = language_server_initialized
    path = os.path.join(ws_root_path, "my.py")
    uri = uris.from_fs_path(path)

    txt = """
from robocorp.tasks import task, task_cache

@task
def my_entry_point():
    pass
    
@task_cache
def cache_on_task():
    pass

"""
    language_server.open_doc(uri, 1, txt)

    ret = language_server.request_code_lens(uri)
    result = ret["result"]
    result = _fix_code_lenses(result, ws_root_path)
    data_regression.check(result)


@pytest.fixture
def workspace(ws_root_path) -> IWorkspace:
    from sema4ai_ls_core import watchdog_wrapper
    from sema4ai_ls_core.lsp import WorkspaceFolder
    from sema4ai_ls_core.protocols import IWorkspaceFolder
    from sema4ai_ls_core.workspace import Workspace

    root_uri = uris.from_fs_path(str(ws_root_path))
    workspace_folders: list[IWorkspaceFolder] = [
        WorkspaceFolder(root_uri, os.path.basename(str(ws_root_path)))
    ]
    extensions = (".py", ".txt", ".yaml")
    fs_observer = watchdog_wrapper.create_observer("dummy", extensions=extensions)

    ws = Workspace(
        root_uri, fs_observer, workspace_folders, track_file_extensions=extensions
    )
    return ws


def _fix_code_lenses(code_lenses: list | None, root):
    """
    Adjusts the file paths in the code lenses to be relative to the specified root directory.

    :param code_lenses: List of code lens dictionaries.
    :param root: The root directory to which paths should be made relative.
    :return: The modified list of code lenses with updated paths.
    """
    if code_lenses is None:
        code_lenses = []
    for lens in code_lenses:
        if "command" in lens and "arguments" in lens["command"]:
            for arg_list in lens["command"]["arguments"]:
                if isinstance(arg_list, list):
                    for i, arg in enumerate(arg_list):
                        if isinstance(arg, str) and os.path.isabs(arg):
                            # Make the path relative to the root
                            arg_list[i] = os.path.relpath(
                                os.path.normcase(arg), start=os.path.normcase(root)
                            )
                elif isinstance(arg_list, dict):
                    if "uri" in arg_list:
                        arg_list["uri"] = os.path.basename(arg_list["uri"])

                    if "robot" in arg_list:
                        if "filePath" in arg_list["robot"]:
                            arg_list["robot"]["filePath"] = os.path.basename(
                                arg_list["robot"]["filePath"]
                            )

                        if "directory" in arg_list["robot"]:
                            arg_list["robot"]["directory"] = os.path.basename(
                                arg_list["robot"]["directory"]
                            )
    return code_lenses


@pytest.mark.parametrize(
    "scenario",
    [
        "simple",
        "no_import",
        "actions",
    ],
)
def test_call_compute_code_lenses_directly(
    ws_root_path, workspace, config_provider, data_regression, scenario
) -> None:
    """
    This is to test that compute_code_lenses can be called directly.
    """
    from pathlib import Path

    from sema4ai_ls_core.jsonrpc.monitor import Monitor

    from sema4ai_code.robo.launch_code_lens import compute_code_lenses

    root = Path(ws_root_path)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "my.py"
    uri = uris.from_fs_path(str(path))

    if scenario == "simple":
        txt = """
from robocorp.tasks import task

@task
def my_entry_point():
    pass
    """
    elif scenario == "actions":
        txt = """
from sema4ai.actions import action
@action
def my_entry_point():
    pass
    """

        # We must have a package.yaml file in the root directory for actions to be searched for.
        (root / "package.yaml").write_text("")

    elif scenario == "no_import":
        txt = """
@task
def my_entry_point():
    pass
    """
    path.write_text(txt)

    func = compute_code_lenses(workspace, config_provider, uri)
    assert func is not None
    ret = func(monitor=Monitor())

    ret = _fix_code_lenses(ret, root)
    data_regression.check(ret, basename=f"run_task_{scenario}")
