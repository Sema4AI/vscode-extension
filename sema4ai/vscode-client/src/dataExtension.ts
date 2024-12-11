import { commands, extensions, window } from "vscode";
import { logError, OUTPUT_CHANNEL } from "./channel";
import { DataServerConfig } from "./robo/actionPackage";

const DATA_EXTENSION_ID = "sema4ai.sema4ai-data-access";
export const DATA_SERVER_START_COMMAND_ID = "sema4ai-data.dataserver.start";
export const DATA_SERVER_STOP_COMMAND_ID = "sema4ai-data.dataserver.stop";
export const DATA_SERVER_STATUS_COMMAND_ID = "sema4ai-data.dataserver.status";
export const DATABASE_ADD_COMMAND_ID = "sema4ai-data.database.add";

/**
 * Returns true if the data extension is installed, false otherwise.
 */
function isDataExtensionInstalled() {
    try {
        let extension = extensions.getExtension(DATA_EXTENSION_ID);
        if (extension) {
            return true;
        }
    } catch (error) {
        logError("Error checking if data extension is installed", error, "ERR_CHECK_DATA_EXTENSION_INSTALLED");
    }

    return false;
}

/**
 * Verify if the data extension is installed and install it if it's not.
 */
export async function verifyDataExtensionIsInstalled(
    msg: string = "It seems that the Sema4AI data extension is not installed. Do you wish to install it?"
) {
    if (isDataExtensionInstalled()) {
        try {
            let extension = extensions.getExtension(DATA_EXTENSION_ID);
            if (extension) {
                let version = extension?.packageJSON.version;
                if (version) {
                    // If we have a '-' in the version, remove it and everything after it
                    if (version.includes("-")) {
                        version = version.split("-")[0];
                    }
                }
                // Check if version matches something as <number>.<number>.<number>
                if (version && version.match(/^\d+\.\d+\.\d+$/)) {
                    // Check if the version is greater or equal to 1.0.2 (use regexp to extract the version number)
                    let [major, minor, patch] = version.split(".").map(Number);
                    if (major > 1 || (major == 1 && minor > 0) || (major == 1 && minor == 0 && patch >= 4)) {
                        if (!extension?.isActive) {
                            await extension?.activate();
                        }
                        return true;
                    }
                }
                // Notify users that the version is too old (or it didn't match the regexp)
                window.showWarningMessage(
                    `The Sema4AI data extension is installed, but the version (${version}) is too old (minimum required version is 1.0.2). Please update it.`
                );
                commands.executeCommand("workbench.extensions.search", DATA_EXTENSION_ID);
                return false;
            }
        } catch (error) {
            logError("Error checking data extension version", error, "ERR_CHECK_DATA_EXTENSION_VERSION");
            return false;
        }
    }

    let install = "Install";
    let dismiss = "Dismiss";
    let chosen = await window.showInformationMessage(msg, install, dismiss);
    if (chosen == install) {
        try {
            await commands.executeCommand("workbench.extensions.installExtension", DATA_EXTENSION_ID);
        } catch (error) {
            commands.executeCommand("workbench.extensions.search", DATA_EXTENSION_ID);
            logError("Error installing data extension", error, "ERR_INSTALL_DATA_EXTENSION");
            window.showErrorMessage(
                "Unable to install the Sema4AI data extension. Please install it manually and retry."
            );
            return false;
        }
        if (isDataExtensionInstalled()) {
            return true;
        }
    }

    return false;
}

function failWithErrorMessage(dataServerInfo: DataServerConfig, errorMessage: string) {
    OUTPUT_CHANNEL.appendLine(
        `${errorMessage} (obtained from the ${DATA_SERVER_START_COMMAND_ID} command). Full data server info: ` +
            JSON.stringify(dataServerInfo, null, 4)
    );
    window.showErrorMessage(errorMessage);
}

export async function startDataServerAndGetInfo(): Promise<DataServerConfig | undefined> {
    const dataServerInfo = (await commands.executeCommand(DATA_SERVER_START_COMMAND_ID, {
        "showUIMessages": false,
    })) as DataServerConfig | undefined;
    if (dataServerInfo) {
        if (!dataServerInfo.isRunning) {
            failWithErrorMessage(
                dataServerInfo,
                "After starting the data server, isRunning still returning false in provided data server config."
            );
            return undefined;
        }

        // Let's validate that the data server info has the correct structure (check each field one by one and
        // show error if it's not correct)
        if (!dataServerInfo.api) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api' field");
            return undefined;
        }

        if (!dataServerInfo.api.http) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.http' field");
            return undefined;
        }

        if (!dataServerInfo.api.http.host) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.http.host' field");
            return undefined;
        }

        if (!dataServerInfo.api.http.port) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.http.port' field");
            return undefined;
        }

        if (!dataServerInfo.api.mysql) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.mysql' field");
            return undefined;
        }

        if (!dataServerInfo.api.mysql.host) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.mysql.host' field");
            return undefined;
        }

        if (!dataServerInfo.api.mysql.port) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'api.mysql.port' field");
            return undefined;
        }

        if (!dataServerInfo.auth) {
            failWithErrorMessage(dataServerInfo, "The data server info is missing the 'auth' field");
            return undefined;
        }
    }
    return dataServerInfo;
}
