import os
import weakref
from typing import List, Optional

from sema4ai_ls_core.basic import overrides
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.lsp import DiagnosticsTypedDict, LSPMessages
from sema4ai_ls_core.protocols import IDocument, IEndPoint, IMonitor, IWorkspace
from sema4ai_ls_core.python_ls import BaseLintInfo, BaseLintManager

from sema4ai_code.protocols import IRcc
from sema4ai_code.robocorp_language_server import RobocorpLanguageServer
from sema4ai_code.vendored_deps.package_deps._deps_protocols import (
    ICondaCloud,
    IPyPiCloud,
)

log = get_logger(__name__)


class DiagnosticsConfig:
    analyze_versions = True
    analyze_rcc = True


def collect_package_yaml_diagnostics(
    pypi_cloud: IPyPiCloud,
    conda_cloud: ICondaCloud,
    workspace: IWorkspace,
    conda_yaml_uri: str,
    monitor: IMonitor | None,
) -> list[DiagnosticsTypedDict]:
    from sema4ai_code.vendored_deps.package_deps import analyzer

    if not DiagnosticsConfig.analyze_versions:
        return []

    doc = workspace.get_document(conda_yaml_uri, accept_from_file=True)
    if doc is None:
        return []
    if monitor:
        monitor.check_cancelled()

    return list(
        analyzer.PackageYamlAnalyzer(
            doc.source, doc.path, conda_cloud, pypi_cloud
        ).iter_package_yaml_issues()
    )


def collect_conda_yaml_diagnostics(
    pypi_cloud: IPyPiCloud,
    conda_cloud: ICondaCloud,
    workspace: IWorkspace,
    conda_yaml_uri: str,
    monitor: IMonitor | None,
) -> list[DiagnosticsTypedDict]:
    from sema4ai_code.vendored_deps.package_deps import analyzer

    if not DiagnosticsConfig.analyze_versions:
        return []

    doc = workspace.get_document(conda_yaml_uri, accept_from_file=True)
    if doc is None:
        return []
    if monitor:
        monitor.check_cancelled()
    return list(
        analyzer.CondaYamlAnalyzer(
            doc.source, doc.path, conda_cloud, pypi_cloud
        ).iter_conda_yaml_issues()
    )


def collect_rcc_configuration_diagnostics(
    rcc: IRcc, robot_yaml_fs_path
) -> list[DiagnosticsTypedDict]:
    import json

    from sema4ai_ls_core.lsp import DiagnosticSeverity

    ret: list[DiagnosticsTypedDict] = []

    if not DiagnosticsConfig.analyze_rcc:
        return ret

    action_result = rcc.configuration_diagnostics(robot_yaml_fs_path)
    if action_result.success:
        json_contents = action_result.result
        if not json_contents:
            return ret

        as_dict = json.loads(json_contents)
        checks = as_dict.get("checks", [])
        ret = []

        CategoryLockFile = 1020
        CategoryLockPid = 1021

        if isinstance(checks, (list, tuple)):
            for check in checks:
                if isinstance(check, dict):
                    status = check.get("status", "ok").lower()

                    if status != "ok":
                        if check.get("category") in (
                            CategoryLockFile,
                            CategoryLockPid,
                        ):
                            continue

                        # Default is error (for fail/fatal)
                        severity = DiagnosticSeverity.Error

                        if status in ("warn", "warning"):
                            severity = DiagnosticSeverity.Warning
                        elif status in ("info", "information"):
                            severity = DiagnosticSeverity.Information

                        # The actual line is not given by rcc, so, put
                        # all errors in the first 2 lines.
                        message = check.get("message", "<unable to get error message>")

                        url = check.get("url")
                        if url:
                            message += f" -- see: {url} for more information."
                        dct: DiagnosticsTypedDict = {
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 1, "character": 0},
                            },
                            "severity": severity,
                            "source": "sema4ai",
                            "message": message,
                        }
                        ret.append(dct)
    return ret


