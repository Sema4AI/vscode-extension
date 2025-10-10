import json
import os
import sys
import typing
import weakref
from concurrent.futures import Future
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.options import DEFAULT_TIMEOUT
from sema4ai_ls_core.protocols import (
    ActionResult,
    IConfig,
    IConfigProvider,
    IEndPoint,
    LaunchActionResult,
)

from sema4ai_code.protocols import (
    ActionServerPackageBuildInfo,
    ActionServerPackageUploadStatus,
    ActionServerVerifyLoginInfoDict,
    ActionTemplate,
)

log = get_logger(__name__)

ONE_MINUTE_S = 60
ACTION_SERVER_VERSION = "2.16.1"

if typing.TYPE_CHECKING:
    from sema4ai_code.vendored_deps.url_callback_server import LastRequestInfoTypedDict


class StatusTypedDict(TypedDict):
    scopes: list[str] | None
    expires_at: str  # iso-formatted datetime or empty string
    access_token: str | None  # Only available if not an automatic id
    metadata: dict | None  # Metadata which may be available


def is_debugger_active() -> bool:
    try:
        import pydevd  # type:ignore
    except ImportError:
        return False

    return bool(pydevd.get_global_debugger())


def is_port_free(port: int) -> bool:
    """
    Checks if a port is free (in localhost)

    Args:
        port: The port number to check.

    Returns:
        True if the port is free, False otherwise.
    """
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def download_action_server(
    location: str,
    action_server_version=ACTION_SERVER_VERSION,
    force: bool = False,
    sys_platform: str | None = None,
    endpoint: IEndPoint | None = None,
) -> None:
    """
    Downloads Action Server to the given location. Note that we don't overwrite it if it
    already exists (unless force == True).

    Args:
        location: The location to store the Action Server executable in the filesystem.
        action_server_version: Version of the Action Server to download. Defaults to latest.
        force: Whether we should overwrite an existing installation.
        sys_platform: The target platform of downloaded artifact.
    """
    from sema4ai_code.tools import Tool, download_tool

    download_tool(
        Tool.ACTION_SERVER,
        location,
        action_server_version,
        force=force,
        sys_platform=sys_platform,
        endpoint=endpoint,
    )


def get_default_action_server_location() -> str:
    from sema4ai_code.tools import Tool, get_default_tool_location

    return get_default_tool_location(Tool.ACTION_SERVER)


if typing.TYPE_CHECKING:
    from sema4ai_ls_core.process import Process


def get_default_sema4ai_home() -> Path:
    if sys.platform == "win32":
        path = r"$LOCALAPPDATA\sema4ai"
    else:
        path = r"$HOME/.sema4ai"
    robocorp_home_str = os.path.expandvars(path)
    return Path(robocorp_home_str)


def get_default_action_server_settings_dir() -> Path:
    return get_default_sema4ai_home() / "action-server"


