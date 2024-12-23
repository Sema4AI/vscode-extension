import { Uri, window, commands, ProgressLocation, Progress, CancellationToken } from "vscode";
import { logError, OUTPUT_CHANNEL } from "../channel";
import { RobotEntry, treeViewIdToTreeDataProvider } from "../viewsCommon";
import { DatasourceInfo, DataSourceState } from "../protocols";
import { langServer } from "../extension";
import {
    DATA_SERVER_STATUS_COMMAND_ID,
    startDataServerAndGetInfo,
    verifyDataExtensionIsInstalled,
} from "../dataExtension";
import { computeDataSourceState, DataServerConfig, getDataSourceCaption } from "./actionPackage";
import { sleep } from "../time";
import { findActionPackagePath } from "../actionServer";
import { SEMA4AI_LIST_ACTIONS_INTERNAL } from "../robocorpCommands";
import { QuickPickItemWithAction, showSelectOneQuickPick } from "../ask";
import { TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE } from "../robocorpViews";
import { RobotsTreeDataProvider } from "../viewsRobots";

function isExternalDatasource(datasource: DatasourceInfo): boolean {
    const externalEngines = ["custom", "files", "models"];
    return !externalEngines.includes(datasource.engine) && !datasource.engine.startsWith("prediction");
}

const waitForModelsToBeReady = async (actionPackageYamlDirectoryUri: string, dataServerInfo: DataServerConfig) => {
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
            return false;
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
            return false;
        }
    }
    OUTPUT_CHANNEL.appendLine("Finished waiting for models to be ready (should not get here).");
};

async function setupSingleDataSource(
    datasource: DatasourceInfo,
    dataServerInfo: any,
    actionPackageYamlDirectoryUri: string
): Promise<boolean> {
    const setupDataSourceResult = await langServer.sendRequest("setupDataSource", {
        action_package_yaml_directory_uri: actionPackageYamlDirectoryUri,
        datasource: datasource,
        data_server_info: dataServerInfo,
    });
    OUTPUT_CHANNEL.appendLine("setupDataSourceResult: " + JSON.stringify(setupDataSourceResult, null, 4));
    if (setupDataSourceResult["success"]) {
        const messages = setupDataSourceResult["result"];
        window.showInformationMessage(messages.join("\n"));
        await waitForModelsToBeReady(actionPackageYamlDirectoryUri, dataServerInfo);
    } else {
        const error = setupDataSourceResult["message"];
        window.showErrorMessage(`There was an error setting up the Data Source: ${error}`);
        return false;
    }

    return true;
}

async function fetchDataSources(actionPackageUri: Uri): Promise<DatasourceInfo[] | null> {
    const result = await commands.executeCommand(SEMA4AI_LIST_ACTIONS_INTERNAL, {
        action_package: actionPackageUri.toString(),
        collect_datasources: true,
    });

    if (!result["success"]) {
        window.showErrorMessage(result["message"] || "Unknown error fetching data sources.");
        return null;
    }

    const dataSources = result["result"].filter((ds: DatasourceInfo) => ds.kind === "datasource");
    if (dataSources.length === 0) {
        window.showInformationMessage("No Data Sources found.");
        return null;
    }

    return dataSources;
}

async function askAndSetupExternalDataSource() {
    const userChoice = await window.showInformationMessage(
        `There are external Data Sources that need to be configured. Do you want to configure them now?`,
        { modal: true },
        "Yes",
        "No"
    );
    if (userChoice === "Yes") {
        try {
            await commands.executeCommand("sema4ai-data.database.add");
        } catch (e) {
            logError("Could not run setup data source command", e, "ERR_DATA_SOURCE_SETUP");
            window.showErrorMessage(`"Could not run setup data source command: ${e.message}"`);
        }

        return;
    }
    if (userChoice === "No" || userChoice === undefined) {
        return;
    }
}

async function dropSingleDataSource(dataSource: DatasourceInfo, dataServerInfo: any): Promise<boolean> {
    const result = await langServer.sendRequest("dropDataSource", {
        datasource: dataSource,
        data_server_info: dataServerInfo,
    });

    if (!result["success"]) {
        window.showErrorMessage(result["message"] || `Failed to drop data source: ${getDataSourceCaption(dataSource)}`);
        return false;
    }
    return true;
}

