"""
Tests for the search depth a robot needs to find the matches of a Windows locator
(the Windows Locator warns when it's bigger than the `robocorp-windows` default).
"""

from dataclasses import dataclass, field

from sema4ai_code.inspector.windows.windows_inspector import (
    ROBOT_DEFAULT_SEARCH_DEPTH,
    WindowsInspector,
)

# i.e.: the Filter box of GitHub Desktop (an Electron app) is 19 levels deep.
DEEP_PATH = "|".join(["1"] * 19)


@dataclass
class _LocationInfo:
    path: str


@dataclass
class _Control:
    location_info: _LocationInfo


@dataclass
class _FakeWindow:
    # The paths a robot finds with its default search depth.
    paths_found_by_robot: list[str] = field(default_factory=list)
    searches: list[tuple[str, int]] = field(default_factory=list)

    def find_many(self, locator, search_depth, timeout, search_strategy, **kwargs):
        self.searches.append((locator, search_depth))
        return [_Control(_LocationInfo(p)) for p in self.paths_found_by_robot]


def _robot_search_depth(window, locator, search_depth, matched_paths):
    return WindowsInspector._get_robot_search_depth(
        window, locator, search_depth, "all", matched_paths
    )


def test_no_matches() -> None:
    window = _FakeWindow()
    assert _robot_search_depth(window, "name:Foo", 30, []) is None
    assert not window.searches


def test_search_depth_not_bigger_than_robot_default() -> None:
    window = _FakeWindow()
    paths = ["1|2|3"]
    assert (
        _robot_search_depth(window, "name:Foo", ROBOT_DEFAULT_SEARCH_DEPTH, paths)
        is None
    )
    assert not window.searches


def test_shallow_match_without_chain_needs_no_search() -> None:
    window = _FakeWindow()
    assert _robot_search_depth(window, "name:Foo", 12, ["1|2|3"]) is None
    # The path length is enough to know a robot finds it.
    assert not window.searches


def test_deep_match_without_chain() -> None:
    window = _FakeWindow()
    assert (
        _robot_search_depth(
            window, "control:EditControl and name:Filter", 30, [DEEP_PATH]
        )
        == 19
    )
    assert window.searches == [
        ("control:EditControl and name:Filter", ROBOT_DEFAULT_SEARCH_DEPTH)
    ]


def test_chained_locator_found_by_robot() -> None:
    # The path is relative to the previous part of the locator, so a robot
    # search is needed to know.
    window = _FakeWindow(paths_found_by_robot=["1|2"])
    assert _robot_search_depth(window, "id:Panel > name:Filter", 12, ["1|2"]) is None
    assert window.searches == [("id:Panel > name:Filter", ROBOT_DEFAULT_SEARCH_DEPTH)]


def test_chained_locator_not_found_by_robot() -> None:
    # i.e.: `id:RootWebArea` is 9 levels deep in Electron apps.
    window = _FakeWindow(paths_found_by_robot=[])
    assert (
        _robot_search_depth(
            window, "id:RootWebArea > name:Filter", 12, ["1|1|1|2|3|1|1|2|2|1"]
        )
        == 12
    )


def test_robot_finds_only_some_matches() -> None:
    # `find()` returns the first match: finding one of them is enough.
    window = _FakeWindow(paths_found_by_robot=["1|2"])
    assert (
        _robot_search_depth(window, "id:Panel > name:Foo", 12, ["1|2", "3|4"]) is None
    )


def test_shallow_and_deep_matches_without_chain() -> None:
    # i.e.: `name:"GitHub Desktop"` matches the window's root pane (level 1)
    # and the Electron page (level 9).
    window = _FakeWindow()
    assert (
        _robot_search_depth(
            window, 'name:"GitHub Desktop"', 12, ["2", "|".join(["1"] * 9)]
        )
        is None
    )
    assert not window.searches


def test_all_matches_too_deep_without_chain() -> None:
    # The depth of the shallowest match is enough to find one.
    window = _FakeWindow()
    paths = ["|".join(["1"] * 12), "|".join(["1"] * 10)]
    assert _robot_search_depth(window, "name:Foo", 30, paths) == 10
