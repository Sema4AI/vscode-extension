import json
import logging
import os.path
import sys
import time
import typing
from pathlib import Path
from typing import Dict, List, Optional
from unittest import mock

import pytest
from sema4ai_code.inspector.common import (
    STATE_CLOSED,
    STATE_NOT_PICKING,
    STATE_OPENED,
    STATE_PICKING,
)
from sema4ai_code.protocols import (
    ActionResult,
    LocalAgentPackageOrganizationInfoDict,
    LocalPackageMetadataInfoDict,
    WorkspaceInfoDict,
)
from sema4ai_ls_core.basic import wait_for_condition
from sema4ai_ls_core.callbacks import Callback
from sema4ai_ls_core.ep_resolve_interpreter import (
    DefaultInterpreterInfo,
    IInterpreterInfo,
)
from sema4ai_ls_core.pluginmanager import PluginManager
from sema4ai_ls_core.unittest_tools.cases_fixture import CasesFixture

from sema4ai_code_tests.fixtures import RCC_TEMPLATE_NAMES, RccPatch
from sema4ai_code_tests.protocols import IRobocorpLanguageServerClient

log = logging.getLogger(__name__)


def test_missing_message(
    language_server: IRobocorpLanguageServerClient, ws_root_path, initialization_options
):
    from sema4ai_ls_core.protocols import IErrorMessage

    language_server.initialize(
        ws_root_path, initialization_options=initialization_options
    )

    # Just ignore this one (it's not a request because it has no id).
    language_server.write(
        {
            "jsonrpc": "2.0",
            "method": "invalidMessageSent",
            "params": {"textDocument": {"uri": "untitled:Untitled-1", "version": 2}},
        }
    )

    # Make sure that we have a response if it's a request (i.e.: it has an id).
    msg = typing.cast(
        IErrorMessage,
        language_server.request(
            {
                "jsonrpc": "2.0",
                "id": "22",
                "method": "invalidMessageSent",
                "params": {
                    "textDocument": {"uri": "untitled:Untitled-1", "version": 2}
                },
            }
        ),
    )

    assert msg["error"]["code"] == -32601


def test_exit_with_parent_process_died(
    language_server_process: IRobocorpLanguageServerClient,
    language_server_io,
    ws_root_path,
    initialization_options,
):
    """
    :note: Only check with the language_server_io (because that's in another process).
    """
    import subprocess

    from sema4ai_ls_core.process import is_process_alive, kill_process_and_subprocesses
    from sema4ai_ls_core.unittest_tools.fixtures import wait_for_test_condition

    language_server = language_server_io
    dummy_process = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(10000)"]
    )

    language_server.initialize(
        ws_root_path,
        process_id=dummy_process.pid,
        initialization_options=initialization_options,
    )

    assert is_process_alive(dummy_process.pid)
    assert is_process_alive(language_server_process.pid)

    kill_process_and_subprocesses(dummy_process.pid)

    wait_for_test_condition(lambda: not is_process_alive(dummy_process.pid))
    wait_for_test_condition(lambda: not is_process_alive(language_server_process.pid))
    language_server_io.require_exit_messages = False


def test_list_rcc_robot_templates(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path: str,
    rcc_location: str,
    tmpdir,
) -> None:
    from sema4ai_code import commands

    assert os.path.exists(rcc_location)
    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_LIST_ROBOT_TEMPLATES_INTERNAL, []
    )["result"]
    assert result["success"]
    template_names = [template["name"] for template in result["result"]]
    assert template_names == RCC_TEMPLATE_NAMES

    target = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(added_folders=[target], removed_folders=[])

    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [
            {
                "directory": target,
                "name": "example",
                "template": template_names[0],
            }
        ],
    )["result"]
    assert result["success"]
    assert not result["message"]

    # Error
    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [{"directory": target, "name": "example", "template": "01-python"}],
    )["result"]
    assert not result["success"]
    assert "Error creating robot" in result["message"]
    assert "not empty" in result["message"]
    assert "b'" not in result["message"]

    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [{"directory": ws_root_path, "name": "example2", "template": "01-python"}],
    )["result"]
    assert result["success"]

    result = language_server.execute_command(
        commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL, []
    )["result"]
    assert result["success"]
    folder_info_lst: List[LocalPackageMetadataInfoDict] = result["result"]
    assert len(folder_info_lst) == 2
    assert set([x["name"] for x in folder_info_lst]) == {"example", "example2"}


def test_list_local_robots(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path: str,
    rcc_location: str,
    tmpdir,
) -> None:
    from sema4ai_code import commands

    assert os.path.exists(rcc_location)
    language_server = language_server_initialized

    target = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(added_folders=[target], removed_folders=[])

    language_server.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [
            {
                "directory": target,
                "name": "example",
                "template": "01-python",
            }
        ],
    )
    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [{"directory": ws_root_path, "name": "example2", "template": "01-python"}],
    )["result"]
    assert result["success"]

    language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{ws_root_path}/agent1",
                "name": "Test agent",
            }
        ],
    )

    assert os.path.exists(
        f"{ws_root_path}/agent1/actions/MyActions"
    ), "actions/MyActions not created when creating agent."
    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{ws_root_path}/agent1/actions/MyActions/action1",
                "name": "example2",
                "template": "basic",
            }
        ],
    )["result"]
    assert result["success"]

    result = language_server.execute_command(
        commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL, []
    )["result"]

    assert result["success"]
    folder_info_lst: List[LocalPackageMetadataInfoDict] = result["result"]
    assert sorted(set([x["name"] for x in folder_info_lst])) == sorted(
        {
            "Test agent",
            "example",
            "example2",
        }
    )
    for info in folder_info_lst:
        if info["name"] == "agent1":
            name_to_org = dict(
                (org["name"], org) for org in (info["organizations"] or [])
            )

            assert set(name_to_org.keys()) == {"MyActions", "Sema4.ai"}
            action_packages = name_to_org["MyActions"]["actionPackages"]
            assert len(action_packages) == 1
            for action_package in action_packages:
                assert "Basic Template Package" == action_package["name"]
    print(json.dumps(folder_info_lst, indent=4))


def test_list_local_agent_packages_with_sub_packages(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path: str,
    agent_cli_location: str,
    tmpdir,
) -> None:
    from sema4ai_code import commands

    assert os.path.exists(agent_cli_location)
    language_server = language_server_initialized

    agent_package_name = "Test Agent"

    # We create one Action package to test whether the command correctly ignores it.
    action_package_name_one = "action_package_one"
    action_package_name_two = "action_package_two"
    action_package_name_three = "action_package_three"

    organization_one = "MyActions"
    organization_two = "Sema4.ai"

    target_directory = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(
        added_folders=[target_directory], removed_folders=[]
    )

    agent_package_directory = f"{target_directory}/{agent_package_name}"
    agent_actions_directory = f"{agent_package_directory}/actions"

    language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": agent_package_directory,
                "name": "Test Agent",
            }
        ],
    )

    language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{agent_actions_directory}/{organization_one}/{action_package_name_one}",
                "template": "minimal",
                "name": "Minimal Action 1",
            }
        ],
    )

    language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{agent_actions_directory}/{organization_one}/{action_package_name_two}",
                "template": "minimal",
                "name": "Minimal Action 2",
            }
        ],
    )

    language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{agent_actions_directory}/{organization_two}/{action_package_name_three}",
                "template": "minimal",
                "name": "Minimal Action 3",
            }
        ],
    )

    result = language_server.execute_command(
        commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL,
        [],
    )["result"]

    assert result["success"]

    packages: List[LocalPackageMetadataInfoDict] = result["result"]

    assert len(packages) == 1
    assert set([x["name"] for x in packages]) == {agent_package_name}
    assert os.path.exists(f"{agent_package_directory}/agent-spec.yaml")

    package = packages[0]
    assert package

    organizations: Optional[List[LocalAgentPackageOrganizationInfoDict]] = package[
        "organizations"
    ]
    assert organizations

    assert len(organizations) == 2
    assert set([x["name"] for x in organizations]) == {
        organization_one,
        organization_two,
    }

    action_packages: List[LocalPackageMetadataInfoDict] = (
        organizations[0]["actionPackages"] + organizations[1]["actionPackages"]
    )

    assert organizations is not None
    assert len(action_packages) == 3

    action_package_one = next(
        (
            x
            for x in action_packages
            if os.path.basename(x["directory"]) == action_package_name_one
        ),
        None,
    )
    action_package_two = next(
        (
            x
            for x in action_packages
            if os.path.basename(x["directory"]) == action_package_name_two
        ),
        None,
    )
    action_package_three = next(
        (
            x
            for x in action_packages
            if os.path.basename(x["directory"]) == action_package_name_three
        ),
        None,
    )

    assert action_package_one is not None
    assert os.path.basename(action_package_one["directory"]) == action_package_name_one

    assert action_package_two is not None
    assert os.path.basename(action_package_two["directory"]) == action_package_name_two

    assert action_package_three is not None
    assert (
        os.path.basename(action_package_three["directory"]) == action_package_name_three
    )


