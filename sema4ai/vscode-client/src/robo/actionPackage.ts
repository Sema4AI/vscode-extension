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
} from "../protocols";
import {
    getPackageName,
    getPackageTargetDirectoryAndName,
    getPackageYamlNameFromDirectory,
    getWorkspacePackages,
    isActionPackage,
    verifyIfIsPackageDirectory,
    refreshFilesExplorer,
    verifyIfPathOkToCreatePackage,
    isActionPackageCommand,
    PackageTargetAndNameResult,
    toKebabCase,
    isAgentPackage,
} from "../common";
import { slugify } from "../slugify";
import { fileExists, makeDirs } from "../files";
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

    let actionResult: ActionResult<LocalPackageMetadataInfo[]> = await commands.executeCommand(
        roboCommands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL
    );
    if (!actionResult.success) {
        window.showErrorMessage("Error listing Action Packages: " + actionResult.message);
        return;
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
    try {
        const xActionContext = await loginToAuth2WhereRequired(targetInput);
        if (xActionContext) {
            const xActionServerHeader = Buffer.from(JSON.stringify(xActionContext), "utf-8").toString("base64");

            debugConfiguration.baseEnv = { "SEMA4AI-VSCODE-X-ACTION-CONTEXT": xActionServerHeader };
        }
    } catch (error) {
        logError("Error making OAuth2 login", error, "ERR_LOGIN_OAUTH2");
        window.showErrorMessage("Error making OAuth2 login:\n" + error.message);
        return;
    }
    let debugSessionOptions: vscode.DebugSessionOptions = {};
    vscode.debug.startDebugging(undefined, debugConfiguration, debugSessionOptions);
}

async function askActionPackageTargetDir(ws: WorkspaceFolder): Promise<PackageTargetAndNameResult> {
    if (await verifyIfIsPackageDirectory(ws.uri, [PackageYamlName.Agent])) {
        return { targetDir: null, name: null }; // Early return if it's already a package directory
    }

    const [rootPackageYaml, workspacePackages] = await Promise.all([
        getPackageYamlNameFromDirectory(ws.uri),
        getWorkspacePackages(),
    ]);

    const insideAgentPackage = "Inside Agent Package";

    // Case 1: Root level agent, use the agent package directly
    if (rootPackageYaml === PackageYamlName.Agent) {
        return await handleAgentLevelPackageCreation(workspacePackages.agentPackages[0]);
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

        if (!actionPackageLevelSelection) return null; // Operation cancelled

        // If the user wants to create inside an agent package, prompt for which one
        if (actionPackageLevelSelection["label"] === insideAgentPackage) {
            const packageName = await window.showQuickPick(
                workspacePackages.agentPackages.map((pkg) => pkg.name),
                {
                    placeHolder: "Where do you want to create the Action Package?",
                    ignoreFocusOut: true,
                }
            );

            if (!packageName) return { targetDir: null, name: null }; // Operation cancelled

            const packageInfo = workspacePackages.agentPackages.find((pkg) => pkg.name === packageName) || null;
            return await handleAgentLevelPackageCreation(packageInfo);
        }
    }

    // Case 3: Create at the root level, because there's no agent package or the user selected it
    return await handleRootLevelPackageCreation(ws);
}

async function handleRootLevelPackageCreation(ws: WorkspaceFolder): Promise<PackageTargetAndNameResult> {
    return await getPackageTargetDirectoryAndName(ws, {
        title: "Where do you want to create the Action Package?",
        useWorkspaceFolderPrompt: "The workspace will only have a single Action Package.",
        useChildFolderPrompt: "Multiple Action Packages can be created in this workspace.",
        provideNamePrompt: "Please provide the name for the Action Package.",
        commandType: isActionPackageCommand,
    });
}

async function handleAgentLevelPackageCreation(
    packageInfo: LocalPackageMetadataInfo
): Promise<PackageTargetAndNameResult | null> {
    const packageName = await getPackageName("Please provide the name for the Action Package.");
    if (!packageName) return { targetDir: null, name: null }; // Operation cancelled

    const dirName = path.join(packageInfo.directory, "actions", "MyActions", toKebabCase(packageName), "0.0.1");
    return { targetDir: dirName, name: packageName };
}

export async function createActionPackage() {
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

    const { targetDir, name } = await askActionPackageTargetDir(ws);

    // Operation cancelled or directory conflict detected.
    if (!targetDir) {
        return;
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

        refreshFilesExplorer();
        window.showInformationMessage("Action Package successfully created in:\n" + targetDir);
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