class _CurrLintInfo(BaseLintInfo):
    def __init__(
        self,
        weak_robocorp_language_server: "weakref.ref[RobocorpLanguageServer]",
        rcc: IRcc,
        lsp_messages: LSPMessages,
        doc_uri,
        is_saved,
        weak_lint_manager,
    ) -> None:
        self._rcc: IRcc = rcc
        self._weak_robocorp_language_server = weak_robocorp_language_server
        BaseLintInfo.__init__(self, lsp_messages, doc_uri, is_saved, weak_lint_manager)

    @staticmethod
    def _find_action_or_agent(uri: str) -> bool:
        """Checks if the given path is inside an action or agent package."""
        from pathlib import Path
        from sema4ai_ls_core import uris

        fs_path = uris.to_fs_path(uri)
        check_dir = Path(fs_path).parent

        for _ in range(6):
            package_yaml_path = check_dir / "package.yaml"
            agent_spec_yaml_path = check_dir / "agent-spec.yaml"

            if package_yaml_path.exists() or agent_spec_yaml_path.exists():
                return True

            if not check_dir.parent or check_dir.parent == check_dir:
                return False
            check_dir = check_dir.parent

        return False

    @overrides(BaseLintInfo._do_lint)
    def _do_lint(self) -> None:
        from concurrent import futures

        from sema4ai_ls_core import uris

        robocorp_language_server = self._weak_robocorp_language_server()
        if robocorp_language_server is None:
            return

        is_saved = self.is_saved
        doc_uri = self.doc_uri

        if doc_uri.endswith(".py"):
            ws: IWorkspace | None = robocorp_language_server.workspace
            if not ws:
                return

            doc: IDocument | None = ws.get_document(doc_uri, accept_from_file=True)
            errors = []

            if doc is not None:
                source = doc.source
                ruff_future = None
                if self._find_action_or_agent(doc_uri):
                    from sema4ai_code.robo.lint_ruff import collect_ruff_errors
                    from sema4ai.common.run_in_thread import run_in_thread

                    ruff_future = run_in_thread(lambda: collect_ruff_errors(doc))

                if "@action" in source:
                    from sema4ai_code.robo.lint_action import collect_lint_errors

                    errors = collect_lint_errors(robocorp_language_server.pm, doc)

                if ruff_future:
                    errors.extend(ruff_future.result())

                self._lsp_messages.publish_diagnostics(doc_uri, errors)
            return

        if doc_uri.endswith("package.yaml"):
            found = []
            if robocorp_language_server is not None:
                ws = robocorp_language_server.workspace
                if ws is not None:
                    found.extend(
                        collect_package_yaml_diagnostics(
                            robocorp_language_server.pypi_cloud,
                            robocorp_language_server.conda_cloud,
                            ws,
                            doc_uri,
                            self._monitor,
                        )
                    )

            self._lsp_messages.publish_diagnostics(doc_uri, found)
            return

        if doc_uri.endswith("agent-spec.yaml"):
            found = []
            if robocorp_language_server is not None:
                ws = robocorp_language_server.workspace
                if ws is not None:
                    from sema4ai_code.agents.collect_agent_spec_diagnostics import (
                        collect_agent_spec_diagnostics,
                    )

                    found.extend(
                        collect_agent_spec_diagnostics(
                            ws,
                            doc_uri,
                            self._monitor,
                        )
                    )

            self._lsp_messages.publish_diagnostics(doc_uri, found)
            return

        if doc_uri.endswith(("conda.yaml", "action-server.yaml")) or doc_uri.endswith(
            "robot.yaml"
        ):
            robot_yaml_fs_path = uris.to_fs_path(doc_uri)
            if robot_yaml_fs_path.endswith(("conda.yaml", "action-server.yaml")):
                p = os.path.dirname(robot_yaml_fs_path)
                for _ in range(3):
                    target = os.path.join(p, "robot.yaml")
                    if target and os.path.exists(target):
                        robot_yaml_fs_path = target
                        break
                else:
                    # We didn't find the 'robot.yaml' for the 'conda.yaml'
                    # bail out.
                    return

            # Get the executor service from the endpoint
            endpoint = self._lsp_messages.endpoint

            # When a document is saved, if it's a conda.yaml or a robot.yaml,
            # validate it with RCC.
            if is_saved:
                executor_service: futures.ThreadPoolExecutor = getattr(
                    endpoint, "executor_service"
                )

                future_diagnostics = executor_service.submit(
                    collect_rcc_configuration_diagnostics,
                    self._rcc,
                    robot_yaml_fs_path,
                )

            found = []
            # Ok, we started collecting RCC diagnostics in a thread. We
            # can now also collect other diagnostics here.
            if doc_uri.endswith(("conda.yaml", "action-server.yaml")):
                if robocorp_language_server is not None:
                    ws = robocorp_language_server.workspace
                    if ws is not None:
                        found.extend(
                            collect_conda_yaml_diagnostics(
                                robocorp_language_server.pypi_cloud,
                                robocorp_language_server.conda_cloud,
                                ws,
                                doc_uri,
                                self._monitor,
                            )
                        )

            if is_saved:
                found.extend(future_diagnostics.result())

            self._lsp_messages.publish_diagnostics(doc_uri, found)


class LintManager(BaseLintManager):
    def __init__(
        self,
        robocorp_language_server: RobocorpLanguageServer,
        rcc: IRcc,
        lsp_messages,
        endpoint: IEndPoint,
        read_queue,
    ) -> None:
        self._rcc: IRcc = rcc
        self._weak_robocorp_language_server = weakref.ref(robocorp_language_server)
        BaseLintManager.__init__(self, lsp_messages, endpoint, read_queue)

    @overrides(BaseLintManager._create_curr_lint_info)
    def _create_curr_lint_info(
        self, doc_uri: str, is_saved: bool, timeout: float
    ) -> BaseLintInfo | None:
        # Note: this call must be done in the main thread.
        weak_lint_manager = weakref.ref(self)

        log.debug("Schedule lint for: %s", doc_uri)
        curr_info = _CurrLintInfo(
            self._weak_robocorp_language_server,
            self._rcc,
            self._lsp_messages,
            doc_uri,
            is_saved,
            weak_lint_manager,
        )
        return curr_info
