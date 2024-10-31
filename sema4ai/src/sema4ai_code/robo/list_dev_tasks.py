import typing
from pathlib import Path

from sema4ai_ls_core.protocols import ActionResult

if typing.TYPE_CHECKING:
    from sema4ai_code.vendored_deps.yaml_with_location import str_with_location


def list_dev_tasks_from_content(
    action_package_yaml_content: str, action_package_yaml_path: Path
) -> ActionResult[dict["str_with_location", "str_with_location"]]:
    from sema4ai_code.vendored_deps.yaml_with_location import (
        LoaderWithLines,
        str_with_location,
    )

    try:
        loader = LoaderWithLines(action_package_yaml_content)
        loader.name = f".../{action_package_yaml_path.parent.name}/{action_package_yaml_path.name}"
        yaml_content = loader.get_single_data()
    except Exception as e:
        return ActionResult.make_failure(
            f"Unable to parse: {action_package_yaml_path} as YAML. Error: {e}"
        )

    if not isinstance(yaml_content, dict):
        return ActionResult.make_failure(
            f"Expected a dictionary as the root of: {action_package_yaml_path}."
        )

    dev_tasks = yaml_content.get("dev-tasks", {})
    if not isinstance(dev_tasks, dict):
        return ActionResult.make_failure(
            f"Expected dev-tasks to be a dictionary in: {action_package_yaml_path}. Found: {dev_tasks}"
        )

    for task_name, task_contents in dev_tasks.items():
        if not isinstance(task_name, str_with_location):
            return ActionResult.make_failure(
                f"Expected dev-task key to be a string in: {action_package_yaml_path} (dev-task: {task_name}: {task_contents})."
            )
        if not isinstance(task_contents, str_with_location):
            return ActionResult.make_failure(
                f"Expected dev-task value to be a string in: {action_package_yaml_path} (dev-task: {task_name}: {task_contents})."
            )

    return ActionResult.make_success(dev_tasks)
