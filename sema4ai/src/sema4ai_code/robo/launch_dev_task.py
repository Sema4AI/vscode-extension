import sys


def main() -> int:
    import json
    import os
    import shlex
    import subprocess

    try:
        run_dev_tasks_str = os.environ["SEMA4AI_RUN_DEV_TASKS"]
    except Exception:
        print(
            "Error: tasks to launch not defined in SEMA4AI_RUN_DEV_TASKS environment variable.",
            file=sys.stderr,
        )
        return 1
    try:
        run_dev_tasks = json.loads(run_dev_tasks_str)
    except Exception:
        print(
            "Error: contents of SEMA4AI_RUN_DEV_TASKS environment variable not a valid json.",
            file=sys.stderr,
        )
        return 1

    assert isinstance(run_dev_tasks, list)

    for dev_task in run_dev_tasks:
        print(f"\nRunning command: {shlex.join(dev_task)}")
        print("=" * 120)
        popen = subprocess.Popen([dev_task[0]] + dev_task[1:], shell=False)
        popen.wait()

        if popen.returncode != 0:
            print(
                f"\nFailed running dev-task: `{shlex.join(dev_task)}` (return code: {popen.returncode}).",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
