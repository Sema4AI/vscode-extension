import threading
import typing
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Optional

from sema4ai_ls_core import uris
from sema4ai_ls_core.command_dispatcher import _SubCommandDispatcher
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.lsp import LSPMessages
from sema4ai_ls_core.protocols import ActionResultDict, IEndPoint

from sema4ai_code import commands
from sema4ai_code.protocols import (
    ActionServerOauth2LoginParams,
    ActionServerOauth2StatusParams,
    IRcc,
)

log = get_logger(__name__)
oauth2_command_dispatcher = _SubCommandDispatcher("_oauth2")

if typing.TYPE_CHECKING:
    from sema4ai_code.action_server import ActionServerAsService

_DEFAULT_OAUTH2_YAML_SETTINGS_FILE_CONTENTS = """
# The "devServerInfo" information is only used to require tokens from VSCode:
#
# This is the server information which will be used to create a server
# which will be used to collect the OAuth2 tokens as needed.
# Note that this is ONLY USED WHEN tokens are requested from 
# a separate application, such as VSCode, as when the action
# server is manually started it'll use host/port provided when
# it was initialized.
devServerInfo:
  redirectUri: "http://localhost:4567"
  # If the redirectUri starts with `https`, ssl information is
  # needed. In this case it's possible to either set `sslSelfSigned`
  # to true to automatically create a self-signed certificate or
  # set the `sslKeyfile` and `sslCertfile` to be used to serve
  # the page.
  #
  # Note: the redirectUri needs to be specified here and in the service.
  # Keep in mind that the port must not be used by any other service
  # in the machine.
  #
  # Disclaimer: if using a self-signed certificate, the browser may complain
  # and an exception needs to be accepted to proceed to the site unless
  # the self-signed certificate is imported in the system.
  sslSelfSigned: false
  sslKeyfile: ""
  sslCertfile: ""

# Details for each provider need to be manually set.
#
# The following providers just require "clientId" and "clientSecret":
# - google, github, slack, and hubspot
#
# The following providers require "server", "clientId" and "clientSecret":
# - microsoft, zendesk
#
# Any other provider besides those also needs to specify
# "server", "tokenEndpoint" and "authorizationEndpoint"
#
# Note: if the "tokenEndpoint"/"authorizationEndpoint" are relative,
# the "server" is prefixed to it to get the absolute version.
#
# google:
#   clientId: "XXXX-YYYYYYYYY.apps.googleusercontent.com"
#   clientSecret: "XXXXX-yyyyyyyyyyyyyyyy"
#
# slack:
#   clientId: "XXXXXXXXXXXX.YYYYYYYYYYY"
#   clientSecret: "zzzzzzzzzzzzzzz"
#
# hubspot:
#   clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#   clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#
# microsoft:
#   clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#   clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#   server: "https://<service.microsoft.com>"
#
# custom:
#   clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#   clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
#   server: "https://<service.microsoft.com>"

"""


@dataclass
class _Data:
    cwd: Path
    datadir: Path
    port: int
    protocol: str
    ssl_self_signed: bool
    ssl_keyfile: str
    ssl_certfile: str


