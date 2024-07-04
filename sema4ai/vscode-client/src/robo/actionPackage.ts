import * as os from "os";

import * as fs from "fs";
import {
    QuickPickItem,
    WorkspaceFolder,
    commands,
    window,
    ProgressLocation,
    Progress,
    CancellationToken,
} from "vscode";
import * as vscode from "vscode";
import { join } from "path";
import * as roboCommands from "../robocorpCommands";
import {
    ActionResult,
    ActionTemplate,
    IActionInfo,
    LocalRobotMetadataInfo,
    ActionServerListOrganizationsOutput,
    ActionServerOrganization,
    ActionServerPackageBuildOutput,
    ActionServerPackageUploadStatusOutput,
} from "../protocols";
import {
    areThereRobotsInWorkspace,
    compareVersions,
    isActionPackage,
    isDirectoryAPackageDirectory,
    verifyIfPathOkToCreatePackage,
} from "../common";
import { slugify } from "../slugify";
import { fileExists, makeDirs } from "../files";
import { QuickPickItemWithAction, askForWs, showSelectOneQuickPick } from "../ask";
import * as path from "path";
import { OUTPUT_CHANNEL, logError } from "../channel";
import {
    downloadOrGetActionServerLocation,
    getActionServerVersion,
    verifyLogin,
    listOrganizations,
    findActionPackagePath,
} from "../actionServer";
import { createEnvWithRobocorpHome, getRobocorpHome } from "../rcc";

export interface QuickPickItemAction extends QuickPickItem {
    actionPackageUri: vscode.Uri;
    actionFileUri: vscode.Uri;
    actionPackageYamlDirectory: string;
    packageYaml: string;
    actionName: string;
    keyInLRU: string;
}

export async function createDefaultInputJson(inputUri: vscode.Uri) {
    await vscode.workspace.fs.writeFile(
        inputUri,
        Buffer.from(`{
    "paramName": "paramValue"
}`)
    );
}

export async function askAndRunRobocorpActionFromActionPackage(noDebug: boolean) {
    let textEditor = window.activeTextEditor;
    let fileName: string | undefined = undefined;

    if (textEditor) {
        fileName = textEditor.document.fileName;
    }

    const RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE = "RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE";
    let runLRU: string[] = await commands.executeCommand(roboCommands.SEMA4AI_LOAD_FROM_DISK_LRU, {
        "name": RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE,
    });

    let actionResult: ActionResult<LocalRobotMetadataInfo[]> = await commands.executeCommand(
        roboCommands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL
    );
    if (!actionResult.success) {
        window.showErrorMessage("Error listing Action Packages: " + actionResult.message);
        return;
    }
    let robotsInfo: LocalRobotMetadataInfo[] = actionResult.result;
    if (robotsInfo) {
        // Only use action packages.
        robotsInfo = robotsInfo.filter((r) => {
            return isActionPackage(r);
        });
    }

    if (!robotsInfo || robotsInfo.length == 0) {
        window.showInformationMessage("Unable to run Action Package (no Action Packages detected in the Workspace).");
        return;
    }

    let items: QuickPickItemAction[] = new Array();

    for (let robotInfo of robotsInfo) {
        try {
            const actionPackageUri = vscode.Uri.file(robotInfo.filePath);
            let result: ActionResult<undefined> = await vscode.commands.executeCommand(
                roboCommands.SEMA4AI_LIST_ACTIONS_INTERNAL,
                {
                    "action_package": actionPackageUri.toString(),
                }
            );
            if (result.success) {
                let actions: IActionInfo[] = result.result;
                for (const action of actions) {
                    const keyInLRU = `${robotInfo.name}: ${action.name}`;
                    const uri = vscode.Uri.parse(action.uri);
                    const item: QuickPickItemAction = {
                        "label": keyInLRU,
                        "actionName": action.name,
                        "actionFileUri": uri,
                        "actionPackageYamlDirectory": robotInfo.directory,
                        "actionPackageUri": actionPackageUri,
                        "packageYaml": robotInfo.filePath,
                        "keyInLRU": action.name,
                    };
                    if (runLRU && runLRU.length > 0 && keyInLRU == runLRU[0]) {
                        // Note that although we have an LRU we just consider the last one for now.
                        items.splice(0, 0, item);
                    } else {
                        items.push(item);
                    }
                }
            }
        } catch (error) {
            logError("Error collecting actions.", error, "ACT_COLLECT_ACTIONS");
        }
    }

    if (!items) {
        window.showInformationMessage("Unable to run Action Package (no Action Package detected in the Workspace).");
        return;
    }

    let selectedItem: QuickPickItemAction;
    if (items.length == 1) {
        selectedItem = items[0];
    } else {
        selectedItem = await window.showQuickPick(items, {
            "canPickMany": false,
            "placeHolder": "Please select the Action Package and Action to run.",
            "ignoreFocusOut": true,
        });
    }

    if (!selectedItem) {
        return;
    }

    await commands.executeCommand(roboCommands.SEMA4AI_SAVE_IN_DISK_LRU, {
        "name": RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE,
        "entry": selectedItem.keyInLRU,
        "lru_size": 3,
    });

    const actionName: string = selectedItem.actionName;
    const actionPackageYamlDirectory: string = selectedItem.actionPackageYamlDirectory;
    const packageYaml: string = selectedItem.actionPackageUri.fsPath;
    const actionFileUri: vscode.Uri = selectedItem.actionFileUri;
    await runActionFromActionPackage(noDebug, actionName, actionPackageYamlDirectory, packageYaml, actionFileUri);
}

