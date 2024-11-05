import { CancellationToken, Progress, ProgressLocation, Terminal, Uri, window, commands } from "vscode";
import * as roboCommands from "./robocorpCommands";
import { createEnvWithRobocorpHome, getRobocorpHome } from "./rcc";
import path = require("path");
import { OUTPUT_CHANNEL } from "./channel";
import * as http from "http";
import * as fs from "fs";
import { listAndAskRobotSelection } from "./activities";
import { ActionResult, ActionServerVerifyLoginOutput, ActionServerListOrganizationsOutput } from "./protocols";
import { Tool, getToolVersion, downloadTool } from "./tools";

const ACTION_SERVER_DEFAULT_PORT = 8082;
const ACTION_SERVER_TERMINAL_NAME = "Sema4.ai: Action Server";

let globalLocation: string | undefined = undefined;

function downloadActionServer(): Thenable<string> {
    return downloadTool(Tool.ActionServer);
}

export const getActionServerVersion = async (): Promise<string> => {
    return getToolVersion(Tool.ActionServer);
};

export const downloadOrGetActionServerLocation = async (): Promise<string | undefined> => {
    if (globalLocation) {
        return globalLocation;
    }
    globalLocation = await downloadActionServer();
    return globalLocation;
};

export const isActionServerAlive = async (port: number = ACTION_SERVER_DEFAULT_PORT) => {
    try {
        await fetchData(port, "/openapi.json", "GET");
        return true;
    } catch (err) {
        return false;
    }
};

function makeRequest(postData: string, options: http.RequestOptions): Promise<string> {
    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let responseData = "";

            res.setEncoding("utf8");
            res.on("data", (chunk) => {
                responseData += chunk;
            });

            res.on("end", () => {
                resolve(responseData);
            });
        });

        req.on("error", (error) => {
            reject(error);
        });

        req.write(postData);
        req.end();
    });
}

/**
 * @param path this is the path in the host (i.e.: /api-endpoint)
 */
async function fetchData(port: number, path: string, method: "POST" | "GET") {
    const postData = JSON.stringify({});

    const options: http.RequestOptions = {
        hostname: "localhost",
        port: port,
        path: path,
        method: method,
        headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(postData),
        },
    };

    return await makeRequest(postData, options);
}

const shutdownExistingActionServer = async (port) => {
    await fetchData(port, "/api/shutdown", "POST");
};

export const getActionServerTerminal = (): undefined | Terminal => {
    for (const terminal of window.terminals) {
        if (terminal.name === ACTION_SERVER_TERMINAL_NAME) {
            return terminal;
        }
    }
    return undefined;
};

const disposeActionServerTerminal = (terminal: Terminal) => {
    terminal.dispose();
    /**
     * @TODO:
     * Verify whether unsetting the reference is necessary.
     * If not, this function can be removed in favour of calling terminal.dispose() in the caller.
     */
    terminal = undefined;
};

const stopActionServer = async () => {
    let actionServerTerminal: Terminal = getActionServerTerminal();

    await shutdownExistingActionServer(ACTION_SERVER_DEFAULT_PORT);
    disposeActionServerTerminal(actionServerTerminal);
};

const startActionServerInternal = async (directory: Uri) => {
    let actionServerTerminal: Terminal = getActionServerTerminal();

    const location = await downloadOrGetActionServerLocation();
    if (!location) {
        return;
    }

    const home = await getRobocorpHome();
    const env = createEnvWithRobocorpHome(await getRobocorpHome());
    env["RC_ADD_SHUTDOWN_API"] = "1";

    const externalApiPid = path.join(home, "sema4ai-studio", "external-api-server.pid");
    if (fs.existsSync(externalApiPid)) {
        const fileContent = JSON.parse(fs.readFileSync(externalApiPid, "utf-8"));

        if (fileContent.port) {
            process.env["SEMA4AI_CREDENTIAL_API"] = `http://localhost:${fileContent.port}/api/v1/ace-services`;
        }
    } else {
        OUTPUT_CHANNEL.appendLine("Studio is not opened, cannot set the external API URL.");
    }

    actionServerTerminal = window.createTerminal({
        name: "Sema4.ai: Action Server",
        env: env,
        cwd: directory,
    });

    actionServerTerminal.show();
    OUTPUT_CHANNEL.appendLine("Starting action-server (in terminal): " + location);

    actionServerTerminal.sendText(""); // Just add a new line in case something is there already.
    actionServerTerminal.sendText(`cd ${directory.fsPath}`);
    actionServerTerminal.sendText(`${location} start --port=${ACTION_SERVER_DEFAULT_PORT}`);
};

