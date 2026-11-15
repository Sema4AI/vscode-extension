import enum
import typing
from typing import (
    Any,
    List,
    Literal,
    Optional,
    Set,
    TypedDict,
    Union,
)
from collections.abc import Callable, Sequence

from sema4ai_ls_core.callbacks import Callback
from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)

if typing.TYPE_CHECKING:
    from sema4ai_code.inspector.windows.robocorp_windows import (
        ControlElement,
        WindowElement,
    )
    from sema4ai_code.inspector.windows.robocorp_windows._iter_tree import (
        ControlTreeNode,
    )


ControlLocatorInfoTypedDict = TypedDict(
    "ControlLocatorInfoTypedDict",
    {
        "control": str,
        "class": str,
        "name": str,
        "automation_id": str,
        "handle": int,
        "left": int,
        "right": int,
        "top": int,
        "bottom": int,
        "width": int,
        "height": int,
        "xcenter": int,
        "ycenter": int,
        # Relative information based on the query.
        # May be used to recreate the tree-structure
        # afterwards (as APIs usually provide
        # a flat list).
        "depth": int,
        "child_pos": int,
        "path": str,
    },
)


WindowLocatorInfoTypedDict = TypedDict(
    "WindowLocatorInfoTypedDict",
    {
        # Same as control
        "control": str,
        "class": str,
        "name": str,
        "automation_id": str,
        "handle": int,
        "left": int,
        "right": int,
        "top": int,
        "bottom": int,
        "width": int,
        "height": int,
        "xcenter": int,
        "ycenter": int,
        # Note: depth/child_pos/path don't make sense for
        # top-level windows.
        # Additional only in Window
        "pid": int,
        "executable": str,
    },
)


class MatchesAndHierarchyTypedDict(TypedDict):
    # A list with the `path` items matched (these are the ones that the
    # locator matched)
    matched_paths: list[str]
    # This includes all the entries found along with the full hierarchy
    # to reach the matched entries.
    hierarchy: list[ControlLocatorInfoTypedDict]


class HighlightResultTypedDict(MatchesAndHierarchyTypedDict):
    # The search depth with which the matches were found (may be the
    # `fallback_search_depth` if nothing was found with the `search_depth`).
    search_depth: int
    # If a robot wouldn't find any of the matches with the default search depth
    # of `robocorp-windows` (i.e.: `window.find(locator)`), the search depth it
    # needs (otherwise None).
    robot_search_depth: int | None


# The default `search_depth` used by `robocorp-windows` when finding elements
# (i.e.: `window.find(locator)` in a robot).
ROBOT_DEFAULT_SEARCH_DEPTH = 8


def _get_from_obj(el: Union["WindowElement", "ControlElement"], dct_name: str) -> Any:
    from sema4ai_code.inspector.windows.robocorp_windows._ui_automation_wrapper import (
        LocationInfo,
    )

    attr_name = dct_name
    target: Union["WindowElement", "ControlElement", "LocationInfo"] = el
    if attr_name == "control":
        attr_name = "control_type"
    elif attr_name == "class":
        attr_name = "class_name"

    elif dct_name in ("depth", "child_pos", "path"):
        target = el.location_info

    return getattr(target, attr_name)


def to_window_info(w: "WindowElement") -> WindowLocatorInfoTypedDict:
    ret = {}
    for dct_name in WindowLocatorInfoTypedDict.__annotations__:
        ret[dct_name] = _get_from_obj(w, dct_name)
    return typing.cast(WindowLocatorInfoTypedDict, ret)


def to_control_info(el: "ControlElement") -> ControlLocatorInfoTypedDict:
    ret = {}
    for dct_name in ControlLocatorInfoTypedDict.__annotations__:
        ret[dct_name] = _get_from_obj(el, dct_name)
    return typing.cast(ControlLocatorInfoTypedDict, ret)


class IOnPickCallback(typing.Protocol):
    def __call__(self, locator_info_tree: list[ControlLocatorInfoTypedDict]):
        """
        Args:
            locator_info_tree: This will provide the structure from parent to
            child containing the nodes to make the pick (i.e.: the first element
            is the first element inside the window and the last element is
            the leaf element picked).
        """

    def register(
        self, callback: Callable[[list[ControlLocatorInfoTypedDict]], Any]
    ) -> None:
        pass

    def unregister(
        self, callback: Callable[[list[ControlLocatorInfoTypedDict]], Any]
    ) -> None:
        pass