class _OAuth2(object):
    def __init__(
        self,
        endpoint: IEndPoint,
        base_command_dispatcher,
        rcc: IRcc,
        feedback,
        lsp_messages: LSPMessages,
    ):
        from sema4ai_code._language_server_feedback import _Feedback
        from sema4ai_code.action_server import ActionServerAsService

        self._endpoint = endpoint
        self._rcc = rcc
        self._feedback: _Feedback = feedback
        self._last_key: Optional[tuple] = None
        self._action_server_as_service: Optional[ActionServerAsService] = None
        self._lock = threading.Lock()
        self._lsp_messages = lsp_messages

        base_command_dispatcher.register_sub_command_dispatcher(
            oauth2_command_dispatcher
        )

    @oauth2_command_dispatcher(commands.SEMA4AI_OAUTH2_STATUS_INTERNAL)
    def _oauth2_status(self, params: ActionServerOauth2StatusParams):
        return partial(self._oauth2_status_in_thread, params=params)

    def _oauth2_status_in_thread(
        self, params: ActionServerOauth2StatusParams
    ) -> ActionResultDict:
        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.action_server import get_default_oauth2_settings_file
        from sema4ai_code.vendored_deps.oauth2_settings import (
            get_oauthlib2_global_settings,
        )

        action_server_location = params["action_server_location"]

        oauth2_settings_file = get_default_oauth2_settings_file()
        try:
            # Raises an error if it's not Ok
            oauth2_global_contents = get_oauthlib2_global_settings(
                str(oauth2_settings_file)
            )
        except Exception as e:
            msg = f"Bad configuration in {oauth2_settings_file}.\nDetails: {e}"
            log.exception(msg)
            return ActionResult.make_failure(message=msg).as_dict()
        try:
            data = self._collect_info(oauth2_global_contents, oauth2_settings_file)
        except Exception as e:
            return ActionResult.make_failure(message=str(e)).as_dict()

        action_server = self.get_action_server_for_oauth2(action_server_location, data)
        reference_id = self._get_reference_id(data.cwd, action_server)
        status = action_server.oauth2_status(reference_id)

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

    def _collect_info(
        self, oauth2_global_contents: dict, oauth2_settings_file: Path
    ) -> _Data:
        from urllib.parse import urlparse

        # If we got here the settings seem ok, so, proceed to call the action server
        dev_server_info = oauth2_global_contents.get("devServerInfo")
        if not dev_server_info:
            msg = (
                f"'devServerInfo' is not properly configured in {oauth2_settings_file}."
            )
            raise RuntimeError(msg)

        if not isinstance(dev_server_info, dict):
            msg = f"'devServerInfo' is expected to be a dict in {oauth2_settings_file}."
            raise RuntimeError(msg)

        redirect_uri = dev_server_info.get("redirectUri")
        if not isinstance(redirect_uri, str):
            msg = f"'devServerInfo/redirectUri' ({redirect_uri}) is not properly configured in {oauth2_settings_file}."
            raise RuntimeError(msg)

        parsed_url = urlparse(redirect_uri)
        protocol = parsed_url.scheme
        port = parsed_url.port

        if protocol not in ("http", "https"):
            msg = f"'devServerInfo/redirectUri' ({redirect_uri}) must start with 'http' or 'https' {oauth2_settings_file}."
            raise RuntimeError(msg)

        if not port:
            msg = f"'devServerInfo/redirectUri' ({redirect_uri}) must specify the port (something as http://localhost:port) {oauth2_settings_file}."
            raise RuntimeError(msg)

        ssl_self_signed = dev_server_info.get("sslSelfSigned", False)
        ssl_keyfile = dev_server_info.get("sslKeyfile", "")
        ssl_certfile = dev_server_info.get("sslCertfile", "")

        extension_datadir = self._rcc.get_robocorp_code_datadir()
        cwd = extension_datadir / "oauth2" / "cwd"
        datadir = extension_datadir / "oauth2" / "datadir"
        cwd.mkdir(parents=True, exist_ok=True)
        datadir.mkdir(parents=True, exist_ok=True)

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
    def _oauth2_settings(self, *args, **kwargs) -> None:
        from sema4ai_code.action_server import get_default_oauth2_settings_file

        oauth_2_settings_file = get_default_oauth2_settings_file()
        if not oauth_2_settings_file.exists():
            # Create default
            oauth_2_settings_file.write_text(
                _DEFAULT_OAUTH2_YAML_SETTINGS_FILE_CONTENTS
            )

        self._lsp_messages.show_document(
            {
                "uri": uris.from_fs_path(str(oauth_2_settings_file)),
                "external": False,
                "takeFocus": True,
            }
        )

    @oauth2_command_dispatcher(commands.SEMA4AI_OAUTH2_LOGIN_INTERNAL)
    def _oauth2_login(self, params: ActionServerOauth2LoginParams):
        return partial(self._oauth2_login_in_thread, params=params)

    def _oauth2_login_in_thread(
        self, params: ActionServerOauth2LoginParams
    ) -> ActionResultDict:
        import json
        from concurrent.futures import Future
        from concurrent.futures._base import as_completed

        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.action_server import get_default_oauth2_settings_file
        from sema4ai_code.vendored_deps.oauth2_settings import (
            get_oauthlib2_global_settings,
            get_oauthlib2_provider_settings,
        )

        action_server_location = params["action_server_location"]
        provider = params["provider"]
        scopes = params["scopes"]

        oauth2_settings_file = get_default_oauth2_settings_file()
        try:
            # Raises an error if it's not Ok
            oauth2_global_contents = get_oauthlib2_global_settings(
                str(oauth2_settings_file)
            )
            get_oauthlib2_provider_settings(provider, str(oauth2_settings_file))
        except Exception as e:
            msg = f"Bad configuration in {oauth2_settings_file} for provider: {provider}.\nDetails: {e}"
            log.exception(msg)
            return ActionResult.make_failure(message=msg).as_dict()

        try:
            data = self._collect_info(oauth2_global_contents, oauth2_settings_file)
        except Exception as e:
            return ActionResult.make_failure(message=str(e)).as_dict()

        action_server = self.get_action_server_for_oauth2(action_server_location, data)

        reference_id = self._get_reference_id(data.cwd, action_server)

        future_oauth2 = action_server.oauth2_login(
            provider=provider, scopes=scopes, reference_id=reference_id
        )
        process_finished_future = action_server.process_finished_future()
        futures: list[Future[Any]] = [future_oauth2, process_finished_future]

        fut: Future[Any]
        f: Future[Any]
        for fut in as_completed(futures):  # After one completes cancel other(s)
            for f in futures:
                if f is not fut:
                    f.cancel()

            break

        if fut is future_oauth2:
            # Ok, OAuth2 was completed.
            result = fut.result()
            loaded_data = json.loads(result["body"])
            if loaded_data.get("reference_id") == reference_id:
                return ActionResult.make_success(loaded_data)

        return ActionResult.make_failure("OAuth2 authentication flow not completed.")

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

            return self._action_server_as_service
