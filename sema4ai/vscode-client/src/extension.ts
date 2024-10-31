/*
Original work Copyright (c) Microsoft Corporation (MIT)
See ThirdPartyNotices.txt in the project root for license information.
All modifications Copyright (c) Robocorp Technologies Inc.
All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License")
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http: // www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

"use strict";

import * as net from "net";
import * as path from "path";
import * as vscode from "vscode";
import * as cp from "child_process";

import { workspace, Disposable, ExtensionContext, window, commands, extensions, env, Uri } from "vscode";
import { LanguageClientOptions, State } from "vscode-languageclient";
import { LanguageClient, ServerOptions } from "vscode-languageclient/node";
import * as playwright from "./playwright";
import { copySelectedToClipboard, removeLocator } from "./locators";
import * as views from "./views";
import * as roboConfig from "./robocorpSettings";
import { logError, OUTPUT_CHANNEL } from "./channel";
import { fileExists, getExtensionRelativeFile, uriExists } from "./files";
import {
    feedbackAnyError,
    feedbackRobocorpCodeError,
    getEndpointUrl,
    getRccLocation,
    getRobocorpHome,
    submitIssue,
} from "./rcc";
import { Timing } from "./time";
import {
    createRobot,
    uploadRobot,
    cloudLogin,
    cloudLogout,
    setPythonInterpreterFromRobotYaml,
    askAndRunRobotRCC,
    rccConfigurationDiagnostics,
    updateLaunchEnvironment,
    resolveInterpreter,
    listAndAskRobotSelection,
    createPackage,
} from "./activities";
import { handleProgressMessage, ProgressReport } from "./progress";
import { TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE, TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE } from "./robocorpViews";
import { askAndCreateRccTerminal } from "./rccTerminal";
import {
    deleteResourceInRobotContentTree,
    newFileInRobotContentTree,
    newFolderInRobotContentTree,
    renameResourceInRobotContentTree,
} from "./viewsRobotContent";
import {
    convertOutputWorkItemToInput,
    deleteWorkItemInWorkItemsTree,
    newWorkItemInWorkItemsTree,
    openWorkItemHelp,
} from "./viewsWorkItems";
import { FSEntry, LocatorEntry, refreshTreeView, RobotEntry } from "./viewsCommon";
import {
    SEMA4AI_CLOUD_LOGIN,
    SEMA4AI_CLOUD_LOGOUT,
    SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION,
    SEMA4AI_CONFIGURATION_DIAGNOSTICS,
    SEMA4AI_CONVERT_OUTPUT_WORK_ITEM_TO_INPUT,
    SEMA4AI_COPY_LOCATOR_TO_CLIPBOARD_INTERNAL,
    SEMA4AI_RCC_TERMINAL_CREATE_ROBOT_TREE_SELECTION,
    SEMA4AI_CREATE_ROBOT,
    SEMA4AI_DEBUG_ROBOT_RCC,
    SEMA4AI_DELETE_RESOURCE_IN_ROBOT_CONTENT_VIEW,
    SEMA4AI_DELETE_WORK_ITEM_IN_WORK_ITEMS_VIEW,
    SEMA4AI_EDIT_ROBOCORP_INSPECTOR_LOCATOR,
    SEMA4AI_GET_LANGUAGE_SERVER_PYTHON,
    SEMA4AI_GET_LANGUAGE_SERVER_PYTHON_INFO,
    SEMA4AI_HELP_WORK_ITEMS,
    SEMA4AI_NEW_FILE_IN_ROBOT_CONTENT_VIEW,
    SEMA4AI_NEW_FOLDER_IN_ROBOT_CONTENT_VIEW,
    SEMA4AI_NEW_ROBOCORP_INSPECTOR_BROWSER,
    SEMA4AI_NEW_ROBOCORP_INSPECTOR_IMAGE,
    SEMA4AI_NEW_WORK_ITEM_IN_WORK_ITEMS_VIEW,
    SEMA4AI_OPEN_CLOUD_HOME,
    SEMA4AI_OPEN_ROBOT_TREE_SELECTION,
    SEMA4AI_RCC_TERMINAL_NEW,
    SEMA4AI_REFRESH_CLOUD_VIEW,
    SEMA4AI_REFRESH_ROBOTS_VIEW,
    SEMA4AI_REFRESH_ROBOT_CONTENT_VIEW,
    SEMA4AI_REMOVE_LOCATOR_FROM_JSON,
    SEMA4AI_RENAME_RESOURCE_IN_ROBOT_CONTENT_VIEW,
    SEMA4AI_ROBOTS_VIEW_TASK_DEBUG,
    SEMA4AI_ROBOTS_VIEW_TASK_RUN,
    SEMA4AI_RUN_ROBOT_RCC,
    SEMA4AI_SET_PYTHON_INTERPRETER,
    SEMA4AI_SUBMIT_ISSUE,
    SEMA4AI_SUBMIT_ISSUE_INTERNAL,
    SEMA4AI_UPDATE_LAUNCH_ENV,
    SEMA4AI_UPLOAD_ROBOT_TO_CLOUD,
    SEMA4AI_ERROR_FEEDBACK_INTERNAL,
    SEMA4AI_OPEN_EXTERNALLY,
    SEMA4AI_OPEN_IN_VS_CODE,
    SEMA4AI_REVEAL_IN_EXPLORER,
    SEMA4AI_REVEAL_ROBOT_IN_EXPLORER,
    SEMA4AI_CONNECT_WORKSPACE,
    SEMA4AI_DISCONNECT_WORKSPACE,
    SEMA4AI_OPEN_VAULT_HELP,
    SEMA4AI_CLEAR_ENV_AND_RESTART,
    SEMA4AI_NEW_ROBOCORP_INSPECTOR_WINDOWS,
    SEMA4AI_SHOW_OUTPUT,
    SEMA4AI_SHOW_INTERPRETER_ENV_ERROR,
    SEMA4AI_FEEDBACK_INTERNAL,
    SEMA4AI_OPEN_FLOW_EXPLORER_TREE_SELECTION,
    SEMA4AI_OPEN_LOCATORS_JSON,
    SEMA4AI_OPEN_ROBOT_CONDA_TREE_SELECTION,
    SEMA4AI_PROFILE_IMPORT,
    SEMA4AI_PROFILE_SWITCH,
    SEMA4AI_RUN_ROBOCORPS_PYTHON_TASK,
    SEMA4AI_DEBUG_ROBOCORPS_PYTHON_TASK,
    SEMA4AI_OPEN_PLAYWRIGHT_RECORDER,
    SEMA4AI_INSPECTOR,
    SEMA4AI_INSPECTOR_DUPLICATE,
    SEMA4AI_START_ACTION_SERVER,
    SEMA4AI_OPEN_PACKAGE_YAML_TREE_SELECTION,
    SEMA4AI_ROBOTS_VIEW_ACTION_RUN,
    SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG,
    SEMA4AI_ROBOTS_VIEW_ACTION_EDIT_INPUT,
    SEMA4AI_ROBOTS_VIEW_ACTION_OPEN,
    SEMA4AI_RUN_ACTION_FROM_ACTION_PACKAGE,
    SEMA4AI_DEBUG_ACTION_FROM_ACTION_PACKAGE,
    SEMA4AI_CREATE_ACTION_PACKAGE,
    SEMA4AI_CREATE_TASK_OR_ACTION_OR_AGENT_PACKAGE,
    SEMA4AI_NEW_ROBOCORP_INSPECTOR_JAVA,
    SEMA4AI_DOWNLOAD_ACTION_SERVER,
    SEMA4AI_PACKAGE_ENVIRONMENT_REBUILD,
    SEMA4AI_ACTION_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP,
    SEMA4AI_ACTION_SERVER_CLOUD_LOGIN,
    SEMA4AI_ACTION_SERVER_PACKAGE_PUBLISH,
    SEMA4AI_ACTION_SERVER_PACKAGE_BUILD,
    SEMA4AI_ACTION_SERVER_PACKAGE_METADATA,
    SEMA4AI_OAUTH2_LOGOUT,
    SEMA4AI_CREATE_AGENT_PACKAGE,
    SEMA4AI_PACK_AGENT_PACKAGE,
    SEMA4AI_OPEN_RUNBOOK_TREE_SELECTION,
    SEMA4AI_AGENT_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP,
    SEMA4AI_AGENT_PACKAGE_IMPORT,
    SEMA4AI_UPDATE_AGENT_VERSION,
    SEMA4AI_REFRESH_AGENT_SPEC,
    SEMA4AI_COLLAPSE_ALL_ENTRIES,
    SEMA4AI_IMPORT_ACTION_PACKAGE,
    SEMA4AI_RUN_ACTION_PACKAGE_DEV_TASK,
} from "./robocorpCommands";
import { installWorkspaceWatcher } from "./pythonExtIntegration";
import { refreshCloudTreeView } from "./viewsRobocorp";
import { connectWorkspace, disconnectWorkspace } from "./vault";
import { CACHE_KEY_LAST_WORKED, getLanguageServerPythonInfoUncached } from "./extensionCreateEnv";
import { registerDebugger } from "./debugger";
import { clearRCCEnvironments, clearRobocorpCodeCaches, computeEnvsToCollect } from "./clear";
import { Mutex } from "./mutex";
import { mergeEnviron } from "./subprocess";
import { feedback } from "./rcc";
import { showSubmitIssueUI } from "./submitIssue";
import { profileImport, profileSwitch } from "./profiles";
import { registerLinkProviders } from "./robo/linkProvider";
import { runRobocorpTasks } from "./robo/runRobocorpTasks";
import { RobotOutputViewProvider } from "./output/outView";
import { setupDebugSessionOutViewIntegration } from "./output/outViewRunIntegration";
import { showInspectorUI } from "./inspector/inspectorView";
import { IAppRoutes } from "./inspector/protocols";
import { actionServerCloudLogin, downloadOrGetActionServerLocation, startActionServer } from "./actionServer";
import {
    askAndRunRobocorpActionFromActionPackage,
    createActionPackage,
    publishActionPackage,
    buildActionPackage,
    openMetadata,
} from "./robo/actionPackage";
import { oauth2Logout } from "./robo/oauth2InInput";
import {
    createAgentPackage,
    selectAndPackAgentPackage,
    packAgentPackage,
    importAgentPackage,
    updateAgentVersion,
    refreshAgentSpec,
} from "./robo/agentPackage";
import { getSema4AIStudioURLForAgentZipPath, getSema4AIStudioURLForFolderPath } from "./deepLink";
import { LocalPackageMetadataInfo } from "./protocols";
import { importActionPackage } from "./robo/importActions";
import { DevTaskInfo, runActionPackageDevTask } from "./robo/runActionPackageDevTask";

interface InterpreterInfo {
    pythonExe: string;
    environ?: { [key: string]: string };
    additionalPythonpathEntries: string[];
}

const clientOptions: LanguageClientOptions = {
    documentSelector: [
        { language: "json", pattern: "**/locators.json" },
        { language: "yaml", pattern: "**/conda.yaml" },
        { language: "yaml", pattern: "**/action-server.yaml" },
        { language: "yaml", pattern: "**/robot.yaml" },
        { language: "yaml", pattern: "**/package.yaml" },
        { language: "yaml", pattern: "**/agent-spec.yaml" },

        // Needed to detect tasks decorated with @task (from robocorp.tasks).
        // Needed to detect actions decorated with @action (from sema4ai.actions).
        { language: "python", pattern: "**/*.py" },
    ],
    synchronize: {
        configurationSection: "sema4ai",
    },
    outputChannel: OUTPUT_CHANNEL,
};

