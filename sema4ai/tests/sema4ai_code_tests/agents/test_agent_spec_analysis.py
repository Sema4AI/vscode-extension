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


def v2_bad_architecture(agent_path):
    agent_spec = agent_path / "agent-spec.yaml"
    txt = agent_spec.read_text()
    agent_spec.write_text(
        txt.replace("architecture: plan_execute", "architecture: bad-architecture")
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
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.jsonrpc.monitor import Monitor
    from sema4ai_ls_core.watchdog_wrapper import create_observer
    from sema4ai_ls_core.workspace import Workspace

    from sema4ai_code.agents.collect_agent_spec_diagnostics import (
        collect_agent_spec_diagnostics,
    )

    agent1 = Path(datadir) / "agent1"

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
    [ok, v2_bad_architecture],
)
def test_agent_spec_analysis_v2(datadir, scenario, data_regression) -> None:
    from sema4ai_ls_core import uris
    from sema4ai_ls_core.jsonrpc.monitor import Monitor
    from sema4ai_ls_core.watchdog_wrapper import create_observer
    from sema4ai_ls_core.workspace import Workspace

    from sema4ai_code.agents.collect_agent_spec_diagnostics import (
        collect_agent_spec_diagnostics,
    )

    agent1 = Path(datadir) / "agent2"

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
