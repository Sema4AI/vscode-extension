import json
from collections.abc import Sequence

from sema4ai_ls_core.command_dispatcher import _SubCommandDispatcher
from sema4ai_ls_core.protocols import ActionResultDict, IEndPoint
from sema4ai_ls_core.core_log import get_logger

from sema4ai_code import commands
from sema4ai_code.protocols import (
    IRcc,
    ProfileImportParamsDict,
    ProfileListResultTypedDict,
    ProfileSwitchParamsDict,
)

log = get_logger(__name__)
profile_command_dispatcher = _SubCommandDispatcher("_profile")


class _Profile:
    def __init__(
        self,
        endpoint: IEndPoint,
        base_command_dispatcher,
        rcc: IRcc,
        feedback,
    ):
        from sema4ai_code._language_server_feedback import _Feedback

        self._endpoint = endpoint
        self._rcc = rcc
        self._feedback: _Feedback = feedback
        self._last_rcc_settings = None

        base_command_dispatcher.register_sub_command_dispatcher(
            profile_command_dispatcher
        )

    @profile_command_dispatcher(commands.SEMA4AI_PROFILE_IMPORT_INTERNAL)
    def _profile_import(self, params: ProfileImportParamsDict) -> ActionResultDict:
        from sema4ai_ls_core import uris, yaml_wrapper
        from sema4ai_ls_core.progress_report import progress_context

        self._feedback.metric("vscode.profile.import")

        try:
            profile_uri = params["profileUri"]
            with progress_context(self._endpoint, "Import profile", None):
                file_path = uris.to_fs_path(profile_uri)
                profile_name: str = ""
                description: str = ""
                try:
                    with open(file_path, encoding="utf-8") as stream:
                        contents = yaml_wrapper.load(stream)
                        profile_name = contents.get("name", "")
                        description = contents.get("description", "")
                except Exception as e:
                    msg = f"Error loading: {file_path} as yaml: {e}."
                    log.exception(msg)
                    return {"success": False, "message": msg, "result": None}

                if not profile_name:
                    return {
                        "success": False,
                        "message": "Profile 'name' not available in yaml.",
                        "result": None,
                    }

                action_result = self._rcc.profile_import(file_path)
                if not action_result.success:
                    return action_result.as_dict()

                result = {"name": profile_name, "description": description}
        finally:
            self._last_rcc_settings = None
        return {"success": True, "message": None, "result": result}

    @profile_command_dispatcher(commands.SEMA4AI_PROFILE_SWITCH_INTERNAL)
    def _profile_switch(self, params: ProfileSwitchParamsDict) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        self._feedback.metric("vscode.profile.switch")

        try:
            profile_name = params["profileName"]
            with progress_context(self._endpoint, "Switch profile", None):
                if not profile_name:
                    return {
                        "success": False,
                        "message": "Profile 'name' not available in yaml.",
                        "result": None,
                    }

                action_result = self._rcc.profile_switch(profile_name)
                if not action_result.success:
                    return action_result.as_dict()

                self._endpoint.notify("$/linkedAccountChanged")

                result = True
        finally:
            self._last_rcc_settings = None
        return {"success": True, "message": None, "result": result}

    @profile_command_dispatcher(commands.SEMA4AI_PROFILE_LIST_INTERNAL)
    def _profile_list(self, *params) -> ActionResultDict:
        from sema4ai_ls_core.protocols import ActionResult

        action_result: ActionResult[ProfileListResultTypedDict] = (
            self._rcc.profile_list()
        )
        return action_result.as_dict()

    @profile_command_dispatcher(commands.SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL)
    def get_pypi_base_urls(self) -> Sequence[str]:
        try:
            if self._last_rcc_settings is None:
                configuration_settings = self._rcc.configuration_settings()
                if configuration_settings.success and configuration_settings.result:
                    settings = json.loads(configuration_settings.result)
                    self._last_rcc_settings = settings
                else:
                    self._last_rcc_settings = None
        except Exception:
            self._last_rcc_settings = None
            log.exception("Error getting pypi base urls.")

        settings = self._last_rcc_settings
        if isinstance(settings, dict):
            endpoints = settings.get("endpoints")
            if isinstance(endpoints, dict):
                pypi = endpoints.get("pypi-trusted")
                if isinstance(pypi, str):
                    pypi = pypi.strip()
                    if pypi and not pypi.startswith("#"):
                        if pypi.endswith("/"):
                            pypi = pypi[:-1]

                        # RCC passes the additional index but does
                        # not stop pass --no-index to stop indexing pypi.org
                        # See: https://pip.pypa.io/en/stable/cli/pip_install/
                        return (pypi, "https://pypi.org")
        return ("https://pypi.org",)