def test_list_local_agent_packages_cache(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path: str,
    agent_cli_location: str,
    tmpdir,
) -> None:
    from sema4ai_code import commands

    assert os.path.exists(agent_cli_location)
    language_server = language_server_initialized

    agent_package_name = "test_agent"
    organization_name = "MyActions"

    # We create one Action package to test whether the command correctly ignores it.
    action_package_name_one = "action_package_one"

    target_directory = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(
        added_folders=[target_directory], removed_folders=[]
    )

    agent_package_directory = f"{target_directory}/{agent_package_name}"
    agent_actions_directory = f"{agent_package_directory}/actions"

    language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": agent_package_directory,
                "name": "Test Agent",
            }
        ],
    )

    language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "directory": f"{agent_actions_directory}/{organization_name}/{action_package_name_one}",
                "template": "minimal",
                "name": "Minimal Action 1",
            }
        ],
    )

    result = language_server.execute_command(
        commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL,
        [],
    )["result"]

    assert result["success"]

    packages: List[LocalPackageMetadataInfoDict] = result["result"]

    assert len(packages) == 1
    assert os.path.exists(f"{agent_package_directory}/agent-spec.yaml")

    package = packages[0]

    organizations: Optional[List[LocalAgentPackageOrganizationInfoDict]] = package[
        "organizations"
    ]
    assert organizations

    # Agent CLI always creates two organizations by default - MyActions and Sema4.ai.
    assert len(organizations) == 2

    organization_with_actions = next(
        (x for x in organizations if x["name"] == organization_name), None
    )

    assert organization_with_actions is not None

    action_packages = organization_with_actions["actionPackages"]

    assert action_packages is not None
    assert len(action_packages) == 1

    result = language_server.execute_command(
        commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL,
        [],
    )["result"]

    assert result["success"]

    packages = result["result"]

    # We want to test whether the result is correct given subsequent calls.
    # These assertions tests, if no Agent package or sub packages are duplicated.
    assert len(packages) == 1

    organizations = packages[0]["organizations"]
    assert organizations
    assert len(organizations) == 2

    organization_with_actions = next(
        (x for x in organizations if x["name"] == organization_name), None
    )

    assert organization_with_actions is not None

    action_packages = organization_with_actions["actionPackages"]

    assert action_packages is not None
    assert len(action_packages) == 1


def get_workspace_from_name(
    workspace_list: List[WorkspaceInfoDict], workspace_name: str
) -> WorkspaceInfoDict:
    for ws in workspace_list:
        if ws["workspaceName"] == workspace_name:
            return ws
    raise AssertionError(f"Did not find workspace: {workspace_name}")


def _get_as_name_to_sort_key_and_package_id(lst: List[WorkspaceInfoDict]):
    name_to_sort_key = {}
    for workspace_info in lst:
        for package_info in workspace_info["packages"]:
            name_to_sort_key[package_info["name"]] = (
                package_info["sortKey"],
                package_info["id"],
            )
    return name_to_sort_key


def test_get_plugins_dir(
    language_server_initialized: IRobocorpLanguageServerClient,
):
    client = language_server_initialized
    result = client.get_plugins_dir()

    assert result
    assert result.endswith("plugins")
    assert os.path.exists(result)


def test_cloud_list_workspaces_sorting(
    language_server_initialized: IRobocorpLanguageServerClient,
    rcc_patch: RccPatch,
    tmpdir,
):
    client = language_server_initialized
    root_dir = str(tmpdir.join("root").mkdir())

    rcc_patch.apply()

    result = client.cloud_list_workspaces()
    assert result[
        "success"
    ], f'Expected the cloud to list workspaces. Error: {result["message"]}'
    ws_info = result["result"]
    assert ws_info

    ci_workspace_info = get_workspace_from_name(ws_info, "CI workspace")

    result = client.upload_to_new_robot(
        ci_workspace_info["workspaceId"],
        f"New package {time.time()}",
        "<dir not there>",
    )
    assert not result["success"]
    msg = result["message"]
    assert msg and "to exist" in msg

    result = client.upload_to_new_robot(
        ci_workspace_info["workspaceId"], "New package", root_dir
    )
    assert result["success"]

    result = client.cloud_list_workspaces()
    assert result["success"]

    res = result["result"]
    assert res
    assert _get_as_name_to_sort_key_and_package_id(res) == {
        "Package Name 1": ("00010package name 1", "452"),
        "Package Name 2": ("00010package name 2", "453"),
        "New package": ("00000new package", "2323"),
    }

    result = client.upload_to_existing_activity(
        ci_workspace_info["workspaceId"], "453", root_dir
    )
    assert result["success"]


def test_cloud_list_workspaces_basic(
    language_server_initialized: IRobocorpLanguageServerClient,
    rcc_patch: RccPatch,
    data_regression,
):
    client = language_server_initialized

    rcc_patch.apply()

    result1 = client.cloud_list_workspaces()
    assert result1["success"]

    data_regression.check(result1)

    rcc_patch.disallow_calls()
    result2 = client.cloud_list_workspaces()
    assert result2["success"]
    assert result1["result"] == result2["result"]

    result3 = client.cloud_list_workspaces(refresh=True)
    assert "message" in result3

    # Didn't work out because the mock forbids it (as expected).
    assert not result3["success"]
    msg = result3["message"]
    assert msg and "This should not be called at this time" in msg


def test_cloud_list_workspaces_errors_single_ws_not_available(
    language_server_initialized: IRobocorpLanguageServerClient,
    rcc_patch: RccPatch,
    data_regression,
):
    client = language_server_initialized

    def custom_handler(args, *sargs, **kwargs):
        if args[:4] == ["cloud", "workspace", "--workspace", "workspace_id_1"]:
            # List packages for workspace 1
            return ActionResult(
                success=False,
                message="""{"error":{"code":"WORKSPACE_TREE_NOT_FOUND","subCode":"","message":"workspace tree not found"}""",
                result=None,
            )

    rcc_patch.custom_handler = custom_handler
    rcc_patch.apply()

    result1 = client.cloud_list_workspaces()

    # i.e.: Should show only workspace 2 as workspace 1 errored.
    data_regression.check(result1)

    rcc_patch.custom_handler = None

    result2 = client.cloud_list_workspaces()
    assert result1["result"] == result2["result"]  # Use cached

    result3 = client.cloud_list_workspaces(refresh=True)
    data_regression.check(result3, basename="test_cloud_list_workspaces_basic")


def test_cloud_list_workspaces_errors_no_ws_available(
    language_server_initialized: IRobocorpLanguageServerClient, rcc_patch: RccPatch
):
    client = language_server_initialized

    def custom_handler(args, *sargs, **kwargs):
        if args[:3] == ["cloud", "workspace", "--workspace"]:
            # List packages for workspace 1
            return ActionResult(
                success=False,
                message="""{"error":{"code":"WORKSPACE_TREE_NOT_FOUND","subCode":"","message":"workspace tree not found"}""",
                result=None,
            )

    rcc_patch.custom_handler = custom_handler
    rcc_patch.apply()

    result1 = client.cloud_list_workspaces()

    assert not result1["success"]


