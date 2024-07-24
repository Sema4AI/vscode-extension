import { ProgressLocation, window } from "vscode";
import { Tool, getToolVersion, downloadTool } from "./tools";
import { getExtensionRelativeFile, fileExists } from "./files";
import { compareVersions } from "./common";
import { getAgentserverLocation } from "./robocorpSettings";

const LATEST_AGENT_SERVER_VERSION = "v0.0.5";
let versionVerified = false;

/**
 * Returns Agent Server's location, and downloads it if missing under assumed location, or if the codebase
 * contains a newer version (see LATEST_AGENT_SERVER_VERSION).
 * The location depends on the extension's settings - if sema4ai.agentServer.location is set, it will be used.
 * Otherwise, it will fallback to "bin" directory relative to extension source files.
 */
export const getAgentServerLocation = async (): Promise<string> => {
    const location = getAgentserverLocation() || getDefaultAgentServerLocation();

    if (!(await fileExists(location))) {
        const savedLocation = await downloadAgentServer(location);

        /**
         * If failed, savedLocation will be nullish - at this point we simply exit the function,
         * as appropriate error notifications have already been shown.
         */
        if (!savedLocation || savedLocation !== location) {
            return;
        }
    }

    if (!versionVerified) {
        const currentVersion = prepareVersionToCompare(await getAgentServerVersion());
        const expectedVersion = prepareVersionToCompare(LATEST_AGENT_SERVER_VERSION);

        const compare = compareVersions(expectedVersion, currentVersion);

        if (compare > 0) {
            await downloadAgentServer(location);
        }
    }

    return location;
};

export const downloadAgentServer = (agentServerLocation: string): Thenable<string> => {
    return window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Downloading Agent Server",
            cancellable: false,
        },
        (): Promise<string> => downloadTool(Tool.AgentServer, agentServerLocation)
    );
};

export const getDefaultAgentServerLocation = (): string => {
    if (process.platform === "win32") {
        return getExtensionRelativeFile("../../bin/agent-server.exe", false);
    }

    return getExtensionRelativeFile("../../bin/agent-server", false);
};

export const getAgentServerVersion = (): Promise<string> => {
    return getToolVersion(Tool.AgentServer);
};

const prepareVersionToCompare = (version: string): string => version.replace("v", "");
