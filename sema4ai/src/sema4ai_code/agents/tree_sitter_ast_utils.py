import logging
import sys
import typing
from typing import Generic, Optional, TypeVar
from collections.abc import Iterator

log = logging.getLogger(__name__)

Y = TypeVar("Y", covariant=True)

if typing.TYPE_CHECKING:
    from tree_sitter import Node as TreeSitterNode


class NodeInfo(Generic[Y]):
    stack: tuple["TreeSitterNode", ...]
    node: "TreeSitterNode"

    __slots__ = ["stack", "node"]

    def __init__(self, stack, node):
        self.stack = stack
        self.node = node

    def __str__(self):
        return f"NodeInfo({self.node.__class__.__name__})"

    __repr__ = __str__


def print_ast(node, stream=None, depth=0):
    if stream is None:
        stream = sys.stderr

    stream.write(
        f'{"  " * depth}Node type: "{node.type}", start: {node.start_point}, end: {node.end_point}\n'
    )

    for child_node in node.children:
        print_ast(child_node, stream, depth + 1)


def _iter_nodes(
    node, internal_stack: list["TreeSitterNode"] | None = None, recursive=True
) -> Iterator[tuple[list["TreeSitterNode"], "TreeSitterNode"]]:
    """
    :note: the yielded stack is actually always the same (mutable) list, so,
    clients that want to return it somewhere else should create a copy.
    """
    stack: list["TreeSitterNode"]
    if internal_stack is None:
        stack = []
        stack.append(node)
    else:
        stack = internal_stack

    children = node.children
    for child_node in children:
        yield stack, child_node
        if recursive:
            stack.append(child_node)
            yield from _iter_nodes(child_node, stack, True)
            stack.pop(-1)


def iter_all_nodes(node, recursive=True) -> Iterator[NodeInfo["TreeSitterNode"]]:
    """
    Note: use this *very* sparingly as no caching will take place
    (as all nodes need to be iterated).

    Use one of the filtered APIs whenever possible as those are cached
    by the type.
    """
    for stack, node in _iter_nodes(node, recursive=recursive):
        yield NodeInfo(tuple(stack), node)
