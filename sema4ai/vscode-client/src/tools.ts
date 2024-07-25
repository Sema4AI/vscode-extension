import { commands, window } from "vscode";
import { sleep } from "./time";
import { logError, OUTPUT_CHANNEL } from "./channel";
import * as roboCommands from "./robocorpCommands";
import { ActionResult } from "./protocols";

export enum Tool {
    Rcc = "rcc",
    ActionServer = "action-server",
    AgentCli = "agent-cli",
}

type ToolAttributeMap<T = string> = { [key in Tool]: T };

const TOOL_EXECUTABLE_NAME_MAP: ToolAttributeMap = {
    [Tool.Rcc]: "rcc",
    [Tool.ActionServer]: "action-server",
    [Tool.AgentCli]: "agent-cli",
};

const TOOL_VERSION_COMMAND_MAP: ToolAttributeMap = {
    [Tool.Rcc]: "",
    [Tool.ActionServer]: roboCommands.SEMA4AI_ACTION_SERVER_VERSION_INTERNAL,
    [Tool.AgentCli]: roboCommands.SEMA4AI_AGENT_CLI_VERSION_INTERNAL,
};

const TOOL_DOWNLOAD_COMMAND_MAP: ToolAttributeMap = {
    [Tool.Rcc]: roboCommands.SEMA4AI_RCC_DOWNLOAD_INTERNAL,
    [Tool.ActionServer]: roboCommands.SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL,
    [Tool.AgentCli]: roboCommands.SEMA4AI_AGENT_CLI_DOWNLOAD_INTERNAL,
};

export const getExecutableFileName = (tool: Tool, suffix: string = ""): string => {
    const executableName = TOOL_EXECUTABLE_NAME_MAP[tool];

    return process.platform === "win32" ? `${executableName}${suffix}.exe` : `${executableName}${suffix}`;
};

export const getToolVersion = async (tool: Tool): Promise<string> => {
    if (tool === Tool.Rcc) {
        throw new Error(`${tool} is not supported for version command`);
    }

    const executableName = TOOL_EXECUTABLE_NAME_MAP[tool];
    const versionCommand = TOOL_VERSION_COMMAND_MAP[tool];

    const maxTimes = 4;

    let lastError;

    for (let checkedTimes = 0; checkedTimes < maxTimes; checkedTimes++) {
        const commandResult: ActionResult<string> = await commands.executeCommand(versionCommand);

        if (commandResult?.success) {
            return commandResult.result;
        } else {
            lastError = commandResult?.message;

            // In Windows right after downloading the file it may not be executable,
            // so, retry a few times.
            await sleep(250);
        }
    }
    const msg = `There was an error running ${executableName}. It may be unusable or you may not have permissions to run it.`;

    logError(msg, lastError, "ERR_VERIFY_ACTION_SERVER_VERSION");
    window.showErrorMessage(msg);

    throw lastError;
};

export const downloadTool = async (tool: Tool, location: string = ""): Promise<string> => {
    const executableName = TOOL_EXECUTABLE_NAME_MAP[tool];
    const downloadCommand = TOOL_DOWNLOAD_COMMAND_MAP[tool];

    // Downloads can go wrong (so, retry a few times before giving up).
    const maxTries = 3;

    OUTPUT_CHANNEL.appendLine(`Downloading tool: ${executableName}`);

    for (let currentTry = 1; currentTry <= maxTries; currentTry++) {
        const commandResult: ActionResult<string> = await commands.executeCommand(
            downloadCommand,
            location ? { location } : null
        );

        if (commandResult?.success) {
            const downloadedTo = commandResult.result;

            OUTPUT_CHANNEL.appendLine(`Finished downloading, file written to: ${downloadedTo}`);

            // If we don't sleep after downloading, the first activation seems to fail on Windows and Mac
            // (EBUSY on Windows, undefined on Mac).
            await sleep(200);

            return downloadedTo;
        } else {
            OUTPUT_CHANNEL.appendLine(
                `Error downloading (${currentTry} of ${maxTries}). Error: ${commandResult?.message}`
            );

            if (currentTry === maxTries) {
                const errorMsg = `Error downloading tool: ${executableName}. Error: ${commandResult?.message}`;

                logError(errorMsg, undefined, "ERR_DOWNLOAD_TOOL");
                window.showErrorMessage(errorMsg);
                return "";
            }
        }
    }
};