export const findActionPackagePath = async ({ includeSemaOrg = true } = {}): Promise<Uri | undefined> => {
    // Need to list the action packages available to decide
    // which one to use for the action server.
    const selected = await listAndAskRobotSelection(
        "Please select the Action Package from which the Action Server should load actions.",
        "Unable to start Action Server because no Action Package was found in the workspace.",
        { showActionPackages: true, showTaskPackages: false, showAgentPackages: false, includeSemaOrg: includeSemaOrg }
    );
    if (!selected) {
        return;
    }
    return Uri.file(selected.directory);
};

export const startActionServer = async (directory: Uri) => {
    if (!directory) {
        directory = await findActionPackagePath();
    }

    let actionServerTerminal: Terminal = getActionServerTerminal();
    if (actionServerTerminal !== undefined) {
        if (await isActionServerAlive(ACTION_SERVER_DEFAULT_PORT)) {
            const RESTART = "Restart action server";
            const option = await window.showWarningMessage(
                "The action server seems to be running already. How do you want to proceed?",
                RESTART,
                "Cancel"
            );
            if (option !== RESTART) {
                return;
            }

            await stopActionServer();
        } else {
            OUTPUT_CHANNEL.appendLine("Action server not alive.");

            /* Called just in case to ensure ActionServer terminal is not active. */
            disposeActionServerTerminal(actionServerTerminal);
        }
    }

    await startActionServerInternal(directory);
};

export const restartActionServer = async (directory: Uri) => {
    await stopActionServer();
    await startActionServerInternal(directory);
};

const askForAccessCredentials = async (): Promise<string | undefined> => {
    const access_credentials: string = await window.showInputBox({
        "placeHolder": "Control Room Access Credentials",
        "prompt": "Please provide the Control Room access credentials.",
        "ignoreFocusOut": true,
        "password": true,
        "validateInput": (access_credentials: string): string | Thenable<string> => {
            const regex = /^\d{1,}:.{11,}$/;
            if (!access_credentials || !regex.test(access_credentials)) {
                return "Invalid access credentials: use form 1234:xxx...x";
            }
        },
    });

    return access_credentials;
};

export const verifyLogin = async (): Promise<ActionServerVerifyLoginOutput | undefined> => {
    const result: ActionResult<ActionServerVerifyLoginOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL
    );

    if (!result.success) {
        window.showErrorMessage(`Failed to verify login: ${result.message}`);
        return;
    }

    return result.result;
};

const askUserForHostname = async (
    progress: Progress<{ message?: string; increment?: number }>
): Promise<string | undefined> => {
    let defaultHostname = "https://us1.robocorp.com";

    progress.report({ message: "Getting default hostname" });
    const loginOutput = await verifyLogin();
    if (loginOutput && loginOutput.logged_in) {
        defaultHostname = loginOutput.hostname;
    }

    progress.report({ message: "Input hostname" });
    const hostname: string = await window.showInputBox({
        "value": defaultHostname,
        "prompt": "Please provide the Control Room hostname.",
        "ignoreFocusOut": true,
        "validateInput": (hostname: string): string | Thenable<string> => {
            if (!hostname) {
                return "Provide valid hostname";
            }
        },
    });

    return hostname;
};

export const actionServerCloudLogin = async () => {
    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Action Server Login",
            cancellable: false,
        },
        async (
            progress: Progress<{ message?: string; increment?: number }>,
            token: CancellationToken
        ): Promise<void> => {
            progress.report({ message: "Validating action server" });
            const actionServerLocation = await downloadOrGetActionServerLocation();
            if (!actionServerLocation) {
                return;
            }

            progress.report({ message: "Input access credentials" });
            const accessCredentials = await askForAccessCredentials();
            if (!accessCredentials) {
                return;
            }

            const hostname = await askUserForHostname(progress);
            if (!hostname) {
                return;
            }

            progress.report({ message: "Logging in" });
            const result: ActionResult<undefined> = await commands.executeCommand(
                roboCommands.SEMA4AI_ACTION_SERVER_CLOUD_LOGIN_INTERNAL,
                {
                    access_credentials: accessCredentials,
                    hostname,
                }
            );

            if (result.success) {
                window.showInformationMessage("Action Server Control Room login successful.");
            } else {
                window.showErrorMessage(`Action Server Control Room login failed: ${result.message}`);
            }
        }
    );
};

export const listOrganizations = async (): Promise<ActionServerListOrganizationsOutput> => {
    const result: ActionResult<ActionServerListOrganizationsOutput> = await commands.executeCommand(
        roboCommands.SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL,
        {}
    );
    if (!result.success) {
        window.showErrorMessage("No organizations found");
        return [];
    }

    return result.result;
};
