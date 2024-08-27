def test_hover_on_agent_spec_v1(data_regression):
    from sema4ai_ls_core.jsonrpc.monitor import Monitor
    from sema4ai_ls_core.workspace import Document

    from sema4ai_code.agents.hover_agent_spec import hover_on_agent_spec_yaml

    content = """agent-package:
  spec-version: v1
  agents:
  - name: New Agent
    description: Agent description
    model: GPT 4 Turbo
    type: agent
    reasoningLevel: 0
    runbooks:
      system: system.md
      retrieval: retrieval.md
    action-packages: []
    resources: []
"""

    doc = Document("uri", content)
    monitor = Monitor()
    result = hover_on_agent_spec_yaml(doc, 1, 4, monitor)  # Not really available for v1
    data_regression.check(result)


def test_hover_on_agent_spec_v2(data_regression):
    from sema4ai_ls_core.jsonrpc.monitor import Monitor
    from sema4ai_ls_core.workspace import Document

    from sema4ai_code.agents.hover_agent_spec import hover_on_agent_spec_yaml

    content = """agent-package:
  spec-version: v2
  agents:
  - name: New Agent
    description: Agent description
    model: GPT 4 Turbo
    type: agent
    reasoningLevel: 0
    runbooks:
      system: system.md
      retrieval: retrieval.md
    action-packages: []
    resources: []
"""

    doc = Document("uri", content)
    monitor = Monitor()
    result = hover_on_agent_spec_yaml(doc, 1, 4, monitor)
    data_regression.check(result)