export async function getTargetInputJson(actionName: string, actionPackageYamlDirectory: string): Promise<string> {
    const nameSlugified = slugify(actionName);

    const dir = actionPackageYamlDirectory;
    const devDataDir = path.join(dir, "devdata");
    await makeDirs(devDataDir);
    const targetInput = path.join(devDataDir, `input_${nameSlugified}.json`);
    return targetInput;
}

export async function runActionFromActionPackage(
    noDebug: boolean,
    actionName: string,
    actionPackageYamlDirectory: string,
    packageYaml: string,
    actionFileUri: vscode.Uri
) {
    // The input must be asked when running actions in this case and it should be
    // saved in 'devdata/input_xxx.json'
    const nameSlugified = slugify(actionName);
    const targetInput = await getTargetInputJson(actionName, actionPackageYamlDirectory);

    if (!(await fileExists(targetInput))) {
        let items: QuickPickItemWithAction[] = new Array();

        items.push({
            "label": `Create "devdata/input_${nameSlugified}.json" to customize action input`,
            "action": "create",
            "detail": "Note: Please relaunch after the customization is completed",
        });

        items.push({
            "label": `Cancel`,
            "action": "cancel",
        });

        let selectedItem: QuickPickItemWithAction | undefined = await showSelectOneQuickPick(
            items,
            "Input for the action not defined. How to proceed?",
            `Customize input for the ${actionName} action`
        );
        if (!selectedItem) {
            return;
        }

        if (selectedItem.action === "create") {
            // Create the file and ask the user to fill it and rerun the action
            // after he finished doing that.
            const inputUri = vscode.Uri.file(targetInput);
            await createDefaultInputJson(inputUri);
            await vscode.window.showTextDocument(inputUri);
        }
        // In any case, don't proceed if it wasn't previously created
        // (so that the user can customize it).
        return;
    }

    // Ok, input available. Let's create the launch and run it.
    let debugConfiguration: vscode.DebugConfiguration = {
        "name": "Config",
        "type": "sema4ai",
        "request": "launch",
        "package": packageYaml,
        "uri": actionFileUri.toString(),
        "jsonInput": targetInput,
        "actionName": actionName,
        "args": [],
        "noDebug": noDebug,
    };
    let debugSessionOptions: vscode.DebugSessionOptions = {};
    vscode.debug.startDebugging(undefined, debugConfiguration, debugSessionOptions);
}

