import * as vscode from "vscode";
import { commands, FileType, Uri, window, WorkspaceFolder } from "vscode";
import { PackageType, PackageYamlName } from "./protocols";
import { logError } from "./channel";
import { join } from "path";
import { uriExists } from "./files";

export type GetPackageTargetDirectoryMessages = {
    title: string;
    useWorkspaceFolderPrompt: string;
    useChildFolderPrompt: string;
    provideNamePrompt: string;
    commandType: string;
};

export type PackageTargetAndNameResult = {
    targetDir: string | null;
    name: string | null;
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

    const useWorkspaceFolder = target["label"] === useWorkspaceFolderLabel;

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

export async function getPackageYamlNameFromDirectory(uri: Uri): Promise<string | null> {
    for (const name of [PackageYamlName.Task, "conda.yaml"]) {
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
                    " because this workspace folder is already a Task Package (nested Packages are not allowed)."
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
