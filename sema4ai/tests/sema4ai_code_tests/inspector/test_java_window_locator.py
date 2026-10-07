import re
import sys
from dataclasses import dataclass

import pytest

from sema4ai_code.inspector.java.window_locator import get_window_locator


@dataclass
class _JavaWindow:
    title: str
    hwnd: int


def _check_parsed(locator: str, expected: dict) -> None:
    """
    Checks that the locator is parsed by robocorp_windows to the expected search
    params (in a single level and a single part, i.e.: not split by `and`, `or`,
    parenthesis or `>`).
    """
    if sys.platform != "win32":
        return  # robocorp_windows can only be imported on Windows.

    from sema4ai_code.inspector.windows.robocorp_windows._match_ast import (
        SearchParams,
        collect_search_params,
    )

    (level,) = collect_search_params(locator)
    (search_params,) = level.parts
    assert isinstance(search_params, SearchParams)
    assert dict(search_params.search_params) == expected


def test_window_locator_uses_handle():
    windows = [_JavaWindow("Other", 111), _JavaWindow("Hello World", 330554)]
    locator = get_window_locator("Hello World", lambda: windows)
    assert locator == "handle:330554"
    _check_parsed(locator, {"handle": 330554})


@pytest.mark.parametrize(
    "title",
    [
        "Hello World",
        "Search and Replace",
        "Save or Discard",
        "Settings (Advanced)",
        "File > Open",
        "name:x is not a locator",
        "C:\\path\\to\\file - Editor",
        "single",
    ],
)
def test_window_locator_falls_back_to_quoted_name(title):
    # i.e.: the window is no longer listed: match the whole title by name (most of
    # these don't work as a locator as-is).
    locator = get_window_locator(title, lambda: [_JavaWindow("Other", 111)])
    assert locator == f'name:"{title}"'
    _check_parsed(locator, {"name": title})


@pytest.mark.parametrize(
    "title", ['A "quoted" title', 'name:"x" or (y)', "ends with backslash\\"]
)
def test_window_locator_falls_back_to_regex(title):
    # A `"` can't be inside a quoted locator value: an anchored regex is used.
    locator = get_window_locator(title, lambda: [_JavaWindow("Other", 111)])
    assert locator.startswith('regex:"') and locator.endswith('"')
    regex = locator[len('regex:"') : -1]
    assert '"' not in regex
    assert re.match(regex, title)
    assert not re.match(regex, title + " (2)")
    _check_parsed(locator, {"regex": regex})


def test_window_locator_listing_error_falls_back_to_name():
    def list_windows():
        raise RuntimeError("Java Access Bridge error")

    assert get_window_locator("Hello World", list_windows) == 'name:"Hello World"'
