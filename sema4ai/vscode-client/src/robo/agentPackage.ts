import { commands, window, WorkspaceFolder, Uri } from "vscode";
import { getAgentCliLocation } from "../agentCli";
import { askForWs } from "../ask";
import {
    getPackageTargetDirectoryAndName,
    verifyIfIsPackageDirectory,
    refreshFilesExplorer,
    verifyIfPathOkToCreatePackage,
    getWorkspacePackages,
    PackageTargetAndNameResult,
} from "../common";
import { ActionResult, LocalPackageMetadataInfo, PackageType } from "../protocols";
import * as roboCommands from "../robocorpCommands";
import { makeDirs } from "../files";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { langServer } from "../extension";

const obtainTargetDirAndNameForAgentPackage = async (title: string): Promise<PackageTargetAndNameResult> => {
    const ws = await askForWs();
    const isWorkspacePackageDirectory = ws ? await verifyIfIsPackageDirectory(ws.uri) : null;

    if (!ws || isWorkspacePackageDirectory) {
        return undefined;
    }

    const { targetDir, name } = await getPackageTargetDirectoryAndName(ws, {
        title,
        useWorkspaceFolderPrompt: "The workspace will only have a single Agent Package.",
        useChildFolderPrompt: "Multiple Agent Packages can be created in this workspace.",
        provideNamePrompt: "Please provide the name for the Agent Package.",
        commandType: PackageType.Agent,
    });

    // Operation cancelled.
    if (!targetDir) {
        return undefined;
    }

    // Now, let's validate if we can indeed create an Agent Package in the given folder.
    const op = await verifyIfPathOkToCreatePackage(targetDir);
    switch (op) {
        case "force":
        case "empty":
            break;
        case "cancel":
            return;
        default:
            throw Error("Unexpected result: " + op);
    }

    await makeDirs(targetDir);
    return { targetDir: targetDir, name: name };
};

export const importAgentPackage = async (): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    let uriResult: Uri[] | undefined = await window.showOpenDialog({
        "canSelectFolders": false,
        "canSelectFiles": true,
        "canSelectMany": false,
        "openLabel": "Import Agent Package",
        "filters": {
            "Agent Packages": ["zip"],
        },
    });
    if (!uriResult || uriResult.length != 1) {
        return;
    }

    const { targetDir } = await obtainTargetDirAndNameForAgentPackage("Where do you want to import the Agent Package?");

    if (!targetDir) {
        return;
    }

    const agentPackageZip = uriResult[0].fsPath;
    OUTPUT_CHANNEL.appendLine(`Importing Agent Package from zip: ${agentPackageZip} into folder: ${targetDir}`);

    try {
        const result = await langServer.sendRequest<ActionResult<string>>("importAgentPackageFromZip", {
            target_dir: targetDir,
            agent_package_zip: agentPackageZip,
        });
        if (!result.success) {
            throw new Error(result.message || "Unknown error");
        }

        refreshFilesExplorer();
        window.showInformationMessage("Agent Package successfully imported in:\n" + targetDir);
    } catch (err) {
        const errorMsg = "Error importing Agent Package. Target: " + targetDir + " File: " + uriResult;
        logError(errorMsg, err, "ERR_IMPORT_ACTION_PACKAGE");
        OUTPUT_CHANNEL.appendLine(errorMsg);
        window.showErrorMessage(errorMsg + " (see `OUTPUT > Sema4.ai` for more details).");
    }
};

export const createAgentPackage = async (): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    const { targetDir, name } = await obtainTargetDirAndNameForAgentPackage(
        "Where do you want to create the Agent Package?"
    );

    // Operation cancelled.
    if (!targetDir) {
        return;
    }

    try {
        const result: ActionResult<string> = await commands.executeCommand(
            roboCommands.SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL,
            {
                "directory": targetDir,
                "name": name,
            }
        );

        if (!result.success) {
            throw new Error(result.message || "Unknown error");
        }

        refreshFilesExplorer();
        window.showInformationMessage("Agent Package successfully created in:\n" + targetDir);
    } catch (err) {
        const errorMsg = "Error creating Agent Package at: " + targetDir;
        logError(errorMsg, err, "ERR_CREATE_ACTION_PACKAGE");
        OUTPUT_CHANNEL.appendLine(errorMsg);
        window.showErrorMessage(errorMsg + " (see `OUTPUT > Sema4.ai` for more details).");
    }
};

export const packAgentPackage = async (packageInfo: LocalPackageMetadataInfo): Promise<{ zipPath: string } | null> => {
    const targetDir = packageInfo.directory;

    try {
        const result: ActionResult<string> = await commands.executeCommand(
            roboCommands.SEMA4AI_PACK_AGENT_PACKAGE_INTERNAL,
            { directory: targetDir }
        );

        if (!result.success) {
            throw new Error(result.message || "An unexpected error occurred during the packaging process.");
        }

        return { zipPath: result.result };
    } catch (error) {
        const errorMsg = `Failed to package the agent at: ${targetDir}`;
        logError(errorMsg, error, "ERR_PACK_ACTION_PACKAGE");

        const detailedErrorMsg = `${errorMsg}. Please check the 'OUTPUT > Sema4.ai' for more details.`;
        OUTPUT_CHANNEL.appendLine(detailedErrorMsg);
        window.showErrorMessage(detailedErrorMsg);
    }

    return null;
};

export const selectAndPackAgentPackage = async (): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    let ws: WorkspaceFolder | undefined = await askForWs();
    if (!ws) {
        // Operation cancelled.
        return;
    }

    const workspacePackages = await getWorkspacePackages();

    if (!workspacePackages?.agentPackages?.length) {
        window.showErrorMessage("No Agent Packages found in the workspace.");
        return;
    }

    let packageInfo: LocalPackageMetadataInfo;
    let actionPackageSelection: string | null = null;

    /* If root level contains an agent-spec.yaml, there will be only one Agent Package. */
    if (workspacePackages.agentPackages.length === 1) {
        packageInfo = workspacePackages.agentPackages[0];
    } else {
        actionPackageSelection = await window.showQuickPick(
            workspacePackages.agentPackages.map((agentPackage) => agentPackage.name),
            {
                placeHolder: "Which action package do you want to pack?",
                ignoreFocusOut: true,
            }
        );

        /* Operation cancelled. */
        if (!actionPackageSelection) {
            return null;
        }

        // Update packageInfo based on selected action package
        packageInfo = workspacePackages.agentPackages.find(
            (agentPackage) => agentPackage.name === actionPackageSelection
        );
    }

    const result = await packAgentPackage(packageInfo);
    if (result) {
        window.showInformationMessage(`Package successfully packed at:\n${result.zipPath}`);
        await commands.executeCommand("revealInExplorer", Uri.file(result.zipPath));
    }
};
