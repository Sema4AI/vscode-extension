import * as vscode from "vscode";
import { readFileSync } from "fs";
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
