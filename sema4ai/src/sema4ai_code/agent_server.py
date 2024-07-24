import os
import sys
import json
import weakref
from typing import Optional, Any

from sema4ai_ls_core.core_log import get_logger
from sema4ai_code.tools import Tool

from sema4ai_ls_core.protocols import (
    IConfig,
    IConfigProvider,
)

from sema4ai_code.protocols import (
    ActionResult,
    ActionServerListOrgsResultDict,
    ActionServerPackageBuildResultDict,
    ActionServerPackageUploadStatusDict,
    ActionServerResult,
    ActionServerVerifyLoginResultDict,
    ActionTemplate,
)

log = get_logger(__name__)


def download_agent_server(
    location: str,
    agent_server_version="v0.0.5",
    force: bool = False,
    sys_platform: Optional[str] = None,
) -> None:
    """
    Downloads Agent Server to the given location. Note that it doesn't overwrite it if it
    already exists (unless force == True).

    Args:
        location: The location to store the Agent Server executable in the filesystem.
        agent_server_version: version of the Agent Server to download. Defaults to latest.
        force: Whether we should overwrite an existing installation.
        sys_platform: The target platform of downloaded artifact.
    """
    from sema4ai_code.tools import download_tool

    download_tool(
        Tool.AGENT_SERVER,
        location,
        agent_server_version,
        force=force,
        sys_platform=sys_platform,
    )


def get_default_agent_server_location(version: str = "") -> str:
    from sema4ai_code.tools import get_default_tool_location

    return get_default_tool_location(Tool.AGENT_SERVER, version)


class AgentServer:
    def __init__(self, config_provider: IConfigProvider):
        self._config_provider = weakref.ref(config_provider)

    def _get_str_optional_setting(self, setting_name) -> Any:
        config_provider = self._config_provider()
        config: Optional[IConfig] = None
        if config_provider is not None:
            config = config_provider.config

        if config:
            return config.get_setting(setting_name, str, None)
        return None

    def get_agent_server_location(self, download_if_missing: bool = False) -> str:
        """
        Returns Agent Server location as specified in extension's settings (if exists), falls back
        to relative "bin" directory otherwise.

        Args:
            download_if_missing: If true, it will attempt to download the Agent Server if missing.
        """
        from sema4ai_code import settings

        agent_server_location = self._get_str_optional_setting(
            settings.SEMA4AI_AGENT_SERVER_LOCATION
        )

        if not agent_server_location:
            agent_server_location = get_default_agent_server_location()

        if download_if_missing and not os.path.exists(agent_server_location):
            download_agent_server(agent_server_location)

        return agent_server_location

    def _run_agent_server_command(
        self,
        args: list[str],
        timeout: float = 35,
    ) -> ActionServerResult:
        """
        Returns an ActionResult where the result is the stdout of the executed Agent Server command.

        Args:
            args: The list of arguments to be passed to the command.
            timeout: The timeout for running the command (in seconds).
        """
        from subprocess import CalledProcessError, TimeoutExpired, list2cmdline, run

        from sema4ai_ls_core.basic import as_str, build_subprocess_kwargs

        agent_server_location = self.get_agent_server_location()

        kwargs = build_subprocess_kwargs(None, env=os.environ.copy())
        args = [agent_server_location] + args
        cmdline = list2cmdline([str(x) for x in args])

        # Not sure why, but (just when running in VSCode) something as:
        # launching sys.executable actually got stuck unless a \n was written
        # (even if stdin was closed it wasn't enough).
        # -- note: this issue seems to be particular to Windows
        # (VSCode + Windows Defender + python).
        input_data = "\n".encode("utf-8")

        try:
            output = run(
                args,
                timeout=timeout,
                check=True,
                capture_output=True,
                input=input_data,
                **kwargs,
            )
        except CalledProcessError as e:
            stdout = as_str(e.stdout)
            stderr = as_str(e.stderr)

            error_message = (
                f"Error running: {cmdline}\n\nStdout: {stdout}\nStderr: {stderr}"
            )

            log.exception(error_message)

            return ActionServerResult(cmdline, success=False, message=error_message)

        except TimeoutExpired:
            error_message = f"Timed out ({timeout}s elapsed) when running: {cmdline}"
            log.exception(error_message)

            return ActionServerResult(cmdline, success=False, message=error_message)

        except Exception:
            error_message = f"Error running {cmdline}"
            log.exception(error_message)

            return ActionServerResult(cmdline, success=False, message=error_message)

        stdout_output = output.stdout.decode("utf-8", "replace")

        return ActionServerResult(
            cmdline, success=True, message=None, result=stdout_output
        )

    def get_version(self) -> ActionResult[str]:
        """
        Returns the version of Agent Server executable.
        """
        command_result = self._run_agent_server_command(["--version"])

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        return ActionResult(success=True, message=None, result=command_result.result)
