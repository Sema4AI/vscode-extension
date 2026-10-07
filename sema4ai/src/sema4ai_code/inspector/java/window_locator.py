"""
Builds the (Windows) locator used to find the window of the selected Java application.

Note: kept free of Windows-only imports so that it can be tested on any platform.
"""

from collections.abc import Callable, Iterable
from typing import Any

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


def get_window_locator(
    window_title: str, list_windows: Callable[[], Iterable[Any]]
) -> str:
    """
    Args:
        window_title: The title of the Java window.
        list_windows: Provides the Java windows (objects with `title` and `hwnd`).

    Returns:
        The locator for the window: its handle if it can be found (exact, even
        with duplicated titles), otherwise its name.

    Note: the title can't be used as-is as a locator: i.e.: `Save or Discard`
    would match `name:Save` or `name:Discard` and `File > Open` would be 2 levels.
    """
    try:
        for java_window in list_windows():
            if java_window.title == window_title and java_window.hwnd:
                return f"handle:{java_window.hwnd}"
    except Exception:
        log.exception("Error listing Java windows to get the window handle.")

    # Everything inside quotes is used as-is, but a `"` can't be part of it
    # (and a trailing backslash would escape the closing quote).
    if '"' not in window_title and not window_title.endswith("\\"):
        return f'name:"{window_title}"'

    import re

    pattern = re.escape(window_title).replace('"', ".")
    return f'regex:"^{pattern}$"'