def test_upload_to_cloud(
    language_server_initialized: IRobocorpLanguageServerClient,
    ci_credentials: str,
    ws_root_path: str,
    monkeypatch,
):
    from sema4ai_code import commands
    from sema4ai_code.protocols import PackageInfoDict
    from sema4ai_code.rcc import Rcc

    client = language_server_initialized

    client.DEFAULT_TIMEOUT = 10  # The cloud may be slow.

    result = client.execute_command(commands.SEMA4AI_IS_LOGIN_NEEDED_INTERNAL, [])[
        "result"
    ]
    assert result["result"], "Expected login to be needed."

    result = client.execute_command(
        commands.SEMA4AI_CLOUD_LOGIN_INTERNAL, [{"credentials": "invalid"}]
    )["result"]
    assert not result["success"], "Expected login to be unsuccessful."

    result = client.execute_command(
        commands.SEMA4AI_CLOUD_LOGIN_INTERNAL, [{"credentials": ci_credentials}]
    )["result"]
    assert result["success"], "Expected login to be successful."

    result = client.cloud_list_workspaces()
    assert result["success"]
    result_workspaces: List[WorkspaceInfoDict] = result["result"]
    assert result_workspaces, "Expected to have the available workspaces and packages."
    found = [x for x in result_workspaces if x["workspaceName"] == "CI workspace"]
    assert (
        len(found) == 1
    ), f'Expected to find "CI workspace". Found: {result_workspaces}'

    found_packages = [x for x in found[0]["packages"] if x["name"] == "CI activity"]
    assert (
        len(found_packages) == 1
    ), f'Expected to find "CI activity". Found: {result_workspaces}'

    found_package: PackageInfoDict = found_packages[0]
    result = client.execute_command(
        commands.SEMA4AI_CREATE_ROBOT_INTERNAL,
        [{"directory": ws_root_path, "name": "example", "template": "01-python"}],
    )["result"]
    assert result["success"]

    directory = os.path.join(ws_root_path, "example")
    result = client.upload_to_existing_activity(
        found_package["workspaceId"], found_package["id"], directory
    )
    assert result["success"]

    def mock_run_rcc(self, args, *sargs, **kwargs):
        if args[:3] == ["cloud", "new", "--workspace"]:
            return ActionResult(
                success=True,
                message=None,
                result="Created new robot named 'New package 1597082853.2224553' with identity 453.\n",
            )
        if args[:3] == ["cloud", "push", "--directory"]:
            return ActionResult(success=True, message=None, result="OK.\n")

        raise AssertionError(f"Unexpected args: {args}")

    # Note: it should work without the monkeypatch as is, but it'd create a dummy
    # package and we don't have an API to remove it.
    monkeypatch.setattr(Rcc, "_run_rcc", mock_run_rcc)

    result = client.upload_to_new_robot(
        found_package["workspaceId"], f"New package {time.time()}", directory
    )
    assert result["success"]


def test_logout_cloud(
    language_server_initialized: IRobocorpLanguageServerClient, monkeypatch
):
    from sema4ai_code import commands
    from sema4ai_code.rcc import Rcc

    client = language_server_initialized

    client.DEFAULT_TIMEOUT = 10  # The cloud may be slow.

    def mock_run_rcc(self, args, *sargs, **kwargs):
        from sema4ai_code.rcc import ACCOUNT_NAME

        if args[:5] == ["config", "credentials", "--account", ACCOUNT_NAME, "--delete"]:
            return ActionResult(success=True, message=None, result="OK.\n")

        raise AssertionError(f"Unexpected args: {args}")

    def mock_credentials_valid(self):
        # Mock rcc.credentials_valid() to return False after "successful" removal from cloud
        return False

    # Note: it should work without the monkeypatch as is, but it'd create a dummy
    # (check test_upload_to_cloud for details)
    # package and we don't have an API to remove it.
    monkeypatch.setattr(Rcc, "_run_rcc", mock_run_rcc)
    monkeypatch.setattr(Rcc, "credentials_valid", mock_credentials_valid)
    result = client.execute_command(commands.SEMA4AI_CLOUD_LOGOUT_INTERNAL, [])[
        "result"
    ]
    assert result["success"]


def test_lru_disk_commands(language_server_initialized: IRobocorpLanguageServerClient):
    from sema4ai_code import commands

    client = language_server_initialized

    def save_to_lru(name: str, entry: str, lru_size: int):
        result = client.execute_command(
            commands.SEMA4AI_SAVE_IN_DISK_LRU,
            [{"name": name, "entry": entry, "lru_size": lru_size}],
        )["result"]

        assert result["success"]

    def get_from_lru(name: str) -> list:
        result = client.execute_command(
            commands.SEMA4AI_LOAD_FROM_DISK_LRU, [{"name": name}]
        )
        return result["result"]

    assert get_from_lru("my_lru") == []

    save_to_lru("my_lru", "entry1", lru_size=2)
    assert get_from_lru("my_lru") == ["entry1"]

    save_to_lru("my_lru", "entry2", lru_size=2)
    assert get_from_lru("my_lru") == ["entry2", "entry1"]

    save_to_lru("my_lru", "entry1", lru_size=2)
    assert get_from_lru("my_lru") == ["entry1", "entry2"]

    save_to_lru("my_lru", "entry3", lru_size=2)
    assert get_from_lru("my_lru") == ["entry3", "entry1"]


def _compute_robot_launch_from_robocorp_code_launch(
    client: IRobocorpLanguageServerClient, task: str, robot: str, **kwargs
):
    from sema4ai_code import commands

    args = {"robot": robot, "task": task, "name": "Launch Name", "request": "launch"}
    args.update(kwargs)
    result = client.execute_command(
        commands.SEMA4AI_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH, [args]
    )["result"]
    return result


def test_compute_robot_launch_from_robocorp_code_launch(
    language_server_initialized: IRobocorpLanguageServerClient, cases: CasesFixture
):
    client = language_server_initialized

    robot = cases.get_path("custom_envs/simple-web-scraper/robot.yaml")
    result = _compute_robot_launch_from_robocorp_code_launch(
        client, "Web scraper", robot
    )
    assert result["success"]
    r = result["result"]

    assert r["target"] == "<target-in-args>"
    assert os.path.samefile(r["cwd"], cases.get_path("custom_envs/simple-web-scraper"))
    assert os.path.samefile(
        cases.get_path("custom_envs/simple-web-scraper/tasks"),
        os.path.join(r["cwd"], r["args"][-1]),
    )
    del r["target"]
    del r["cwd"]
    r["args"].pop(-1)

    assert r == {
        "type": "robotframework-lsp",
        "name": "Launch Name",
        "request": "launch",
        "args": ["-d", "output", "--logtitle", "Task log"],
        "terminal": "integrated",
        "internalConsoleOptions": "neverOpen",
    }


def test_compute_python_launch_from_robocorp_code_launch(
    language_server_initialized: IRobocorpLanguageServerClient, cases: CasesFixture
):
    client = language_server_initialized

    robot = cases.get_path("custom_envs/pysample/robot.yaml")
    result = _compute_robot_launch_from_robocorp_code_launch(
        client, "Default", robot, pythonExe="c:/temp/py.exe"
    )
    assert result["success"]
    r = result["result"]

    assert os.path.samefile(
        r["program"], cases.get_path("custom_envs/pysample/task.py")
    )
    assert os.path.samefile(r["cwd"], cases.get_path("custom_envs/pysample"))
    del r["program"]
    del r["cwd"]

    assert r == {
        "type": "python",
        "name": "Launch Name",
        "request": "launch",
        "pythonArgs": [],
        "args": [],
        "python": "c:/temp/py.exe",
        "console": "integratedTerminal",
        "internalConsoleOptions": "neverOpen",
    }