const serverOptions: ServerOptions = async function () {
    let executableAndEnv: InterpreterInfo | undefined;
    function onNoPython() {
        OUTPUT_CHANNEL.appendLine(
            "Unable to activate Sema4.ai extension because python executable from RCC environment was not provided.\n" +
                " -- Most common reason is that the environment couldn't be created due to network connectivity issues.\n" +
                " -- Please fix the error and restart VSCode."
        );
        C.useErrorStubs = true;
        notifyOfInitializationErrorShowOutputTab();
    }

    try {
        // Note: we need to get it even in the case where we connect through a socket
        // as the debugger needs it afterwards to do other launches.
        executableAndEnv = await getLanguageServerPythonInfo();
        if (!executableAndEnv) {
            throw new Error("Unable to get language server python info.");
        }
    } catch (error) {
        onNoPython();
        logError("Error getting Python", error, "INIT_PYTHON_ERR");
        throw error;
    }

    OUTPUT_CHANNEL.appendLine("Using python executable: " + executableAndEnv.pythonExe);

    let port: number = roboConfig.getLanguageServerTcpPort();
    if (port) {
        // For TCP server needs to be started seperately
        OUTPUT_CHANNEL.appendLine("Connecting to language server in port: " + port);
        return new Promise((resolve, reject) => {
            var client = new net.Socket();
            client.setTimeout(2000, reject);
            try {
                client.connect(port, "127.0.0.1", function () {
                    resolve({
                        reader: client,
                        writer: client,
                    });
                });
            } catch (error) {
                reject(error);
            }
        });
    } else {
        let targetFile: string = getExtensionRelativeFile("../../src/sema4ai_code/__main__.py");
        if (!targetFile) {
            OUTPUT_CHANNEL.appendLine("Error resolving ../../src/sema4ai_code/__main__.py");
            C.useErrorStubs = true;
            notifyOfInitializationErrorShowOutputTab();
            feedbackRobocorpCodeError("INIT_MAIN_NOT_FOUND");
            return;
        }

        let args: Array<string> = ["-u", targetFile];
        let lsArgs = roboConfig.getLanguageServerArgs();
        if (lsArgs && lsArgs.length >= 1) {
            args = args.concat(lsArgs);
        } else {
            // Default is using simple verbose mode (shows critical/info but not debug).
            args = args.concat(["-v"]);
        }

        OUTPUT_CHANNEL.appendLine("Starting Sema4.ai with args: " + executableAndEnv.pythonExe + " " + args.join(" "));

        let src: string = path.resolve(__dirname, "../../src");
        let executableAndEnvEnviron = {};
        if (executableAndEnv.environ) {
            executableAndEnvEnviron = executableAndEnv.environ;
        }

        let finalEnv = mergeEnviron({ ...executableAndEnvEnviron, PYTHONPATH: src });
        const serverProcess = cp.spawn(executableAndEnv.pythonExe, args, {
            env: finalEnv,
            cwd: path.dirname(executableAndEnv.pythonExe),
        });
        if (!serverProcess || !serverProcess.pid) {
            throw new Error(`Launching server using command ${executableAndEnv.pythonExe} with args: ${args} failed.`);
        }
        return serverProcess;
    }
};

