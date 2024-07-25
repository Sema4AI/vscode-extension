import {
    commands,
    window
} from "vscode";
import { getAgentCliLocation } from "../agentCli";
import { askForWs } from "../ask";
import {
    getPackageTargetDirectory,
    isDirectoryAPackageDirectory,
    refreshFilesExplorer,
    verifyIfPathOkToCreatePackage
} from "../common";
import { ActionResult } from "../protocols";
import * as roboCommands from "../robocorpCommands";
import { makeDirs } from "../files";
import {
    logError,
    OUTPUT_CHANNEL
} from "../channel";

export const createAgentPackage = async (): Promise<void> => {
    /* We make sure Agent Server exists - if not, getAgentServerLocation will ask user to download it.  */
    const agentCli = getAgentCliLocation();
    if (!agentCli) {
        return;
    }

    const ws = await askForWs();
    const isPackageDirectory = ws ? await isDirectoryAPackageDirectory(ws.uri) : null;

    if (!ws || isPackageDirectory) {
        return;
    }

    const targetDir = await getPackageTargetDirectory(ws, {
            title: "Where do you want to create the Agent Package?",
            useWorkspaceFolderPrompt: "The workspace will only have a single Agent Package.",
            useChildFolderPrompt: "Multiple Agent Packages can be created in this workspace.",
            provideNamePrompt: "Please provide the name for the Agent Package folder name."
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
