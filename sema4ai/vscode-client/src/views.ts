import {
    TREE_VIEW_SEMA4AI_CLOUD_TREE,
    TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE,
    TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE,
    TREE_VIEW_SEMA4AI_PACKAGE_RESOURCES_TREE,
} from "./robocorpViews";
import * as vscode from "vscode";
import { commands, ExtensionContext } from "vscode";
import { runRobotRCC, uploadRobot } from "./activities";
import { createRccTerminal } from "./rccTerminal";
import { RobotContentTreeDataProvider } from "./viewsRobotContent";
import {
    debounce,
    refreshTreeView,
    RobotEntry,
    RobotEntryType,
    treeViewIdToTreeDataProvider,
    treeViewIdToTreeView,
} from "./viewsCommon";
import { getSelectedRobot, onSelectedRobotChanged, onChangedRobotSelection } from "./viewsSelection";
import { CloudTreeDataProvider } from "./viewsRobocorp";
import { RobotsTreeDataProvider } from "./viewsRobots";
import { ResourcesTreeDataProvider } from "./viewsResources";
import * as path from "path";
import { fileExists, uriExists, verifyFileExists } from "./files";
import { getTargetInputJson, runActionFromActionPackage } from "./robo/actionPackage";
import { ActionResult } from "./protocols";
import * as roboCommands from "./robocorpCommands";
import { createActionInputs } from "./robo/actionInputs";

export async function editInput(actionName?: string, actionDirectory?: string) {
    if (!actionName || !actionDirectory) {
        vscode.window.showErrorMessage("Unable to edit input: no target action entry defined for action.");
        return;
    }
    const targetInput = await getTargetInputJson(actionName, actionDirectory);
    let mustCreateInputs = !(await fileExists(targetInput));
    if (!mustCreateInputs) {
        const inputUri = vscode.Uri.file(targetInput);
        // Check if the file is not empty
        const fileContents = await vscode.workspace.fs.readFile(inputUri);
        mustCreateInputs = fileContents.length === 0;
    }
    if (mustCreateInputs) {
        const success = await createActionInputs(
            vscode.Uri.file(actionDirectory),
            actionName,
            targetInput,
            actionDirectory
        );
        if (!success) {
            return;
        }
    }
    const inputUri = vscode.Uri.file(targetInput);
    await vscode.window.showTextDocument(inputUri);
}

export async function openRobotTreeSelection(robot?: RobotEntry) {
    if (!robot) {
        robot = getSelectedRobot();
    }
    if (robot) {
        vscode.window.showTextDocument(robot.uri);
    }
}

export async function openRobotCondaTreeSelection(robot?: RobotEntry) {
    if (!robot) {
        robot = getSelectedRobot();
    }
    if (robot) {
        const yamlContents = robot.robot.yamlContents;
        if (yamlContents) {
            const condaConfigFile = yamlContents["condaConfigFile"];
            if (condaConfigFile) {
                vscode.window.showTextDocument(vscode.Uri.file(path.join(robot.robot.directory, condaConfigFile)));
                return;
            }
        }

        // It didn't return: let's just check for a conda.yaml.
        const condaYamlPath = path.join(robot.robot.directory, "conda.yaml");
        const condaYamlUri = vscode.Uri.file(condaYamlPath);
        if (await uriExists(condaYamlUri)) {
            vscode.window.showTextDocument(condaYamlUri);
            return;
        }
    }
}

export async function openPackageTreeSelection(robot?: RobotEntry) {
    if (!robot) {
        robot = getSelectedRobot();
    }
    if (robot) {
        const packageYamlPath = path.join(robot.robot.directory, "package.yaml");
        const packageYamlUri = vscode.Uri.file(packageYamlPath);
        if (await uriExists(packageYamlUri)) {
            vscode.window.showTextDocument(packageYamlUri);
            return;
        }
    }
}

