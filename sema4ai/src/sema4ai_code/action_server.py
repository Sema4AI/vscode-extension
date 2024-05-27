import sys
import os
from typing import Optional
from sema4ai_ls_core.core_log import get_logger
from sema4ai_code.protocols import (
    ActionResult,
    ActionServerResult,
    ActionTemplate,
)

log = get_logger(__name__)


def download_action_server(
    location: str,
    force: bool = False,
    sys_platform: Optional[str] = None,
    action_server_version="0.11.0",
) -> None:
    """
    Downloads Action Server to the given location. Note that we don't overwrite it if it
    already exists (unless force == True).

    Args:
        location: The location to store the Action Server executable in the filesystem.
        force: Whether we should overwrite an existing installation.
        sys_platform: The target platform of downloaded artifact.
        action_server_version: version of the Action Server to download. Defaults to latest.
    """
    from sema4ai_ls_core.system_mutex import timed_acquire_mutex

    if sys_platform is None:
        sys_platform = sys.platform

    if not os.path.exists(location) or force:
        with timed_acquire_mutex("sema4ai-get-action-server", timeout=120):
            # if other call is already in progress, we need to check it again,
            # as to not overwrite it when force was equal to False.
            if not os.path.exists(location) or force:
                import urllib.request
                from sema4ai_code import get_release_artifact_relative_path

                relative_path = get_release_artifact_relative_path(
                    sys_platform, "action-server"
                )

                prefix = f"https://downloads.robocorp.com/action-server/releases/{action_server_version}"
                url = prefix + relative_path

                log.info(f"Downloading Action Server from: {url} to: {location}.")

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


def get_default_action_server_location(version: str = "") -> str:
    from sema4ai_code import get_extension_relative_path

    version_suffix = f"-{version}" if version else ""

    if sys.platform == "win32":
        return get_extension_relative_path("bin", f"action-server{version_suffix}.exe")
    else:
        return get_extension_relative_path("bin", f"action-server{version_suffix}")


class ActionServer:
    def __init__(self, action_server_location: str):
        self._action_server_location = action_server_location

    def _run_action_server_command(
        self,
        args: list[str],
        timeout: float = 35,
    ) -> ActionServerResult:
        """
        Returns an ActionResult where the result is the stdout of the executed Action Server command.

        Note that by design, we let the extension client handle the location (or eventual download) of
        the Action Server executable, therefore we want to avoid downloading the binary as a side effect.
        Hence, we require action_server_location as an argument to the __init__ function.

        Args:
            args: The list of arguments to be passed to the command.
            timeout: The timeout for running the command (in seconds).
        """
        from subprocess import list2cmdline, run, CalledProcessError, TimeoutExpired
        from sema4ai_ls_core.basic import as_str

        args = [self._action_server_location] + args
        cmdline = list2cmdline([str(x) for x in args])

        try:
            output = run(args, timeout=timeout, check=True, capture_output=True)
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
        Returns the version of used Action Server executable.
        """
        command_result = self._run_action_server_command(["version"])

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        return ActionResult(success=True, message=None, result=command_result.result)

    def get_action_templates(self) -> ActionResult[list[ActionTemplate]]:
        """
        Returns the list of available Action templates.
        """
        import json

        command_result = self._run_action_server_command(
            ["new", "list-templates", "--json"]
        )

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        if command_result.result is None:
            return ActionResult(success=False, message="Output not available")

        try:
            json_data: list[dict[str, str]] = json.loads(command_result.result)
        except json.decoder.JSONDecodeError as e:
            return ActionResult(success=False, message=f"Invalid output format: {e}")

        templates: list[ActionTemplate] = []

        for template in json_data:
            templates.append(
                ActionTemplate(
                    name=template["name"], description=template["description"]
                )
            )

        return ActionResult(success=True, message=None, result=templates)

    def create_action_package(
        self, directory: str, template: Optional[str]
    ) -> ActionResult:
        """
        Creates a new Action package under given directory, using specified template.

        Args:
            directory: The directory to create the Action package in.
            template: The template to use for the new Action package.
        """

        def get_error_message(result_message: str) -> str:
            return f"Error creating Action package.\n{result_message}"

        version_result = self.get_version()
        if not version_result.result:
            return ActionResult(
                success=False,
                message=get_error_message(
                    "Action Server version could not be determined."
                ),
            )

        version_tuple = tuple(
            int(x) for x in version_result.result.strip().split(".")[:2]
        )

        # Action Server < v10 does not support templates handling, therefore we skip the parameter.
        if version_tuple <= (0, 10):
            args = ["new", f"--name={directory}"]
        else:
            args = ["new", f"--name={directory}", f"--template={template}"]

        command_result = self._run_action_server_command(args)

        if command_result.success:
            return ActionResult(success=True, message=None)
        else:
            return ActionResult(
                success=False, message=get_error_message(command_result.message or "")
            )
