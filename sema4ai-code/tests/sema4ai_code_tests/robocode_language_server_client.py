from sema4ai_code_tests.protocols import IRobocorpLanguageServerClient
from sema4ai_ls_core.basic import implements
from sema4ai_ls_core.unittest_tools.language_server_client import LanguageServerClient

from sema4ai_code.protocols import (
    ActionResultDict,
    ListWorkspacesActionResultDict,
    UploadNewRobotParamsDict,
    UploadRobotParamsDict,
)


class RobocorpLanguageServerClient(LanguageServerClient):
    @implements(IRobocorpLanguageServerClient.cloud_list_workspaces)
    def cloud_list_workspaces(self, refresh=False) -> ListWorkspacesActionResultDict:
        from sema4ai_code import commands

        result = self.execute_command(
            commands.SEMA4AI_CLOUD_LIST_WORKSPACES_INTERNAL, [{"refresh": refresh}]
        )["result"]
        return result

    @implements(IRobocorpLanguageServerClient.upload_to_existing_activity)
    def upload_to_existing_activity(
        self, workspace_id: str, package_id: str, directory: str
    ) -> ActionResultDict:
        from sema4ai_code import commands

        params: UploadRobotParamsDict = {
            "workspaceId": workspace_id,
            "robotId": package_id,
            "directory": directory,
        }
        result = self.execute_command(
            commands.SEMA4AI_UPLOAD_TO_EXISTING_ROBOT_INTERNAL, [params]
        )["result"]
        return result

    @implements(IRobocorpLanguageServerClient.upload_to_new_robot)
    def upload_to_new_robot(
        self, workspace_id: str, robot_name: str, directory: str
    ) -> ActionResultDict:
        from sema4ai_code import commands

        paramsNew: UploadNewRobotParamsDict = {
            "workspaceId": workspace_id,
            "robotName": robot_name,
            "directory": directory,
        }
        result = self.execute_command(
            commands.SEMA4AI_UPLOAD_TO_NEW_ROBOT_INTERNAL, [paramsNew]
        )["result"]
        return result

    def get_plugins_dir(self) -> str:
        from sema4ai_code import commands

        result = self.execute_command(commands.SEMA4AI_GET_PLUGINS_DIR, [])["result"]
        return result

    def __typecheckself__(self) -> None:
        from sema4ai_ls_core.protocols import check_implements

        _: IRobocorpLanguageServerClient = check_implements(self)