export async function createActionPackage() {
    const robotsInWorkspacePromise: Promise<boolean> = areThereRobotsInWorkspace();
    const actionServerLocation = await downloadOrGetActionServerLocation();
    if (!actionServerLocation) {
        return;
    }

    let ws: WorkspaceFolder | undefined = await askForWs();
    if (!ws) {
        // Operation cancelled.
        return;
    }

    const actionServerVersionPromise: Promise<string | undefined> = getActionServerVersion(actionServerLocation);

    if (await isDirectoryAPackageDirectory(ws.uri)) {
        return;
    }

    const robotsInWorkspace: boolean = await robotsInWorkspacePromise;
    let useWorkspaceFolder: boolean;
    if (robotsInWorkspace) {
        // i.e.: if we already have robots, this is a multi-Robot workspace.
        useWorkspaceFolder = false;
    } else {
        const USE_WORKSPACE_FOLDER_LABEL = "Use workspace folder (recommended)";
        let target = await window.showQuickPick(
            [
                {
                    "label": USE_WORKSPACE_FOLDER_LABEL,
                    "detail": "The workspace will only have a single Action Package.",
                },
                {
                    "label": "Use child folder in workspace (advanced)",
                    "detail": "Multiple Action Packages can be created in this workspace.",
                },
            ],
            {
                "placeHolder": "Where do you want to create the Action Package?",
                "ignoreFocusOut": true,
            }
        );

        if (!target) {
            // Operation cancelled.
            return;
        }
        useWorkspaceFolder = target["label"] == USE_WORKSPACE_FOLDER_LABEL;
    }

    let targetDir = ws.uri.fsPath;
    if (!useWorkspaceFolder) {
        let name: string = await window.showInputBox({
            "value": "Example",
            "prompt": "Please provide the name for the Action Package folder name.",
            "ignoreFocusOut": true,
        });
        if (!name) {
            // Operation cancelled.
            return;
        }
        targetDir = join(targetDir, name);
    }

    // Now, let's validate if we can indeed create an Action Package in the given folder.
    const op = await verifyIfPathOkToCreatePackage(targetDir);
    let force: boolean;
    switch (op) {
        case "force":
            force = true;
            break;
        case "empty":
            force = false;
            break;
        case "cancel":
            return;
        default:
            throw Error("Unexpected result: " + op);
    }

    const robocorpHome = await getRobocorpHome();
    const env = createEnvWithRobocorpHome(robocorpHome);

    await makeDirs(targetDir);

    try {
        const actionServerVersion: string | undefined = await actionServerVersionPromise;
        if (actionServerVersion === undefined) {
            const msg = "Cannot do `new` command (it was not possible to get the action server version).";
            OUTPUT_CHANNEL.appendLine(msg);
            window.showErrorMessage(msg);
            return;
        }

        const compare = compareVersions("0.10.0", actionServerVersion);

        /**
         * For versions before 0.10.0, we pass empty string, to indicate no template.
         * It will be handled internally by the language server.
         */
        let template = "";

        if (compare <= 0) {
            template = await getTemplate(actionServerLocation);

            /* If there is no template, it means operation was cancelled, or errored. */
            if (!template) {
                return;
            }
        }

        const result: ActionResult<unknown> = await commands.executeCommand(
            roboCommands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
            {
                "action_server_location": actionServerLocation,
                "directory": targetDir,
                "template": template,
            }
        );

        if (!result.success) {
            throw new Error(result.message || "Unkown error");
        }

        try {
            commands.executeCommand("workbench.files.action.refreshFilesExplorer");
        } catch (error) {
            logError("Error refreshing file explorer.", error, "ACT_REFRESH_FILE_EXPLORER");
        }

        window.showInformationMessage("Action Package successfully created in:\n" + targetDir);
    } catch (err) {
        const errorMsg = "Error creating Action Package at: " + targetDir;
        logError(errorMsg, err, "ERR_CREATE_ACTION_PACKAGE");
        OUTPUT_CHANNEL.appendLine(errorMsg);
        window.showErrorMessage(errorMsg + " (see `OUTPUT > Sema4.ai` for more details).");
    }
}

async function getTemplate(actionServerLocation: string) {
    const listActionTemplatesResult: ActionResult<ActionTemplate[]> = await commands.executeCommand(
        roboCommands.SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL,
        {
            "action_server_location": actionServerLocation,
        }
    );

    if (!listActionTemplatesResult.success) {
        window.showErrorMessage("Unable to list Action Package templates: " + listActionTemplatesResult.message);

        return null;
    }

    const templates = listActionTemplatesResult.result;
    if (!templates) {
        window.showErrorMessage("Unable to create Action Package (the Action Package templates could not be loaded).");
        return null;
    }

    const selectedItem = await window.showQuickPick(
        templates.map((template) => template.description),
        {
            canPickMany: false,
            "placeHolder": "Please select the template for the Action Package.",
            "ignoreFocusOut": true,
        }
    );

    const selectedTemplate = templates.find((template) => template.description === selectedItem);
    return selectedTemplate?.name;
}

const chooseOrganization = async (
    organizations: ActionServerListOrganizationsOutput
): Promise<ActionServerOrganization> => {
    const organization = await window.showQuickPick(
        organizations.map((organization) => organization.name),
        {
            "canPickMany": false,
            "placeHolder": "Select the organization to publish package to",
            "ignoreFocusOut": true,
        }
    );

    return organizations.find((org) => org.name == organization);
};

const buildPackage = async (actionServerLocation: string, workspaceDir: string, outputDir: string): Promise<string> => {
    const result: ActionResult<ActionServerPackageBuildOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL,
        {
            action_server_location: actionServerLocation,
            workspace_dir: workspaceDir,
            output_dir: outputDir,
        }
    );
    if (!result.success) {
        window.showErrorMessage(`Failed to upload action package: ${result.message}`);
        return;
    }

    return result.result.package_path;
};

