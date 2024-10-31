import { ProcessExecution, Task, TaskDefinition, tasks, window, WorkspaceFolder } from "vscode";
import { askForActionPackageAndDevTask } from "./actionPackage";
import { langServer } from "../extension";
import { ActionResult } from "../protocols";
import { askForWs } from "../ask";

export interface DevTaskInfo {
    packageYamlPath: string;
    taskName: string;
}

export const runActionPackageDevTask = async (devTaskInfo: DevTaskInfo | undefined) => {
    if (!devTaskInfo) {
        devTaskInfo = {
            packageYamlPath: undefined,
            taskName: undefined,
        };
    }

    if (!devTaskInfo.packageYamlPath && devTaskInfo.taskName) {
        // This would be an error in the caller!
        window.showErrorMessage(
            "Unable to run Action Package dev task: The task name was provided, but the package.yaml file path was not."
        );
        return;
    }

    if (!devTaskInfo.packageYamlPath) {
        // TODO: Filter based on the active text editor.
        // const activeTextEditor = window.activeTextEditor;
        // if (activeTextEditor && activeTextEditor.document && activeTextEditor.document.fileName) {
        //     if (activeTextEditor.document.fileName.endsWith("package.yaml")) {
        //         devTaskInfo.packageYamlPath = activeTextEditor.document.fileName;
        //     }
        // }

        if (!devTaskInfo.packageYamlPath) {
            // We don't even have an active package.yaml file opened. This means we have to ask the user to
            // select an action package first.
            const selection = await askForActionPackageAndDevTask();
            if (!selection) {
                return;
            }
            devTaskInfo.packageYamlPath = selection.actionPackageYaml;
            devTaskInfo.taskName = selection.taskName;
        }
    }

    const { packageYamlPath, taskName } = devTaskInfo;

    const definition: DevTaskDefinition = {
        type: "Sema4.ai: dev-task",
    };

    let ws: WorkspaceFolder | undefined = await askForWs();
    if (!ws) {
        // Operation cancelled.
        return;
    }
    const result: ActionResult<undefined> = await langServer.sendRequest("computeDevTaskSpecToRun", {
        "package_yaml_path": packageYamlPath,
        "task_name": taskName,
    });

    if (!result.success) {
        window.showErrorMessage(result.message);
        return;
    }

    const processExecutionInfo: ProcessExecutionInfo = result.result;
    if (!processExecutionInfo) {
        window.showErrorMessage("Unable to run Action Package dev task: The task specification is missing.");
        return;
    }

    const processExecution: ProcessExecution = new ProcessExecution(
        processExecutionInfo.program,
        processExecutionInfo.args,
        { cwd: processExecutionInfo.cwd, env: processExecutionInfo.env }
    );
    tasks.executeTask(new Task(definition, ws, `Sema4.ai dev-task: ${taskName}`, "dev-task", processExecution));
};

interface DevTaskDefinition extends TaskDefinition {}

interface ProcessExecutionInfo {
    cwd: string;
    program: string;
    args: string[];
    env: Record<string, string>;
}
