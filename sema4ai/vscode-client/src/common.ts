import * as roboCommands from "./robocorpCommands";
import * as vscode from "vscode";
import { commands, FileType, Uri, window, WorkspaceFolder } from "vscode";
import { ActionResult, LocalPackageMetadataInfo, PackageType, PackageYamlName } from "./protocols";
import { logError, OUTPUT_CHANNEL } from "./channel";
import { feedbackRobocorpCodeError } from "./rcc";
import { join } from "path";
import { uriExists } from "./files";
import { RobotEntry, RobotEntryType, treeViewIdToTreeDataProvider, treeViewIdToTreeView } from "./viewsCommon";
import { TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE } from "./robocorpViews";
import { RobotsTreeDataProvider } from "./viewsRobots";
import path = require("path");

export type GetPackageTargetDirectoryMessages = {
    title: string;
    useWorkspaceFolderPrompt: string;
    useChildFolderPrompt: string;
    provideNamePrompt: string;
    commandType: string;
};

export type WorkspacePackagesInfo = {
    agentPackages: LocalPackageMetadataInfo[];
    taskActionPackages: LocalPackageMetadataInfo[];
};

export type PackageTargetAndNameResult = {
    targetDir: string | null;
    name: string | null;
};

export type ActionPackageTargetInfo = PackageTargetAndNameResult & {
    agentSpecPath: string | null;
};

