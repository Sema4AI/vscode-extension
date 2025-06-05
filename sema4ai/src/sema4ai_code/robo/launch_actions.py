import os
import sys
from pathlib import Path


def create_and_rotate_directories(
    dir_path: str, prefix: str, max_count: int = 20
) -> str:
    """
    Creates directories named <number>-prefix in the given directory,
    maintaining a maximum count by removing the one with the lowest number
    when reaching the limit.

    Args:
        dir_path: Path to the directory where directories will be created.
        prefix: Prefix to add to the directory names.
        max_count: Maximum number of directories to maintain. Defaults to 20.
    """
    import threading
    from functools import partial

    # Get existing directory names
    existing_dirs = [
        entry.name
        for entry in os.scandir(dir_path)
        if entry.is_dir() and "-" in entry.name
    ]

    existing_numbers = []
    for d in existing_dirs:
        try:
            existing_numbers.append(int(d.split("-")[-1]))
        except ValueError:
            continue  # Ignore if not in the pattern we want
    existing_numbers.sort()

    next_number = 1
    if existing_numbers:
        next_number = existing_numbers[-1] + 1

    # Create the new directory with calculated number and prefix
    new_dir_name = f"{prefix}-{next_number}"
    new_dir_path = os.path.join(dir_path, new_dir_name)
    os.makedirs(new_dir_path, exist_ok=True)  # Create directory with parents if needed

    # Remove the oldest directories if exceeding max count
    if len(existing_dirs) >= max_count:
        t = threading.Thread(
            target=partial(_delete_old, dir_path, existing_dirs, max_count)
        )
        t.start()

    return new_dir_path


def on_rm_rf_error(func, path: str, exc, *, start_path: Path) -> bool:
    """Handles known read-only errors during rmtree.

    The returned value is used only by our own tests.
    """
    _exctype, excvalue = exc[:2]

    # another process removed the file in the middle of the "rm_rf" (xdist for example)
    # more context: https://github.com/pytest-dev/pytest/issues/5974#issuecomment-543799018
    if isinstance(excvalue, FileNotFoundError):
        return False

    if not isinstance(excvalue, PermissionError):
        return False

    if func not in (os.rmdir, os.remove, os.unlink):
        return False

    # Chmod + retry.
    import stat

    def chmod_rw(p: str) -> None:
        mode = os.stat(p).st_mode
        os.chmod(p, mode | stat.S_IRUSR | stat.S_IWUSR)

    # For files, we need to recursively go upwards in the directories to
    # ensure they all are also writable.
    p = Path(path)
    if p.is_file():
        for parent in p.parents:
            chmod_rw(str(parent))
            # stop when we reach the original path passed to rm_rf
            if parent == start_path:
                break
    chmod_rw(str(path))

    func(path)
    return True


def get_extended_length_path_str(path: str) -> str:
    """Converts to extended length path as a str"""
    long_path_prefix = "\\\\?\\"
    unc_long_path_prefix = "\\\\?\\UNC\\"
    if path.startswith((long_path_prefix, unc_long_path_prefix)):
        return path
    # UNC
    if path.startswith("\\\\"):
        return unc_long_path_prefix + path[2:]
    return long_path_prefix + path


def ensure_extended_length_path(path: Path) -> Path:
    """Get the extended-length version of a path (Windows).

    On Windows, by default, the maximum length of a path (MAX_PATH) is 260
    characters, and operations on paths longer than that fail. But it is possible
    to overcome this by converting the path to "extended-length" form before
    performing the operation:
    https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file#maximum-path-length-limitation

    On Windows, this function returns the extended-length absolute version of path.
    On other platforms it returns path unchanged.
    """
    if sys.platform.startswith("win32"):
        path = path.resolve()
        path = Path(get_extended_length_path_str(str(path)))
    return path


def rm_rf(path: Path) -> None:
    """Remove the path contents recursively, even if some elements
    are read-only.
    """
    import shutil
    from functools import partial

    path = ensure_extended_length_path(path)
    onerror = partial(on_rm_rf_error, start_path=path)
    shutil.rmtree(str(path), onerror=onerror)


def _delete_old(dir_path: str, existing_dirs: list[str], max_count: int):
    while len(existing_dirs) >= max_count:
        oldest = existing_dirs.pop(0)
        rm_rf(Path(dir_path) / oldest)


def create_pm():
    # The X-Action-Context header may be provided through an environment
    # variable when launching in VSCode (and it needs to be passed on
    # to sema4ai-actions).
    x_action_context = os.environ.get("SEMA4AI_VSCODE_X_ACTION_CONTEXT")
    if not x_action_context:
        return None

    try:
        from sema4ai.actions._customization._extension_points import EPManagedParameters
        from sema4ai.actions._customization._plugin_manager import PluginManager
        from sema4ai.actions._managed_parameters import ManagedParameters
        from sema4ai.actions._request import Request
    except ImportError:
        return None

    pm = PluginManager()
    pm.set_instance(
        EPManagedParameters,
        ManagedParameters(
            {
                "request": Request.model_validate(
                    {"headers": {"x-action-context": x_action_context}}
                )
            }
        ),
    )
    return pm


def main():
    from tempfile import gettempdir

    cli = None
    actions = None
    try:
        from sema4ai import actions
        from sema4ai.actions import cli  # noqa #type: ignore
    except ImportError:
        try:
            # Backward compatibility
            from robocorp.actions import cli  # noqa #type: ignore

        except ImportError:
            pass

        if cli is None:
            raise  # Raise the sema4ai.actions error

    dir_path = Path(gettempdir()) / "sema4ai-vscode-actions"
    dir_path.mkdir(parents=True, exist_ok=True)

    store_artifacts_at = create_and_rotate_directories(dir_path, "run-action", 20)
    os.environ.pop("ROBOT_ROOT", None)
    os.environ["ROBOT_ARTIFACTS"] = store_artifacts_at

    args = sys.argv[1:]
    if actions is not None:
        if actions.version_info >= [0, 7, 0]:
            # Only available on newer versions of sema4ai-actions.
            args.append("--print-result")

    print(
        f"Running with sema4ai.actions version: {'.'.join(str(x) for x in actions.version_info)}"
    )
    kwargs = {}
    if actions.version_info >= [0, 9, 0]:
        # Add managed arguments based on env variables.
        pm = create_pm()
        if pm is not None:
            kwargs["plugin_manager"] = pm

    return cli.main(args, exit=True, **kwargs)


if __name__ == "__main__":
    main()