export async function openRunbookTreeSelection(robot?: RobotEntry) {
    const selectedRobot = robot ?? getSelectedRobot();

    if (!selectedRobot) {
        vscode.window.showErrorMessage("Unable to open runbook: no agent selected.");
        return;
    }

    const agentYamlPath = path.join(selectedRobot.robot.directory, "agent-spec.yaml");
    const agentYamlUri = vscode.Uri.file(agentYamlPath);

    if (!(await uriExists(agentYamlUri))) {
        vscode.window.showErrorMessage(`Agent spec file not found in path: ${agentYamlPath}`);
        return;
    }

    const result: ActionResult<string> = await commands.executeCommand(
        roboCommands.SEMA4AI_GET_RUNBOOK_PATH_FROM_AGENT_SPEC_INTERNAL,
        { agent_spec_path: agentYamlPath }
    );

    if (!result.success) {
        vscode.window.showErrorMessage(`${result.message}`);
        return;
    }

    const fullRunbookPath = path.join(selectedRobot.robot.directory, result.result);
    const runbookUri = vscode.Uri.file(fullRunbookPath);

    if (await uriExists(runbookUri)) {
        vscode.window.showTextDocument(runbookUri);
        return;
    } else {
        vscode.window.showErrorMessage(`Runbook file not found: ${fullRunbookPath}`);
    }
}

export async function openLocatorsJsonTreeSelection() {
    // Json
    const robot = getSelectedRobot();
    if (robot) {
        let locatorJson = path.join(robot.robot.directory, "locators.json");
        if (verifyFileExists(locatorJson, false)) {
            vscode.window.showTextDocument(vscode.Uri.file(locatorJson));
        }
    }
}

export async function cloudUploadRobotTreeSelection(robot?: RobotEntry) {
    if (!robot) {
        robot = getSelectedRobot();
    }
    if (robot) {
        uploadRobot(robot.robot);
    }
}

export async function createRccTerminalTreeSelection(robot?: RobotEntry) {
    if (!robot) {
        robot = getSelectedRobot();
    }
    if (robot) {
        createRccTerminal(robot.robot);
    }
}

export async function runSelectedRobot(noDebug: boolean, taskRobotEntry?: RobotEntry) {
    if (!taskRobotEntry) {
        taskRobotEntry = await getSelectedRobot({
            noSelectionMessage: "Unable to make launch (Task not selected in Packages Tree).",
            moreThanOneSelectionMessage: "Unable to make launch -- only 1 task must be selected.",
        });
    }
    runRobotRCC(noDebug, taskRobotEntry.robot.filePath, taskRobotEntry.taskName);
}

export async function openAction(actionRobotEntry?: RobotEntry) {
    const range = actionRobotEntry.range;
    if (range) {
        const selection: vscode.Range = new vscode.Range(
            new vscode.Position(range.start.line - 1, range.start.character),
            new vscode.Position(range.end.line - 1, range.end.character)
        );
        await vscode.window.showTextDocument(actionRobotEntry.uri, { selection: selection });
    } else {
        await vscode.window.showTextDocument(actionRobotEntry.uri);
    }
}

export async function runSelectedAction(noDebug: boolean, actionRobotEntry?: RobotEntry) {
    if (!actionRobotEntry) {
        actionRobotEntry = await getSelectedRobot({
            noSelectionMessage: "Unable to make launch (Action not selected in Packages Tree).",
            moreThanOneSelectionMessage: "Unable to make launch -- only 1 action must be selected.",
        });
        if (!actionRobotEntry) {
            return;
        }
    }

    if (!actionRobotEntry.actionName) {
        vscode.window.showErrorMessage("actionName not available in entry to launch.");
        return;
    }

    await runActionFromActionPackage(
        noDebug,
        actionRobotEntry.actionName,
        actionRobotEntry.robot.directory,
        actionRobotEntry.robot.filePath,
        actionRobotEntry.uri
    );
}

