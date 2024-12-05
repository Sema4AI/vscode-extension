import ast as ast_module
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sema4ai_ls_core import uris
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.lsp import RangeTypedDict
from sema4ai_ls_core.protocols import ActionInfoTypedDict, DatasourceInfoTypedDict

log = get_logger(__name__)


def _collect_py_files(root_path: Path) -> Iterator[Path]:
    for item in root_path.iterdir():
        if item.is_dir():
            yield from _collect_py_files(item)
        elif item.suffix == ".py":
            yield item


def _iter_nodes(
    node, internal_stack: list[Any] | None = None, recursive=True
) -> Iterator[tuple[list[Any], Any]]:
    """
    :note: the yielded stack is actually always the same (mutable) list, so,
    clients that want to return it somewhere else should create a copy.
    """
    stack: list[Any]
    if internal_stack is None:
        stack = []
        if node.__class__.__name__ != "File":
            stack.append(node)
    else:
        stack = internal_stack

    if recursive:
        for _field, value in ast_module.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast_module.AST):
                        yield stack, item
                        stack.append(item)
                        yield from _iter_nodes(item, stack, recursive=True)
                        stack.pop()

            elif isinstance(value, ast_module.AST):
                yield stack, value
                stack.append(value)

                yield from _iter_nodes(value, stack, recursive=True)

                stack.pop()
    else:
        # Not recursive
        for _field, value in ast_module.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast_module.AST):
                        yield stack, item

            elif isinstance(value, ast_module.AST):
                yield stack, value


def _collect_variables(ast: ast_module.AST) -> dict[str, Any]:
    variables = {}
    for _stack, node in _iter_nodes(ast, recursive=False):
        if isinstance(node, ast_module.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast_module.Name) and isinstance(
                node.value, ast_module.Constant
            ):
                variables[target.id] = node.value.value

    return variables


def _resolve_value(node: ast_module.AST, variable_values: dict[str, str]) -> str | None:
    """
    Resolve a value from an AST node, considering variable references.

    Args:
        node: AST node to resolve.
        variable_values: Dictionary of known variable values.
    """
    if isinstance(node, ast_module.Constant):
        return node.value
    elif isinstance(node, ast_module.Name) and node.id in variable_values:
        return variable_values[node.id]
    return None


DATASOURCE_KIND = "datasource"


def _extract_datasource_info(call_node: ast_module.Call, variable_values: dict) -> dict:
    """
    Extract datasource information from a DataSourceSpec(...) call node.

    Args:
        call_node: AST node representing the call.
        variable_values: Dictionary of known variable values.
    """

    interested_info = ["name", "model_name", "engine", "created_table"]
    info = {"kind": DATASOURCE_KIND, "node": call_node}

    for keyword in call_node.keywords:
        if keyword.arg in interested_info:
            name = _resolve_value(keyword.value, variable_values)
            info[keyword.arg] = name

    if info.get("engine") == "files":
        info["name"] = "files"
    elif info.get("model_name"):
        info["name"] = "models"

    return info


def _collect_actions_from_ast(
    p: Path, collect_datasources: bool = False
) -> Iterator[dict]:
    action_contents_file = p.read_bytes()
    ast = ast_module.parse(action_contents_file, "<string>")
    variables = _collect_variables(ast)

    for _stack, node in _iter_nodes(ast, recursive=False):
        if isinstance(node, ast_module.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast_module.Call):
                    # Case for @action(is_consequential=True)
                    decorator = decorator.func

                # Case for @action
                if isinstance(decorator, ast_module.Name) and decorator.id in [
                    "action",
                    "query",
                    "predict",
                ]:
                    yield {"node": node, "kind": decorator.id}

    # TODO: Instead of iterating over all nodes to collect datasources, we should
    # try to find the following structure:
    #
    # DataSourceVarName = Annotated[DataSource, DataSourceSpec(name="my_datasource")]
    #
    # Note that the DataSourceSpec(...) is a Call node inside the Annotated[...]
    # which in turn must be inside an Assign node.

    for _stack, node in _iter_nodes(ast, recursive=True):
        if (
            collect_datasources
            and isinstance(node, ast_module.Call)
            and isinstance(node.func, ast_module.Name)
            and node.func.id == "DataSourceSpec"
        ):
            result = _extract_datasource_info(node, variables)
            if result:
                yield result


def _get_ast_node_range(
    node: ast_module.FunctionDef | ast_module.Call,
) -> RangeTypedDict:
    coldelta = 4

    if isinstance(node, ast_module.Call):
        func_node = node.func
        return {
            "start": {
                "line": func_node.lineno,
                "character": func_node.col_offset,
            },
            "end": {
                "line": node.end_lineno or func_node.lineno,
                "character": node.end_col_offset or node.col_offset,
            },
        }

    return {
        "start": {
            "line": node.lineno,
            "character": node.col_offset + coldelta,
        },
        "end": {
            "line": node.lineno,
            "character": node.col_offset + coldelta + len(node.name),
        },
    }


def _make_action_or_datasource_info(
    uri: str, node_info: dict
) -> ActionInfoTypedDict | DatasourceInfoTypedDict:
    ast_node = node_info["node"]
    node_range = _get_ast_node_range(ast_node)

    if node_info["kind"] == DATASOURCE_KIND:
        return DatasourceInfoTypedDict(
            range=node_range,
            uri=uri,
            name=node_info.get("name", "<name not found>"),
            engine=node_info.get("engine", "<engine not found>"),
            model_name=node_info.get("model_name"),
            created_table=node_info.get("created_table"),
            kind="datasource",
        )
    else:
        return ActionInfoTypedDict(
            range=node_range, uri=uri, name=ast_node.name, kind=node_info["kind"]
        )


DEFAULT_ACTION_SEARCH_GLOB = (
    "*action*.py|*query*.py|*queries*.py|*predict*.py|*datasource*.py|*data_source*.py"
)

globs = DEFAULT_ACTION_SEARCH_GLOB.split("|")


def iter_actions_and_datasources(
    root_directory: Path,
    collect_datasources: bool = False,
) -> Iterator[ActionInfoTypedDict | DatasourceInfoTypedDict]:
    """
    Iterates over the actions just by using the AST (this means that it doesn't
    give complete information, rather, it is a fast way to provide just simple
    metadata such as the action name and location).
    """
    import fnmatch

    f: Path
    for f in _collect_py_files(root_directory):
        for glob in globs:
            if fnmatch.fnmatch(f.name, glob):
                try:
                    for node_info in _collect_actions_from_ast(f, collect_datasources):
                        yield _make_action_or_datasource_info(
                            uris.from_fs_path(str(f)), node_info
                        )
                except Exception as e:
                    log.error(
                        f"Unable to collect @action/@query/@predict/datasources from {f}. Error: {e}"
                    )
