"""
Helper main which starts a server which listens in a socket.

This makes it easier to start it under a debugger.

The extension must have the "sema4ai.language-server.tcp-port" setting set to 1456.
"""

import sys


def dev_main():
    import os.path

    try:
        import sema4ai_code
    except ImportError:
        # Automatically add it to the path if __main__ is being executed.
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import sema4ai_code  # @UnusedImport
    sema4ai_code.import_robocorp_ls_core()

    from sema4ai_code.__main__ import main

    sys.argv = [
        sys.argv[0],
        "-vv",
        "--tcp",
        "--port=1457",
        # "--log-file=c:/temp/robotlog.log",
    ]

    main()


if __name__ == "__main__":
    while True:
        print("--- Starting new dev session ---")
        dev_main()
