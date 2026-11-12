import os
import sys

import pytest


def test_playwright_available(tmpdir):
    from sema4ai_code._language_server_playwright import _is_playwright_available

    tmpdir.join("playwright").mkdir().join("__init__.py").write_text("", "utf-8")

    assert _is_playwright_available(
        sys.executable, {"PYTHONPATH": str(tmpdir)}, str(tmpdir)
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Uses a shell script as python.")
def test_playwright_not_available(tmpdir):
    from sema4ai_code._language_server_playwright import _is_playwright_available

    # A python without site-packages (so, `playwright` can't be there).
    python_exe = tmpdir.join("python_no_site")
    python_exe.write_text(f'#!/bin/sh\nexec "{sys.executable}" -S -E "$@"\n', "utf-8")
    os.chmod(str(python_exe), 0o755)

    assert not _is_playwright_available(str(python_exe), {}, str(tmpdir))


def test_playwright_check_not_possible(tmpdir):
    from sema4ai_code._language_server_playwright import _is_playwright_available

    # If the check can't be done the launch should proceed (and report its own errors).
    assert _is_playwright_available(
        str(tmpdir.join("python_does_not_exist")), {}, str(tmpdir)
    )


@pytest.mark.parametrize(
    "returncode, expected",
    [
        (0, True),
        (3, False),
        # Only the exit code of the check means that it's not available: on
        # anything else the launch should proceed (and report its own errors).
        (1, True),
        (-9, True),
    ],
)
def test_playwright_available_returncodes(tmpdir, monkeypatch, returncode, expected):
    import subprocess
    from unittest import mock

    from sema4ai_code._language_server_playwright import _is_playwright_available

    run = mock.Mock(return_value=mock.Mock(returncode=returncode))
    monkeypatch.setattr(subprocess, "run", run)

    assert _is_playwright_available("python", {}, str(tmpdir)) == expected
    run.assert_called_once()


def test_playwright_check_timeout(tmpdir, monkeypatch):
    import subprocess
    from unittest import mock

    from sema4ai_code._language_server_playwright import _is_playwright_available

    run = mock.Mock(side_effect=subprocess.TimeoutExpired("python", 30))
    monkeypatch.setattr(subprocess, "run", run)

    assert _is_playwright_available("python", {}, str(tmpdir))
    run.assert_called_once()


def _create_playwright_with_interpreter(python_exe: str, environ: dict):
    from unittest import mock

    from sema4ai_code._language_server_playwright import _Playwright

    interpreter_info = mock.Mock()
    interpreter_info.get_python_exe.return_value = python_exe
    interpreter_info.get_environ.return_value = environ

    ep = mock.Mock()
    ep.get_interpreter_info_for_doc_uri.return_value = interpreter_info

    plugin_manager = mock.Mock()
    plugin_manager.get_implementations.return_value = [ep]

    playwright = _Playwright(mock.Mock(), mock.Mock(), plugin_manager, mock.Mock())
    playwright._launch_playwright_recorder = mock.Mock()  # type: ignore[method-assign]
    return playwright


def test_recorder_not_launched_without_playwright(tmpdir, monkeypatch):
    from sema4ai_ls_core import uris

    from sema4ai_code import _language_server_playwright
    from sema4ai_code._language_server_playwright import (
        PLAYWRIGHT_NOT_AVAILABLE_MESSAGE,
    )

    monkeypatch.setattr(
        _language_server_playwright, "_is_playwright_available", lambda *args: False
    )
    playwright = _create_playwright_with_interpreter("python", {"SOME_VAR": "1"})

    result = playwright._threaded_playwright_recorder(
        uris.from_fs_path(str(tmpdir.join("robot.yaml")))
    )

    assert result == {
        "success": False,
        "message": PLAYWRIGHT_NOT_AVAILABLE_MESSAGE,
        "result": None,
    }
    playwright._launch_playwright_recorder.assert_not_called()


def test_recorder_launched_with_playwright(tmpdir, monkeypatch):
    from sema4ai_ls_core import uris

    from sema4ai_code import _language_server_playwright

    check_args = []

    def is_playwright_available(*args):
        check_args.append(args)
        return True

    monkeypatch.setattr(
        _language_server_playwright,
        "_is_playwright_available",
        is_playwright_available,
    )
    environ = {"SOME_VAR": "1"}
    playwright = _create_playwright_with_interpreter("python", environ)

    robot_yaml_uri = uris.from_fs_path(str(tmpdir.join("robot.yaml")))
    # Note: on Windows the drive letter is lowercased when converting from the uri.
    cwd = os.path.dirname(uris.to_fs_path(robot_yaml_uri))

    result = playwright._threaded_playwright_recorder(robot_yaml_uri)

    assert result == {"success": True, "message": None, "result": None}
    assert check_args == [("python", environ, cwd)]
    playwright._launch_playwright_recorder.assert_called_once_with(
        "python", environ, cwd=cwd
    )
