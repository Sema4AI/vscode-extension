import * as assert from "assert";
import * as vscode from "vscode";
import { WorkspaceFolder } from "vscode";
import { ActionResult, LocalPackageMetadataInfo } from "../../protocols";
import { SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL } from "../../robocorpCommands";

const testFolderLocation = "/resources/";

suite("Sema4.ai Extension Test Suite", () => {
    vscode.window.showInformationMessage("Start all tests.");

    test("Test that robots can be listed", async () => {
        // i.e.: Jus check that we're able to get the contents.
        let workspaceFolders: ReadonlyArray<WorkspaceFolder> = vscode.workspace.workspaceFolders;
        assert.strictEqual(workspaceFolders.length, 1);

        let actionResult: ActionResult<LocalPackageMetadataInfo[]>;
        actionResult = await vscode.commands.executeCommand(SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL);
        assert.strictEqual(actionResult.success, true);
        let robotsInfo: LocalPackageMetadataInfo[] = actionResult.result;
        // Check that we're able to load at least one robot.
        assert.ok(robotsInfo.length >= 1);
    });
});
