import * as vscode from "vscode";
import { OUTPUT_CHANNEL, logError } from "./channel";
import { uriExists } from "./files";
import { LocalPackageMetadataInfo, ActionResult, IActionInfo } from "./protocols";
import * as roboCommands from "./robocorpCommands";
import { basename, RobotEntry, RobotEntryType } from "./viewsCommon";
import { getSelectedRobot } from "./viewsSelection";
import { isActionPackage, isAgentPackage } from "./common";
import path = require("path");

let _globalSentMetric: boolean = false;

function empty<T>(array: T[]) {
    return array === undefined || array.length === 0;
}

function getRobotLabel(robotInfo: LocalPackageMetadataInfo): string {
    let label: string = undefined;
    if (robotInfo.yamlContents) {
        if (isActionPackage(robotInfo) || isAgentPackage(robotInfo)) {
            label = robotInfo.name;
        } else {
            label = robotInfo.yamlContents["name"];
        }
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

    public onAgentsTreeSelectionChanged() {
        this.fireRootChange();
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
                    "No Task nor Action Package found.",
                    "A few ways to get started:",
                    "➔ Run the “Sema4.ai: Create Agent Package”",
                    "➔ Run the “Sema4.ai: Create Action Package”",
                    "➔ Run the “Sema4.ai: Create Task Package”",
                    "➔ Open an Agent Package folder (with a “agent-spec.yaml” file)",
                    "➔ Open an Action Package folder (with a “package.yaml” file)",
                    "➔ Open a Task Package folder (with a “robot.yaml” file)",
                    "➔ Open a parent folder (with multiple Agent/Action/Task Packages)",
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
                return [
                    {
                        "label": "Run Task",
                        "uri": element.uri,
                        "robot": element.robot,
                        "taskName": element.taskName,
                        "iconPath": "run",
                        "type": RobotEntryType.Run,
                        "parent": element,
                    },
                    {
                        "label": "Debug Task",
                        "uri": element.uri,
                        "robot": element.robot,
                        "taskName": element.taskName,
                        "iconPath": "debug",
                        "type": RobotEntryType.Debug,
                        "parent": element,
                    },
                ];
            } else if (element.type === RobotEntryType.Action) {
                return [
                    {
                        "label": "Run Action",
                        "uri": element.uri,
                        "robot": element.robot,
                        "actionName": element.actionName,
                        "iconPath": "run",
                        "type": RobotEntryType.RunAction,
                        "parent": element,
                    },
                    {
                        "label": "Debug Action",
                        "uri": element.uri,
                        "robot": element.robot,
                        "actionName": element.actionName,
                        "iconPath": "debug",
                        "type": RobotEntryType.DebugAction,
                        "parent": element,
                    },
                ];
            } else if (element.type === RobotEntryType.ActionPackage) {
                let children: RobotEntry[] = [
                    {
                        "label": "Configure Action Package",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "go-to-file",
                        "type": RobotEntryType.OpenPackageYaml,
                        "parent": element,
                    },
                ];

                try {
                    let result: ActionResult<undefined> = await vscode.commands.executeCommand(
                        roboCommands.SEMA4AI_LIST_ACTIONS_INTERNAL,
                        {
                            "action_package": element.uri.toString(),
                        }
                    );
                    if (result.success) {
                        let actions: IActionInfo[] = result.result;
                        const iconMapping = {
                            "query": "database",
                            "predict": "eye",
                            "action": "circle",
                        };
                        for (const action of actions) {
                            const uri = vscode.Uri.parse(action.uri);
                            children.push({
                                "label": action.name,
                                "actionName": action.name,
                                "robot": element.robot,
                                "uri": uri,
                                "action_package_uri": element.uri,
                                "iconPath": iconMapping[action.kind],
                                "type": RobotEntryType.Action,
                                "parent": element,
                                "range": action.range,
                                "collapsed": true,
                            });
                        }
                    }
                } catch (error) {
                    logError("Error collecting actions.", error, "ACT_COLLECT_ACTIONS");
                }
                children.push({
                    "label": "Commands",
                    "uri": element.uri,
                    "robot": element.robot,
                    "iconPath": "tools",
                    "type": RobotEntryType.ActionsInActionPackage,
                    "parent": element,
                    "collapsed": false,
                });
                return children;
            } else if (element.type === RobotEntryType.ActionsInAgentPackage) {
                return [
                    {
                        "label": "Export Agent Package (zip)",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "desktop-download",
                        "type": RobotEntryType.ExportAgentPackage,
                        "parent": element,
                        "tooltip": "Exports the Agent Package as a ZIP archive",
                    },
                    {
                        "label": "Publish to Sema4.ai Studio",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "desktop-download",
                        "type": RobotEntryType.PublishAgentToSema4AIStudioApp,
                        "parent": element,
                        "tooltip": "Publishes the Agent Package to the Sema4.ai Studio application",
                    },
                    {
                        "label": "Import Action Package",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "desktop-download",
                        "type": RobotEntryType.ImportActionPackage,
                        "parent": element,
                        "tooltip": "Imports an Action Package into the Agent Package",
                    },
                    {
                        "label": "Create Action Package",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "file-directory-create",
                        "type": RobotEntryType.CreateActionPackage,
                        "parent": element,
                        "tooltip": "Creates an Action Package inside the Agent Package",
                    },
                    {
                        "label": "Update Agent Version",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "versions",
                        "type": RobotEntryType.UpdateAgentVersion,
                        "parent": element,
                        "tooltip": "Updates the Agent Package version in the agent-spec.yaml",
                    },
                    {
                        "label": "Refresh Agent Configuration",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "refresh",
                        "type": RobotEntryType.RefreshAgentConfiguration,
                        "parent": element,
                        "tooltip": "Updates the agent-spec.yaml with the information we have on the file system",
                    },
                ];
            } else if (element.type === RobotEntryType.ActionsInActionPackage) {
                return [
                    {
                        "label": "Start Action Server",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "tools",
                        "type": RobotEntryType.StartActionServer,
                        "parent": element,
                        "tooltip": "Start the Action Server for the actions in the action package",
                    },
                    {
                        "label": "Rebuild Package Environment",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "sync",
                        "type": RobotEntryType.PackageRebuildEnvironment,
                        "parent": element,
                        "tooltip": "Rebuilds the current Python package environment",
                    },
                    ...(element.parent?.parent?.label.toLowerCase().replace(".", "") !== "sema4ai"
                        ? [
                              {
                                  "label": "Publish to Sema4.ai Studio",
                                  "uri": element.uri,
                                  "robot": element.robot,
                                  "iconPath": "desktop-download",
                                  "type": RobotEntryType.PackagePublishToSema4AIStudioApp,
                                  "parent": element,
                                  "tooltip": "Publishes the Action Package to the Sema4.ai Studio application",
                              },
                              {
                                  "label": "Build Action Package (zip)",
                                  "uri": element.uri,
                                  "robot": element.robot,
                                  "iconPath": "archive",
                                  "type": RobotEntryType.PackageBuildToWorkspace,
                                  "parent": element,
                                  "tooltip": "Builds the Action Package .zip file in the workspace folder",
                              },
                          ]
                        : []),
                    {
                        "label": "Preview the Package OpenAPI Spec (metadata.json)",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "new-file",
                        "type": RobotEntryType.PackageMetadata,
                        "parent": element,
                        "tooltip": "Preview the Action Package OpenAPI spec (metadata.json) file",
                    },
                ];
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
                        "label": "Upload Task Package to Control Room",
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
                    {
                        "label": "Open Flow Explorer",
                        "uri": element.uri,
                        "robot": element.robot,
                        "iconPath": "type-hierarchy-sub",
                        "type": RobotEntryType.OpenFlowExplorer,
                        "parent": element,
                    },
                ];
            } else if (element.type === RobotEntryType.AgentPackageOrganizationForActions) {
                const ret = [];
                const collapsed = true;
                for (const actionPackageInfo of element["actionPackages"]) {
                    ret.push(this.createNodeFromPackage(element, collapsed, actionPackageInfo));
                }
                return ret;
            } else if (element.type === RobotEntryType.AgentPackage) {
                const ret = [];
                ret.push({
                    "label": "Configure Agent",
                    "uri": element.uri,
                    "robot": element.robot,
                    "iconPath": "go-to-file",
                    "type": RobotEntryType.OpenAgentSpecYaml,
                    "parent": element,
                });
                ret.push({
                    "label": "Edit Runbook",
                    "uri": element.uri,
                    "robot": element.robot,
                    "iconPath": "go-to-file",
                    "type": RobotEntryType.OpenRunbook,
                    "parent": element,
                });

                if (element.robot.organizations) {
                    for (const org of element.robot.organizations) {
                        ret.push({
                            "label": org["name"],
                            "uri": element.uri,
                            "robot": element.robot,
                            "iconPath": "list-tree",
                            "type": RobotEntryType.AgentPackageOrganizationForActions,
                            "parent": element,
                            "actionPackages": org["actionPackages"],
                        });
                    }
                }
                ret.push({
                    "label": "Commands",
                    "uri": element.uri,
                    "robot": element.robot,
                    "iconPath": "tools",
                    "type": RobotEntryType.ActionsInAgentPackage,
                    "parent": element,
                    "collapsed": false,
                });
                return ret;
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
        const isAgent = isAgentPackage(robotInfo);
        const isAction = isActionPackage(robotInfo);

        return {
            "label": getRobotLabel(robotInfo),
            "uri": vscode.Uri.file(robotInfo.filePath),
            "robot": robotInfo,
            "iconPath": isAgent ? "person" : isAction ? "symbol-event" : "package",
            "type": isAgent
                ? RobotEntryType.AgentPackage
                : isAction
                ? RobotEntryType.ActionPackage
                : RobotEntryType.Robot,
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
        } else if (element.type === RobotEntryType.RunAction) {
            treeItem.command = {
                "title": "Run Action",
                "command": roboCommands.SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
            treeItem.contextValue = "actionItemRun";
        } else if (element.type === RobotEntryType.DebugAction) {
            treeItem.command = {
                "title": "Debug Action",
                "command": roboCommands.SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
            treeItem.contextValue = "actionItemDebug";
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
        } else if (element.type === RobotEntryType.OpenAgentSpecYaml) {
            treeItem.command = {
                "title": "Configure Agent",
                "command": roboCommands.SEMA4AI_OPEN_ROBOT_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.OpenRunbook) {
            treeItem.command = {
                "title": "Edit Runbook",
                "command": roboCommands.SEMA4AI_OPEN_RUNBOOK_TREE_SELECTION,
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
        } else if (element.type === RobotEntryType.OpenPackageYaml) {
            treeItem.command = {
                "title": "Configure Action Package",
                "command": roboCommands.SEMA4AI_OPEN_PACKAGE_YAML_TREE_SELECTION,
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
        } else if (element.type === RobotEntryType.OpenFlowExplorer) {
            treeItem.command = {
                "title": "Open Flow Explorer",
                "command": "robot.openFlowExplorer",
                "arguments": [vscode.Uri.file(element.robot.directory).toString()],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.UploadRobot) {
            treeItem.command = {
                "title": "Upload Robot to Control Room",
                "command": roboCommands.SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION,
                "arguments": [element],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.Robot) {
            treeItem.contextValue = "robotItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.Task) {
            treeItem.contextValue = "taskItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.Action) {
            treeItem.contextValue = "actionItem";
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        } else if (element.type === RobotEntryType.Error) {
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.StartActionServer) {
            treeItem.command = {
                "title": "Start Action Server",
                "command": roboCommands.SEMA4AI_START_ACTION_SERVER,
                "arguments": [vscode.Uri.file(element.robot.directory)],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.PackageRebuildEnvironment) {
            treeItem.command = {
                "title": "Rebuild Package Environment",
                "command": roboCommands.SEMA4AI_PACKAGE_ENVIRONMENT_REBUILD,
                "arguments": [vscode.Uri.file(element.robot.directory)],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.PackagePublishToSema4AIStudioApp) {
            treeItem.command = {
                "title": "Publish Package to Sema4.ai Studio",
                "command": roboCommands.SEMA4AI_ACTION_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP,
                "arguments": [vscode.Uri.file(path.join(element.robot.directory, "package.yaml"))],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.PublishAgentToSema4AIStudioApp) {
            treeItem.command = {
                "title": "Publish Agent Package to Sema4.ai Studio",
                "command": roboCommands.SEMA4AI_AGENT_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP,
                "arguments": [element.robot.directory],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.ImportActionPackage) {
            treeItem.command = {
                "title": "Import Action Package",
                "command": roboCommands.SEMA4AI_IMPORT_ACTION_PACKAGE,
                "arguments": [element.robot.directory],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.ExportAgentPackage) {
            treeItem.command = {
                "title": "Export Agent Package (zip)",
                "command": roboCommands.SEMA4AI_PACK_AGENT_PACKAGE,
                "arguments": [element.robot.directory],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.PackageBuildToWorkspace) {
            treeItem.command = {
                "title": "Build Action Package (zip) in Workspace",
                "command": roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_BUILD,
                "arguments": [vscode.Uri.file(element.robot.directory)],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.PackageMetadata) {
            treeItem.command = {
                "title": "Open the Package OpenAPI Spec (metadata.json)",
                "command": roboCommands.SEMA4AI_ACTION_SERVER_PACKAGE_METADATA,
                "arguments": [vscode.Uri.file(element.robot.directory)],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.CreateActionPackage) {
            treeItem.command = {
                "title": "Create Action Package",
                "command": roboCommands.SEMA4AI_CREATE_ACTION_PACKAGE,
                "arguments": [element.robot],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.UpdateAgentVersion) {
            treeItem.command = {
                "title": "Update Agent Version",
                "command": roboCommands.SEMA4AI_UPDATE_AGENT_VERSION,
                "arguments": [element.robot.directory],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        } else if (element.type === RobotEntryType.RefreshAgentConfiguration) {
            treeItem.command = {
                "title": "Refresh Agent Configuration",
                "command": roboCommands.SEMA4AI_REFRESH_AGENT_SPEC,
                "arguments": [element.robot.directory],
            };
            treeItem.collapsibleState = vscode.TreeItemCollapsibleState.None;
        }
        if (element.tooltip) {
            treeItem.tooltip = element.tooltip;
        }
        if (element.iconPath) {
            if (element.type === RobotEntryType.AgentPackage) {
                treeItem.iconPath = new vscode.ThemeIcon(
                    element.iconPath,
                    new vscode.ThemeColor("textLink.foreground")
                );
            } else {
                treeItem.iconPath = new vscode.ThemeIcon(element.iconPath);
            }
        }
        if (element.collapsed !== undefined) {
            treeItem.collapsibleState = element.collapsed
                ? vscode.TreeItemCollapsibleState.Collapsed
                : vscode.TreeItemCollapsibleState.Expanded;
        }
        return treeItem;
    }
}
