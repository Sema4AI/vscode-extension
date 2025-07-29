import * as vscode from "vscode";
import { readFileSync } from "fs";
import * as path from "path";
import { getExtensionRelativeFile } from "./files";
import { langServer } from "./extension";
import { selectAgentPackage } from "./robo/agentPackage";

interface MCPServerConfig {
    name: string;
    description?: string;
    transport: string;
    url?: string;
    commandLine?: string;
    cwd?: string;
    headers?: Record<string, string | MCPVariableConfig>;
    env?: Record<string, string | MCPVariableConfig>;
}

interface MCPVariableConfig {
    type: "string" | "secret" | "oauth2-secret" | "data-server-info";
    description?: string;
    default?: string;
    provider?: string;
    scopes?: string[];
}

interface ActionResult<T = any> {
    success: boolean;
    message?: string;
    result?: T;
}

export const addMCPServer = async (agentDir?: string) => {
    if (!agentDir) {
        agentDir = await selectAgentPackage();
        if (!agentDir) {
            return;
        }
    }

    const panel = vscode.window.createWebviewPanel("mcpServerForm", "Add MCP Server", vscode.ViewColumn.One, {
        enableScripts: true,
        retainContextWhenHidden: true,
    });

    panel.webview.html = getWebviewContent();

    panel.webview.onDidReceiveMessage(async (message) => {
        switch (message.command) {
            case "submit":
                const config: MCPServerConfig = message.config;

                try {
                    // Call the language server function to add the MCP server
                    const result = (await langServer.sendRequest("addMCPServer", {
                        agent_dir: agentDir,
                        mcp_server_config: config,
                    })) as ActionResult;

                    if (result.success) {
                        // Show success message in the webview
                        panel.webview.postMessage({
                            command: "showSuccess",
                            message: result.message || "MCP Server configuration saved successfully!",
                        });

                        // Also show a notification
                        vscode.window.showInformationMessage(result.message || "MCP Server configuration saved!");

                        // Close the webview after 1 second
                        setTimeout(() => {
                            panel.dispose();
                        }, 1000);
                    } else {
                        // Show error message in the webview
                        panel.webview.postMessage({
                            command: "showError",
                            message: result.message || "Failed to save MCP Server configuration",
                        });

                        // Also show an error notification
                        vscode.window.showErrorMessage(result.message || "Failed to save MCP Server configuration");
                    }
                } catch (error) {
                    console.error("Error adding MCP server:", error);

                    // Show error message in the webview
                    panel.webview.postMessage({
                        command: "showError",
                        message: `Error adding MCP server: ${error}`,
                    });

                    // Also show an error notification
                    vscode.window.showErrorMessage(`Error adding MCP server: ${error}`);
                }
                return;

            case "cancel":
                panel.dispose();
                return;
        }
    });
};

function getWebviewContent(): string {
    const templateFile = getExtensionRelativeFile("../../vscode-client/templates/mcp_server_form.html", true);
    const data = readFileSync(templateFile, "utf8");
    return data;
}

export const addDockerMCPGateway = async (agentDir?: string) => {
    if (!agentDir) {
        agentDir = await selectAgentPackage();
        if (!agentDir) {
            return;
        }
    }

    try {
        // First check if docker-mcp-gateway already exists
        const checkResult = (await langServer.sendRequest("checkDockerMCPGatewayExists", {
            agent_dir: agentDir,
        })) as ActionResult<{ exists: boolean }>;

        if (!checkResult.success) {
            vscode.window.showErrorMessage(checkResult.message || "Failed to check Docker MCP Gateway configuration");
            return;
        }

        // If it exists, show warning dialog
        if (checkResult.result?.exists) {
            const OVERRIDE = "Override";
            const CANCEL = "Cancel";

            const userChoice = await vscode.window.showWarningMessage(
                "A Docker MCP Gateway configuration already exists in agent-spec.yaml. This action will override the existing configuration.",
                { modal: true },
                OVERRIDE,
                CANCEL
            );

            if (userChoice !== OVERRIDE) {
                // User cancelled or closed the dialog
                return;
            }
        }

        // Proceed with adding/overriding the docker-mcp-gateway
        const result = (await langServer.sendRequest("addDockerMCPGateway", {
            agent_dir: agentDir,
        })) as ActionResult;

        if (result.success) {
            vscode.window.showInformationMessage(result.message || "Docker MCP Gateway configuration saved!");

            const agentSpecPath = path.join(agentDir, "agent-spec.yaml");
            try {
                const document = await vscode.workspace.openTextDocument(agentSpecPath);
                await vscode.window.showTextDocument(document);
            } catch (error) {
                console.error("Error opening agent-spec.yaml:", error);
            }
        } else {
            vscode.window.showErrorMessage(result.message || "Failed to save Docker MCP Gateway configuration");
        }
    } catch (error) {
        console.error("Error adding Docker MCP Gateway:", error);
        vscode.window.showErrorMessage(`Error adding Docker MCP Gateway: ${error}`);
    }
};