const askUserForChangelogInput = async (): Promise<string> => {
    return window.showInputBox({
        "placeHolder": "Changelog update...",
        "prompt": "Please provide the changelog update for the package.",
        "ignoreFocusOut": true,
        "validateInput": (changelog: string): string | Thenable<string> => {
            if (!changelog) {
                return "No value added";
            }
        },
    });
};

const uploadActionPackage = async (
    actionServerLocation: string,
    packagePath: string,
    organizationId: string
): Promise<ActionServerPackageUploadStatusOutput | undefined> => {
    const result: ActionResult<ActionServerPackageUploadStatusOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL,
        {
            action_server_location: actionServerLocation,
            package_path: packagePath,
            organization_id: organizationId,
        }
    );
    if (!result.success) {
        window.showErrorMessage(`Failed to upload action package: ${result.message}`);
        return;
    }

    return result.result;
};

const getActionPackageStatus = async (
    actionServerLocation: string,
    actionPackageId: string,
    organizationId: string
): Promise<ActionServerPackageUploadStatusOutput> => {
    const result: ActionResult<ActionServerPackageUploadStatusOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL,
        {
            action_server_location: actionServerLocation,
            package_id: actionPackageId,
            organization_id: organizationId,
        }
    );
    if (!result.success) {
        window.showErrorMessage(`Failed to get action package status: ${result.message}`);
        return;
    }

    return result.result;
};

const waitUntilPackageVerified = async (
    actionServerLocation: string,
    actionPackage: ActionServerPackageUploadStatusOutput,
    organizationId: string,
    progress: Progress<{ message?: string; increment?: number }>
): Promise<boolean> => {
    let status = "unknown";
    let timedOut = false;

    const timeout = setTimeout(() => {
        timedOut = true;
    }, 1000 * 60 * 15); // fifteen minutes

    try {
        while (status !== "published" && status !== "completed" && !timedOut) {
            const packageStatus = await getActionPackageStatus(actionServerLocation, actionPackage.id, organizationId);
            status = packageStatus.status;
            progress.report({ message: `Status - ${status}` });

            if (status === "failed") {
                window.showErrorMessage(
                    `Action package failed to be uploaded: ${packageStatus.error || "unknown error"}`
                );
                if (timeout) {
                    clearTimeout(timeout);
                }
                return false;
            }
        }

        if (timedOut) {
            window.showErrorMessage(`Action package verification timed out, see status from: ${actionPackage.url}`);
            return false;
        }
    } finally {
        if (timeout) {
            clearTimeout(timeout);
        }
    }

    return true;
};

const updateChangelog = async (
    actionServerLocation: string,
    packageId: string,
    organizationId: string,
    changelogInput: string
): Promise<boolean> => {
    const result: ActionResult<void> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL,
        {
            action_server_location: actionServerLocation,
            package_id: packageId,
            organization_id: organizationId,
            changelog_input: changelogInput,
        }
    );

    if (!result.success) {
        window.showErrorMessage(`Failed to update the changelog: ${result.message}`);
        return false;
    }

    return true;
};

const createMetadataFile = async (
    actionServerLocation: string,
    actionPackagePath: string,
    outputFilePath: string
): Promise<boolean> => {
    const result: ActionResult<void> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL,
        {
            action_server_location: actionServerLocation,
            action_package_path: actionPackagePath,
            output_file_path: outputFilePath,
        }
    );

    if (!result.success) {
        window.showErrorMessage(`Failed to create the metadata file: ${result.message}`);
        return false;
    }

    return true;
};

