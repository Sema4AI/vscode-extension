import * as vscode from "vscode";
import { OUTPUT_CHANNEL } from "./channel";
import { uriExists } from "./files";
import { LocalPackageMetadataInfo, ActionResult } from "./protocols";
import * as roboCommands from "./robocorpCommands";
import { basename, isRobotFrameworkTask, RobotEntry, RobotEntryType } from "./viewsCommon";
import { getSelectedRobot } from "./viewsSelection";

let _globalSentMetric: boolean = false;

function empty<T>(array: T[]) {
    return array === undefined || array.length === 0;
}

function getRobotLabel(robotInfo: LocalPackageMetadataInfo): string {
    let label: string = undefined;
    if (robotInfo.yamlContents) {
        label = robotInfo.yamlContents["name"];
    }
    if (!label) {
        if (robotInfo.directory) {
            label = basename(robotInfo.directory);
        }
    }
    if (!label) {
        label = "";
    }
    return label;
}

export class RobotsTreeDataProvider implements vscode.TreeDataProvider<RobotEntry> {
    private _onDidChangeTreeData: vscode.EventEmitter<RobotEntry | null> = new vscode.EventEmitter<RobotEntry | null>();
    readonly onDidChangeTreeData: vscode.Event<RobotEntry | null> = this._onDidChangeTreeData.event;

    private _onForceSelectionFromTreeData: vscode.EventEmitter<RobotEntry[]> = new vscode.EventEmitter<RobotEntry[]>();
    readonly onForceSelectionFromTreeData: vscode.Event<RobotEntry[]> = this._onForceSelectionFromTreeData.event;

    private lastRoot: RobotEntry[] | undefined = undefined;

    fireRootChange() {
        this._onDidChangeTreeData.fire(null);
    }

    /**
     * Note that we make sure to only return valid entries here (i.e.: no entries
     * where RobotEntry.type === RobotEntryType.Error).
     */
    async getValidCachedOrComputeChildren(element?: RobotEntry): Promise<RobotEntry[]> {
        if (element === undefined) {
            if (this.lastRoot !== undefined) {
                let ret: RobotEntry[] = this.lastRoot.filter((e) => {
                    return e.type !== RobotEntryType.Error;
                });
                if (ret.length > 0) {
                    // We need to check whether entries still exist.
                    let foundAll: boolean = true;
                    for (const entry of ret) {
                        if (!(await uriExists(entry.uri))) {
                            foundAll = false;
                            break;
                        }
                    }
                    if (foundAll) {
                        return ret;
                    }
                }
            }
        }
        let ret: RobotEntry[] = await this.getChildren(element);
        // Remove any "error" entries
        return ret.filter((e) => {
            return e.type !== RobotEntryType.Error;
        });
    }

    /**
     * This function will compute the children and store the `lastRoot`
     * cache (if element === undefined).
     */
    async getChildren(element?: RobotEntry): Promise<RobotEntry[]> {
        let ret = await this.computeChildren(element);
        if (element === undefined) {
            // i.e.: this is the root entry, so, we've
            // collected the actual robots here.

            let notifySelection = false;
            if (empty(this.lastRoot) && empty(ret)) {
                // Don't notify of anything, nothing changed...
            } else if (empty(this.lastRoot)) {
                // We had nothing and now we have something, notify.
                if (!empty(ret)) {
                    notifySelection = true;
                }
            } else {
                // lastRoot is valid
                // We had something and now we have nothing, notify.
                if (empty(ret)) {
                    notifySelection = true;
                }
            }
            if (!empty(ret) && !notifySelection) {
                // Verify if the last selection is still valid (if it's not we need
                // to notify).
                let currentSelectedRobot = getSelectedRobot();
                let found = false;
                for (const entry of ret) {
                    if (currentSelectedRobot == entry) {
                        found = true;
                    }
                }
                if (!found) {
                    notifySelection = true;
                }
            }
            this.lastRoot = ret;

            if (notifySelection) {
                setTimeout(() => {
                    this._onForceSelectionFromTreeData.fire(this.lastRoot);
                }, 50);
            }

            if (ret.length === 0) {
                // No robot was actually found, so, we'll return a dummy entry
                // giving more instructions to the user.
                let added: boolean = false;
                for (const label of [
                    "No Task Package found.",
                    "A few ways to get started:",
                    "➔ Run the “Sema4.ai: Create Task Package”",
                    "➔ Open a Task Package folder (with a “robot.yaml” file)",
                    "➔ Open a parent folder (with multiple Task Packages)",
                ]) {
                    ret.push({
                        "label": label,
                        "uri": undefined,
                        "robot": undefined,
                        "taskName": undefined,
                        "iconPath": added ? "" : "error",
                        "type": RobotEntryType.Error,
                        "parent": element,
                    });
                    added = true;
                }
            }
        }
        return ret;
    }

    async getParent?(element: RobotEntry): Promise<RobotEntry> {
        return element.parent;
    }

