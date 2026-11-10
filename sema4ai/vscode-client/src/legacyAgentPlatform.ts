import * as vscode from "vscode";
import { logError, OUTPUT_CHANNEL } from "./channel";

// Docs section with the downloads of the 2.x extension (the last version supporting
// Agent and Action Packages of the legacy agent platform).
export const LEGACY_AGENT_PLATFORM_DOCS_URL =
    "https://sema4.ai/docs/build/visual-studio-code#version-2x-legacy-agent-platform";

const LEGACY_AGENT_PLATFORM_NOTICE_SHOWN_KEY = "sema4ai.legacyAgentPlatformNoticeShown";
// Set per workspace when it was searched and had no legacy packages (so that the search
// is done only once per workspace).
const LEGACY_AGENT_PLATFORM_NOT_FOUND_KEY = "sema4ai.legacyAgentPlatformPackagesNotFound";
const EXCLUDE_GLOB = "**/{node_modules,.venv,.git}/**";

async function hasLegacyAgentPlatformPackage(): Promise<boolean> {
    const agentSpecs = await vscode.workspace.findFiles("**/agent-spec.yaml", EXCLUDE_GLOB, 1);
    if (agentSpecs.length > 0) {
        return true;
    }

    // Action Packages have a package.yaml depending on sema4ai-actions (or robocorp-actions).
    // Other tools also use package.yaml, so, check the contents.
    const packageYamls = await vscode.workspace.findFiles("**/package.yaml", EXCLUDE_GLOB, 50);
    for (const uri of packageYamls) {
        const contents = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString("utf-8");
        if (contents.includes("sema4ai-actions") || contents.includes("robocorp-actions")) {
            return true;
        }
    }
    return false;
}

/**
 * Shows (only once) a notice when the workspace has Agent or Action Packages, which are
 * no longer supported, pointing to the docs on how to install the 2.x extension.
 */
export async function showLegacyAgentPlatformNotice(context: vscode.ExtensionContext): Promise<void> {
    const { globalState, workspaceState } = context;
    try {
        if (globalState.get(LEGACY_AGENT_PLATFORM_NOTICE_SHOWN_KEY)) {
            return;
        }
        if (!vscode.workspace.workspaceFolders?.length || workspaceState.get(LEGACY_AGENT_PLATFORM_NOT_FOUND_KEY)) {
            return;
        }
        if (!(await hasLegacyAgentPlatformPackage())) {
            await workspaceState.update(LEGACY_AGENT_PLATFORM_NOT_FOUND_KEY, true);
            return;
        }
        await globalState.update(LEGACY_AGENT_PLATFORM_NOTICE_SHOWN_KEY, true);

        const msg =
            "Agent and Action Packages belong to the legacy agent platform and are not supported in this version " +
            "of the Sema4.ai SDK. To keep working with them, install version 2.x of the extension.";
        OUTPUT_CHANNEL.appendLine(msg + " See: " + LEGACY_AGENT_PLATFORM_DOCS_URL);

        const LEARN_MORE = "Learn more";
        const selection = await vscode.window.showInformationMessage(msg, LEARN_MORE);
        if (selection === LEARN_MORE) {
            vscode.env.openExternal(vscode.Uri.parse(LEGACY_AGENT_PLATFORM_DOCS_URL));
        }
    } catch (error) {
        logError("Error checking for legacy agent platform packages.", error, "ERR_LEGACY_AGENT_PLATFORM_NOTICE");
    }
}
