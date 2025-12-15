from pathlib import Path

import pytest


def bad_format(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    agent_spec.write_text(
        """
agent-package:
  spec-version: v1
  agents
"""
    )


def no_spec_version(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(txt.replace("spec-version: v1", ""))


def bad_spec_version(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(txt.replace("spec-version: v1", "spec-version: 22"))


def v2_new_architecture(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(
        txt.replace("architecture: plan_execute", "architecture: new_enum_value")
    )


def ok(agent_path):
    pass


def no_agents_section(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(txt.replace("agents:", "no-agents:"))


def empty_agents(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(txt.replace("agents:", "agents: []\n  no-agents:"))


def bad_agent_items(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(
        txt.replace("name: New Agent", "name: 1")
        .replace("description: Agent description", "")
        .replace("type: agent", "type: foobar")
        .replace("reasoningLevel: 0", "reasoningLevel: 22")
    )


def v2_bad_type(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    update(agent_spec, lambda txt: txt.replace("type: zip", "type: folder"))


def v2_bad_action_package_version(agent_path):
    package_yaml = (
        agent_path
        / "actions"
        / "MyActions"
        / "control-room-test"
        / "0.0.1"
        / "package.yaml"
    )
    txt = package_yaml.read_text()
    package_yaml.write_text(txt.replace("version: 0.0.1", "version: 1.1.1"))


def update(package_yaml, replace_func):
    txt = package_yaml.read_text()
    new = replace_func(txt)
    assert txt != new
    package_yaml.write_text(new)


def v2_bad_action_package_name(agent_path):
    package_yaml = agent_path / "agent-spec.yaml"

    update(
        package_yaml,
        lambda txt: txt.replace("name: Control Room Test", "name: Some other name"),
    )


def v2_bad_mcp_transport(agent_path):
    package_yaml = agent_path / "agent-spec.yaml"

    update(
        package_yaml,
        lambda txt: txt.replace(
            "transport: streamable-http", "transport: bad-transport"
        ),
    )


def v2_document_intelligence_v2(agent_path):
    """Test that document-intelligence: v2 is valid."""
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    # Add document-intelligence: v2 after reasoning line
    agent_spec.write_text(
        txt.replace("reasoning: enabled", "reasoning: enabled\n      document-intelligence: v2")
    )


def v2_document_intelligence_v2_1(agent_path):
    """Test that document-intelligence: v2.1 is valid."""
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    # Add document-intelligence: v2.1 after reasoning line
    agent_spec.write_text(
        txt.replace("reasoning: enabled", "reasoning: enabled\n      document-intelligence: v2.1")
    )


def v2_document_intelligence_invalid(agent_path):
    """Test that document-intelligence with invalid value is rejected."""
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    # Add invalid document-intelligence value after reasoning line
    agent_spec.write_text(
        txt.replace("reasoning: enabled", "reasoning: enabled\n      document-intelligence: v3")
    )


def v2_unreferenced_action_package(agent_path):
    import shutil

    zip_path = (
        agent_path
        / "actions"
        / "MyActions"
        / "control-room-test"
        / "0.0.1"
        / "0.0.1.zip"
    )
    new_zip_path = (
        agent_path
        / "actions"
        / "MyActions"
        / "control-room-test"
        / "0.0.1"
        / "new-path.zip"
    )
    shutil.move(zip_path, new_zip_path)


def check(agent_name: str, datadir, scenario, data_regression) -> None:
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.jsonrpc.monitor import Monitor
    from sema4ai_ls_core.watchdog_wrapper import create_observer
    from sema4ai_ls_core.workspace import Workspace

    from sema4ai_code.agents.collect_agent_spec_diagnostics import (
        collect_agent_spec_diagnostics,
    )

    agent1 = Path(datadir) / agent_name

    scenario(agent1)

    workspace = Workspace(
        uris.from_fs_path(str(agent1)), create_observer("dummy", None)
    )
    monitor = Monitor()
    found = list(
        collect_agent_spec_diagnostics(
            workspace, uris.from_fs_path(str(agent1 / "agent-spec.yaml")), monitor
        )
    )

    data_regression.check(found)


@pytest.mark.parametrize(
    "scenario",
    [
        bad_spec_version,
        no_spec_version,
        ok,
        bad_format,
        no_agents_section,
        empty_agents,
        bad_agent_items,
    ],
)
def test_agent_spec_analysis(datadir, scenario, data_regression) -> None:
    check("agent1", datadir, scenario, data_regression)


@pytest.mark.parametrize(
    "scenario",
    [
        ok,
        v2_new_architecture,
        v2_bad_action_package_version,
        v2_bad_action_package_name,
    ],
)
def test_agent_spec_analysis_v2(datadir, scenario, data_regression) -> None:
    check("agent2", datadir, scenario, data_regression)


@pytest.mark.parametrize(
    "scenario",
    [ok, v2_bad_type, v2_bad_action_package_name, v2_unreferenced_action_package],
)
def test_agent_spec_analysis_v2_agent3(datadir, scenario, data_regression) -> None:
    check("agent3", datadir, scenario, data_regression)


@pytest.mark.parametrize(
    "scenario",
    [ok, v2_bad_mcp_transport],
)
def test_agent_spec_analysis_21_agent4(datadir, scenario, data_regression) -> None:
    check("agent4", datadir, scenario, data_regression)


@pytest.mark.parametrize(
    "scenario",
    [
        v2_document_intelligence_v2,
        v2_document_intelligence_v2_1,
        v2_document_intelligence_invalid,
    ],
)
def test_agent_spec_document_intelligence(datadir, scenario, data_regression) -> None:
    """Test document-intelligence field validation with v2, v2.1, and invalid values."""
    check("agent4", datadir, scenario, data_regression)
