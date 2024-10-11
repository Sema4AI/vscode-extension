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
    revealInExtension,
} from "../common";
import { ActionResult, LocalPackageMetadataInfo, PackageType, PackageYamlName } from "../protocols";
import * as roboCommands from "../robocorpCommands";
import { makeDirs } from "../files";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { langServer } from "../extension";
import { RobotEntryType } from "../viewsCommon";

const obtainTargetDirAndNameForAgentPackage = async (title: string): Promise<PackageTargetAndNameResult> => {
    const ws = await askForWs();
    const isWorkspacePackageDirectory = ws ? await verifyIfIsPackageDirectory(ws.uri) : null;

    if (!ws || isWorkspacePackageDirectory) {
        return { targetDir: null, name: null };
    }

    const requestPackageName = true;
    const { targetDir, name } = await getPackageTargetDirectoryAndName(
        ws,
        {
            title,
            useWorkspaceFolderPrompt: "The workspace will only have a single Agent Package.",
            useChildFolderPrompt: "Multiple Agent Packages can be created in this workspace.",
            provideNamePrompt: "Please provide the name for the Agent Package.",
            commandType: PackageType.Agent,
        },
        requestPackageName
    );

    // Operation cancelled.
    if (!targetDir) {
        return { targetDir: null, name: null };
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

        revealInExtension(targetDir, RobotEntryType.AgentPackage);
        window.showInformationMessage("Agent Package successfully created in:\n" + targetDir);
    } catch (err) {
        const errorMsg = "Error creating Agent Package at: " + targetDir;
        logError(errorMsg, err, "ERR_CREATE_ACTION_PACKAGE");
        OUTPUT_CHANNEL.appendLine(errorMsg);
        window.showErrorMessage(errorMsg + " (see `OUTPUT > Sema4.ai` for more details).");
    }
};

export const packAgentPackage = async (targetDir: string): Promise<{ zipPath: string } | null> => {
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

const selectAgentPackage = async (): Promise<string> => {
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
    let agentPackageSelection: string | null = null;

    /* If root level contains an agent-spec.yaml, there will be only one Agent Package. */
    if (workspacePackages.agentPackages.length === 1) {
        packageInfo = workspacePackages.agentPackages[0];
    } else {
        agentPackageSelection = await window.showQuickPick(
            workspacePackages.agentPackages.map((agentPackage) => agentPackage.name),
            {
                placeHolder: "Which agent package do you want to pack?",
                ignoreFocusOut: true,
            }
        );

        /* Operation cancelled. */
        if (!agentPackageSelection) {
            return null;
        }

        // Update packageInfo based on selected action package
        packageInfo = workspacePackages.agentPackages.find(
            (agentPackage) => agentPackage.name === agentPackageSelection
        );
    }

    return packageInfo.directory;
};

export const selectAndPackAgentPackage = async (agentPath?: string): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    if (!agentPath) {
        agentPath = await selectAgentPackage();
    }

    const result = await packAgentPackage(agentPath);
    if (result) {
        window.showInformationMessage(`Package successfully packed at:\n${result.zipPath}`);
        await commands.executeCommand("revealInExplorer", Uri.file(result.zipPath));
    }
};

export const updateAgentVersion = async (agentPath: string): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    if (!agentPath) {
        agentPath = await selectAgentPackage();
    }

    const versionType = await window.showQuickPick(["Patch", "Minor", "Major"], {
        placeHolder: "What kind of version increment would you like to apply?",
        ignoreFocusOut: true,
    });

    if (!versionType) {
        return;
    }

    try {
        const result: ActionResult<string> = await commands.executeCommand(
            roboCommands.SEMA4AI_UPDATE_AGENT_VERSION_INTERNAL,
            {
                "agent_path": agentPath,
                "version_type": versionType,
            }
        );

        if (!result.success) {
            throw new Error(result.message || "An unexpected error occurred during the update process.");
        }

        window.showInformationMessage("Agent successfully updated.");
    } catch (error) {
        const errorMsg = `Failed to update the agent at: ${agentPath}`;
        logError(errorMsg, error, "ERR_UPDATE_AGENT_VERSION");

        const detailedErrorMsg = `${errorMsg}. Please check the 'OUTPUT > Sema4.ai' for more details.`;
        OUTPUT_CHANNEL.appendLine(detailedErrorMsg);
        window.showErrorMessage(detailedErrorMsg);
    }
};

export const refreshAgentSpec = async (agentPath: string): Promise<void> => {
    getAgentCliLocation(); // Starts getting agent cli in promise.

    if (!agentPath) {
        agentPath = await selectAgentPackage();
    }

    try {
        const result: ActionResult<string> = await commands.executeCommand(
            roboCommands.SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL,
            {
                "agent_spec_path": Uri.joinPath(Uri.file(agentPath), PackageYamlName.Agent).fsPath,
            }
        );

        if (!result.success) {
            throw new Error(result.message || "An unexpected error occurred during the refresh process.");
        }

        window.showInformationMessage("Agent successfully refreshed.");
    } catch (error) {
        const errorMsg = `Failed to refresh the Agent Configuration`;
        logError(errorMsg, error, "ERR_REFRESH_AGENT_SPEC");

        const detailedErrorMsg = `${errorMsg}. Please check the 'OUTPUT > Sema4.ai' for more details.`;
        OUTPUT_CHANNEL.appendLine(detailedErrorMsg);
        window.showErrorMessage(detailedErrorMsg);
    }
};
