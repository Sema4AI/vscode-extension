import typing

from sema4ai_ls_core.lsp import HoverTypedDict
from sema4ai_ls_core.protocols import IDocument, IMonitor

if typing.TYPE_CHECKING:
    from tree_sitter import Node


def yield_all_nodes(node: "Node"):
    for child in node.children:
        yield child
        yield from yield_all_nodes(child)


def _find_version(node: "Node") -> str | None:
    """
    In this function we must search for the version node and return its value.
    """
    for node in yield_all_nodes(node):
        if node.type == "block_mapping_pair":
            key = node.child_by_field_name("key")
            if key and key.text and key.text.decode("utf8") == "spec-version":
                value = node.child_by_field_name("value")
                if value and value.text:
                    return value.text.decode("utf8")
    return None


def hover_on_agent_spec_yaml(
    doc: IDocument, line: int, col: int, monitor: IMonitor
) -> HoverTypedDict | None:
    import tree_sitter_yaml
    from tree_sitter import Language, Parser, Point

    language = tree_sitter_yaml.language()
    parser = Parser(Language(language))
    contents = doc.source.encode("utf8", errors="replace")
    tree = parser.parse(contents, encoding="utf8")

    pos = Point(line, col)
    descendant = tree.root_node.named_descendant_for_point_range(pos, pos)
    if not descendant:
        return None

    version = _find_version(tree.root_node)

    def get_full_path(node) -> str:
        path: list[str] = []
        current = node
        while current.parent:
            if current.type == "block_mapping_pair":
                key = current.child_by_field_name("key")
                if key:
                    path.insert(0, key.text.decode("utf-8"))
            current = current.parent
        return "/".join(path)

    def get_description(full_path) -> str | None:
        from sema4ai_code.agents.agent_spec import AGENT_SPEC_V2

        if version == "v2":
            # Hover currently only available for v2

            info = AGENT_SPEC_V2
            entry = info.get(full_path, None)
            if not entry:
                return None
            return entry.description
        else:
            # Hover currently only available for the latest version (right now v2)
            info = AGENT_SPEC_V2
            entry = info.get(full_path, None)
            if not entry:
                return None
            return entry.description

    full_path = get_full_path(descendant)
    description = get_description(full_path)
    if not description:
        return None

    hover: HoverTypedDict = {
        "contents": {
            "kind": "plaintext",
            "value": description,
        },
        "range": {
            "start": {
                "line": descendant.start_point.row,
                "character": descendant.start_point.column,
            },
            "end": {
                "line": descendant.end_point.row,
                "character": descendant.end_point.column,
            },
        },
    }
    return hover
