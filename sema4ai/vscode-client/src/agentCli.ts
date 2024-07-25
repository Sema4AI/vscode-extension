import { ProgressLocation, window } from "vscode";
import { Tool, getToolVersion, downloadTool } from "./tools";
import { getExtensionRelativeFile, fileExists } from "./files";
import { compareVersions } from "./common";
import { getAgentcliLocation } from "./robocorpSettings";

const LATEST_AGENT_CLI_VERSION = "v0.0.6";
let versionVerified = false;

/**
 * Returns Agent CLI's location, and downloads it if missing under assumed location, or if the codebase
 * contains a newer version (see LATEST_AGENT_CLI_VERSION).
 * The location depends on the extension's settings - if sema4ai.agentCli.location is set, it will be used.
 * Otherwise, it will fallback to "bin" directory relative to extension source files.
 */
export const getAgentCliLocation = async (): Promise<string> => {
    const location = getAgentcliLocation() || getDefaultAgentCliLocation();

    if (!(await fileExists(location))) {
        const savedLocation = await downloadAgentCli(location);

        /**
         * If failed, savedLocation will be nullish - at this point we simply exit the function,
         * as appropriate error notifications have already been shown.
         */
        if (!savedLocation || savedLocation !== location) {
            return;
        }
    }

    if (!versionVerified) {
        const currentVersion = prepareVersionToCompare(await getAgentCliVersion());
        const expectedVersion = prepareVersionToCompare(LATEST_AGENT_CLI_VERSION);

        const compare = compareVersions(expectedVersion, currentVersion);

        if (compare > 0) {
            await downloadAgentCli(location);
        }
    }

    return location;
};

export const downloadAgentCli = (agentCliLocation: string): Thenable<string> => {
    return window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Downloading Agent CLI",
            cancellable: false,
        },
        (): Promise<string> => downloadTool(Tool.AgentCli, agentCliLocation)
    );
};

export const getDefaultAgentCliLocation = (): string => {
    if (process.platform === "win32") {
        return getExtensionRelativeFile("../../bin/agent-cli.exe", false);
    }

    return getExtensionRelativeFile("../../bin/agent-cli", false);
};

export const getAgentCliVersion = (): Promise<string> => {
    return getToolVersion(Tool.AgentCli);
};

const prepareVersionToCompare = (version: string): string => version.replace("v", "");
