import { commands, window, WorkspaceFolder, Uri } from "vscode";
import { getAgentCliLocation } from "../agentCli";
import { askForWs } from "../ask";
import {
    getPackageTargetDirectoryAndName,
    verifyIfIsPackageDirectory,
    refreshFilesExplorer,
    verifyIfPathOkToCreatePackage,
    getWorkspacePackages,
    isAgetPackageCommand,
} from "../common";
import { ActionResult, LocalPackageMetadataInfo, PackageYamlName } from "../protocols";
import * as roboCommands from "../robocorpCommands";
import { makeDirs } from "../files";
import { logError, OUTPUT_CHANNEL } from "../channel";

export const createAgentPackage = async (): Promise<void> => {
    /* We make sure Agent Server exists - if not, getAgentServerLocation will ask user to download it.  */
    const agentCli = getAgentCliLocation();
    if (!agentCli) {
        return;
    }

    const ws = await askForWs();
    const isWorkspacePackageDirectory = ws ? await verifyIfIsPackageDirectory(ws.uri) : null;

    if (!ws || isWorkspacePackageDirectory) {
        return;
    }

    const { targetDir, name } = await getPackageTargetDirectoryAndName(ws, {
        title: "Where do you want to create the Agent Package?",
        useWorkspaceFolderPrompt: "The workspace will only have a single Agent Package.",
        useChildFolderPrompt: "Multiple Agent Packages can be created in this workspace.",
        provideNamePrompt: "Please provide the name for the Agent Package.",
        commandType: isAgetPackageCommand,
    });

    /* Operation cancelled. */
    if (!targetDir) {
        return;
    }

    /* Now, let's validate if we can indeed create an Agent Package in the given folder. */
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
    const agentCli = getAgentCliLocation();
    if (!agentCli) {
        return;
    }

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
