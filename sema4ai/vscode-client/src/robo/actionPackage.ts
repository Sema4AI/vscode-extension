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
import * as roboCommands from "../robocorpCommands";
import {
    ActionResult,
    ActionTemplate,
    IActionInfo,
    LocalPackageMetadataInfo,
    ActionServerListOrganizationsOutput,
    ActionServerOrganization,
    ActionServerPackageBuildOutput,
    ActionServerPackageUploadStatusOutput,
    PackageYamlName,
    PackageType,
} from "../protocols";
import {
    getPackageName,
    getPackageTargetDirectoryAndName,
    getPackageYamlNameFromDirectory,
    getWorkspacePackages,
    isActionPackage,
    verifyIfIsPackageDirectory,
    verifyIfPathOkToCreatePackage,
    PackageTargetAndNameResult,
    toKebabCase,
    isAgentPackage,
    ActionPackageTargetInfo,
    revealInExtension,
} from "../common";
import { slugify } from "../slugify";
import { fileExists, makeDirs, readFromFile, writeToFile } from "../files";
import { QuickPickItemWithAction, askForWs, showSelectOneQuickPick } from "../ask";
import * as path from "path";
import { OUTPUT_CHANNEL, logError } from "../channel";
import {
    downloadOrGetActionServerLocation,
    verifyLogin,
    listOrganizations,
    findActionPackagePath,
} from "../actionServer";
import { loginToAuth2WhereRequired } from "./oauth2InInput";
import { RobotEntryType } from "../viewsCommon";
import { createActionInputs, errorMessageValidatingV2Input } from "./actionInputs";
import { langServer } from "../extension";

export interface QuickPickItemAction extends QuickPickItem {
    actionPackageUri: vscode.Uri;
    actionFileUri: vscode.Uri;
    actionPackageYamlDirectory: string;
    packageYaml: string;
    actionName: string;
    keyInLRU: string;
}

export interface QuickPickItemDevTask extends QuickPickItem {
    taskName: string;
    taskContents: string;
    actionPackageYaml: string;
}

/**
 * Lists all the action packages available in the workspace (both in the current workspace and in the agent packages).
 * @returns The list of action packages or undefined if there was an error.
 */
export async function listAllActionPackages(): Promise<ActionResult<LocalPackageMetadataInfo[]>> {
    let actionResult: ActionResult<LocalPackageMetadataInfo[]> = await commands.executeCommand(
        roboCommands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL
    );
    if (!actionResult.success) {
        return actionResult;
    }
    let robotsInfo: LocalPackageMetadataInfo[] = actionResult.result;
    if (robotsInfo) {
        // Only use action packages.
        const agentPackages = robotsInfo.filter((r) => {
            return isAgentPackage(r);
        });
        robotsInfo = robotsInfo.filter((r) => {
            return isActionPackage(r);
        });

        if (agentPackages) {
            for (const agentPackage of agentPackages) {
                if (agentPackage.organizations) {
                    for (const organization of agentPackage.organizations) {
                        if (organization.actionPackages) {
                            for (const actionPackage of organization.actionPackages) {
                                robotsInfo.push(actionPackage);
                            }
                        }
                    }
                }
            }
        }
    }

    return { success: true, message: undefined, result: robotsInfo };
}

export async function runActionPackageFromFileAndName(noDebug: boolean, fileName: string, actionName: string) {
    let actionPackageYamlDirectory: string | undefined = undefined;
    let packageYaml: string | undefined = undefined;

    // Search the parents of fileName until a package.yaml is found.
    let currentDir = path.dirname(fileName);
    while (true) {
        const potentialPackageYaml = path.join(currentDir, "package.yaml");
        if (await fileExists(potentialPackageYaml)) {
            packageYaml = potentialPackageYaml;
            actionPackageYamlDirectory = currentDir;
            break;
        }
        const oldDir = currentDir;
        currentDir = path.dirname(currentDir);
        if (oldDir === currentDir || currentDir === "/" || !currentDir) {
            break;
        }
    }

    if (!packageYaml || !actionPackageYamlDirectory) {
        window.showErrorMessage("No package.yaml found in the parent directories.");
        return;
    }

    const actionFileUri: vscode.Uri = vscode.Uri.file(fileName);
    await runActionFromActionPackage(noDebug, actionName, actionPackageYamlDirectory, packageYaml, actionFileUri);
}

export interface ActionPackageAndActionResult {
    actionName: string;
    actionPackageYamlDirectory: string;
    packageYaml: string;
    actionFileUri: vscode.Uri;
}

