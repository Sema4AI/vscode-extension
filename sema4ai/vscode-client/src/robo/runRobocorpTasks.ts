import { DebugConfiguration, DebugSessionOptions, commands, debug } from "vscode";
import { OUTPUT_CHANNEL, logError } from "../channel";
import { SEMA4AI_RESOLVE_INTERPRETER, SEMA4AI_UPDATE_LAUNCH_ENV } from "../robocorpCommands";
import { ActionResult, InterpreterInfo } from "../protocols";
import * as path from "path";
import { updateDebugConfigurationAndAutoActivatePythonExtension } from "../debugger";

export async function runRobocorpTasks(noDebug: boolean, args: string[]) {
    // Code lens should always make sure that the first arg is the .py
    // to be run.
    const targetPy = args[0];

    let debugConfiguration: DebugConfiguration = {
        "name": "Python: Sema4.ai Tasks",
        "type": "python",
        "request": "launch",
        "module": "robocorp.tasks",
        "args": ["run"].concat(args),
        "justMyCode": true,
        "noDebug": noDebug,
        "cwd": path.dirname(targetPy),
    };

    let interpreterInfo: InterpreterInfo | undefined = undefined;
    try {
        let result: ActionResult<InterpreterInfo | undefined> = await commands.executeCommand(
            SEMA4AI_RESOLVE_INTERPRETER,
            {
                "target_robot": targetPy,
            }
        );
        if (result.success) {
            interpreterInfo = result["result"];
            debugConfiguration.env = interpreterInfo.environ;
            debugConfiguration.python = interpreterInfo.pythonExe;
        } else {
            logError(result.message, undefined, "RESOLVE_INT_RUN_SEMA4AI_TASKS_1");
        }
    } catch (error) {
        logError("Error resolving interpreter.", error, "RESOLVE_INT_RUN_SEMA4AI_TASKS_2");
    }

    // Overridde env variables in the launch config.
    if (interpreterInfo !== undefined) {
        try {
            let newEnv: { [key: string]: string } | "cancelled" = await commands.executeCommand(
                SEMA4AI_UPDATE_LAUNCH_ENV,
                {
                    "targetRobot": targetPy,
                    "env": debugConfiguration.env,
                }
            );
            if (newEnv == "cancelled") {
                OUTPUT_CHANNEL.appendLine("Launch cancelled");
                return undefined;
            }

            debugConfiguration.env = newEnv;
        } catch (error) {
            // The command may not be available.
        }
    }
    let debugSessionOptions: DebugSessionOptions = {};
    debugConfiguration = await updateDebugConfigurationAndAutoActivatePythonExtension(debugConfiguration);
    debug.startDebugging(undefined, debugConfiguration, debugSessionOptions);
}