async function fetchDataServerStatus(): Promise<any | null> {
    return window.withProgress(
        { location: ProgressLocation.Notification, title: "Getting data server status...", cancellable: false },
        async () => {
            const status = await commands.executeCommand(DATA_SERVER_STATUS_COMMAND_ID);
            return status["success"] ? status : null;
        }
    );
}

async function resolveActionPackageUri(entry?: RobotEntry): Promise<Uri | undefined> {
    if (entry) return entry.uri;

    return findActionPackagePath({ includeSemaOrg: false });
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

    await setupSingleDataSource(datasource, dataServerInfo, Uri.file(entry.robot.directory).toString());

    const dataProvider = treeViewIdToTreeDataProvider.get(
        TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE
    ) as RobotsTreeDataProvider;
    dataProvider.updateDatasourceStatuses();
};

export async function dropDataSource(entry?: RobotEntry) {
    if (!(await verifyDataExtensionIsInstalled())) {
        return;
    }
    const dataServerStatus = await fetchDataServerStatus();
    if (!dataServerStatus) {
        window.showErrorMessage("Unable to get the data server status. Please start the data server and try again.");
        return;
    }

    let datasource: DatasourceInfo | undefined;
    if (!entry) {
        let selectedActionPackage = await findActionPackagePath({ includeSemaOrg: false });
        if (!selectedActionPackage) {
            return;
        }

        const dataSources = await fetchDataSources(selectedActionPackage);
        if (!dataSources) {
            return;
        }

        let captions: QuickPickItemWithAction[] = new Array();
        for (const source of dataSources) {
            let caption: QuickPickItemWithAction = {
                "label": getDataSourceCaption(source),
                "action": source,
            };
            captions.push(caption);
        }
        let selectedItem = await showSelectOneQuickPick(captions, "Please select which Data Source to drop.");

        if (!selectedItem) {
            return;
        }

        datasource = selectedItem.action;
    } else {
        datasource = entry.extraData?.datasource;
        if (!datasource) {
            window.showErrorMessage("Data Source object was not provided in extraData.");
            return;
        }
        const userChoice = await window.showWarningMessage(
            `Are you sure you want to drop ${entry.label}?`,
            { modal: true },
            "Yes",
            "No"
        );
        if (userChoice === "No" || userChoice === undefined) {
            return;
        }
    }

    const result = await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Dropping Data Source...",
            cancellable: false,
        },
        async (progress: Progress<{ message?: string; increment?: number }>, token: CancellationToken) => {
            OUTPUT_CHANNEL.appendLine("Dropping Data Source: " + JSON.stringify(datasource, null, 4));
            return await langServer.sendRequest(
                "dropDataSource",
                {
                    "datasource": datasource,
                    "data_server_info": dataServerStatus["data"],
                },
                token
            );
        }
    );

    if (!result["success"]) {
        window.showErrorMessage(result["message"] || "Unknown error");
        return;
    }

    const dataProvider = treeViewIdToTreeDataProvider.get(
        TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE
    ) as RobotsTreeDataProvider;
    dataProvider.updateDatasourceStatuses();

    window.showInformationMessage(result["message"]);
}

