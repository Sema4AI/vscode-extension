import ast as ast_module
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, TypedDict

from sema4ai_ls_core import uris
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.lsp import RangeTypedDict
from sema4ai_ls_core.protocols import (
    ActionInfoTypedDict,
    ActionResult,
    DatasourceInfoTypedDict,
    IMonitor,
)

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


def _resolve_value(node: ast_module.AST, variable_values: dict[str, str]) -> Any:
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
    elif isinstance(node, ast_module.List):
        return [_resolve_value(item, variable_values) for item in node.elts]
    return None


class _DatasourceInfo(TypedDict, total=False):
    kind: Literal["datasource"]
    node: ast_module.AST
    name: str | None
    engine: str | None
    model_name: str | None
    created_table: str | None
    python_variable_name: str
    description: str | None
    file: str | None
    setup_sql: str | None
    setup_sql_files: list[str] | None


def _extract_datasource_info(
    call_node: ast_module.Call,
    variable_values: dict,
    python_variable_name: str,
    target_node: ast_module.AST,
) -> _DatasourceInfo:
    """
    Extract datasource information from a DataSourceSpec(...) call node.

    Args:
        call_node: AST node representing the call.
        variable_values: Dictionary of known variable values.
    """
    import typing

    collect_info = (
        "name",
        "model_name",
        "engine",
        "description",
        "file",
        "created_table",
        "setup_sql",
        "setup_sql_files",
    )

    info: _DatasourceInfo = {"kind": "datasource", "node": target_node}

    for keyword in call_node.keywords:
        if keyword.arg in collect_info:
            key = typing.cast(
                Literal[
                    "name",
                    "model_name",
                    "engine",
                    "description",
                    "file",
                    "created_table",
                    "setup_sql",
                    "setup_sql_files",
                ],
                keyword.arg,
            )
            value = _resolve_value(keyword.value, variable_values)
            info[key] = value

    if info.get("engine") == "files":
        info["name"] = "files"
    elif info.get("model_name"):
        info["name"] = "models"

    info["python_variable_name"] = python_variable_name

    return info


def is_annotated_type(node: ast_module.AST) -> bool:
    if isinstance(node, ast_module.Name):
        return node.id == "Annotated"

    if isinstance(node, ast_module.Attribute):
        return node.attr == "Annotated"

    return False


def _collect_datasources(
    ast: ast_module.AST, variables: dict[str, Any]
) -> Iterator[_DatasourceInfo]:
    """
    Collect datasource information by identifying specific structures in the AST.

    Args:
        ast: The root AST node.
        variables: Dictionary of known variable values.
    """
    for _stack, node in _iter_nodes(ast, recursive=False):
        if isinstance(node, ast_module.Assign) and len(node.targets) == 1:
            # Get the name of the variable being assigned
            target = node.targets[0]
            if isinstance(target, ast_module.Name) and isinstance(
                node.value, ast_module.Subscript
            ):
                python_variable_name = target.id
                subscript = node.value
                # Check if the value is an Annotated[...] or typing.Annotated[...]
                if is_annotated_type(subscript.value):
                    # Check if the slice is a Call node with DataSourceSpec
                    if isinstance(subscript.slice, ast_module.Tuple):
                        elts = subscript.slice.elts
                        if len(elts) == 2:
                            if isinstance(elts[1], ast_module.Call):
                                if (
                                    isinstance(elts[1].func, ast_module.Name)
                                    and elts[1].func.id == "DataSourceSpec"
                                ):
                                    yield _extract_datasource_info(
                                        elts[1],
                                        variables,
                                        python_variable_name,
                                        target_node=target,
                                    )


class _ActionInfo(TypedDict):
    kind: str
    node: ast_module.FunctionDef


def _collect_actions_from_ast(ast: ast_module.AST) -> Iterator[_ActionInfo]:
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


def _get_ast_node_range(
    node: ast_module.FunctionDef | ast_module.Call | ast_module.AST,
) -> RangeTypedDict:
    if isinstance(node, ast_module.FunctionDef):
        coldelta = 4
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

    if isinstance(node, ast_module.Call):
        node_expr = node.func
    elif isinstance(node, ast_module.expr):
        node_expr = node
    else:
        raise ValueError(f"Unexpected node type to get node range: {type(node)}")

    return {
        "start": {
            "line": node_expr.lineno,
            "character": node_expr.col_offset,
        },
        "end": {
            "line": node_expr.end_lineno or node_expr.lineno,
            "character": node_expr.end_col_offset or node_expr.col_offset,
        },
    }


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
                    action_contents_file = f.read_bytes()
                    ast = ast_module.parse(action_contents_file, "<string>")
                    uri = uris.from_fs_path(str(f))

                    for node_info_action in _collect_actions_from_ast(ast):
                        function_def_node = node_info_action["node"]
                        node_range = _get_ast_node_range(function_def_node)
                        yield ActionInfoTypedDict(
                            uri=uri,
                            range=node_range,
                            name=function_def_node.name,
                            kind=node_info_action["kind"],
                        )

                    if collect_datasources:
                        variables = _collect_variables(ast)
                        # Note: Instead of iterating over all nodes to collect datasources, we
                        # try to find the following structure:
                        #
                        # DataSourceVarName = Annotated[DataSource, DataSourceSpec(name="my_datasource")]
                        #
                        # Note that the DataSourceSpec(...) is a Call node inside the Annotated[...]
                        # which in turn must be inside an Assign node.

                        if collect_datasources:
                            for node_info_datasource in _collect_datasources(
                                ast, variables
                            ):
                                ast_node = node_info_datasource["node"]
                                node_range = _get_ast_node_range(ast_node)
                                yield DatasourceInfoTypedDict(
                                    range=node_range,
                                    uri=uri,
                                    name=node_info_datasource.get("name")
                                    or "<name not found>",
                                    engine=node_info_datasource.get(
                                        "engine",
                                    )
                                    or "<engine not found>",
                                    model_name=node_info_datasource.get("model_name"),
                                    created_table=node_info_datasource.get(
                                        "created_table"
                                    ),
                                    kind="datasource",
                                    python_variable_name=node_info_datasource.get(
                                        "python_variable_name"
                                    ),
                                    setup_sql=node_info_datasource.get("setup_sql"),
                                    setup_sql_files=node_info_datasource.get(
                                        "setup_sql_files"
                                    ),
                                    description=node_info_datasource.get("description"),
                                    file=node_info_datasource.get("file"),
                                )
                except Exception as e:
                    log.error(
                        f"Unable to collect @action/@query/@predict/datasources from {f}. Error: {e}"
                    )


def get_action_signature(
    action_relative_path: str,
    action_package_yaml_directory: str,
    action_name: str,
    monitor: IMonitor,
) -> ActionResult[str]:
    action_file_path = Path(action_package_yaml_directory) / action_relative_path
    if not action_file_path.exists():
        return ActionResult.make_failure(f"Action file not found: {action_file_path}")

    action_contents_file = action_file_path.read_bytes()
    try:
        ast = ast_module.parse(action_contents_file, "<string>")
    except Exception:
        return ActionResult.make_failure(
            f"Unable to parse action file: {action_file_path}"
        )

    for node_info_action in _collect_actions_from_ast(ast):
        function_def_node = node_info_action["node"]
        if function_def_node.name == action_name:
            # Convert the function signature to a string
            signature = ast_module.unparse(function_def_node.args)
            return ActionResult.make_success(
                f"{node_info_action['kind']}/args: {signature!r}"
            )

    return ActionResult.make_failure(f"Action not found: {action_name}")
