import os
import urllib.parse
import urllib.request
from pathlib import Path

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


def download_with_resume(url: str, target: Path, make_executable: bool) -> Path:
    """
    Downloads a file from a URL to a target path with resume support.
    """
    import stat

    log.info(f"Downloading '{url}' to '{target}'")

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
    except Exception:
        pass

    chunk_size = 1024 * 5
    with _open_urllib(url) as response:
        content_size = int(response.getheader("Content-Length") or -1)
        try:
            with open(url, "wb") as stream:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        # Note: in a bad connection it can return an empty chunk
                        # even before finishing (so, we resume it afterward if
                        # that was the case).
                        break
                    stream.write(chunk)
        except Exception:
            # Non-resumable case, just raise.
            if content_size <= 0:
                raise
            # Otherwise, keep on going to resume the download if it still
            # hasn't finished.

    MAX_TRIES = 10
    for i in range(MAX_TRIES):
        curr_file_size = _get_file_size(target)

        if content_size > 0:
            # It can be resumed.
            if content_size > curr_file_size:
                log.info(
                    f"Resuming download of '{url}' to '{target}' (downloaded {curr_file_size} of {content_size} (bytes))"
                )
                try:
                    _resume_download(url, target, chunk_size)
                except Exception:
                    if i == MAX_TRIES - 1:
                        raise
            else:
                break
        else:
            # It cannot be resumed: raise if everything wasn't downloaded.
            if content_size > curr_file_size:
                raise RuntimeError(
                    f"Unable to download {url} to {target}. Please retry later."
                )

    if make_executable:
        st = os.stat(target)
        os.chmod(target, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return target


def _open_urllib(url: str, headers=None):
    # Cloudflare seems to be blocking "User-Agent: Python-urllib/3.9".
    # Use a different one as that must be sorted out.
    use_headers = {"User-Agent": "Mozilla"}
    if headers:
        use_headers.update(headers)
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=use_headers), timeout=20
    )


def _get_file_size(filename: str | Path) -> int:
    # Check if file already exists and get downloaded size (if any)
    file_size = 0
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            file_size = os.fstat(f.fileno()).st_size
    return file_size


def _resume_download(url: str, filename: str | Path, chunk_size: int = 1024):
    """Downloads a file in chunks with resume support.

    Args:
        url: The URL of the file to download.
        filename: The filename to save the downloaded file.
        chunk_size: The size of each chunk to download (in bytes).
    """
    downloaded_size = _get_file_size(filename)
    # Set headers for resume download
    headers = {}
    if downloaded_size > 0:
        headers["Range"] = f"bytes={downloaded_size}-"

    with _open_urllib(url, headers) as response, open(filename, "ab") as stream:
        content_size = response.getheader("Content-Length")

        if not content_size:
            raise RuntimeError("Resuming downloads is not supported.")

        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            stream.write(chunk)


class HTTPError(Exception):
    """Custom HTTPError exception to mimic requests' HTTPError."""


class Response:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status
        self.headers = response.headers
        self.url = response.url
        self.reason = response.reason
        self.content = response.read()

    @property
    def text(self):
        return self.content.decode("utf-8")

    def json(self):
        import json

        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code != 200:
            raise HTTPError(f"{self.status_code} {self.reason}, accessing: {self.url}")


def _request(method, url, **kwargs):
    data = kwargs.pop("data", None)
    headers = kwargs.pop("headers", {})
    timeout = kwargs.pop("timeout", None)
    assert kwargs == {}, f"Unexpected kwargs: {kwargs}"

    if data:
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

    with urllib.request.urlopen(req, timeout=timeout) as response:
        return Response(response)


def get(url, **kwargs):
    return _request("GET", url, **kwargs)


def post(url, **kwargs):
    return _request("POST", url, **kwargs)


def put(url, **kwargs):
    return _request("PUT", url, **kwargs)


def delete(url, **kwargs):
    return _request("DELETE", url, **kwargs)
