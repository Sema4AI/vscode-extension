import json

from .agent_spec_handler import Entry, load_spec

AGENT_SPEC_V2: dict[str, Entry] = load_spec(
    json.loads(
        r"""{
  "agent-package": {
    "description": "Root element for the agent spec",
    "required": true,
    "expected-type": "object"
  },
  "agent-package/spec-version": {
    "description": "The version of the spec being used. Example: \"v2\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents": {
    "description": "Defines the agents in the package (note: only a single agent is expected to be defined)",
    "required": true,
    "expected-type": "list"
  },
  "agent-package/agents/name": {
    "description": "The name of the agent. Example: \"My Agent\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/description": {
    "description": "Description for the agent. Example: \"My smart agent that does what I want\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/model": {
    "description": "Section to describe the LLM used by the agent",
    "required": true,
    "expected-type": "object"
  },
  "agent-package/agents/model/provider": {
    "description": "The LLM Provider.",
    "required": true,
    "expected-type": {
      "type": "string",
      "recommended-values": [
        "OpenAI",
        "Azure",
        "Anthropic",
        "Google",
        "Amazon",
        "Ollama"
      ]
    }
  },
  "agent-package/agents/model/name": {
    "description": "The LLM model name to be used.",
    "required": true,
    "expected-type": {
      "type": "string",
      "recommended-values": [
        "gpt-3.5-turbo",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4",
        "llama3"
      ]
    }
  },
  "agent-package/agents/version": {
    "description": "Version of the Agent Package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/architecture": {
    "description": "The agent type. Accepted values are: \"agent\", \"plan_execute\". \"agent\" means using chat + RAG + tools, \"plan_execute\" means chat + RAG + Tools with the ability to plan/replan its approach to coming up with an answer to a user's question/prompt.",
    "required": true,
    "expected-type": {
      "type": "enum",
      "values": ["agent", "plan_execute"]
    }
  },
  "agent-package/agents/reasoning": {
    "description": "The reasoning level for the agent. Accepted values: \"disabled\", \"enabled\", \"verbose\"",
    "required": true,
    "expected-type": {
      "type": "enum",
      "values": ["disabled", "enabled", "verbose"]
    }
  },
  "agent-package/agents/runbook": {
    "description": "The runbook is used to build the prompt passed to the agent to define its behavior. Relative path (right next to the `agent-spec.yaml`) for the file to be used for the runbook. A markdown formatted file is expected.",
    "required": true,
    "expected-type": {
      "type": "file",
      "relative-to": "./"
    }
  },
  "agent-package/agents/action-packages": {
    "description": "Section with the action packages that the agent can use.",
    "required": true,
    "expected-type": "list"
  },
  "agent-package/agents/action-packages/name": {
    "description": "The name of the action package. Example: \"my-action-package\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/organization": {
    "description": "The organization that provided the action. Example: \"MyActions\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/type": {
    "description": "The type of the action package distribution. Accepted values are \"zip\" and \"folder\"",
    "required": true,
    "expected-type": {
      "type": "enum",
      "values": ["zip", "folder"]
    }
  },
  "agent-package/agents/action-packages/version": {
    "description": "Version of the action package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/whitelist": {
    "description": "Whitelist of actions (comma-separated string) accepted in the action package. An empty string value for whitelist implies usage of all actions. Example: action1, action2",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/path": {
    "description": "Relative path under \"actions\" to access the action package folder or zip. Example: \"MyActions/my-action-package\" or \"Sema4.ai/free-web-search/1.0.0.zip\"",
    "required": true,
    "expected-type": {
      "type": "file",
      "relative-to": "/actions"
    }
  },
  "agent-package/agents/knowledge": {
    "description": "Section to indicate additional knowledge files for the agent or actions.",
    "required": false,
    "expected-type": "list"
  },
  "agent-package/agents/knowledge/name": {
    "description": "Relative path under \"knowledge\" for the related knowledge file.",
    "required": true,
    "expected-type": {
      "type": "file",
      "relative-to": "./knowledge"
    }
  },
  "agent-package/agents/knowledge/embedded": {
    "description": "Setting embedded to true means that the file is vectorized and embedded into the context. False means that the file is not used in the context, but can be uploaded for use in actions.",
    "required": true,
    "expected-type": "bool"
  },
  "agent-package/agents/knowledge/digest": {
    "description": "SHA-256 hex string for the knowledge file content. Should not be specified while developing, but when a package is built for distribution, tooling should generate this.",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/metadata": {
    "description": "Metadata on how to run the agent",
    "required": true,
    "expected-type": "object"
  },
  "agent-package/agents/metadata/mode": {
    "description": "Mode of worker allowed values: \"conversational\" | \"worker\"",
    "required": true,
    "expected-type": {
      "type": "enum",
      "values": ["conversational", "worker"]
    }
  },
  "agent-package/agents/metadata/worker-config": {
    "description": "Configuration for the worker (only required if 'mode' is worker)",
    "required": false,
    "expected-type": "object"
  },
  "agent-package/agents/metadata/worker-config/type": {
    "description": "Worker type (required if 'worker-config' is specified)",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/metadata/worker-config/document-type": {
    "description": "Document type (required if 'worker-config' is specified)",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/resources": {
    "description": "Please use 'knowledge' instead",
    "deprecated": true
  },
  "agent-package/agents/type": {
    "description": "Please use 'architecture' instead",
    "deprecated": true
  },
  "agent-package/agents/reasoningLevel": {
    "description": "Please use 'reasoning' instead",
    "deprecated": true
  },
  "agent-package/agents/runbooks": {
    "description": "Please use 'runbook' instead",
    "deprecated": true
  }
}
"""
    )
)