    async computeChildren(element?: RobotEntry): Promise<RobotEntry[]> {
        if (element) {
            // Get child elements.
            if (element.type === RobotEntryType.Task) {
                const taskChildren: RobotEntry[] = [
                    {
                        "label": "Run Task",
                        "uri": element.uri,
                        "robot": element.robot,
                        "taskName": element.taskName,
                        "iconPath": "run",
                        "type": RobotEntryType.Run,
                        "parent": element,
                    },
                ];
                if (!element.isRobotFrameworkTask) {
                    taskChildren.push({
                        "label": "Debug Task",
                        "uri": element.uri,
                        "robot": element.robot,
                        "taskName": element.taskName,
                        "iconPath": "debug",
                        "type": RobotEntryType.Debug,
                        "parent": element,
                    });
                }
                return taskChildren;
            } else if (element.type === RobotEntryType.Robot) {
                let yamlContents = element.robot.yamlContents;
                let robotChildren = [];
                if (yamlContents) {
                    let tasks: object[] = yamlContents["tasks"];
                    if (tasks) {
                        const robotInfo = element.robot;
                        robotChildren = Object.keys(tasks).map((task: string) => ({
                            "label": task,
                            "uri": vscode.Uri.file(robotInfo.filePath),
                            "robot": robotInfo,
                            "taskName": task,
                            "isRobotFrameworkTask": isRobotFrameworkTask(tasks[task]),
                            "iconPath": "debug-alt-small",
                            "type": RobotEntryType.Task,
                            "parent": element,
                        }));
                    }
                }
                robotChildren.push({
                    "label": "Commands",
                    "uri": element.uri,
                    "robot": element.robot,
                    "iconPath": "tools",
                    "type": RobotEntryType.ActionsInRobot,
                    "parent": element,
                    "collapsed": false,
                });
                return robotChildren;
            } else if (element.type === RobotEntryType.ActionsInRobot) {
                return [
                    {
                        "label": "Publish Task Package to Control Room",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "cloud-upload",
                        "type": RobotEntryType.UploadRobot,
                        "parent": element,
                    },
                    {
                        "label": "Open Task Package Terminal",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "terminal",
                        "type": RobotEntryType.RobotTerminal,
                        "parent": element,
                    },
                    {
                        "label": "Configure Tasks (robot.yaml)",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "go-to-file",
                        "type": RobotEntryType.OpenRobotYaml,
                        "parent": element,
                    },
                    {
                        "label": "Configure Dependencies (conda.yaml)",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "list-tree",
                        "type": RobotEntryType.OpenRobotCondaYaml,
                        "parent": element,
                    },
                ];
            } else if (element.type === RobotEntryType.Error) {
                return [];
            }

            OUTPUT_CHANNEL.appendLine("Unhandled in viewsRobots.ts: " + element.type);
            return [];
        }

        if (!_globalSentMetric) {
            _globalSentMetric = true;
            vscode.commands.executeCommand(roboCommands.SEMA4AI_SEND_METRIC, {
                "name": "vscode.treeview.used",
                "value": "1",
            });
        }

        let robotsInfo: LocalPackageMetadataInfo[] = [];

        // Get root elements.
        const actionResult: ActionResult<LocalPackageMetadataInfo[]> = await vscode.commands.executeCommand(
            roboCommands.SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL
        );

        if (!actionResult.success) {
            OUTPUT_CHANNEL.appendLine(actionResult.message);
            return [];
        }

        robotsInfo = actionResult.result;

        if (empty(robotsInfo)) {
            return [];
        }

        const collapsed = robotsInfo.length > 1;

        const ret = [];
        for (const robotInfo of robotsInfo) {
            ret.push(this.createNodeFromPackage(element, collapsed, robotInfo));
        }

        return ret;
    }

    createNodeFromPackage(parent: any, collapsed: boolean, robotInfo: LocalPackageMetadataInfo) {
        return {
            "label": getRobotLabel(robotInfo),
            "uri": vscode.Uri.file(robotInfo.filePath),
            "robot": robotInfo,
            "iconPath": "package",
            "type": RobotEntryType.Robot,
            "parent": parent,
            "collapsed": collapsed,
        };
    }

    getTreeItem(element: RobotEntry): vscode.TreeItem {
        const treeItem = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.Collapsed);
        if (element.type === RobotEntryType.Run) {
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
            treeItem.contextValue = "taskItemRun";
            treeItem.command = {
                "title": "Run",
                "command": roboCommands.SEMA4AI_ROBOTS_VIEW_TASK_RUN,
                "arguments": [element],
            };
        } else if (element.type === RobotEntryType.Debug) {
            treeItem.command = {
                "title": "Debug",
                "command": roboCommands.SEMA4AI_ROBOTS_VIEW_TASK_DEBUG,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
            treeItem.contextValue = "taskItemDebug";
        } else if (element.type === RobotEntryType.ActionsInRobot) {
            treeItem.contextValue = "actionsInRobotItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.OpenRobotYaml) {
            treeItem.command = {
                "title": "Configure Robot (robot.yaml)",
                "command": roboCommands.SEMA4AI_OPEN_ROBOT_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.OpenRobotCondaYaml) {
            treeItem.command = {
                "title": "Configure Dependencies (conda.yaml)",
                "command": roboCommands.SEMA4AI_OPEN_ROBOT_CONDA_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.RobotTerminal) {
            treeItem.command = {
                "title": "Open Robot Terminal",
                "command": roboCommands.SEMA4AI_RCC_TERMINAL_CREATE_ROBOT_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.UploadRobot) {
            treeItem.command = {
                "title": "Publish Task Package to Control Room",
                "command": roboCommands.SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.Robot) {
            treeItem.contextValue = "robotItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.Task) {
            // Robot Framework tasks have no Debug action.
            treeItem.contextValue = element.isRobotFrameworkTask ? "robotFrameworkTaskItem" : "taskItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.Error) {
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        }
        if (element.tooltip) {
            treeItem.tooltip = element.tooltip;
        }
        if (element.iconPath) {
            treeItem.iconPath = new vscode.ThemeIcon(element.iconPath);
        }
        if (element.collapsed !== undefined) {
            treeItem.collapsibleState = element.collapsed
                ? vscode.TreeItemCollapsibleState.Collapsed
                : vscode.TreeItemCollapsibleState.Expanded;
        }
        return treeItem;
    }
}
