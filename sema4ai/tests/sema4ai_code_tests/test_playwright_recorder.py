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