async function notifyOfInitializationErrorShowOutputTab(msg?: string) {
    OUTPUT_CHANNEL.show();
    if (!msg) {
        msg = "Unable to activate Sema4.ai extension. Please see: Output > Sema4.ai for more details.";
    }
    window.showErrorMessage(msg);
    const selection = await window.showErrorMessage(msg, "Show Output > Sema4.ai");
    if (selection) {
        OUTPUT_CHANNEL.show();
    }
}

class CommandRegistry {
    private context: ExtensionContext;
    public registerErrorStubs: boolean = false;
    public useErrorStubs: boolean = false;
    public errorMessage: string | undefined = undefined;

    public constructor(context: ExtensionContext) {
        this.context = context;
    }

    public registerWithoutStub(command: string, callback: (...args: any[]) => any, thisArg?: any): void {
        this.context.subscriptions.push(commands.registerCommand(command, callback));
    }

    /**
     * Registers with a stub so that an error may be shown if the initialization didn't work.
     */
    public register(command: string, callback: (...args: any[]) => any, thisArg?: any): void {
        const that = this;
        async function redirect() {
            if (that.useErrorStubs) {
                notifyOfInitializationErrorShowOutputTab(that.errorMessage);
            } else {
                return await callback.apply(thisArg, arguments);
            }
        }

        this.context.subscriptions.push(commands.registerCommand(command, redirect));
    }
}

async function cloudLoginShowConfirmationAndRefresh() {
    let loggedIn = await cloudLogin();
    if (loggedIn) {
        window.showInformationMessage("Successfully logged in Control Room.");
    }
    refreshCloudTreeView();
}

async function cloudLogoutAndRefresh() {
    await cloudLogout();
    refreshCloudTreeView();
}

