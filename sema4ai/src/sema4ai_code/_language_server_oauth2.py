import threading
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sema4ai_ls_core import uris
from sema4ai_ls_core.command_dispatcher import _SubCommandDispatcher
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.lsp import LSPMessages
from sema4ai_ls_core.protocols import ActionResultDict, IEndPoint, IMonitor

from sema4ai_code import commands
from sema4ai_code.protocols import IRcc

log = get_logger(__name__)
oauth2_command_dispatcher = _SubCommandDispatcher("_oauth2")

if typing.TYPE_CHECKING:
    from concurrent.futures import Future

    from sema4ai_code.action_server import ActionServer, ActionServerAsService


@dataclass
class _Data:
    cwd: Path
    datadir: Path
    port: int
    protocol: str
    ssl_self_signed: bool
    ssl_keyfile: str
    ssl_certfile: str


def create_monitor_cancelled_future(monitor: IMonitor) -> "Future[Any]":
    from concurrent.futures import Future

    f: Future[Any] = Future()

    monitor.add_listener(f.cancel)

    return f


def wait_first_future_completed(
    futures: list["Future[Any]"], timeout: int | None = None
) -> set["Future[Any]"]:
    """
    Args:
        futures: the futures to wait for
        timeout: the time to wait for

    Returns:
        A set with the futures done (may be empty if it times out
        and no features are completed).
    """
    done = set()
    ev = threading.Event()

    def on_done(f):
        done.add(f)
        ev.set()

    for f in futures:
        f.add_done_callback(on_done)

    ev.wait(timeout)
    return done