export interface ActionPackageAndDevTaskResult {
    taskName: string;
    taskContents: string;
    actionPackageYaml: string;
}

export async function askForActionPackageAndDevTask(): Promise<ActionPackageAndDevTaskResult | undefined> {
    let actionResult: ActionResult<LocalPackageMetadataInfo[]> = await listAllActionPackages();
    if (!actionResult.success) {
        window.showInformationMessage(actionResult.message);
        return;
    }
    let localActionPackages: LocalPackageMetadataInfo[] = actionResult.result;
    if (localActionPackages.length == 0) {
        window.showInformationMessage(
            "Unable to select Action Package (no Action Packages detected in the Workspace)."
        );
        return;
    }

    let items: QuickPickItemDevTask[] = new Array();

    for (let actionPackage of localActionPackages) {
        try {
            const actionPackageYamlUri = vscode.Uri.file(actionPackage.filePath);
            const result: ActionResult<{ [key: string]: string }> = await langServer.sendRequest("listDevTasks", {
                "action_package_uri": actionPackageYamlUri.toString(),
            });

            if (result.success) {
                let devTasks: { [key: string]: string } = result.result;
                for (const [taskName, taskContents] of Object.entries(devTasks)) {
                    const label = `${actionPackage.name}: ${taskName}`;
                    const item: QuickPickItemDevTask = {
                        "label": label,
                        "taskName": taskName,
                        "taskContents": taskContents,
                        "actionPackageYaml": actionPackage.filePath,
                    };
                    items.push(item);
                }
            } else if (result.message) {
                window.showErrorMessage(result.message);
            }
        } catch (error) {
            logError("Error collecting dev tasks.", error, "ACT_COLLECT_DEV_TASKS");
        }
    }

    if (!items) {
        window.showInformationMessage("Unable to select Dev Task (no Dev Tasks detected in the Workspace).");
        return;
    }

    let selectedItem: QuickPickItemDevTask;
    if (items.length == 1) {
        selectedItem = items[0];
    } else {
        selectedItem = await window.showQuickPick(items, {
            "canPickMany": false,
            "placeHolder": "Please select the Action Package and Dev Task.",
            "ignoreFocusOut": true,
        });
    }

    if (!selectedItem) {
        return;
    }

    const taskName: string = selectedItem.taskName;
    const taskContents: string = selectedItem.taskContents;
    const actionPackageYaml: string = selectedItem.actionPackageYaml;
    return { taskName, taskContents, actionPackageYaml };
}