export const publishActionPackage = async (actionPackagePath?: vscode.Uri) => {
    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Publishing Action Package",
            cancellable: false,
        },
        async (
            progress: Progress<{ message?: string; increment?: number }>,
            token: CancellationToken
        ): Promise<void> => {
            if (!actionPackagePath) {
                progress.report({ message: "Choose action package" });
                actionPackagePath = await findActionPackagePath();
                if (!actionPackagePath) {
                    return;
                }
            }

            progress.report({ message: "Validating action server" });
            const actionServerLocation = await downloadOrGetActionServerLocation();
            if (!actionServerLocation) {
                return;
            }

            progress.report({ message: "Validating authentication" });
            const verifyLoginOutput = await verifyLogin(actionServerLocation);
            if (!verifyLoginOutput || !verifyLoginOutput.logged_in) {
                window.showErrorMessage(
                    "Action Server Not authenticated to Control Room, run: Sema4ai: Authenticate the Action Server to Control Room"
                );
                return;
            }

            progress.report({ message: "Finding organizations" });
            const organizations = await listOrganizations(actionServerLocation);
            if (organizations.length === 0) {
                return;
            }

            progress.report({ message: "Choose organization" });
            const organization = await chooseOrganization(organizations);
            if (!organization) {
                return;
            }

            progress.report({ message: "Input changelog entry" });
            const changelogInput = await askUserForChangelogInput();
            if (!changelogInput) {
                return;
            }

            const tempDir = path.join(os.tmpdir(), "vscode-extension", Date.now().toString());
            try {
                fs.mkdirSync(tempDir, { recursive: true });

                progress.report({ message: "Building package" });
                const packagePath = await buildPackage(actionServerLocation, actionPackagePath.fsPath, tempDir);
                if (!packagePath) {
                    return;
                }

                progress.report({ message: "Uploading package to Control Room" });
                const actionPackage = await uploadActionPackage(actionServerLocation, packagePath, organization.id);
                if (!actionPackage) {
                    return;
                }

                progress.report({ message: "Waiting for package to be verified" });
                const verified = await waitUntilPackageVerified(
                    actionServerLocation,
                    actionPackage,
                    organization.id,
                    progress
                );
                if (!verified) {
                    return;
                }

                progress.report({ message: "Updating the package changelog to Control Room" });
                const updated = await updateChangelog(
                    actionServerLocation,
                    actionPackage.id,
                    organization.id,
                    changelogInput
                );
                if (!updated) {
                    return;
                }
            } catch (error) {
                window.showErrorMessage(`Failed to publish action package: ${error.message}`);
                return;
            } finally {
                try {
                    fs.rmSync(tempDir, { recursive: true, force: true });
                } catch (error) {
                    // pass the warning, the OS will handle the temp dir deletion if it cannot be deleted here for some reason
                }
            }
            window.showInformationMessage("Package published successfully!");
        }
    );
};

export const buildActionPackage = async (actionPackagePath?: vscode.Uri) => {
    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Build Action Package",
            cancellable: false,
        },
        async (
            progress: Progress<{ message?: string; increment?: number }>,
            token: CancellationToken
        ): Promise<void> => {
            if (!actionPackagePath) {
                progress.report({ message: "Choose action package" });
                actionPackagePath = await findActionPackagePath();
                if (!actionPackagePath) {
                    return;
                }
            }

            progress.report({ message: "Validating action server" });
            const actionServerLocation = await downloadOrGetActionServerLocation();
            if (!actionServerLocation) {
                return;
            }

            progress.report({ message: "Building package" });
            const packagePath = await buildPackage(
                actionServerLocation,
                actionPackagePath.fsPath,
                actionPackagePath.fsPath
            );
            if (!packagePath) {
                return;
            }

            window.showInformationMessage("Action Package built successfully to the workspace.");
        }
    );
};

const createMetadata = async (actionPackagePath: string, outputFilePath: string): Promise<boolean> => {
    return window.withProgress<boolean>(
        {
            location: ProgressLocation.Notification,
            title: "Create Metadata",
            cancellable: false,
        },
        async (
            progress: Progress<{ message?: string; increment?: number }>,
            token: CancellationToken
        ): Promise<boolean> => {
            progress.report({ message: "Validating action server" });
            const actionServerLocation = await downloadOrGetActionServerLocation();
            if (!actionServerLocation) {
                return false;
            }

            progress.report({ message: "Creating metadata.json (please wait, this can take a long time)" });
            const ok = await createMetadataFile(actionServerLocation, actionPackagePath, outputFilePath);
            if (!ok) {
                return false;
            }

            return true;
        }
    );
};

export const openMetadata = async (actionPackagePath?: vscode.Uri) => {
    if (!actionPackagePath) {
        actionPackagePath = await findActionPackagePath();
        if (!actionPackagePath) {
            return;
        }
    }

    try {
        const package_folder = path.basename(actionPackagePath.fsPath);
        const metadataFilePath = path.join(os.tmpdir(), package_folder, `metadata.json`);
        const created = await createMetadata(actionPackagePath.fsPath, metadataFilePath);
        if (created) {
            const document = await vscode.workspace.openTextDocument(metadataFilePath);
            await window.showTextDocument(document, { preview: false });
        } // Error handled in the createMetadata function
    } catch (error) {
        window.showErrorMessage(`Failed to open metadata.json: ${error.message}`);
    }
};