export function registerViews(context: ExtensionContext) {
    // Cloud data
    const cloudTreeDataProvider = new CloudTreeDataProvider();
    const viewsCloudTree = vscode.window.createTreeView(TREE_VIEW_SEMA4AI_CLOUD_TREE, {
        "treeDataProvider": cloudTreeDataProvider,
    });
    treeViewIdToTreeView.set(TREE_VIEW_SEMA4AI_CLOUD_TREE, viewsCloudTree);
    treeViewIdToTreeDataProvider.set(TREE_VIEW_SEMA4AI_CLOUD_TREE, cloudTreeDataProvider);

    // Robots (i.e.: list of robots, not its contents)
    const robotsTreeDataProvider = new RobotsTreeDataProvider();
    const robotsTree = vscode.window.createTreeView(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE, {
        "treeDataProvider": robotsTreeDataProvider,
    });

    // Periodic refresh every 60 seconds
    setInterval(() => {
        robotsTreeDataProvider.updateDatasourceStatuses();
    }, 5 * 1000);

    treeViewIdToTreeView.set(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE, robotsTree);
    treeViewIdToTreeDataProvider.set(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE, robotsTreeDataProvider);

    context.subscriptions.push(
        robotsTree.onDidChangeSelection(
            async (e) => await onChangedRobotSelection(robotsTree, robotsTreeDataProvider, e.selection)
        )
    );

    context.subscriptions.push(
        robotsTreeDataProvider.onForceSelectionFromTreeData(
            async (e) => await onChangedRobotSelection(robotsTree, robotsTreeDataProvider, robotsTree.selection)
        )
    );

    // Update contexts when the current robot changes.
    context.subscriptions.push(
        onSelectedRobotChanged(async (robotEntry: RobotEntry | undefined) => {
            if (!robotEntry) {
                vscode.commands.executeCommand("setContext", "sema4ai:single-task-selected", false);
                vscode.commands.executeCommand("setContext", "sema4ai:single-robot-selected", false);
                return;
            }
            vscode.commands.executeCommand(
                "setContext",
                "sema4ai:single-task-selected",
                robotEntry.type == RobotEntryType.Task
            );
            vscode.commands.executeCommand("setContext", "sema4ai:single-robot-selected", true);
        })
    );

    // The contents of a single robot (the one selected in the Robots tree).
    const robotContentTreeDataProvider = new RobotContentTreeDataProvider();
    const robotContentTree = vscode.window.createTreeView(TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE, {
        "treeDataProvider": robotContentTreeDataProvider,
    });
    treeViewIdToTreeView.set(TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE, robotContentTree);
    treeViewIdToTreeDataProvider.set(TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE, robotContentTreeDataProvider);

    context.subscriptions.push(
        onSelectedRobotChanged((e) => robotContentTreeDataProvider.onRobotsTreeSelectionChanged(e))
    );
    context.subscriptions.push(
        robotContentTreeDataProvider.onForceSelectionFromTreeData(
            async (e) => await onChangedRobotSelection(robotsTree, robotsTreeDataProvider, robotsTree.selection)
        )
    );

    // Resources
    const resourcesDataProvider = new ResourcesTreeDataProvider();
    const resourcesTree = vscode.window.createTreeView(TREE_VIEW_SEMA4AI_PACKAGE_RESOURCES_TREE, {
        "treeDataProvider": resourcesDataProvider,
        "canSelectMany": true,
    });
    treeViewIdToTreeView.set(TREE_VIEW_SEMA4AI_PACKAGE_RESOURCES_TREE, resourcesTree);
    treeViewIdToTreeDataProvider.set(TREE_VIEW_SEMA4AI_PACKAGE_RESOURCES_TREE, resourcesDataProvider);

    context.subscriptions.push(onSelectedRobotChanged((e) => resourcesDataProvider.onRobotsTreeSelectionChanged(e)));

    const robotsWatcher: vscode.FileSystemWatcher = vscode.workspace.createFileSystemWatcher(
        "**/{robot.yaml,package.yaml,agent-spec.yaml,actions/*}"
    );

    const onChangeRobotsYaml = debounce(() => {
        // Note: this doesn't currently work if the parent folder is renamed or removed.
        // (https://github.com/microsoft/vscode/pull/110858)
        refreshTreeView(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE);
    }, 300);

    robotsWatcher.onDidChange(onChangeRobotsYaml);
    robotsWatcher.onDidCreate(onChangeRobotsYaml);
    robotsWatcher.onDidDelete(onChangeRobotsYaml);

    const locatorsWatcher: vscode.FileSystemWatcher = vscode.workspace.createFileSystemWatcher("**/locators.json");

    const onChangeLocatorsJson = debounce(() => {
        // Note: this doesn't currently work if the parent folder is renamed or removed.
        // (https://github.com/microsoft/vscode/pull/110858)
        refreshTreeView(TREE_VIEW_SEMA4AI_PACKAGE_RESOURCES_TREE);
    }, 300);

    locatorsWatcher.onDidChange(onChangeLocatorsJson);
    locatorsWatcher.onDidCreate(onChangeLocatorsJson);
    locatorsWatcher.onDidDelete(onChangeLocatorsJson);

    context.subscriptions.push(robotsTree);
    context.subscriptions.push(resourcesTree);
    context.subscriptions.push(robotsWatcher);
    context.subscriptions.push(locatorsWatcher);
}