@pytest.mark.skipif(
    sys.platform != "win32", reason="As the base platform changes so does the result."
)
def test_hover_conda_yaml_conda_forge_versions(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud,
    patch_conda_forge_cloud_setup,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/conda.yaml"
    txt = """
channels:
  - conda-forge

dependencies:
  - python=3.7
  - pip=22.1.2
  - mu_repo=1.8.2"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 10
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


@pytest.mark.skipif(
    sys.platform != "win32", reason="As the base platform changes so does the result."
)
def test_hover_package_yaml_conda_forge_versions(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud,
    patch_conda_forge_cloud_setup,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/package.yaml"
    txt = """
name: Name
description: Action package description
version: 0.0.1
documentation: https://github.com/...
dependencies:
  conda-forge:
  - python=3.7
  - pip=22.1.2
  - mu_repo=1.8.2"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 10
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


@pytest.mark.skipif(
    sys.platform != "win32", reason="As the base platform changes so does the result."
)
def test_hover_conda_yaml_conda_forge_numpy_versions(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/conda.yaml"
    txt = """
channels:
  - conda-forge

dependencies:
  - numpy"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 2
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


@pytest.mark.skipif(
    sys.platform != "win32", reason="As the base platform changes so does the result."
)
def test_hover_conda_yaml_conda_forge_python_versions(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/conda.yaml"
    txt = """
channels:
  - conda-forge

dependencies:
  - python=3.9"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 7
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


def test_hover_conda_yaml_pypi_versions(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/conda.yaml"
    txt = """
channels:
  - conda-forge

dependencies:
  - python=3.7               # https://pyreadiness.org/3.9/
  - pip=22.1.2                  # https://pip.pypa.io/en/stable/news/
  - pip:
      # Define pip packages here -> https://pypi.org/
      - rpaframework==22.5.3"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 10
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


def test_hover_conda_yaml_versions_no_releases(
    language_server_initialized: IRobocorpLanguageServerClient,
    data_regression,
    patch_pypi_cloud_no_releases_12_months,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/conda.yaml"
    txt = """
channels:
  - conda-forge

dependencies:
  - python=3.7               # https://pyreadiness.org/3.9/
  - pip=22.1.2                  # https://pip.pypa.io/en/stable/news/
  - pip:
      # Define pip packages here -> https://pypi.org/
      - rpaframework==22.5.3"""
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    col -= 10
    ret = client.hover(uri, line, col)
    data_regression.check(ret["result"])


def test_hover_browser_integration(
    language_server_initialized: IRobocorpLanguageServerClient,
):
    from sema4ai_ls_core.workspace import Document

    client = language_server_initialized
    uri = "x/y/locators.json"
    txt = """
    "Browser.Locator.01": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAACgAAAA" """
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    ret = client.hover(uri, line, col)
    assert ret["result"] == {
        "contents": {
            "kind": "markdown",
            "value": "![Screenshot](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAA)",
        },
        "range": {
            "start": {"line": 2, "character": 56},
            "end": {"line": 2, "character": 56},
        },
    }


def test_hover_image_integration(
    language_server_initialized: IRobocorpLanguageServerClient, tmpdir
):
    import base64

    from sema4ai_ls_core import uris
    from sema4ai_ls_core.workspace import Document

    from sema4ai_code_tests.fixtures import IMAGE_IN_BASE64

    locators_json = tmpdir.join("locators.json")
    locators_json.write_text("", "utf-8")

    imgs_dir = tmpdir.join(".images")
    imgs_dir.mkdir()
    img1 = imgs_dir.join("img1.png")
    with img1.open("wb") as stream:
        stream.write(base64.b64decode(IMAGE_IN_BASE64))

    client = language_server_initialized
    uri = uris.from_fs_path(str(locators_json))
    txt = """
    "Image.Locator.01": {
        "path": ".images/img1.png",
        "source": ".images/img1.png" """
    doc = Document("", txt)
    client.open_doc(uri, 1, txt)
    line, col = doc.get_last_line_col()
    ret = client.hover(uri, line, col)
    result = ret["result"]
    value = result["contents"].pop("value")
    assert value.startswith("![Screenshot](data:image/png;base64,iVBORw0KGgo")
    assert value.endswith(")")

    assert ret["result"] == {
        "contents": {
            "kind": "markdown",
            # "value": "![Screenshot](data:image/png;base64,iVBORw0KGgo...)",
        },
        "range": {
            "start": {"line": 3, "character": 37},
            "end": {"line": 3, "character": 37},
        },
    }


def test_obtain_locator_info(
    language_server_initialized: IRobocorpLanguageServerClient, tmpdir, data_regression
) -> None:
    from sema4ai_code import commands

    # robot.yaml contents don't matter for this test (it just needs to be there).
    robot_yaml = tmpdir.join("robot.yaml")
    robot_yaml.write("")
    tmpdir.join("locators.json").write(
        """{
    "Browser.Locator.00": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAVsAAAAiCAYAAADxlXpQAAAAAXNSR0IArs4c6QAAAKFJREFUeJzt1lENgDAUBMGClPr3+FDBNoEZBfe1uWtmZgHwqvv0AIA/EFuAgNgCBMQWICC2AAGxBQiILUBAbAEC91pr7b1P7wD4NM8WICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBMQWICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBK6ZmdMjAL7OswUIiC1AQGwBAmILEBBbgIDYAgTEFiDwADUBCKHOZd2rAAAAAElFTkSuQmCC",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "name",
        "type": "browser",
        "value": "q"
    },
    "Browser.Locator.01": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAsCAYAAAAXb/p7AAAAAXNSR0IArs4c6QAAAJxJREFUWIXt17EOgCAMhOFqHPrQDAx9aDbcTYw9jgjDfYsL0T+FGD167902dq4O+KJAlgJZCmQpkKVAlgJZCmRtH3ghiyPCWmv0Q93dSimptdAEZ8Sh9xna4lordUUcyD9JdlsyIiK1ThN8owmyshOE3oNPyERGpmf2Y+Ao6Ay6+5SHIveBzuAK238sKJClQJYCWQpkKZClQJYCWTdtZlHGc2zySwAAAABJRU5ErkJggg==",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "class",
        "type": "browser",
        "value": "J9leP"
    }
}"""
    )

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_GET_LOCATORS_JSON_INFO, [{"robotYaml": str(robot_yaml)}]
    )["result"]
    assert result["success"]
    res = result["result"]
    new_res = []
    for item in res:
        new_item = {}
        for key, val in item.items():
            if key == "filePath":
                val = os.path.basename(val)
            new_item[key] = val
        new_res.append(new_item)
    data_regression.check(new_res)


def test_remove_locator(
    language_server_initialized: IRobocorpLanguageServerClient, tmpdir, data_regression
) -> None:
    import json

    from sema4ai_code import commands

    # robot.yaml contents don't matter for this test (it just needs to be there).
    robot_yaml = tmpdir.join("robot.yaml")
    robot_yaml.write("")
    locator_file = tmpdir.join("locators.json")
    locator_file.write(
        """{
    "Browser.Locator.00": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAVsAAAAiCAYAAADxlXpQAAAAAXNSR0IArs4c6QAAAKFJREFUeJzt1lENgDAUBMGClPr3+FDBNoEZBfe1uWtmZgHwqvv0AIA/EFuAgNgCBMQWICC2AAGxBQiILUBAbAEC91pr7b1P7wD4NM8WICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBMQWICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBK6ZmdMjAL7OswUIiC1AQGwBAmILEBBbgIDYAgTEFiDwADUBCKHOZd2rAAAAAElFTkSuQmCC",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "name",
        "type": "browser",
        "value": "q"
    },
    "Browser.Locator.01": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAsCAYAAAAXb/p7AAAAAXNSR0IArs4c6QAAAJxJREFUWIXt17EOgCAMhOFqHPrQDAx9aDbcTYw9jgjDfYsL0T+FGD167902dq4O+KJAlgJZCmQpkKVAlgJZCmRtH3ghiyPCWmv0Q93dSimptdAEZ8Sh9xna4lordUUcyD9JdlsyIiK1ThN8owmyshOE3oNPyERGpmf2Y+Ao6Ay6+5SHIveBzuAK238sKJClQJYCWQpkKZClQJYCWTdtZlHGc2zySwAAAABJRU5ErkJggg==",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "class",
        "type": "browser",
        "value": "J9leP"
    }
}"""
    )

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL,
        [{"robotYaml": str(robot_yaml), "name": "Browser.Locator.00"}],
    )["result"]
    locators_content = json.loads(locator_file.read())
    assert result["success"]
    assert result["result"] is None
    assert result["message"] is None
    assert "Browser.Locator.00" not in locators_content
    assert "Browser.Locator.01" in locators_content


def test_internal_load_locators_db(
    language_server_initialized: IRobocorpLanguageServerClient, tmpdir, data_regression
) -> None:
    from sema4ai_code.robocorp_language_server import RobocorpLanguageServer

    # robot.yaml contents don't matter for this test (it just needs to be there).
    robot_yaml = tmpdir.join("robot.yaml")
    robot_yaml.write("")
    locator_file = tmpdir.join("locators.json")
    locator_file.write(
        """{
    "Browser.Locator.00": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAVsAAAAiCAYAAADxlXpQAAAAAXNSR0IArs4c6QAAAKFJREFUeJzt1lENgDAUBMGClPr3+FDBNoEZBfe1uWtmZgHwqvv0AIA/EFuAgNgCBMQWICC2AAGxBQiILUBAbAEC91pr7b1P7wD4NM8WICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBMQWICC2AAGxBQiILUBAbAECYgsQEFuAgNgCBK6ZmdMjAL7OswUIiC1AQGwBAmILEBBbgIDYAgTEFiDwADUBCKHOZd2rAAAAAElFTkSuQmCC",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "name",
        "type": "browser",
        "value": "q"
    },
    "Browser.Locator.01": {
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAsCAYAAAAXb/p7AAAAAXNSR0IArs4c6QAAAJxJREFUWIXt17EOgCAMhOFqHPrQDAx9aDbcTYw9jgjDfYsL0T+FGD167902dq4O+KJAlgJZCmQpkKVAlgJZCmRtH3ghiyPCWmv0Q93dSimptdAEZ8Sh9xna4lordUUcyD9JdlsyIiK1ThN8owmyshOE3oNPyERGpmf2Y+Ao6Ay6+5SHIveBzuAK238sKJClQJYCWQpkKZClQJYCWTdtZlHGc2zySwAAAABJRU5ErkJggg==",
        "source": "https://www.google.com/?gws_rd=ssl",
        "strategy": "class",
        "type": "browser",
        "value": "J9leP"
    }
}"""
    )

    action_result = RobocorpLanguageServer._load_locators_db(robot_yaml)
    db_and_locators = action_result["result"]
    assert db_and_locators is not None
    db, locators_json_path = db_and_locators
    assert action_result["success"]
    assert action_result["message"] is None
    assert str(locators_json_path) == str(locator_file)
    assert "Browser.Locator.00" in db.locators
    assert "Browser.Locator.01" in db.locators


def test_metric(language_server_initialized: IRobocorpLanguageServerClient) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_SEND_METRIC, [{"value": "foo"}]
    )["result"]
    assert not result["success"]

    result = language_server.execute_command(
        commands.SEMA4AI_SEND_METRIC, [{"name": "bar", "value": "foo"}]
    )["result"]
    assert result["success"]