class ActionServerAsService:
    """
    This class is meant to be used in the use-case where the action server
    is started as a service and then there's communication with it through
    http requests.
    """

    _process: Optional["Process"] = None

    def __init__(
        self,
        action_server_location: str,
        port: int,
        *,
        cwd: str,
        datadir: str = "",
        use_https: bool = False,
        ssl_self_signed: bool = False,
        ssl_keyfile: str = "",
        ssl_certfile: str = "",
    ):
        self._action_server_location = action_server_location
        self._port = port
        self._datadir = datadir
        self._cwd = cwd
        assert os.path.exists(cwd)

        self._use_https = use_https
        self._ssl_self_signed = ssl_self_signed
        self._ssl_keyfile = ssl_keyfile
        self._ssl_certfile = ssl_certfile

        protocol = "https" if use_https else "http"
        self._base_url = f"{protocol}://localhost:{port}"

    @property
    def base_url(self) -> str:
        return self._base_url

    def start_for_oauth2(self) -> None:
        if self._port != 0:
            if not is_port_free(self._port):
                raise RuntimeError(
                    f"Port: {self._port} is already in use. Please stop the service / action server in that port."
                )

        assert self._process is None, "A process is already started"

        from sema4ai_ls_core.process import Process

        args: list[str] = [
            self._action_server_location,
            "start",
            "--port",
            str(self._port),
        ]
        args.append(f"--parent-pid={os.getpid()}")

        args.append("--actions-sync=false")
        args.append(f"--datadir={self._datadir}")

        if self._use_https:
            args.append("--https")

        if self._ssl_self_signed:
            args.append("--ssl-self-signed")

        if self._ssl_keyfile:
            args.append(f"--ssl-keyfile={self._ssl_keyfile}")

        if self._ssl_certfile:
            args.append(f"--ssl-cerfile={self._ssl_certfile}")

        args.append("--kill-lock-holder")

        self._process = Process(args, cwd=self._cwd)
        self._process.on_stderr.register(self._on_stderr)
        self._process.on_stdout.register(self._on_stdout)
        self._process.start()

    def _urlopen_kwargs(self, **kwargs) -> dict:
        """
        Provides the default kwargs that should be used for a urlopen call.
        """
        # if is_debugger_active():
        #     kwargs["timeout"] = None

        if "timeout" not in kwargs:
            kwargs["timeout"] = DEFAULT_TIMEOUT

        if self._use_https:
            import ssl

            if self._ssl_certfile:
                cert_file_path = str(self._ssl_certfile)
            else:
                cert_file_path = str(
                    get_default_action_server_settings_dir()
                    / "action-server-public-certfile.pem"
                )

            if not os.path.exists(cert_file_path):
                raise RuntimeError(
                    f"Expected: {cert_file_path} to exist (it should've been created "
                    "when the action server is started with the option to use a self-signed certificate)."
                )
            from ssl import Purpose

            ctx = ssl.create_default_context(Purpose.SERVER_AUTH)
            ctx.load_verify_locations(cert_file_path)
            kwargs["context"] = ctx

        return kwargs

    def build_full_url(self, url: str) -> str:
        if url.startswith("/"):
            url = url[1:]
        return f"{self.base_url}/{url}"

    def get_str(
        self,
        url,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = DEFAULT_TIMEOUT,
    ):
        """Fetches the URL using urllib and handles basic request parameters.
        Note: requests is not a dependency so it cannot be used.

        Args:
          url: The URL to fetch.
          params: A dictionary of query parameters. (Optional)
          headers: A dictionary of headers to send with the request. (Optional)
          timeout: The timeout in seconds for the request. (Optional)
        """
        import time
        import urllib.parse
        import urllib.request
        from urllib.error import URLError

        url = self.build_full_url(url)
        # Build the full URL with query parameters
        if params:
            encoded_params = urllib.parse.urlencode(params)
            url = f"{url}?{encoded_params}"

        use_headers = {"User-Agent": "Mozilla"}
        if headers:
            use_headers.update(headers)
        kwargs = self._urlopen_kwargs(timeout=timeout)

        timeout_at = time.time() + (timeout or 0)
        while True:
            try:
                response = urllib.request.urlopen(
                    urllib.request.Request(url, headers=use_headers),
                    **kwargs,
                )
                break
            except URLError as e:
                code = getattr(e, "code", -1)
                if code != -1:
                    # If we had an actual http failure don't retry.
                    raise RuntimeError(f"Error trying to access url: {url}")

                elif time.time() > timeout_at:
                    # The connection wasn't even completed, retry.
                    raise RuntimeError(f"Error trying to access url: {url}")
                time.sleep(1 / 3.0)

        if response.status != 200:
            raise RuntimeError(
                f"Error. Found status: {response.status} ({response.msg}) when accessing: {url}."
            )

        data = response.read()
        return data.decode("utf-8")

    def get_json(self, *args, **kwargs):
        contents = self.get_str(*args, **kwargs)
        try:
            return json.loads(contents)
        except Exception:
            raise AssertionError(f"Unable to load: {contents!r}")

    def get_config(self, timeout: int | None = DEFAULT_TIMEOUT) -> dict:
        return self.get_json("config", timeout=timeout)

    def _on_stderr(self, line):
        sys.stderr.write(f"{line.rstrip()}\n")

    def _on_stdout(self, line):
        sys.stderr.write(f"{line.rstrip()}\n")

    def oauth2_login(
        self, provider: str, scopes: list[str], reference_id: str
    ) -> Future["LastRequestInfoTypedDict"]:
        """
        Args:
            provider: The provider for the oauth2 login.
            scopes: The scopes requested.

        Returns:
            A future where resulting dict has a `body` which is a json string with:
                'provider'
                'reference_id'
                'access_token'
                'expires_at'
                'token_type'
                'scopes'
        """
        import webbrowser

        from sema4ai_code.vendored_deps.url_callback_server import (
            start_server_in_thread,
        )

        fut_uri, fut_address = start_server_in_thread(port=0)
        scopes_str = " ".join(scopes)

        callback_url = fut_address.result(DEFAULT_TIMEOUT)
        assert callback_url

        log.info(
            f"Requesting OAuth2 login flow for provider: {provider}, scopes: {scopes} in browser."
        )

        # Needs to open the /oauth2/login in the browser.
        webbrowser.open(
            self.build_full_url(
                "/oauth2/login?"
                f"provider={provider}&"
                f"scopes={scopes_str}&"
                f"reference_id={reference_id}"
                f"&callback_url={callback_url}"
            ),
            new=1,
        )

        # The fut_uri will resolve when the user does the login.
        return fut_uri

    def oauth2_status(
        self, reference_id: str, provide_access_token: bool = False
    ) -> dict[str, StatusTypedDict]:
        provider_to_status = self.get_json(
            "/oauth2/status",
            params={
                "reference_id": reference_id,
                "provide_access_token": provide_access_token,
                "refresh_tokens": True if provide_access_token else False,
                "force_refresh": True,
            },
        )
        return provider_to_status

    def oauth2_logout(self, reference_id: str, provider: str) -> ActionResult:
        status = self.get_json(
            "/oauth2/logout",
            params={"reference_id": reference_id, "provider": provider},
        )
        if status["success"]:
            return ActionResult.make_success(True)
        else:
            return ActionResult.make_failure(status["error_message"])

    def stop(self) -> None:
        if self._process is not None:
            self._process.stop()
            self._process = None

    def create_reference_id(self) -> str:
        result = self.get_json("/oauth2/create-reference-id")

        return result["reference_id"]

    def is_alive(self) -> bool:
        process = self._process
        if process is None:
            return False

        return process.is_alive()

    def process_finished_future(self) -> Future[Literal[True]]:
        """
        Returns:
            A Future which will have its result set to `True` when
            the process is finished.
        """
        from sema4ai_ls_core.python_ls import run_in_new_thread

        fut: Future[Literal[True]] = Future()
        if self._process is None:
            fut.set_result(True)

        else:

            def wait_for_not_alive():
                try:
                    while not fut.cancelled() and self.is_alive():
                        try:
                            process = self._process
                            if process is not None:
                                process.join(2)
                            else:
                                break
                        except Exception:
                            pass
                finally:
                    if not fut.cancelled():
                        try:
                            fut.set_result(True)
                        except Exception:
                            # This could in theory happen in a race condition
                            # if it's cancelled in the meantime.
                            pass

            run_in_new_thread(wait_for_not_alive, "Wait for process", daemon=True)

        return fut


