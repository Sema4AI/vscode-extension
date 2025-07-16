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
  "agent-package/exclude": {
    "description": "List of files to exclude from the agent package. Example: [\"*.zip\", \"*.pyc\"]",
    "required": false,
    "expected-type": "list"
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
      "recommended-values": ["OpenAI", "Azure", "Anthropic", "Google", "Amazon", "Ollama"]
    }
  },
  "agent-package/agents/model/name": {
    "description": "The LLM model name to be used.",
    "required": true,
    "expected-type": {
      "type": "string",
      "recommended-values": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o", "gpt-4", "llama3"]
    }
  },
  "agent-package/agents/version": {
    "description": "Version of the Agent Package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "agent_semver_version"
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
    "expected-type": "action_package_name_link"
  },
  "agent-package/agents/action-packages/organization": {
    "description": "The organization that provided the action. Example: \"MyActions\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/type": {
    "description": "The type of the action package distribution. Accepted values are \"zip\" and \"folder\". Note that \"zip\" is only supported when the agent is packaged for distribution.",
    "required": true,
    "expected-type": {
      "type": "zip_or_folder_based_on_path",
      "values": ["zip", "folder"]
    }
  },
  "agent-package/agents/action-packages/version": {
    "description": "Version of the action package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "action_package_version_link"
  },
  "agent-package/agents/action-packages/whitelist": {
    "description": "Whitelist of actions (comma-separated string) accepted in the action package. An empty string value for whitelist implies usage of all actions. Example: action1, action2",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/path": {
    "description": "Relative path under \"actions\" to access the action package folder or zip. Example: \"MyActions/my-action-package\" or \"Sema4.ai/free-web-search/1.0.0.zip\". Note that \"zips\" are only supported when the agent is packaged for distribution.",
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

AGENT_SPEC_V3: dict[str, Entry] = load_spec(
    json.loads(r"""{
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
  "agent-package/exclude": {
    "description": "List of files to exclude from the agent package. Example: [\"*.zip\", \"*.pyc\"]",
    "required": false,
    "expected-type": "list"
  },
  "agent-package/variables": {
    "description": "Variables that can be used in mcp-server header values and env values.",
    "required": false,
    "expected-type": "list",
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/name": {
    "description": "The name of the variable. Example: \"api-key\"",
    "required": true,
    "expected-type": "string",
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/type": {
    "description": "The type of the variable. Accepted values: \"secret\", \"oauth2-secret\", \"string\"",
    "required": true,
    "expected-type": {
      "type": "enum",
      "values": ["secret", "oauth2-secret", "string"]
    },
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/description": {
    "description": "Optional: human-readable description of the variable.",
    "required": false,
    "expected-type": "string",
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/provider": {
    "description": "OAuth2 provider name (only required for oauth2-secret type). Example: \"Microsoft\"",
    "required": false,
    "expected-type": "string",
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/scopes": {
    "description": "OAuth2 scopes (only required for oauth2-secret type). Example: [\"user.read\", \"user.write\"]",
    "required": false,
    "expected-type": "list",
    "note": "Variables are in the spec are NOT meant to be used currently!"
  },
  "agent-package/variables/default": {
    "description": "Default value for the variable (only for string type).",
    "required": false,
    "expected-type": "string",
    "note": "Variables are in the spec are NOT meant to be used currently!"
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
      "recommended-values": ["OpenAI", "Azure", "Anthropic", "Google", "Amazon", "Ollama"]
    }
  },
  "agent-package/agents/model/name": {
    "description": "The LLM model name to be used.",
    "required": true,
    "expected-type": {
      "type": "string",
      "recommended-values": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o", "gpt-4", "llama3"]
    }
  },
  "agent-package/agents/version": {
    "description": "Version of the Agent Package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "agent_semver_version"
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
    "expected-type": "action_package_name_link"
  },
  "agent-package/agents/action-packages/organization": {
    "description": "The organization that provided the action. Example: \"MyActions\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/type": {
    "description": "The type of the action package distribution. Accepted values are \"zip\" and \"folder\". Note that \"zip\" is only supported when the agent is packaged for distribution.",
    "required": true,
    "expected-type": {
      "type": "zip_or_folder_based_on_path",
      "values": ["zip", "folder"]
    }
  },
  "agent-package/agents/action-packages/version": {
    "description": "Version of the action package. Example: \"1.3.0\"",
    "required": true,
    "expected-type": "action_package_version_link"
  },
  "agent-package/agents/action-packages/whitelist": {
    "description": "Whitelist of actions (comma-separated string) accepted in the action package. An empty string value for whitelist implies usage of all actions. Example: action1, action2",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/action-packages/path": {
    "description": "Relative path under \"actions\" to access the action package folder or zip. Example: \"MyActions/my-action-package\" or \"Sema4.ai/free-web-search/1.0.0.zip\". Note that \"zips\" are only supported when the agent is packaged for distribution.",
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
  "agent-package/agents/mcp-servers": {
    "description": "Section to define MCP (Model Context Protocol) servers that the agent can connect to.",
    "required": false,
    "expected-type": "list"
  },
  "agent-package/agents/mcp-servers/name": {
    "description": "The name of the MCP server. Example: \"my-server\"",
    "required": true,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/transport": {
    "description": "The transport to use for the MCP server connection. Accepted values: \"streamable-http\", \"sse\", \"stdio\"",
    "required": false,
    "expected-type": "mcp_server_transport"
  },
  "agent-package/agents/mcp-servers/description": {
    "description": "Description of the MCP server and configuration instructions.",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/url": {
    "description": "URL for the MCP server (only for streamable-http and sse kinds). Example: \"http://localhost:8000\"",
    "required": false,
    "expected-type": "mcp_server_url"
  },
  "agent-package/agents/mcp-servers/headers": {
    "description": "Required headers for the MCP server connection (only for streamable-http and sse kinds).",
    "required": false,
    "expected-type": "mcp_server_headers"
  },
  "agent-package/agents/mcp-servers/headers/type": {
    "description": "The type of the header. Accepted values: \"secret\", \"oauth2-secret\", \"string\", \"data-server-info\"",
    "required": true,
    "expected-type": "mcp_server_var_type"
  },
  "agent-package/agents/mcp-servers/headers/description": {
    "description": "Optional: human-readable description of the header.",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/headers/provider": {
    "description": "OAuth2 provider name (only required for oauth2-secret type). Example: \"Microsoft\"",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/headers/scopes": {
    "description": "OAuth2 scopes (only required for oauth2-secret type). Example: [\"user.read\", \"user.write\"]",
    "required": false,
    "expected-type": "list"
  },
  "agent-package/agents/mcp-servers/headers/default": {
    "description": "Default value for the variable (only for string type).",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/command-line": {
    "description": "Command line to execute for stdio MCP servers. Example: [\"uv\", \"run\", \"python\", \"-m\", \"my-server\"]",
    "required": false,
    "expected-type": "mcp_server_command_line"
  },
  "agent-package/agents/mcp-servers/env": {
    "description": "Environment variables for the MCP server (only for stdio kind).",
    "required": false,
    "expected-type": "mcp_server_env"
  },
  "agent-package/agents/mcp-servers/env/type": {
    "description": "The type of the environment variable. Accepted values: \"secret\", \"oauth2-secret\", \"string\", \"data-server-info\"",
    "required": true,
    "expected-type": "mcp_server_var_type"
  },
  "agent-package/agents/mcp-servers/env/description": {
    "description": "Optional: human-readable description of the environment variable.",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/env/provider": {
    "description": "OAuth2 provider name (only required for oauth2-secret type). Example: \"Microsoft\"",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/env/scopes": {
    "description": "OAuth2 scopes (only required for oauth2-secret type). Example: [\"user.read\", \"user.write\"]",
    "required": false,
    "expected-type": "list"
  },
  "agent-package/agents/mcp-servers/env/default": {
    "description": "Default value for the variable (only for string type).",
    "required": false,
    "expected-type": "string"
  },
  "agent-package/agents/mcp-servers/cwd": {
    "description": "Working directory for the command line (defaults to agent-spec directory if not specified). Can be relative or absolute path.",
    "required": false,
    "expected-type": {
      "type": "file",
      "relative-to": "./"
    }
  },
  "agent-package/agents/mcp-servers/force-serial-tool-calls": {
    "description": "If true, tool calls are serialized (default is false).",
    "required": false,
    "expected-type": "bool"
  },
  "agent-package/agents/conversation-guide": {
    "description": "Conversation guide for the agent. Example: \"conversation-guide.yaml\"",
    "required": false,
    "expected-type": {
      "type": "file",
      "relative-to": "./"
    }
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
""")
)
