import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import * as roboCommands from "./robocorpCommands";
import { CloudEntry, treeViewIdToTreeDataProvider } from "./viewsCommon";
import { SEMA4AI_SUBMIT_ISSUE } from "./robocorpCommands";
import { TREE_VIEW_SEMA4AI_CLOUD_TREE } from "./robocorpViews";
import { getWorkspaceDescription } from "./ask";
import { logError } from "./channel";
import { ActionResult, IAccountInfo, IVaultInfo } from "./protocols";

export class CloudTreeDataProvider implements vscode.TreeDataProvider<CloudEntry> {
    private _onDidChangeTreeData: vscode.EventEmitter<CloudEntry | null> = new vscode.EventEmitter<CloudEntry | null>();
    readonly onDidChangeTreeData: vscode.Event<CloudEntry | null> = this._onDidChangeTreeData.event;

    public refreshOnce = false;

    fireRootChange() {
        this._onDidChangeTreeData.fire(null);
    }

    private async _fillRoots(ret: CloudEntry[]) {
        const accountInfoResult: ActionResult<IAccountInfo> = await vscode.commands.executeCommand(
            roboCommands.SEMA4AI_GET_LINKED_ACCOUNT_INFO_INTERNAL
        );
        const profileListResultPromise: Thenable<ActionResult<any>> = vscode.commands.executeCommand(
            roboCommands.SEMA4AI_PROFILE_LIST_INTERNAL
        );

        if (!accountInfoResult.success) {
            ret.push({
                "label": "Link to Control Room",
                "iconPath": "link",
                "viewItemContextValue": "cloudLoginItem",
                "command": {
                    "title": "Link to Control Room",
                    "command": roboCommands.SEMA4AI_CLOUD_LOGIN,
                },
            });
        } else {
            const accountInfo: IAccountInfo = accountInfoResult.result;
            ret.push({
                "label": "Linked: " + accountInfo.fullname + " (" + accountInfo.email + ")",
                "iconPath": "link",
                "viewItemContextValue": "cloudLogoutItem",
            });

            let vaultInfoResult: ActionResult<any> = await vscode.commands.executeCommand(
                roboCommands.SEMA4AI_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL
            );

            if (!vaultInfoResult || !vaultInfoResult.success || !vaultInfoResult.result) {
                ret.push({
                    "label": "Workspace (vault, storage): disconnected.",
                    "iconPath": "unlock",
                    "viewItemContextValue": "workspaceDisconnected",
                    "tooltip": `Connecting to a workspace enables accessing vault and storage settings in the selected workspace.`,
                });
            } else {
                const result: IVaultInfo = vaultInfoResult.result;
                const desc = getWorkspaceDescription(result);
                ret.push({
                    "label": "Workspace: " + desc,
                    "iconPath": "lock",
                    "viewItemContextValue": "workspaceConnected",
                    "tooltip": `Enables access to vault and storage settings in: "${getWorkspaceDescription(result)}"`,
                });
            }
        }

        const profileListResult = await profileListResultPromise;
        if (profileListResult?.success) {
            ret.push({
                "label": `Profile: ${profileListResult.result["current"]}`,
                "iconPath": "person",
                "viewItemContextValue": "profileItem",
            });
        } else {
            ret.push({
                "label": `Profile: ${profileListResult.message}`,
                "iconPath": "person",
                "viewItemContextValue": "profileItem",
            });
        }
    }

    async getChildren(element?: CloudEntry): Promise<CloudEntry[]> {
        if (!element) {
            let ret: CloudEntry[] = [];
            try {
                await this._fillRoots(ret);
                ret.push({
                    "label": "Documentation",
                    "iconPath": "book",
                    "command": {
                        "title": "Open https://robocorp.com/docs",
                        "command": "vscode.open",
                        "arguments": [vscode.Uri.parse("https://robocorp.com/docs")],
                    },
                });
            } catch (error) {
                logError("Error getting children", error, "VIEWS_CLOUD_COMPUTE_ROOTS");
                ret.push({
                    "label": "Error initializing. Click to see Output > Sema4.ai.",
                    "iconPath": "error",
                    "command": {
                        "title": "See output",
                        "command": roboCommands.SEMA4AI_SHOW_OUTPUT,
                    },
                });
            }
            ret.push({
                "label": "Submit issue to Sema4.ai",
                "iconPath": "report",
                "command": {
                    "title": "Submit issue to Sema4.ai",
                    "command": SEMA4AI_SUBMIT_ISSUE,
                },
            });
            ret.push(getBuildInfoEntry());

            return ret;
        }
        if (element.children) {
            return element.children;
        }
        return [];
    }

    getTreeItem(element: CloudEntry): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(
            element.label,
            element.children ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None
        );
        treeItem.command = element.command;
        treeItem.iconPath = new vscode.ThemeIcon(element.iconPath);
        if (element.viewItemContextValue) {
            treeItem.contextValue = element.viewItemContextValue;
        }
        if (element.tooltip) {
            treeItem.tooltip = element.tooltip;
        }
        return treeItem;
    }
}

// Version, commit and build time of the running extension (the commit and build
// time come from out/buildInfo.json, written by scripts/writeBuildInfo.js).
function getBuildInfoEntry(): CloudEntry {
    const extension = vscode.extensions.getExtension("sema4ai.sema4ai");
    const version: string = extension?.packageJSON.version ?? "unknown";
    let commit = "unknown";
    let buildTime = "unknown";
    let buildTimeLabel = "unknown";
    // The file is missing in dev setups (`npm run watch` doesn't write it), so only
    // log real read or parse errors.
    const buildInfoPath = extension
        ? path.join(extension.extensionPath, "vscode-client", "out", "buildInfo.json")
        : undefined;
    if (buildInfoPath && fs.existsSync(buildInfoPath)) {
        try {
            const buildInfo = JSON.parse(fs.readFileSync(buildInfoPath, "utf-8"));
            commit = buildInfo["commit"] ?? commit;
            buildTime = buildInfo["buildTime"] ?? buildTime;
            // i.e.: 2026-11-09T09:54:56.544Z -> 2026-11-09 09:54 UTC
            buildTimeLabel = buildTime.slice(0, 16).replace("T", " ") + " UTC";
        } catch (error) {
            logError("Error reading build info", error, "VIEWS_CLOUD_BUILD_INFO");
        }
    }
    const buildInfo = `Sema4.ai SDK ${version} · ${commit} · ${buildTime}`;
    return {
        "label": `Version ${version} · ${commit} · ${buildTimeLabel}`,
        "iconPath": "info",
        "tooltip": `Sema4.ai SDK ${version}\nCommit: ${commit}\nBuilt: ${buildTime}\n\nClick to copy to the clipboard.`,
        "command": {
            "title": "Copy to clipboard",
            "command": roboCommands.SEMA4AI_COPY_BUILD_INFO_INTERNAL,
            "arguments": [buildInfo],
        },
    };
}

export function refreshCloudTreeView() {
    let dataProvider: CloudTreeDataProvider = <CloudTreeDataProvider>(
        treeViewIdToTreeDataProvider.get(TREE_VIEW_SEMA4AI_CLOUD_TREE)
    );
    if (dataProvider) {
        dataProvider.refreshOnce = true;
        dataProvider.fireRootChange();
    }
}