function registerRobocorpCodeCommands(C: CommandRegistry, context: ExtensionContext) {
    C.register(SEMA4AI_START_ACTION_SERVER, startActionServer);

    C.register(SEMA4AI_GET_LANGUAGE_SERVER_PYTHON, () => getLanguageServerPython());
    C.register(SEMA4AI_GET_LANGUAGE_SERVER_PYTHON_INFO, () => getLanguageServerPythonInfo());
    C.register(SEMA4AI_CREATE_ROBOT, () => createRobot());
    C.register(SEMA4AI_CREATE_ACTION_PACKAGE, (agentPackage?: LocalPackageMetadataInfo) =>
        createActionPackage(agentPackage)
    );
    C.register(SEMA4AI_CREATE_TASK_OR_ACTION_OR_AGENT_PACKAGE, () => createPackage());
    C.register(SEMA4AI_DOWNLOAD_ACTION_SERVER, async () => {
        try {
            const location = await downloadOrGetActionServerLocation();
            if (location) {
                // If it failed a message should've been displayed already.
                window.showInformationMessage(`Action Server downloaded to: ${location}`);
            }
        } catch (error) {
            logError("Error downloading Action Server", error, "ERR_DOWNLOAD_ACTION_SERVER");
            window.showErrorMessage(
                "There was an error downloading the action server. See `OUTPUT > Sema4.ai` for more information."
            );
        }
    });
    C.register(SEMA4AI_UPLOAD_ROBOT_TO_CLOUD, () => uploadRobot());
    C.register(SEMA4AI_CONFIGURATION_DIAGNOSTICS, () => rccConfigurationDiagnostics());
    C.register(SEMA4AI_RUN_ROBOT_RCC, () => askAndRunRobotRCC(true));
    C.register(SEMA4AI_DEBUG_ROBOT_RCC, () => askAndRunRobotRCC(false));
    C.register(SEMA4AI_RUN_ACTION_FROM_ACTION_PACKAGE, () => askAndRunRobocorpActionFromActionPackage(true));
    C.register(SEMA4AI_DEBUG_ACTION_FROM_ACTION_PACKAGE, () => askAndRunRobocorpActionFromActionPackage(false));
    C.register(SEMA4AI_SET_PYTHON_INTERPRETER, () => setPythonInterpreterFromRobotYaml());
    C.register(SEMA4AI_REFRESH_ROBOTS_VIEW, () => refreshTreeView(TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE));
    C.register(SEMA4AI_REFRESH_CLOUD_VIEW, () => refreshCloudTreeView());
    C.register(SEMA4AI_ROBOTS_VIEW_TASK_RUN, (entry: RobotEntry) => views.runSelectedRobot(true, entry));
    C.register(SEMA4AI_ROBOTS_VIEW_TASK_DEBUG, (entry: RobotEntry) => views.runSelectedRobot(false, entry));
    C.register(SEMA4AI_ROBOTS_VIEW_ACTION_RUN, (entry: RobotEntry) => views.runSelectedAction(true, entry));
    C.register(SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG, (entry: RobotEntry) => views.runSelectedAction(false, entry));
    C.register(SEMA4AI_ROBOTS_VIEW_ACTION_EDIT_INPUT, (entry: RobotEntry) => views.editInput(entry));
    C.register(SEMA4AI_ROBOTS_VIEW_ACTION_OPEN, (entry: RobotEntry) => views.openAction(entry));
    C.register(SEMA4AI_RUN_ROBOCORPS_PYTHON_TASK, (args: string[] | undefined) => runRobocorpTasks(true, args));
    C.register(SEMA4AI_DEBUG_ROBOCORPS_PYTHON_TASK, (args: string[] | undefined) => runRobocorpTasks(false, args));
    C.register(SEMA4AI_EDIT_ROBOCORP_INSPECTOR_LOCATOR, (locator?: LocatorEntry): Promise<void> => {
        return showInspectorUI(context, IAppRoutes.LOCATORS_MANAGER);
    });
    C.register(SEMA4AI_OPEN_PLAYWRIGHT_RECORDER, (useTreeSelected: boolean = false) =>
        playwright.openPlaywrightRecorder(useTreeSelected)
    );
    C.register(SEMA4AI_COPY_LOCATOR_TO_CLIPBOARD_INTERNAL, (locator?: LocatorEntry) =>
        copySelectedToClipboard(locator)
    );
    C.register(SEMA4AI_REMOVE_LOCATOR_FROM_JSON, (locator?: LocatorEntry) => removeLocator(locator));
    C.register(SEMA4AI_OPEN_ROBOT_TREE_SELECTION, (robot: RobotEntry) => views.openRobotTreeSelection(robot));
    C.register(SEMA4AI_OPEN_ROBOT_CONDA_TREE_SELECTION, (robot: RobotEntry) =>
        views.openRobotCondaTreeSelection(robot)
    );
    C.register(SEMA4AI_OPEN_PACKAGE_YAML_TREE_SELECTION, (robot: RobotEntry) => views.openPackageTreeSelection(robot));
    C.register(SEMA4AI_OPEN_LOCATORS_JSON, (locatorRoot) => views.openLocatorsJsonTreeSelection());
    C.register(SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION, (robot: RobotEntry) =>
        views.cloudUploadRobotTreeSelection(robot)
    );
    C.register(SEMA4AI_OPEN_FLOW_EXPLORER_TREE_SELECTION, (robot: RobotEntry) =>
        commands.executeCommand("robot.openFlowExplorer", Uri.file(robot.robot.directory).toString())
    );
    C.register(SEMA4AI_RCC_TERMINAL_CREATE_ROBOT_TREE_SELECTION, (robot: RobotEntry) =>
        views.createRccTerminalTreeSelection(robot)
    );
    C.register(SEMA4AI_RCC_TERMINAL_NEW, () => askAndCreateRccTerminal());
    C.register(SEMA4AI_REFRESH_ROBOT_CONTENT_VIEW, () => refreshTreeView(TREE_VIEW_SEMA4AI_PACKAGE_CONTENT_TREE));
    C.register(SEMA4AI_NEW_FILE_IN_ROBOT_CONTENT_VIEW, newFileInRobotContentTree);
    C.register(SEMA4AI_NEW_FOLDER_IN_ROBOT_CONTENT_VIEW, newFolderInRobotContentTree);
    C.register(SEMA4AI_DELETE_RESOURCE_IN_ROBOT_CONTENT_VIEW, deleteResourceInRobotContentTree);
    C.register(SEMA4AI_RENAME_RESOURCE_IN_ROBOT_CONTENT_VIEW, renameResourceInRobotContentTree);
    C.register(SEMA4AI_UPDATE_LAUNCH_ENV, updateLaunchEnvironment);
    C.register(SEMA4AI_CONNECT_WORKSPACE, connectWorkspace);
    C.register(SEMA4AI_DISCONNECT_WORKSPACE, disconnectWorkspace);
    C.register(SEMA4AI_OPEN_CLOUD_HOME, async () => {
        const cloudBaseUrl = await getEndpointUrl("cloud-ui");
        commands.executeCommand("vscode.open", Uri.parse(cloudBaseUrl + "home"));
    });
    C.register(SEMA4AI_OPEN_VAULT_HELP, async () => {
        const cloudBaseUrl = await getEndpointUrl("docs");
        commands.executeCommand(
            "vscode.open",
            Uri.parse(cloudBaseUrl + "development-guide/variables-and-secrets/vault")
        );
    });
    C.register(SEMA4AI_OPEN_EXTERNALLY, async (item: FSEntry) => {
        if (item.filePath) {
            if (await fileExists(item.filePath)) {
                env.openExternal(Uri.file(item.filePath));
                return;
            }
        }
        window.showErrorMessage("Unable to open: " + item.filePath + " (file does not exist).");
    });
    C.register(SEMA4AI_OPEN_IN_VS_CODE, async (item: FSEntry) => {
        if (item.filePath) {
            if (await fileExists(item.filePath)) {
                commands.executeCommand("vscode.open", Uri.file(item.filePath));
                return;
            }
        }
        window.showErrorMessage("Unable to open: " + item.filePath + " (file does not exist).");
    });
    C.register(SEMA4AI_REVEAL_IN_EXPLORER, async (item: FSEntry) => {
        if (item.filePath) {
            if (await fileExists(item.filePath)) {
                commands.executeCommand("revealFileInOS", Uri.file(item.filePath));
                return;
            }
        }
        window.showErrorMessage("Unable to reveal in explorer: " + item.filePath + " (file does not exist).");
    });
    C.register(SEMA4AI_REVEAL_ROBOT_IN_EXPLORER, async (item: RobotEntry) => {
        if (item.uri) {
            if (await uriExists(item.uri)) {
                commands.executeCommand("revealFileInOS", item.uri);
                return;
            }
        }
        window.showErrorMessage("Unable to reveal in explorer: " + item.uri + " (Robot does not exist).");
    });
    C.register(SEMA4AI_CONVERT_OUTPUT_WORK_ITEM_TO_INPUT, convertOutputWorkItemToInput);
    C.register(SEMA4AI_CLOUD_LOGIN, () => cloudLoginShowConfirmationAndRefresh());
    C.register(SEMA4AI_CLOUD_LOGOUT, () => cloudLogoutAndRefresh());
    C.register(SEMA4AI_NEW_WORK_ITEM_IN_WORK_ITEMS_VIEW, newWorkItemInWorkItemsTree);
    C.register(SEMA4AI_DELETE_WORK_ITEM_IN_WORK_ITEMS_VIEW, deleteWorkItemInWorkItemsTree);
    C.register(SEMA4AI_HELP_WORK_ITEMS, openWorkItemHelp);
    C.register(SEMA4AI_PROFILE_IMPORT, async () => await profileImport());
    C.register(SEMA4AI_PROFILE_SWITCH, async () => await profileSwitch());
    C.register(SEMA4AI_ACTION_SERVER_CLOUD_LOGIN, async () => await actionServerCloudLogin());
    C.register(SEMA4AI_ACTION_SERVER_PACKAGE_PUBLISH, publishActionPackage);
    C.register(SEMA4AI_ACTION_SERVER_PACKAGE_BUILD, buildActionPackage);
    C.register(SEMA4AI_ACTION_SERVER_PACKAGE_METADATA, openMetadata);
    C.register(SEMA4AI_OAUTH2_LOGOUT, oauth2Logout);
    C.register(SEMA4AI_CREATE_AGENT_PACKAGE, createAgentPackage);
    C.register(SEMA4AI_AGENT_PACKAGE_IMPORT, importAgentPackage);
    C.register(SEMA4AI_PACK_AGENT_PACKAGE, async (agentPath: string) => selectAndPackAgentPackage(agentPath));
    C.register(SEMA4AI_OPEN_RUNBOOK_TREE_SELECTION, (robot: RobotEntry) => views.openRunbookTreeSelection(robot));
    C.register(SEMA4AI_UPDATE_AGENT_VERSION, async (agentPath: string) => updateAgentVersion(agentPath));
    C.register(SEMA4AI_REFRESH_AGENT_SPEC, async (agentPath: string) => refreshAgentSpec(agentPath));
    C.register(SEMA4AI_COLLAPSE_ALL_ENTRIES, collapseAllEntries);
    C.register(SEMA4AI_IMPORT_ACTION_PACKAGE, async (agentPath: string) => importActionPackage(agentPath));
    C.register(SEMA4AI_RUN_ACTION_PACKAGE_DEV_TASK, async (devTaskInfo: DevTaskInfo | undefined) =>
        runActionPackageDevTask(devTaskInfo)
    );
}

