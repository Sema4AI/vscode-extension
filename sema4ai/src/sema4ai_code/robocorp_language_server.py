import os
import sys
import time
import typing
import weakref
from base64 import b64encode
from collections.abc import Iterator, Sequence
from functools import partial
from pathlib import Path
from typing import Any, cast

import sema4ai_ls_core
from sema4ai_ls_core import uris, watchdog_wrapper
from sema4ai_ls_core.basic import overrides
from sema4ai_ls_core.command_dispatcher import _CommandDispatcher
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.jsonrpc.endpoint import require_monitor
from sema4ai_ls_core.lsp import (
    CodeActionTypedDict,
    HoverTypedDict,
    TextDocumentCodeActionTypedDict,
)
from sema4ai_ls_core.protocols import (
    ActionInfoTypedDict,
    DatasourceInfoTypedDict,
    DataSourceStateDict,
    IConfig,
    IMonitor,
    LibraryVersionInfoDict,
)
from sema4ai_ls_core.python_ls import BaseLintManager, PythonLanguageServer
from sema4ai_ls_core.watchdog_wrapper import IFSObserver

from sema4ai_code import commands
from sema4ai_code.action_server import get_default_sema4ai_home
from sema4ai_code.agents.agent_spec_handler import ErrorCode
from sema4ai_code.inspector.inspector_language_server import InspectorLanguageServer
from sema4ai_code.protocols import (
    ActionResult,
    ActionResultDict,
    ActionResultDictLocalRobotMetadata,
    ActionResultDictLocatorsJson,
    ActionResultDictLocatorsJsonInfo,
    ActionResultDictRobotLaunch,
    ActionResultDictWorkItems,
    ActionServerAccessCredentialsDict,
    ActionServerListOrgsResultDict,
    ActionServerLoginDict,
    ActionServerPackageBuildDict,
    ActionServerPackageBuildResultDict,
    ActionServerPackageMetadataDict,
    ActionServerPackageSetChangelogDict,
    ActionServerPackageStatusDict,
    ActionServerPackageUploadDict,
    ActionServerPackageUploadStatusDict,
    ActionServerVerifyLoginResultDict,
    AgentSpecPathDict,
    CloudListWorkspaceDict,
    ConfigurationDiagnosticsDict,
    CreateActionPackageParamsDict,
    CreateAgentPackageParamsDict,
    CreateRobotParamsDict,
    DataServerConfigTypedDict,
    DownloadToolDict,
    IRccRobotMetadata,
    IRccWorkspace,
    ListActionsParams,
    ListWorkItemsParams,
    ListWorkspacesActionResultDict,
    LocatorEntryInfoDict,
    PackageInfoDict,
    PackageInfoInLRUDict,
    RunInRccParamsDict,
    TypedDict,
    UpdateAgentVersionParamsDict,
    UploadNewRobotParamsDict,
    UploadRobotParamsDict,
    WorkItem,
    WorkspaceInfoDict,
)
from sema4ai_code.refresh_agent_spec_helper import update_agent_spec
from sema4ai_code.robo.collect_actions_ast import (
    ActionInfoTypedDict,
    DatasourceInfoTypedDict,
)
from sema4ai_code.vendored_deps.package_deps._deps_protocols import (
    ICondaCloud,
    IPyPiCloud,
)
from sema4ai_code.workspace_manager import WorkspaceManager

if typing.TYPE_CHECKING:
    from sema4ai_code.agents.gallery_actions import GalleryActionPackages
    from sema4ai_code.data.data_server_connection import DataServerConnection

DataSourceSetupResponse = list[str]

log = get_logger(__name__)

try:
    __file__ = os.path.abspath(__file__)
except NameError:
    pass  # During pydevd debugger auto reload __file__ may not be there.
else:
    if __file__.endswith((".pyc", ".pyo")):
        __file__ = __file__[:-1]


def _parse_version(version) -> tuple:
    ret = []
    for v in version.split("."):
        try:
            ret.append(int(v))
        except Exception:
            ret.append(v)
    return tuple(ret)


def _verify_version(found_version, expected_version):
    found_version = found_version[: len(expected_version)]
    return found_version >= expected_version


class ListWorkspaceCachedInfoDict(TypedDict):
    ws_info: list[WorkspaceInfoDict]
    account_cache_key: tuple


command_dispatcher = _CommandDispatcher()


