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