class _State(enum.Enum):
    default = 1
    picking = 2
    highlighting = 3


def to_matches_and_hierarchy(
    parent: "ControlElement", matched_controls: Sequence["ControlElement"]
) -> MatchesAndHierarchyTypedDict:
    from sema4ai_code.inspector.windows.robocorp_windows._inspect import (
        build_parent_hierarchy,
    )

    hierarchy: list[ControlLocatorInfoTypedDict] = []
    matched_paths: list[str] = []

    # Keep the paths already seen.
    already_in_hierarchy: set[str] = set()
    for control in matched_controls:
        path = control.location_info.path
        assert path
        matched_paths.append(path)

        for node in build_parent_hierarchy(control, parent):
            if node.path not in already_in_hierarchy:
                already_in_hierarchy.add(node.path)
                hierarchy.append(to_control_info(node.control))

    return {"matched_paths": matched_paths, "hierarchy": hierarchy}


class WindowsInspector:
    def __init__(self) -> None:
        from sema4ai_code.inspector.windows.robocorp_windows._inspect import (
            ElementInspector,
        )

        # Called as: self.on_pick([ControlLocatorInfoTypedDict])
        self.on_pick: IOnPickCallback = Callback()
        self._element_inspector: ElementInspector | None = None
        self._state = _State.default

    def dispose(self):
        if self._element_inspector is not None:
            self._element_inspector.dispose()
            self._element_inspector = None
        self._state = _State.default

    def set_window_locator(self, window_locator: str):
        """
        Sets the base window which should be inspected.

        Args:
            window_locator: The locator of the window which should be inspected.

        Raises:
            ElementNotFound if the window matching the given locator wasn't found.
        """
        self.dispose()

        from sema4ai_code.inspector.windows.robocorp_windows import find_window
        from sema4ai_code.inspector.windows.robocorp_windows._inspect import (
            ElementInspector,
        )

        # No timeout. The windows must be there already.
        pick_window = find_window(
            window_locator, timeout=0, move_cursor_to_center=False
        )
        self._element_inspector = ElementInspector(control_element=pick_window)

    def _on_internal_pick(self, found: list["ControlTreeNode[ControlElement]"]):
        converted: list[ControlLocatorInfoTypedDict] = []
        for node in found:
            converted.append(to_control_info(node.control))
        self.on_pick(converted)

    def reset_to_default_state(self):
        """
        Will stop any pick or highlight currently in place.
        """
        if self._state == _State.picking:
            self.stop_pick()

        elif self._state == _State.highlighting:
            self.stop_highlight()

    def start_pick(self) -> None:
        """
        Starts picking so that when the cursor is hovered over an item of the
        UI the `on_pick` callback is triggered.

        Args:
            window_locator: The locator of the window which should be picked.

        Raises:
            ElementNotFound if the window matching the given locator wasn't found.
        """

        if self._element_inspector is None:
            return

        self.reset_to_default_state()
        self._state = _State.picking
        self._element_inspector.start_picking(self._on_internal_pick)

    def stop_pick(self) -> None:
        """
        Stops picking.
        """

        if self._state == _State.picking:
            if self._element_inspector is not None:
                self._element_inspector.stop_picking()
            self._state = _State.default

    def start_highlight(
        self,
        locator: str,
        search_depth: int = 8,
        search_strategy: Literal["siblings", "all"] = "all",
        fallback_search_depth: int | None = None,
    ) -> HighlightResultTypedDict:
        """
        Starts highlighting the matches given by the locator specified.

        Args:
            locator: The locator whose matches should be highlighted.
            fallback_search_depth: If given and nothing matches with the
                `search_depth`, the search is retried with this (bigger) depth
                (i.e.: elements deep inside Electron apps).

        Returns:
            The matches found as a flattened list (the tree hierarchy
            may be rebuilt based on the `path` or `depth` and `child_pos`),
            the depth used to find them and the depth a robot needs to find
            them (if bigger than its default).
        """
        if not self._element_inspector:
            raise RuntimeError(
                "Unable to make match because `set_window_locator` was not previously used to set the window of interest."
            )

        self.reset_to_default_state()
        self._state = _State.highlighting
        element_inspector = self._element_inspector
        matched_controls = element_inspector.start_highlight(
            locator,
            search_depth=search_depth,
            timeout=0,
            search_strategy=search_strategy,
        )
        if (
            not matched_controls
            and fallback_search_depth is not None
            and fallback_search_depth > search_depth
        ):
            search_depth = fallback_search_depth
            matched_controls = element_inspector.start_highlight(
                locator,
                search_depth=search_depth,
                timeout=0,
                search_strategy=search_strategy,
            )

        parent = element_inspector.control_element
        matches_and_hierarchy = to_matches_and_hierarchy(parent, matched_controls)
        return {
            "matched_paths": matches_and_hierarchy["matched_paths"],
            "hierarchy": matches_and_hierarchy["hierarchy"],
            "search_depth": search_depth,
            "robot_search_depth": self._get_robot_search_depth(
                parent,
                locator,
                search_depth,
                search_strategy,
                matches_and_hierarchy["matched_paths"],
            ),
        }

    @staticmethod
    def _get_robot_search_depth(
        parent: "ControlElement",
        locator: str,
        search_depth: int,
        search_strategy: Literal["siblings", "all"],
        matched_paths: list[str],
    ) -> int | None:
        """
        Returns:
            None if a robot finds the locator with the default search depth of
            `robocorp-windows` (at least one of the matches: `find()` returns the
            first one), otherwise the search depth it needs.
        """
        if not matched_paths or search_depth <= ROBOT_DEFAULT_SEARCH_DEPTH:
            return None

        # The path of a match is relative to the element found by the previous
        # part of the locator (i.e.: `id:RootWebArea > name:Filter`), so, without
        # a `>` its length is the depth needed to find it.
        min_path_depth = min(len(path.split("|")) for path in matched_paths)
        if ">" not in locator and min_path_depth <= ROBOT_DEFAULT_SEARCH_DEPTH:
            return None

        # Search as a robot would (no highlight) to know whether it'd find them.
        try:
            robot_matches = parent.find_many(
                locator,
                ROBOT_DEFAULT_SEARCH_DEPTH,
                0,
                search_strategy,
                wait_for_element=False,
            )
        except Exception:
            robot_matches = []
        robot_paths = {c.location_info.path for c in robot_matches}
        if any(path in robot_paths for path in matched_paths):
            return None

        # With a `>` each part is searched with the search depth, so, the depth
        # used here is enough (but the total depth isn't known).
        return search_depth if ">" in locator else min_path_depth

    def stop_highlight(self) -> None:
        """
        Stops highlighting matches.
        """
        if self._state == _State.highlighting:
            if self._element_inspector is not None:
                self._element_inspector.stop_highlight()
            self._state = _State.default

    def list_windows(self) -> list[WindowLocatorInfoTypedDict]:
        from sema4ai_code.inspector.windows import robocorp_windows

        windows = robocorp_windows.find_windows("regex:.*", search_depth=1)
        return [to_window_info(w) for w in windows]

    def collect_tree(
        self,
        locator: str,
        search_depth: int = 8,
        search_strategy: Literal["siblings", "all"] = "all",
        fallback_search_depth: int | None = None,
    ) -> MatchesAndHierarchyTypedDict:
        """
        Args:
            fallback_search_depth: If given and nothing matches with the
                `search_depth`, the search is retried with this (bigger) depth.
        """
        if not self._element_inspector:
            raise RuntimeError(
                "Unable to collect tree because `set_window_locator` was not previously used to set the window of interest."
            )
        control_element = self._element_inspector.control_element
        matched_controls: list["ControlElement"] = control_element.find_many(
            locator,
            search_depth=search_depth,
            search_strategy=search_strategy,
            timeout=0,
        )
        if (
            not matched_controls
            and fallback_search_depth is not None
            and fallback_search_depth > search_depth
        ):
            matched_controls = control_element.find_many(
                locator,
                search_depth=fallback_search_depth,
                search_strategy=search_strategy,
                timeout=0,
            )
        return to_matches_and_hierarchy(control_element, matched_controls)

    def shutdown(self):
        if self._element_inspector:
            self._element_inspector.shutdown()