def sort_diagnostics(diagnostics):
    def key(diag_dict):
        return (
            diag_dict["source"],
            diag_dict["range"]["start"]["line"],
            diag_dict.get("code", 0),
            diag_dict["severity"],
            diag_dict["message"],
        )

    return sorted(diagnostics, key=key)


def filter_diagnostics(diagnostics):
    ret = []
    for diag in diagnostics:
        # Filter out some diagnostics.
        if "SSL_CERT_FILE is set to" in diag["message"]:
            continue

        if "Dependencies drift file" in diag["message"]:
            continue

        if "PLAYWRIGHT_BROWSERS_PATH" in diag["message"]:
            continue
        ret.append(diag)
    return ret


def test_lint_robot_integration_rcc(
    language_server_initialized: IRobocorpLanguageServerClient, tmpdir, data_regression
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.unittest_tools.fixtures import TIMEOUT

    robot_yaml = tmpdir.join("robot.yaml")
    robot_yaml_text = """
tasks:
  Obtain environment information:
    command:
      - python
      - get_env_info.py

artifactsDir: output

condaConfigFile: conda.yaml

"""
    robot_yaml.write_text(robot_yaml_text, "utf-8")

    conda_yaml = tmpdir.join("conda.yaml")
    conda_yaml.write_text(
        """
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.8
""",
        "utf-8",
    )

    language_server = language_server_initialized
    robot_yaml_uri = uris.from_fs_path(str(robot_yaml))
    message_matcher = language_server.obtain_pattern_message_matcher(
        {"method": "textDocument/publishDiagnostics"}
    )
    assert message_matcher
    language_server.open_doc(robot_yaml_uri, 1, robot_yaml_text)

    assert message_matcher.event.wait(TIMEOUT)
    diag = message_matcher.msg["params"]["diagnostics"]
    data_regression.check(filter_diagnostics(sort_diagnostics(diag)))


@pytest.fixture
def disable_rcc_diagnostics():
    from sema4ai_code._lint import DiagnosticsConfig

    DiagnosticsConfig.analyze_rcc = False
    yield
    DiagnosticsConfig.analyze_rcc = True


def test_profile_import(
    language_server_initialized: IRobocorpLanguageServerClient,
    datadir,
    disable_rcc_diagnostics,
):
    from sema4ai_code.commands import (
        SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL,
        SEMA4AI_PROFILE_IMPORT_INTERNAL,
        SEMA4AI_PROFILE_LIST_INTERNAL,
        SEMA4AI_PROFILE_SWITCH_INTERNAL,
    )
    from sema4ai_ls_core import uris

    result = language_server_initialized.execute_command(
        SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL,
        [],
    )["result"]
    assert result == ["https://pypi.org"]

    # Import sample profile.
    sample_profile = datadir / "sample_profile.yml"
    result = language_server_initialized.execute_command(
        SEMA4AI_PROFILE_IMPORT_INTERNAL,
        [{"profileUri": uris.from_fs_path(str(sample_profile))}],
    )["result"]
    assert result["success"]

    # List profiles
    result = language_server_initialized.execute_command(
        SEMA4AI_PROFILE_LIST_INTERNAL,
        [],
    )["result"]
    assert result["success"]
    loaded_profiles = result["result"]
    assert "sample" in loaded_profiles["profiles"]
    current = loaded_profiles["current"]
    if current.lower() == "default":
        current = "<remove-current-back-to-defaults>"

    try:
        result = language_server_initialized.execute_command(
            SEMA4AI_PROFILE_SWITCH_INTERNAL,
            [{"profileName": "sample"}],
        )["result"]
        assert result["success"]

        result = language_server_initialized.execute_command(
            SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL,
            [],
        )["result"]
        assert result == ["https://test.pypi.org", "https://pypi.org"]

    finally:
        result = language_server_initialized.execute_command(
            SEMA4AI_PROFILE_SWITCH_INTERNAL,
            [{"profileName": current}],
        )["result"]
        assert result["success"]


def test_lint_robot_integration_deps(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir,
    data_regression,
    disable_rcc_diagnostics,
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.unittest_tools.fixtures import TIMEOUT

    robot_yaml = tmpdir.join("robot.yaml")
    robot_yaml_text = """
tasks:
  Obtain environment information:
    command:
      - python
      - get_env_info.py

artifactsDir: output

condaConfigFile: conda.yaml

"""
    robot_yaml.write_text(robot_yaml_text, "utf-8")

    conda_yaml = tmpdir.join("conda.yaml")
    conda_yaml_text = """
    channels:
      - conda-forge
    dependencies:
      - python=3.7
      - pip=22
    """
    conda_yaml.write_text(
        conda_yaml_text,
        "utf-8",
    )

    language_server = language_server_initialized
    conda_yaml_uri = uris.from_fs_path(str(conda_yaml))
    message_matcher = language_server.obtain_pattern_message_matcher(
        {"method": "textDocument/publishDiagnostics"}
    )
    assert message_matcher
    language_server.open_doc(conda_yaml_uri, 1, conda_yaml_text)

    assert message_matcher.event.wait(TIMEOUT)
    diag = message_matcher.msg["params"]["diagnostics"]
    data_regression.check(sort_diagnostics(diag))


def test_lint_agent_spec(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir,
    data_regression,
    disable_rcc_diagnostics,
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.unittest_tools.fixtures import TIMEOUT

    agent_spec_yaml = tmpdir.join("agent-spec.yaml")
    agent_spec_yaml_text = """
bad yaml
    """
    agent_spec_yaml.write_text(
        agent_spec_yaml_text,
        "utf-8",
    )

    language_server = language_server_initialized
    agent_spec_yaml_uri = uris.from_fs_path(str(agent_spec_yaml))
    message_matcher = language_server.obtain_pattern_message_matcher(
        {"method": "textDocument/publishDiagnostics"}
    )
    assert message_matcher
    language_server.open_doc(agent_spec_yaml_uri, 1, agent_spec_yaml_text)

    assert message_matcher.event.wait(TIMEOUT)
    diag = message_matcher.msg["params"]["diagnostics"]
    data_regression.check(sort_diagnostics(diag))


def test_hover_agent_spec(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir,
    data_regression,
    disable_rcc_diagnostics,
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.workspace import Document

    agent_spec_yaml = tmpdir.join("agent-spec.yaml")
    agent_spec_yaml_text = """
agent-package:
  spec-version: v1
  agents:
  - name: New Agent
    description: Agent description
    model: GPT 4 Turbo
    type: agent
    reasoningLevel: 1
    runbooks:
      system: system.md
      retrieval: retrieval.md
    action-packages: []
    resources: []
    """
    agent_spec_yaml.write_text(
        agent_spec_yaml_text,
        "utf-8",
    )

    language_server = language_server_initialized
    agent_spec_yaml_uri = uris.from_fs_path(str(agent_spec_yaml))
    language_server.open_doc(agent_spec_yaml_uri, 1, agent_spec_yaml_text)

    doc = Document("", agent_spec_yaml_text)
    line, col = doc.get_last_line_col_with_contents("description: Agent description")
    col -= 2
    ret = language_server.hover(agent_spec_yaml_uri, line, col)
    data_regression.check(ret["result"])


def test_lint_action_package_integration_deps(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir,
    disable_rcc_diagnostics,
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.unittest_tools.fixtures import TIMEOUT

    conda_yaml = tmpdir.join("package.yaml")
    conda_yaml_text = """
# Bad: missing
# documentation:
# version:
# description:

dependencies:
  conda-forge:
  - python=3.10.12
  - pip=23.2.1
  - robocorp-truststore=0.8.0
  pypi:
  - rpaframework=28.3.0 # https://rpaframework.org/releasenotes.html
  - robocorp=1.6.2 # https://pypi.org/project/robocorp
  - robocorp-actions=0.0.7
  - pandas==2.2.1 # Bad, == not supported.
  pip: # Bad: pip should not be here.
  - some-pack=1.1
    """
    conda_yaml.write_text(
        conda_yaml_text,
        "utf-8",
    )

    language_server = language_server_initialized
    conda_yaml_uri = uris.from_fs_path(str(conda_yaml))
    message_matcher = language_server.obtain_pattern_message_matcher(
        {"method": "textDocument/publishDiagnostics"}
    )
    assert message_matcher
    language_server.open_doc(conda_yaml_uri, 1, conda_yaml_text)

    assert message_matcher.event.wait(TIMEOUT)
    diag = message_matcher.msg["params"]["diagnostics"]
    for d in diag:
        if (
            d["message"]
            == "Error: only expected children are pypi and conda (dict entries). Found: pip"
        ):
            break
    else:
        raise AssertionError("Did not find expected diagnostic entry")


class ResolveInterpreterCurrentEnv:
    def get_interpreter_info_for_doc_uri(self, doc_uri) -> Optional[IInterpreterInfo]:
        """
        Provides a customized interpreter for a given document uri.
        """
        return DefaultInterpreterInfo("interpreter_id", sys.executable, {}, [])


def test_lint_python_action(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir,
    data_regression,
    disable_rcc_diagnostics,
):
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.ep_resolve_interpreter import EPResolveInterpreter
    from sema4ai_ls_core.unittest_tools.fixtures import TIMEOUT

    conda_yaml = tmpdir.join("action.py")
    python_file = """
from robocorp.actions import action

@action
def my_action():
    pass
    """
    conda_yaml.write_text(
        python_file,
        "utf-8",
    )

    language_server_client = language_server_initialized

    # Note: so that we don't create a conda.yaml with robocorp.actions installed
    # in it, we just add a new resolver which adds the current environment
    # (and added robocorp.actions to the current environment in pyproject.toml).
    language_server = language_server_client.language_server_instance  # type:ignore
    pm: PluginManager = language_server.pm
    pm.register(EPResolveInterpreter, ResolveInterpreterCurrentEnv)
    conda_yaml_uri = uris.from_fs_path(str(conda_yaml))
    message_matcher = language_server_client.obtain_pattern_message_matcher(
        {"method": "textDocument/publishDiagnostics"}
    )
    assert message_matcher
    language_server_client.open_doc(conda_yaml_uri, 1, python_file)

    assert message_matcher.event.wait(TIMEOUT)
    diag = message_matcher.msg["params"]["diagnostics"]
    data_regression.check(sort_diagnostics(diag))


class LSAutoApiClient:
    def __init__(self, ls_client) -> None:
        from sema4ai_code_tests.robocode_language_server_client import (
            RobocorpLanguageServerClient,
        )

        self.ls_client: RobocorpLanguageServerClient = ls_client

    def underscore_to_camelcase(self, name):
        words = name.split("_")
        camelcase_name = words[0] + "".join(word.capitalize() for word in words[1:])
        return camelcase_name

    def __getattr__(self, attr: str):
        if attr.startswith("m_"):
            attr = attr[2:]
            method_name = self.underscore_to_camelcase(attr)

            def method(**kwargs):
                ret = self.ls_client.request_sync(method_name, **kwargs)
                result = {}
                if ret is not None:
                    result = ret.get("result", {})
                if isinstance(result, dict):
                    # Deal with ActionResultDict.
                    success = result.get("success")
                    if success is not None:
                        assert success

                    return result.get("result", {})

                return result

            return method
        raise AttributeError(attr)


def test_web_inspector_integrated(
    language_server_initialized, ws_root_path, cases, browser_preinstalled
) -> None:
    """
    This test should be a reference spanning all the APIs that are available
    for the inspector webview to use.
    """
    from sema4ai_ls_core import uris

    from sema4ai_code_tests.robocode_language_server_client import (
        RobocorpLanguageServerClient,
    )

    cases.copy_to("robots", ws_root_path)
    ls_client: RobocorpLanguageServerClient = language_server_initialized

    api_client = LSAutoApiClient(ls_client)

    # List robots and load the locators.json.
    listed_robots = api_client.m_list_robots()
    assert len(listed_robots) == 2

    name_to_info: Dict[str, LocalPackageMetadataInfoDict] = {}
    for robot in listed_robots:
        name_to_info[robot["name"]] = robot

    robot2_directory = name_to_info["robot2"]["directory"]
    assert api_client.m_manager_load_locators(directory=robot2_directory) == {}

    existing = api_client.m_manager_load_locators(
        directory=name_to_info["robot1"]["directory"]
    )
    assert len(existing) == 3

    # Create a locator from a browser pick on robot 2 (which has no
    # locators).
    api_client.m_web_inspector_open_browser(
        url=uris.from_fs_path(str(Path(robot2_directory) / "page_to_test.html"))
    )

    api_client.m_web_inspector_start_pick()

    pick_message_matcher = ls_client.obtain_pattern_message_matcher(
        {"method": "$/webPick"}
    )
    api_client.m_web_inspector_click(locator="#div1")
    pick_message_matcher.event.wait(10)
    assert pick_message_matcher.msg

    api_client.m_web_inspector_close_browser()


def test_web_inspector_integrated_state(
    language_server_initialized, ws_root_path, cases, browser_preinstalled
) -> None:
    from sema4ai_code_tests.robocode_language_server_client import (
        RobocorpLanguageServerClient,
    )

    cases.copy_to("robots", ws_root_path)

    ls_client: RobocorpLanguageServerClient = language_server_initialized

    api_client = LSAutoApiClient(ls_client)

    pick_message_matcher = ls_client.obtain_pattern_message_matcher(
        {"method": "$/webInspectorState"}, remove_on_match=False
    )
    assert pick_message_matcher
    pick_message_matcher.on_message = Callback()
    messages: list = []
    pick_message_matcher.on_message.register(messages.append)

    api_client.m_web_inspector_start_pick()

    def check_messages(expected_state: str):
        for msg in messages:
            if msg["params"].get("state") == expected_state:
                return True
        return False

    wait_for_condition(lambda: check_messages(STATE_OPENED))
    wait_for_condition(lambda: check_messages(STATE_PICKING))
    del messages[:]

    api_client.m_web_inspector_stop_pick()
    wait_for_condition(lambda: check_messages(STATE_NOT_PICKING))
    del messages[:]

    api_client.m_web_inspector_start_pick()
    wait_for_condition(lambda: check_messages(STATE_PICKING))
    del messages[:]

    api_client.m_web_inspector_close_browser()
    wait_for_condition(lambda: check_messages(STATE_CLOSED))
    del messages[:]

    time.sleep(0.5)  # Doing it too fast seems to make the test brittle.
    api_client.m_web_inspector_start_pick()
    wait_for_condition(lambda: check_messages(STATE_OPENED))
    wait_for_condition(lambda: check_messages(STATE_PICKING))
    del messages[:]

    api_client.m_web_inspector_close_browser()
    wait_for_condition(lambda: check_messages(STATE_CLOSED))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only test.")
def test_windows_inspector_integrated(
    language_server_initialized, ws_root_path, cases, tk_process
) -> None:
    """
    This test should be a reference spanning all the APIs that are available
    for the inspector webview to use.
    """
    from sema4ai_code_tests.robocode_language_server_client import (
        RobocorpLanguageServerClient,
    )

    cases.copy_to("robots", ws_root_path)
    ls_client: RobocorpLanguageServerClient = language_server_initialized

    api_client = LSAutoApiClient(ls_client)

    result = api_client.m_windows_inspector_parse_locator(locator="")
    assert not result["success"]
    assert result["message"]

    result = api_client.m_windows_inspector_parse_locator(locator="foo bar")
    assert result["success"]
    assert "No locator strategy found in: 'foo'" in result["message"]

    result = api_client.m_windows_inspector_parse_locator(locator="foo:bar")
    assert result["success"]
    assert "No locator strategy found in: 'foo:bar'" in result["message"]

    result = api_client.m_windows_inspector_set_window_locator(
        locator='name:"name is not there"'
    )
    assert not result["success"]

    result = api_client.m_windows_inspector_list_windows()
    assert result["success"]
    windows = [x for x in result["result"] if x["name"] == "Tkinter Elements Showcase"]
    assert len(windows) == 1

    result = api_client.m_windows_inspector_set_window_locator(
        locator='name:"Tkinter Elements Showcase"'
    )
    assert result["success"]

    pick_message_matcher = ls_client.obtain_pattern_message_matcher(
        {"method": "$/windowsPick"}
    )

    # When we set the window locator the mouse will be moved to the
    # window. This means that just starting the picking now will have
    # the cursor at the proper location.
    result = api_client.m_windows_inspector_start_pick()
    assert result["success"]
    pick_message_matcher.event.wait(10)
    assert pick_message_matcher.msg

    result = api_client.m_windows_inspector_stop_pick()
    assert result["success"]

    result = api_client.m_windows_inspector_start_highlight(locator="control:Button")
    assert result["success"]
    assert len(result["result"]["matched_paths"]) > 4

    result = api_client.m_windows_inspector_collect_tree(locator="control:Button")
    assert result["success"]
    assert len(result["result"]["matched_paths"]) > 4

    result = api_client.m_windows_inspector_stop_highlight()
    assert result["success"]


def test_list_action_templates(
    language_server_initialized: IRobocorpLanguageServerClient,
    action_server_location: str,
) -> None:
    from sema4ai_code import commands

    assert os.path.exists(action_server_location)

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL,
        [],
    )["result"]

    assert result["success"]
    template_names = [template["name"] for template in result["result"]]

    assert "minimal" in template_names
    assert "basic" in template_names
    assert "advanced" in template_names


def test_create_action_package(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir: str,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    target = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(added_folders=[target], removed_folders=[])

    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [{"directory": target, "template": "minimal", "name": "My first action"}],
    )["result"]

    assert result["success"]
    assert not result["message"]
    assert os.path.exists(target + "/package.yaml")

    with open(target + "/package.yaml", "r") as f:
        content = f.read()
    assert "My first action" in content

    # When creating a package in a directory that is not empty,
    # we expect an error to be returned.
    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [{"directory": target, "template": "minimal", "name": "My second action"}],
    )["result"]

    assert not result["success"]
    assert "Error creating Action package" in result["message"]
    assert "not empty" in result["message"]


def test_create_action_package_without_templates_handling(
    language_server_initialized: IRobocorpLanguageServerClient,
    tmpdir: str,
) -> None:
    from sema4ai_code import commands
    from sema4ai_code.action_server import get_default_action_server_location

    language_server = language_server_initialized

    target = str(tmpdir.join("dest"))
    language_server.change_workspace_folders(added_folders=[target], removed_folders=[])

    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
        [
            {
                "action_server_location": get_default_action_server_location(),
                "directory": target,
                "template": "",
                "name": "My first action",
            }
        ],
    )["result"]

    assert not result["success"]
    assert "Template name must be provided and may not be empty" in result["message"]


def test_verify_login(
    language_server_initialized: IRobocorpLanguageServerClient,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL,
        [],
    )["result"]

    assert result["success"]
    logged_id = result["result"]["logged_in"]
    assert isinstance(logged_id, bool), "Expected boolean type for logged_in variable"


@pytest.mark.timeout(60)
def test_list_organizations(
    language_server_initialized: IRobocorpLanguageServerClient,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    access_credentials = os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS")
    hostname = os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev")

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL,
        [
            {
                "access_credentials": access_credentials,
                "hostname": hostname,
            },
        ],
    )["result"]

    assert result["success"]
    organizations = result["result"]
    assert len(organizations) == 4
    assert organizations[0]["name"] == "Action Server"


@pytest.mark.timeout(60 * 5)
def test_package_build(
    language_server_initialized: IRobocorpLanguageServerClient,
    cases: CasesFixture,
) -> None:
    import tempfile

    from sema4ai_code import commands

    action_package_path = Path(cases.get_path("action_packages"), "action_package1")
    assert Path(action_package_path, "package.yaml").exists()

    language_server = language_server_initialized

    with tempfile.TemporaryDirectory() as output_dir:
        result = language_server.execute_command(
            commands.SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL,
            [
                {
                    "workspace_dir": str(action_package_path),
                    "output_dir": output_dir,
                },
            ],
            timeout=60 * 5,
        )["result"]

        assert result["success"]
        package_path = Path(result["result"]["package_path"])
        assert package_path.exists()
        assert package_path.is_file()
        assert package_path == Path(output_dir, "test_action.zip")


@pytest.mark.timeout(60)
def test_package_upload(
    language_server_initialized: IRobocorpLanguageServerClient,
    cases: CasesFixture,
) -> None:
    raise pytest.skip(reason="Server upload not online")
    from sema4ai_code import commands

    built_package_path = Path(
        cases.get_path("action_packages"), "action_package1", "saved_action.zip"
    )
    assert built_package_path.exists()

    language_server = language_server_initialized

    organization_id = "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b"
    access_credentials = os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS")
    hostname = os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev")

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL,
        [
            {
                "package_path": str(built_package_path),
                "organization_id": organization_id,
                "access_credentials": access_credentials,
                "hostname": hostname,
            },
        ],
    )["result"]

    assert result["success"]
    package_status = result["result"]
    assert package_status["id"] is not None
    assert package_status["error"] is None


@pytest.mark.timeout(60)
def test_package_status(
    language_server_initialized: IRobocorpLanguageServerClient,
) -> None:
    raise pytest.skip(reason="Server upload not online")

    from sema4ai_code import commands

    language_server = language_server_initialized

    package_id = "21a4a0ea-7ada-4754-8a62-ed9d17dedb1d"
    organization_id = "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b"
    access_credentials = os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS")
    hostname = os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev")

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL,
        [
            {
                "package_id": package_id,
                "organization_id": organization_id,
                "access_credentials": access_credentials,
                "hostname": hostname,
            },
        ],
    )["result"]

    assert result["success"]
    package_status = result["result"]
    assert package_status["id"] == "21a4a0ea-7ada-4754-8a62-ed9d17dedb1d"
    assert package_status["error"] is None


