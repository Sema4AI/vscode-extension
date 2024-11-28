import { commands, extensions, window } from "vscode";

const DATA_EXTENSION_ID = "sema4ai.vscode-sema4ai-client";

function isDataExtensionInstalled() {
    try {
        let extension = extensions.getExtension(DATA_EXTENSION_ID);
        if (extension) {
            return true;
        }
    } catch (error) {}

    return false;
}

export async function verifyDataExtensionIsInstalled() {
    if (isDataExtensionInstalled()) {
        return true;
    }

    let install = "Install";
    let dismiss = "Dismiss";
    let chosen = await window.showInformationMessage(
        "It seems that the Sema4AI data extension is not installed. Do you wish to install it?",
        install,
        dismiss
    );
    if (chosen == install) {
        await commands.executeCommand("workbench.extensions.installExtension", DATA_EXTENSION_ID);
        return true;
    }

    return false;
}