class _OAuth2:
    def __init__(
        self,
        endpoint: IEndPoint,
        base_command_dispatcher,
        rcc: IRcc,
        feedback,
        lsp_messages: LSPMessages,
        action_server: "ActionServer",
    ):
        from sema4ai_code._language_server_feedback import _Feedback
        from sema4ai_code.action_server import ActionServerAsService

        self._endpoint = endpoint
        self._rcc = rcc
        self._feedback: _Feedback = feedback
        self._last_key: tuple | None = None
        self._action_server_as_service: ActionServerAsService | None = None
        self._lock = threading.Lock()
        self._lsp_messages = lsp_messages
        self._action_server = action_server

        base_command_dispatcher.register_sub_command_dispatcher(
            oauth2_command_dispatcher
        )
        from ._oauth2 import set_get_sema4ai_oauth2_config_callback

        set_get_sema4ai_oauth2_config_callback(
            self._action_server.get_sema4ai_oauth2_config_str
        )

    def oauth2_logout(
        self, action_server_location: str, provider: str, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.vendored_deps.oauth2_settings import (
            get_oauthlib2_user_settings,
        )

        oauth2_settings_file = self._get_default_oauth2_settings_file()
        try:
            # Raises an error if it's not Ok
            oauth2_user_contents = get_oauthlib2_user_settings(
                str(oauth2_settings_file)
            )
        except Exception as e:
            msg = f"Bad configuration in {oauth2_settings_file}.\nDetails: {e}"
            log.exception(msg)
            self.open_oauth2_settings()
            return ActionResult.make_failure(message=msg).as_dict()
        try:
            data = self._collect_info(
                oauth2_user_contents, oauth2_settings_file, provider=provider
            )
        except Exception as e:
            return ActionResult.make_failure(message=str(e)).as_dict()

        action_server = self.get_action_server_for_oauth2(action_server_location, data)
        reference_id = self._get_reference_id(data.cwd, action_server)
        result = action_server.oauth2_logout(reference_id, provider=provider)
        return result.as_dict()

    def oauth2_status(
        self, action_server_location: str, provide_access_token: bool, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.vendored_deps.oauth2_settings import (
            get_oauthlib2_user_settings,
        )

        oauth2_settings_file = self._get_default_oauth2_settings_file()
        try:
            # Raises an error if it's not Ok
            oauth2_user_contents = get_oauthlib2_user_settings(
                str(oauth2_settings_file)
            )
        except Exception as e:
            msg = f"Bad configuration in {oauth2_settings_file}.\nDetails: {e}"
            log.exception(msg)
            self.open_oauth2_settings()
            return ActionResult.make_failure(message=msg).as_dict()
        try:
            data = self._collect_info(oauth2_user_contents, oauth2_settings_file)
        except Exception as e:
            log.exception("Error collecting OAuth2 status.")
            return ActionResult.make_failure(message=str(e)).as_dict()

        action_server = self.get_action_server_for_oauth2(action_server_location, data)
        reference_id = self._get_reference_id(data.cwd, action_server)
        status = action_server.oauth2_status(
            reference_id, provide_access_token=provide_access_token
        )

        return ActionResult.make_success(status).as_dict()

    def _get_reference_id(
        self, cwd: Path, action_server: "ActionServerAsService"
    ) -> str:
        reference_id_path = cwd / ".vscode_reference_id"
        if reference_id_path.exists():
            reference_id = reference_id_path.read_text()
        else:
            reference_id = action_server.create_reference_id()
            reference_id_path.write_text(reference_id)
        return reference_id

    def _get_redirect_uri(self, requires_https: bool) -> tuple[int, str]:
        """
        Args:
            requires_https: Whether https is required.
        Returns:
            tuple with (port, protocol), where protocol is `http` or `https`.
        """
        from urllib.parse import urlparse

        from sema4ai_code.action_server import is_port_free

        oauth2_config = self._action_server.get_sema4ai_oauth2_config()
        redirect_urls = oauth2_config["oauth2Config"]["redirectUrls"]
        redirect_urls = tuple(x.strip() for x in redirect_urls.split(","))

        checked_ports = set()
        for redirect_url in redirect_urls:
            parsed_url = urlparse(redirect_url)
            protocol = parsed_url.scheme
            port = parsed_url.port
            path = parsed_url.path

            if protocol not in ("http", "https"):
                msg = f"'oauth2Config/redirectUrls' ({redirect_url}) must start with 'http' or 'https' in Sema4.ai oauth2 config."
                raise RuntimeError(msg)

            if not port:
                msg = f"'oauth2Config/redirectUrls' ({redirect_url}) must specify the port (something as http://localhost:port/sema4ai/oauth2/) in Sema4.ai oauth2 config."
                raise RuntimeError(msg)

            if path != "/sema4ai/oauth2/":
                msg = f"'oauth2Config/redirectUrls' ({redirect_url}) must end with '/sema4ai/oauth2/' in Sema4.ai oauth2 config."
                raise RuntimeError(msg)

            if requires_https and protocol != "https":
                continue
            elif protocol != "http":
                continue

            if is_port_free(port):
                return (port, protocol)
            checked_ports.add(port)

        raise RuntimeError(
            f"Found no free ports to start OAuth2 flow (checked ports: {checked_ports}).\nConfigured redirect urls: {redirect_urls}."
        )

    def _collect_info(
        self,
        oauth2_user_contents: dict,
        oauth2_settings_file: Path,
        provider: str | None = None,
    ) -> _Data:
        """
        Args:
            provider: if given the settings provided will be based on the given
                provider to determine if https should be used (otherwise it'll
                default to http instead of https).
        """

        ssl_self_signed = False
        ssl_keyfile = ""
        ssl_certfile = ""
        requires_https = False
        if provider:
            # If the provider is passed then it's possible to determine if https is needed.
            oauth2_config = oauth2_user_contents.get("oauth2Config")
            if not oauth2_config:
                msg = f"'oauth2Config' is not properly configured in {oauth2_settings_file}."
                self.open_oauth2_settings()
                raise RuntimeError(msg)

            if not isinstance(oauth2_config, dict):
                msg = f"'oauth2Config' is expected to be a dict in {oauth2_settings_file}."
                self.open_oauth2_settings()
                raise RuntimeError(msg)

            providers = oauth2_config.get("providers")
            if not providers or not isinstance(providers, dict):
                msg = f"'oauth2Config/providers' is expected to be a (non-empty) dict in {oauth2_settings_file}."
                self.open_oauth2_settings()
                raise RuntimeError(msg)

            provider_info = providers.get(provider)
            if not provider_info or not isinstance(provider_info, dict):
                msg = f"oauth2Config/providers/{provider} is expected to be a (non-empty) dict in {oauth2_settings_file}."
                self.open_oauth2_settings()
                raise RuntimeError(msg)

            mode = provider_info.get("mode")
            if mode not in ("custom", "sema4ai"):
                msg = f"mode for provider: {provider} is expected to be 'custom' or 'sema4ai' in {oauth2_settings_file}."
                self.open_oauth2_settings()
                raise RuntimeError(msg)

            if mode == "sema4ai":
                try:
                    sema4ai_oauth2_config = (
                        self._action_server.get_sema4ai_oauth2_config()
                    )
                    providers = sema4ai_oauth2_config["oauth2Config"]["providers"]
                except Exception:
                    raise RuntimeError("Error in Sema4.ai OAuth2 config.")
                provider_info = providers.get(provider)

            requires_https = provider_info.get("requiresHttps", False)
            if requires_https:
                ssl_self_signed = oauth2_config.get("sslSelfSigned", False)
                ssl_keyfile = oauth2_config.get("sslKeyfile", "")
                ssl_certfile = oauth2_config.get("sslCertfile", "")

        extension_datadir = self._rcc.get_robocorp_code_datadir()
        cwd = extension_datadir / "oauth2" / "cwd"
        datadir = extension_datadir / "oauth2" / "datadir"
        cwd.mkdir(parents=True, exist_ok=True)
        datadir.mkdir(parents=True, exist_ok=True)

        port, protocol = self._get_redirect_uri(requires_https)

        return _Data(
            cwd=cwd,
            datadir=datadir,
            port=port,
            protocol=protocol,
            ssl_self_signed=ssl_self_signed,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )

    @oauth2_command_dispatcher(commands.SEMA4AI_OAUTH2_OPEN_SETTINGS)
    def open_oauth2_settings(self, *args, **kwargs) -> None:
        oauth_2_settings_file = self._get_default_oauth2_settings_file()

        self._lsp_messages.show_document(
            {
                "uri": uris.from_fs_path(str(oauth_2_settings_file)),
                "external": False,
                "takeFocus": True,
            }
        )

    def _get_default_oauth2_settings_file(self) -> Path:
        return self._action_server.get_user_oauth2_config_file()

    def oauth2_login(
        self,
        action_server_location: str,
        provider: str,
        scopes: list[str],
        monitor: IMonitor,
    ) -> ActionResultDict:
        import json

        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.vendored_deps.oauth2_settings import (
            get_oauthlib2_user_settings,
        )

        oauth2_settings_file = self._get_default_oauth2_settings_file()
        try:
            # Raises an error if it's not Ok
            oauth2_user_contents = get_oauthlib2_user_settings(
                str(oauth2_settings_file)
            )
        except Exception as e:
            msg = f"Bad configuration in {oauth2_settings_file}.\nDetails: {e}"
            log.exception(msg)
            self.open_oauth2_settings()
            return ActionResult.make_failure(message=msg).as_dict()

        try:
            data = self._collect_info(
                oauth2_user_contents, oauth2_settings_file, provider=provider
            )
        except Exception as e:
            log.exception("Error collecting OAuth2 information.")
            return ActionResult.make_failure(message=str(e)).as_dict()

        action_server = self.get_action_server_for_oauth2(action_server_location, data)

        reference_id = self._get_reference_id(data.cwd, action_server)

        future_oauth2 = action_server.oauth2_login(
            provider=provider, scopes=scopes, reference_id=reference_id
        )
        process_finished_future = action_server.process_finished_future()
        future_monitor_cancelled = create_monitor_cancelled_future(monitor)

        # i.e.: the clauses for termination are: action completes, process is killed,
        # the user cancels the action.
        futures: list["Future[Any]"] = [
            future_oauth2,
            process_finished_future,
            future_monitor_cancelled,
        ]

        done = wait_first_future_completed(futures)
        completed = future_oauth2 in done

        # After one completes cancel other(s)
        for f in futures:
            if f not in done:
                f.cancel()

        monitor.check_cancelled()

        if completed:
            # Ok, OAuth2 was completed.
            result = future_oauth2.result()
            if not result["body"]:
                return ActionResult.make_failure(
                    "body not available in future_oauth2"
                ).as_dict()

            loaded_data = json.loads(result["body"])
            if loaded_data.get("reference_id") == reference_id:
                log.info("OAuth2 authentication flow completed.")
                return ActionResult.make_success(loaded_data).as_dict()

        msg = "OAuth2 authentication flow not completed."
        log.info(msg)
        return ActionResult.make_failure(msg).as_dict()

    def get_action_server_for_oauth2(
        self,
        action_server_location: str,
        data: _Data,
    ) -> "ActionServerAsService":
        from sema4ai_code.action_server import ActionServerAsService

        # If nothing changed, we can reuse a previously created one, otherwise
        # kill previous and start new one.
        key = (
            action_server_location,
            data.port,
            data.cwd,
            data.protocol,
            data.datadir,
            data.ssl_self_signed,
            data.ssl_keyfile,
            data.ssl_certfile,
        )

        with self._lock:
            if self._action_server_as_service is not None:
                if self._last_key == key:
                    # See if we can make a request and if it's live.
                    try:
                        self._action_server_as_service.get_config()
                    except Exception:
                        self._last_key = None
                        self._action_server_as_service.stop()
                        self._action_server_as_service = None
                else:
                    self._action_server_as_service.stop()
                    self._action_server_as_service = None

            if self._last_key != key or self._action_server_as_service is None:
                self._last_key = key

                self._action_server_as_service = ActionServerAsService(
                    action_server_location,
                    port=data.port,
                    cwd=str(data.cwd),
                    use_https=data.protocol == "https",
                    datadir=str(data.datadir),
                    ssl_self_signed=data.ssl_self_signed,
                    ssl_keyfile=data.ssl_keyfile,
                    ssl_certfile=data.ssl_certfile,
                )
                self._action_server_as_service.start_for_oauth2()
                # Initialize and make a request to wait for it to be live.
                self._action_server_as_service.get_config(timeout=60)
                log.info("Action Server live (responded first request).")

            return self._action_server_as_service
