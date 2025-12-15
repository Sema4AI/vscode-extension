import os
import typing
import weakref
from pathlib import Path
from typing import Any

from sema4ai_ls_core import uris
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.jsonrpc.monitor import IMonitor
from sema4ai_ls_core.protocols import (
    ActionResult,
    ActionResultDict,
    IConfig,
    IConfigProvider,
    IEndPoint,
    IWorkspace,
    LaunchActionResult,
)

from sema4ai_code.tools import Tool

if typing.TYPE_CHECKING:
    from sema4ai_code.action_server import ActionServer

log = get_logger(__name__)

AGENT_CLI_VERSION = "v2.2.0"


def download_agent_cli(
    location: str,
    agent_cli_version=AGENT_CLI_VERSION,
    force: bool = False,
    sys_platform: str | None = None,
    endpoint: IEndPoint | None = None,
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
        endpoint=endpoint,
    )


def get_default_agent_cli_location() -> str:
    from sema4ai_code.tools import get_default_tool_location

    return get_default_tool_location(Tool.AGENT_CLI)


def get_agent_package_actions_sub_directory() -> str:
    """
    Returns the directory containing Agents' actions inside of an Agent Package.
    """

    return "actions"


class AgentCli:
    def __init__(self, config_provider: IConfigProvider, action_server: "ActionServer"):
        self._config_provider = weakref.ref(config_provider)
        self._action_server = action_server

    def _get_str_optional_setting(self, setting_name) -> Any:
        config_provider = self._config_provider()
        config: IConfig | None = None
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
        agent_cli_location = get_default_agent_cli_location()

        if download_if_missing and not os.path.exists(agent_cli_location):
            download_agent_cli(agent_cli_location)

        return agent_cli_location

    def _run_agent_cli_command(
        self,
        args: list[str],
        timeout: float = 35,
        env: dict[str, str] | None = None,
        download_if_missing: bool = True,
    ) -> LaunchActionResult:
        """
        Returns an ActionResult where the result is the stdout of the executed Agent CLI command.

        Args:
            args: The list of arguments to be passed to the command.
            timeout: The timeout for running the command (in seconds).
        """
        from sema4ai_ls_core.process import launch

        agent_cli_location = self.get_agent_cli_location(
            download_if_missing=download_if_missing
        )

        if not os.path.exists(agent_cli_location):
            return LaunchActionResult(
                command_line="agent-cli --version",
                success=False,
                message="Agent CLI executable not found.",
            )

        return launch(args=[agent_cli_location] + args, timeout=timeout, env=env)

    def get_version(self, download_if_missing: bool = True) -> ActionResult[str]:
        """
        Returns the version of Agent CLI executable.
        """
        command_result = self._run_agent_cli_command(
            ["--version"], download_if_missing=download_if_missing
        )

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        return ActionResult(success=True, message=None, result=command_result.result)

    def create_agent_package(self, directory: str, name: str) -> ActionResult[str]:
        """
        Create a new Agent package under given directory.

        Args:
            directory: The directory to create the Agent package in.
            name: string, the name of the agent package.
        """
        args = ["project", "new", "--path", directory]

        # FOR SUPPORT: agent-cli project new
        command_result = self._run_agent_cli_command(args)

        if not command_result.success:
            return ActionResult(
                success=False,
                message=f"Error creating Agent package.\n{command_result.message}",
            )

        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True
        package_path = f"{directory}/agent-spec.yaml"

        # Add prompted name to agent spec yaml
        with open(package_path) as stream:
            agent_spec = yaml.load(stream.read())

        agent_spec["agent-package"]["agents"][0]["name"] = name
        agent_spec["agent-package"]["agents"][0]["document-intelligence"] = "v2.1"

        with open(package_path, "w") as file:
            yaml.dump(agent_spec, file)

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
        # FOR SUPPORT: agent-cli package metadata
        # command_result = self._run_agent_cli_command(args)
        # if not command_result.success:
        #     return False, f"Error validating the agent package.\n{command_result.message}"

        agent_spec = uris.from_fs_path(str(Path(directory) / "agent-spec.yaml"))
        diagnostics = list(
            collect_agent_spec_diagnostics(workspace, agent_spec, monitor)
        )
        errors = [
            diag
            for diag in diagnostics
            if diag.get("severity") == DiagnosticSeverity.Error
        ]

        if errors:
            error_details = [
                f"Line {error['range']['start']['line'] + 1}: {error['message']}"
                for error in errors
            ]

            return False, f"Error validating the agent package:\n" + "\n".join(
                error_details
            )

        return True, ""

    def _get_env_for_agent_cli_with_action_server(self) -> dict[str, str]:
        action_server_location = self._action_server.get_action_server_location(
            download_if_missing=True
        )
        log.info(f"Action server location: {action_server_location}")

        env = os.environ.copy()
        # Environment variable for the action server location is needed for the agent cli.
        env["ACTION_SERVER_BIN_PATH"] = action_server_location
        return env

    def import_agent_package(
        self, agent_package_zip: str, target_dir: str, monitor: IMonitor
    ) -> ActionResult[str]:
        # Usage:
        # agent-cli package extract [flags]

        # Flags:
        # -h, --help                help for extract
        #     --output-dir string   Set the output directory. (default ".")
        #     --overwrite           The contents will be extracted to a non-empty directory
        #     --package string      The .zip file that should be extracted. (default "agent-package.zip")
        env = self._get_env_for_agent_cli_with_action_server()

        # FOR SUPPORT: agent-cli package extract
        command_result = self._run_agent_cli_command(
            [
                "package",
                "extract",
                "--output-dir",
                target_dir,
                "--overwrite",
                "--package",
                agent_package_zip,
            ],
            env=env,
        )
        return command_result

    def validate_agent_package(
        self, directory: str, workspace: IWorkspace, monitor: IMonitor
    ) -> ActionResultDict:
        valid, error_message = self._validate_agent_package(
            directory, workspace, monitor
        )
        if not valid:
            return ActionResult(success=False, message=error_message).as_dict()

        return ActionResult(success=True, message="").as_dict()

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

        env = self._get_env_for_agent_cli_with_action_server()

        # FOR SUPPORT: agent-cli package build
        # Packaging can take minutes so timeout set to 5min
        command_result = self._run_agent_cli_command(args, env=env, timeout=300)

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

    def get_docker_registries(self, directory: str) -> ActionResultDict:
        """
        Get the agent Docker registries for the given agent package directory.
        """
        args = [
            "externals",
            "docker",
            "get-registry",
            directory,
        ]
        command_result = self._run_agent_cli_command(args)
        if not command_result.success:
            return ActionResult(
                success=False,
                message=f"Error getting Docker registries.\n{command_result.message}",
            ).as_dict()

        return ActionResult(
            success=True,
            message=None,
            result=command_result.result,
        ).as_dict()
