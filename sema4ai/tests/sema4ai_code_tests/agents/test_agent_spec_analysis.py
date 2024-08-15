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


def ok(agent_path):
    pass


@pytest.mark.parametrize(
    "scenario", [no_spec_version, bad_spec_version, ok, bad_format]
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