export async function askForActionPackageAndAction(): Promise<ActionPackageAndActionResult | undefined> {
    const RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE = "RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE";
    let runLRU: string[] = await commands.executeCommand(roboCommands.SEMA4AI_LOAD_FROM_DISK_LRU, {
        "name": RUN_ACTION_FROM_ACTION_PACKAGE_LRU_CACHE,
    });

    let actionResult: ActionResult<LocalPackageMetadataInfo[]> = await listAllActionPackages();
    if (!actionResult.success) {
        window.showInformationMessage(actionResult.message);
        return;
    }
    let robotsInfo: LocalPackageMetadataInfo[] = actionResult.result;
    if (robotsInfo.length == 0) {
        window.showInformationMessage(
            "Unable to select Action Package (no Action Packages detected in the Workspace)."
        );
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
        window.showInformationMessage("Unable to select Action Package (no Action Package detected in the Workspace).");
        return;
    }

    let selectedItem: QuickPickItemAction;
    if (items.length == 1) {
        selectedItem = items[0];
    } else {
        selectedItem = await window.showQuickPick(items, {
            "canPickMany": false,
            "placeHolder": "Please select the Action Package and Action.",
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
    return { actionName, actionPackageYamlDirectory, packageYaml, actionFileUri };
}

export async function askAndRunRobocorpActionFromActionPackage(noDebug: boolean) {
    const selectedActionPackageAndAction = await askForActionPackageAndAction();
    if (!selectedActionPackageAndAction) {
        return;
    }
    const { actionName, actionPackageYamlDirectory, packageYaml, actionFileUri } = selectedActionPackageAndAction;
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
    const multiTargetInput = await getTargetInputJson(actionName, actionPackageYamlDirectory);

    const contents = await readFromFile(multiTargetInput);

    if (!(await fileExists(multiTargetInput)) || contents.length === 0) {
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
            "File input for the action does not exist or is empty. How to proceed?",
            `Customize input for the ${actionName} action`
        );
        if (!selectedItem) {
            return;
        }

        if (selectedItem.action === "create") {
            // Create the file and ask the user to fill it and rerun the action
            // after he finished doing that.
            await createActionInputs(actionFileUri, actionName, multiTargetInput, actionPackageYamlDirectory);
        }
        // In any case, don't proceed if it wasn't previously created
        // (so that the user can customize it).
        return;
    }

    // Now, in the new format, we need to check if the input is in the new format and then extract the input from there
    let input;
    try {
        input = JSON.parse(contents);
    } catch (error) {
        window.showErrorMessage(
            `Unable to run action package: error reading file: ${multiTargetInput} as json: ${error.message}`
        );
        return;
    }
    let targetInput: string;
    const isV2 = input?.metadata?.inputFileVersion === "v2";
    if (!isV2) {
        window.showWarningMessage(
            `The format of the input file is not v2.
Please remove the contents of the file (${multiTargetInput}) and relaunch the action to regenerate
the input file in the new format. The launch will proceed with the current values, but it's
advised to regenerate it as it may not work with future versions of the extension.`
        );
    }
    if (isV2) {
        const errorMessage = errorMessageValidatingV2Input(input);
        if (errorMessage) {
            window.showErrorMessage("Unable to run action package (input file is not valid v2):\n" + errorMessage);
            return;
        }
        // Ok, now, check if we have just one input or multiple (if we have just one, create a temporary file with the input)
        let inputValue;
        if (input.inputs.length === 1) {
            // Create a temporary file with the input
            inputValue = input.inputs[0].inputValue;
        } else {
            // Ask the user to select one of the inputs
            const selectedInput = await window.showQuickPick(
                input.inputs.map((input) => input.inputName),
                {
                    "canPickMany": false,
                    "placeHolder": "Please select the input to use for the action.",
                    "ignoreFocusOut": true,
                }
            );
            if (!selectedInput) {
                return;
            }
            inputValue = input.inputs.find((input) => input.inputName === selectedInput).inputValue;
        }
        const tempInputFile = path.join(os.tmpdir(), `sema4ai_vscode_extension_input_${nameSlugified}.json`);
        await writeToFile(tempInputFile, JSON.stringify(inputValue, null, 4));
        targetInput = tempInputFile;
    } else {
        // No version matched, so, the input is used directly as is (backward compatibility)
        OUTPUT_CHANNEL.appendLine(
            `Expected v2 input file (with metadata.inputFileVersion === "v2"). As it was not found, considering it's an old file and using the input directly as is for the action.`
        );
        targetInput = multiTargetInput;
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
    try {
        const xActionContext = await loginToAuth2WhereRequired(targetInput);
        if (xActionContext) {
            const xActionServerHeader = Buffer.from(JSON.stringify(xActionContext), "utf-8").toString("base64");

            debugConfiguration.baseEnv = { "SEMA4AI_VSCODE_X_ACTION_CONTEXT": xActionServerHeader };
        }
    } catch (error) {
        logError("Error making OAuth2 login", error, "ERR_LOGIN_OAUTH2");
        window.showErrorMessage("Error making OAuth2 login:\n" + error.message);
        return;
    }
    let debugSessionOptions: vscode.DebugSessionOptions = {};
    vscode.debug.startDebugging(undefined, debugConfiguration, debugSessionOptions);
}

export async function askActionPackageTargetDir(
    ws: WorkspaceFolder,
    actionsKind: "sema4ai" | "myaction",
    requestPackageName: boolean
): Promise<ActionPackageTargetInfo> {
    if (await verifyIfIsPackageDirectory(ws.uri, [PackageYamlName.Agent])) {
        return { targetDir: null, name: null, agentSpecPath: null }; // Early return if it's already a package directory
    }

    const [rootPackageYaml, workspacePackages] = await Promise.all([
        getPackageYamlNameFromDirectory(ws.uri),
        getWorkspacePackages(),
    ]);

    const insideAgentPackage = "Inside Agent Package";

    // Case 1: Existing root level agent, use the agent package directly
    if (rootPackageYaml === PackageYamlName.Agent) {
        return await handleAgentLevelPackageCreation(
            workspacePackages.agentPackages[0],
            actionsKind,
            requestPackageName
        );
    }
    // Case 2: Multiple agents, ask the user for action package level selection
    else if (workspacePackages?.agentPackages?.length) {
        const actionPackageLevelSelection = await window.showQuickPick(
            [
                {
                    label: insideAgentPackage,
                    detail: "Action Package will be created inside an Agent Package",
                },
                {
                    label: "Workspace (root) level",
                    detail: "Action Package will be created at workspace root level",
                },
            ],
            {
                placeHolder: "Where do you want to create the Action Package?",
                ignoreFocusOut: true,
            }
        );

        if (!actionPackageLevelSelection) return { targetDir: null, name: null, agentSpecPath: null }; // Operation cancelled

        // If the user wants to create inside an agent package, prompt for which one
        if (actionPackageLevelSelection["label"] === insideAgentPackage) {
            const packageName = await window.showQuickPick(
                workspacePackages.agentPackages.map((pkg) => pkg.name),
                {
                    placeHolder: "In which agent do you want to create the Action Package?",
                    ignoreFocusOut: true,
                }
            );

            if (!packageName) return { targetDir: null, name: null, agentSpecPath: null }; // Operation cancelled

            const packageInfo = workspacePackages.agentPackages.find((pkg) => pkg.name === packageName) || null;
            return await handleAgentLevelPackageCreation(packageInfo, actionsKind, requestPackageName);
        }
    }

    // Case 3: Create at the root level, because there's no agent package or the user selected it
    return {
        ...(await handleRootLevelPackageCreation(ws, requestPackageName)),
        agentSpecPath: null,
    };
}

async function handleRootLevelPackageCreation(
    ws: WorkspaceFolder,
    requestPackageName: boolean
): Promise<PackageTargetAndNameResult> {
    return await getPackageTargetDirectoryAndName(
        ws,
        {
            title: "Where do you want to create the Action Package?",
            useWorkspaceFolderPrompt: "The workspace will only have a single Action Package.",
            useChildFolderPrompt: "Multiple Action Packages can be created in this workspace.",
            provideNamePrompt: "Please provide the name for the Action Package.",
            commandType: PackageType.Action,
        },
        requestPackageName
    );
}

async function handleAgentLevelPackageCreation(
    packageInfo: LocalPackageMetadataInfo,
    actionsKind: "sema4ai" | "myaction",
    requestPackageName: boolean
): Promise<ActionPackageTargetInfo> {
    let packageName;
    if (requestPackageName) {
        packageName = await getPackageName("Please provide the name for the Action Package.");
        if (!packageName) {
            return { targetDir: null, name: null, agentSpecPath: null }; // Operation cancelled
        }
    }

    let dirName;
    if (actionsKind == "myaction") {
        dirName = path.join(packageInfo.directory, "actions", "MyActions");
    } else {
        dirName = path.join(packageInfo.directory, "actions", "Sema4.ai");
    }

    if (requestPackageName) {
        dirName = path.join(dirName, toKebabCase(packageName));
    }

    return {
        targetDir: dirName,
        name: packageName,
        agentSpecPath: vscode.Uri.joinPath(vscode.Uri.file(packageInfo.directory), PackageYamlName.Agent).fsPath,
    };
}

export async function createActionPackage(agentPackage?: LocalPackageMetadataInfo) {
    // We make sure Action Server exists - if not, downloadOrGetActionServerLocation will ask user to download it.
    const actionServerLocation = await downloadOrGetActionServerLocation();
    if (!actionServerLocation) {
        return;
    }

    let ws: WorkspaceFolder | undefined = await askForWs();
    if (!ws) {
        // Operation cancelled.
        return;
    }

    let packageInfo: ActionPackageTargetInfo;
    const requestPackageName = true;
    if (agentPackage) {
        packageInfo = await handleAgentLevelPackageCreation(agentPackage, "myaction", requestPackageName);
    } else {
        packageInfo = await askActionPackageTargetDir(ws, "myaction", requestPackageName);
    }

    const { targetDir, name, agentSpecPath } = packageInfo;

    // Operation cancelled or directory conflict detected.
    if (!targetDir) {
        return;
    }

    // Now, let's validate if we can indeed create an Action Package in the given folder.
    const op = await verifyIfPathOkToCreatePackage(targetDir);
    switch (op) {
        case "force":
            break;
        case "empty":
            break;
        case "cancel":
            return;
        default:
            throw Error("Unexpected result: " + op);
    }

    try {
        /**
         * For versions before 0.10.0, we pass empty string, to indicate no template.
         * It will be handled internally by the language server.
         */
        const template = await getTemplate();
        if (!template) {
            return;
        }

        await makeDirs(targetDir);

        const result: ActionResult<unknown> = await commands.executeCommand(
            roboCommands.SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
            {
                "directory": targetDir,
                "template": template,
                "name": name,
            }
        );

        if (!result.success) {
            throw new Error(result.message || "Unknown error");
        }
        afterActionPackageCreated(targetDir, agentSpecPath);
    } catch (err) {
        const errorMsg = "Error creating Action Package at: " + targetDir;
        logError(errorMsg, err, "ERR_CREATE_ACTION_PACKAGE");
        OUTPUT_CHANNEL.appendLine(errorMsg);
        window.showErrorMessage(errorMsg + " (see `OUTPUT > Sema4.ai` for more details).");
    }
}

async function getTemplate() {
    const listActionTemplatesResult: ActionResult<ActionTemplate[]> = await commands.executeCommand(
        roboCommands.SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL
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

const buildPackage = async (workspaceDir: string, outputDir: string): Promise<string> => {
    const result: ActionResult<ActionServerPackageBuildOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL,
        {
            workspace_dir: workspaceDir,
            output_dir: outputDir,
        }
    );
    if (!result.success) {
        window.showErrorMessage(`Failed to build action package: ${result.message}`);
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
    packagePath: string,
    organizationId: string
): Promise<ActionServerPackageUploadStatusOutput | undefined> => {
    const result: ActionResult<ActionServerPackageUploadStatusOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL,
        {
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
    actionPackageId: string,
    organizationId: string
): Promise<ActionServerPackageUploadStatusOutput> => {
    const result: ActionResult<ActionServerPackageUploadStatusOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL,
        {
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
            const packageStatus = await getActionPackageStatus(actionPackage.id, organizationId);
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

const updateChangelog = async (packageId: string, organizationId: string, changelogInput: string): Promise<boolean> => {
    const result: ActionResult<void> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL,
        {
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

const createMetadataFile = async (actionPackagePath: string, outputFilePath: string): Promise<boolean> => {
    const result: ActionResult<void> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL,
        {
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
                actionPackagePath = await findActionPackagePath({ includeSemaOrg: false });
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
            const verifyLoginOutput = await verifyLogin();
            if (!verifyLoginOutput || !verifyLoginOutput.logged_in) {
                window.showErrorMessage(
                    "Action Server Not authenticated to Control Room, run: Sema4ai: Authenticate the Action Server to Control Room"
                );
                return;
            }

            progress.report({ message: "Finding organizations" });
            const organizations = await listOrganizations();
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
                const packagePath = await buildPackage(actionPackagePath.fsPath, tempDir);
                if (!packagePath) {
                    return;
                }

                progress.report({ message: "Uploading package to Control Room" });
                const actionPackage = await uploadActionPackage(packagePath, organization.id);
                if (!actionPackage) {
                    return;
                }

                progress.report({ message: "Waiting for package to be verified" });
                const verified = await waitUntilPackageVerified(actionPackage, organization.id, progress);
                if (!verified) {
                    return;
                }

                progress.report({ message: "Updating the package changelog to Control Room" });
                const updated = await updateChangelog(actionPackage.id, organization.id, changelogInput);
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
                actionPackagePath = await findActionPackagePath({ includeSemaOrg: false });
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
            const packagePath = await buildPackage(actionPackagePath.fsPath, actionPackagePath.fsPath);
            if (!packagePath) {
                return;
            }

            const msg = `Action Package built successfully (in ${packagePath}).`;
            OUTPUT_CHANNEL.appendLine(msg);
            window.showInformationMessage(msg);
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
            const ok = await createMetadataFile(actionPackagePath, outputFilePath);
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

export async function afterActionPackageCreated(targetDir: string, agentSpecPath: string) {
    revealInExtension(targetDir, RobotEntryType.ActionPackage);
    window.showInformationMessage("Action Package successfully created in:\n" + targetDir);

    // Check action was created inside agent, refresh the agent spec to include this action
    if (agentSpecPath) {
        const refreshResult: ActionResult<unknown> = await commands.executeCommand(
            roboCommands.SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL,
            {
                "agent_spec_path": agentSpecPath,
            }
        );
        if (!refreshResult.success) {
            throw new Error(refreshResult.message || "Unknown error");
        }
    }
}

export async function getActionsMetadata(actionPackagePath: string) {
    const metadataResult: ActionResult<{ [key: string]: any }> = await langServer.sendRequest("getActionsMetadata", {
        "action_package_path": actionPackagePath,
    });

    if (!metadataResult["success"]) {
        throw new Error(metadataResult["message"] || "Unknown error");
    }

    const metadata = metadataResult["result"];
    return metadata;
}
