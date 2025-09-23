import enum
import typing
import weakref
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar

from sema4ai_ls_core.core_log import get_logger

if typing.TYPE_CHECKING:
    from tree_sitter import Node, Tree

    from .list_actions_from_agent import ActionPackageInFilesystem


log = get_logger(__name__)


def is_valid_semver_version(version: str) -> bool:
    import re

    SEMVER_REGEX = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
    )

    return SEMVER_REGEX.match(version) is not None


class _ExpectedTypeEnum(Enum):
    object = "object"
    string = "string"
    enum = "enum"
    file = "file"
    list = "list"
    bool = "bool"
    int = "int"
    float = "float"
    NOT_SET = "NOT_SET"  # Should be set only when deprecated is true.
    action_package_version_link = "action_package_version_link"
    action_package_name_link = "action_package_name_link"
    zip_or_folder_based_on_path = "zip_or_folder_based_on_path"
    agent_semver_version = "agent_semver_version"
    mcp_server_url = "mcp_server_url"
    mcp_server_transport = "mcp_server_transport"
    mcp_server_command_line = "mcp_server_command_line"
    mcp_server_env = "map[string,object]#mcp_server_env"
    mcp_server_headers = "map[string,object]#mcp_server_headers"
    mcp_server_cwd = "mcp_server_cwd"
    mcp_server_var_type = "mcp_server_var_type"
    mcp_server_tools = "mcp_server_tools"
    map_string_object = "map[string,object]"
    version_v2 = "version_v2"
    dynamic_object = "dynamic_object"


class _YamlNodeKind(Enum):
    # 'unhandled' is the default (when we find the actual type afterwards it's set
    # -- if not there it's probably an object or something we didn't expect, and that's ok,
    # but it may also signal we need some additional heuristic to determin the actual type).
    unhandled = "unhandled"

    list = "list"
    list_item = "list-item"
    bool = "bool"
    int = "int"
    float = "float"
    string = "string"


class ErrorCode(Enum):
    action_package_info_unsynchronized = "action_package_info_unsynchronized"
    agent_package_incomplete = "agent_package_incomplete"
    zipped_action_inside_unzipped_agent = "zipped_action_inside_unzipped_agent"


@dataclass
class _ExpectedType:
    expected_type: _ExpectedTypeEnum  # May be "object", "string", "enum", "file", "list" (implies "list[object]"), or "bool".

    # If a "string" type, the recommended values may be provided
    # (this means that any string value is accepted, but the recommended values can be used to help the user).
    recommended_values: list[str] | None = None

    # If an "enum" type, the accepted values should be provided.
    enum_values: list[str] | None = None

    # If a "file" type, the relative path to the file (based on the agent root dir) should be provided.
    relative_to: str | None = None

    def __post_init__(self) -> None:
        if self.expected_type == "file":
            assert self.relative_to is not None, (
                "relative_to must be provided for file type."
            )

        if self.expected_type == "enum":
            assert self.enum_values is not None, (
                "enum_values must be provided for enum type."
            )


@dataclass
class Entry:
    # The path to the key in the YAML spec (i.e.: "agent-package/agents/name")
    path: str

    # The description of the key in the YAML spec.
    description: str

    # The expected type of the key in the YAML spec.
    expected_type: _ExpectedType

    # Whether the key is required (default is true).
    required: bool = True

    # Whether the key is deprecated.
    deprecated: bool = False


class RootHasNoDataError(Exception):
    pass


def load_spec(json_spec: dict[str, Any]) -> dict[str, Entry]:
    ret: dict[str, Entry] = {}

    for path, value in json_spec.items():
        try:
            expected_type: dict | None | str = "<unknown>"
            assert isinstance(value, dict), (
                f"Invalid spec: {path}. Expected a dictionary. Found {type(value)}"
            )

            value = value.copy()
            deprecated = value.pop("deprecated", False)
            required = value.pop("required", False)
            expected_type = value.pop("expected-type", None)
            description = value.pop("description", None)
            value.pop("note", None)  # Used to add comments.
            if not description:
                raise Exception(f"Invalid spec: {path}. Expected a description.")

            if isinstance(expected_type, dict):
                recommended_values = expected_type.get("recommended-values", None)
                enum_values = expected_type.get("values", None)
                relative_to = expected_type.get("relative-to", None)
                expected_type = expected_type.get("type", None)
            else:
                recommended_values = None
                enum_values = None
                relative_to = None

            if value:
                raise Exception(f"Invalid spec: {path}. Unexpected keys: {value}")

            if expected_type is None:
                expected_type_enum = _ExpectedTypeEnum.NOT_SET
            else:
                expected_type_enum = _ExpectedTypeEnum(expected_type)

            ret[path] = Entry(
                path=path,
                description=description,
                expected_type=_ExpectedType(
                    expected_type=expected_type_enum,
                    recommended_values=recommended_values,
                    enum_values=enum_values,
                    relative_to=relative_to,
                ),
                required=required,
                deprecated=deprecated,
            )
        except Exception:
            raise Exception(
                f"Invalid spec: {path}. Expected type {expected_type} is not a valid expected type."
            )
    return ret


T = TypeVar("T")


