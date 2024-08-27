import json
from typing import Optional

from sema4ai_ls_core.lsp import HoverTypedDict
from sema4ai_ls_core.protocols import IDocument, IMonitor


def hover_on_agent_spec_yaml(
    doc: IDocument, line: int, col: int, monitor: IMonitor
) -> Optional[HoverTypedDict]:
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

    def get_description(full_path) -> Optional[str]:
        from sema4ai_code.agents.agent_spec_provider import load_v2_spec

        info = load_v2_spec()
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
