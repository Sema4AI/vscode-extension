import re
from dataclasses import dataclass

import pytest


@dataclass
class _JavaWindow:
    title: str
    hwnd: int


def _element_inspector(windows):
    from sema4ai_code.inspector.java.robocorp_java._inspector import ElementInspector

    # Don't start anything (no Java Access Bridge needed): only the locator is tested.
    inspector = object.__new__(ElementInspector)
    inspector.list_windows = lambda: windows  # type: ignore[method-assign]
    return inspector


def _search_params(locator: str) -> dict:
    from sema4ai_code.inspector.windows.robocorp_windows._match_ast import (
        SearchParams,
        collect_search_params,
    )

    # A single level with a single set of search params (i.e.: not split in parts).
    (level,) = collect_search_params(locator)
    (search_params,) = level.parts
    assert isinstance(search_params, SearchParams)
    return dict(search_params.search_params)


def test_window_locator_uses_handle():
    inspector = _element_inspector(
        [_JavaWindow("Other", 111), _JavaWindow("Hello World", 330554)]
    )
    locator = inspector._get_window_locator("Hello World")
    assert locator == "handle:330554"
    assert _search_params(locator) == {"handle": 330554}


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
    inspector = _element_inspector([_JavaWindow("Other", 111)])
    assert _search_params(inspector._get_window_locator(title)) == {"name": title}


@pytest.mark.parametrize(
    "title", ['A "quoted" title', 'name:"x" or (y)', "ends with backslash\\"]
)
def test_window_locator_falls_back_to_regex(title):
    # A `"` can't be inside a quoted locator value: an anchored regex is used.
    inspector = _element_inspector([_JavaWindow("Other", 111)])
    regex = _search_params(inspector._get_window_locator(title))["regex"]
    assert re.match(regex, title)
    assert not re.match(regex, title + " (2)")


def test_window_locator_listing_error_falls_back_to_name():
    from sema4ai_code.inspector.java.robocorp_java._inspector import ElementInspector

    inspector = object.__new__(ElementInspector)

    def list_windows():
        raise RuntimeError("Java Access Bridge error")

    inspector.list_windows = list_windows  # type: ignore[method-assign]
    assert _search_params(inspector._get_window_locator("Hello World")) == {
        "name": "Hello World"
    }
