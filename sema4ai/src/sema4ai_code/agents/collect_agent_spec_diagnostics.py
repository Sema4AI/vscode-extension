import pathlib
import typing
from typing import Iterator, Optional

from sema4ai_ls_core.lsp import DiagnosticSeverity, DiagnosticsTypedDict
from sema4ai_ls_core.protocols import IDocument, IMonitor, IWorkspace, Sentinel

if typing.TYPE_CHECKING:
    from sema4ai_code.vendored_deps.yaml_with_location import ScalarInfo


class _Node:
    def __init__(self):
        pass


class _EntryNode(_Node):
    def __init__(self, key: "ScalarInfo", value):
        self.key = key
        self.value = value


class _ErrorNode(_Node):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic


def _get_node(
    data, key: str, msg: str, require_key_scalar_info: bool = True
) -> _EntryNode | _ErrorNode:
    from sema4ai_code.vendored_deps.yaml_with_location import (
        ScalarInfo,
        create_range_from_location,
    )

    report_location: Optional[tuple] = None
    diagnostic: DiagnosticsTypedDict

    if isinstance(data, _EntryNode):
        report_location = data.key.location
        data = data.value

    report_location = report_location or (0, 0)

    if not isinstance(data, dict):
        diagnostic = {
            "range": create_range_from_location(0, 0),
            "severity": DiagnosticSeverity.Error,
            "source": "sema4ai",
            "message": msg,
        }
        return _ErrorNode(diagnostic)

    if not require_key_scalar_info:
        use_key = ScalarInfo(key, None)
        ret = data.get(use_key, Sentinel.SENTINEL)
        if ret != Sentinel.SENTINEL:
            return _EntryNode(use_key, ret)
    else:
        for k, v in data.items():
            # We do a (slow) search because we want the key as a ScalarInfo
            # (for the position). We could pre-index so that it wasn't so
            # slow, but I don't think it matters until we start to have
            # really big `agent-spec.yaml` contents (which is not expected
            # at this point).
            #
            # If the key position won't be used, `require_key_scalar_info`
            # should be passed as False.
            if isinstance(k, ScalarInfo):
                if k.scalar == key:
                    return _EntryNode(k, v)

    diagnostic = {
        "range": create_range_from_location(*report_location),
        "severity": DiagnosticSeverity.Error,
        "source": "sema4ai",
        "message": msg,
    }
    return _ErrorNode(diagnostic)


class _Analyzer:
    def __init__(self, workspace: IWorkspace, doc: IDocument, monitor: IMonitor):
        self.workspace = workspace
        self.doc = doc
        self.monitor = monitor

        self._load_errors: list[DiagnosticsTypedDict] = []
        self._loaded_yaml = False
        self._yaml_data: Optional[dict] = None

    def _load_yaml(self) -> None:
        from yaml.error import MarkedYAMLError

        from sema4ai_code.vendored_deps.yaml_with_location import (
            LoaderWithLines,
            ScalarInfo,
            create_range_from_location,
        )

        if self._loaded_yaml:
            return
        self._loaded_yaml = True

        diagnostic: DiagnosticsTypedDict

        try:
            contents = self.doc.source
            loader = LoaderWithLines(contents)
            path: pathlib.Path = pathlib.Path(self.doc.path)

            loader.name = f".../{path.parent.name}/{path.name}"
            data = loader.get_single_data()
            if isinstance(data, dict):
                self._yaml_data = data
            else:
                if isinstance(data, ScalarInfo):
                    diagnostic = {
                        "range": create_range_from_location(0, 0),
                        "severity": DiagnosticSeverity.Error,
                        "source": "sema4ai",
                        "message": f"Error: expected dict to be root of yaml (found: {type(data.scalar)})",
                    }
                else:
                    diagnostic = {
                        "range": create_range_from_location(0, 0),
                        "severity": DiagnosticSeverity.Error,
                        "source": "sema4ai",
                        "message": f"Error: expected dict to be root of yaml (found: {type(data)})",
                    }
                self._load_errors.append(diagnostic)

        except MarkedYAMLError as e:
            if e.problem_mark:
                diagnostic = {
                    "range": create_range_from_location(
                        e.problem_mark.line, e.problem_mark.column
                    ),
                    "severity": DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Syntax error: {e}",
                }
                self._load_errors.append(diagnostic)

    def iter_issues(self) -> Iterator[DiagnosticsTypedDict]:
        self._load_yaml()

        if self._load_errors:
            yield from iter(self._load_errors)
            return

        data = self._yaml_data
        if not data:
            return

        agent_package = _get_node(
            data, "agent-package", "Error: 'agent-package' not found in yaml root."
        )
        if isinstance(agent_package, _ErrorNode):
            yield agent_package.diagnostic
            return

        spec_version = _get_node(
            agent_package,
            "spec-version",
            "Error: 'spec-version' not found in 'agent-package'",
        )
        if isinstance(spec_version, _ErrorNode):
            yield spec_version.diagnostic
            return

        diagnostic: DiagnosticsTypedDict

        version_value = _get_scalar_value_str(spec_version.value)
        if not version_value:
            diagnostic = {
                "range": spec_version.key.as_range(),
                "severity": DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: expected spec-version to be a string (something as `v1`, `v2`, ...).",
            }
            yield diagnostic
            return

        if not version_value.startswith("v"):
            diagnostic = {
                "range": spec_version.value.as_range(),
                "severity": DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: expected spec-version to be a string starting with `v`.",
            }
            yield diagnostic
            return

        if version_value not in ("v1",):
            diagnostic = {
                "range": spec_version.value.as_range(),
                "severity": DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: unexpected spec-version (only `v1` is currently supported).",
            }
            yield diagnostic
            return


def _get_scalar_value_str(v):
    from sema4ai_code.vendored_deps.yaml_with_location import ScalarInfo

    if isinstance(v, ScalarInfo) and isinstance(v.scalar, str):
        return v.scalar
    if isinstance(v, str):
        return v
    return None


def collect_agent_spec_diagnostics(
    workspace: IWorkspace, agent_spec_uri: str, monitor: IMonitor
):
    doc = workspace.get_document(agent_spec_uri, accept_from_file=True)
    if doc is None:
        return []
    if monitor:
        monitor.check_cancelled()

    analyzer = _Analyzer(workspace, doc, monitor)
    yield from analyzer.iter_issues()