export const debounce = (func, wait) => {
    let timeout: NodeJS.Timeout;

    return function wrapper(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

export interface PackageEntry {
    filePath: string;
    packageType?: string;
}

export const isActionPackage = (entry: PackageEntry | LocalPackageMetadataInfo) => {
    return entry.filePath.endsWith("package.yaml");
};

export const isAgentPackage = (entry: PackageEntry | LocalPackageMetadataInfo) => {
    return entry.packageType === PackageType.Agent;
};

export async function getWorkspacePackages(): Promise<WorkspacePackagesInfo> {
    const actionResultListLocalRobots = (await vscode.commands.executeCommand(
        roboCommands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL
    )) as ActionResult<LocalPackageMetadataInfo[]>;

    if (!actionResultListLocalRobots.success) {
        feedbackRobocorpCodeError("ACT_LIST_ROBOT");
        window.showErrorMessage("Error listing robots: " + actionResultListLocalRobots.message);

        // This shouldn't happen, but let's proceed as if there were no Robots in the workspace.
        return {
            agentPackages: [],
            taskActionPackages: [],
        };
    } else {
        return {
            agentPackages: actionResultListLocalRobots.result.filter((data) => {
                return data.packageType === PackageType.Agent;
            }),
            taskActionPackages: actionResultListLocalRobots.result.filter((data) => {
                return data.packageType !== PackageType.Agent;
            }),
        };
    }
}

export async function areTherePackagesInWorkspace(): Promise<boolean> {
    const workspacePackages = await getWorkspacePackages();

    if (!workspacePackages) {
        return false;
    }

    return workspacePackages.taskActionPackages.length > 0 && workspacePackages.agentPackages.length > 0;
}

export function toKebabCase(str: string): string {
    return str
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-") // Replace spaces and non-alphanumeric characters with hyphens
        .replace(/^-+|-+$/g, ""); // Remove leading/trailing hyphens
}

export async function getPackageTargetDirectoryAndName(
    ws: WorkspaceFolder,
    messages: GetPackageTargetDirectoryMessages,
    requestPackageName: boolean
): Promise<PackageTargetAndNameResult> {
    if (!requestPackageName) {
        // When not requesting the package name it's expected that the package name will
        // be added by the caller (so, it's always a child folder of the workspace folder
        // in this case).
        return {
            targetDir: ws.uri.fsPath,
            name: null,
        };
    }

    const packagesInDirectory = await areTherePackagesInWorkspace();

    let useWorkspaceFolder = false;
    if (!packagesInDirectory) {
        const useWorkspaceFolderLabel = "Use workspace folder (recommended)";

        const target = await window.showQuickPick(
            [
                {
                    "label": useWorkspaceFolderLabel,
                    "detail": messages.useWorkspaceFolderPrompt,
                },
                {
                    "label": "Use child folder in workspace (advanced)",
                    "detail": messages.useChildFolderPrompt,
                },
            ],
            {
                "placeHolder": messages.title,
                "ignoreFocusOut": true,
            }
        );

        // Operation cancelled
        if (!target) return { targetDir: null, name: null };

        useWorkspaceFolder = target["label"] === useWorkspaceFolderLabel;
    }

    // If using the workspace folder and it's a task package command, we don't need the name
    if (useWorkspaceFolder && messages.commandType === PackageType.Task) {
        return { targetDir: ws.uri.fsPath, name: null };
    }

    const name = await getPackageName(messages.provideNamePrompt);
    if (!name) return { targetDir: null, name: null }; // Handle cancellation

    return {
        targetDir: useWorkspaceFolder ? ws.uri.fsPath : join(ws.uri.fsPath, toKebabCase(name)),
        name,
    };
}

export async function getPackageName(prompt: string): Promise<string | null> {
    const name = await window.showInputBox({
        "value": "Example",
        "prompt": prompt,
        "ignoreFocusOut": true,
    });

    return name || null;
}

export function refreshFilesExplorer() {
    try {
        commands.executeCommand("workbench.files.action.refreshFilesExplorer");
    } catch (error) {
        logError("Error refreshing file explorer.", error, "ACT_REFRESH_FILE_EXPLORER");
    }
}

export async function revealInExtension(directoryPath: string, entryType: RobotEntryType): Promise<void> {
    const treeView = treeViewIdToTreeView.get(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE);

    if (!treeView.visible) {
        return;
    }

    const dataProvider = treeViewIdToTreeDataProvider.get(
        TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE
    ) as RobotsTreeDataProvider;

    const nodes = await dataProvider.getChildren();
    const normalizedDirectoryPath = path.normalize(directoryPath);

    async function findNode(nodes: RobotEntry[]): Promise<RobotEntry | undefined> {
        for (const node of nodes) {
            if (node.type === entryType && path.normalize(node.robot.directory) === normalizedDirectoryPath) {
                return node;
            }

            const childNodes = await dataProvider.getChildren(node);
            if (childNodes && childNodes.length > 0) {
                const foundChild = await findNode(childNodes);
                if (foundChild) {
                    return foundChild;
                }
            }
        }
        return undefined;
    }

    const node = await findNode(nodes);
    if (node) {
        dataProvider.fireRootChange();
        treeView.reveal(node, { focus: true, expand: true });
    }
}

export async function getPackageYamlNameFromDirectory(uri: Uri): Promise<string | null> {
    for (const name of [PackageYamlName.Agent, PackageYamlName.Action, PackageYamlName.Task, "conda.yaml"]) {
        if (await uriExists(Uri.joinPath(uri, name))) {
            return name;
        }
    }

    return null;
}

export async function verifyIfIsPackageDirectory(wsUri: Uri, ignore: string[] = []): Promise<boolean> {
    // Check if we still don't have a Robot in this folder (i.e.: if we have a Robot in the workspace
    // root already, we shouldn't create another Robot inside it).
    // Note: shows error message to the user.
    try {
        const packageYaml = await getPackageYamlNameFromDirectory(wsUri);

        if (packageYaml && !ignore.includes(packageYaml)) {
            window.showErrorMessage(
                "It's not possible to create a Package in: " +
                    wsUri.fsPath +
                    " because this workspace folder is already a Task, Action or Agent Package (nested Packages are not allowed)."
            );
            return true;
        }
    } catch (error) {
        logError("Error reading contents of: " + wsUri.fsPath, error, "ACT_CREATE_ROBOT");
    }
    return false;
}

export async function verifyIfPathOkToCreatePackage(targetDir: string): Promise<"force" | "empty" | "cancel"> {
    let dirUri = vscode.Uri.file(targetDir);
    let directoryExists = true;
    try {
        let stat = await vscode.workspace.fs.stat(dirUri); // this will raise if the directory doesn't exist.
        if (stat.type == FileType.File) {
            window.showErrorMessage(
                "It's not possible to create a Package in: " +
                    targetDir +
                    " because this points to a file which already exists (please erase this file and retry)."
            );
            return "cancel";
        }
    } catch (err) {
        // ok, directory does not exist
        directoryExists = false;
    }
    let force: boolean = false;
    if (directoryExists) {
        let isEmpty: boolean = true;
        try {
            // The directory already exists, let's see if it's empty (if it's not we need to check
            // whether to force the creation of the Robot).
            let dirContents: [string, FileType][] = await vscode.workspace.fs.readDirectory(dirUri);
            for (const element of dirContents) {
                if (element[0] != ".vscode") {
                    // If there's just a '.vscode', proceed, otherwise,
                    // we need to ask the user about overwriting it.
                    isEmpty = false;
                    break;
                } else {
                    force = true;
                }
            }
        } catch (error) {
            logError("Error reading contents of directory: " + dirUri, error, "ACT_CREATE_ROBOT_LIST_TARGET");
        }
        if (!isEmpty) {
            const CANCEL = "Cancel Package Creation";
            // Check if the user wants to override the contents.
            let target = await window.showQuickPick(
                [
                    {
                        "label": "Create Package anyways",
                        "detail": "The Package will be created and conflicting files will be overwritten.",
                    },
                    {
                        "label": CANCEL,
                        "detail": "No changes will be done.",
                    },
                ],
                {
                    "placeHolder": "The directory is not empty. How do you want to proceed?",
                    "ignoreFocusOut": true,
                }
            );

            if (!target || target["label"] == CANCEL) {
                // Operation cancelled.
                return "cancel";
            }
            force = true;
        }
    }
    if (force) {
        return "force";
    }
    return "empty";
}

export function compareVersions(version1: string, version2: string): number {
    // Example usage:
    // console.log(compareVersions("0.0.3", "4.3.1")); // Output: -1 (0.0.3 < 4.3.1)
    // console.log(compareVersions("4.3.1", "4.4a1")); // Output: -1 (4.3.1 < 4.4a1)
    // console.log(compareVersions("4.5.1", "4.2")); // Output: 1 (4.5.1 > 4.2)
    // console.log(compareVersions("1.0.0", "1.0.0")); // Output: 0 (1.0.0 == 1.0.0)
    // console.log(compareVersions("2.0", "2.0.0")); // Output: 0 (2.0 == 2.0.0)
    const v1Components = version1
        .split(".")
        .map((component) => (isNaN(parseInt(component)) ? component : parseInt(component)));
    const v2Components = version2
        .split(".")
        .map((component) => (isNaN(parseInt(component)) ? component : parseInt(component)));

    const maxLength = Math.max(v1Components.length, v2Components.length);

    for (let i = 0; i < maxLength; i++) {
        const v1Value = v1Components[i] || 0;
        const v2Value = v2Components[i] || 0;

        if (v1Value < v2Value) {
            return -1;
        } else if (v1Value > v2Value) {
            return 1;
        }
    }

    return 0;
}

export async function showErrorMessageWithShowOutputButton(message: string) {
    const result = await window.showErrorMessage(
        message + " (see `OUTPUT > Sema4.ai` for more details).",
        "Open OUTPUT > Sema4.ai"
    );
    if (result === "Open OUTPUT > Sema4.ai") {
        OUTPUT_CHANNEL.show();
    }
}

export async function promptForUnsavedChanges() {
    const unsavedFiles = vscode.workspace.textDocuments.filter((doc) => doc.isDirty && doc.uri.scheme === "file");

    if (unsavedFiles.length > 0) {
        const userResponse = await vscode.window.showWarningMessage(
            `You have unsaved changes. Do you want to save them before proceeding?`,
            { modal: true },
            "Save All",
            "Ignore"
        );

        if (userResponse === "Save All") {
            await vscode.workspace.saveAll();
            vscode.window.showInformationMessage("All files saved.");
        } else if (userResponse === "Ignore") {
            vscode.window.showInformationMessage("Ignoring unsaved files.");
        }
    }
}