class Severity(enum.Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


def _create_range_from_location(
    start_line: int,
    start_col: int,
    end_line: int | None = None,
    end_col: int | None = None,
) -> dict:
    """
    If the end_line and end_col aren't passed we consider
    that the location should go up until the end of the line.
    """
    if end_line is None:
        assert end_col is None
        end_line = start_line + 1
        end_col = 0
    assert end_col is not None
    dct: dict = {
        "start": {
            "line": start_line,
            "character": start_col,
        },
        "end": {
            "line": end_line,
            "character": end_col,
        },
    }
    return dct


@dataclass
class Error:
    message: str
    node: Optional["Node"] = None
    code: ErrorCode | None = None
    severity: Severity = Severity.critical

    def as_diagostic(self, agent_node) -> dict:
        from collections.abc import Sequence

        use_location: Sequence[int]
        error = self

        if not error.node:
            use_location = (0, 0, 1, 0)
            if agent_node is not None:
                if agent_node.key.location:
                    use_location = agent_node.key.location
        else:
            start_line, start_col = (
                error.node.start_point.row,
                error.node.start_point.column,
            )
            end_line, end_col = (
                error.node.end_point.row,
                error.node.end_point.column,
            )
            use_location = start_line, start_col, end_line, end_col

        use_range = _create_range_from_location(*use_location)

        if error.severity == Severity.critical:
            severity = 1
        elif error.severity == Severity.warning:
            severity = 2
        elif error.severity == Severity.info:
            severity = 3
        else:
            raise RuntimeError(f"Unexpected severity: {error.severity}")

        diagnostic = {
            "range": use_range,
            "severity": severity,
            "source": "sema4ai",
            "message": error.message,
        }

        if error.code:
            diagnostic["code"] = error.code.value
        return diagnostic


class TreeNode(Generic[T]):
    _parent: weakref.ref["TreeNode[T]"] | None = None

    def __init__(self, name: str, parent: Optional["TreeNode[T]"] = None):
        self.name = name
        self._children: dict[str, "TreeNode[T]"] = {}
        self._data: T | None = None
        if parent:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None

    def pretty(self, level: int = 0) -> str:
        level_str = "  " * level
        ret = f"{level_str}{self.name}{self._pretty_data()}\n"
        for child in self._children.values():
            ret += child.pretty(level + 1)
        return ret

    def _pretty_data(self) -> str:
        return ""

    @property
    def data(self) -> T:
        if self._data is None:
            raise RootHasNoDataError(f"Data not set for {self.name}.")
        return self._data

    @property
    def parent(self) -> Optional["TreeNode[T]"]:
        if self._parent:
            return self._parent()
        return None

    def obtain(self, name: str, data: T) -> "TreeNode[T]":
        assert "/" not in name, f"Did not expect / to be in {name}."
        child = self._children.get(name)
        if child is None:
            child = self.__class__(name, self)
            self._children[name] = child
            child._data = data
        return child

    def __str__(self) -> str:
        cls = self.__class__.__name__
        return f"{cls}({self.name})"

    __repr__ = __str__


class _SpecTreeNode(TreeNode[Entry]):  # Subclass is just for typing
    def obtain(self, name: str, data: Entry) -> "_SpecTreeNode":
        return typing.cast("_SpecTreeNode", super().obtain(name, data))

    @property
    def parent(self) -> Optional["_SpecTreeNode"]:
        if self._parent:
            return typing.cast("_SpecTreeNode", self._parent())
        return None

    @property
    def children(self) -> dict[str, "_SpecTreeNode"]:
        return typing.cast(dict[str, "_SpecTreeNode"], self._children)

    def _pretty_data(self) -> str:
        if self._data is None:
            return " (no data)"

        ret = ""
        if self._data.required:
            ret += " (required)"
        if self._data.deprecated:
            ret += " (deprecated)"
        return ret


class YamlNodeData:
    def __init__(
        self,
        node: "Node",
        kind: _YamlNodeKind,
    ) -> None:
        self.node = node
        self.kind = kind


class _YamlTreeNode(TreeNode[YamlNodeData]):  # Subclass is just for typing
    def obtain(self, name: str, data: YamlNodeData) -> "_YamlTreeNode":
        return typing.cast("_YamlTreeNode", super().obtain(name, data))

    @property
    def parent(self) -> Optional["_YamlTreeNode"]:
        if self._parent:
            return typing.cast("_YamlTreeNode", self._parent())
        return None

    @property
    def children(self) -> dict[str, "_YamlTreeNode"]:
        return typing.cast(dict[str, "_YamlTreeNode"], self._children)

    def _pretty_data(self) -> str:
        if self._data is None:
            return " (no data)"
        return f" ({self._data.kind.value})"


def _convert_flattened_to_nested(flattened: dict[str, Entry]) -> _SpecTreeNode:
    """
    Converts a flattened dictionary of entries into a nested tree of _SpecTreeNode objects
    (the idea is that we convert the flattened structure of the spec into a tree which
    will be traversed to validate the yaml contents).
    """
    root = _SpecTreeNode("root")
    for path, entry in flattened.items():
        curr = root
        parts = path.split("/")
        for part in parts:
            curr = curr.obtain(part, entry)
    return root


class InvalidSpec(Exception):
    pass


def validate_from_spec(
    spec_entries: dict[str, Entry],
    yaml_spec_contents: str,
    agent_root_dir: Path,
    raise_on_error: bool = True,
) -> tuple[Error, ...]:
    """
    Validate the YAML agent spec against the JSON agent spec.

    Note: the yaml should've been already pre-loaded with yaml.safe_load
    and the parsing should be correct. At this point the validation will
    be done with tree-sitter (which may not catch syntax errors).

    Params:
        spec_entries: The spec entries as a dictionary (previously loaded from load_spec with the correct version).
        yaml_spec_contents: The YAML agent spec contents as a string.
        agent_root_dir: The root directory of the agent package (contains the agent-spec.yaml file).

    Raises:
        InvalidSpec: If the YAML agent spec is invalid.
    """

    validator = Validator(spec_entries, agent_root_dir)
    tree = tree_sitter_parse_yaml(yaml_spec_contents)
    errors: tuple[Error, ...] = tuple(validator.validate(tree.root_node))
    if errors and raise_on_error:
        msg = "\n".join(e.message for e in errors)
        raise InvalidSpec(msg)
    return tuple(sorted(errors, key=lambda e: e.message))


def tree_sitter_parse_yaml(yaml_spec_contents: str) -> "Tree":
    import tree_sitter_yaml
    from tree_sitter import Language, Parser

    language = tree_sitter_yaml.language()
    parser = Parser(Language(language))
    contents = yaml_spec_contents.encode("utf8", errors="replace")
    tree = parser.parse(contents, encoding="utf8")
    return tree


class Validator:
    PRINT_YAML_TREE = False

    def __init__(self, spec_entries: dict[str, Entry], agent_root_dir: Path) -> None:
        """
        Params:
            spec_entries: The spec entries as a dictionary. Keys are the paths to the keys in the json spec.
                i.e.: "agent-package/agents/name".
            agent_root_dir: The root directory of the agent package (contains the agent-spec.yaml file).
        """
        self._spec_entries = spec_entries
        self._stack: list[str] = []
        self._current_stack_as_str = ""
        self._agent_root_dir = agent_root_dir

        # During the validation, the yaml parse will be used to create a tree with the actual
        # yaml content to be validated (the first pass is doing a validation of the nodes that exist
        # in the yaml, while also creating the tree with the actual contents and the second pass is
        # doing the actual validation from the spec checking that the nodes exist and have the correct info).
        self._yaml_info_loaded = _YamlTreeNode("root")
        self._yaml_cursor_node: _YamlTreeNode = self._yaml_info_loaded
        self._action_packages_found_in_filesystem: dict[
            Path, "ActionPackageInFilesystem"
        ] = {}

    def _validate_key_pair(
        self, key_node: "Node", value_node: Optional["Node"]
    ) -> Iterator[Error]:
        entry = self._spec_entries.get(self._current_stack_as_str)
        if not entry:
            # Ok, we haven't been able to find the entry in the spec as is. This may be due to
            # map[string,object]#<type> or map[string,object] fields.
            # We have to check the curren stack to see if there is a path which is a map[string,object]#<type>
            # or map[string,object] field.
            # If so, we have to remove the the related part and re-validate the path without that part.
            # For example, if the current stack is:
            # agent-package/agents/mcp-servers/headers/my-object/my-field
            # we have to remove the my-object part and validate the path without that part.
            # So, the new path will be:
            # agent-package/agents/mcp-servers/headers/my-field

            current_stack_as_str = []
            skip_next = False
            for part in self._current_stack_as_str.split("/"):
                if skip_next:
                    skip_next = False
                    continue
                current_stack_as_str.append(part)
                parent_entry = self._spec_entries.get("/".join(current_stack_as_str))
                if parent_entry:
                    if parent_entry.expected_type.expected_type.value.startswith(
                        "map[string,object]"
                    ):
                        skip_next = True
                    elif (
                        parent_entry.expected_type.expected_type.value
                        == "dynamic_object"
                    ):
                        # i.e.: we have a dynamic_object and we are validating a field inside it.
                        # In this case, we can ignore the fact that the field is not defined.
                        return

            entry = self._spec_entries.get("/".join(current_stack_as_str))

        if not entry:
            parent_as_str = "<unknown>"
            curr = "<unknown>"

            if self._stack:
                parent, curr = self._stack[:-1], self._stack[-1]
                if parent:
                    parent_as_str = "/".join(parent)
                else:
                    parent_as_str = "root"

            if not entry:
                yield Error(
                    message=f"Unexpected entry: {curr} (in {parent_as_str}).",
                    node=key_node,
                    severity=Severity.warning,
                )

        # Note: not having a value is ok (i.e.: empty object).

    def _is_scalar_node(self, node: Optional["Node"]) -> bool:
        if node is None:
            return False
        if node.type == "flow_node":
            children = node.children
            if len(children) == 1:
                c1 = children[0]
                if c1.type == "plain_scalar":
                    if len(c1.children) == 1:
                        c2 = c1.children[0]
                        if c2.type == "string_scalar":
                            return True
        return False

    def _validate_nodes_exist_and_build_yaml_info(
        self, node: "Node"
    ) -> Iterator[Error]:
        # level = len(self._stack)
        # print("  " * level, node.type, node.start_point.row)
        added_to_stack = False
        changed_yaml_cursor = False
        default_visit_children = True

        if node.type in ("block_sequence_item", "flow_node"):
            changed_yaml_cursor = True
            use_key_name = f"list-item-{len(self._yaml_cursor_node.children)}"
            self._yaml_cursor_node = self._yaml_cursor_node.obtain(
                use_key_name, YamlNodeData(node, kind=_YamlNodeKind.list_item)
            )

        elif node.type in ("flow_sequence", "block_sequence"):
            self._yaml_cursor_node.data.kind = _YamlNodeKind.list

        elif node.type in (
            "string_scalar",
            "double_quote_scalar",
            "single_quote_scalar",
        ):
            self._yaml_cursor_node.data.kind = _YamlNodeKind.string

        elif node.type == "boolean_scalar":
            self._yaml_cursor_node.data.kind = _YamlNodeKind.bool

        elif node.type == "integer_scalar":
            self._yaml_cursor_node.data.kind = _YamlNodeKind.int

        elif node.type == "float_scalar":
            self._yaml_cursor_node.data.kind = _YamlNodeKind.float

        elif node.type == "block_mapping_pair":
            key = node.child_by_field_name("key")
            value = node.child_by_field_name("value")
            if self._is_scalar_node(key):
                assert key is not None, "Expected key from tree sitter."
                assert key.text, "Expected key text from tree sitter."
                key_name = key.text.decode("utf8")
                self._stack.append(key_name)
                self._current_stack_as_str = "/".join(self._stack)

                changed_yaml_cursor = True
                self._yaml_cursor_node = self._yaml_cursor_node.obtain(
                    key_name, YamlNodeData(node, kind=_YamlNodeKind.unhandled)
                )

                yield from self._validate_key_pair(key, value)
                added_to_stack = True
                default_visit_children = False

                if value:
                    for child in value.children:
                        yield from self._validate_nodes_exist_and_build_yaml_info(child)

        if default_visit_children:
            for child in node.children:
                yield from self._validate_nodes_exist_and_build_yaml_info(child)

        if added_to_stack:
            self._stack.pop()
            self._current_stack_as_str = "/".join(self._stack)

        if changed_yaml_cursor:
            parent = self._yaml_cursor_node.parent
            assert parent is not None, "Expected parent to be loaded."
            self._yaml_cursor_node = parent

    def _verify_yaml_matches_spec(
        self,
        spec_node: _SpecTreeNode,
        yaml_node: _YamlTreeNode | None,
        parent_node: _YamlTreeNode | None,
    ) -> Iterator[Error]:
        from typing import Literal

        if spec_node.parent is None:
            assert yaml_node is not None, "Expected yaml node to be provided for root."
            for child in spec_node.children.values():
                yield from self._verify_yaml_matches_spec(
                    child, yaml_node.children.get(child.name), yaml_node
                )
            return

        assert spec_node.data is not None, (
            f"Expected data to be loaded. Name: {spec_node.name}. Parent: {spec_node.parent}"
        )

        if spec_node.data.required:
            if yaml_node is None:
                try:
                    data = parent_node.data if parent_node else None
                except RootHasNoDataError:
                    data = None
                yield Error(
                    message=f"Missing required entry: {spec_node.data.path}.",
                    node=data.node if data else None,
                    code=ErrorCode.agent_package_incomplete,
                )

        if yaml_node is None:
            # Unable to proceed the validation for this node as the yaml info was not found.
            return
        else:
            # print(
            #     f"--- {spec_node.data.path} {spec_node.data.expected_type.expected_type} ---"
            # )
            # Ok, the node exists. Let's validate it.
            if spec_node.data.deprecated:
                yield Error(
                    message=f"Deprecated: {spec_node.data.path!r}. {spec_node.data.description}.",
                    node=yaml_node.data.node,
                )

            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.object:
                for child in spec_node.children.values():
                    yield from self._verify_yaml_matches_spec(
                        child, yaml_node.children.get(child.name), yaml_node
                    )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.version_v2
            ):
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    version = self._get_value_text(yaml_node)
                    if version and version != "v2":
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be 'v2' (validation will proceed considering v2 spec, unexpected nodes will be reported as warnings and the related functionality will be disabled). Found: {version}",
                            node=yaml_node.data.node,
                            severity=Severity.warning,
                        )

            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.list:
                if yaml_node.data.kind != _YamlNodeKind.list:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a list.",
                        node=yaml_node.data.node,
                    )
                else:
                    for list_item_node in yaml_node.children.values():
                        for spec_child in spec_node.children.values():
                            child_node = list_item_node.children.get(spec_child.name)
                            yield from self._verify_yaml_matches_spec(
                                spec_child, child_node, yaml_node
                            )
            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.string:
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.agent_semver_version
            ):
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    version = self._get_value_text(yaml_node)
                    if version:
                        # We're dealing with tree sitter, so, we may need to remove the quotes.
                        if version.startswith('"') and version.endswith('"'):
                            version = version[1:-1]
                        if version.startswith("'") and version.endswith("'"):
                            version = version[1:-1]
                    if version and not is_valid_semver_version(version):
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be a valid semantic version (found {version!r}).",
                            node=yaml_node.data.node,
                        )
            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_transport
            ):
                # Must check that:
                # - It's a string
                # - It must be either 'streamable-http', 'sse' or 'stdio'
                # - If it's 'streamable-http' or 'sse', the 'url' field must be defined.
                # - If it's 'stdio', the 'command-line' field must be defined.
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    transport = self._get_value_text(yaml_node)
                    if transport not in ["streamable-http", "sse", "stdio", "auto"]:
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be one of ['streamable-http', 'sse', 'stdio'] (found {transport!r}).",
                            node=yaml_node.data.node,
                        )
                    else:
                        if transport in ("streamable-http", "sse"):
                            if (
                                not yaml_node.parent
                                or "url" not in yaml_node.parent.children
                            ):
                                yield Error(
                                    message=f"{spec_node.data.path}: When the transport is 'streamable-http' or 'sse', the url must be defined.",
                                    node=yaml_node.data.node,
                                )
                        elif transport == "stdio":
                            if (
                                not yaml_node.parent
                                or "command-line" not in yaml_node.parent.children
                            ):
                                yield Error(
                                    message=f"{spec_node.data.path}: When the transport is 'stdio', the command-line must be defined.",
                                    node=yaml_node.data.node,
                                )
                        elif transport == "auto":
                            # Check that either the url or command-line field is defined.
                            if not yaml_node.parent or (
                                "url" not in yaml_node.parent.children
                                and "command-line" not in yaml_node.parent.children
                            ):
                                yield Error(
                                    message=f"{spec_node.data.path}: When the transport is 'auto', either the url or command-line field must be defined.",
                                    node=yaml_node.data.node,
                                )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_url
            ):
                # Must check that:
                # - It must be a string
                # - The 'command-line' field is not defined (it's either 'command-line' or 'url').
                # - If the `transport` field is defined, it must be one of the following: 'streamable-http' or 'sse'.
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    # Check that 'command-line' field is not defined (mutual exclusivity)
                    if yaml_node.parent and "command-line" in yaml_node.parent.children:
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be mutually exclusive with 'command-line' field.",
                            node=yaml_node.data.node,
                        )

                    # Check transport field if it exists
                    if yaml_node.parent and "transport" in yaml_node.parent.children:
                        transport_node = yaml_node.parent.children["transport"]
                        transport_value = self._get_value_text(transport_node)
                        if transport_value not in ["streamable-http", "sse", "auto"]:
                            yield Error(
                                message=f"Expected transport field to be one of ['streamable-http', 'sse', 'auto'] when using 'url' field (found {transport_value!r}).",
                                node=transport_node.data.node,
                            )

            elif spec_node.data.expected_type.expected_type in (
                _ExpectedTypeEnum.mcp_server_headers,
                _ExpectedTypeEnum.mcp_server_env,
                _ExpectedTypeEnum.map_string_object,
            ):
                accept_direct_string = False
                if (
                    spec_node.data.expected_type.expected_type
                    == _ExpectedTypeEnum.mcp_server_headers
                ):
                    accept_direct_string = True
                    # Must check that:
                    # - It must be an object
                    # - The 'url' field is also defined.
                    if yaml_node.data.kind == _YamlNodeKind.unhandled:
                        # Check that 'url' field is also defined
                        if (
                            not yaml_node.parent
                            or "url" not in yaml_node.parent.children
                        ):
                            yield Error(
                                message=f"Expected {spec_node.data.path} to be used together with 'url' field.",
                                node=yaml_node.data.node,
                            )
                elif (
                    spec_node.data.expected_type.expected_type
                    == _ExpectedTypeEnum.mcp_server_env
                ):
                    accept_direct_string = True
                    # Must check that:
                    # - It must be an object
                    # - The 'command-line' field is defined
                    if yaml_node.data.kind == _YamlNodeKind.unhandled:
                        # Check that 'command-line' field is defined
                        if (
                            not yaml_node.parent
                            or "command-line" not in yaml_node.parent.children
                        ):
                            yield Error(
                                message=f"Expected {spec_node.data.path} to be used together with 'command-line' field.",
                                node=yaml_node.data.node,
                            )

                if yaml_node.data.kind != _YamlNodeKind.unhandled:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be an object (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    # For all (map[string,object] or map[string,object]#<type>)
                    # Validate that all values are strings or objects (with the according type).
                    for value in yaml_node.children.values():
                        if (
                            accept_direct_string
                            and value.data.kind == _YamlNodeKind.string
                        ):
                            pass  # Ok, it's a string, no need of further validation

                        elif value.data.kind != _YamlNodeKind.unhandled:
                            if accept_direct_string:
                                msg = f"Expected all items in {spec_node.data.path} to be strings or objects. Found {value.data.kind.value}."
                            else:
                                msg = f"Expected all items in {spec_node.data.path} to be objects. Found {value.data.kind.value}."
                            yield Error(
                                message=msg,
                                node=value.data.node,
                            )
                        else:
                            for spec_child in spec_node.children.values():
                                child_node = value.children.get(spec_child.name)
                                if child_node:
                                    yield from self._verify_yaml_matches_spec(
                                        spec_child, child_node, yaml_node
                                    )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_tools
            ):
                # - It must be a list of strings
                if yaml_node.data.kind == _YamlNodeKind.list:
                    for list_item_node in yaml_node.children.values():
                        if list_item_node.data.kind != _YamlNodeKind.list_item:
                            yield Error(
                                message=f"Expected all items in {spec_node.data.path} to be list items.",
                                node=list_item_node.data.node,
                            )
                        else:
                            for item_node in list_item_node.children.values():
                                if item_node.data.kind != _YamlNodeKind.string:
                                    yield Error(
                                        message=f"Expected all items in {spec_node.data.path} to be strings. Found: {item_node.data.kind.value}",
                                        node=item_node.data.node,
                                    )

                else:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a list of strings (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_command_line
            ):
                # Must check that:
                # - It must be a list of strings
                # - The 'url' field is not defined (it's either 'command-line' or 'url').
                # - If the `transport` field is defined, it must be 'stdio'.
                if yaml_node.data.kind != _YamlNodeKind.list:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a list (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    # Check that 'url' field is not defined (mutual exclusivity)
                    if yaml_node.parent and "url" in yaml_node.parent.children:
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be mutually exclusive with 'url' field.",
                            node=yaml_node.data.node,
                        )

                    # Check transport field if it exists
                    if yaml_node.parent and "transport" in yaml_node.parent.children:
                        transport_node = yaml_node.parent.children["transport"]
                        transport_value = self._get_value_text(transport_node)
                        if transport_value != "stdio" and transport_value != "auto":
                            yield Error(
                                message=f"Expected transport field to be 'stdio' or 'auto' when using 'command-line' field (found {transport_value!r}).",
                                node=transport_node.data.node,
                            )

                    # Validate that all list items are strings
                    for list_item_node in yaml_node.children.values():
                        if list_item_node.data.kind != _YamlNodeKind.string:
                            yield Error(
                                message=f"Expected all items in {spec_node.data.path} to be strings.",
                                node=list_item_node.data.node,
                            )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_var_type
            ):
                # Var type must be one of the following:
                # - secret
                # - oauth2-secret
                # - string
                # - data-server-info
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    # Check that the value is one of the allowed types
                    var_type = self._get_value_text(yaml_node)
                    if var_type not in [
                        "secret",
                        "oauth2-secret",
                        "string",
                        "data-server-info",
                    ]:
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be one of ['secret', 'oauth2-secret', 'string', 'data-server-info'] (found {var_type!r}).",
                            node=yaml_node.data.node,
                        )
                    else:
                        ValidVarType = Literal[
                            "secret", "oauth2-secret", "string", "data-server-info"
                        ]
                        # the other fields are the following:
                        # - type
                        # - provider
                        # - scopes
                        # - default
                        # - description
                        # but not all combinations are allowed, so, we do additional checks for what should be allowed.
                        found_type: ValidVarType = typing.cast(
                            ValidVarType,
                            var_type,
                        )

                        constraints_for_var_type: dict[
                            ValidVarType,
                            dict[str, Literal["required", "not-allowed", "optional"]],
                        ] = {
                            "secret": {
                                "provider": "not-allowed",
                                "scopes": "not-allowed",
                                "value": "optional",
                            },
                            "oauth2-secret": {
                                "provider": "required",
                                "scopes": "required",
                                "value": "not-allowed",
                            },
                            "string": {
                                "provider": "not-allowed",
                                "scopes": "not-allowed",
                                "value": "optional",
                            },
                            "data-server-info": {
                                "provider": "not-allowed",
                                "scopes": "not-allowed",
                                "value": "not-allowed",
                            },
                        }

                        # now, get the contraints based on the var_type
                        constraints = constraints_for_var_type[found_type]
                        assert yaml_node.parent is not None, (
                            "Expected parent to be defined at this point."
                        )
                        for contraint_attr, contraint_value in constraints.items():
                            if contraint_value == "required":
                                if contraint_attr not in yaml_node.parent.children:
                                    yield Error(
                                        message=f"type: {found_type} requires {contraint_attr} to be defined.",
                                        node=yaml_node.data.node,
                                    )
                            elif contraint_value == "not-allowed":
                                if contraint_attr in yaml_node.parent.children:
                                    yield Error(
                                        message=f"type: {found_type} does not expect {contraint_attr} to be defined.",
                                        node=yaml_node.data.node,
                                        severity=Severity.warning,
                                    )

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.mcp_server_cwd
            ):
                # Must check that:
                # - It must be a string
                # - The 'command-line' field is defined
                # - The path it points to exists (either relative to the agent root or absolute)
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    # Check that 'command-line' field is defined
                    if (
                        not yaml_node.parent
                        or "command-line" not in yaml_node.parent.children
                    ):
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be used together with 'command-line' field.",
                            node=yaml_node.data.node,
                        )

                    # Check that the path exists
                    cwd_value = self._get_value_text(yaml_node)
                    if cwd_value:
                        # Try as absolute path first
                        cwd_path = Path(cwd_value)
                        if not cwd_path.is_absolute():
                            # Try as relative to agent root
                            cwd_path = self._agent_root_dir / cwd_value

                        if not cwd_path.exists():
                            yield Error(
                                message=f"Expected {spec_node.data.path} to point to an existing directory (found {cwd_value!r}).",
                                node=yaml_node.data.node,
                            )
                        elif not cwd_path.is_dir():
                            yield Error(
                                message=f"Expected {spec_node.data.path} to point to a directory, not a file (found {cwd_value!r}).",
                                node=yaml_node.data.node,
                            )

            elif spec_node.data.expected_type.expected_type in (
                _ExpectedTypeEnum.action_package_version_link,
                _ExpectedTypeEnum.action_package_name_link,
            ):
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                        code=ErrorCode.action_package_info_unsynchronized,
                    )
                else:
                    package_info_in_filesystem: Optional[
                        "ActionPackageInFilesystem"
                    ] = self._get_action_package_info(spec_node, yaml_node)
                    if package_info_in_filesystem is not None:
                        if (
                            spec_node.data.expected_type.expected_type
                            == _ExpectedTypeEnum.action_package_version_link
                        ):
                            version_in_filesystem = (
                                package_info_in_filesystem.get_version()
                                or "Unable to get version from package.yaml"
                            )
                            version_in_agent_package = self._get_value_text(yaml_node)
                            if version_in_filesystem != version_in_agent_package:
                                yield Error(
                                    message=f"Expected {spec_node.data.path} to match the version in the action package being referenced ('{version_in_filesystem}'). Found in spec: '{version_in_agent_package}'",
                                    node=yaml_node.data.node,
                                    code=ErrorCode.action_package_info_unsynchronized,
                                )
                        elif (
                            spec_node.data.expected_type.expected_type
                            == _ExpectedTypeEnum.action_package_name_link
                        ):
                            name_in_filesystem = (
                                package_info_in_filesystem.get_name()
                                or "Unable to get name from package.yaml"
                            )
                            name_in_agent_package = self._get_value_text(yaml_node)
                            if name_in_filesystem != name_in_agent_package:
                                yield Error(
                                    message=f"Expected {spec_node.data.path} to match the name in the action package being referenced ('{name_in_filesystem}'). Found in spec: '{name_in_agent_package}'",
                                    node=yaml_node.data.node,
                                    code=ErrorCode.action_package_info_unsynchronized,
                                )

            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.int:
                if yaml_node.data.kind != _YamlNodeKind.int:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be an int (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.float:
                if yaml_node.data.kind not in (_YamlNodeKind.int, _YamlNodeKind.float):
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a float (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.bool:
                if yaml_node.data.kind != _YamlNodeKind.bool:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a bool (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
            elif spec_node.data.expected_type.expected_type in (
                _ExpectedTypeEnum.enum,
                _ExpectedTypeEnum.zip_or_folder_based_on_path,
            ):
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                value_node = yaml_node.data.node.child_by_field_name("value")
                if value_node is None:
                    yield Error(
                        message=f"Error while handling: {spec_node.data.path} .",
                        node=yaml_node.data.node,
                    )
                else:
                    yaml_node_text = (
                        value_node.text.decode("utf8")
                        if value_node.text is not None
                        else ""
                    )
                    enum_values = spec_node.data.expected_type.enum_values or [
                        "No enum values specified"
                    ]
                    if yaml_node_text not in enum_values:
                        yield Error(
                            message=f"Expected {spec_node.data.path} to be one of {enum_values} (found {yaml_node_text!r}).",
                            node=yaml_node.data.node,
                            severity=Severity.warning,
                        )

                    elif (
                        spec_node.data.expected_type.expected_type
                        == _ExpectedTypeEnum.zip_or_folder_based_on_path
                    ):
                        # Additional validation based on the path (to see if zip/folder matches what's in the spec).
                        package_info_in_filesystem = self._get_action_package_info(
                            spec_node, yaml_node
                        )
                        if package_info_in_filesystem is not None:
                            is_zip_package = package_info_in_filesystem.is_zip()
                            if is_zip_package:
                                expected_type_from_filesystem = "zip"
                            else:
                                expected_type_from_filesystem = "folder"

                            if yaml_node_text != expected_type_from_filesystem:
                                yield Error(
                                    message=f"Expected {spec_node.data.path} to match the type in the action package being referenced ('{expected_type_from_filesystem}'). Found in spec: '{yaml_node_text}'",
                                    node=yaml_node.data.node,
                                    code=ErrorCode.action_package_info_unsynchronized,
                                )

                            # In VSCode we can only analyze the agent when it's unzipped.
                            if expected_type_from_filesystem == "zip":
                                yield Error(
                                    message="The 'zip' mode is only supported inside a .zip distribution. When unzipped, action packages must NOT be zipped! -- "
                                    "maybe it was just unzipped instead of using the `Import Agent Package` to import the agent into VSCode?",
                                    node=yaml_node.data.node,
                                    severity=Severity.critical,
                                    code=ErrorCode.zipped_action_inside_unzipped_agent,
                                )

            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.file:
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    relative_to: str = spec_node.data.expected_type.relative_to or ""
                    error_or_path = self._get_node_value_points_to_path(
                        spec_node.data.path, yaml_node, relative_to
                    )
                    if isinstance(error_or_path, Error):
                        yield error_or_path

            elif (
                spec_node.data.expected_type.expected_type
                == _ExpectedTypeEnum.dynamic_object
            ):
                # i.e.: we have a dynamic_object and we are validating a field inside it.
                # In this case, we don't need any validation and we don't need to recurse into
                # the children (as anything can be defined inside a dynamic_object).
                return

            else:
                raise Exception(
                    f"Unexpected expected type: {spec_node.data.expected_type.expected_type}"
                )

    def _get_action_package_info(
        self, spec_node, yaml_node
    ) -> Optional["ActionPackageInFilesystem"]:
        p: str = "/".join(spec_node.data.path.split("/")[:-1] + ["path"])
        path_yaml_node = yaml_node.parent.children.get("path")
        error_or_path = self._get_node_value_points_to_path(
            p, path_yaml_node, "actions"
        )
        if not isinstance(error_or_path, Path):
            # i.e.: if not path we can just ignore it.
            return None

        if error_or_path.is_dir():
            found_in_filesystem: "ActionPackageInFilesystem" | None = (
                self._action_packages_found_in_filesystem.get(
                    error_or_path / "package.yaml"
                )
            )

        elif error_or_path.is_file():
            found_in_filesystem = self._action_packages_found_in_filesystem.get(
                error_or_path
            )

        else:
            return None

        if found_in_filesystem is not None:
            found_in_filesystem.referenced_from_agent_spec = True
        return found_in_filesystem

    def _get_node_value_points_to_path(
        self, spec_path_for_error_msg: str, yaml_node, relative_to: str
    ) -> Error | Path | None:
        value_text = self._get_value_text(yaml_node)
        if value_text is None:
            return Error(
                message=f"Error while handling: {spec_path_for_error_msg} .",
                node=yaml_node.data.node,
            )
        else:
            if "\\" in value_text:
                return Error(
                    message=f"{spec_path_for_error_msg} may not contain `\\` characters.",
                    node=yaml_node.data.node,
                )
            else:
                # Check if path is a Windows path or a Unix path
                value_text_is_absolute_path = value_text.startswith(
                    "/"
                ) or value_text.startswith("\\")
                value_text_is_windows_absolute_path = (
                    len(value_text) > 1 and value_text[1] == ":"
                )

                # Look into the relative to guide
                if relative_to == "" and (
                    value_text_is_absolute_path or value_text_is_windows_absolute_path
                ):
                    # Treat this as an absolute path
                    p = Path(value_text).absolute()
                else:
                    # Treat this as a relative path to the agent root dir
                    if not relative_to.startswith("."):
                        relative_to = "./" + relative_to
                    p = (self._agent_root_dir / relative_to / value_text).absolute()

                path_exists: bool = p.exists()

                if not path_exists:
                    if relative_to.startswith("./"):
                        relative_to = relative_to[2:]
                    if relative_to == "./":
                        relative_to = "dir('agent-spec.yaml')"
                    else:
                        relative_to = f"dir('agent-spec.yaml')/{relative_to}"
                    return Error(
                        message=f"Expected {spec_path_for_error_msg} to map to a file named {value_text!r} relative to {relative_to!r}.",
                        node=yaml_node.data.node,
                    )
                return p

    def _get_value_text(self, node: _YamlTreeNode) -> str | None:
        value_node = node.data.node.child_by_field_name("value")
        if value_node is None:
            return None
        else:
            yaml_node_text = (
                value_node.text.decode("utf8") if value_node.text is not None else ""
            )
            return yaml_node_text

    def _validate_yaml_from_spec(self) -> Iterator[Error]:
        root = _convert_flattened_to_nested(self._spec_entries)

        # print("--- root ---")
        # print(root.pretty())
        if self.PRINT_YAML_TREE:
            print("--- yaml ---")
            print(self._yaml_info_loaded.pretty())
            print("-----------")

        yield from self._verify_yaml_matches_spec(root, self._yaml_info_loaded, None)

    def _validate_unreferenced_action_packages(self) -> Iterator[Error]:
        # print(self._yaml_info_loaded.pretty())

        agent_package = self._yaml_info_loaded.children.get("agent-package")
        report_error_at_node = agent_package
        if not agent_package:
            return

        agents = agent_package.children.get("agents")
        if agents:
            report_error_at_node = agents
            for _, agent in agents.children.items():
                action_packages_node = agent.children.get("action-packages")
                if action_packages_node is not None:
                    report_error_at_node = action_packages_node
                break

        for (
            action_package_in_filesystem
        ) in self._action_packages_found_in_filesystem.values():
            if not action_package_in_filesystem.referenced_from_agent_spec:
                yield Error(
                    message=f"Action Package path not referenced in the `agent-spec.yaml`: '{action_package_in_filesystem.relative_path}'.",
                    node=report_error_at_node.data.node
                    if report_error_at_node is not None
                    else None,
                    code=ErrorCode.action_package_info_unsynchronized,
                    severity=Severity.warning,
                )

    def validate(self, node: "Node") -> Iterator[Error]:
        from .list_actions_from_agent import list_actions_from_agent

        self._action_packages_found_in_filesystem = list_actions_from_agent(
            self._agent_root_dir
        )

        yield from self._validate_nodes_exist_and_build_yaml_info(node)
        yield from self._validate_yaml_from_spec()
        yield from self._validate_unreferenced_action_packages()
