import { Uri, window, commands, ProgressLocation, Progress, CancellationToken } from "vscode";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { RobotEntry } from "../viewsCommon";
import { DatasourceInfo, DataSourceState } from "../protocols";
import { langServer } from "../extension";
import { startDataServerAndGetInfo } from "../dataExtension";
import { computeDataSourceState, DataServerConfig } from "./actionPackage";
import { sleep } from "../time";

export function isExternalDatasource(datasource: DatasourceInfo): boolean {
    const externalEngines = ["custom", "files", "models"];
    return !externalEngines.includes(datasource.engine) && !datasource.engine.startsWith("prediction");
}

export const setupDataSource = async (entry?: RobotEntry) => {
    if (!entry || !entry.extraData || !entry.extraData.datasource) {
        window.showErrorMessage("Data source not specified.");
        return;
    }

    const dataServerInfo = await startDataServerAndGetInfo();
    if (!dataServerInfo) {
        window.showErrorMessage(
            "Unable to run (error getting local data server connection info):\n" +
                JSON.stringify(dataServerInfo, null, 4)
        );
        return false;
    }

    const datasource: DatasourceInfo = entry.extraData.datasource;
    OUTPUT_CHANNEL.appendLine("setupDataSource: " + JSON.stringify(datasource, null, 4));

    if (isExternalDatasource(datasource)) {
        try {
            await commands.executeCommand("sema4ai-data.database.add");
        } catch (e) {
            logError("Could not run setup data source command", e, "ERR_DATA_SOURCE_SETUP");
            window.showErrorMessage(`"Could not run setup data source command: ${e.message}"`);
        }

        return;
    }

    const setupDataSourceResult = await langServer.sendRequest("setupDataSource", {
        action_package_yaml_directory_uri: Uri.file(entry.robot.directory).toString(),
        datasource: datasource,
        data_server_info: dataServerInfo,
    });
    OUTPUT_CHANNEL.appendLine("setupDataSourceResult: " + JSON.stringify(setupDataSourceResult, null, 4));
    if (setupDataSourceResult["success"]) {
        const messages = setupDataSourceResult["result"];
        window.showInformationMessage(messages.join("\n"));
        await waitForModelsToBeReady(Uri.file(entry.robot.directory).toString(), dataServerInfo);
    } else {
        const error = setupDataSourceResult["message"];
        window.showErrorMessage(`There was an error setting up the Data Source: ${error}`);
    }
};

export const waitForModelsToBeReady = async (
    actionPackageYamlDirectoryUri: string,
    dataServerInfo: DataServerConfig
) => {
    const dataSourceStateResult = await computeDataSourceState(actionPackageYamlDirectoryUri, dataServerInfo);

    const modelsBeingTrained: DatasourceInfo[] = [];

    if (dataSourceStateResult.success) {
        const dataSourceState: DataSourceState = dataSourceStateResult.result;
        // Ok, now see if any model is still being trained or has errors in the model.
        for (const datasource of dataSourceState.required_data_sources) {
            if (datasource.model_name) {
                if (datasource.model_state?.status === "error") {
                    window.showErrorMessage(
                        `There is an error with the model: ${datasource.name}.${datasource.model_name}: ${datasource.model_state.error}`
                    );
                } else if (datasource.model_state?.status !== "complete") {
                    modelsBeingTrained.push(datasource);
                }
            }
        }

        if (modelsBeingTrained.length > 0) {
            const modelNames = modelsBeingTrained.map((m) => `${m.name}.${m.model_name}`).join(", ");
            await window.withProgress(
                {
                    location: ProgressLocation.Notification,
                    title: `Waiting for model(s) to be ready: ${modelNames}`,
                    cancellable: true,
                },
                async (progress: Progress<{ message?: string; increment?: number }>, token: CancellationToken) => {
                    return await showProgressUntilModelsAreAllReady(
                        actionPackageYamlDirectoryUri,
                        dataServerInfo,
                        modelsBeingTrained,
                        progress,
                        token
                    );
                }
            );
        }
    } else {
        window.showErrorMessage(
            `There was an error computing the Data Sources state: ${dataSourceStateResult.message}`
        );
    }
};

const showProgressUntilModelsAreAllReady = async (
    actionPackageYamlDirectoryUri: string,
    dataServerInfo: DataServerConfig,
    models: DatasourceInfo[],
    progress: Progress<{ message?: string; increment?: number }>,
    token: CancellationToken
) => {
    // Extract datasource name and model name
    const waitForModels: string[] = models.map((m) => `${m.name}.${m.model_name}`);
    const initialTime = Date.now();

    let keepChecking = true;
    while (keepChecking) {
        await sleep(500);
        if (token.isCancellationRequested) {
            return;
        }
        const elapsedTime = Date.now() - initialTime;
        const timeInSecondsFormattedAsString = (elapsedTime / 1000).toFixed(1);
        progress.report({
            message: `elapsed: ${timeInSecondsFormattedAsString}s`,
        });
        keepChecking = false;
        const dataSourceStateResult = await computeDataSourceState(actionPackageYamlDirectoryUri, dataServerInfo);
        const errors = [];
        if (dataSourceStateResult.success) {
            const dataSourceState: DataSourceState = dataSourceStateResult.result;
            for (const datasource of dataSourceState.required_data_sources) {
                if (waitForModels.includes(`${datasource.name}.${datasource.model_name}`)) {
                    if (!datasource.model_state) {
                        // It was deleted in the meantime, so we can stop waiting for it.
                        continue;
                    }
                    if (datasource.model_state.status === "error") {
                        errors.push(
                            `There is an error with the model: ${datasource.model_name}: ${datasource.model_state.error}`
                        );
                    } else if (datasource.model_state.status !== "complete") {
                        // Check if the model is in the list of models to wait for
                        keepChecking = true;
                        break;
                    }
                }
            }
        } else {
            window.showErrorMessage(
                `There was an error computing the Data Sources state: ${dataSourceStateResult.message} (will stop waiting for models to be ready).`
            );
            return;
        }

        if (!keepChecking) {
            if (errors.length > 0) {
                window.showErrorMessage(
                    `Finished training models, but the following models had errors:\n${errors.join("\n")}`
                );
            }
            return;
        }
    }
    OUTPUT_CHANNEL.appendLine("Finished waiting for models to be ready (should not get here).");
};
