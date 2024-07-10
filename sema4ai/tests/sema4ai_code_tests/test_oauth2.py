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
    from sema4ai_code.oauth2 import oauth_helper

    port = find_free_port()
    future = oauth_helper.start_server_in_thread(port=port)
    result = requests.get(f"http://localhost:{port}/foo/bar")
    result.raise_for_status()
    last_uri = future.result(timeout=10)
    assert last_uri == f"http://localhost:{port}/foo/bar"


def test_oauth2_server_cancel():
    from requests.exceptions import ConnectTimeout, ReadTimeout

    from sema4ai_code.oauth2 import oauth_helper

    port = find_free_port()
    future = oauth_helper.start_server_in_thread(port=port)
    time.sleep(1)
    future.cancel()

    with pytest.raises(CancelledError):
        future.result()

    with pytest.raises((ConnectTimeout, ReadTimeout)):
        requests.get(f"http://localhost:{port}/foo/bar", timeout=1)