class ActionServer:
    def __init__(self, config_provider: IConfigProvider, endpoint: IEndPoint):
        self._config_provider = weakref.ref(config_provider)
        self._endpoint = weakref.ref(endpoint)
        self._cached_user_config_path: Path | None = None
        self._cached_sema4ai_oauth2_config: dict | None = None
        self._cached_sema4ai_oauth2_config_str: str | None = None

    def _get_str_optional_setting(self, setting_name) -> Any:
        config_provider = self._config_provider()
        config: IConfig | None = None
        if config_provider is not None:
            config = config_provider.config

        if config:
            return config.get_setting(setting_name, str, None)
        return None

    def get_action_server_location(self, download_if_missing: bool = True) -> str:
        """
        Returns Action Server location as specified in extension's settings (if exists), falls back
        to relative "bin" directory otherwise.
        Note that because Action Server executables are more controlled by the user, we don't want
        to download them by default if missing. Instead, we want to inform user about the error if it
        doesn't exist when running a command, so they can validate whether they provided a correct path
        for the executable of their choosing.

        Args:
            download_if_missing: If true, it will attempt to download the Action Server if missing.
        """
        action_server_location = get_default_action_server_location()

        if download_if_missing and not os.path.exists(action_server_location):
            download_action_server(action_server_location, endpoint=self._endpoint())

        return action_server_location

    def get_user_oauth2_config_file(self) -> Path:
        if (
            self._cached_user_config_path is None
            or not self._cached_user_config_path.exists()
        ):
            # FOR SUPPORT: action-server oauth2
            action_result = self._run_action_server_command(
                ["oauth2", "user-config-path"], timeout=10
            )
            if not action_result.success:
                # If not provided we don't really have a way to recover...
                raise RuntimeError(action_result.message)
            if not action_result.result:
                raise RuntimeError(
                    "Output of `action-server oauth2 user-config-path` is empty."
                )
            p = action_result.result.strip()
            self._cached_user_config_path = Path(p)
        return self._cached_user_config_path

    def get_sema4ai_oauth2_config_str(self) -> str:
        self.get_sema4ai_oauth2_config()
        assert self._cached_sema4ai_oauth2_config_str, (
            "Expected sema4ai oauth2 config to be set at this point."
        )
        return self._cached_sema4ai_oauth2_config_str

    def get_sema4ai_oauth2_config(self) -> dict:
        import yaml

        if not self._cached_sema4ai_oauth2_config:
            # FOR SUPPORT: action-server oauth2
            action_result = self._run_action_server_command(
                ["oauth2", "sema4ai-config"], timeout=10
            )
            if not action_result.success:
                raise RuntimeError(action_result.message)

            if not action_result.result:
                raise RuntimeError(
                    "Output of `action-server oauth2 sema4ai-config` is empty."
                )
            try:
                oauth2_config = yaml.safe_load(action_result.result)
            except Exception:
                raise RuntimeError(
                    "Sema4ai oauth2 settings gotten from the action server don't seem to be valid. "
                    f"Found: {action_result.result}"
                )
            self._cached_sema4ai_oauth2_config = oauth2_config
            self._cached_sema4ai_oauth2_config_str = action_result.result

        assert self._cached_sema4ai_oauth2_config, (
            "Expected sema4ai oauth2 config to be set at this point."
        )
        return self._cached_sema4ai_oauth2_config

    def _run_action_server_command(
        self,
        args: list[str],
        timeout: float = 35,
        download_if_missing: bool = True,
    ) -> LaunchActionResult:
        """
        Returns an ActionResult where the result is the stdout of the executed Action Server command.
        Args:
            args: The list of arguments to be passed to the command.
            timeout: The timeout for running the command (in seconds).
        """
        from sema4ai_ls_core.process import launch

        action_server_location = self.get_action_server_location(
            download_if_missing=download_if_missing
        )

        if not os.path.exists(action_server_location):
            return LaunchActionResult(
                command_line="action-server version",
                success=False,
                message="Action Server executable not found",
            )

        env: dict[str, str] = {"SEMA4AI_SKIP_UPDATE_CHECK": "1"}
        return launch(args=[action_server_location] + args, timeout=timeout, env=env)

    def get_version(self, download_if_missing=True) -> ActionResult[str]:
        """
        Returns the version of Action Server executable.
        """
        command_result = self._run_action_server_command(
            ["version"], download_if_missing=download_if_missing
        )

        if not command_result.success:
            return ActionResult(success=False, message=command_result.message)

        return ActionResult(success=True, message=None, result=command_result.result)

    def get_action_templates(self) -> ActionResult[list[ActionTemplate]]:
        """
        Returns the list of available Action templates.
        """
        # FOR SUPPORT: action-server new
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
        self, directory: str, template: str, name: str
    ) -> ActionResult:
        """
        Creates a new Action package under given directory, using specified template.

        Args:
            directory: The directory to create the Action package in.
            template: The template to use for the new Action package.
            name: The name of the Action package.
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

        if not template:
            return ActionResult(
                success=False,
                message="Template name must be provided and may not be empty.",
            )

        # Action Server < v10 is not supported.
        if version_tuple <= (0, 10):
            return ActionResult(
                success=False,
                message="Action Server version is too old. Please update.",
            )
        else:
            args = ["new", f"--name={directory}", f"--template={template}", "--force"]

        # FOR SUPPORT: action-server new
        command_result = self._run_action_server_command(args)

        if command_result.success:
            from ruamel.yaml import YAML

            yaml = YAML()
            yaml.preserve_quotes = True
            package_path = f"{directory}/package.yaml"

            with open(package_path) as stream:
                package_yaml = yaml.load(stream.read())

            package_yaml["name"] = name

            with open(package_path, "w") as file:
                yaml.dump(package_yaml, file)

            return ActionResult(success=True, message=None, result=package_path)
        else:
            return ActionResult(
                success=False, message=get_error_message(command_result.message or "")
            )

    def cloud_login(self, access_credentials: str, hostname: str) -> ActionResult:
        """
        Set authentication information to the Control Room for action server.

        Args:
            access_credentials: Control Room access credentials.
            hostname: Control Room hostname.
        """
        args = [
            "cloud",
            "login",
            "--access-credentials",
            access_credentials,
            "--hostname",
            hostname,
        ]

        # FOR SUPPORT: action-server cloud login
        command_result = self._run_action_server_command(args)

        if command_result.success:
            return ActionResult(success=True, message=None)

        return ActionResult(
            success=False,
            message=f"Error login to Control Room.\n{command_result.message or ''}",
        )

    def verify_login(self) -> ActionResult[ActionServerVerifyLoginInfoDict]:
        """
        Verify authentication information from the Control Room for action server.
        """
        args = ["cloud", "verify-login", "--json"]

        # FOR SUPPORT: action-server cloud verify-login
        command_result = self._run_action_server_command(args, timeout=ONE_MINUTE_S)

        if command_result.success:
            try:
                if command_result.result:
                    result = json.loads(command_result.result)
                else:
                    return ActionResult(
                        success=False,
                        message=f"Error empty output.\n{command_result.message}",
                    )
            except Exception:
                return ActionResult(
                    success=False,
                    message=f"Error parsing output.\n{command_result.result}",
                )
            return ActionResult(success=True, message=None, result=result)

        return ActionResult(
            success=False,
            message=f"Error verifying Control Room authentication.\n{command_result.message or ''}",
        )

    def list_organizations(
        self, access_credentials: str | None, hostname: str | None
    ) -> ActionResult[list[str]]:
        """
        List available organizations with access credentials used at login.
        """
        args = ["cloud", "list-organizations", "--json"]

        if access_credentials and hostname:
            args.extend(
                ["--access-credentials", access_credentials, "--hostname", hostname]
            )

        command_result = self._run_action_server_command(args, timeout=ONE_MINUTE_S * 5)

        if command_result.success:
            try:
                result = (
                    json.loads(command_result.result) if command_result.result else None
                )
            except Exception:
                return ActionResult(
                    success=False,
                    message=f"Error parsing output.\n{command_result.result}",
                )
            return ActionResult(success=True, message=None, result=result)
        else:
            return ActionResult(
                success=False,
                message=f"Error listing Control Room organizations.\n{command_result.message or ''}",
            )

    def package_build(
        self, workspace_dir: str, output_dir: str
    ) -> ActionResult[ActionServerPackageBuildInfo]:
        """
        Build action package.

        Args:
            workspace_dir, path to the current workspace.
            output_dir, path to the directory where the package will be built.
        """
        args = [
            "package",
            "build",
            "--input-dir",
            workspace_dir,
            "--output-dir",
            output_dir,
            "--override",
            "--json",
        ]

        # FOR SUPPORT: action-server package build
        command_result = self._run_action_server_command(
            args, timeout=ONE_MINUTE_S * 10
        )

        if command_result.success:
            try:
                if not command_result.result:
                    return ActionResult(
                        success=False,
                        message="Error not output from action server.",
                    )
                result = json.loads(command_result.result)
            except Exception:
                return ActionResult(
                    success=False,
                    message=f"Error parsing output.\n{command_result.result}",
                )
            return ActionResult(success=True, message=None, result=result)

        return ActionResult(
            success=False,
            message=f"Error building action package.\n{command_result.message or ''}",
        )

    def package_upload(
        self,
        package_path: str,
        organization_id: str,
        access_credentials: str | None,
        hostname: str | None,
    ) -> ActionResult[ActionServerPackageUploadStatus]:
        """
        Upload action package to Control Room.

        Args:
            package_path, path tot he package to upload.
            organization_id, Control Room organization id.
        """
        args = [
            "package",
            "upload",
            "--package-path",
            package_path,
            "--organization-id",
            organization_id,
            "--json",
        ]

        if access_credentials and hostname:
            args.extend(
                ["--access-credentials", access_credentials, "--hostname", hostname]
            )

        # FOR SUPPORT: action-server upload
        command_result = self._run_action_server_command(
            args, timeout=ONE_MINUTE_S * 10
        )

        if command_result.success:
            try:
                if not command_result.result:
                    return ActionResult(
                        success=False,
                        message="Error not output from action server.",
                    )
                result = json.loads(command_result.result)
            except Exception:
                return ActionResult(
                    success=False,
                    message=f"Error parsing output.\n{command_result.result}",
                )
            return ActionResult(success=True, message=None, result=result)

        return ActionResult(
            success=False,
            message=f"Error uploading package to Control Room.\n{command_result.message or ''}",
        )

    def package_status(
        self,
        package_id: str,
        organization_id: str,
        access_credentials: str | None,
        hostname: str | None,
    ) -> ActionResult[ActionServerPackageUploadStatus]:
        """
        Get uploaded action package status from Control Room.

        Args:
            package_id, uploaded package id.
            organization_id, Control Room organization id.
        """
        args = [
            "package",
            "status",
            "--package-id",
            package_id,
            "--organization-id",
            organization_id,
            "--json",
        ]

        if access_credentials and hostname:
            args.extend(
                ["--access-credentials", access_credentials, "--hostname", hostname]
            )

        # FOR SUPPORT: action-server package status
        command_result = self._run_action_server_command(args, timeout=ONE_MINUTE_S * 5)

        if command_result.success:
            try:
                if not command_result.result:
                    return ActionResult(
                        success=False,
                        message="Error not output from action server.",
                    )
                result = json.loads(command_result.result)
            except Exception:
                return ActionResult(
                    success=False,
                    message=f"Error parsing output.\n{command_result.result}",
                )
            return ActionResult(success=True, message=None, result=result)
        else:
            return ActionResult(
                success=False,
                message=f"Error getting package status from Control Room.\n{command_result.message or ''}",
            )

    def package_set_changelog(
        self,
        package_id: str,
        organization_id: str,
        changelog_input: str,
        access_credentials: str | None,
        hostname: str | None,
    ) -> ActionResult:
        """
        Update the changelog for package in Control Room.

        Args:
            package_id, uploaded package id.
            organization_id, Control Room organization id.
            changelog_input, line to the package changelog.
        """
        args = [
            "package",
            "set-changelog",
            "--package-id",
            package_id,
            "--organization-id",
            organization_id,
            "--change-log",
            changelog_input,
        ]

        if access_credentials and hostname:
            args.extend(
                ["--access-credentials", access_credentials, "--hostname", hostname]
            )

        # FOR SUPPORT: action-server set-changelog
        command_result = self._run_action_server_command(args, timeout=ONE_MINUTE_S * 5)

        if command_result.success:
            return ActionResult(success=True, message=None)

        return ActionResult(
            success=False,
            message=f"Error updating the changelog for package to Control Room.\n{command_result.message or ''}",
        )

    def package_metadata(
        self, action_package_path: str, output_file_path: str
    ) -> ActionResult:
        """
        Create the Action Package metadata.json.

        Args:
            input_dir, directory to find the package.json from.
            output_dir, directory where to create the metadata.json file.
        """
        args = [
            "package",
            "metadata",
            "--input-dir",
            action_package_path,
            "--output-file",
            output_file_path,
        ]

        # Make sure the path is created
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # FOR SUPPORT: action-server metadata
        command_result = self._run_action_server_command(
            args, timeout=ONE_MINUTE_S * 60
        )

        if command_result.success:
            return ActionResult(success=True, message=None)

        return ActionResult(
            success=False,
            message=f"Error creating the metadata file.\n{command_result.message or ''}",
        )
