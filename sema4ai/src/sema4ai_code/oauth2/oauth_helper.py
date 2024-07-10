import os
import ssl
import sys
import wsgiref.simple_server
from concurrent.futures import Future
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional
from wsgiref.simple_server import WSGIServer

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


class _RedirectWSGIApp(object):
    """
    WSGI app to handle the authorization redirect.

    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message: str):
        """
        Args:
            success_message: The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri: Optional[str] = None
        self._success_message = success_message

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[[str, list], Any]
    ) -> list[bytes]:
        """
        Store the requested uri and return a text message.

        Args:
            environ: The WSGI environment.
            start_response: Callable to provide response headers.

        Returns:
            The response body.
        """
        start_response(
            "200 OK",
            [
                ("Content-type", "text/plain; charset=utf-8"),
                (
                    "Cache-Control",
                    "no-store, no-cache, max-age=0, must-revalidate, proxy-revalidate",
                ),
            ],
        )
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]


class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, fmt, *args):
        pass  # No need to log anything.


def _wrap_socket(
    sock,
    keyfile=None,
    certfile=None,
):
    """
    Converts a regular socket into as SSL socket.
    """
    from ssl import SSLContext

    if keyfile and not certfile:
        raise ValueError("certfile must be specified")
    context = SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.verify_mode = ssl.VerifyMode.CERT_NONE
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    return context.wrap_socket(
        sock=sock,
        server_side=True,
        do_handshake_on_connect=True,
        suppress_ragged_eofs=True,
    )


@lru_cache
def _get_action_server_user_sema4_path() -> Path:
    """
    Note: use the same folder as the action server (to reuse the certificate
    that was generated there if available).
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
        home = Path(localappdata) / "sema4ai"
    else:
        # Linux/Mac
        home = Path("~/.sema4ai").expanduser()

    user_sema4_path = home / "action-server"
    user_sema4_path.mkdir(parents=True, exist_ok=True)
    return user_sema4_path


def _start_server(
    host: str = "localhost",
    port: int = 4444,
    *,
    use_https: bool = False,
    ssl_self_signed: bool = False,
    ssl_keyfile: Optional[str] = None,
    ssl_certfile: Optional[str] = None,
    show_message: str = "Ok, it worked.",
) -> tuple[WSGIServer, _RedirectWSGIApp, str]:
    """
    Args:
        keyfile:
            Required if SSL is required.
        certfile:
            Required if SSL is required.

    Returns:
        The server the app and the address for the server (the server
        is not actually handling requests at this point).
    """
    wsgiref.simple_server.WSGIServer.allow_reuse_address = False
    wsgi_app = _RedirectWSGIApp(show_message)

    local_server = wsgiref.simple_server.make_server(
        host, port, wsgi_app, handler_class=_WSGIRequestHandler
    )

    protocol = "https" if use_https else "http"

    if use_https:
        if not ssl_self_signed:
            if not ssl_keyfile or not ssl_certfile:
                raise RuntimeError(
                    "When use_https is used, either `ssl_self_signed` must be passed or the `ssl_keyfile` and `ssl_certfile` arguments must be provided."
                )
        else:
            if ssl_keyfile or ssl_certfile:
                raise RuntimeError(
                    "When `ssl_self_signed`is passed `ssl_keyfile` and `ssl_certfile` should not be provided (a key/certificate will be generated in the default location)."
                )

    if use_https:
        if ssl_self_signed:
            from sema4ai_code.oauth2 import _gen_certificate

            user_path = _get_action_server_user_sema4_path()

            # Note: Same paths from the action server.

            private_path = user_path / "action-server-private-keyfile.pem"
            public_path = user_path / "action-server-public-certfile.pem"

            public, private = _gen_certificate.gen_self_signed_certificate()

            public_path.write_bytes(public)
            private_path.write_bytes(private)

            KEY_FILE_PERMISSIONS = 0o600
            private_path.chmod(KEY_FILE_PERMISSIONS)
            ssl_keyfile = str(private_path)
            ssl_certfile = str(public_path)
        else:
            # Note: this was already previously checked.
            assert ssl_keyfile and ssl_certfile

        # Wrap the server with SSL
        local_server.socket = _wrap_socket(
            local_server.socket,
            keyfile=ssl_keyfile,
            certfile=ssl_certfile,
        )

    address = f"{protocol}://{host}:{port}"
    return local_server, wsgi_app, address


def start_server_in_thread(**kwargs) -> Future[str]:
    """
    Calls `_start_server` with the passed args in a thread and returns
    a future which returns the last uri accessed.

    If the returned `Future` is cancelled, the server is also closed.
    """
    import threading

    fut: Future[str] = Future()

    def method() -> None:
        try:
            # Start the server
            local_server, app, address = _start_server(**kwargs)

            def on_done(*args, **kwargs):
                # Close when done (either cancelled or in regular flow)
                local_server.server_close()

            fut.add_done_callback(on_done)

            log.info(f"Serving OAuth2 redirect server on {address}")

            local_server.handle_request()  # serve one request, then exit
            # local_server.serve_forever()

            if not fut.cancelled():
                if app.last_request_uri:
                    fut.set_result(app.last_request_uri)
                else:
                    fut.set_exception(
                        RuntimeError("last_request_uri not set in request")
                    )
        except BaseException as e:
            if not fut.cancelled():
                fut.set_exception(e)

    t = threading.Thread(target=method, name="OAuth2 Server")
    t.start()
    return fut


if __name__ == "__main__":
    last_request = start_server_in_thread()
    last_request.cancel()
    print("last uri", last_request.result())
