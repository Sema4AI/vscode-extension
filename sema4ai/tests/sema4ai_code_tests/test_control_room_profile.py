import pytest

US3_PROFILE = """\
name: sema4ai-us3
description: Sema4.ai US3
settings:
  endpoints:
    cloud-api: https://us3.sema4.ai/api/v1/rc/rcc/
    cloud-linking: https://us3.sema4.ai/
    cloud-ui: https://us3.sema4.ai/
    telemetry: https://telemetry.robocorp.com/
    issues: https://telemetry.robocorp.com/
  meta:
    name: sema4ai-us3
    description: Sema4.ai US3
    source: builtin
    version: '2022.09'
"""


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://us3.sema4.ai", "https://us3.sema4.ai"),
        ("us3.sema4.ai", "https://us3.sema4.ai"),
        (
            "  https://us3.sema4.ai/account/access-credentials?x=1  ",
            "https://us3.sema4.ai",
        ),
        ("http://localhost:8080/", "http://localhost:8080"),
    ],
)
def test_normalize_control_room_origin(url, expected):
    from sema4ai_code._language_server_profile import normalize_control_room_origin

    assert normalize_control_room_origin(url) == expected


@pytest.mark.parametrize("url", ["", "   ", "ftp://us3.sema4.ai", "https://"])
def test_normalize_control_room_origin_invalid(url):
    from sema4ai_code._language_server_profile import (
        ProfileDownloadError,
        normalize_control_room_origin,
    )

    with pytest.raises(ProfileDownloadError):
        normalize_control_room_origin(url)


class _Response:
    def __init__(self, status, text):
        self.status = status
        self.text = text


def test_download_rcc_profile(tmpdir, monkeypatch):
    import os

    import sema4ai_http

    from sema4ai_ls_core import uris

    from sema4ai_code._language_server_profile import download_rcc_profile

    requested = []

    def get(url, **kwargs):
        requested.append(url)
        return _Response(200, US3_PROFILE)

    monkeypatch.setattr(sema4ai_http, "get", get)

    result = download_rcc_profile("us3.sema4.ai", str(tmpdir))
    assert requested == ["https://us3.sema4.ai/.well-known/rcc-profile.yaml"]

    file_path = uris.to_fs_path(result["profileUri"])
    assert os.path.normcase(os.path.dirname(file_path)) == os.path.normcase(str(tmpdir))
    with open(file_path, encoding="utf-8") as stream:
        assert stream.read() == US3_PROFILE


def test_download_rcc_profile_not_published(tmpdir, monkeypatch):
    import sema4ai_http

    from sema4ai_code._language_server_profile import (
        ProfileDownloadError,
        download_rcc_profile,
    )

    monkeypatch.setattr(sema4ai_http, "get", lambda url, **kwargs: _Response(404, ""))

    with pytest.raises(ProfileDownloadError, match="HTTP 404"):
        download_rcc_profile("https://example.com", str(tmpdir))
