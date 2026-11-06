import typing
from functools import partial

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.jsonrpc.endpoint import require_monitor
from sema4ai_ls_core.lsp import CodeLensTypedDict
from sema4ai_ls_core.protocols import (
    IConfig,
    IConfigProvider,
    IDocument,
    IMonitor,
    IWorkspace,
)

if typing.TYPE_CHECKING:
    import ast


log = get_logger(__name__)


def compute_code_lenses(
    workspace: IWorkspace | None, config_provider: IConfigProvider, doc_uri: str
) -> partial | None:
    from sema4ai_ls_core import uris

    ws = workspace
    if ws is None:
        return None

    document: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
    if document is None:
        return None

    config_provider = config_provider
    config: IConfig | None = None

    fs_path = uris.to_fs_path(doc_uri)
    if fs_path.endswith(".py"):
        compute_robo_tasks_code_lenses = True

        if config_provider is not None:
            config = config_provider.config
            if config:
                from sema4ai_code.settings import SEMA4AI_CODE_LENS_ROBO_LAUNCH

                compute_robo_tasks_code_lenses = config.get_setting(
                    SEMA4AI_CODE_LENS_ROBO_LAUNCH, bool, True
                )

        if not compute_robo_tasks_code_lenses:
            return None
        # Provide a partial which will be computed in a thread with a monitor.
        return require_monitor(
            partial(
                _collect_python_code_lenses_in_thread,
                document,
            )
        )

    return None


def _is_robocorp_tasks_import(node: "ast.AST") -> bool:
    import ast

    if isinstance(node, ast.ImportFrom):
        # Check if the module is 'robocorp.tasks' and 'task' is in the names
        if node.module == "robocorp.tasks":
            for alias in node.names:
                if alias.name == "task":
                    return True
    return False


def _create_code_lens(start_line, title, command, arguments) -> CodeLensTypedDict:
    return {
        "range": {
            "start": {
                "line": start_line,
                "character": 0,
            },
            "end": {
                "line": start_line,
                "character": 0,
            },
        },
        "command": {
            "title": title,
            "command": command,
            "arguments": arguments,
        },
        "data": None,
    }


def _collect_python_code_lenses_in_thread(
    document: IDocument,
    monitor: IMonitor,
) -> list[CodeLensTypedDict] | None:
    import ast

    tasks_code_lenses: list[CodeLensTypedDict] = []
    contents = document.source

    # Parse the document source into an AST
    try:
        tree = ast.parse(contents)
    except Exception:
        return None

    found_robocorp_tasks_import = False

    # Iterate over the AST nodes
    for node in ast.walk(tree):
        monitor.check_cancelled()

        # Detect if there's a `from robocorp.tasks import task` import.
        if not found_robocorp_tasks_import:
            found_robocorp_tasks_import = _is_robocorp_tasks_import(node)

        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "task":
                    function_name = node.name
                    start_line = decorator.lineno - 1  # AST line numbers are 1-based
                    tasks_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Run Task",
                            "sema4ai.runRobocorpsPythonTask",
                            [
                                [
                                    document.path,
                                    "-t",
                                    function_name,
                                ]
                            ],
                        )
                    )
                    tasks_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Debug Task",
                            "sema4ai.debugRobocorpsPythonTask",
                            [
                                [
                                    document.path,
                                    "-t",
                                    function_name,
                                ]
                            ],
                        )
                    )

    if not found_robocorp_tasks_import:
        # If there was no import, then @task decorators are from some other library!
        return []
    return tasks_code_lenses