async function clearEnvAndRestart() {
    await window.withProgress(
        {
            location: vscode.ProgressLocation.Window,
            title: "Clearing environments and restarting Sema4.ai.",
            cancellable: false,
        },
        clearEnvsAndRestart
    );
}

async function clearEnvsAndRestart(progress: vscode.Progress<{ message?: string; increment?: number }>) {
    let allOk: boolean = true;
    let okToRestartRFLS = false;
    try {
        await langServerMutex.dispatch(async () => {
            let result = await clearEnvsLocked(progress);
            if (!result) {
                // Something didn't work out...
                return;
            }
            okToRestartRFLS = result["okToRestartRFLS"];
        });
        const timing = new Timing();
        progress.report({
            "message": `Waiting for Sema4.ai to be ready.`,
        });
        await langServer.onReady();
        let msg = "Restarted Sema4.ai. Took: " + timing.getTotalElapsedAsStr();
        progress.report({
            "message": msg,
        });
        OUTPUT_CHANNEL.appendLine(msg);
    } catch (err) {
        allOk = false;
        const msg = "Error restarting Sema4.ai";
        notifyOfInitializationErrorShowOutputTab(msg);
        logError(msg, err, "INIT_RESTART_ROBOCORP_CODE");
    } finally {
        if (allOk) {
            window.showInformationMessage("RCC Environments cleared and Sema4.ai restarted.");
            C.useErrorStubs = false;
        } else {
            C.useErrorStubs = true;
        }

        if (okToRestartRFLS) {
            progress.report({
                "message": `Starting Robot Framework Language Server.`,
            });
            await commands.executeCommand("robot.clearCachesAndRestartProcesses.finish.internal");
        }
    }
}

