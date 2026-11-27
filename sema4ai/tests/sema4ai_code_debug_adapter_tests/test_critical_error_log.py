def test_dap_critical_error_log(tmp_path):
    import os
    import subprocess
    import sys

    from sema4ai_code_debug_adapter import __main__ as dap_main

    # Make the debug adapter fail during startup.
    script = """
import runpy
import sys

import sema4ai_code


def fail(*args, **kwargs):
    raise RuntimeError("Simulated debug adapter failure")


sema4ai_code.import_robocorp_ls_core = fail
runpy.run_path(sys.argv[1], run_name="__main__")
"""
    env = os.environ.copy()
    # expanduser("~") uses HOME on Linux and macOS, USERPROFILE on Windows.
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    subprocess.run(
        [sys.executable, "-c", script, dap_main.__file__],
        env=env,
        capture_output=True,
        timeout=120,
    )

    critical_log = tmp_path / "sema4ai_code_dap_critical.log"
    assert critical_log.exists(), os.listdir(tmp_path)
    assert "Simulated debug adapter failure" in critical_log.read_text()
    assert not (tmp_path / "robocorp_code_dap_critical.log").exists()
