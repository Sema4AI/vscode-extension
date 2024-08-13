import * as vscode from "vscode";
import { RobotEntry, RobotEntryType, treeViewIdToTreeView } from "./viewsCommon";
import { RobotsTreeDataProvider } from "./viewsRobots";

export interface SingleTreeSelectionOpts {
    noSelectionMessage?: string;
    moreThanOneSelectionMessage?: string;
}

function empty<T>(array: readonly T[]) {
    return array === undefined || array.length === 0;
}

const _onSelectedRobotChanged: vscode.EventEmitter<RobotEntry> = new vscode.EventEmitter<RobotEntry>();
export const onSelectedRobotChanged: vscode.Event<RobotEntry> = _onSelectedRobotChanged.event;
let lastSelectedRobot: RobotEntry | undefined = undefined;

/**
 * Returns the selected robot or undefined if there are no robots or if more than one robot is selected.
 * If the messages are passed as a parameter, a warning is shown with that message if the selection is invalid.
 */
export function getSelectedRobot(opts?: SingleTreeSelectionOpts): RobotEntry | undefined {
    let ret = lastSelectedRobot;
    if (!ret) {
        if (opts?.noSelectionMessage) {
            vscode.window.showWarningMessage(opts.noSelectionMessage);
        }
    }
    return ret;
}

function setSelectedRobot(robotEntry: RobotEntry | undefined) {
    lastSelectedRobot = robotEntry;
    _onSelectedRobotChanged.fire(robotEntry);
}

export async function onChangedRobotSelection(
    robotsTree: vscode.TreeView<RobotEntry>,
    treeDataProvider: RobotsTreeDataProvider,
    selection: readonly RobotEntry[]
) {
    if (selection === undefined) {
        selection = [];
    }
    // Remove error nodes from the selection.
    selection = selection.filter((e) => {
        return e.type != RobotEntryType.Error;
    });

    if (empty(selection)) {
        let rootChildren: RobotEntry[] = await treeDataProvider.getValidCachedOrComputeChildren(undefined);
        if (empty(rootChildren)) {
            // i.e.: there's nothing to reselect, so, just notify as usual.
            setSelectedRobot(undefined);
            return;
        }

        // Automatically update selection / reselect some item.
        setSelectedRobot(rootChildren[0]);
        robotsTree.reveal(rootChildren[0], { "select": true });
        return;
    }

    if (!empty(selection)) {
        setSelectedRobot(selection[0]);
        return;
    }

    let rootChildren: RobotEntry[] = await treeDataProvider.getValidCachedOrComputeChildren(undefined);
    if (empty(rootChildren)) {
        // i.e.: there's nothing to reselect, so, just notify as usual.
        setSelectedRobot(undefined);
        return;
    }

    // // Automatically update selection / reselect some item.
    setSelectedRobot(rootChildren[0]);
    robotsTree.reveal(rootChildren[0], { "select": true });
}

export async function getSingleTreeSelection<T>(treeId: string, opts?: any): Promise<T | undefined> {
    const noSelectionMessage: string | undefined = opts?.noSelectionMessage;
    const moreThanOneSelectionMessage: string | undefined = opts?.moreThanOneSelectionMessage;

    const treeView = treeViewIdToTreeView.get(treeId);
    if (!treeView || treeView.selection.length == 0) {
        if (noSelectionMessage) {
            vscode.window.showWarningMessage(noSelectionMessage);
        }
        return undefined;
    }

    if (treeView.selection.length > 1) {
        if (moreThanOneSelectionMessage) {
            vscode.window.showWarningMessage(moreThanOneSelectionMessage);
        }
        return undefined;
    }

    let element = treeView.selection[0];
    return element;
}
