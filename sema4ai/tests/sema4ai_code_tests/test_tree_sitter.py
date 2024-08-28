from sema4ai_code.agents.tree_sitter_ast_utils import iter_all_nodes


def test_tree_sitter() -> None:
    from io import StringIO

    import tree_sitter_yaml
    from sema4ai_ls_core.workspace import Document
    from tree_sitter import Language, Parser, Point

    from sema4ai_code.agents.tree_sitter_ast_utils import print_ast

    language = tree_sitter_yaml.language()
    parser = Parser(Language(language))
    contents = """agent-package:
  spec-version: v1
  agents:
  - name: New Agent
    description: Agent description
    model: GPT 4 Turbo
    type: agent
    reasoningLevel: 0
    runbooks:
      system: system.md
      retrieval: retrieval.md
    action-packages: []
    resources: []
"""
    tree = parser.parse(
        contents.encode("utf8"),
        encoding="utf8",
    )
    cursor = tree.walk()
    assert cursor.node == tree.root_node

    stream = StringIO()
    print_ast(tree.root_node, stream=stream)

    for node_info in iter_all_nodes(tree.root_node):
        text = ""
        if node_info.node.type in ("string_scalar", "integer_scalar"):
            text = f" - {node_info.node.text.decode('utf-8') if node_info.node.text else 'text:None'}"

            print(
                str(".".join([n.type for n in node_info.stack])),
                "-",
                node_info.node.type,
                text,
                file=stream,
            )

    d = Document(uri="", source=contents)
    for line, line_text in enumerate(d.iter_lines(keep_ends=False)):
        last_found = None
        for column in range(len(line_text) + 3):
            pos = Point(line, column)
            descendant = tree.root_node.named_descendant_for_point_range(pos, pos)
            if descendant:
                if last_found == descendant:
                    continue
                last_found = descendant
                if descendant.type in ("string_scalar", "integer_scalar"):
                    print(
                        "found at pos",
                        pos,
                        descendant.text.decode("utf-8")
                        if descendant.text
                        else "text:None",
                        file=stream,
                    )