@pytest.mark.timeout(60)
def test_package_set_changelog(
    language_server_initialized: IRobocorpLanguageServerClient,
) -> None:
    raise pytest.skip(reason="Server upload not online")
    from sema4ai_code import commands

    language_server = language_server_initialized

    package_id = "9749f9e5-b3c3-4eb8-8007-2b6337901529"
    organization_id = "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b"
    access_credentials = os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS")
    hostname = os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev")

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL,
        [
            {
                "package_id": package_id,
                "organization_id": organization_id,
                "changelog_input": "Testing",
                "access_credentials": access_credentials,
                "hostname": hostname,
            },
        ],
    )["result"]

    assert result["success"]
    package_status = result["result"]
    assert package_status["id"] == "9749f9e5-b3c3-4eb8-8007-2b6337901529"
    assert package_status["error"] is None


@pytest.mark.timeout(60)
def test_package_metadata(
    language_server_initialized: IRobocorpLanguageServerClient,
    cases: CasesFixture,
    data_regression,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized
    action_package_path = Path(cases.get_path("action_packages"), "action_package1")
    assert Path(action_package_path, "package.yaml").exists()

    output_file_path = Path(action_package_path, "metadata.json")

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL,
        [
            {
                "action_package_path": str(action_package_path),
                "output_file_path": str(output_file_path),
            },
        ],
    )["result"]

    assert result["success"]

    action_package_metadata_path = Path(action_package_path, "metadata.json")
    assert action_package_metadata_path.exists()

    with open(action_package_metadata_path, "r") as f:
        data = json.loads(f.read())
    static_data = {
        "metadata": data["metadata"],
        "openapi.json": {
            "components": data["openapi.json"]["components"],
            "paths": data["openapi.json"]["paths"],
            "servers": data["openapi.json"]["servers"],
        },
    }
    data_regression.check(static_data)


