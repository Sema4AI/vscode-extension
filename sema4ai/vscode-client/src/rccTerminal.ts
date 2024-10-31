import { Progress, ProgressLocation, window } from "vscode";
import { OUTPUT_CHANNEL } from "./channel";
import * as pathModule from "path";
import { listAndAskRobotSelection, resolveInterpreter } from "./activities";
import { getRccLocation, getRobocorpHome } from "./rcc";
import { mergeEnviron } from "./subprocess";
import { getAutosetpythonextensiondisableactivateterminal } from "./robocorpSettings";
import { disablePythonTerminalActivateEnvironment } from "./pythonExtIntegration";
import { LocalPackageMetadataInfo, ActionResult, InterpreterInfo } from "./protocols";
import * as fsModule from "fs";
import { randomBytes } from "crypto";

export async function askAndCreateRccTerminal() {
    let robot: LocalPackageMetadataInfo = await listAndAskRobotSelection(
        "Please select the target Task Package for the terminal.",
        "Unable to create terminal (no Task Package detected in the Workspace).",
        { showActionPackages: true, showTaskPackages: true, showAgentPackages: false }
    );
    if (robot) {
        await createRccTerminal(robot);
    }
}

const createTempFile = async () => {
    const sema4aiHome = await getRobocorpHome();
    const sema4aiHomeTemp = pathModule.join(sema4aiHome, "temp");
    if (!fsModule.existsSync(sema4aiHomeTemp)) {
        fsModule.mkdirSync(sema4aiHomeTemp, { recursive: true });
    }
    const isWindows = process.platform.toString() === "win32";
    const filename = "env-vars-" + randomBytes(16).toString("hex");
    const varsFilePath = pathModule.join(sema4aiHomeTemp, filename + (isWindows ? ".bat" : ".sh"));

    const deleteFile = () => {
        fsModule.rmSync(varsFilePath, { force: true, recursive: true });
    };

    // Delete temporary file when program exits
    process.once("exit", deleteFile);
    process.once("SIGINT", deleteFile);
    process.once("SIGTERM", deleteFile);

    return varsFilePath;
};

/**
 * Creates a terminal with the interpreter resolved from the given file path.
 */
export async function createTerminalForFile(filePath: string, terminalName: string, additionalPathEntry?: string) {
    let result: ActionResult<InterpreterInfo | undefined> = await resolveInterpreter(filePath);
    if (!result.success) {
        window.showWarningMessage("Error resolving interpreter info: " + result.message);
        return;
    }

    let interpreter: InterpreterInfo = result.result;
    if (!interpreter || !interpreter.pythonExe) {
        window.showWarningMessage("Unable to obtain interpreter information from: " + filePath);
        return;
    }
    OUTPUT_CHANNEL.appendLine("Retrieved Python interpreter: " + interpreter.pythonExe);

    // If vscode-python is installed, we need to disable the terminal activation as it
    // conflicts with the robot environment.
    if (getAutosetpythonextensiondisableactivateterminal()) {
        await disablePythonTerminalActivateEnvironment();
    }

    let env = mergeEnviron();
    // Update env to contain rcc location.
    if (interpreter.environ) {
        for (let key of Object.keys(interpreter.environ)) {
            let value = interpreter.environ[key];
            let isPath = false;
            if (process.platform == "win32") {
                key = key.toUpperCase();
                if (key == "PATH") {
                    isPath = true;
                }
            } else {
                if (key == "PATH") {
                    isPath = true;
                }
            }
            if (isPath) {
                value = additionalPathEntry + pathModule.delimiter + value;
            }

            env[key] = value;
        }
    }
    OUTPUT_CHANNEL.appendLine("Retrieved environment: " + JSON.stringify(env, null, 2));

    // We need to activate the RCC python environment after the terminal has spawned
    // This way we avoid the environment being overwritten by shell startup scripts
    // The Terminal env injection works if no overwrites happen

    const sema4aiHome = await getRobocorpHome();
    const sema4aiHomeTemp = pathModule.join(sema4aiHome, "temp");
    if (!fsModule.existsSync(sema4aiHomeTemp)) {
        fsModule.mkdirSync(sema4aiHomeTemp, { recursive: true });
    }
    const varsFilePath = await createTempFile();

    if (process.platform.toString() === "win32") {
        // Making sure we create a CMD prompt in Windows as it can default to PowerShell
        // and the Python Environment activation fails
        const terminal = window.createTerminal({
            name: terminalName,
            env: env,
            cwd: pathModule.dirname(filePath),
            message: "Sema4.ai Package Activated Interpreter (Python Environment)",
            shellPath: "C:\\Windows\\System32\\cmd.exe",
        });

        const envVarsContent = Object.keys(env)
            .reduce((acc, key) => {
                return `${acc}SET ${key}=${env[key]}\n`;
            }, "")
            .trim();
        OUTPUT_CHANNEL.appendLine("Create terminal with environment: " + envVarsContent);
        fsModule.writeFileSync(varsFilePath, envVarsContent);
        terminal.sendText(`call ${varsFilePath}\n`);
        terminal.show();
    } else {
        // The shell in UNIX doesn't matter that much as the syntax to set the Python Environment is common
        const terminal = window.createTerminal({
            name: terminalName,
            env: env,
            cwd: pathModule.dirname(filePath),
            message: "Sema4.ai Package Activated Interpreter (Python Environment)",
        });
        const envVarsContent = Object.keys(env)
            .reduce((acc, key) => {
                return `${acc}export ${key}=${env[key]}\n`;
            }, "")
            .trim();
        OUTPUT_CHANNEL.appendLine("Create terminal with environment: " + envVarsContent);
        fsModule.writeFileSync(varsFilePath, envVarsContent);
        terminal.sendText(`source ${varsFilePath}\n`);
        terminal.show();
    }
}

export async function createRccTerminal(robotInfo: LocalPackageMetadataInfo) {
    if (robotInfo) {
        async function startShell(progress: Progress<{ message?: string; increment?: number }>): Promise<undefined> {
            const rccLocation = await getRccLocation();
            if (!rccLocation) {
                OUTPUT_CHANNEL.appendLine(
                    "Unable to collect environment to create terminal with RCC:" +
                        rccLocation +
                        " for Package: " +
                        robotInfo.name
                );
                window.showErrorMessage("Unable to find RCC.");
                return;
            }

            OUTPUT_CHANNEL.appendLine(
                "Create terminal with RCC: " + rccLocation + " for Package: " + robotInfo.filePath
            );
            createTerminalForFile(
                robotInfo.filePath,
                robotInfo.name + " Package environment",
                pathModule.dirname(rccLocation)
            );

            OUTPUT_CHANNEL.appendLine("Terminal created!");
            return undefined;
        }

        await window.withProgress(
            {
                location: ProgressLocation.Notification,
                title: "Start RCC shell for: " + robotInfo.name,
                cancellable: false,
            },
            startShell
        );
    }
}
