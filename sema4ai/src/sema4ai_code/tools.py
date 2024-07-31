import sys
import os
from enum import Enum
from typing import Optional

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


class Tool(Enum):
    RCC = "rcc"
    ACTION_SERVER = "action-server"
    AGENT_CLI = "agent-cli"


TOOL_MUTEX_MAP = {
    Tool.RCC: "robocorp_get_rcc",
    Tool.ACTION_SERVER: "sema4ai-get-action-server",
    Tool.AGENT_CLI: "sema4ai-get-agent-cli",
}


TOOL_BASE_URL_MAP = {
    Tool.RCC: "https://cdn.sema4.ai/rcc/releases",
    Tool.ACTION_SERVER: "https://cdn.sema4.ai/action-server/releases",
    Tool.AGENT_CLI: "https://cdn.sema4.ai/agent-cli/releases",
}


TOOL_EXECUTABLE_NAME_MAP = {
    Tool.RCC: "rcc",
    Tool.ACTION_SERVER: "action-server",
    Tool.AGENT_CLI: "agent-cli",
}


def download_tool(
    tool: Tool,
    location: str,
    tool_version: str,
    force: bool = False,
    sys_platform: Optional[str] = None,
) -> None:
    """
    Downloads Given Sema4.ai tool to specified location. Note that it doesn't overwrite it if it
    already exists (unless force == True).

    Args:
        tool: The type of the tool to download. Available tools are specified with Tool enum.
        location: The location to store the tool executable in the filesystem.
        tool_version: version of the tool to download.
        force: Whether we should overwrite an existing installation. Defaults to False.
        sys_platform: The target platform of downloaded artifact. Defaults to None.
    """

    from sema4ai_ls_core.system_mutex import timed_acquire_mutex

    if sys_platform is None:
        sys_platform = sys.platform

    if os.path.exists(location) and not force:
        return

    with timed_acquire_mutex(TOOL_MUTEX_MAP[tool], timeout=120):
        # if other call is already in progress, we need to check it again,
        # as to not overwrite it when force was equal to False.
        if os.path.exists(location) and not force:
            return

        import urllib.request
        from sema4ai_code import get_release_artifact_relative_path

        executable_name = TOOL_EXECUTABLE_NAME_MAP[tool]

        relative_path = get_release_artifact_relative_path(
            sys_platform, executable_name
        )

        url = f"{TOOL_BASE_URL_MAP[tool]}/{tool_version}/{relative_path}"

        log.info(f"Downloading tool: '{executable_name}' from: {url} to: {location}.")

        # Cloudflare seems to be blocking "User-Agent: Python-urllib/3.9".
        # Use a different one as that must be sorted out.
        response = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla"})
        )

        # Put it all in memory before writing (i.e. just write it if
        # we know we downloaded everything).
        data = response.read()

        try:
            os.makedirs(os.path.dirname(location))
        except Exception:
            pass  # Error expected if the parent dir already exists.

        try:
            with open(location, "wb") as stream:
                stream.write(data)
            os.chmod(location, 0x744)
        except Exception:
            log.exception(
                "Error writing to: %s.\nParent dir exists: %s",
                location,
                os.path.dirname(location),
            )
            raise


def get_default_tool_location(tool: Tool, version: str = "") -> str:
    """
    Returns the default path for the given Tool to be located in.

    Args:
        tool: type of the tool.
        version: version of the tool we want to get the location for.
    """
    from sema4ai_code import get_extension_relative_path

    executable_name = TOOL_EXECUTABLE_NAME_MAP[tool]

    version_suffix = f"-{version}" if version else ""
    executable_extension = ".exe" if sys.platform == "win32" else ""

    return get_extension_relative_path(
        "bin", f"{executable_name}{version_suffix}{executable_extension}"
    )
