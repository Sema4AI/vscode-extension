import * as vscode from "vscode";
import { ExtensionContext } from "vscode";

// Track when the last message was shown
let lastMessageTime: number = 0;
const MESSAGE_THROTTLE_MS = 5 * 60 * 1000; // 5 minutes in milliseconds

function checkSema4aiActionPackageWarning(doc: vscode.TextDocument) {
    // Check if the file matches the Sema4.ai action package pattern
    const pattern = new vscode.RelativePattern(
        vscode.workspace.getWorkspaceFolder(doc.uri)!,
        "**/Sema4.ai/**/*"
    );

    if (vscode.languages.match(pattern, doc)) {
        const now = Date.now();
        // Only show message if 5 minutes have passed since last message
        if (now - lastMessageTime > MESSAGE_THROTTLE_MS) {
            vscode.window.showErrorMessage(
                "Changes to files under Sema4.ai folder will not be picked up when deploying, as gallery actions are always fetched from the gallery."
            );
            lastMessageTime = now;
        }
    }
}

export function installSema4aiActionWatcher(context: ExtensionContext) {
    // Watch for document saves
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc) => {
            checkSema4aiActionPackageWarning(doc);
        })
    );
}
