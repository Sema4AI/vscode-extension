import socket
import time
from concurrent.futures import CancelledError

import pytest
import requests


def find_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def test_oauth2_server_basic():
    from sema4ai_code.vendored_deps.url_callback_server import start_server_in_thread

    last_request, reserved_address = start_server_in_thread(port=0)
    address = reserved_address.result(timeout=10)

    result = requests.post(f"{address}/foo/bar")
    result.raise_for_status()
    last_uri = last_request.result(timeout=10)
    assert last_uri == {"uri": f"{address}/foo/bar", "body": ""}


def test_oauth2_server_cancel():
    from requests.exceptions import ConnectTimeout, ReadTimeout

    from sema4ai_code.vendored_deps.url_callback_server import start_server_in_thread

    last_request, reserved_address = start_server_in_thread(port=0)
    address = reserved_address.result(5)
    last_request.cancel()
    time.sleep(0.2)

    with pytest.raises(CancelledError):
        last_request.result(1)

    with pytest.raises((ConnectTimeout, ReadTimeout)):
        requests.post(f"{address}/foo/bar", timeout=1)
