import * as vscode from "vscode";
import { LocalPackageMetadataInfo } from "./protocols";

/**
 * Note: if type is error|info the name is the message to be shown.
 */
export interface LocatorEntry {
    name: string;
    line: number;
    column: number;
    type: string; // "browser", "image", "coordinate", "error", "info",...
    filePath: string;
    tooltip: string | undefined;
}

export const NO_PACKAGE_FOUND_MSG = "No package found in current folder";

/**
 * @TODO:
 * Rename when there is a collective term for Action/Task packages.
 */
export enum RobotEntryType {
    Robot = "Robot",
    Task = "Task",
    Error = "Error",
    Run = "Run",
    Debug = "Debug",
    ActionsInRobot = "ActionsInRobot",
    UploadRobot = "UploadRobot",
    RobotTerminal = "RobotTerminal",
    OpenRobotYaml = "OpenRobotYaml",
    OpenRobotCondaYaml = "OpenRobotCondaYaml",
}

export interface CloudEntry {
    label: string;
    iconPath?: string;
    command?: vscode.Command;
    children?: CloudEntry[];
    viewItemContextValue?: string;
    tooltip?: string;
}

export interface RobotEntry {
    label: string;
    uri: vscode.Uri | undefined;
    robot: LocalPackageMetadataInfo | undefined;
    iconPath: string;
    type: RobotEntryType;
    parent: RobotEntry | undefined;
    collapsed?: boolean | undefined;
    tooltip?: string | undefined;

    // For task
    taskName?: string;
}

export interface FSEntry {
    name: string;
    isDirectory: boolean;
    filePath: string;
}

export const treeViewIdToTreeView: Map<string, vscode.TreeView<any>> = new Map();
export const treeViewIdToTreeDataProvider: Map<string, vscode.TreeDataProvider<any>> = new Map();

export function refreshTreeView(treeViewId: string) {
    let dataProvider: any = <any>treeViewIdToTreeDataProvider.get(treeViewId);
    if (dataProvider) {
        dataProvider.fireRootChange();
    }
}

export function basename(s) {
    return s.split("\\").pop().split("/").pop();
}

export const debounce = (func, wait) => {
    let timeout;

    return function wrapper(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};
