import json
from typing import TypedDict

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.ep_resolve_interpreter import (
    EPResolveInterpreter,
    IInterpreterInfo,
)
from sema4ai_ls_core.pluginmanager import PluginManager
from sema4ai_ls_core.protocols import ActionResult, IMonitor

log = get_logger(__name__)

_MetadataType = TypedDict(
    "MetadataType",
    {
        "actions-spec-version": str,
        "actions": list[dict] | None,
        "data": dict,
        "data-spec-version": str,
    },
)


class ExtractedActionInfo(TypedDict):
    # Default values that can be used to bootstrap the action input.
    default_values: dict
    # Informal representation of the schema.
    informal_schema_representation: list[str]
    # JSON Schema of the action input.
    json_schema: dict
    # Schema related to the managed params (secrets/oauth2).
    managed_params_json_schema: dict
    action_name: str
    action_relative_path: str


def extract_info(
    action_info_found: list, action_package_yaml_directory: str
) -> dict[str, ExtractedActionInfo]:
    """
    Args:
        action_info_found: The result from calling 'collect_actions_full_and_slow'.
    """
    from pathlib import Path

    from sema4ai_code.robo.actions_form_data import (
        form_data_to_payload,
        properties_to_form_data,
    )

    action_name_to_extracted_info: dict[str, ExtractedActionInfo] = {}
    for item in action_info_found:
        action_name = item.get("name", "")
        target_file = item.get("file", "")
        relative_path = ""
        # Now, make relative to the action_package_yaml_directory
        if target_file:
            relative_path = (
                Path(target_file).relative_to(action_package_yaml_directory).as_posix()
            )

        input_schema = item.get("input_schema", {})
        managed_params_schema = item.get("managed_params_schema", {})
        as_form_data = properties_to_form_data(input_schema)
        payload = form_data_to_payload(as_form_data)

        if managed_params_schema:
            for (
                managed_param_name,
                managed_param_schema,
            ) in managed_params_schema.items():
                if isinstance(managed_param_schema, dict):
                    oauth2_requests: dict = {}
                    if managed_param_schema.get("type") == "Secret":
                        payload[managed_param_name] = "<specify-secret>"
                    elif managed_param_schema.get("type") == "OAuth2Secret":
                        oauth2_requests[managed_param_name] = {
                            "type": managed_param_schema.get("type"),
                            "provider": managed_param_schema.get("provider"),
                            "scopes": managed_param_schema.get("scopes"),
                            "access_token": "<access-token-will-be-requested-by-vscode>",
                        }

                    if oauth2_requests:
                        payload["vscode:request:oauth2"] = oauth2_requests

        informal_schema_representation = []
        for d in as_form_data:
            informal_schema_representation.append(f"{d.name}: {d.value_as_str()}")

        full: ExtractedActionInfo = {
            "default_values": payload,
            "informal_schema_representation": informal_schema_representation,
            "json_schema": input_schema,
            "managed_params_json_schema": managed_params_schema,
            "action_name": action_name,
            "action_relative_path": relative_path,
        }

        action_name_to_extracted_info[item.get("name")] = full
    return action_name_to_extracted_info


def _execute_within_user_env(
    pm: PluginManager,
    uri: str,
    args: list[str],
    monitor: IMonitor,
    cwd: str,
    returns_json=True,
) -> ActionResult:
    from sema4ai_ls_core.basic import launch_and_return_future

    try:
        for ep in pm.get_implementations(EPResolveInterpreter):
            interpreter_info: IInterpreterInfo = ep.get_interpreter_info_for_doc_uri(
                uri
            )
            if interpreter_info is not None:
                environ = interpreter_info.get_environ()
                python_exe = interpreter_info.get_python_exe()
                future = launch_and_return_future(
                    [python_exe] + args,
                    environ=environ,
                    cwd=cwd,
                    timeout=30,
                    monitor=monitor,
                )
                result = future.result(30)
                if result.returncode == 0:
                    if result.stdout:
                        if returns_json:
                            try:
                                return ActionResult.make_success(
                                    json.loads(result.stdout)
                                )
                            except Exception:
                                msg = f"Unable to parse as json: {result.stdout}"
                                log.exception(msg)
                                return ActionResult.make_failure(msg)
                        else:
                            return ActionResult.make_success(result.stdout)
                if result.stderr:
                    error_msg = (
                        f"Found errors while running {args[2]} errors: {result.stderr}"
                    )
                    log.info(error_msg)
                break
    except BaseException as e:
        message = f"Unable to execute {args[2]} command. Error: {e}"
        log.exception(message)
        return ActionResult.make_failure(message)

    return ActionResult.make_failure(f"Unable to execute {args[2]} command")


def _call_sema4ai_actions(
    pm: PluginManager, monitor: IMonitor, argument: str, uri: str
) -> ActionResult:
    """Note: the way this works is that we'll launch a separate script using the user
    environment to collect the actions information.

    The major reason this is done (vs just loading the actions in the current
    environment is that if we used the current environment, if the user uses a new
    version of python we could potentially have a syntax error or load libraries not
    available to the VSCode extension (because for listing the actions we need to
    actually load the user code to resolve things such as complex models).
    """
    from pathlib import Path

    from sema4ai_ls_core import uris

    if not uri:
        return ActionResult.make_failure("No uri given")

    path = Path(uris.to_fs_path(uri))
    file_name = path.name
    args = [
        "-m",
        "sema4ai.actions",
        argument,
        "--skip-lint",
    ]

    if not path.is_dir():
        # If a file is given, we'll use the glob to list the actions just in that file.
        args.append("--glob")
        args.append(file_name)
        cwd = str(path.parent)
    else:
        cwd = str(path)

    return _execute_within_user_env(pm, uri, args, monitor, cwd)


def _get_actions_version(
    pm: PluginManager, uri: str, monitor: IMonitor
) -> ActionResult:
    from pathlib import Path

    from sema4ai_ls_core import uris

    libname = "sema4ai.actions"
    args = ["-c", f"import {libname};print({libname}.__version__)"]

    path = Path(uris.to_fs_path(uri))
    if not path.is_dir():
        cwd = str(path.parent)
    else:
        cwd = str(path)

    error_msg = f"""Unable to get {libname} version.

    This usually means that `{libname}` is not installed in the python
    environment (make sure that `{libname.replace('.', '-')}`
    is defined in your `package.yaml`).
    """

    result = _execute_within_user_env(pm, uri, args, monitor, cwd, returns_json=False)
    if result.success and result.result:
        try:
            result.result = tuple(int(x) for x in result.result.strip().split("."))
        except Exception:
            result.message = error_msg
    else:
        result.message = error_msg

    return result


def collect_actions_full_and_slow(
    pm: PluginManager, uri: str, monitor: IMonitor
) -> ActionResult:
    return _call_sema4ai_actions(pm, monitor, "list", uri)


def get_metadata(pm: PluginManager, uri: str, monitor: IMonitor) -> ActionResult[dict]:
    actions_library_result = _get_actions_version(pm, uri, monitor)
    if not actions_library_result.success:
        return actions_library_result

    if actions_library_result.result and actions_library_result.result > (1, 0, 1):
        return _call_sema4ai_actions(pm, monitor, "metadata", uri)
    else:
        result = _call_sema4ai_actions(pm, monitor, "list", uri)
        if result.success:
            metadata: _MetadataType = {
                "actions-spec-version": "v1",
                "actions": result.result or [],
                "data": {"datasources": []},
                "data-spec-version": "v1",
            }
            result.result = metadata
        return result
