import * as vscode from "vscode";
import * as path from "path";
import { commands } from "vscode";
import { PackageYamlName } from "../protocols";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL } from "../robocorpCommands";
import { fileExists } from "../files";
import { ActionResult } from "../protocols";

export function installPackageYamlWatcher(context: vscode.ExtensionContext) {
    // Watch for changes to package.yaml files
    const packageYamlWatcher = vscode.workspace.createFileSystemWatcher("**/package.yaml");

    const onPackageYamlChanged = async (uri: vscode.Uri) => {
        try {
            // Check if this package.yaml is inside an agent package
            const packageYamlDir = path.dirname(uri.fsPath);
            const agentSpecPath = path.join(packageYamlDir, "..", "..", "..", PackageYamlName.Agent);

            if (await fileExists(agentSpecPath)) {
                // This is inside an agent package, refresh the agent spec
                const result = await commands.executeCommand<ActionResult<unknown>>(
                    SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL,
                    {
                        "agent_spec_path": agentSpecPath,
                    }
                );

                if (!result.success) {
                    logError("Failed to refresh agent spec", new Error(result.message), "ERR_REFRESH_AGENT_SPEC");
                }
            }
        } catch (error) {
            logError("Error handling package.yaml change", error, "ERR_PACKAGE_YAML_CHANGE");
        }
    };

    packageYamlWatcher.onDidChange(onPackageYamlChanged);
    context.subscriptions.push(packageYamlWatcher);
}