class RobocorpLanguageServer(PythonLanguageServer, InspectorLanguageServer):
    # V2: save the account info along to validate user.
    # V3: Add organizationName
    CLOUD_LIST_WORKSPACE_CACHE_KEY = "CLOUD_LIST_WORKSPACE_CACHE_V3"
    PACKAGE_ACCESS_LRU_CACHE_KEY = "PACKAGE_ACCESS_LRU_CACHE"

    def __init__(self, read_stream, write_stream) -> None:
        from queue import Queue

        from sema4ai_ls_core.cache import DirCache
        from sema4ai_ls_core.ep_providers import (
            DefaultConfigurationProvider,
            DefaultDirCacheProvider,
            DefaultEndPointProvider,
            EPConfigurationProvider,
            EPDirCacheProvider,
            EPEndPointProvider,
        )
        from sema4ai_ls_core.pluginmanager import PluginManager

        from sema4ai_code._language_server_feedback import _Feedback
        from sema4ai_code._language_server_login import _Login
        from sema4ai_code._language_server_oauth2 import _OAuth2
        from sema4ai_code._language_server_playwright import _Playwright
        from sema4ai_code._language_server_pre_run_scripts import _PreRunScripts
        from sema4ai_code._language_server_profile import _Profile
        from sema4ai_code._language_server_vault import _Vault
        from sema4ai_code.action_server import ActionServer
        from sema4ai_code.agent_cli import AgentCli
        from sema4ai_code.rcc import Rcc
        from sema4ai_code.vendored_deps.package_deps.pypi_cloud import PyPiCloud

        user_home = os.getenv("ROBOCORP_CODE_USER_HOME", None)
        if user_home is None:
            user_home = os.path.expanduser("~")
        cache_dir = os.path.join(user_home, ".sema4ai", ".cache")

        log.info(f"Cache dir: {cache_dir}")

        try:
            import ssl
        except Exception:
            # This means that we won't be able to download drivers to
            # enable the creation of browser locators!
            # Let's print a bit more info.
            env_vars_info = ""

            related_vars = [
                "LD_LIBRARY_PATH",
                "PATH",
                "DYLD_LIBRARY_PATH",
                "DYLD_FALLBACK_LIBRARY_PATH",
            ]
            for v in related_vars:
                libpath = os.environ.get(v, "")

                libpath = "\n    ".join(libpath.split(os.pathsep))
                if libpath:
                    libpath = "\n    " + libpath + "\n"
                else:
                    libpath = " <not set>\n"

                env_vars_info += f"{v}: {libpath}"

            log.critical(
                f"SSL module could not be imported.\n"
                f"sys.executable: {sys.executable}\n"
                f"Env vars info: {env_vars_info}\n"
            )

        self._fs_observer: IFSObserver | None = None

        self._dir_cache = DirCache(cache_dir)
        self._rcc = Rcc(self)
        self._feedback = _Feedback(self._rcc)
        self._pre_run_scripts = _PreRunScripts(command_dispatcher)

        PythonLanguageServer.__init__(self, read_stream, write_stream)

        self._vault = _Vault(
            self._dir_cache, self._endpoint, self._rcc, command_dispatcher
        )

        self._action_server = ActionServer(self, self._endpoint)
        self._agent_cli = AgentCli(self, self._action_server)

        weak_self = weakref.ref(self)  # Avoid cyclic ref.

        def clear_caches_on_login_change():
            s = weak_self()
            if s is not None:
                s._discard_listed_workspaces_info()
                s._vault.discard_vault_workspace_info()

        self._login = _Login(
            self._dir_cache,
            self._endpoint,
            command_dispatcher,
            self._rcc,
            self._feedback,
            clear_caches_on_login_change,
        )

        self._profile = _Profile(
            self._endpoint,
            command_dispatcher,
            self._rcc,
            self._feedback,
        )

        self._oauth2 = _OAuth2(
            self._endpoint,
            command_dispatcher,
            self._rcc,
            self._feedback,
            lsp_messages=self._lsp_messages,
            action_server=self._action_server,
        )

        self._pm = PluginManager()
        self._config_provider = DefaultConfigurationProvider(self.config)
        self._pm.set_instance(EPConfigurationProvider, self._config_provider)
        self._pm.set_instance(
            EPDirCacheProvider, DefaultDirCacheProvider(self._dir_cache)
        )
        self._pm.set_instance(
            EPEndPointProvider, DefaultEndPointProvider(self._endpoint)
        )
        from sema4ai_code.resolve_interpreter import register_plugins

        self._prefix_to_last_run_number_and_time: dict[str, tuple[int, float]] = {}

        self._pypi_cloud = PyPiCloud(weakref.WeakMethod(self._get_pypi_base_urls))  # type: ignore
        self._cache_dir = cache_dir
        self._paths_remover = None
        self.__conda_cloud: ICondaCloud | None = None
        self._paths_remover_queue: "Queue[Path]" = Queue()
        register_plugins(self._pm)

        self._playwright = _Playwright(
            base_command_dispatcher=command_dispatcher,
            feedback=self._feedback,
            plugin_manager=self._pm,
            lsp_messages=self._lsp_messages,
        )

        InspectorLanguageServer.__init__(self)

    @property
    def _conda_cloud(self) -> ICondaCloud:  # Create it on demand
        if self.__conda_cloud is None:
            conda_cloud = self.__conda_cloud = self._create_conda_cloud(self._cache_dir)
            conda_cloud.schedule_update()
        return self.__conda_cloud

    def _create_conda_cloud(self, cache_dir: str) -> ICondaCloud:
        """
        Note: monkey-patched in tests (so that we don't reindex
        and specify the conda-indexes to use).
        """
        from sema4ai_code.vendored_deps.package_deps.conda_cloud import CondaCloud

        return CondaCloud(Path(cache_dir) / ".conda_indexes")

    def _get_pypi_base_urls(self) -> Sequence[str]:
        return self._profile.get_pypi_base_urls()

    @property
    def pypi_cloud(self) -> IPyPiCloud:
        return self._pypi_cloud

    @property
    def conda_cloud(self) -> ICondaCloud:
        return self._conda_cloud

    def _discard_listed_workspaces_info(self):
        self._dir_cache.discard(self.CLOUD_LIST_WORKSPACE_CACHE_KEY)

    def _schedule_path_removal(self, path):
        from sema4ai_code.path_operations import PathsRemover

        if self._paths_remover is None:
            self._paths_remover = PathsRemover(self._paths_remover_queue)
            self._paths_remover.start()

        log.info("Schedule path removal for: %s", path)
        self._paths_remover_queue.put(path)

    @overrides(PythonLanguageServer.m_initialize)
    def m_initialize(
        self,
        processId=None,
        rootUri=None,
        rootPath=None,
        initializationOptions=None,
        workspaceFolders=None,
        **_kwargs,
    ) -> dict:
        ret = PythonLanguageServer.m_initialize(
            self,
            processId=processId,
            rootUri=rootUri,
            rootPath=rootPath,
            initializationOptions=initializationOptions,
            workspaceFolders=workspaceFolders,
        )

        if initializationOptions and isinstance(initializationOptions, dict):
            self._feedback.track = not initializationOptions.get("do-not-track", False)

        from sema4ai_code import __version__

        self._feedback.metric("vscode.started", __version__)
        self._feedback.metric("vscode.started.os", sys.platform)

        # self.workspace is initialized in parent's m_initialize, therefore we defer
        # assignment from __init__.
        self._workspace_manager = WorkspaceManager(self.workspace)

        return ret

    def m_shutdown(self, **_kwargs):
        PythonLanguageServer.m_shutdown(self, **_kwargs)

    @overrides(PythonLanguageServer._obtain_fs_observer)
    def _obtain_fs_observer(self) -> IFSObserver:
        if self._fs_observer is None:
            self._fs_observer = watchdog_wrapper.create_observer("dummy", ())
        return self._fs_observer

    def _create_lint_manager(self) -> BaseLintManager | None:
        from sema4ai_code._lint import LintManager

        return LintManager(
            self,
            self._rcc,
            self._lsp_messages,
            self._endpoint,
            self._jsonrpc_stream_reader.get_read_queue(),
        )

    @overrides(PythonLanguageServer._create_config)
    def _create_config(self) -> IConfig:
        from sema4ai_code.robocorp_config import RobocorpConfig

        return RobocorpConfig()

    @overrides(PythonLanguageServer.capabilities)
    def capabilities(self):
        from sema4ai_ls_core.lsp import TextDocumentSyncKind

        from sema4ai_code.commands import ALL_SERVER_COMMANDS

        server_capabilities = {
            "codeActionProvider": True,
            "codeLensProvider": {
                "resolveProvider": False,
            },
            # "completionProvider": {
            #     "resolveProvider": False  # We know everything ahead of time
            # },
            "documentFormattingProvider": False,
            "documentHighlightProvider": False,
            "documentRangeFormattingProvider": False,
            "documentSymbolProvider": False,
            "definitionProvider": False,
            "executeCommandProvider": {"commands": ALL_SERVER_COMMANDS},
            "hoverProvider": True,
            "referencesProvider": False,
            "renameProvider": False,
            "foldingRangeProvider": False,
            "textDocumentSync": {
                "change": TextDocumentSyncKind.INCREMENTAL,
                "save": {"includeText": False},
                "openClose": True,
            },
            "workspace": {
                "workspaceFolders": {"supported": True, "changeNotifications": True}
            },
        }
        log.debug("Server capabilities: %s", server_capabilities)
        return server_capabilities

    def m_text_document__code_action(self, **kwargs) -> list[CodeActionTypedDict]:
        params: TextDocumentCodeActionTypedDict = cast(
            TextDocumentCodeActionTypedDict, kwargs
        )
        # Sample params:
        # {
        #     "textDocument": {
        #         "uri": "file:///x%3A/vscode-robot/local_test/robot_check/checkmy.robot"
        #     },
        #     "range": {
        #         "start": {"line": 12, "character": 5},
        #         "end": {"line": 12, "character": 5},
        #     },
        #     "context": {
        #         "diagnostics": [
        #             {
        #                 "range": {
        #                     "start": {"line": 12, "character": 4},
        #                     "end": {"line": 12, "character": 8},
        #                 },
        #                 "message": "Undefined keyword: rara.",
        #                 "severity": 1,
        #                 "source": "robotframework",
        #             }
        #         ],
        #         "triggerKind": 1,
        #     },
        # }
        code_action_list: list[CodeActionTypedDict] = []
        diagnostics = params.get("context", {}).get("diagnostics", [])

        if not diagnostics:
            return code_action_list

        incomplete_package_diags = [
            d
            for d in diagnostics
            if d.get("code")
            in [
                ErrorCode.action_package_info_unsynchronized.value,
                ErrorCode.agent_package_incomplete.value,
            ]
        ]

        document_dir = Path(
            sema4ai_ls_core.uris.to_fs_path(params["textDocument"]["uri"])
        )

        if incomplete_package_diags:
            code_action_list.append(
                {
                    "title": "Refresh Agent Configuration",
                    "kind": "quickfix",
                    "diagnostics": incomplete_package_diags,
                    "command": {
                        "title": "Refresh Agent Configuration",
                        "command": commands.SEMA4AI_REFRESH_AGENT_SPEC,
                        "arguments": [str(document_dir.parent)],
                    },
                }
            )

        return code_action_list

    def m_text_document__completion(self, **kwargs):
        return []

    def m_workspace__execute_command(self, command=None, arguments=()) -> Any:
        return command_dispatcher.dispatch(self, command, arguments)

    def m_import_agent_package_from_zip(
        self, target_dir: str | None = None, agent_package_zip: str | None = None
    ) -> ActionResultDict:
        if not target_dir:
            return ActionResult.make_failure(
                f"target_dir not sent in arguments."
            ).as_dict()
        if not agent_package_zip:
            return ActionResult.make_failure(
                f"agent_package_zip not sent in arguments."
            ).as_dict()

        return require_monitor(
            partial(
                self._import_agent_package_from_zip_threaded,
                agent_package_zip,
                target_dir,
            )
        )

    def _import_agent_package_from_zip_threaded(
        self, agent_package_zip: str, target_dir: str, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint, "Importing Agent Package", self._dir_cache
        ):
            return self._agent_cli.import_agent_package(
                agent_package_zip, target_dir, monitor
            ).as_dict()

    @command_dispatcher(commands.SEMA4AI_CONFIGURATION_DIAGNOSTICS_INTERNAL)
    def _configuration_diagnostics_internal(
        self, params: ConfigurationDiagnosticsDict
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        robot_yaml = params["robotYaml"]
        with progress_context(
            self._endpoint, "Collecting configuration diagnostics", self._dir_cache
        ):
            action_result = self._rcc.configuration_diagnostics(robot_yaml, json=False)
            return action_result.as_dict()

    @command_dispatcher(commands.SEMA4AI_SAVE_IN_DISK_LRU)
    def _save_in_disk_lru(self, params: dict) -> ActionResultDict:
        name = params["name"]
        entry = params["entry"]
        lru_size = params["lru_size"]
        try:
            cache_lru_list = self._dir_cache.load(name, list)
        except Exception:
            cache_lru_list = []

        try:
            if cache_lru_list[0] == entry:
                # Nothing to do as it already matches.
                return {"success": True, "message": "", "result": entry}

            cache_lru_list.remove(entry)
        except Exception:
            pass  # If empty or if entry is not there, just proceed.

        if len(cache_lru_list) >= lru_size:
            cache_lru_list = cache_lru_list[:-1]

        cache_lru_list.insert(0, entry)
        self._dir_cache.store(name, cache_lru_list)
        return {"success": True, "message": "", "result": entry}

    @command_dispatcher(commands.SEMA4AI_LOAD_FROM_DISK_LRU, list)
    def _load_from_disk_lru(self, params: dict) -> list:
        try:
            name = params["name"]
            cache_lru_list = self._dir_cache.load(name, list)
        except Exception:
            cache_lru_list = []

        return cache_lru_list

    def _get_sort_key_info(self) -> dict:
        try:
            cache_lru_list: list[PackageInfoInLRUDict] = self._dir_cache.load(
                self.PACKAGE_ACCESS_LRU_CACHE_KEY, list
            )
        except KeyError:
            cache_lru_list = []
        DEFAULT_SORT_KEY = 10
        ws_id_and_pack_id_to_lru_index: dict = {}
        for i, entry in enumerate(cache_lru_list):
            if i >= DEFAULT_SORT_KEY:
                break

            if isinstance(entry, dict):
                ws_id = entry.get("workspace_id")
                pack_id = entry.get("package_id")
                if ws_id is not None and pack_id is not None:
                    key = (ws_id, pack_id)
                    ws_id_and_pack_id_to_lru_index[key] = i
        return ws_id_and_pack_id_to_lru_index

    @command_dispatcher(commands.SEMA4AI_GET_LINKED_ACCOUNT_INFO_INTERNAL)
    def _get_linked_account_info(self, params=None) -> ActionResultDict:
        from sema4ai_code.rcc import AccountInfo

        curr_account_info: AccountInfo | None = self._rcc.last_verified_account_info
        if curr_account_info is None:
            curr_account_info = self._rcc.get_valid_account_info()
            if curr_account_info is None:
                return {
                    "success": False,
                    "message": "Unable to get account info (no linked account).",
                    "result": None,
                }
        return {
            "success": True,
            "message": None,
            "result": {
                "account": curr_account_info.account,
                "identifier": curr_account_info.identifier,
                "email": curr_account_info.email,
                "fullname": curr_account_info.fullname,
            },
        }

    @command_dispatcher(commands.SEMA4AI_CLOUD_LIST_WORKSPACES_INTERNAL)
    def _cloud_list_workspaces(
        self, params: CloudListWorkspaceDict
    ) -> ListWorkspacesActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        DEFAULT_SORT_KEY = 10
        package_info: PackageInfoDict
        ws_dict: WorkspaceInfoDict

        ws_id_and_pack_id_to_lru_index = self._get_sort_key_info()
        curr_account_info = self._rcc.last_verified_account_info
        if curr_account_info is None:
            curr_account_info = self._rcc.get_valid_account_info()
            if curr_account_info is None:
                return {
                    "success": False,
                    "message": "Unable to get workspace info (no user is logged in).",
                    "result": None,
                }

        account_cache_key = (curr_account_info.account, curr_account_info.identifier)

        if not params.get("refresh", True):
            try:
                cached: ListWorkspaceCachedInfoDict = self._dir_cache.load(
                    self.CLOUD_LIST_WORKSPACE_CACHE_KEY, dict
                )
            except KeyError:
                pass
            else:
                # We need to update the sort key when it's gotten from the cache.
                try:
                    if account_cache_key == tuple(cached.get("account_cache_key", ())):
                        for ws_dict in cached["ws_info"]:
                            for package_info in ws_dict["packages"]:
                                key = (package_info["workspaceId"], package_info["id"])
                                sort_key = "%05d%s" % (
                                    ws_id_and_pack_id_to_lru_index.get(
                                        key, DEFAULT_SORT_KEY
                                    ),
                                    package_info["name"].lower(),
                                )

                                package_info["sortKey"] = sort_key
                        return {
                            "success": True,
                            "message": None,
                            "result": cached["ws_info"],
                        }
                except Exception:
                    log.exception(
                        "Error computing new sort keys for cached entry. Refreshing and proceeding."
                    )

        last_error_result = None

        with progress_context(
            self._endpoint, "Listing Control Room workspaces", self._dir_cache
        ):
            ws: IRccWorkspace
            ret: list[WorkspaceInfoDict] = []
            result = self._rcc.cloud_list_workspaces()
            if not result.success:
                # It's an error, so, the data should be None.
                return typing.cast(
                    ActionResultDict[list[WorkspaceInfoDict]], result.as_dict()
                )

            workspaces = result.result
            for ws in workspaces or []:
                packages: list[PackageInfoDict] = []

                activity_package: IRccRobotMetadata
                activities_result = self._rcc.cloud_list_workspace_robots(
                    ws.workspace_id
                )
                if not activities_result.success:
                    # If we can't list the robots of a specific workspace, just skip it
                    # (the log should still show it but we can proceed to list the
                    # contents of other workspaces).
                    last_error_result = activities_result
                    continue

                workspace_activities = activities_result.result
                for activity_package in workspace_activities or []:
                    key = (ws.workspace_id, activity_package.robot_id)
                    sort_key = "%05d%s" % (
                        ws_id_and_pack_id_to_lru_index.get(key, DEFAULT_SORT_KEY),
                        activity_package.robot_name.lower(),
                    )

                    package_info = {
                        "name": activity_package.robot_name,
                        "id": activity_package.robot_id,
                        "sortKey": sort_key,
                        "organizationName": ws.organization_name,
                        "workspaceId": ws.workspace_id,
                        "workspaceName": ws.workspace_name,
                    }
                    packages.append(package_info)

                ws_dict = {
                    "organizationName": ws.organization_name,
                    "workspaceName": ws.workspace_name,
                    "workspaceId": ws.workspace_id,
                    "packages": packages,
                }
                ret.append(ws_dict)

        if not ret and last_error_result is not None:
            # It's an error, so, the data should be None.
            return typing.cast(
                ActionResultDict[list[WorkspaceInfoDict]], last_error_result.as_dict()
            )

        if ret:  # Only store if we got something.
            store: ListWorkspaceCachedInfoDict = {
                "ws_info": ret,
                "account_cache_key": account_cache_key,
            }
            self._dir_cache.store(self.CLOUD_LIST_WORKSPACE_CACHE_KEY, store)
        return {"success": True, "message": None, "result": ret}

    @command_dispatcher(commands.SEMA4AI_CREATE_ROBOT_INTERNAL)
    def _create_robot(self, params: CreateRobotParamsDict) -> ActionResultDict:
        self._feedback.metric("vscode.create.robot")
        directory = params["directory"]
        template = params["template"]

        name = params.get("name", "").strip()
        force: bool = bool(params.get("force", False))
        if name:
            # If the name is given we join it to the directory, otherwise
            # we use the directory directly.
            target_dir = os.path.join(directory, name)
        else:
            target_dir = directory
        return self._rcc.create_robot(template, target_dir, force=force).as_dict()

    @command_dispatcher(commands.SEMA4AI_LIST_ROBOT_TEMPLATES_INTERNAL)
    def _list_activity_templates(self, params=None) -> ActionResultDict:
        result = self._rcc.get_template_names()
        return result.as_dict()

    @command_dispatcher(commands.SEMA4AI_RUN_IN_RCC_INTERNAL)
    def _run_in_rcc_internal(self, params=RunInRccParamsDict) -> ActionResultDict:
        try:
            args = params["args"]
            ret = self._rcc._run_rcc(args)
        except Exception as e:
            log.exception(f"Error running in RCC: {params}.")
            return dict(success=False, message=str(e), result=None)
        return ret.as_dict()

    def m_list_actions_full_and_slow(
        self, action_package_uri: str = "", action_package_yaml_directory: str = ""
    ):
        if not action_package_uri:
            msg = f"Unable to collect actions because the target action_package_uri was not given (or was empty)."
            return dict(success=False, message=msg, result=None)
        if not action_package_yaml_directory:
            msg = f"Unable to collect actions because the target action_package_yaml_directory was not given (or was empty)."
            return dict(success=False, message=msg, result=None)
        return require_monitor(
            partial(
                self._list_actions_full_and_slow,
                action_package_uri=action_package_uri,
                action_package_yaml_directory=action_package_yaml_directory,
            )
        )

    def _list_actions_full_and_slow(
        self,
        action_package_uri: str,
        action_package_yaml_directory: str,
        monitor: IMonitor,
    ) -> ActionResultDict:
        from sema4ai_code.robo.collect_actions import (
            collect_actions_full_and_slow,
            extract_info,
        )

        p = Path(uris.to_fs_path(action_package_uri))
        if not p.exists():
            msg = f"Unable to collect actions from: {p} because it does not exist."
            return dict(success=False, message=msg, result=None)

        try:
            if not self.workspace:
                return dict(
                    success=False, message="No workspace currently open", result=None
                )

            result = collect_actions_full_and_slow(
                self._pm, action_package_uri, action_package_yaml_directory, monitor
            )
            if not result.success:
                return result.as_dict()

            lst = result.result
            assert (
                lst is not None
            ), "When collecting actions, the result should not be None in the success case"
            actions_info = extract_info(lst, action_package_yaml_directory)
        except Exception as e:
            log.exception("Error collecting actions.")
            return dict(
                success=False, message=f"Error collecting actions: {e}", result=None
            )

        return dict(success=True, message=None, result=actions_info)

    @command_dispatcher(commands.SEMA4AI_LIST_ACTIONS_INTERNAL)
    def _local_list_actions_internal(self, params: ListActionsParams | None):
        # i.e.: should not block.
        if not params:
            msg = f"Unable to collect actions because no arguments were given."
            return dict(success=False, message=msg, result=None)

        action_package_uri = params.get("action_package")
        if not action_package_uri:
            msg = f"Unable to collect actions because the target action_package was not given."
            return dict(success=False, message=msg, result=None)

        collect_datasources = bool(params.get("collect_datasources", False))

        return partial(
            self._local_list_actions_internal_impl,
            action_package_uri=action_package_uri,
            collect_datasources=collect_datasources,
        )

    def _local_list_actions_internal_impl(
        self, action_package_uri: str, collect_datasources: bool
    ) -> "ActionResultDict[list[ActionInfoTypedDict | DatasourceInfoTypedDict]]":
        from sema4ai_code.robo.collect_actions_ast import iter_actions_and_datasources

        # TODO: We should move this code somewhere else and have a cache of
        # things so that when the user changes anything the client is notified
        # about it.
        p = Path(uris.to_fs_path(action_package_uri))
        if not p.exists():
            msg = f"Unable to collect actions/datasources from: {p} because it does not exist."
            return ActionResult.make_failure(msg).as_dict()  # type: ignore

        if not p.is_dir():
            p = p.parent

        try:
            actions_and_datasources = list(
                iter_actions_and_datasources(p, collect_datasources)
            )
        except Exception as e:
            log.exception("Error collecting actions/datasources.")
            return dict(
                success=False,
                message=f"Error collecting actions/datasources: {e}",
                result=None,
            )

        return dict(success=True, message=None, result=actions_and_datasources)

    @command_dispatcher(commands.SEMA4AI_LIST_WORK_ITEMS_INTERNAL)
    def _local_list_work_items_internal(
        self, params: ListWorkItemsParams | None = None
    ) -> ActionResultDictWorkItems:
        from sema4ai_code.protocols import WorkItemsInfo

        if params is None:
            return dict(
                success=False,
                message=f"Parameters not passed for {commands.SEMA4AI_LIST_WORK_ITEMS_INTERNAL}.",
                result=None,
            )

        robot = params.get("robot")
        if not robot:
            return dict(
                success=False,
                message=f"Expected 'robot' to be passed and valid in args.",
                result=None,
            )

        increment_output = params.get("increment_output")
        if increment_output is None:
            return dict(
                success=False,
                message=f"Expected 'increment_output' to be passed and valid in args.",
                result=None,
            )

        output_prefix = params.get("output_prefix")
        if not output_prefix:
            output_prefix = "run-"

        if not output_prefix.endswith("-"):
            return dict(
                success=False,
                message=f"output-prefix must end with '-'. Found: {output_prefix}",
                result=None,
            )

        path = Path(robot)
        try:
            stat = path.stat()
        except Exception:
            message = f"Expected {path} to exist."
            log.exception(message)
            return dict(success=False, message=message, result=None)

        robot_yaml = self._find_robot_yaml_path_from_path(path, stat)
        if not robot_yaml:
            return dict(
                success=False,
                message=f"Unable to find robot.yaml from {robot}.",
                result=None,
            )

        work_items_in_dir = robot_yaml.parent / "devdata" / "work-items-in"
        work_items_out_dir = robot_yaml.parent / "devdata" / "work-items-out"

        input_work_items: list[WorkItem] = []
        output_work_items: list[WorkItem] = []

        def sort_by_number_postfix(entry: WorkItem):
            try:
                return int(entry["name"].rsplit("-", 1)[-1])
            except Exception:
                # That's ok, item just doesn't match our expected format.
                return 9999999

        if work_items_in_dir.is_dir():
            input_work_items.extend(self._collect_work_items(work_items_in_dir))
            input_work_items.sort(key=sort_by_number_postfix)

        if work_items_out_dir.is_dir():
            output_work_items.extend(self._collect_work_items(work_items_out_dir))
            output_work_items.sort(key=sort_by_number_postfix)
            if increment_output:
                output_work_items = self._schedule_output_work_item_removal(
                    output_work_items, output_prefix
                )

        if increment_output:
            new_output_workitem_str = str(
                self._compute_new_output_workitem_path(
                    work_items_out_dir, output_work_items, output_prefix
                )
            )
        else:
            new_output_workitem_str = ""

        work_items_info: WorkItemsInfo = {
            "robot_yaml": str(robot_yaml),
            "input_folder_path": str(work_items_in_dir),
            "output_folder_path": str(work_items_out_dir),
            "input_work_items": input_work_items,
            "output_work_items": output_work_items,
            "new_output_workitem_path": new_output_workitem_str,
        }
        return dict(success=True, message=None, result=work_items_info)

    TIMEOUT_TO_CONSIDER_LAST_RUN_FRESH = 10.0  # In seconds

    OUTPUT_ITEMS_TO_KEEP = 5

    def _compute_new_output_workitem_path(
        self,
        work_items_out_dir: Path,
        output_work_items: list[WorkItem],
        output_prefix: str,
    ):
        max_run, last_time = self._prefix_to_last_run_number_and_time.get(
            output_prefix, (0, 0)
        )

        if max_run > 0:
            if time.time() - last_time > self.TIMEOUT_TO_CONSIDER_LAST_RUN_FRESH:
                # If the user does 2 subsequent runs, we will want to provide
                # different ids (i.e.: run-1 / run-2), but if XX seconds already
                # elapsed from the last run, we start to consider only the
                # filesystem entries.
                max_run = 0

        for work_item in output_work_items:
            name = work_item["name"]
            if name.startswith(output_prefix):
                try:
                    run_number = int(name[len(output_prefix) :])
                except Exception:
                    pass  # Just ignore (it wouldn't clash anyways)
                else:
                    if run_number > max_run:
                        max_run = run_number

        next_run = max_run + 1
        self._prefix_to_last_run_number_and_time[output_prefix] = (
            next_run,
            time.time(),
        )
        return work_items_out_dir / f"{output_prefix}{next_run}" / "work-items.json"

    def _collect_work_items(self, work_items_dir: Path) -> Iterator[WorkItem]:
        def create_work_item(json_path) -> WorkItem:
            return {"name": json_path.parent.name, "json_path": str(json_path)}

        for path in work_items_dir.iterdir():
            json_path = path / "work-items.json"
            if json_path.is_file():
                yield create_work_item(json_path)
            else:
                json_path = path / "work-items.output.json"
                if json_path.is_file():
                    yield create_work_item(json_path)

    # Automatically schedule a removal of work item that matches the output prefix
    def _schedule_output_work_item_removal(
        self, output_work_items: list[WorkItem], output_prefix: str
    ) -> list[WorkItem]:
        import re

        # Find the amount of work items that match the output prefix
        pattern = rf"^{re.escape(output_prefix)}\d+$"
        non_recyclable_output_work_items = []
        recyclable_output_work_items = []

        for output_work_item in output_work_items:
            if re.match(pattern, output_work_item["name"]):
                recyclable_output_work_items.append(output_work_item)
            else:
                non_recyclable_output_work_items.append(output_work_item)

        while len(recyclable_output_work_items) > self.OUTPUT_ITEMS_TO_KEEP:
            # Items should be sorted already, so, we can erase the first ones
            # (and remove them from the list as they should be considered
            # outdated at this point).
            remove_item: WorkItem = recyclable_output_work_items.pop(0)
            self._schedule_path_removal(Path(remove_item["json_path"]).parent)

        return recyclable_output_work_items + non_recyclable_output_work_items

    def _find_robot_yaml_path_from_path(self, path: Path, stat) -> Path | None:
        from sema4ai_code import find_robot_yaml

        return find_robot_yaml.find_robot_yaml_path_from_path(path, stat)

    # @TODO:
    # At this point, this should probably be renamed or split, as it will list not only Robots,
    # but also Action packages.
    @command_dispatcher(commands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL)
    def _local_list_robots(self, params=None) -> ActionResultDictLocalRobotMetadata:
        try:
            ret = self._workspace_manager.get_local_robots()
        except Exception as e:
            log.exception("Error listing robots.")
            return dict(success=False, message=str(e), result=None)

        return dict(success=True, message=None, result=ret)

    def m_list_robots(self) -> ActionResultDictLocalRobotMetadata:
        return self._local_list_robots()

    def m_list_dev_tasks(self, action_package_uri: str) -> partial:
        return require_monitor(
            partial(self._list_dev_tasks_in_thread, action_package_uri)
        )

    def m_get_external_api_url(self) -> str | None:
        home = get_default_sema4ai_home()
        external_api_pid = home / "sema4ai-studio" / "external-api-server.pid"

        if not external_api_pid.exists():
            return None

        try:
            with external_api_pid.open("r", encoding="utf-8") as file:
                import json

                file_content = json.load(file)
        except Exception as e:
            log.exception(f"Failed to read external-api-server.pid file: {e}")
            return None

        def _is_port_open(port) -> bool:
            import socket

            try:
                conn = socket.create_connection(("localhost", port), timeout=0.05)
                conn.close()
            except (OSError, ConnectionRefusedError):
                return False

            return True

        if "port" in file_content:
            if _is_port_open(file_content["port"]):
                return f"http://localhost:{file_content['port']}/api/v1/ace-services"

            return None

        return None

    def _get_actions_metadata(
        self,
        action_package_path: str,
        monitor: IMonitor,
    ) -> ActionResultDict:
        from sema4ai_code.robo.collect_actions import get_metadata

        p = Path(uris.to_fs_path(action_package_path))
        if not p.exists():
            msg = f"Unable to collect actions metadata from: {p} because it does not exist."
            return dict(success=False, message=msg, result=None)

        try:
            if not self.workspace:
                return dict(
                    success=False, message="No workspace currently open", result=None
                )

            result = get_metadata(self._pm, action_package_path, monitor)
        except Exception as e:
            log.exception("Error collecting actions metadata.")
            return dict(
                success=False,
                message=f"Error collecting actions metadata: {e}",
                result=None,
            )

        return result.as_dict()

    def m_get_actions_metadata(
        self, action_package_path: str
    ) -> partial[ActionResultDict]:
        return require_monitor(
            partial(
                self._get_actions_metadata,
                action_package_path=action_package_path,
            )
        )

    def _list_dev_tasks_in_thread(
        self, action_package_uri: str, monitor: IMonitor
    ) -> ActionResultDict:
        """
        Provides a dict[str, str] with the dev tasks found in the Action Package.
        """
        from sema4ai_code.robo.list_dev_tasks import list_dev_tasks_from_content

        action_package_yaml_path = Path(uris.to_fs_path(action_package_uri))
        try:
            action_package_yaml_content = action_package_yaml_path.read_text()
        except Exception as e:
            return dict(
                success=False,
                message=f"Unable to read: {action_package_yaml_path}. Error: {e}",
                result=None,
            )

        return list_dev_tasks_from_content(
            action_package_yaml_content, action_package_yaml_path
        ).as_dict()

    def m_compute_dev_task_spec_to_run(
        self, package_yaml_path: str, task_name: str
    ) -> partial:
        return require_monitor(
            partial(
                self._compute_dev_task_spec_to_run_in_thread,
                package_yaml_path,
                task_name,
            )
        )

    def _compute_dev_task_spec_to_run_in_thread(
        self,
        package_yaml_path: str,
        task_name: str,
        monitor: IMonitor,
    ) -> ActionResultDict:
        import json
        import shlex

        from sema4ai_ls_core.process import build_python_launch_env

        from sema4ai_code.robo import launch_dev_task

        result = self._list_dev_tasks_in_thread(
            uris.from_fs_path(package_yaml_path), monitor
        )
        if not result["success"]:
            return result

        try:
            dct = result["result"]
            if dct is None:
                return dict(
                    success=False,
                    message="Expected result to be a dict.",
                    result=None,
                )
            task_contents = dct[task_name]
        except KeyError:
            return dict(
                success=False,
                message=f"dev-task: {task_name} not found in: {package_yaml_path}.",
                result=None,
            )

        task_command = task_contents.strip()
        if not task_command:
            return dict(
                success=False,
                message="Expected task contents to be a non-empty string.",
                result=None,
            )

        task_commands: list[list[str]] = []
        for line in task_command.splitlines():
            monitor.check_cancelled()
            if line.strip():
                try:
                    c = shlex.split(line.strip())
                except Exception as e:
                    msg = f"Unable to shlex.split command: {line.strip()}. Error: {e}"
                    log.critical(msg)
                    return dict(success=False, message=msg, result=None)

                if not c:
                    msg = f"Unable to make sense of command: {line.strip()}."
                    log.critical(msg)
                    return dict(success=False, message=msg, result=None)
                task_commands.append(c)

        if len(task_commands) == 1:
            log.debug(f"Parsed command as: {task_commands[0]}")
        else:
            m = "\n    ".join(str(x) for x in task_commands)
            log.debug(f"Parsed (multiple) commands as:\n{m}")

        cwd = str(Path(package_yaml_path).parent)
        interpreter_info_result = self._resolve_interpreter(
            params=dict(target_robot=package_yaml_path)
        )
        monitor.check_cancelled()
        if not interpreter_info_result["success"]:
            return interpreter_info_result

        interpreter_info = interpreter_info_result["result"]

        env = build_python_launch_env(interpreter_info["environ"])

        log.debug("Environment variables:")
        for env_key in ("PATH", "PYTHONPATH"):
            env_val = env.get(env_key)
            if env_val:
                log.debug(f"{env_key}:")
                for path_part in env_val.split(os.path.pathsep):
                    log.debug(f"  {path_part}")
            else:
                log.debug(f"{env_key}: (none)")
        try:
            PATH = env["PATH"]

            commands_list = []

            for command in task_commands:
                # search for command[0] in PATH

                command_path = None
                for path in PATH.split(os.path.pathsep):
                    if os.path.exists(os.path.join(path, command[0])):
                        command_path = os.path.join(path, command[0])
                        break
                    if sys.platform == "win32":
                        if os.path.exists(os.path.join(path, command[0] + ".exe")):
                            command_path = os.path.join(path, command[0] + ".exe")
                            break

                if not command_path:
                    msg = f"Command: {command[0]} not found in PATH."
                    log.critical(msg)
                    return dict(success=False, message=msg, result=None)
                log.debug(f"Target program: {command_path}")

                monitor.check_cancelled()

                commands_list.append(command)

            env["SEMA4AI_RUN_DEV_TASKS"] = json.dumps(commands_list)
            python = env["PYTHON_EXE"]
            task_spec = {
                "env": env,
                "cwd": cwd,
                "program": python,
                "args": [launch_dev_task.__file__],
            }

            return dict(success=True, message=None, result=task_spec)

        except Exception as e:
            msg = f"It was not possible to run the task: {task_name}.\nThe error below happened when running the command:\n{task_command}\n{e}"
            log.critical(msg)
            return dict(success=False, message=msg, result=None)

    def _validate_directory(self, directory) -> str | None:
        if not os.path.exists(directory):
            return f"Expected: {directory} to exist."

        if not os.path.isdir(directory):
            return f"Expected: {directory} to be a directory."
        return None

    def _add_package_info_to_access_lru(
        self, workspace_id, package_id, directory
    ) -> None:
        try:
            lst: list[PackageInfoInLRUDict] = self._dir_cache.load(
                self.PACKAGE_ACCESS_LRU_CACHE_KEY, list
            )
        except KeyError:
            lst = []

        new_lst: list[PackageInfoInLRUDict] = [
            {
                "workspace_id": workspace_id,
                "package_id": package_id,
                "directory": directory,
                "time": time.time(),
            }
        ]
        for i, entry in enumerate(lst):
            if isinstance(entry, dict):
                if (
                    entry.get("package_id") == package_id
                    and entry.get("workspace_id") == workspace_id
                ):
                    continue  # Skip this one (we moved it to the start of the LRU).
                new_lst.append(entry)

            if i == 5:
                break  # Max number of items in the LRU reached.

        self._dir_cache.store(self.PACKAGE_ACCESS_LRU_CACHE_KEY, new_lst)

    @command_dispatcher(commands.SEMA4AI_UPLOAD_TO_EXISTING_ROBOT_INTERNAL)
    def _upload_to_existing_activity(
        self, params: UploadRobotParamsDict
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        self._feedback.metric("vscode.cloud.upload.existing")

        directory = params["directory"]
        error_msg = self._validate_directory(directory)
        if error_msg:
            return {"success": False, "message": error_msg, "result": None}

        workspace_id = params["workspaceId"]
        robot_id = params["robotId"]
        with progress_context(
            self._endpoint, "Uploading to existing robot", self._dir_cache
        ):
            result = self._rcc.cloud_set_robot_contents(
                directory, workspace_id, robot_id
            )
            self._add_package_info_to_access_lru(workspace_id, robot_id, directory)

        return result.as_dict()

    @command_dispatcher(commands.SEMA4AI_UPLOAD_TO_NEW_ROBOT_INTERNAL)
    def _upload_to_new_robot(
        self, params: UploadNewRobotParamsDict
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        self._feedback.metric("vscode.cloud.upload.new")

        directory = params["directory"]
        error_msg = self._validate_directory(directory)
        if error_msg:
            return {"success": False, "message": error_msg, "result": None}

        workspace_id = params["workspaceId"]
        robot_name = params["robotName"]

        # When we upload to a new activity, clear the existing cache key.
        self._discard_listed_workspaces_info()
        with progress_context(
            self._endpoint, "Uploading to new robot", self._dir_cache
        ):
            new_robot_result = self._rcc.cloud_create_robot(workspace_id, robot_name)
            if not new_robot_result.success:
                return new_robot_result.as_dict()

            robot_id = new_robot_result.result
            if not robot_id:
                return dict(
                    success=False,
                    message="Expected to have package id from creating new activity.",
                    result=None,
                )

            result = self._rcc.cloud_set_robot_contents(
                directory, workspace_id, robot_id
            )
            self._add_package_info_to_access_lru(workspace_id, robot_id, directory)
        return result.as_dict()

    @command_dispatcher(commands.SEMA4AI_GET_PLUGINS_DIR, str)
    def _get_plugins_dir(self, params=None) -> str:
        return str(Path(__file__).parent / "plugins")

    @command_dispatcher(commands.SEMA4AI_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH)
    def _compute_robot_launch_from_robocorp_code_launch(
        self, params: dict
    ) -> ActionResultDictRobotLaunch:
        from sema4ai_code import compute_launch

        name: str | None = params.get("name")
        request: str | None = params.get("request")

        # Task package related:
        task: str | None = params.get("task")
        robot: str | None = params.get("robot")

        # Action package related:
        package: str | None = params.get("package")
        action_name: str | None = params.get("actionName")
        uri: str | None = params.get("uri")
        json_input: str | None = params.get("jsonInput")

        additional_pythonpath_entries: list[str] | None = params.get(
            "additionalPythonpathEntries"
        )
        env: dict[str, str] | None = params.get("env")
        python_exe: str | None = params.get("pythonExe")

        return compute_launch.compute_robot_launch_from_robocorp_code_launch(
            name=name,
            request=request,
            task=task,
            robot=robot,
            additional_pythonpath_entries=additional_pythonpath_entries,
            env=env,
            python_exe=python_exe,
            package=package,
            action_name=action_name,
            uri=uri,
            json_input=json_input,
        )

    @property
    def pm(self):
        return self._pm

    @command_dispatcher(commands.SEMA4AI_RESOLVE_INTERPRETER, dict)
    def _resolve_interpreter(self, params=None) -> ActionResultDict:
        from sema4ai_ls_core.ep_resolve_interpreter import (
            EPResolveInterpreter,
            IInterpreterInfo,
        )

        try:
            target_robot: str = params.get("target_robot")
            if not target_robot:
                msg = f"Error resolving interpreter: No 'target_robot' passed. Received: {params}"
                log.critical(msg)
                return {"success": False, "message": msg, "result": None}

            for ep in self._pm.get_implementations(EPResolveInterpreter):
                interpreter_info: IInterpreterInfo = (
                    ep.get_interpreter_info_for_doc_uri(uris.from_fs_path(target_robot))
                )
                if interpreter_info is not None:
                    return {
                        "success": True,
                        "message": None,
                        "result": {
                            "pythonExe": interpreter_info.get_python_exe(),
                            "environ": interpreter_info.get_environ(),
                            "additionalPythonpathEntries": interpreter_info.get_additional_pythonpath_entries(),
                        },
                    }
        except Exception as e:
            log.exception(f"Error resolving interpreter. Args: {params}")
            return {"success": False, "message": str(e), "result": None}

        # i.e.: no error but we couldn't find an interpreter.
        return {
            "success": False,
            "message": "Couldn't find an interpreter",
            "result": None,
        }

    @command_dispatcher(commands.SEMA4AI_VERIFY_LIBRARY_VERSION_INTERNAL)
    def _verify_library_version(self, params: dict) -> LibraryVersionInfoDict:
        from sema4ai_ls_core import yaml_wrapper

        conda_prefix = Path(params["conda_prefix"])
        if not conda_prefix.exists():
            return {
                "success": False,
                "message": f"Expected {conda_prefix} to exist.",
                "result": None,
            }

        golden_ee = conda_prefix / "golden-ee.yaml"
        if not golden_ee.exists():
            return {
                "success": False,
                "message": f"Expected {golden_ee} to exist.",
                "result": None,
            }

        try:
            with golden_ee.open("r", encoding="utf-8") as stream:
                yaml_contents = yaml_wrapper.load(stream)
        except Exception:
            msg = f"Error loading: {golden_ee} as yaml."
            log.exception(msg)
            return {"success": False, "message": msg, "result": None}

        libs_and_version = params["libs_and_version"]
        lib_to_version = dict(libs_and_version)

        if not isinstance(yaml_contents, list):
            return {
                "success": False,
                "message": f"Expected {golden_ee} to have a list of dicts as the root.",
                "result": None,
            }

        version_mismatch_error_msgs: list[str] = []
        for entry in yaml_contents:
            if isinstance(entry, dict):
                name = entry.get("name")
                if not isinstance(name, str):
                    continue

                found_version = entry.get("version")
                version = lib_to_version.get(name)
                if version is None or found_version is None:
                    continue

                # Ok, this is one of the expected libraries.
                expected_version = _parse_version(version)
                if _verify_version(_parse_version(found_version), expected_version):
                    return {
                        "success": True,
                        "message": "",
                        "result": {"library": name, "version": found_version},
                    }

                version_mismatch_error_msgs.append(
                    f"{name} {found_version} does not match minimum required version ({version})."
                )

        if version_mismatch_error_msgs:
            return {
                "success": False,
                "message": "\n".join(version_mismatch_error_msgs),
                "result": None,
            }
        return {
            "success": False,
            "message": f"Libraries: {', '.join([str(x) for x in lib_to_version])} not found in environment.",
            "result": None,
        }

    @command_dispatcher(commands.SEMA4AI_SEND_METRIC)
    def _send_metric(self, params: dict) -> ActionResultDict:
        name = params.get("name")
        value = params.get("value")
        if name is None or value is None:
            return {
                "success": False,
                "message": f"Expected name and value. Received name: {name!r} value: {value!r}",
                "result": None,
            }

        self._feedback.metric(name, value)
        return {"success": True, "message": None, "result": None}

    def m_text_document__code_lens(self, **kwargs) -> partial | None:
        from sema4ai_code.robo.launch_code_lens import compute_code_lenses

        doc_uri = kwargs["textDocument"]["uri"]

        return compute_code_lenses(self._workspace, self._config_provider, doc_uri)

    def m_text_document__hover(self, **kwargs) -> Any:
        """
        When hovering over a png in base64 surrounded by double-quotes... something as:
        "iVBORw0KGgo...rest of png in base 64 contents..."

        i.e.: Provide the contents in markdown format to show the actual image from the
        locators.json.
        """
        from sema4ai_code.protocols import PackageYamlName

        doc_uri = kwargs["textDocument"]["uri"]
        # Note: 0-based
        line: int = kwargs["position"]["line"]
        col: int = kwargs["position"]["character"]
        fspath = uris.to_fs_path(doc_uri)

        if fspath.endswith("locators.json"):
            return require_monitor(
                partial(self._hover_on_locators_json, doc_uri, line, col)
            )
        if fspath.endswith(("conda.yaml", "action-server.yaml")):
            return require_monitor(
                partial(self._hover_on_conda_yaml, doc_uri, line, col)
            )
        if fspath.endswith("package.yaml"):
            return require_monitor(
                partial(self._hover_on_package_yaml, doc_uri, line, col)
            )
        if fspath.endswith(PackageYamlName.AGENT.value):
            return require_monitor(
                partial(self._hover_on_agent_spec_yaml, doc_uri, line, col)
            )
        return None

    def _hover_on_conda_yaml(
        self, doc_uri, line, col, monitor: IMonitor
    ) -> HoverTypedDict | None:
        from sema4ai_ls_core.protocols import IDocument

        from sema4ai_code.hover import hover_on_conda_yaml

        ws = self._workspace
        if ws is None:
            return None

        doc: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
        if doc is None:
            return None

        return hover_on_conda_yaml(doc, line, col, self._pypi_cloud, self._conda_cloud)

    def _hover_on_package_yaml(
        self, doc_uri, line, col, monitor: IMonitor
    ) -> HoverTypedDict | None:
        from sema4ai_ls_core.protocols import IDocument

        from sema4ai_code.hover import hover_on_package_yaml

        ws = self._workspace
        if ws is None:
            return None

        doc: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
        if doc is None:
            return None

        return hover_on_package_yaml(
            doc, line, col, self._pypi_cloud, self._conda_cloud
        )

    def _hover_on_agent_spec_yaml(
        self, doc_uri, line, col, monitor: IMonitor
    ) -> HoverTypedDict | None:
        from sema4ai_ls_core.protocols import IDocument

        from sema4ai_code.agents.hover_agent_spec import hover_on_agent_spec_yaml

        ws = self._workspace
        if ws is None:
            return None

        doc: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
        if doc is None:
            return None

        return hover_on_agent_spec_yaml(doc, line, col, monitor)

    def _hover_on_locators_json(
        self, doc_uri, line, col, monitor: IMonitor
    ) -> dict | None:
        from sema4ai_ls_core.lsp import MarkupContent, MarkupKind, Range
        from sema4ai_ls_core.protocols import IDocument, IDocumentSelection

        ws = self._workspace
        if ws is None:
            return None

        document: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
        if document is None:
            return None
        sel: IDocumentSelection = document.selection(line, col)
        current_line: str = sel.current_line
        i: int = current_line.find(
            '"iVBORw0KGgo'
        )  # I.e.: pngs in base64 always start with this prefix.
        if i >= 0:
            current_line = current_line[i + 1 :]
            i = current_line.find('"')
            if i >= 0:
                current_line = current_line[0:i]
                image_path = f"data:image/png;base64,{current_line}"
                s = f"![Screenshot]({image_path})"
                return {
                    "contents": MarkupContent(MarkupKind.Markdown, s).to_dict(),
                    "range": Range((line, col), (line, col)).to_dict(),
                }

        # Could not find a base-64 img embedded, let's see if we have an element
        # with a relative path.
        import re

        p = Path(document.path).parent

        for found in re.findall('"(.+?)"', current_line):
            if found.endswith(".png"):
                check = p / found
                if check.exists():
                    with check.open("rb") as image_content:
                        image_base64 = b64encode(image_content.read()).decode("utf-8")
                    image_path = f"data:image/png;base64,{image_base64}"
                    s = f"![Screenshot]({image_path})"
                    return {
                        "contents": MarkupContent(MarkupKind.Markdown, s).to_dict(),
                        "range": Range((line, col), (line, col)).to_dict(),
                    }

        return None

    def _get_line_col(self, name, content_lines):
        """
        Note: there are Python libraries that can be used to extract line/col from json information:
        https://pypi.org/project/dirtyjson/
        https://pypi.org/project/json-cfg/ (jsoncfg.node_location(node)).

        So, we could use the json parsing with this, but there's some logic in
        the LocatorsDatabase to deal with old formats and we may have to deal with
        old formats too in this case... given that, for now let's just see if we
        match a substring there (it's very inefficient, but we don't expect
        thousands of locators, so, it should be ok).
        """
        match = f'"{name}"'
        for i, line in enumerate(content_lines):
            col = line.find(match)
            if col >= 0:
                return i, col

        return 0, 0  # I.e.: unable to find

    @staticmethod
    def _load_locators_db(robot_yaml_path) -> ActionResultDictLocatorsJson:
        from .vendored.locators.database import LocatorsDatabase

        locators_json = Path(robot_yaml_path).parent / "locators.json"
        db = LocatorsDatabase(str(locators_json))
        db.load()
        if db.error:
            error = db.error
            if not isinstance(error, str):
                if isinstance(error, tuple) and len(error) == 2:
                    try:
                        error = error[0] % error[1]
                    except Exception:
                        error = str(error)
                else:
                    error = str(error)
            return {"success": False, "message": error, "result": None}
        return {"success": True, "message": None, "result": (db, locators_json)}

    @command_dispatcher(commands.SEMA4AI_GET_LOCATORS_JSON_INFO)
    def _get_locators_json_info(
        self, params: dict | None = None
    ) -> ActionResultDictLocatorsJsonInfo:
        from .vendored.locators.containers import Locator

        if not params or "robotYaml" not in params:
            return {
                "success": False,
                "message": "robot.yaml filename not passed",
                "result": None,
            }

        path = Path(params["robotYaml"])
        locators_json_info: list[LocatorEntryInfoDict] = []
        locator: Locator
        try:
            action_result: ActionResultDictLocatorsJson = self._load_locators_db(path)
            if action_result["success"]:
                result = action_result["result"]
                if not result:
                    return {
                        "success": False,
                        "message": f"Expected result to be a tuple(db, locators_json). Found {result}",
                        "result": None,
                    }

                db, locators_json = result
            else:
                return {
                    "success": False,
                    "message": str(action_result["message"]),
                    "result": None,
                }

            content_lines: list = []
            if Path(locators_json).exists():
                with locators_json.open("r") as stream:
                    contents = stream.read()
                content_lines = contents.splitlines()

            for name, locator in db.locators.items():
                as_dict = locator.to_dict()
                line, col = self._get_line_col(name, content_lines)
                locators_json_info.append(
                    {
                        "name": name,
                        "line": line,
                        "column": col,
                        "type": as_dict["type"],
                        "filePath": str(locators_json),
                    }
                )
        except Exception as e:
            log.exception(f"Error loading locators")
            return {"success": False, "message": str(e), "result": None}

        return {"success": True, "message": None, "result": locators_json_info}

    @command_dispatcher(commands.SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL)
    def _remove_locator_from_json_internal(
        self, params: dict | None = None
    ) -> ActionResultDict:
        if not params or "robotYaml" not in params or "name" not in params:
            return {
                "success": False,
                "message": "robot.yaml filename or locator name not passed",
                "result": None,
            }

        path = Path(params["robotYaml"])
        name = params["name"]
        db, locators_json = None, None
        try:
            action_result: ActionResultDictLocatorsJson = self._load_locators_db(path)
            if action_result["success"]:
                result = action_result["result"]
                if not result:
                    return {
                        "success": False,
                        "message": f"Expected result to be a tuple(db, locators_json). Found {result}",
                        "result": None,
                    }

                db, locators_json = result
            else:
                return {
                    "success": False,
                    "message": str(action_result["message"]),
                    "result": None,
                }
            if not db.error:
                del db.locators[name]
                db.save()
        except Exception as e:
            log.exception(f'Error removing locator "{name}" from: {locators_json}')
            return {"success": False, "message": str(e), "result": None}

        return {"success": True, "message": None, "result": None}

    @command_dispatcher(commands.SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL)
    def _list_action_templates(self) -> ActionResultDict:
        return require_monitor(partial(self._list_action_templates_threaded))

    def _list_action_templates_threaded(self, monitor: IMonitor) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint, "Collecting action server templates", self._dir_cache
        ):
            return self._action_server.get_action_templates().as_dict()

    @command_dispatcher(commands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL)
    def _create_action_package(
        self, params: CreateActionPackageParamsDict
    ) -> ActionResultDict:
        directory = params["directory"]
        template = params["template"]
        name = params["name"]

        return require_monitor(
            partial(self._create_action_package_threaded, directory, template, name)
        )

    def _create_action_package_threaded(
        self, directory: str, template: str, name: str, monitor: IMonitor
    ) -> ActionResultDict:
        return self._action_server.create_action_package(
            directory, template, name
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_CLOUD_LOGIN_INTERNAL)
    def _action_server_login(self, params: ActionServerLoginDict) -> ActionResultDict:
        access_credentials = params["access_credentials"]
        hostname = params["hostname"]

        return self._action_server.cloud_login(access_credentials, hostname).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL)
    def _action_server_verify_login(self) -> ActionServerVerifyLoginResultDict:
        return self._action_server.verify_login().as_dict()

    @command_dispatcher(
        commands.SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL
    )
    def _action_server_list_organizations(
        self, params: ActionServerAccessCredentialsDict
    ) -> ActionServerListOrgsResultDict:
        access_credentials = (
            params["access_credentials"] if "access_credentials" in params else None
        )
        hostname = params["hostname"] if "hostname" in params else None

        return self._action_server.list_organizations(
            access_credentials, hostname
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL)
    def _action_server_package_build(
        self, params: ActionServerPackageBuildDict
    ) -> ActionServerPackageBuildResultDict:
        workspace_dir = params["workspace_dir"]
        output_dir = params["output_dir"]

        return self._action_server.package_build(workspace_dir, output_dir).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL)
    def _action_server_package_upload(
        self, params: ActionServerPackageUploadDict
    ) -> ActionServerPackageUploadStatusDict:
        package_path = params["package_path"]
        organization_id = params["organization_id"]
        access_credentials = (
            params["access_credentials"] if "access_credentials" in params else None
        )
        hostname = params["hostname"] if "hostname" in params else None

        return self._action_server.package_upload(
            package_path, organization_id, access_credentials, hostname
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL)
    def _action_server_package_status(
        self, params: ActionServerPackageStatusDict
    ) -> ActionServerPackageUploadStatusDict:
        package_id = params["package_id"]
        organization_id = params["organization_id"]
        access_credentials = (
            params["access_credentials"] if "access_credentials" in params else None
        )
        hostname = params["hostname"] if "hostname" in params else None

        return self._action_server.package_status(
            package_id, organization_id, access_credentials, hostname
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL)
    def _action_server_package_set_changelog(
        self, params: ActionServerPackageSetChangelogDict
    ) -> ActionResultDict:
        package_id = params["package_id"]
        organization_id = params["organization_id"]
        changelog_input = params["changelog_input"]
        access_credentials = (
            params["access_credentials"] if "access_credentials" in params else None
        )
        hostname = params["hostname"] if "hostname" in params else None

        return self._action_server.package_set_changelog(
            package_id, organization_id, changelog_input, access_credentials, hostname
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL)
    def _action_server_package_metadata(
        self, params: ActionServerPackageMetadataDict
    ) -> ActionResultDict:
        action_package_path = params["action_package_path"]
        output_file_path = params["output_file_path"]

        return self._action_server.package_metadata(
            action_package_path, output_file_path
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_RCC_DOWNLOAD_INTERNAL)
    def _rcc_download(self, params: DownloadToolDict | None = None) -> ActionResultDict:
        from sema4ai_code.rcc import download_rcc

        location = params["location"] if params else self._rcc.get_rcc_location(False)

        try:
            download_rcc(location, endpoint=self._endpoint)
        except Exception as e:
            return {
                "success": False,
                "message": f"RCC download failed: {e}",
                "result": None,
            }

        return {"success": True, "message": None, "result": location}

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL)
    def _action_server_download(
        self, params: DownloadToolDict | None = None
    ) -> ActionResultDict:
        from sema4ai_code.action_server import download_action_server

        location = (
            params["location"]
            if params
            else self._action_server.get_action_server_location(False)
        )

        try:
            download_action_server(location, endpoint=self._endpoint)
        except Exception as e:
            return {
                "success": False,
                "message": f"Action Server download failed: {e}",
                "result": None,
            }

        return {"success": True, "message": None, "result": location}

    @command_dispatcher(commands.SEMA4AI_AGENT_CLI_DOWNLOAD_INTERNAL)
    def _agent_cli_download(self, params: DownloadToolDict | None = None):
        return require_monitor(partial(self._agent_cli_download_threaded, params))

    def _agent_cli_download_threaded(
        self, params: DownloadToolDict | None, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_code.agent_cli import download_agent_cli

        location = (
            params["location"]
            if params
            else self._agent_cli.get_agent_cli_location(False)
        )

        try:
            download_agent_cli(location, endpoint=self._endpoint)
        except Exception as e:
            return {
                "success": False,
                "message": f"Agent CLI download failed: {e}",
                "result": None,
            }

        return {"success": True, "message": None, "result": location}

    @command_dispatcher(commands.SEMA4AI_ACTION_SERVER_VERSION_INTERNAL)
    def _action_server_version(self, download_if_missing=True) -> ActionResultDict:
        return self._action_server.get_version(
            download_if_missing=download_if_missing
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_AGENT_CLI_VERSION_INTERNAL)
    def _agent_cli_version(self, download_if_missing=True) -> ActionResultDict:
        return self._agent_cli.get_version(
            download_if_missing=download_if_missing
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL)
    def _create_agent_package(
        self, params: CreateAgentPackageParamsDict
    ) -> ActionResultDict:
        directory = params["directory"]
        name = params["name"]

        return self._agent_cli.create_agent_package(directory, name).as_dict()

    @command_dispatcher(commands.SEMA4AI_PACK_AGENT_PACKAGE_INTERNAL)
    def _pack_agent_package(
        self, params: CreateAgentPackageParamsDict
    ) -> ActionResultDict:
        directory = params["directory"]

        ws = self.workspace
        if ws is None:
            return {
                "success": False,
                "message": "Workspace already closed",
                "result": None,
            }
        return require_monitor(
            partial(self._pack_agent_package_threaded, directory, ws)
        )

    @staticmethod
    def _bump_version(version: str, version_type: str) -> str:
        try:
            major, minor, patch = map(int, version.split("."))
        except ValueError:
            raise ValueError(
                "Version must be in the format 'major.minor.patch', e.g. 1.0.1"
            )

        version_type = version_type.lower()
        if version_type == "patch":
            patch += 1
        elif version_type == "minor":
            minor += 1
            patch = 0
        elif version_type == "major":
            major += 1
            minor, patch = 0, 0
        else:
            raise ValueError(
                "Invalid version type. Choose 'Patch', 'Minor', or 'Major'."
            )

        return f"{major}.{minor}.{patch}"

    @command_dispatcher(commands.SEMA4AI_UPDATE_AGENT_VERSION_INTERNAL)
    def _update_agent_version(
        self, params: UpdateAgentVersionParamsDict
    ) -> ActionResultDict:
        agent_spec_path = Path(params["agent_path"]) / "agent-spec.yaml"
        version_type = params["version_type"]

        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            with agent_spec_path.open("r") as file:
                agent_spec = yaml.load(file.read())

            try:
                current_version = agent_spec["agent-package"]["agents"][0].get(
                    "version"
                )
            except Exception:
                raise ValueError("Version entry was not found in the agent spec.")

            bumped_version = (
                "0.0.1"
                if not current_version
                else self._bump_version(current_version, version_type)
            )
            agent_spec["agent-package"]["agents"][0]["version"] = bumped_version

            with agent_spec_path.open("w") as file:
                yaml.dump(agent_spec, file)

        except Exception as e:
            return ActionResult(success=False, message=str(e)).as_dict()

        return ActionResult(success=True, message=None).as_dict()

    @command_dispatcher(commands.SEMA4AI_GET_RUNBOOK_PATH_FROM_AGENT_SPEC_INTERNAL)
    def _get_runbook_path_from_agent_spec(
        self, params: AgentSpecPathDict
    ) -> ActionResultDict:
        agent_spec_path = params["agent_spec_path"]

        import yaml

        with open(agent_spec_path) as yaml_file:
            yaml_content = yaml.safe_load(yaml_file)

        try:
            runbook_path = yaml_content["agent-package"]["agents"][0]["runbook"]
        except Exception:
            return ActionResult(
                success=False, message="Runbook entry was not found in the agent spec."
            ).as_dict()

        return ActionResult(
            success=True,
            message=None,
            result=runbook_path,
        ).as_dict()

    @command_dispatcher(commands.SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL)
    def _refresh_agent_spec(self, params: AgentSpecPathDict) -> ActionResultDict:
        try:
            update_agent_spec(Path(params["agent_spec_path"]))
        except Exception as e:
            return ActionResult(
                success=False, message=f"Failed to refresh the agent configuration: {e}"
            ).as_dict()

        return ActionResult(success=True, message=None).as_dict()

    def _pack_agent_package_threaded(self, directory, ws, monitor: IMonitor):
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint, "Building Agent Package", self._dir_cache
        ):
            return self._agent_cli.pack_agent_package(directory, ws, monitor)

    def forward_msg(self, msg: dict) -> None:
        method = msg["method"]
        self._endpoint.notify(method, msg["params"])

    def m_oauth2_status(
        self, action_server_location: str, provide_access_token: bool = True
    ):
        return require_monitor(
            partial(
                self._oauth2.oauth2_status, action_server_location, provide_access_token
            )
        )

    def m_oauth2_login(
        self, action_server_location: str, provider: str, scopes: list[str]
    ):
        return require_monitor(
            partial(self._oauth2.oauth2_login, action_server_location, provider, scopes)
        )

    def m_oauth2_logout(self, action_server_location: str, provider: str):
        return require_monitor(
            partial(self._oauth2.oauth2_logout, action_server_location, provider)
        )

    def _get_gallery_action_packages(self) -> "GalleryActionPackages":
        if not hasattr(self, "_gallery_action_packages"):
            from sema4ai_code.agents.gallery_actions import GalleryActionPackages

            self._gallery_action_packages = GalleryActionPackages()

        return self._gallery_action_packages

    def m_list_gallery_action_packages(self) -> ActionResultDict:
        return require_monitor(partial(self._list_gallery_action_packages))

    def _list_gallery_action_packages(self, monitor: IMonitor) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint,
            "Listing action packages from Sema4.ai Gallery",
            self._dir_cache,
        ):
            return self._get_gallery_action_packages().list_packages().as_dict()

    def m_import_gallery_action_package(
        self, package_key: str, target_dir: str
    ) -> ActionResultDict:
        return require_monitor(
            partial(
                self._import_gallery_action_package_threaded, package_key, target_dir
            )
        )

    def _import_gallery_action_package_threaded(
        self, package_key: str, target_dir: str, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint,
            "Importing action package from Sema4.ai Gallery",
            self._dir_cache,
        ):
            return (
                self._get_gallery_action_packages()
                .extract_package(package_key, Path(target_dir), monitor)
                .as_dict()
            )

    def m_import_zip_as_action_package(
        self, zip_path: str, target_dir: str
    ) -> ActionResultDict:
        if not zip_path:
            return ActionResult.make_failure("zip_path may not be empty.").as_dict()

        if not isinstance(zip_path, str):
            return ActionResult.make_failure("zip_path must be a string.").as_dict()

        if not target_dir:
            return ActionResult.make_failure("target_dir may not be empty.").as_dict()

        if not Path(zip_path).exists():
            return ActionResult.make_failure(
                f"zip_path does not exist: {zip_path}"
            ).as_dict()

        return require_monitor(
            partial(self._import_zip_as_action_package, zip_path, target_dir)
        )

    def _import_zip_as_action_package(
        self, zip_path: str, target_dir: str, monitor: IMonitor
    ) -> ActionResultDict:
        from sema4ai_ls_core.progress_report import progress_context

        with progress_context(
            self._endpoint,
            "Importing action package from zip file",
            self._dir_cache,
        ):
            import zipfile

            import yaml

            try:
                # Check if the zip is a valid action package
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    if "package.yaml" not in zip_ref.namelist():
                        return ActionResult.make_failure(
                            "Invalid action package: package.yaml not found in the zip file."
                        ).as_dict()

                    # Read package.yaml content
                    with zip_ref.open("package.yaml") as package_yaml:
                        package_info = yaml.safe_load(package_yaml)

                    # Get the name from package.yaml and slugify it
                    package_name = package_info.get("name")
                    if not package_name:
                        return ActionResult.make_failure(
                            "Invalid package.yaml: 'name' field is missing."
                        ).as_dict()

                    from sema4ai_ls_core.basic import slugify

                    slugified_name = slugify(package_name)

                    # Create the final directory
                    final_dir = Path(target_dir) / slugified_name
                    final_dir.mkdir(parents=True, exist_ok=True)

                    # Extract the contents of the zip into the final directory
                    zip_ref.extractall(final_dir)

                return ActionResult.make_success(str(final_dir)).as_dict()
            except Exception as e:
                msg = f"Error importing action package: {str(e)}"
                log.exception(msg)
                return ActionResult.make_failure(msg).as_dict()

    def _get_connection(
        self, data_server_info: DataServerConfigTypedDict
    ) -> "DataServerConnection":
        from sema4ai_code.data.data_server_connection import DataServerConnection

        http = data_server_info["api"]["http"]
        auth = data_server_info["auth"]
        user = auth["username"]
        password = auth["password"]

        connection = DataServerConnection(
            http_url=f"http://{http['host']}:{http['port']}",
            http_user=user,
            http_password=password,
        )
        return connection

    def _drop_data_source_impl(
        self,
        datasource: DatasourceInfoTypedDict,
        data_server_info: DataServerConfigTypedDict,
        monitor: IMonitor,
    ) -> ActionResultDict:
        connection = self._get_connection(data_server_info)
        name = datasource.get("name")
        engine = datasource["engine"]
        created_table = datasource.get("created_table")
        model_name = datasource.get("model_name")

        query = ""
        if engine == "files":
            files_table_names = set(
                x["tables_in_files"]
                for x in connection.query("files", "SHOW TABLES").iter_as_dicts()
            )
            if created_table not in files_table_names:
                return ActionResult(
                    success=True,
                    message="Data source does not exist, no action needed.",
                ).as_dict()
            query = f"DROP TABLE files.{created_table}"

        elif name == "custom" and created_table:
            query = f"DROP TABLE {name}.{created_table}"

        elif engine.startswith("prediction:") or (name == "custom" and model_name):
            query = f"DROP MODEL {name}.{model_name}"
        else:
            query = f"DROP DATABASE {name}"

        try:
            connection.run_sql(query)
        except Exception as e:
            if "not exist" in str(e).lower():
                return ActionResult(
                    success=True,
                    message="Data source does not exist, no action needed.",
                ).as_dict()

            log.exception(f"Error while executing query: {query}. {str(e)}")
            return ActionResult.make_failure(
                f"Error while dropping data source: {str(e)}"
            ).as_dict()

        return ActionResult(
            success=True, message="Data Source dropped successfully."
        ).as_dict()

    def m_drop_data_source(
        self,
        datasource: DatasourceInfoTypedDict,
        data_server_info: DataServerConfigTypedDict,
    ) -> partial[ActionResultDict]:
        return require_monitor(
            partial(
                self._drop_data_source_impl,
                datasource,
                data_server_info,
            )
        )

    def m_setup_data_source(
        self,
        action_package_yaml_directory_uri: str,
        datasource: DatasourceInfoTypedDict,
        data_server_info: DataServerConfigTypedDict,
    ) -> partial[ActionResultDict[DataSourceSetupResponse]]:
        return require_monitor(
            partial(
                self._setup_data_source_impl,
                action_package_yaml_directory_uri,
                datasource,
                data_server_info,
            )
        )

    def _setup_data_source_impl(
        self,
        action_package_yaml_directory_uri: str,
        datasource: DatasourceInfoTypedDict | list[DatasourceInfoTypedDict],
        data_server_info: DataServerConfigTypedDict,
        monitor: IMonitor,
    ) -> ActionResultDict[DataSourceSetupResponse]:
        from sema4ai_ls_core.progress_report import progress_context

        from sema4ai_code.data.data_source_helper import DataSourceHelper

        with progress_context(
            self._endpoint, "Setting up data sources", self._dir_cache
        ):
            root_path = Path(uris.to_fs_path(action_package_yaml_directory_uri))
            if not root_path.exists():
                return (
                    ActionResult[DataSourceSetupResponse]
                    .make_failure(
                        f"Unable to setup data source. Root path does not exist: {root_path}"
                    )
                    .as_dict()
                )

            if not isinstance(datasource, list):
                datasources = [datasource]
            else:
                datasources = datasource

            connection = self._get_connection(data_server_info)
            messages = []
            for datasource in datasources:
                monitor.check_cancelled()
                datasource_helper = DataSourceHelper(
                    Path(uris.to_fs_path(action_package_yaml_directory_uri)),
                    datasource,
                    connection,
                )
                validation_errors = datasource_helper.get_validation_errors()
                if validation_errors:
                    return (
                        ActionResult[DataSourceSetupResponse]
                        .make_failure(
                            f"Unable to setup data source. {validation_errors[0]}"
                        )
                        .as_dict()
                    )

                if datasource["engine"] == "files":
                    created_table = datasource["created_table"]
                    relative_path = datasource["file"]

                    # These asserts should've been caught by the validation.
                    assert (
                        datasource_helper.is_table_datasource
                    ), "Expected a table datasource for the files engine."
                    assert (
                        created_table
                    ), "Expected a created_table for the files engine."
                    assert relative_path, "Expected a file for the files engine."

                    full_path = Path(root_path) / relative_path
                    if not full_path.exists():
                        return (
                            ActionResult[DataSourceSetupResponse]
                            .make_failure(
                                f"Unable to setup files engine data source. File does not exist: {full_path}"
                            )
                            .as_dict()
                        )
                    try:
                        connection.upload_file(full_path, created_table)
                    except Exception as e:
                        return (
                            ActionResult[DataSourceSetupResponse]
                            .make_failure(
                                f"Unable to upload file {full_path} to table files.{created_table}. Error: {e}"
                            )
                            .as_dict()
                        )

                    messages.append(
                        f"Uploaded file {full_path} to table {created_table}"
                    )
                    continue

                if datasource["engine"] == "custom":
                    # These asserts should've been caught by the validation.
                    assert (
                        datasource_helper.custom_sql
                    ), "Expected the sql to be defined for the custom engine."

                    for sql in datasource_helper.custom_sql:
                        try:
                            connection.run_sql(sql)
                        except Exception as e:
                            return (
                                ActionResult[DataSourceSetupResponse]
                                .make_failure(
                                    f"Unable to setup custom engine data source. Error executing SQL: {sql}. Error: {e}"
                                )
                                .as_dict()
                            )

                    messages.append(
                        f"custom engine setup: executed {len(datasource_helper.custom_sql)} SQL statements."
                    )
                    continue

                if datasource["engine"].startswith("prediction:"):
                    model_name = datasource["model_name"]
                    assert (
                        model_name
                    ), "Expected a model_name for the prediction engine."
                    assert (
                        datasource_helper.custom_sql
                    ), "Expected the setup sql to be defined for the prediction engine."

                    for sql in datasource_helper.custom_sql:
                        try:
                            connection.run_sql(sql)
                        except Exception as e:
                            return (
                                ActionResult[DataSourceSetupResponse]
                                .make_failure(
                                    f"Unable to setup prediction engine data source. Error executing SQL: {sql}. Error: {e}"
                                )
                                .as_dict()
                            )

                    messages.append(
                        f"prediction engine setup: executed {len(datasource_helper.custom_sql)} SQL statements."
                    )
                    continue

                messages.append(
                    f"Unable to setup external data source automatically (engine: {datasource['engine']}). Please use the `Sema4.ai: Add New Data Source` command to setup this data source."
                )

            return (
                ActionResult[DataSourceSetupResponse].make_success(messages).as_dict()
            )

    def m_compute_data_source_state(
        self,
        action_package_yaml_directory_uri: str,
        data_server_info: DataServerConfigTypedDict,
    ) -> partial[ActionResultDict[DataSourceStateDict]]:
        return require_monitor(
            partial(
                self._compute_data_source_state_impl,
                action_package_yaml_directory_uri,
                data_server_info,
            )
        )

    def _compute_data_source_state_impl(
        self,
        action_package_yaml_directory_uri: str,
        data_server_info: DataServerConfigTypedDict,
        monitor: IMonitor,
    ) -> ActionResultDict[DataSourceStateDict]:
        try:
            return self._impl_compute_data_source_state_impl(
                action_package_yaml_directory_uri, data_server_info, monitor
            )
        except Exception as e:
            log.exception("Error computing data source state")
            return (
                ActionResult[DataSourceStateDict]
                .make_failure(f"Error computing data source state: {e}")
                .as_dict()
            )

    def _impl_compute_data_source_state_impl(
        self,
        action_package_yaml_directory_uri: str,
        data_server_info: DataServerConfigTypedDict,
        monitor: IMonitor,
    ) -> ActionResultDict[DataSourceStateDict]:
        from sema4ai_ls_core.lsp import DiagnosticSeverity, DiagnosticsTypedDict
        from sema4ai_ls_core.progress_report import progress_context

        from sema4ai_code.data.data_source_helper import DataSourceHelper

        with progress_context(
            self._endpoint, "Computing data sources state", self._dir_cache
        ) as progress_reporter:
            progress_reporter.set_additional_info("Listing actions")
            actions_and_datasources_result: ActionResultDict[
                "list[ActionInfoTypedDict | DatasourceInfoTypedDict]"
            ] = self._local_list_actions_internal_impl(
                action_package_uri=action_package_yaml_directory_uri,
                collect_datasources=True,
            )
            if not actions_and_datasources_result["success"]:
                # Ok to cast as it's an error.
                return typing.cast(
                    ActionResultDict[DataSourceStateDict],
                    actions_and_datasources_result,
                )

            monitor.check_cancelled()
            progress_reporter.set_additional_info("Getting data sources")
            connection = self._get_connection(data_server_info)
            projects_as_dicts = connection.get_data_sources("WHERE type = 'project'")
            not_projects_as_dicts = connection.get_data_sources(
                "WHERE type != 'project'"
            )

            all_databases_as_dicts = projects_as_dicts + not_projects_as_dicts

            try:
                data_source_names_in_data_server = set(
                    x["database"].lower() for x in all_databases_as_dicts
                )
            except Exception:
                log.exception(
                    "Error getting data source names in data server. Query result: %s",
                    all_databases_as_dicts,
                )
                return (
                    ActionResult[DataSourceStateDict]
                    .make_failure("Error getting data source names in data server")
                    .as_dict()
                )

            projects_data_source_names_in_data_server = set(
                x["database"].lower() for x in projects_as_dicts
            )

            monitor.check_cancelled()
            progress_reporter.set_additional_info("Getting models")

            data_source_to_models = {}
            for data_source in projects_data_source_names_in_data_server:
                result_set_models = connection.query(
                    data_source, "SELECT * FROM models"
                )
                if result_set_models:
                    data_source_to_models[data_source] = [
                        x["name"] for x in result_set_models.iter_as_dicts()
                    ]

            monitor.check_cancelled()
            progress_reporter.set_additional_info("Getting files")

            files_table_names = set(
                x["tables_in_files"]
                for x in connection.query("files", "SHOW TABLES").iter_as_dicts()
            )

            monitor.check_cancelled()
            progress_reporter.set_additional_info("Computing data sources state")

            assert actions_and_datasources_result["result"] is not None
            actions_and_datasources: "list[ActionInfoTypedDict | DatasourceInfoTypedDict]" = actions_and_datasources_result[
                "result"
            ]
            required_data_sources: list["DatasourceInfoTypedDict"] = [
                typing.cast("DatasourceInfoTypedDict", d)
                for d in actions_and_datasources
                if d["kind"] == "datasource"
            ]

            unconfigured_data_sources: list["DatasourceInfoTypedDict"] = []
            uri_to_error_messages: dict[str, list[DiagnosticsTypedDict]] = {}
            ret: DataSourceStateDict = {
                "unconfigured_data_sources": unconfigured_data_sources,
                "uri_to_error_messages": uri_to_error_messages,
                "required_data_sources": required_data_sources,
                "data_sources_in_data_server": sorted(data_source_names_in_data_server),
            }

            if required_data_sources:
                root_path = Path(uris.to_fs_path(action_package_yaml_directory_uri))
                datasource: "DatasourceInfoTypedDict"
                for datasource in required_data_sources:
                    uri = datasource.get("uri", "<uri-missing>")
                    datasource_helper = DataSourceHelper(
                        root_path, datasource, connection
                    )
                    validation_errors = datasource_helper.get_validation_errors()
                    if validation_errors:
                        for validation_error in validation_errors:
                            uri_to_error_messages.setdefault(uri, []).append(
                                {
                                    "range": datasource["range"],
                                    "severity": DiagnosticSeverity.Error,
                                    "message": validation_error,
                                }
                            )
                        continue  # this one is invalid, so, we can't go forward.

                    datasource_name = datasource["name"]
                    datasource_engine = datasource["engine"]

                    if datasource_helper.is_table_datasource:
                        created_table = datasource["created_table"]
                        if datasource_engine == "files":
                            if created_table not in files_table_names:
                                unconfigured_data_sources.append(datasource)
                        else:
                            # Custom datasource with created_table.
                            tables_result_set = connection.query("files", "SHOW TABLES")
                            custom_table_names = set(
                                x["tables_in_files"]
                                for x in tables_result_set.iter_as_dicts()
                            )
                            if created_table not in custom_table_names:
                                unconfigured_data_sources.append(datasource)
                        continue  # Ok, handled use case.

                    if datasource_helper.is_model_datasource:
                        model_name = datasource["model_name"]
                        if model_name not in data_source_to_models.get(
                            datasource_name, []
                        ):
                            unconfigured_data_sources.append(datasource)
                        continue

                    if datasource_name.lower() not in data_source_names_in_data_server:
                        unconfigured_data_sources.append(datasource)

            return ActionResult[DataSourceStateDict].make_success(ret).as_dict()
