import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import IEndPoint, LaunchActionResult

log = get_logger(__name__)


class Tool(Enum):
    RCC = "rcc"
    ACTION_SERVER = "action-server"
    AGENT_CLI = "agent-cli"


@dataclass
class ToolInfo:
    mutex_name: str
    base_url: str
    executable_name: str
    version_command: tuple[str, ...]


_tool_info_map = {
    Tool.RCC: ToolInfo(
        mutex_name="robocorp_get_rcc",
        base_url="https://cdn.sema4.ai/rcc/releases",
        executable_name="rcc",
        version_command=("--version",),
    ),
    Tool.ACTION_SERVER: ToolInfo(
        mutex_name="sema4ai-get-action-server",
        base_url="https://cdn.sema4.ai/action-server/releases",
        executable_name="action-server",
        version_command=("version",),
    ),
    Tool.AGENT_CLI: ToolInfo(
        mutex_name="sema4ai-get-agent-cli",
        base_url="https://cdn.sema4.ai/agent-cli/releases",
        executable_name="agent-cli",
        version_command=("--version",),
    ),
}


def get_tool_info(tool: Tool) -> ToolInfo:
    return _tool_info_map[tool]


def get_tool_version(tool: Tool, location: str) -> LaunchActionResult:
    tool_info = get_tool_info(tool)
    version_command = tool_info.version_command

    from sema4ai_ls_core.process import launch

    return launch((location,) + version_command)


def verify_tool_downloaded_ok(
    tool: Tool, location: str, force: bool, make_run_check: bool, version: str
) -> bool:
    """
    Args:
        version: If `make_run_check` is True, the version is matched against the
            downloaded version (and if it doesn't match `False` will be returned).

    Returns:
        True if everything is ok and False otherwise.
    """
    if location in _checked_downloaded_tools and not force:
        if os.path.isfile(location):
            return True  # Already checked: just do simpler check.

    import time

    if not os.path.isfile(location):
        log.info(f"Tool {location} does not exist.")
        return False

    if not os.access(location, os.X_OK):
        log.info(f"Tool {location} is not executable.")
        return False

    # Actually execute it to make sure it works (in windows right after downloading
    # it may not be ready, so, retry a few times).
    if not make_run_check:
        _checked_downloaded_tools.add(location)
        return True
    else:
        times = 5
        timeout = 1
        for _ in range(times):
            version_result = get_tool_version(tool, location)
            if version_result.success:
                if (
                    version_result.result
                    and version_result.result.strip() == version.strip()
                ):
                    _checked_downloaded_tools.add(location)
                    return True
                else:
                    log.info(
                        f"The currently downloaded version of {location} ({version_result.result!r}) "
                        f"does not match the required version for the vscode extension: {version}"
                    )
                    return False
            time.sleep(timeout / times)
        log.info(
            f"Tool {location} failed to execute. Details: {version_result.message}"
        )

        return False


# Entries should be the location of the tools
_checked_downloaded_tools: set[str] = set()


def download_tool(
    tool: Tool,
    location: str,
    tool_version: str,
    force: bool = False,
    sys_platform: str | None = None,
    endpoint: IEndPoint | None = None,
) -> None:
    """
    Downloads the given Sema4.ai tool to the specified location. Note that it doesn't overwrite it if it
    already exists (unless force == True).

    Args:
        tool: The type of the tool to download. Available tools are specified with Tool enum.
        location: The location to store the tool executable in the filesystem.
        tool_version: version of the tool to download.
        force: Whether we should overwrite an existing installation. Defaults to False.
        sys_platform: The target platform of downloaded artifact. Defaults to None.
    """

    from contextlib import _GeneratorContextManager
    from pathlib import Path

    from sema4ai_ls_core.constants import NULL, Null
    from sema4ai_ls_core.http import download_with_resume
    from sema4ai_ls_core.progress_report import progress_context
    from sema4ai_ls_core.protocols import IProgressReporter
    from sema4ai_ls_core.system_mutex import timed_acquire_mutex

    if sys_platform is None:
        sys_platform = sys.platform

    if not force:
        if verify_tool_downloaded_ok(
            tool,
            location,
            force=force,
            make_run_check=sys_platform == sys.platform,
            version=tool_version,
        ):
            return

    tool_info = get_tool_info(tool)
    ctx: _GeneratorContextManager[IProgressReporter] | Null
    with timed_acquire_mutex(tool_info.mutex_name, timeout=300):
        # If other call was already in progress, we need to check it again,
        # as to not overwrite it when force was equal to False.
        if not force:
            if verify_tool_downloaded_ok(
                tool,
                location,
                force=force,
                make_run_check=sys_platform == sys.platform,
                version=tool_version,
            ):
                return

        if endpoint is not None:
            ctx = progress_context(
                endpoint, f"Download {tool.value}", dir_cache=None, cancellable=True
            )
        else:
            ctx = NULL

        from sema4ai_code import get_release_artifact_relative_path

        executable_name = tool_info.executable_name

        relative_path = get_release_artifact_relative_path(
            sys_platform, executable_name
        )

        url = f"{tool_info.base_url}/{tool_version}/{relative_path}"

        with ctx as progress_reporter:
            download_with_resume(
                url,
                Path(location),
                make_executable=True,
                progress_reporter=progress_reporter,
            )

        if not verify_tool_downloaded_ok(
            tool,
            location,
            force=True,
            make_run_check=sys_platform == sys.platform,
            version=tool_version,
        ):
            raise Exception(
                f"After downloading {tool!r} the verification failed (location: {location})!"
            )


def get_default_tool_location(tool: Tool) -> str:
    """
    Returns the default path for the given Tool to be located in.

    Args:
        tool: type of the tool.
        version: version of the tool we want to get the location for.
    """
    from sema4ai_code import get_extension_relative_path

    tool_info = get_tool_info(tool)
    executable_name = tool_info.executable_name

    executable_extension = ".exe" if sys.platform == "win32" else ""

    return get_extension_relative_path(
        "bin", f"{executable_name}{executable_extension}"
    )


def is_valid_semver_version(version: str) -> bool:
    import re

    SEMVER_REGEX = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
    )

    return SEMVER_REGEX.match(version) is not None
