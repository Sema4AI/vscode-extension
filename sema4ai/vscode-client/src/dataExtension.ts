import { commands, extensions, window, ProgressLocation } from "vscode";
import { logError, OUTPUT_CHANNEL } from "./channel";

const DATA_EXTENSION_ID = "sema4ai.sema4ai-data-access";
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

export async function fetchDataServerStatus(): Promise<any | null> {
    return window.withProgress(
        { location: ProgressLocation.Notification, title: "Getting data server status...", cancellable: false },
        async () => {
            const status = await commands.executeCommand(DATA_SERVER_STATUS_COMMAND_ID);
            if (!status["success"]) {
                window.showErrorMessage(
                    "Unable to get the data server status. Got error: " +
                        status["error"]["message"] +
                        ". Please start the data server from Sema4.ai Studio and try again."
                );
                return null;
            }
            if (!status["data"]["is_running"]) {
                window.showErrorMessage(
                    "The data server is not running. Please start the data server from Sema4.ai Studio and try again."
                );
                return null;
            }
            return status;
        }
    );
}
