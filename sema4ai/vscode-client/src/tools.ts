import { commands, window } from "vscode";
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

export const getToolVersion = async (tool: Tool): Promise<string> => {
    if (tool === Tool.Rcc) {
        throw new Error(`${tool} is not supported for version command`);
    }

    const executableName = TOOL_EXECUTABLE_NAME_MAP[tool];
    const versionCommand = TOOL_VERSION_COMMAND_MAP[tool];

    const commandResult: ActionResult<string> = await commands.executeCommand(versionCommand);

    if (commandResult?.success) {
        return commandResult.result;
    }
    const msg = `There was an error running ${executableName}. It may be unusable or you may not have permissions to run it.\n${commandResult?.message}`;

    logError(msg, undefined, "ERR_VERIFY_ACTION_SERVER_VERSION");
    window.showErrorMessage(msg);
    throw new Error(msg);
};

export const downloadTool = async (tool: Tool, location: string = ""): Promise<string> => {
    const executableName = TOOL_EXECUTABLE_NAME_MAP[tool];
    const downloadCommand = TOOL_DOWNLOAD_COMMAND_MAP[tool];

    OUTPUT_CHANNEL.appendLine(`Downloading tool: ${executableName}`);
    const commandResult: ActionResult<string> = await commands.executeCommand(
        downloadCommand,
        location ? { location } : null
    );

    if (commandResult?.success) {
        const downloadedTo = commandResult.result;
        OUTPUT_CHANNEL.appendLine(`Finished downloading, file written to: ${downloadedTo}`);
        return downloadedTo;
    } else {
        const errorMsg = `Error downloading tool: ${executableName}. Error: ${commandResult?.message}`;

        logError(errorMsg, undefined, "ERR_DOWNLOAD_TOOL");
        window.showErrorMessage(errorMsg);
        return "";
    }
};