async function clearEnvsLocked(progress: vscode.Progress<{ message?: string; increment?: number }>) {
    const rccLocation = await getRccLocation();
    if (!rccLocation) {
        let msg = "Unable to clear caches because RCC is not available.";
        OUTPUT_CHANNEL.appendLine(msg);
        window.showErrorMessage(msg);
        return undefined;
    }

    const robocorpHome = await getRobocorpHome();
    progress.report({
        "message": `Computing environments to collect.`,
    });
    const envsToLoCollect = await computeEnvsToCollect(rccLocation, robocorpHome);

    // Clear our cache since we're killing that environment...
    globalCachedPythonInfo = undefined;

    C.useErrorStubs = true; // Prevent any calls while restarting...
    C.errorMessage = "Unable to use Sema4.ai actions while clearing environments.";
    let okToRestartRFLS = false;
    try {
        let timing = new Timing();
        const extension = extensions.getExtension("robocorp.robotframework-lsp");
        if (extension) {
            progress.report({
                "message": `Stopping Robot Framework Language Server.`,
            });
            // In this case we also need to stop the language server.
            okToRestartRFLS = await commands.executeCommand("robot.clearCachesAndRestartProcesses.start.internal");
            OUTPUT_CHANNEL.appendLine(
                "Stopped Robot Framework Language Server. Took: " + timing.getTotalElapsedAsStr()
            );
        }

        let timingStop = new Timing();
        progress.report({
            "message": `Stopping Sema4.ai.`,
        });
        await langServer.stop();
        OUTPUT_CHANNEL.appendLine("Stopped Sema4.ai. Took: " + timingStop.getTotalElapsedAsStr());

        if (envsToLoCollect) {
            await clearRCCEnvironments(rccLocation, robocorpHome, envsToLoCollect, progress);
        }

        try {
            progress.report({
                "message": `Clearing Sema4.ai caches.`,
            });
            await clearRobocorpCodeCaches(robocorpHome);
        } catch (error) {
            let msg = "Error clearing Sema4.ai caches.";
            logError(msg, error, "RCC_CLEAR_ENV");
        }

        progress.report({
            "message": `Starting Sema4.ai.`,
        });
        langServer.start();
    } finally {
        C.errorMessage = undefined;
    }
    return { "okToRestartRFLS": okToRestartRFLS };
}

export let langServer: LanguageClient;
let C: CommandRegistry;
export let globalCachedPythonInfo: InterpreterInfo;
const langServerMutex: Mutex = new Mutex();
export let GLOBAL_STATE: undefined | vscode.Memento = undefined;

function checkDeprecatedRobocorpCoreExtension() {
    const robocorpExtensionId = "Robocorp.robocorp-code";
    const robocorpExtension = vscode.extensions.getExtension(robocorpExtensionId);
    if (robocorpExtension) {
        OUTPUT_CHANNEL.appendLine(`Found deprecated ${robocorpExtension.packageJSON.displayName} extension.`);
        vscode.window
            .showWarningMessage(
                `The deprecated "${robocorpExtension.packageJSON.displayName}" extension found. It may cause conflicts with the rebranded Sema4ai extension.`,
                "Open Extensions"
            )
            .then((selection) => {
                if (selection === "Open Extensions") {
                    vscode.commands.executeCommand("workbench.view.extensions");
                }
            });
    }
}

export async function activate(context: ExtensionContext) {
    GLOBAL_STATE = context.globalState;
    let timing = new Timing();
    OUTPUT_CHANNEL.appendLine("Activating Sema4.ai extension.");

    checkDeprecatedRobocorpCoreExtension();

    registerLinkProviders(context);

    C = new CommandRegistry(context);

    try {
        return await langServerMutex.dispatch(async () => {
            let ret = await doActivate(context, C);
            OUTPUT_CHANNEL.appendLine("Sema4.ai initialization finished. Took: " + timing.getTotalElapsedAsStr());
            return ret;
        });
    } catch (error) {
        logError("Error initializing Sema4.ai extension", error, "INIT_ROBOCORP_CODE_ERROR");
        C.useErrorStubs = true;
        notifyOfInitializationErrorShowOutputTab();
    }
}

interface ExecuteWorkspaceCommandArgs {
    command: string;
    arguments: any;
}

