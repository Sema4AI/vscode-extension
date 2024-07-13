import json
import os
import sys
import typing
from concurrent.futures import Future
from pathlib import Path
from typing import Literal, Optional, TypedDict

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.options import DEFAULT_TIMEOUT

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

ONE_MINUTE_S = 60

if typing.TYPE_CHECKING:
    from sema4ai_code.vendored_deps.url_callback_server import LastRequestInfoTypedDict


class StatusTypedDict(TypedDict):
    scopes: Optional[list[str]]
    expires_at: str  # iso-formatted datetime or empty string
    access_token: Optional[str]  # Only available if not an automatic id
    metadata: Optional[dict]  # Metadata which may be available


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
    force: bool = False,
    sys_platform: Optional[str] = None,
    action_server_version="0.16.1",
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


def get_default_oauth2_settings_file() -> Path:
    return get_default_action_server_settings_dir() / "oauth2-settings.yaml"


class ActionServerAsService:
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
        self.action_server_location = action_server_location
        self.port = port

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

        self._process = Process(args, cwd=self._cwd)
        self._process.on_stderr.register(self._on_stderr)
        self._process.on_stdout.register(self._on_stdout)
        self._process.start()

    def _urlopen_kwargs(self, **kwargs) -> dict:
        """
        Provides the default kwargs that should be used for a urlopen call.
        """
        if is_debugger_active():
            kwargs["timeout"] = None

        elif "timeout" not in kwargs:
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
            # Create a context with certificate verification
            try:
                import truststore

                truststore.extract_from_ssl()
            except Exception:
                pass

            from ssl import Purpose

            ctx = ssl.create_default_context(Purpose.SERVER_AUTH)
            ctx.load_verify_locations(cert_file_path)
            kwargs["context"] = ctx

            try:
                import truststore

                truststore.inject_into_ssl()
            except Exception:
                pass
        return kwargs

    def build_full_url(self, url: str) -> str:
        if url.startswith("/"):
            url = url[1:]
        return f"{self.base_url}/{url}"

    def get_str(
        self,
        url,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ):
        """Fetches the URL using urllib and handles basic request parameters.
        Note: requests is not a dependency so it cannot be used.

        Args:
          url: The URL to fetch.
          params: A dictionary of query parameters. (Optional)
          headers: A dictionary of headers to send with the request. (Optional)
          timeout: The timeout in seconds for the request. (Optional)
        """
        import urllib.parse
        import urllib.request

        url = self.build_full_url(url)
        # Build the full URL with query parameters
        if params:
            encoded_params = urllib.parse.urlencode(params)
            url = f"{url}?{encoded_params}"

        use_headers = {"User-Agent": "Mozilla"}
        if headers:
            use_headers.update(headers)
        kwargs = self._urlopen_kwargs(timeout=timeout)

        response = urllib.request.urlopen(
            urllib.request.Request(url, headers=use_headers),
            **kwargs,
        )
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

    def get_config(self, timeout: Optional[int] = DEFAULT_TIMEOUT) -> dict:
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

    def oauth2_status(self, reference_id: str) -> dict[str, StatusTypedDict]:
        provider_to_status = self.get_json(
            "/oauth2/status",
            params={
                "reference_id": reference_id,
                "provide_access_token": True,
                "refresh_tokens": True,
                "force_refresh": True,
            },
        )
        return provider_to_status

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
                            pass  # This could in theory fail in a race condition.

            run_in_new_thread(wait_for_not_alive, "Wait for process")

        return fut


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
        from subprocess import CalledProcessError, TimeoutExpired, list2cmdline, run

        from sema4ai_ls_core.basic import as_str, build_subprocess_kwargs

        kwargs = build_subprocess_kwargs(None, env=os.environ.copy())
        args = [self._action_server_location] + args
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

        command_result = self._run_action_server_command(args)

        if command_result.success:
            return ActionResult(success=True, message=None)

        return ActionResult(
            success=False,
            message=f"Error login to Control Room.\n{command_result.message or ''}",
        )

    def verify_login(self) -> ActionResult[ActionServerVerifyLoginResultDict]:
        """
        Verify authentication information from the Control Room for action server.
        """
        args = ["cloud", "verify-login", "--json"]

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
        self, access_credentials: Optional[str], hostname: Optional[str]
    ) -> ActionResult[ActionServerListOrgsResultDict]:
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
    ) -> ActionResult[ActionServerPackageBuildResultDict]:
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
        access_credentials: Optional[str],
        hostname: Optional[str],
    ) -> ActionResult[ActionServerPackageUploadStatusDict]:
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
        access_credentials: Optional[str],
        hostname: Optional[str],
    ) -> ActionResult[ActionServerPackageUploadStatusDict]:
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
        access_credentials: Optional[str],
        hostname: Optional[str],
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

        command_result = self._run_action_server_command(
            args, timeout=ONE_MINUTE_S * 60
        )

        if command_result.success:
            return ActionResult(success=True, message=None)

        return ActionResult(
            success=False,
            message=f"Error creating the metadata file.\n{command_result.message or ''}",
        )


if __name__ == "__main__":
    import truststore

    truststore.extract_from_ssl()

    s = ActionServerAsService(
        "", cwd=".", port=4567, use_https=True, ssl_self_signed=True
    )
    print(s.get_config(timeout=10))

    truststore.inject_into_ssl()
    s = ActionServerAsService(
        "", cwd=".", port=4567, use_https=True, ssl_self_signed=True
    )
    print(s.get_config(timeout=10))