def test_rcc_download(
    language_server_initialized,
) -> None:
    from sema4ai_code import commands
    from sema4ai_code.rcc import get_default_rcc_location

    language_server = language_server_initialized

    language_server.settings({"settings": {"sema4ai": {"rcc": {}}}})

    default_location = get_default_rcc_location()

    with mock.patch("sema4ai_code.rcc.download_rcc") as mock_download_rcc:
        mock_download_rcc.return_value = None

        # Test default location fallback
        result = language_server.execute_command(
            commands.SEMA4AI_RCC_DOWNLOAD_INTERNAL, []
        )["result"]

        assert mock_download_rcc.call_count == 1
        assert result["result"] == default_location

        # Test location from settings
        test_settings_location = "test/settings/location"

        language_server.settings(
            {"settings": {"sema4ai": {"rcc": {"location": test_settings_location}}}}
        )

        result = language_server.execute_command(
            commands.SEMA4AI_RCC_DOWNLOAD_INTERNAL, []
        )["result"]

        assert mock_download_rcc.call_count == 2
        assert result["result"] == test_settings_location

        # Test passing location explicitly
        test_explicit_location = "test/explicit/location"

        result = language_server.execute_command(
            commands.SEMA4AI_RCC_DOWNLOAD_INTERNAL,
            [{"location": test_explicit_location}],
        )["result"]

        assert mock_download_rcc.call_count == 3
        assert result["result"] == test_explicit_location


