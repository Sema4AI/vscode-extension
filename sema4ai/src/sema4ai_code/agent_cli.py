import os
import weakref
from pathlib import Path
from typing import Any, Optional

from sema4ai_ls_core import uris
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.jsonrpc.monitor import IMonitor
from sema4ai_ls_core.protocols import (
    ActionResultDict,
    IConfig,
    IConfigProvider,
    IWorkspace,
)

from sema4ai_code.protocols import ActionResult, AgentCliResult
from sema4ai_code.tools import Tool

log = get_logger(__name__)


def download_agent_cli(
    location: str,
    agent_cli_version="v0.0.9",
    force: bool = False,
    sys_platform: Optional[str] = None,
) -> None:
    """
    Downloads Agent CLI to the given location. Note that it doesn't overwrite it if it
    already exists (unless force == True).

    Args:
        location: The location to store the Agent CLI executable in the filesystem.
        agent_cli_version: version of the Agent CLI to download. Defaults to latest.
        force: Whether we should overwrite an existing installation.
        sys_platform: The target platform of downloaded artifact.
    """
    from sema4ai_code.tools import download_tool

    download_tool(
        Tool.AGENT_CLI,
        location,
        agent_cli_version,
        force=force,
        sys_platform=sys_platform,
    )


def get_default_agent_cli_location(version: str = "") -> str:
    from sema4ai_code.tools import get_default_tool_location

    return get_default_tool_location(Tool.AGENT_CLI, version)


def get_agent_package_actions_sub_directory() -> str:
    """
    Returns the directory containing Agents' actions inside of an Agent Package.
    """
    return "actions"


class AgentCli:
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

    def get_agent_cli_location(self, download_if_missing: bool = True) -> str:
        """
        Returns Agent CLI location as specified in extension's settings (if exists), falls back
        to relative "bin" directory otherwise.

        Args:
            download_if_missing: If true, it will attempt to download the Agent CLI if missing.
        """
        from sema4ai_code import settings

        agent_cli_location = self._get_str_optional_setting(
            settings.SEMA4AI_AGENT_CLI_LOCATION
        )

        if not agent_cli_location:
            agent_cli_location = get_default_agent_cli_location()

        if download_if_missing and not os.path.exists(agent_cli_location):
            download_agent_cli(agent_cli_location)

        return agent_cli_location

    def _run_agent_cli_command(
        self,
        args: list[str],
        timeout: float = 35,
    ) -> AgentCliResult:
        """
        Returns an ActionResult where the result is the stdout of the executed Agent CLI command.

        Args:
            args: The list of arguments to be passed to the command.
            timeout: The timeout for running the command (in seconds).
        """
        from subprocess import CalledProcessError, TimeoutExpired, list2cmdline, run

        from sema4ai_ls_core.basic import as_str, build_subprocess_kwargs

        agent_cli_location = self.get_agent_cli_location()

        kwargs = build_subprocess_kwargs(None, env=os.environ.copy())
        args = [agent_cli_location] + args
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

            return AgentCliResult(cmdline, success=False, message=error_message)

        except TimeoutExpired:
            error_message = f"Timed out ({timeout}s elapsed) when running: {cmdline}"
            log.exception(error_message)

            return AgentCliResult(cmdline, success=False, message=error_message)

        except Exception:
            error_message = f"Error running {cmdline}"
            log.exception(error_message)

            return AgentCliResult(cmdline, success=False, message=error_message)

        stdout_output = output.stdout.decode("utf-8", "replace")

        return AgentCliResult(cmdline, success=True, message=None, result=stdout_output)

    def get_version(self) -> ActionResult[str]:
        """
        Returns the version of Agent CLI executable.
        """
        command_result = self._run_agent_cli_command(["--version"])

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        return ActionResult(success=True, message=None, result=command_result.result)

    def create_agent_package(self, directory: str) -> ActionResult[str]:
        """
        Create a new Agent package under given directory.

        Args:
            directory: The directory to create the Agent package in.
        """
        args = ["project", "new", "--path", directory]
        command_result = self._run_agent_cli_command(args)

        if not command_result.success:
            return ActionResult(
                success=False,
                message=f"Error creating Agent package.\n{command_result.message}",
            )

        return ActionResult(success=True, message=None)

    @staticmethod
    def _validate_agent_package(
        directory: str, workspace: IWorkspace, monitor: IMonitor
    ) -> tuple[bool, str]:
        from sema4ai_ls_core.lsp import DiagnosticSeverity

        from sema4ai_code.agents.collect_agent_spec_diagnostics import (
            collect_agent_spec_diagnostics,
        )

        # [TODO] - uncomment this when the agent package validation is fixed
        # Validate the agent package
        # args = [
        #     "package",
        #     "metadata",
        #     "--package",
        #     directory,
        # ]
        # command_result = self._run_agent_cli_command(args)
        # if not command_result.success:
        #     return False, f"Error validating the agent package.\n{command_result.message}"

        agent_spec = uris.from_fs_path(str(Path(directory) / "agent-spec.yaml"))
        found = list(collect_agent_spec_diagnostics(workspace, agent_spec, monitor))

        if found:
            error_details = [
                f"Line {error['range']['start']['line'] + 1}: {error['message']}"
                for error in found
                if error.get("severity") == DiagnosticSeverity.Error
            ]

            return False, f"Error validating the agent package:\n" + "\n".join(
                error_details
            )

        return True, ""

    def pack_agent_package(
        self, directory: str, workspace: IWorkspace, monitor: IMonitor
    ) -> ActionResultDict:
        """
        Packs into a zip file the given agent package directory.

        Args:
            directory: The agent package directory to pack.
            workspace: The workspace to pack the agent package into.
            monitor: The monitor to report progress to.
        """

        valid, error_message = self._validate_agent_package(
            directory, workspace, monitor
        )
        if not valid:
            return ActionResult(success=False, message=error_message).as_dict()

        # Zip the agent package
        args = [
            "package",
            "build",
            "--overwrite",
            "--input-dir",
            directory,
            "--output-dir",
            directory,
        ]
        command_result = self._run_agent_cli_command(args)

        if not command_result.success:
            return ActionResult(
                success=False,
                message=f"Error packing the agent package.\n{command_result.message}",
            ).as_dict()

        return ActionResult(
            success=True,
            message=None,
            result=str(Path(directory) / "agent-package.zip"),
        ).as_dict()
