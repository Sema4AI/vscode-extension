import typing
from functools import partial
from pathlib import Path

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
        compute_action_packages_code_lenses = True

        if config_provider is not None:
            config = config_provider.config
            if config:
                from sema4ai_code.settings import SEMA4AI_CODE_LENS_ROBO_LAUNCH

                compute_robo_tasks_code_lenses = config.get_setting(
                    SEMA4AI_CODE_LENS_ROBO_LAUNCH, bool, True
                )

                from sema4ai_code.settings import SEMA4AI_CODE_LENS_ACTIONS_LAUNCH

                compute_action_packages_code_lenses = config.get_setting(
                    SEMA4AI_CODE_LENS_ACTIONS_LAUNCH, bool, True
                )

        if (
            not compute_robo_tasks_code_lenses
            and not compute_action_packages_code_lenses
        ):
            return None
        # Provide a partial which will be computed in a thread with a monitor.
        return require_monitor(
            partial(
                _collect_python_code_lenses_in_thread,
                document,
                compute_robo_tasks_code_lenses,
                compute_action_packages_code_lenses,
            )
        )

    if fs_path.endswith("package.yaml"):
        return require_monitor(
            partial(_collect_package_yaml_code_lenses_in_thread, document)
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


def _is_sema4ai_actions_import(node: "ast.AST") -> bool:
    import ast

    if isinstance(node, ast.ImportFrom):
        # Check if the module is 'sema4ai.actions' and 'action' is in the names
        if node.module == "sema4ai.actions":
            for alias in node.names:
                if alias.name == "action":
                    return True
    return False


def _is_sema4ai_queries_import(node: "ast.AST") -> bool:
    import ast

    if isinstance(node, ast.ImportFrom):
        # Check if the module is 'sema4ai.data' and 'query' is in the names
        if node.module == "sema4ai.data":
            for alias in node.names:
                if alias.name == "query":
                    return True
    return False


def _is_sema4ai_predict_import(node: "ast.AST") -> bool:
    import ast

    if isinstance(node, ast.ImportFrom):
        # Check if the module is 'sema4ai.data' and 'predict' is in the names
        if node.module == "sema4ai.data":
            for alias in node.names:
                if alias.name == "predict":
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


def _collect_package_yaml_code_lenses_in_thread(
    document: IDocument,
    monitor: IMonitor,
) -> list[CodeLensTypedDict] | None:
    from pathlib import Path

    from sema4ai_code.commands import SEMA4AI_RUN_ACTION_PACKAGE_DEV_TASK
    from sema4ai_code.robo.list_dev_tasks import list_dev_tasks_from_content

    result = list_dev_tasks_from_content(document.source, Path(document.path))

    if not result.success:
        log.info(result.message or "<no message when unable to list dev tasks>")
        return None

    code_lenses: list[CodeLensTypedDict] = []
    dev_tasks = result.result
    if dev_tasks:
        for task_name in dev_tasks.keys():
            if task_name.location:
                code_lenses.append(
                    _create_code_lens(
                        task_name.location[0],
                        "Run Dev Task",
                        SEMA4AI_RUN_ACTION_PACKAGE_DEV_TASK,
                        [
                            {
                                "packageYamlPath": document.path,
                                "taskName": task_name,
                            }
                        ],
                    )
                )
    return code_lenses


def _find_package_yaml_from_path(fs_path: Path) -> Path | None:
    import itertools

    for path in itertools.chain(iter([fs_path]), fs_path.parents):
        # Give higher priority to package.yaml (in case conda.yaml became
        # package.yaml but robot.yaml is still lingering around).
        package_yaml: Path = path / "package.yaml"
        if package_yaml.exists():
            return package_yaml
    return None


def _collect_python_code_lenses_in_thread(
    document: IDocument,
    compute_robo_tasks_code_lenses: bool,
    compute_action_packages_code_lenses: bool,
    monitor: IMonitor,
) -> list[CodeLensTypedDict] | None:
    import ast

    from sema4ai_code.commands import (
        SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
        SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
    )

    tasks_code_lenses: list[CodeLensTypedDict] = []
    actions_code_lenses: list[CodeLensTypedDict] = []
    contents = document.source

    # Parse the document source into an AST
    try:
        tree = ast.parse(contents)
    except Exception:
        return None

    found_robocorp_tasks_import = False
    found_sema4ai_actions_import = False
    found_sema4ai_queries_import = False
    found_sema4ai_predict_import = False

    package_yaml_path = _find_package_yaml_from_path(Path(document.path))
    if not package_yaml_path:
        compute_action_packages_code_lenses = False

    # Iterate over the AST nodes
    for node in ast.walk(tree):
        monitor.check_cancelled()

        # Detect if there's a `from robocorp.tasks import task` import.
        if not found_robocorp_tasks_import and compute_robo_tasks_code_lenses:
            found_robocorp_tasks_import = _is_robocorp_tasks_import(node)

        # Detect if there's a `from sema4ai.actions import action` import.
        if not found_sema4ai_actions_import and compute_action_packages_code_lenses:
            found_sema4ai_actions_import = _is_sema4ai_actions_import(node)

        # Detect if there's a `from sema4ai.data import query` import.
        if not found_sema4ai_queries_import and compute_action_packages_code_lenses:
            found_sema4ai_queries_import = _is_sema4ai_queries_import(node)

        # Detect if there's a `from sema4ai.data import predict` import.
        if not found_sema4ai_predict_import and compute_action_packages_code_lenses:
            found_sema4ai_predict_import = _is_sema4ai_predict_import(node)

        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            for decorator in node.decorator_list:
                if (
                    compute_action_packages_code_lenses
                    and found_sema4ai_actions_import
                    and isinstance(decorator, ast.Name)
                    and decorator.id == "action"
                ):
                    assert (
                        package_yaml_path is not None
                    ), "Expected package_yaml_path to be defined at this point."
                    function_name = node.name
                    start_line = decorator.lineno - 1  # AST line numbers are 1-based
                    robot_entry = {
                        "actionName": function_name,
                        "robot": {
                            "directory": str(package_yaml_path.parent),
                            "filePath": str(package_yaml_path),
                        },
                        "uri": document.uri,
                    }
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Run Action",
                            SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
                            [robot_entry],
                        )
                    )
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Debug Action",
                            SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
                            [robot_entry],
                        )
                    )

                elif (
                    compute_action_packages_code_lenses
                    and found_sema4ai_queries_import
                    and isinstance(decorator, ast.Name)
                    and decorator.id == "query"
                ):
                    assert (
                        package_yaml_path is not None
                    ), "Expected package_yaml_path to be defined at this point."
                    function_name = node.name
                    start_line = decorator.lineno - 1  # AST line numbers are 1-based
                    robot_entry = {
                        "actionName": function_name,
                        "robot": {
                            "directory": str(package_yaml_path.parent),
                            "filePath": str(package_yaml_path),
                        },
                        "uri": document.uri,
                    }
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Run Query",
                            SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
                            [robot_entry],
                        )
                    )
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Debug Query",
                            SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
                            [robot_entry],
                        )
                    )

                elif (
                    compute_action_packages_code_lenses
                    and found_sema4ai_predict_import
                    and isinstance(decorator, ast.Name)
                    and decorator.id == "predict"
                ):
                    assert (
                        package_yaml_path is not None
                    ), "Expected package_yaml_path to be defined at this point."
                    function_name = node.name
                    start_line = decorator.lineno - 1  # AST line numbers are 1-based
                    robot_entry = {
                        "actionName": function_name,
                        "robot": {
                            "directory": str(package_yaml_path.parent),
                            "filePath": str(package_yaml_path),
                        },
                        "uri": document.uri,
                    }
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Run Predict",
                            SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
                            [robot_entry],
                        )
                    )
                    actions_code_lenses.append(
                        _create_code_lens(
                            start_line,
                            "Debug Predict",
                            SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
                            [robot_entry],
                        )
                    )

                elif (
                    compute_robo_tasks_code_lenses
                    and isinstance(decorator, ast.Name)
                    and decorator.id == "task"
                ):
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

    all_lenses = []
    if found_robocorp_tasks_import:
        # If there was no import, then @task decorators are from some other library!
        all_lenses.extend(tasks_code_lenses)

    all_lenses.extend(actions_code_lenses)
    return all_lenses
