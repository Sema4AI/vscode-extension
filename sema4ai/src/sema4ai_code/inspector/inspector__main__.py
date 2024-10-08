import os.path
import sys
import traceback

__file__ = os.path.abspath(__file__)
if __file__.endswith((".pyc", ".pyo")):
    __file__ = __file__[:-1]

_critical_error_log_file = os.path.join(
    os.path.expanduser("~"), "inspector_critical.log"
)


def _stderr_reader(stream):
    from sema4ai_ls_core.core_log import get_logger

    log = get_logger(__name__)

    try:
        while True:
            line = stream.readline()
            if not line:
                break
            sys.stderr.buffer.write(line)
    except BaseException:
        log.exception("Error reading from inspector process stream.")
    finally:
        log.debug("Finished reading from inspector process stream.")


def start_server_process(args=(), python_exe=None, env=None):
    """
    Calls this __main__ in another process.

    :param args:
        The list of arguments for the server process.
        i.e.:
            ["-vv", "--log-file=%s" % log_file]
    """
    import subprocess
    import threading

    from sema4ai_ls_core.core_log import get_logger

    log = get_logger(__name__)

    if python_exe:
        if not os.path.exists(python_exe):
            raise RuntimeError(f"Expected {python_exe} to exist")

    args = [python_exe or sys.executable, "-u", __file__] + list(args)
    log.debug('Starting inspector process with args: "{}"'.format('" "'.join(args)))
    environ = os.environ.copy()
    environ.pop("PYTHONPATH", "")
    environ.pop("PYTHONHOME", "")
    environ.pop("VIRTUAL_ENV", "")
    if env is not None:
        for key, val in env.items():
            environ[key] = val

    environ["PYTHONIOENCODING"] = "utf-8"
    environ["PYTHONUNBUFFERED"] = "1"

    env_log = ["Environ:"]
    for key, val in environ.items():
        env_log.append(f"  {key}={val}")

    inspector_process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=environ,
        bufsize=0,
    )

    t = threading.Thread(target=_stderr_reader, args=(inspector_process.stderr,))
    t.name = f"Stderr from Inspector Server api ({args})"
    t.daemon = True
    t.start()

    return inspector_process


def main():
    log = None
    try:
        src_folder = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        try:
            import sema4ai_code
        except ImportError:
            # Automatically add it to the path if __main__ is being executed.
            assert os.path.exists(src_folder), f"Expected: {src_folder} to exist"
            sys.path.append(src_folder)
            import sema4ai_code  # @UnusedImport

        sema4ai_code.import_robocorp_ls_core()

        from sema4ai_ls_core.core_log import get_logger

        log = get_logger(__name__)

        log.info("Initializing Inspector Server api. Args: %s", (sys.argv[1:],))

        from sema4ai_code import __main__

        args = sys.argv[1:]

        from sema4ai_code.inspector.inspector_api import InspectorApi

        __main__.main(
            language_server_class=InspectorApi,
            args=args,
            log_prefix="inspector-api",
        )
    except BaseException:
        try:
            if log is not None:
                log.exception("Error initializing InspectorApi.")
        finally:
            # Critical error (the logging may not be set up properly).

            # Print to file and stderr.
            with open(_critical_error_log_file, "a+") as stream:
                traceback.print_exc(file=stream)

            traceback.print_exc()


if __name__ == "__main__":
    main()
