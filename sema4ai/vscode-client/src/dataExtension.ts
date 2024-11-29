import { commands, extensions, window } from "vscode";
import { logError } from "./channel";

const DATA_EXTENSION_ID = "sema4ai.sema4ai-data-access";
export const DATA_SERVER_START_COMMAND_ID = "sema4ai-data.dataserver.start";
export const DATA_SERVER_STOP_COMMAND_ID = "sema4ai-data.dataserver.stop";
export const DATA_SERVER_STATUS_COMMAND_ID = "sema4ai-data.dataserver.status";

/**
 * Returns true if the data extension is installed, false otherwise.
 */
function isDataExtensionInstalled() {
    try {
        let extension = extensions.getExtension(DATA_EXTENSION_ID);
        if (extension) {
            return true;
        }
    } catch (error) {}

    return false;
}

/**
 * Verify if the data extension is installed and install it if it's not.
 */
export async function verifyDataExtensionIsInstalled(
    msg: string = "It seems that the Sema4AI data extension is not installed. Do you wish to install it?"
) {
    if (isDataExtensionInstalled()) {
        return true;
    }

    let install = "Install";
    let dismiss = "Dismiss";
    let chosen = await window.showInformationMessage(msg, install, dismiss);
    if (chosen == install) {
        try {
            await commands.executeCommand("workbench.extensions.installExtension", DATA_EXTENSION_ID);
        } catch (error) {
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