export async function doActivate(context: ExtensionContext, C: CommandRegistry) {
    // Note: register the submit issue actions early on so that we can later actually
    // report startup errors.
    C.registerWithoutStub(SEMA4AI_SUBMIT_ISSUE, async () => {
        await showSubmitIssueUI(context);
    });

    // register Inspector applications
    C.registerWithoutStub(SEMA4AI_INSPECTOR, async () => {
        await showInspectorUI(context, IAppRoutes.LOCATORS_MANAGER);
    });
    C.registerWithoutStub(SEMA4AI_INSPECTOR_DUPLICATE, async () => {
        await showInspectorUI(context, IAppRoutes.LOCATORS_MANAGER);
    });
    C.register(
        SEMA4AI_NEW_ROBOCORP_INSPECTOR_BROWSER,
        async () => await showInspectorUI(context, IAppRoutes.WEB_INSPECTOR)
    );
    C.register(
        SEMA4AI_NEW_ROBOCORP_INSPECTOR_WINDOWS,
        async () => await showInspectorUI(context, IAppRoutes.WINDOWS_INSPECTOR)
    );
    C.register(
        SEMA4AI_NEW_ROBOCORP_INSPECTOR_IMAGE,
        async () => await showInspectorUI(context, IAppRoutes.IMAGE_INSPECTOR)
    );
    C.register(
        SEMA4AI_NEW_ROBOCORP_INSPECTOR_JAVA,
        async () => await showInspectorUI(context, IAppRoutes.JAVA_INSPECTOR)
    );

    // i.e.: allow other extensions to also use our submit issue api.
    C.registerWithoutStub(
        SEMA4AI_SUBMIT_ISSUE_INTERNAL,
        (
            dialogMessage: string,
            email: string,
            errorName: string,
            errorCode: string,
            errorMessage: string,
            files: string[]
        ) => submitIssue(dialogMessage, email, errorName, errorCode, errorMessage, files)
    );

    C.registerWithoutStub(SEMA4AI_SHOW_OUTPUT, () => OUTPUT_CHANNEL.show());
    C.registerWithoutStub(SEMA4AI_SHOW_INTERPRETER_ENV_ERROR, async (params) => {
        const fileWithError = params.fileWithError;
        vscode.window.showTextDocument(Uri.file(fileWithError));
    });

    // i.e.: allow other extensions to also use our error feedback api.
    C.registerWithoutStub(SEMA4AI_ERROR_FEEDBACK_INTERNAL, (errorSource: string, errorCode: string) =>
        feedbackAnyError(errorSource, errorCode)
    );
    // i.e.: allow other extensions to also use our feedback api.
    C.registerWithoutStub(SEMA4AI_FEEDBACK_INTERNAL, (name: string, value: string) => feedback(name, value));

    C.register(SEMA4AI_PACKAGE_ENVIRONMENT_REBUILD, async (actionPackagePath?: vscode.Uri) => {
        if (!actionPackagePath) {
            const selected = await listAndAskRobotSelection(
                "Please select the Action Package for which you'd like to rebuild the environment",
                "Unable to continue because no Action Package was found in the workspace.",
                { showActionPackages: true, showTaskPackages: false, showAgentPackages: false }
            );
            if (!selected) {
                return;
            }
            actionPackagePath = vscode.Uri.file(selected.filePath);
        }

        const result = await resolveInterpreter(actionPackagePath.fsPath);
        if (result.success) {
            vscode.window.showInformationMessage(`Environment built & cached. Python interpreter loaded.`);
        } else {
            vscode.window.showErrorMessage(`Error resolving interpreter: ${result.message}`);
        }
    });

    C.register(SEMA4AI_ACTION_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP, async (actionPackagePath?: vscode.Uri) => {
        if (!actionPackagePath) {
            const selected = await listAndAskRobotSelection(
                "Please select the Action Package that you'd like to be published to the Sema4.ai Studio",
                "Unable to continue because no Action Package was found in the workspace.",
                { showActionPackages: true, showTaskPackages: false, showAgentPackages: false, includeSemaOrg: false }
            );
            if (!selected) {
                vscode.window.showErrorMessage(`Please open an Action Package and try again`);
                return;
            }
            actionPackagePath = vscode.Uri.file(selected.filePath);
        }

        const sema4aiStudioAPIPath = getSema4AIStudioURLForFolderPath(actionPackagePath.fsPath);
        const opened = vscode.env.openExternal(vscode.Uri.parse(sema4aiStudioAPIPath));
        if (opened) {
            vscode.window.showInformationMessage(`Publishing to Sema4.ai Studio succeeded`);
        } else {
            vscode.window.showErrorMessage(`Publishing to Sema4.ai Studio failed`);
        }
    });

    C.register(SEMA4AI_AGENT_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP, async (agentPackagePath?: string) => {
        if (!agentPackagePath) {
            const selected = await listAndAskRobotSelection(
                "Please select the Agent Package that you'd like to be published to the Sema4.ai Studio",
                "Unable to continue because no Agent Package was found in the workspace.",
                { showActionPackages: false, showTaskPackages: false, showAgentPackages: true, includeSemaOrg: false }
            );

            if (!selected) {
                vscode.window.showErrorMessage(`Please open an Agent Package and try again`);
                return;
            }
            agentPackagePath = selected.directory;
        }

        const packResult = await packAgentPackage(agentPackagePath);
        if (!packResult) {
            return;
        }

        const sema4aiStudioAPIPath = getSema4AIStudioURLForAgentZipPath(packResult.zipPath);
        const opened = vscode.env.openExternal(vscode.Uri.parse(sema4aiStudioAPIPath));
        if (opened) {
            vscode.window.showInformationMessage(`Publishing to Sema4.ai Studio succeeded`);
        } else {
            vscode.window.showErrorMessage(`Publishing to Sema4.ai Studio failed`);
        }
    });

    C.registerWithoutStub(SEMA4AI_CLEAR_ENV_AND_RESTART, clearEnvAndRestart);
    // Register other commands (which will have an error message shown depending on whether
    // the extension was activated properly).
    registerRobocorpCodeCommands(C, context);

    const outputProvider = new RobotOutputViewProvider(context);
    const options = { webviewOptions: { retainContextWhenHidden: true } };
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(RobotOutputViewProvider.viewType, outputProvider, options)
    );
    await setupDebugSessionOutViewIntegration(context);

    const extension = extensions.getExtension("robocorp.robotframework-lsp");
    if (extension) {
        // If the Robot Framework Language server is present, make sure it is compatible with this
        // version.
        try {
            const version: string = extension.packageJSON.version;
            const splitted = version.split(".");
            const major = parseInt(splitted[0]);
            const minor = parseInt(splitted[1]);
            const micro = parseInt(splitted[2]);
            if (major < 1 || (major == 1 && (minor < 7 || (minor == 7 && micro < 0)))) {
                const msg =
                    "Unable to initialize the Sema4.ai extension because the Robot Framework Language Server version (" +
                    version +
                    ") is not compatible with this version of Sema4.ai. Robot Framework Language Server 1.7.0 or newer is required. Please update to proceed. ";
                OUTPUT_CHANNEL.appendLine(msg);
                C.useErrorStubs = true;
                notifyOfInitializationErrorShowOutputTab(msg);
                return;
            }
        } catch (err) {
            logError("Error verifying Robot Framework Language Server version.", err, "INIT_RF_TOO_OLD");
        }
    }

    workspace.onDidChangeConfiguration((event) => {
        for (let s of [
            roboConfig.SEMA4AI_LANGUAGE_SERVER_ARGS,
            roboConfig.SEMA4AI_LANGUAGE_SERVER_PYTHON,
            roboConfig.SEMA4AI_LANGUAGE_SERVER_TCP_PORT,
        ]) {
            if (event.affectsConfiguration(s)) {
                window
                    .showWarningMessage(
                        'Please use the "Reload Window" action for changes in ' + s + " to take effect.",
                        ...["Reload Window"]
                    )
                    .then((selection) => {
                        if (selection === "Reload Window") {
                            commands.executeCommand("workbench.action.reloadWindow");
                        }
                    });
                return;
            }
        }
    });

    let startLsTiming = new Timing();
    langServer = new LanguageClient("Sema4.ai", serverOptions, clientOptions);

    context.subscriptions.push(
        langServer.onDidChangeState((event) => {
            if (event.newState == State.Running) {
                // i.e.: We need to register the customProgress as soon as it's running (we can't wait for onReady)
                // because at that point if there are open documents, lots of things may've happened already, in
                // which case the progress won't be shown on some cases where it should be shown.
                context.subscriptions.push(
                    langServer.onNotification("$/customProgress", (args: ProgressReport) => {
                        // OUTPUT_CHANNEL.appendLine(args.id + " - " + args.kind + " - " + args.title + " - " + args.message + " - " + args.increment);
                        let progressReporter = handleProgressMessage(args);
                        if (progressReporter) {
                            if (args.kind == "begin") {
                                const progressId = args.id;
                                progressReporter.token.onCancellationRequested(() => {
                                    langServer.sendNotification("cancelProgress", { progressId: progressId });
                                });
                            }
                        }
                    })
                );
                context.subscriptions.push(
                    langServer.onNotification("$/linkedAccountChanged", () => {
                        refreshCloudTreeView();
                    })
                );
                context.subscriptions.push(
                    langServer.onRequest("$/executeWorkspaceCommand", async (args: ExecuteWorkspaceCommandArgs) => {
                        // OUTPUT_CHANNEL.appendLine(args.command + " - " + args.arguments);
                        let ret;
                        try {
                            ret = await commands.executeCommand(args.command, args.arguments);
                        } catch (err) {
                            if (!(err.message && err.message.endsWith("not found"))) {
                                // Log if the error wasn't that the command wasn't found
                                logError("Error executing workspace command.", err, "EXT_EXECUTE_WS_COMMAND");
                            }
                        }
                        return ret;
                    })
                );
            }
        })
    );
    views.registerViews(context);
    registerDebugger();

    try {
        let disposable: Disposable = langServer.start();
        context.subscriptions.push(disposable);
        // i.e.: if we return before it's ready, the language server commands
        // may not be available.
        OUTPUT_CHANNEL.appendLine("Waiting for Sema4.ai (python) language server to finish activating...");
        await langServer.onReady();
        // If it started properly, mark that it worked.
        GLOBAL_STATE.update(CACHE_KEY_LAST_WORKED, true);
        OUTPUT_CHANNEL.appendLine(
            "Took: " + startLsTiming.getTotalElapsedAsStr() + " to initialize Sema4.ai Language Server."
        );
    } catch (error) {
        logError("Error initializing Robocorp code.", error, "ERROR_INITIALIZING_ROBOCORP_CODE_LANG_SERVER");
    }

    // Note: start the async ones below but don't await on them (the extension should be considered initialized
    // regardless of it -- as it may call robot.resolveInterpreter, it may need to activate the language
    // server extension, which in turn requires robocorp code to be activated already).
    installWorkspaceWatcher(context);
}

