import { Uri, window } from "vscode";
import { OUTPUT_CHANNEL } from "../channel";
import { RobotEntry } from "../viewsCommon";
import { DatasourceInfo } from "../protocols";
import { langServer } from "../extension";
import { startDataServerAndGetInfo } from "../dataExtension";

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

    OUTPUT_CHANNEL.appendLine("setupDataSource: " + JSON.stringify(entry));
    const datasource: DatasourceInfo = entry.extraData.datasource;
    const result = await langServer.sendRequest("setupDataSource", {
        action_package_yaml_directory_uri: Uri.file(entry.robot.directory).toString(),
        datasource: datasource,
        data_server_info: dataServerInfo,
    });
    if (result["success"]) {
        const messages = result["result"];
        window.showInformationMessage(messages.join("\n"));
    } else {
        const error = result["message"];
        window.showErrorMessage(error);
    }
};
