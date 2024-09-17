import pathlib
import typing
from dataclasses import dataclass
from typing import Optional, Union
from collections.abc import Iterator

from sema4ai_ls_core.lsp import DiagnosticSeverity, DiagnosticsTypedDict
from sema4ai_ls_core.protocols import IDocument, IMonitor, IWorkspace, Sentinel

if typing.TYPE_CHECKING:
    from sema4ai_code.vendored_deps.yaml_with_location import str_with_location


class RequiredValidationFailedError(RuntimeError):
    pass


class _Node:
    def __init__(self):
        pass


class _EntryNode(_Node):
    def __init__(self, key: "str_with_location", value):
        self.key = key
        self.value: object = value


class _ErrorNode(_Node):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic


def _get_node(data, key: str, msg: str) -> _EntryNode | _ErrorNode:
    from sema4ai_code.vendored_deps.yaml_with_location import (
        create_range_from_location,
        dict_with_location,
        str_with_location_capture,
    )

    report_location: tuple | None = None
    diagnostic: DiagnosticsTypedDict

    if isinstance(data, _EntryNode):
        report_location = data.key.location
        data = data.value

    if isinstance(data, dict_with_location) and data.location:
        report_location = data.location[:2]  # just start line/col for this report

    report_location = report_location or (0, 0)

    if not isinstance(data, dict):
        diagnostic = {
            "range": create_range_from_location(*report_location),
            "severity": DiagnosticSeverity.Error,
            "source": "sema4ai",
            "message": msg,
        }
        return _ErrorNode(diagnostic)

    use_key = str_with_location_capture(key)
    ret = data.get(use_key, Sentinel.SENTINEL)
    if ret != Sentinel.SENTINEL:
        return _EntryNode(use_key, ret)

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
        self._yaml_data: dict | None = None

    def _load_yaml(self) -> None:
        from yaml.error import MarkedYAMLError

        from sema4ai_code.vendored_deps.yaml_with_location import (
            LoaderWithLines,
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
                diagnostic = {
                    "range": create_range_from_location(0, 0),
                    "severity": DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Error: expected dict to be root of yaml (found: {data})",
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
            data, "agent-package", "'agent-package' not found in yaml root."
        )
        if isinstance(agent_package, _ErrorNode):
            yield agent_package.diagnostic
            return

        spec_version = _get_node(
            agent_package,
            "spec-version",
            "'spec-version' not found in 'agent-package'",
        )
        if isinstance(spec_version, _ErrorNode):
            yield spec_version.diagnostic
            return

        version_value = _get_scalar_value_str(spec_version.value)
        yield from validate(
            version_value,
            spec_version,
            "Expected spec-version to be a string (something as `v1`, `v2`, ...).",
            required=True,
        )

        yield from validate(
            version_value.startswith("v"),
            spec_version,
            "Expected spec-version to be a string starting with `v`.",
            required=True,
        )

        is_v1 = version_value == "v1"
        is_v2 = version_value == "v2"
        yield from validate(
            is_v1 or is_v2,
            spec_version,
            "Unexpected spec-version (only `v1` and `v2` are currently supported).",
            required=True,
        )

        # For now no need to check version for further checks, but in the future
        # some logic will be needed here as checks may depend on the actual version.
        agents_node = _get_node(
            agent_package,
            "agents",
            "No 'agents' section defined under 'agent-package'.",
        )
        if isinstance(agents_node, _ErrorNode):
            yield agents_node.diagnostic
            return

        yield from validate(
            isinstance(agents_node.value, list),
            agents_node.key,
            "'agents' is expected to be a list.",
            required=True,
        )

        yield from validate(
            bool(agents_node.value),
            agents_node.key,
            "No 'agents' defined.",
            # Warning because that's a valid file, just not really useful...
            severity=DiagnosticSeverity.Warning,
            required=True,
        )

        # isinstance to make type-checker happy (we validated that already).
        assert isinstance(agents_node.value, list)
        for agent in agents_node.value:
            yield from validate_agent(
                self.doc, agent, _Version(is_v1=is_v1, is_v2=is_v2)
            )


@dataclass
class _Version:
    is_v1: bool
    is_v2: bool


def validate_agent(
    doc: IDocument, agent_node: _EntryNode, version: _Version
) -> Iterator[DiagnosticsTypedDict]:
    from sema4ai_code.agents.agent_spec import AGENT_SPEC_V2
    from sema4ai_code.agents.agent_spec_handler import Error, validate_from_spec

    if version.is_v1:
        yield from validate_sections_v1(
            agent_node,
            {
                "name": str,
                "description": str,
                "type": ("agent", "chat_plan_execute"),
                "reasoningLevel": (0, 1, 2, 3),
            },
        )
    elif version.is_v2:
        error: Error
        for error in validate_from_spec(
            AGENT_SPEC_V2,
            doc.source,
            pathlib.Path(doc.path).parent,
            raise_on_error=False,
        ):
            yield typing.cast(DiagnosticsTypedDict, error.as_diagostic(agent_node))

    else:
        raise AssertionError(f"Unexpected version: {version}")


def validate_sections_v1(
    node: _EntryNode, spec: dict[str, type[str] | tuple]
) -> Iterator[DiagnosticsTypedDict]:
    for k, v in spec.items():
        child = _get_node(node, k, f"'{k}' section not found.")
        if isinstance(child, _ErrorNode):
            yield child.diagnostic
        else:
            if v == str:
                yield from validate(
                    isinstance(child.value, str),
                    child,
                    f"Expected {child.key} to be a string.",
                    required=False,
                )

            elif isinstance(v, tuple):
                valid = "', '".join(str(x) for x in v)
                yield from validate(
                    child.value in v,
                    child,
                    f"Expected {child.key} to be one of: '{valid}'.",
                    required=False,
                )
            else:
                raise AssertionError(f"Bad node specification: {v}")


def validate(
    condition: bool,
    scalar: Union["str_with_location", _EntryNode],
    msg: str,
    *,
    required: bool,
    severity=DiagnosticSeverity.Error,
) -> Iterator[DiagnosticsTypedDict]:
    from sema4ai_code.vendored_deps.yaml_with_location import create_range_from_location

    diagnostic: DiagnosticsTypedDict
    if not condition:
        use_location = None

        check_order: tuple[object, ...]

        if isinstance(scalar, _EntryNode):
            # Try to use value first
            check_order = (scalar.value, scalar.key)
        else:
            check_order = (scalar,)

        for check in check_order:
            location = getattr(check, "location", None)
            if location and isinstance(location, (tuple, list)) and len(location) == 4:
                use_location = location
                break
        else:
            use_location = (0, 0, 1, 0)

        start_line, start_col, end_line, end_col = use_location
        use_range = create_range_from_location(start_line, start_col, end_line, end_col)

        diagnostic = {
            "range": use_range,
            "severity": severity,
            "source": "sema4ai",
            "message": msg,
        }
        yield diagnostic
        if required:
            raise RequiredValidationFailedError()


def _get_scalar_value_str(v):
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
    try:
        yield from analyzer.iter_issues()
    except RequiredValidationFailedError:
        # Just ignore this one (the error should've been yielded and the exception
        # is just a marker to stop trying to check further issues).
        pass