export function deactivate(): Thenable<void> | undefined {
    if (!langServer) {
        return undefined;
    }
    return langServer.stop();
}

async function getLanguageServerPython(): Promise<string | undefined> {
    let info = await getLanguageServerPythonInfo();
    if (!info) {
        return undefined;
    }
    return info.pythonExe;
}

// Helper to avoid 2 asyncs starting up the process to get the pyhon info.
let globalGetLanguageServerPythonInfoUncachedPromise: Promise<InterpreterInfo | undefined>;

export async function getLanguageServerPythonInfo(): Promise<InterpreterInfo | undefined> {
    if (globalCachedPythonInfo) {
        return globalCachedPythonInfo;
    }

    if (globalGetLanguageServerPythonInfoUncachedPromise !== undefined) {
        return await globalGetLanguageServerPythonInfoUncachedPromise;
    }

    try {
        globalGetLanguageServerPythonInfoUncachedPromise = getLanguageServerPythonInfoUncached();

        let cachedPythonInfo: InterpreterInfo | undefined;
        cachedPythonInfo = await globalGetLanguageServerPythonInfoUncachedPromise;
        if (!cachedPythonInfo) {
            return undefined; // Unable to get it.
        }
        // Ok, we got it (cache that info).
        globalCachedPythonInfo = cachedPythonInfo;
    } finally {
        globalGetLanguageServerPythonInfoUncachedPromise = undefined;
    }

    return globalCachedPythonInfo;
}

export const collapseAllEntries = async (): Promise<void> => {
    vscode.commands.executeCommand(`workbench.actions.treeView.${TREE_VIEW_SEMA4AI_TASK_PACKAGES_TREE}.collapseAll`);
};
