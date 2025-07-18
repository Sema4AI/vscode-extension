// Warning: Don't edit file (autogenerated from python -m dev codegen).

export const SEMA4AI_GET_LANGUAGE_SERVER_PYTHON = "sema4ai.getLanguageServerPython";  // Get a python executable suitable to start the language server
export const SEMA4AI_GET_LANGUAGE_SERVER_PYTHON_INFO = "sema4ai.getLanguageServerPythonInfo";  // Get info suitable to start the language server {pythonExe, environ}
export const SEMA4AI_GET_PLUGINS_DIR = "sema4ai.getPluginsDir";  // Get the directory for plugins
export const SEMA4AI_CREATE_ROBOT = "sema4ai.createRobot";  // Create Task Package
export const SEMA4AI_CREATE_ACTION_PACKAGE = "sema4ai.createActionPackage";  // Create Action Package
export const SEMA4AI_CREATE_TASK_OR_ACTION_OR_AGENT_PACKAGE = "sema4ai.createTaskOrActionOrAgentPackage";  // Create Agent, Action or Task Package
export const SEMA4AI_LIST_ROBOT_TEMPLATES_INTERNAL = "sema4ai.listRobotTemplates.internal";  // Provides a list with the available Task Package templates
export const SEMA4AI_CREATE_ROBOT_INTERNAL = "sema4ai.createRobot.internal";  // Actually calls rcc to create the Task Package
export const SEMA4AI_UPLOAD_ROBOT_TO_CLOUD = "sema4ai.uploadRobotToCloud";  // Upload Task Package to Control Room
export const SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL = "sema4ai.localListRobots.internal";  // Lists the activities currently available in the workspace
export const SEMA4AI_IS_LOGIN_NEEDED_INTERNAL = "sema4ai.isLoginNeeded.internal";  // Checks if the user is already linked to an account
export const SEMA4AI_GET_LINKED_ACCOUNT_INFO_INTERNAL = "sema4ai.getLinkedAccountInfo.internal";  // Provides information related to the current linked account
export const SEMA4AI_CLOUD_LOGIN = "sema4ai.cloudLogin";  // Link to Control Room
export const SEMA4AI_CLOUD_LOGIN_INTERNAL = "sema4ai.cloudLogin.internal";  // Link to Control Room (receives credentials)
export const SEMA4AI_CLOUD_LIST_WORKSPACES_INTERNAL = "sema4ai.cloudListWorkspaces.internal";  // Lists the workspaces available for the user (in the Control Room)
export const SEMA4AI_UPLOAD_TO_NEW_ROBOT_INTERNAL = "sema4ai.uploadToNewRobot.internal";  // Uploads a Task Package as a new Task Package in the Control Room
export const SEMA4AI_UPLOAD_TO_EXISTING_ROBOT_INTERNAL = "sema4ai.uploadToExistingRobot.internal";  // Uploads a Task Package as an existing Task Package in the Control Room
export const SEMA4AI_RUN_IN_RCC_INTERNAL = "sema4ai.runInRcc.internal";  // Runs a custom command in RCC
export const SEMA4AI_RUN_ROBOT_RCC = "sema4ai.runRobotRcc";  // Run Task Package
export const SEMA4AI_RUN_ACTION_FROM_ACTION_PACKAGE = "sema4ai.runActionFromActionPackage";  // Run Action (from Action Package)
export const SEMA4AI_DEBUG_ROBOT_RCC = "sema4ai.debugRobotRcc";  // Debug Task Package
export const SEMA4AI_DEBUG_ACTION_FROM_ACTION_PACKAGE = "sema4ai.debugActionFromActionPackage";  // Debug Action (from Action Package)
export const SEMA4AI_ROBOTS_VIEW_TASK_RUN = "sema4ai.robotsViewTaskRun";  // Launch Task
export const SEMA4AI_ROBOTS_VIEW_TASK_DEBUG = "sema4ai.robotsViewTaskDebug";  // Debug Task
export const SEMA4AI_ROBOTS_VIEW_ACTION_RUN = "sema4ai.robotsViewActionRun";  // Launch Action
export const SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG = "sema4ai.robotsViewActionDebug";  // Debug Action
export const SEMA4AI_ROBOTS_VIEW_ACTION_EDIT_INPUT = "sema4ai.robotsViewActionEditInput";  // Configure Action Input
export const SEMA4AI_CONFIGURE_ACTION_INPUT = "sema4ai.configureActionInput";  // Configure Action Input
export const SEMA4AI_ROBOTS_VIEW_ACTION_OPEN = "sema4ai.robotsViewActionOpen";  // Open Action
export const SEMA4AI_RUN_ROBOCORPS_PYTHON_TASK = "sema4ai.runRobocorpsPythonTask";  // Run Sema4.ai's Python Task
export const SEMA4AI_DEBUG_ROBOCORPS_PYTHON_TASK = "sema4ai.debugRobocorpsPythonTask";  // Debug Sema4.ai's Python Task
export const SEMA4AI_SAVE_IN_DISK_LRU = "sema4ai.saveInDiskLRU";  // Saves some data in an LRU in the disk
export const SEMA4AI_LOAD_FROM_DISK_LRU = "sema4ai.loadFromDiskLRU";  // Loads some LRU data from the disk
export const SEMA4AI_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH = "sema4ai.computeRobotLaunchFromRobocorpCodeLaunch";  // Computes a Task Package launch debug configuration based on the Sema4.ai launch debug configuration
export const SEMA4AI_SET_PYTHON_INTERPRETER = "sema4ai.setPythonInterpreter";  // Set python executable based on robot.yaml
export const SEMA4AI_RESOLVE_INTERPRETER = "sema4ai.resolveInterpreter";  // Resolves the interpreter to be used given a path
export const SEMA4AI_CLOUD_LOGOUT = "sema4ai.cloudLogout";  // Unlink and remove credentials from Control Room
export const SEMA4AI_CLOUD_LOGOUT_INTERNAL = "sema4ai.cloudLogout.internal";  // Unlink and remove credentials from Control Room internal
export const SEMA4AI_REFRESH_ROBOTS_VIEW = "sema4ai.refreshRobotsView";  // Refresh Packages view
export const SEMA4AI_REFRESH_ROBOT_CONTENT_VIEW = "sema4ai.refreshRobotContentView";  // Refresh Task Package Content view
export const SEMA4AI_NEW_FILE_IN_ROBOT_CONTENT_VIEW = "sema4ai.newFileInRobotContentView";  // New File
export const SEMA4AI_NEW_FOLDER_IN_ROBOT_CONTENT_VIEW = "sema4ai.newFolderInRobotContentView";  // New Folder
export const SEMA4AI_DELETE_RESOURCE_IN_ROBOT_CONTENT_VIEW = "sema4ai.deleteResourceInRobotContentView";  // Delete
export const SEMA4AI_RENAME_RESOURCE_IN_ROBOT_CONTENT_VIEW = "sema4ai.renameResourceInRobotContentView";  // Rename
export const SEMA4AI_REFRESH_CLOUD_VIEW = "sema4ai.refreshCloudView";  // Refresh Sema4.ai view
export const SEMA4AI_GET_LOCATORS_JSON_INFO = "sema4ai.getLocatorsJsonInfo";  // Obtain information from the locators.json given a robot.yaml
export const SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL = "sema4ai.removeLocatorFromJson.internal";  // Remove a named locator from locators.json
export const SEMA4AI_REMOVE_LOCATOR_FROM_JSON = "sema4ai.removeLocatorFromJson";  // Remove Locator
export const SEMA4AI_OPEN_LOCATORS_JSON = "sema4ai.openLocatorsJson";  // Open locators.json
export const SEMA4AI_OPEN_CLOUD_HOME = "sema4ai.openCloudHome";  // Open cloud home
export const SEMA4AI_NEW_ROBOCORP_INSPECTOR_BROWSER = "sema4ai.newRobocorpInspectorBrowser";  // Add Web Locator
export const SEMA4AI_NEW_ROBOCORP_INSPECTOR_WINDOWS = "sema4ai.newRobocorpInspectorWindows";  // Add Windows Locator
export const SEMA4AI_NEW_ROBOCORP_INSPECTOR_IMAGE = "sema4ai.newRobocorpInspectorImage";  // Add Image Locator
export const SEMA4AI_NEW_ROBOCORP_INSPECTOR_JAVA = "sema4ai.newRobocorpInspectorJava";  // Add Java Locator
export const SEMA4AI_OPEN_PLAYWRIGHT_RECORDER = "sema4ai.openPlaywrightRecorder";  // Open Playwright Recorder
export const SEMA4AI_OPEN_PLAYWRIGHT_RECORDER_INTERNAL = "sema4ai.openPlaywrightRecorder.internal";  // Open Playwright Recorder Internal
export const SEMA4AI_EDIT_ROBOCORP_INSPECTOR_LOCATOR = "sema4ai.editRobocorpInspectorLocator";  // Edit locator
export const SEMA4AI_COPY_LOCATOR_TO_CLIPBOARD_INTERNAL = "sema4ai.copyLocatorToClipboard.internal";  // Copy locator name to clipboard
export const SEMA4AI_OPEN_ROBOT_TREE_SELECTION = "sema4ai.openRobotTreeSelection";  // Configure Task Package (robot.yaml)
export const SEMA4AI_OPEN_ROBOT_CONDA_TREE_SELECTION = "sema4ai.openRobotCondaTreeSelection";  // Configure Dependencies (conda.yaml)
export const SEMA4AI_OPEN_PACKAGE_YAML_TREE_SELECTION = "sema4ai.openPackageYamlTreeSelection";  // Configure Action Package
export const SEMA4AI_OPEN_EXTERNALLY = "sema4ai.openExternally";  // Open externally
export const SEMA4AI_OPEN_IN_VS_CODE = "sema4ai.openInVSCode";  // Open in VSCode
export const SEMA4AI_REVEAL_IN_EXPLORER = "sema4ai.revealInExplorer";  // Reveal in File Explorer
export const SEMA4AI_REVEAL_ROBOT_IN_EXPLORER = "sema4ai.revealRobotInExplorer";  // Reveal robot.yaml in File Explorer
export const SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION = "sema4ai.cloudUploadRobotTreeSelection";  // Upload Task Package to Control Room
export const SEMA4AI_RCC_TERMINAL_CREATE_ROBOT_TREE_SELECTION = "sema4ai.rccTerminalCreateRobotTreeSelection";  // Open terminal with Package Python environment
export const SEMA4AI_SEND_METRIC = "sema4ai.sendMetric";  // Send metric
export const SEMA4AI_SUBMIT_ISSUE_INTERNAL = "sema4ai.submitIssue.internal";  // Submit issue (internal)
export const SEMA4AI_SUBMIT_ISSUE = "sema4ai.submitIssue";  // Submit issue to Sema4.ai
export const SEMA4AI_INSPECTOR_INTERNAL = "sema4ai.inspector.internal";  // Inspector Manager (internal)
export const SEMA4AI_INSPECTOR = "sema4ai.inspector";  // Open Inspector
export const SEMA4AI_INSPECTOR_DUPLICATE = "sema4ai.inspector.duplicate";  // Create & manage locators
export const SEMA4AI_ERROR_FEEDBACK_INTERNAL = "sema4ai.errorFeedback.internal";  // Error feedback (internal)
export const SEMA4AI_FEEDBACK_INTERNAL = "sema4ai.feedback.internal";  // Feedback (internal)
export const SEMA4AI_CONFIGURATION_DIAGNOSTICS_INTERNAL = "sema4ai.configuration.diagnostics.internal";  // Task Package Configuration Diagnostics (internal)
export const SEMA4AI_CONFIGURATION_DIAGNOSTICS = "sema4ai.configuration.diagnostics";  // Task Package Configuration Diagnostics
export const SEMA4AI_RCC_TERMINAL_NEW = "sema4ai.rccTerminalNew";  // Terminal with Task Package environment
export const SEMA4AI_LIST_WORK_ITEMS_INTERNAL = "sema4ai.listWorkItems.internal";  // Lists the work items available for a Task Package
export const SEMA4AI_UPDATE_LAUNCH_ENV = "sema4ai.updateLaunchEnv";  // Updates the environment variables used for some launch (given a Task Package
export const SEMA4AI_UPDATE_LAUNCH_ENV_GET_VAULT_ENV_INTERNAL = "sema4ai.updateLaunchEnv.getVaultEnv.internal";  // Provides the environment variables related to the vault.
export const SEMA4AI_NEW_WORK_ITEM_IN_WORK_ITEMS_VIEW = "sema4ai.newWorkItemInWorkItemsView";  // New Work Item
export const SEMA4AI_DELETE_WORK_ITEM_IN_WORK_ITEMS_VIEW = "sema4ai.deleteWorkItemInWorkItemsView";  // Delete Work Item
export const SEMA4AI_HELP_WORK_ITEMS = "sema4ai.helpWorkItems";  // Work Items Help
export const SEMA4AI_CONVERT_OUTPUT_WORK_ITEM_TO_INPUT = "sema4ai.convertOutputWorkItemToInput";  // Convert output work item to input
export const SEMA4AI_VERIFY_LIBRARY_VERSION_INTERNAL = "sema4ai.verifyLibraryVersion.internal";  // Collect a library version and verify if it matches some expected version
export const SEMA4AI_CONNECT_WORKSPACE = "sema4ai.connectWorkspace";  // Connect to Control Room Workspace (vault, storage, ...)
export const SEMA4AI_DISCONNECT_WORKSPACE = "sema4ai.disconnectWorkspace";  // Disconnect from Control Room Workspace
export const SEMA4AI_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "sema4ai.getConnectedVaultWorkspace.internal";  // Gets workspace id currently connected
export const SEMA4AI_SET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "sema4ai.setConnectedVaultWorkspace.internal";  // Sets the currently connected Control Room Workspace
export const SEMA4AI_OPEN_VAULT_HELP = "sema4ai.openVaultHelp";  // Open vault help
export const SEMA4AI_CLEAR_ENV_AND_RESTART = "sema4ai.clearEnvAndRestart";  // Clear Sema4.ai (RCC) environments and restart Sema4.ai
export const SEMA4AI_SHOW_OUTPUT = "sema4ai.showOutput";  // Show Sema4.ai > Output logs
export const SEMA4AI_SHOW_INTERPRETER_ENV_ERROR = "sema4ai.showInterpreterEnvError";  // Show error related to interpreter env creation
export const SEMA4AI_OPEN_FLOW_EXPLORER_TREE_SELECTION = "sema4ai.openFlowExplorerTreeSelection";  // Open Flow Explorer
export const SEMA4AI_PROFILE_IMPORT = "sema4ai.profileImport";  // Import Profile
export const SEMA4AI_PROFILE_IMPORT_INTERNAL = "sema4ai.profileImport.internal";  // Import Profile (internal)
export const SEMA4AI_PROFILE_SWITCH = "sema4ai.profileSwitch";  // Switch Profile
export const SEMA4AI_PROFILE_SWITCH_INTERNAL = "sema4ai.profileSwitch.internal";  // Switch Profile
export const SEMA4AI_PROFILE_LIST_INTERNAL = "sema4ai.profileList.internal";  // List Profiles
export const SEMA4AI_HAS_PRE_RUN_SCRIPTS_INTERNAL = "sema4ai.hasPreRunScripts.internal";  // Has Pre Run Scripts
export const SEMA4AI_RUN_PRE_RUN_SCRIPTS_INTERNAL = "sema4ai.runPreRunScripts.internal";  // Run Pre Run Scripts
export const SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL = "sema4ai.getPyPiBaseUrls.internal";  // Get PyPi base urls
export const SEMA4AI_START_ACTION_SERVER = "sema4ai.startActionServer";  // Start Action Server
export const SEMA4AI_DOWNLOAD_ACTION_SERVER = "sema4ai.downloadActionServer";  // Download Action Server
export const SEMA4AI_START_ACTION_SERVER_INTERNAL = "sema4ai.startActionServer.internal";  // Start Action Server (internal)
export const SEMA4AI_LIST_ACTIONS_INTERNAL = "sema4ai.listActions.internal";  // Lists the actions available in an action package given a root dir (internal)
export const SEMA4AI_PACKAGE_ENVIRONMENT_REBUILD = "sema4ai.packageEnvironmentRebuild";  // Rebuild Package Environment
export const SEMA4AI_ACTION_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP = "sema4ai.actionPackagePublishToSema4AIStudioApp";  // Publish Action Package to Sema4.ai Studio
export const SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL = "sema4ai.listActionTemplates.internal";  // Provides a list with the available Action templates
export const SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL = "sema4ai.createActionPackage.internal";  // Actually calls Action Server to create the Action Package
export const SEMA4AI_ACTION_SERVER_CLOUD_LOGIN = "sema4ai.actionServerCloudLogin";  // Authenticate the Action Server to Control Room
export const SEMA4AI_ACTION_SERVER_CLOUD_LOGIN_INTERNAL = "sema4ai.actionServerCloudLogin.internal";  // Authenticate the Action Server to Control Room (internal)
export const SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL = "sema4ai.actionServerCloudVerifyLogin.internal";  // Verify that the action server Control Room credentials are saved (internal)
export const SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL = "sema4ai.actionServerCloudListOrganizations.internal";  // List Action Server authenticated organizations (internal)
export const SEMA4AI_ACTION_SERVER_PACKAGE_BUILD = "sema4ai.actionServerPackageBuild";  // Build Action Package (zip)
export const SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL = "sema4ai.actionServerPackageBuild.internal";  // Build Action Package (internal)
export const SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL = "sema4ai.actionServerPackageUpload.internal";  // Upload action package to the Control Room (internal)
export const SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL = "sema4ai.actionServerPackageStatus.internal";  // Get action package upload status from the Control Room (internal)
export const SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL = "sema4ai.actionServerPackageSetChangelog.internal";  // Set action package changelog entry in the Control Room (internal)
export const SEMA4AI_ACTION_SERVER_PACKAGE_PUBLISH = "sema4ai.actionServerPackagePublish";  // Publish Action Package to Control Room
export const SEMA4AI_ACTION_SERVER_PACKAGE_METADATA = "sema4ai.actionServerPackageMetadata";  // Preview the Package OpenAPI Spec (metadata.json)
export const SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL = "sema4ai.actionServerPackageMetadata.internal";  // Preview the Package OpenAPI Spec (metadata.json) (internal)
export const SEMA4AI_OAUTH2_LOGOUT = "sema4ai.oauth2.logout";  // OAuth2 logout
export const SEMA4AI_OAUTH2_OPEN_SETTINGS = "sema4ai.oauth2.open_settings";  // Open Oauth2 Settings
export const SEMA4AI_RCC_DOWNLOAD_INTERNAL = "sema4ai.rccDownload.internal";  // Downloads the RCC (internal)
export const SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL = "sema4ai.actionServerDownload.internal";  // Downloads the Action Server (internal)
export const SEMA4AI_AGENT_CLI_DOWNLOAD_INTERNAL = "sema4ai.agentCliDownload.internal";  // Downloads the Agent CLI (internal)
export const SEMA4AI_ACTION_SERVER_VERSION_INTERNAL = "sema4ai.actionServerVersion.internal";  // Get the Action Server's version (internal)
export const SEMA4AI_AGENT_CLI_VERSION_INTERNAL = "sema4ai.agentCliVersion.internal";  // Get the Agent CLI's version (internal)
export const SEMA4AI_CREATE_AGENT_PACKAGE = "sema4ai.createAgentPackage";  // Create Agent Package
export const SEMA4AI_CREATE_AGENT_PACKAGE_INTERNAL = "sema4ai.createAgentPackage.internal";  // Calls Agent Server to create new Agent Package
export const SEMA4AI_PACK_AGENT_PACKAGE = "sema4ai.packAgentPackage";  // Export Agent Package (Zip)
export const SEMA4AI_PACK_AGENT_PACKAGE_INTERNAL = "sema4ai.packAgentPackage.internal";  // Export Agent Package (internal)
export const SEMA4AI_OPEN_RUNBOOK_TREE_SELECTION = "sema4ai.openRunbookTreeSelection";  // Edit Runbook
export const SEMA4AI_GET_RUNBOOK_PATH_FROM_AGENT_SPEC_INTERNAL = "sema4ai.getRunbookPathFromAgentSpec.internal";  // Get Runbook Path from Agent Spec (internal)
export const SEMA4AI_AGENT_PACKAGE_PUBLISH_TO_SEMA4_AI_STUDIO_APP = "sema4ai.agentPackagePublishToSema4AIStudioApp";  // Publish Agent Package to Sema4.ai Studio
export const SEMA4AI_AGENT_PACKAGE_IMPORT = "sema4ai.agentPackageImport";  // Import Agent Package (Zip)
export const SEMA4AI_REFRESH_AGENT_SPEC = "sema4ai.refreshAgentSpec";  // Refresh Agent Configuration
export const SEMA4AI_REFRESH_AGENT_SPEC_INTERNAL = "sema4ai.refreshAgentSpec.internal";  // Refresh Agent Spec (internal)
export const SEMA4AI_UPDATE_AGENT_VERSION = "sema4ai.updateAgentVersion";  // Update Agent Version
export const SEMA4AI_UPDATE_AGENT_VERSION_INTERNAL = "sema4ai.updateAgentVersion.internal";  // Update Agent Version (internal)
export const SEMA4AI_COLLAPSE_ALL_ENTRIES = "sema4ai.collapseAllEntries";  // Collapse All Entries
export const SEMA4AI_IMPORT_ACTION_PACKAGE = "sema4ai.importActionPackage";  // Import Action Package
export const SEMA4AI_RUN_ACTION_PACKAGE_DEV_TASK = "sema4ai.runActionPackageDevTask";  // Run dev-task (from Action Package)
export const SEMA4AI_GET_ACTIONS_METADATA = "sema4ai.getActionsMetadata";  // Get Actions Metadata
export const SEMA4AI_DROP_DATA_SOURCE = "sema4ai.dropDataSource";  // Remove Data Source
export const SEMA4AI_SETUP_DATA_SOURCE = "sema4ai.setupDataSource";  // Setup Data Source
export const SEMA4AI_OPEN_DATA_SOURCE_DEFINITION = "sema4ai.openDataSourceDefinition";  // Open Data Source definition
export const SEMA4AI_DROP_ALL_DATA_SOURCES = "sema4ai.dropAllDataSources";  // Remove All Data Sources
export const SEMA4AI_SETUP_ALL_DATA_SOURCES = "sema4ai.setupAllDataSources";  // Setup All Data Sources
export const SEMA4AI_FIX_WRONG_AGENT_IMPORT = "sema4ai.fixWrongAgentImport";  // Fix wrong agent import
export const SEMA4AI_ADD_MCP_SERVER = "sema4ai.addMCPServer";  // Add MCP Server