import { ActionResult, LocalPackageMetadataInfo } from "./protocols";
import { RobotEntry } from "./viewsCommon";
import { getSelectedRobot } from "./viewsSelection";
import { listAndAskRobotSelection } from "./activities";
import { logError } from "./channel";
import { commands, ProgressLocation, Uri, window } from "vscode";
import { SEMA4AI_OPEN_PLAYWRIGHT_RECORDER_INTERNAL } from "./robocorpCommands";

export async function openPlaywrightRecorder(useTreeSelected: boolean = false): Promise<void> {
    let currentUri: Uri | undefined = undefined;
    if (!useTreeSelected && window.activeTextEditor && window.activeTextEditor.document) {
        currentUri = window.activeTextEditor.document.uri;
    }

    if (!currentUri) {
        // User doesn't have a current editor opened, get from the tree
        // selection.
        let selectedEntry: RobotEntry = getSelectedRobot();
        let robot: LocalPackageMetadataInfo | undefined = selectedEntry?.robot;
        if (robot === undefined) {
            // Ask for the robot to be used and then show dialog with the options.
            robot = await listAndAskRobotSelection(
                "Please select the Task or Action Package where the locators should be saved.",
                "Unable to open Inspector (no Task or Action Package detected in the Workspace).",
                { showActionPackages: true, showTaskPackages: true, showAgentPackages: false }
            );
            if (!robot) {
                return;
            }
        }
        currentUri = Uri.file(robot.filePath);
    }

    if (!currentUri) {
        window.showErrorMessage("Unable to get selection for recording with playwright.");
        return;
    }

    let resolveProgress = undefined;
    window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Sema4.ai",
            cancellable: false,
        },
        (progress) => {
            progress.report({ message: "Opening Playwright Recorder..." });
            return new Promise<void>((resolve) => {
                resolveProgress = resolve;
            });
        }
    );

    try {
        const actionResult: ActionResult<any> = await commands.executeCommand(
            SEMA4AI_OPEN_PLAYWRIGHT_RECORDER_INTERNAL,
            {
                "target_robot_uri": currentUri.toString(),
            }
        );
        if (!actionResult.success) {
            resolveProgress();
            await window.showErrorMessage(actionResult.message);
        }
    } catch (error) {
        logError("Error resolving interpreter:", error, "ACT_RESOLVE_INTERPRETER");
    } finally {
        resolveProgress();
    }
}
