"""
Helper main which starts a server which listens in a socket.

This makes it easier to start it under a debugger.

The extension must have the "robot.language-server.tcp-port" setting set to 1456.
"""
import sys


def dev_main():
    import os.path

    try:
        import example_vscode
    except ImportError:
        # Automatically add it to the path if __main__ is being executed.
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import example_vscode  # @UnusedImport
    example_vscode.import_robocorp_ls_core()

    from example_vscode.__main__ import main

    sys.argv = [
        sys.argv[0],
        "-vv",
        "--tcp",
        "--port=1456",
        # "--log-file=c:/temp/robotlog.log",
    ]

    main()


if __name__ == "__main__":
    while True:
        print("--- Starting new dev session ---")
        dev_main()
