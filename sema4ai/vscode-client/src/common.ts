import * as roboCommands from "./robocorpCommands";
import * as vscode from "vscode";
import { commands, FileType, Uri, window, WorkspaceFolder } from "vscode";
import { ActionResult, LocalPackageMetadataInfo, PackageType, PackageYamlName } from "./protocols";
import { logError } from "./channel";
import { feedbackRobocorpCodeError } from "./rcc";
import { join } from "path";
import { uriExists } from "./files";

export type GetPackageTargetDirectoryMessages = {
    title: string;
    useWorkspaceFolderPrompt: string;
    useChildFolderPrompt: string;
    provideNamePrompt: string;
};

export type WorkspacePackagesInfo = {
    agentPackages: LocalPackageMetadataInfo[];
    taskActionPackages: LocalPackageMetadataInfo[];
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
}

export const isActionPackage = (entry: PackageEntry | LocalPackageMetadataInfo) => {
    return entry.filePath.endsWith("package.yaml");
};

export const isAgentPackage = (entry: PackageEntry | LocalPackageMetadataInfo) => {
    return entry.filePath.endsWith("agent-spec.yaml");
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

export async function getPackageTargetDirectory(
    ws: WorkspaceFolder,
    messages: GetPackageTargetDirectoryMessages
): Promise<string | null> {
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

        /* Operation cancelled. */
        if (!target) {
            return null;
        }

        useWorkspaceFolder = target["label"] === useWorkspaceFolderLabel;
    }

    if (!useWorkspaceFolder) {
        const name = await getPackageDirectoryName(messages.provideNamePrompt);

        /* Operation cancelled. */
        if (!name) {
            return null;
        }

        return join(ws.uri.fsPath, name);
    }

    return ws.uri.fsPath;
}

export async function getPackageDirectoryName(prompt: string): Promise<string | null> {
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