export async function dropAllDataSources(entry?: RobotEntry) {
    if (!(await verifyDataExtensionIsInstalled())) {
        return;
    }

    const dataServerStatus = await fetchDataServerStatus();
    if (!dataServerStatus) {
        window.showErrorMessage("Unable to get the data server status. Please start the data server and try again.");
        return;
    }

    const actionPackageUri = await resolveActionPackageUri(entry);
    if (!actionPackageUri) {
        return;
    }

    const dataSources = await fetchDataSources(actionPackageUri);
    if (!dataSources) {
        return;
    }

    const areYouSureAsk = await window.showInformationMessage(
        `Are you sure you want to delete all data sources?`,
        { modal: true },
        "Yes",
        "No"
    );

    if (areYouSureAsk === undefined || areYouSureAsk === "No") {
        return;
    }

    let deleteExternalSources;
    const externalDataSources = dataSources.filter((ds) => {
        return isExternalDatasource(ds);
    });
    if (externalDataSources.length > 0) {
        deleteExternalSources = await window.showInformationMessage(
            `Do you want to remove external sources as well?`,
            { modal: true },
            "Yes",
            "No"
        );

        if (deleteExternalSources === undefined) {
            return;
        }
    }

    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Dropping Data Sources...",
            cancellable: true,
        },
        async (progress: Progress<{ message?: string; increment?: number }>, token: CancellationToken) => {
            for (const item of dataSources.reverse()) {
                if (token.isCancellationRequested) {
                    OUTPUT_CHANNEL.appendLine("Operation cancelled.");
                    return;
                }

                // Drop the external data sources last
                if (isExternalDatasource(item)) {
                    continue;
                }

                const success = await dropSingleDataSource(item, dataServerStatus["data"]);
                if (!success) return;

                progress.report({ message: `Dropped: ${getDataSourceCaption(item)}` });
            }

            if (deleteExternalSources === "Yes") {
                for (const item of externalDataSources) {
                    const success = await dropSingleDataSource(item, dataServerStatus["data"]);
                    if (!success) return;

                    progress.report({ message: `Dropped: ${getDataSourceCaption(item)}` });
                }
            }
            window.showInformationMessage("Data Sources dropped succesfully.");
        }
    );

    const dataProvider = treeViewIdToTreeDataProvider.get(
        TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE
    ) as RobotsTreeDataProvider;
    dataProvider.updateDatasourceStatuses();
}

export async function setupAllDataSources(entry?: RobotEntry) {
    if (!(await verifyDataExtensionIsInstalled())) {
        return;
    }

    let actionPackageUri;
    if (entry) {
        actionPackageUri = entry.robot.directory;
    } else {
        actionPackageUri = findActionPackagePath({ includeSemaOrg: false });
    }
    if (!actionPackageUri) {
        return;
    }

    const dataServerStatus = await fetchDataServerStatus();
    if (!dataServerStatus) {
        window.showErrorMessage("Unable to get the data server status. Please start the data server and try again.");
        return;
    }

    const dataSourceStateResult = await computeDataSourceState(actionPackageUri.toString(), dataServerStatus["data"]);
    if (!dataSourceStateResult.success) {
        window.showErrorMessage(
            `There was an error computing the Data Sources state: ${dataSourceStateResult.message}`
        );
        return;
    }
    const dataSources = dataSourceStateResult.result.required_data_sources;
    if (dataSources.length === 0) {
        window.showInformationMessage("No Data Sources found to configure.");
        return;
    }

    const unconfiguredExternalDataSources = dataSources.filter((ds) => !ds.configured && isExternalDatasource(ds));
    if (unconfiguredExternalDataSources.length > 0) {
        await askAndSetupExternalDataSource();
        return;
    }

    const unconfiguredDataSources = dataSources.filter((ds) => !ds.configured && !isExternalDatasource(ds));
    if (unconfiguredDataSources.length === 0) {
        window.showInformationMessage("All Data Sources are already configured.");
        return;
    }

    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "Setting up Data Sources...",
            cancellable: true,
        },
        async (progress: Progress<{ message?: string; increment?: number }>, token: CancellationToken) => {
            for (const item of unconfiguredDataSources) {
                if (token.isCancellationRequested) {
                    OUTPUT_CHANNEL.appendLine("Operation cancelled.");
                    return;
                }

                const success = await setupSingleDataSource(
                    item,
                    dataServerStatus["data"],
                    actionPackageUri.toString()
                );
                if (!success) return;

                if (item.model_name && success) {
                    const dataSourceStateResult = await computeDataSourceState(
                        actionPackageUri.toString(),
                        dataServerStatus["data"]
                    );
                    const dataSourceState: DataSourceState = dataSourceStateResult.result;
                    const currentDatasource = dataSourceState.required_data_sources.find(
                        (dataSource) =>
                            dataSource.engine === item.engine &&
                            dataSource.name === item.name &&
                            dataSource.model_name === item.model_name
                    );
                    if (currentDatasource.model_state?.status != "complete") {
                        window.showErrorMessage(
                            `There is an error with the model: ${currentDatasource.name}.${currentDatasource.model_name}: ${currentDatasource.model_state.error}`
                        );
                        return;
                    }

                    progress.report({ message: `Setup completed for: ${getDataSourceCaption(item)}` });
                }
            }
        }
    );

    const dataProvider = treeViewIdToTreeDataProvider.get(
        TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE
    ) as RobotsTreeDataProvider;
    dataProvider.updateDatasourceStatuses();
}
