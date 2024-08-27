import typing
import weakref
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Iterator, Optional, TypeVar

if typing.TYPE_CHECKING:
    from tree_sitter import Node


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


@dataclass
class _ExpectedType:
    expected_type: _ExpectedTypeEnum  # May be "object", "string", "enum", "file", "list" (implies "list[object]"), or "bool".

    # If a "string" type, the recommended values may be provided
    # (this means that any string value is accepted, but the recommended values can be used to help the user).
    recommended_values: Optional[list[str]] = None

    # If an "enum" type, the accepted values should be provided.
    enum_values: Optional[list[str]] = None

    # If a "file" type, the relative path to the file (based on the agent root dir) should be provided.
    relative_to: Optional[str] = None

    def __post_init__(self) -> None:
        if self.expected_type == "file":
            assert (
                self.relative_to is not None
            ), "relative_to must be provided for file type."

        if self.expected_type == "enum":
            assert (
                self.enum_values is not None
            ), "enum_values must be provided for enum type."


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
            assert isinstance(
                value, dict
            ), f"Invalid spec: {path}. Expected a dictionary. Found {type(value)}"

            value = value.copy()
            deprecated = value.pop("deprecated", False)
            required = value.pop("required", False)
            expected_type = value.pop("expected-type", None)
            description = value.pop("description", None)
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


@dataclass
class Error:
    message: str
    node: Optional["Node"] = None


class TreeNode(Generic[T]):
    _parent: Optional[weakref.ref["TreeNode[T]"]] = None

    def __init__(self, name: str, parent: Optional["TreeNode[T]"] = None):
        self.name = name
        self._children: dict[str, "TreeNode[T]"] = {}
        self._data: Optional[T] = None
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


def validate(
    yaml_spec_contents: str,
    json_spec: dict,
    agent_root_dir: Path,
    raise_on_error: bool = True,
) -> tuple[Error, ...]:
    """
    Validate the YAML agent spec against the JSON agent spec.

    Params:
        yaml_spec_contents: The YAML agent spec contents as a string.
        json_spec: The JSON agent spec as a dictionary (loaded from the JSON file).
        agent_root_dir: The root directory of the agent package (contains the agent-spec.yaml file).

    Raises:
        InvalidSpec: If the YAML agent spec is invalid.
    """
    import tree_sitter_yaml
    import yaml
    from tree_sitter import Language, Parser

    # Make sure the YAML agent spec is valid
    yaml.safe_load(yaml_spec_contents)

    spec_entries = load_spec(json_spec)

    language = tree_sitter_yaml.language()
    parser = Parser(Language(language))
    contents = yaml_spec_contents.encode("utf8", errors="replace")
    tree = parser.parse(contents, encoding="utf8")

    validator = Validator(spec_entries, agent_root_dir)
    errors: tuple[Error, ...] = tuple(validator.validate(tree.root_node))
    if errors and raise_on_error:
        msg = "\n".join(e.message for e in errors)
        raise InvalidSpec(msg)
    return errors


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

    def _validate_key_pair(
        self, key_node: "Node", value_node: Optional["Node"]
    ) -> Iterator[Error]:
        entry = self._spec_entries.get(self._current_stack_as_str)
        if not entry or not value_node:
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
                )
            else:
                yield Error(
                    message=f"Expected value for {self._current_stack_as_str}.",
                    node=key_node,
                )

            return

        # Ok, it's an expected key.

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
        yaml_node: Optional[_YamlTreeNode],
        parent_node: Optional[_YamlTreeNode],
    ) -> Iterator[Error]:
        if spec_node.parent is None:
            assert yaml_node is not None, "Expected yaml node to be provided for root."
            for child in spec_node.children.values():
                yield from self._verify_yaml_matches_spec(
                    child, yaml_node.children.get(child.name), yaml_node
                )
            return

        assert (
            spec_node.data is not None
        ), f"Expected data to be loaded. Name: {spec_node.name}. Parent: {spec_node.parent}"

        if spec_node.data.required:
            if yaml_node is None:
                try:
                    data = parent_node.data if parent_node else None
                except RootHasNoDataError:
                    data = None
                yield Error(
                    message=f"Missing required entry: {spec_node.data.path}.",
                    node=data.node if data else None,
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
            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.enum:
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
                        )
            elif spec_node.data.expected_type.expected_type == _ExpectedTypeEnum.file:
                if yaml_node.data.kind != _YamlNodeKind.string:
                    yield Error(
                        message=f"Expected {spec_node.data.path} to be a string (found {yaml_node.data.kind.value}).",
                        node=yaml_node.data.node,
                    )
                else:
                    value_text = self._get_value_text(yaml_node)
                    if value_text is None:
                        yield Error(
                            message=f"Error while handling: {spec_node.data.path} .",
                            node=yaml_node.data.node,
                        )
                    else:
                        if "\\" in value_text:
                            yield Error(
                                message=f"{spec_node.data.path} may not contain `\\` characters.",
                                node=yaml_node.data.node,
                            )
                        else:
                            relative_to = spec_node.data.expected_type.relative_to
                            assert relative_to, f"Expected relative_to to be set in {spec_node.data.path}"

                            if not relative_to.startswith("."):
                                relative_to = "./" + relative_to

                            p = self._agent_root_dir / relative_to / value_text
                            if not p.exists():
                                if relative_to.startswith("./"):
                                    relative_to = relative_to[2:]
                                if relative_to == "./":
                                    relative_to = "dir('agent-spec.yaml')"
                                else:
                                    relative_to = (
                                        f"dir('agent-spec.yaml')/{relative_to}"
                                    )

                                yield Error(
                                    message=f"Expected {spec_node.data.path} to map to a file named {value_text!r} relative to {relative_to!r}.",
                                    node=yaml_node.data.node,
                                )

            else:
                raise Exception(
                    f"Unexpected expected type: {spec_node.data.expected_type.expected_type}"
                )

    def _get_value_text(self, node: _YamlTreeNode) -> Optional[str]:
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

    def validate(self, node: "Node") -> Iterator[Error]:
        yield from self._validate_nodes_exist_and_build_yaml_info(node)
        yield from self._validate_yaml_from_spec()