import * as roboCommands from "./robocorpCommands";
import { commands, env, window } from "vscode";
import { listAndAskRobotSelection } from "./activities";
import { LocatorEntry, RobotEntry } from "./viewsCommon";
import { getSelectedRobot } from "./viewsSelection";
import { OUTPUT_CHANNEL } from "./channel";
import { LocalPackageMetadataInfo, ActionResult } from "./protocols";
import { getLocatorSingleTreeSelection } from "./viewsResources";

export async function copySelectedToClipboard(locator?: LocatorEntry) {
    let locatorSelected: LocatorEntry | undefined = locator || (await getLocatorSingleTreeSelection());
    if (locatorSelected) {
        env.clipboard.writeText("alias:" + locatorSelected.name);
    }
}

export async function removeLocator(locator?: LocatorEntry) {
    // Confirmation dialog button texts
    const DELETE = "Delete";
    let locatorSelected: LocatorEntry | undefined = locator || (await getLocatorSingleTreeSelection());
    if (!locatorSelected) {
        OUTPUT_CHANNEL.appendLine("Warning: Trying to delete locator when there is no locator selected");
        return;
    }
    let selectedEntry: RobotEntry = getSelectedRobot({
        noSelectionMessage: "Please select a robot first.",
    });
    let robot: LocalPackageMetadataInfo | undefined = selectedEntry?.robot;
    if (!robot) {
        // Ask for the robot to be used and then show dialog with the options.
        robot = await listAndAskRobotSelection(
            "Please select the Task or Action Package where the locator should be removed.",
            "Unable to remove locator (no Task or Action Package detected in the Workspace).",
            { showActionPackages: true, showTaskPackages: true, showAgentPackages: false }
        );
        if (!robot) {
            OUTPUT_CHANNEL.appendLine("Warning: Trying to delete locator when there is no robot selected");
            return;
        }
    }
    const result = await window.showWarningMessage(
        `Are you sure you want to delete the locator "${locatorSelected?.name}"?`,
        { "modal": true },
        DELETE
    );
    if (result === DELETE) {
        const actionResult: ActionResult<any> = await commands.executeCommand(
            roboCommands.SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL,
            {
                robotYaml: robot.filePath,
                name: locatorSelected?.name,
            }
        );
        if (actionResult.success) {
            OUTPUT_CHANNEL.appendLine(`Locator "${locatorSelected?.name} removed successfully`);
        } else {
            OUTPUT_CHANNEL.appendLine(
                `Unable to remove Locator "${locatorSelected?.name}, because of:\n${actionResult.message}`
            );
        }
    }
}
