import { Uri, window, WorkspaceFolder } from "vscode";

import { askForWs, QuickPickItemWithAction, showSelectOneQuickPick } from "../ask";
import { afterActionPackageCreated, askActionPackageTargetDir } from "./actionPackage";
import { langServer } from "../extension";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { PackageYamlName } from "../protocols";

export const importActionPackage = async (agentPath?: string) => {
    // We have 2 different ways of importing an action:
    // 1. Get online from the gallery
    // 2. Get from local path

    let ws: WorkspaceFolder | undefined = await askForWs();
    if (!ws) {
        // Operation cancelled.
        return;
    }

    // show a dialog with the options
    const options: QuickPickItemWithAction[] = [
        {
            "label": "Import from Sema4.ai Gallery",
            "detail": "Import action package from Sema4.ai online gallery",
            "action": "from_gallery",
        },
        {
            "label": "Import from zip file",
            "detail": "Import action package from zip file",
            "action": "from_local_path",
        },
    ];

    let selectedItem: QuickPickItemWithAction = await showSelectOneQuickPick(options, "Select kind of action import");
    if (!selectedItem) {
        return;
    }

    let action_kind: "sema4ai" | "myaction" = "myaction";

    let importCommand: (targetDir: string) => Promise<any>;
    if (selectedItem.action === "from_gallery") {
        action_kind = "sema4ai";

        const result = await langServer.sendRequest("listGalleryActionPackages");

        if (!result["success"]) {
            window.showErrorMessage(result["message"] || "Unknown error");
        }

        const packages = result["result"];
        if (!packages) {
            throw new Error("No packages found in metadata");
        }

        const entries = Object.entries(packages);

        // Sort entries by the name and version
        entries.sort((a, b) => {
            const [keyA, valueA] = a;
            const [keyB, valueB] = b;

            const nameA = valueA["name"];
            const nameB = valueB["name"];

            if (nameA === nameB) {
                const versionA = valueA["version"];
                const versionB = valueB["version"];
                try {
                    // version is in the format X.Y.Z, we need to compare as ints each part.
                    const versionAInts = versionA.split(".").map(Number);
                    const versionBInts = versionB.split(".").map(Number);

                    for (let i = 0; i < 3; i++) {
                        if (versionAInts[i] !== versionBInts[i]) {
                            return versionAInts[i] - versionBInts[i];
                        }
                    }
                } catch (error) {
                    logError(
                        `Error comparing versions ${versionA} and ${versionB}`,
                        error,
                        "ERROR_IMPORT_ACTION_PACKAGE"
                    );
                }
            }

            return nameA.localeCompare(nameB);
        });

        const options: QuickPickItemWithAction[] = [];
        for (const [key, value] of entries) {
            options.push({
                "label": key,
                "detail": value["description"],
                "action": key,
            });
        }

        let selectedItem: QuickPickItemWithAction = await showSelectOneQuickPick(
            options,
            "Select gallery action package to import"
        );
        if (!selectedItem) {
            return;
        }

        importCommand = async (targetDir: string) => {
            return await langServer.sendRequest("importGalleryActionPackage", {
                "package_key": selectedItem.action,
                "target_dir": targetDir,
            });
        };
    } else if (selectedItem.action === "from_local_path") {
        // Open dialog to select a zip file
        const zipFilePath: Uri[] | undefined = await window.showOpenDialog({
            "title": "Select the zip file",
            "canSelectFiles": true,
            "canSelectFolders": false,
            "canSelectMany": false,
            "filters": { "Zip files": ["zip"] },
        });

        if (!zipFilePath) {
            return;
        }

        importCommand = async (targetDir: string) => {
            return await langServer.sendRequest("importZipAsActionPackage", {
                "zip_path": zipFilePath[0].fsPath,
                "target_dir": targetDir,
            });
        };
    }

    let agentSpecPath: string;
    let targetDir: string;

    if (!agentPath) {
        const requestPackageName = false;
        const packageInfo = await askActionPackageTargetDir(ws, action_kind, requestPackageName);
        const { targetDir: tempTargetDir, agentSpecPath: tempAgentSpecPath } = packageInfo;

        // Operation cancelled or directory conflict detected.
        if (!tempTargetDir) {
            return;
        }

        // Assign the final values from packageInfo
        targetDir = tempTargetDir;
        agentSpecPath = tempAgentSpecPath;
    } else {
        const dirName = action_kind === "myaction" ? "MyActions" : "Sema4.ai";
        targetDir = Uri.joinPath(Uri.file(agentPath), "actions", dirName).fsPath;

        agentSpecPath = Uri.joinPath(Uri.file(agentPath), PackageYamlName.Agent).fsPath;
    }

    const result = await importCommand(targetDir);
    if (!result.success) {
        const msg = result.message || "Unknown error";
        OUTPUT_CHANNEL.appendLine(`Error importing action package: ${msg}`);
        window.showErrorMessage(msg);
        return;
    }
    afterActionPackageCreated(result["result"], agentSpecPath);
};
