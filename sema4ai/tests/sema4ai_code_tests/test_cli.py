def call(args):
    import subprocess

    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Error. Output: {e.output}")


def test_cli_help(main_module):
    import sys

    output = call([sys.executable, main_module.__file__, "--help"])
    output = output.decode("utf-8")
    assert "Traceback" not in output
    assert "Python Language Server" not in output
    assert "Sema4.ai" in output


def test_cli_version(main_module):
    import sys

    from sema4ai_code import __version__

    output = call([sys.executable, main_module.__file__, "--version"])
    output = output.decode("utf-8")
    assert output == __version__


def test_cli_critical_error_log(main_module, tmp_path):
    import os
    import subprocess
    import sys

    # Make the language server fail after startup, outside of its own error handling.
    script = """
import runpy
import sys

import sema4ai_code

sema4ai_code.import_robocorp_ls_core()

from sema4ai_ls_core import python_ls


def fail(*args, **kwargs):
    raise RuntimeError("Simulated language server failure")


python_ls.start_io_lang_server = fail
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
    env = os.environ.copy()
    # expanduser("~") uses HOME on Linux and macOS, USERPROFILE on Windows.
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    subprocess.run(
        [sys.executable, "-c", script, main_module.__file__],
        env=env,
        capture_output=True,
        timeout=120,
    )

    critical_log = tmp_path / "sema4ai_code_critical.log"
    assert critical_log.exists(), os.listdir(tmp_path)
    assert "Simulated language server failure" in critical_log.read_text()
    assert not (tmp_path / "robocorp_code_critical.log").exists()
