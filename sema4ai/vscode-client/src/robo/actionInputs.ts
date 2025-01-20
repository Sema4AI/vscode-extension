import * as vscode from "vscode";

import { langServer } from "../extension";
import { window } from "vscode";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { ActionResult } from "../protocols";

interface ExtractedActionInfo {
    default_values: any;
    informal_schema_representation: string[];
    json_schema: any;
    managed_params_json_schema: any;
    action_name: string;
    action_relative_path: string;
    kind: "action" | "query" | "predict";
}

// Create interface for the input we write.
export interface ActionInputsV2 {
    inputs: { inputName: string; inputValue: any }[];
    metadata: {
        actionName: string;
        actionRelativePath: string;
        schemaDescription: string[];
        managedParamsSchemaDescription: any;
        inputFileVersion: "v2";
    };
}

// Same as v2, but with the kind field in the metadata.
export interface ActionInputsV3 {
    inputs: { inputName: string; inputValue: any }[];
    metadata: {
        actionName: string;
        actionRelativePath: string;
        schemaDescription: string[];
        managedParamsSchemaDescription: any;
        inputFileVersion: "v3";
        // Kind is new in v3
        kind: "action" | "query" | "predict";
        // Action signature is new in v3
        // This can be later gotten from the actionRelativePath and action name to validate if the function signature is still the same
        // (if it's not, we should ask the user to update the input file).
        actionSignature: string;
    };
}

/**
 * Returns an error message if the input is not in v2 format or if the v2 input is not properly followed, otherwise returns undefined.
 */
export const errorMessageValidatingV2OrV3Input = (input: any): string | undefined => {
    if (input.metadata.inputFileVersion !== "v2" && input.metadata.inputFileVersion !== "v3") {
        return "Input file is not in v2 or v3 format.";
    }
    if (!input.inputs || !Array.isArray(input.inputs) || input.inputs.length === 0) {
        return "Input file is in v2 or v3 format, but the inputs array is missing or empty.";
    }
    // Check inputName
    if (!input.inputs.every((input) => typeof input.inputName === "string" && input.inputName.length > 0)) {
        return "Input file is in v2 or v3 format, but one of the `inputName` fields is not a string, is missing or is empty.";
    }
    // Check the metadata
    if (!input.metadata.actionName || typeof input.metadata.actionName !== "string") {
        return "Input file is in v2 or v3 format, but the action name in metadata is missing or not a string.";
    }
    if (!input.metadata.actionRelativePath || typeof input.metadata.actionRelativePath !== "string") {
        return "Input file is in v2 or v3 format, but the action relative path in metadata is missing or not a string.";
    }
    return undefined;
};

export const updateActionInputsMetadata = async (
    actionFileUri: vscode.Uri,
    actionName: string,
    targetInput: string,
    actionPackageYamlDirectory: string,
    existingInputs: ActionInputsV2 | ActionInputsV3,
    showToUser: boolean = false
): Promise<ActionInputsV3 | undefined> => {
    const result = await window.withProgress(
        {
            location: vscode.ProgressLocation.Window,
            title: "Creating input file",
            cancellable: false,
        },
        async (progress) => {
            const result = await _createActionInputs(actionFileUri, actionName, actionPackageYamlDirectory, progress);
            if (result !== undefined) {
                OUTPUT_CHANNEL.appendLine(`Updating input file ${targetInput} metadata.`);
                // Update the input file
                result.inputs = existingInputs.inputs; // Keep the same inputs that were there before
                const inputUri = vscode.Uri.file(targetInput);
                await vscode.workspace.fs.writeFile(inputUri, Buffer.from(JSON.stringify(result, null, 4)));
                if (showToUser) {
                    await vscode.window.showTextDocument(inputUri);
                }
                return result;
            }
            return undefined;
        }
    );
    return result;
};

export const createActionInputs = async (
    actionFileUri: vscode.Uri,
    actionName: string,
    targetInput: string,
    actionPackageYamlDirectory: string
): Promise<boolean> => {
    const result = await window.withProgress(
        {
            location: vscode.ProgressLocation.Window,
            title: "Creating input file",
            cancellable: false,
        },
        async (progress) => {
            const result = await _createActionInputs(actionFileUri, actionName, actionPackageYamlDirectory, progress);
            if (result !== undefined) {
                const inputUri = vscode.Uri.file(targetInput);
                await vscode.workspace.fs.writeFile(inputUri, Buffer.from(JSON.stringify(result, null, 4)));
                await vscode.window.showTextDocument(inputUri);
                return true;
            }
            return false;
        }
    );
    return result;
};

const _createActionInputs = async (
    actionFileUri: vscode.Uri,
    actionName: string,
    actionPackageYamlDirectory: string,
    progress: vscode.Progress<{ message?: string; increment?: number }>
): Promise<ActionInputsV3 | undefined> => {
    try {
        progress.report({ message: "Listing actions/queries/predictions in the package" });
        const result: any = await langServer.sendRequest("listActionsFullAndSlow", {
            action_package_uri: actionFileUri.toString(),
            action_package_yaml_directory: actionPackageYamlDirectory,
        });
        if (!result.success) {
            const OPEN_OUTPUT_CHANNEL = "Open OUTPUT for more details";
            const option = await window.showErrorMessage(
                `It was not possible to create the Action input because there was an issue listing the actions.
The most common issue is that importing the module with the Action code is not working.
If that's the case, please fix the Action python code and try again.`,
                { modal: true },
                OPEN_OUTPUT_CHANNEL
            );
            if (option === OPEN_OUTPUT_CHANNEL) {
                OUTPUT_CHANNEL.show();
            }
            return undefined;
        }
        const actions = result.result;
        const action: ExtractedActionInfo = actions[actionName];
        if (!action) {
            window.showErrorMessage(
                `It was not possible to create the Action input because an action named '${actionName}' was not found. Actions found: ${Object.keys(
                    actions
                ).join(", ")}`,
                { modal: true }
            );
            return undefined;
        }

        const actionSignatureResult: ActionResult<string> = await langServer.sendRequest("getActionSignature", {
            action_relative_path: action.action_relative_path,
            action_package_yaml_directory: actionPackageYamlDirectory,
            action_name: actionName,
        });

        let actionSignature: string | undefined;
        if (!actionSignatureResult.success) {
            window.showErrorMessage("Error getting action signature: " + actionSignatureResult.message);
            actionSignature = undefined;
        } else {
            actionSignature = actionSignatureResult.result;
        }

        const inputData: ActionInputsV3 = {
            inputs: [{ inputName: "input-1", inputValue: action.default_values }],
            metadata: {
                actionName: action.action_name,
                actionRelativePath: action.action_relative_path,
                schemaDescription: action.informal_schema_representation,
                managedParamsSchemaDescription: action.managed_params_json_schema,
                inputFileVersion: "v3",
                kind: action.kind,
                actionSignature: actionSignature,
            },
        };
        return inputData;
    } catch (error) {
        window.showErrorMessage("Error creating action inputs: " + error);
        logError("Error creating action inputs.", error, "ERROR_CREATING_ACTION_INPUTS");
        return undefined;
    }
};
