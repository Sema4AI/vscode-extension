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

// Helper function to handle common response logic
const handleServerResponse = async (
    panel: vscode.WebviewPanel,
    result: ActionResult,
    successMessage: string,
    errorMessage: string,
    shouldCloseOnSuccess: boolean = false
) => {
    if (result.success) {
        // Show success message in the webview
        panel.webview.postMessage({
            command: "showSuccess",
            message: result.message || successMessage,
        });

        // Also show a notification
        vscode.window.showInformationMessage(result.message || successMessage);

        // Close the webview if specified
        if (shouldCloseOnSuccess) {
            setTimeout(() => {
                panel.dispose();
            }, 1000);
        }
    } else {
        // Show error message in the webview
        panel.webview.postMessage({
            command: "showError",
            message: result.message || errorMessage,
        });

        // Also show an error notification
        vscode.window.showErrorMessage(result.message || errorMessage);
    }
};

const handleServerError = (panel: vscode.WebviewPanel, error: any, operation: string) => {
    console.error(`Error ${operation} MCP server:`, error);

    // Show error message in the webview
    panel.webview.postMessage({
        command: "showError",
        message: `Error ${operation} MCP server: ${error}`,
    });

    // Also show an error notification
    vscode.window.showErrorMessage(`Error ${operation} MCP server: ${error}`);
};

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

                    await handleServerResponse(
                        panel,
                        result,
                        "MCP Server configuration saved successfully!",
                        "Failed to save MCP Server configuration",
                        true // Close panel on success
                    );
                } catch (error) {
                    handleServerError(panel, error, "adding");
                }
                return;

            case "testServer":
                const testConfig: MCPServerConfig = message.config;

                try {
                    // Call the language server function to validate the MCP server
                    const result = (await langServer.sendRequest("testMCPServer", {
                        mcp_server_config: testConfig,
                    })) as ActionResult;

                    await handleServerResponse(
                        panel,
                        result,
                        "MCP Server test successful!",
                        "Failed to validate MCP Server",
                        false // Don't close panel on success
                    );
                } catch (error) {
                    handleServerError(panel, error, "testing");
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
