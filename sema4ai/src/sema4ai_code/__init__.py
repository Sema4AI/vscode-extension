import os.path
import sys
from typing import List

__version__ = "2.12.5"
version_info: list[int] = [int(x) for x in __version__.split(".")]

__file__ = os.path.abspath(__file__)
if __file__.endswith((".pyc", ".pyo")):
    __file__ = __file__[:-1]


def get_extension_relative_path(*path: str) -> str:
    root_folder = os.path.dirname(get_src_folder())
    # i.e.: src_folder would be root_folder / src
    return os.path.join(root_folder, *path)


def get_src_folder() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_bin_folder() -> str:
    # Note: if we're installed in the site-packages, this could return
    # site-packages/bin.
    return get_extension_relative_path("bin")


def get_release_artifact_relative_path(sys_platform: str, executable_name: str) -> str:
    """
    Helper function for getting the release artifact relative path as defined in S3 bucket.

    Args:
        sys_platform: Platform for which the release artifact is being retrieved.
        executable_name: Name of the executable we want to get the path for.
    """
    import platform

    machine = platform.machine()
    is_64 = not machine or "64" in machine

    if sys_platform == "win32":
        if is_64:
            return f"windows64/{executable_name}.exe"
        else:
            return f"windows32/{executable_name}.exe"

    # This will come from release-sema4ai-sdk.yml workflow.
    elif sys_platform == "darwin-arm64":
        return f"macos-arm64/{executable_name}"

    elif sys_platform == "darwin":
        if machine == "arm64":
            return f"macos-arm64/{executable_name}"
        else:
            return f"macos64/{executable_name}"

    else:
        if is_64:
            return f"linux64/{executable_name}"
        else:
            return f"linux32/{executable_name}"


def import_robocorp_ls_core() -> None:
    """
    Helper function to make sure that sema4ai_ls_core is imported properly
    (either in dev or in release mode).
    """

    try:
        import sema4ai_ls_core
    except ImportError:
        log_contents = []
        use_folder = None
        try:
            src_folder = get_src_folder()
            log_contents.append(f"Source folder: {src_folder}")
            src_core_folder = os.path.abspath(
                os.path.join(src_folder, "..", "..", "sema4ai-python-ls-core", "src")
            )

            if os.path.isdir(src_core_folder):
                log_contents.append(f"Dev mode detected. Found: {src_core_folder}")
                use_folder = src_core_folder

            else:
                vendored_folder = os.path.join(src_folder, "sema4ai_code", "vendored")
                log_contents.append(f"Using vendored mode. Found: {vendored_folder}")
                use_folder = vendored_folder
                assert os.path.isdir(use_folder), (
                    f"Expected: {use_folder} to exist and be a directory."
                )

            sys.path.append(use_folder)
            import sema4ai_ls_core
        except:
            try:
                if use_folder:
                    log_contents.append(
                        f"{use_folder} contents:\n{os.listdir(use_folder)}"
                    )
            except:
                log_contents.append(f"Error in os.listdir('{use_folder}').")
            raise ImportError(
                "Error importing sema4ai_ls_core. Log: %s" % "\n".join(log_contents)
            )