def test_action_server_download(
    language_server_initialized,
) -> None:
    from sema4ai_code import commands
    from sema4ai_code.action_server import get_default_action_server_location

    language_server = language_server_initialized

    default_location = get_default_action_server_location()

    with mock.patch(
        "sema4ai_code.action_server.download_action_server"
    ) as mock_download_action_server:
        mock_download_action_server.return_value = None

        # Test default location fallback
        result = language_server.execute_command(
            commands.SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL, []
        )["result"]

        assert mock_download_action_server.call_count == 1
        assert result["result"] == default_location


def test_agent_cli_download(
    language_server_initialized,
) -> None:
    from sema4ai_code import commands
    from sema4ai_code.agent_cli import get_default_agent_cli_location

    language_server = language_server_initialized

    default_location = get_default_agent_cli_location()

    with mock.patch(
        "sema4ai_code.agent_cli.download_agent_cli"
    ) as mock_download_agent_cli:
        mock_download_agent_cli.return_value = None

        # Test default location fallback
        result = language_server.execute_command(
            commands.SEMA4AI_AGENT_CLI_DOWNLOAD_INTERNAL, []
        )["result"]

        assert mock_download_agent_cli.call_count == 1
        assert result["result"] == default_location


def test_action_server_version(
    language_server_initialized,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_ACTION_SERVER_VERSION_INTERNAL, []
    )["result"]

    assert result["success"]
    assert result["result"] is not None


def test_agent_cli_version(
    language_server_initialized,
) -> None:
    from sema4ai_code import commands

    language_server = language_server_initialized

    result = language_server.execute_command(
        commands.SEMA4AI_AGENT_CLI_VERSION_INTERNAL, []
    )["result"]

    assert result["success"]
    assert result["result"] is not None


def _write_agent_spec_and_pack(
    agent_spec: dict, target_directory: str, language_server, commands
) -> dict:
    import yaml

    with open(f"{target_directory}/agent-spec.yaml", "w") as yaml_file:
        yaml.dump(agent_spec, yaml_file, default_flow_style=False)

    return language_server.execute_command(
        commands.SEMA4AI_PACK_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": target_directory,
            }
        ],
    )["result"]


def test_create_and_pack_agent_package(
    language_server_initialized,
    tmpdir,
    agent_cli_location: str,
) -> None:
    assert os.path.exists(agent_cli_location)

    import yaml
    from sema4ai_code import commands

    language_server = language_server_initialized

    package_name = "test_agent"

    target_directory = str(tmpdir.join(package_name))
    language_server.change_workspace_folders(
        added_folders=[target_directory], removed_folders=[]
    )

    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": target_directory,
                "name": "Test Agent",
            }
        ],
    )["result"]

    assert result["success"]
    assert not result["message"]
    assert os.path.exists(f"{target_directory}/agent-spec.yaml")

    with open(f"{target_directory}/agent-spec.yaml") as stream:
        agent_spec = yaml.safe_load(stream)
        assert isinstance(agent_spec, dict)

    # When creating a package in a directory that is not empty,
    # we expect an error to be returned.
    result = language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": target_directory,
                "name": "Test Agent 2",
            }
        ],
    )["result"]

    assert not result["success"]
    assert "Error creating Agent package" in result["message"]
    assert "not empty" in result["message"]

    result = _write_agent_spec_and_pack(
        agent_spec, target_directory, language_server, commands
    )

    assert result["success"]
    assert not result["message"]
    assert os.path.exists(f"{target_directory}/agent-package.zip")

    # Incorrect agent spec configuration
    del agent_spec["agent-package"]["agents"][0]["description"]

    result = _write_agent_spec_and_pack(
        agent_spec, target_directory, language_server, commands
    )

    assert not result["success"]
    assert (
        "Missing required entry: agent-package/agents/description." in result["message"]
    )


def test_get_runbook_from_agent_spec(
    language_server_initialized,
    tmpdir,
) -> None:
    import yaml
    from sema4ai_code import commands

    language_server = language_server_initialized
    package_name = "test_agent"
    target_directory = str(tmpdir.join(package_name))

    language_server.change_workspace_folders(
        added_folders=[target_directory], removed_folders=[]
    )

    language_server.execute_command(
        commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
        [
            {
                "directory": target_directory,
                "name": "Test Agent",
            }
        ],
    )

    with open(f"{target_directory}/agent-spec.yaml", "r+") as stream:
        agent_spec = yaml.safe_load(stream.read())
        agent_spec["agent-package"]["agents"][0]["runbook"] = "runbook.md"
        stream.seek(0)
        yaml.dump(agent_spec, stream, default_flow_style=False)

    result = language_server.execute_command(
        commands.SEMA4AI_GET_RUNBOOK_PATH_FROM_AGENT_SPEC_INTERNAL,
        [
            {
                "agent_spec_path": str(Path(target_directory) / "agent-spec.yaml"),
            }
        ],
    )["result"]

    assert result["success"]
    assert result["result"] == "runbook.md"

    with open(f"{target_directory}/agent-spec.yaml", "w") as stream:
        del agent_spec["agent-package"]["agents"][0]["runbook"]
        yaml.dump(agent_spec, stream, default_flow_style=False, sort_keys=False)

    result = language_server.execute_command(
        commands.SEMA4AI_GET_RUNBOOK_PATH_FROM_AGENT_SPEC_INTERNAL,
        [
            {
                "agent_spec_path": str(Path(target_directory) / "agent-spec.yaml"),
            }
        ],
    )["result"]

    assert not result["success"]
    assert result["message"] == "Runbook entry was not found in the agent spec."
