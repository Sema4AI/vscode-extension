# fmt: off
# Warning: Don't edit file (autogenerated from python -m dev codegen).

SEMA4AI_GET_LANGUAGE_SERVER_PYTHON = "sema4ai.getLanguageServerPython"  # Get a python executable suitable to start the language server
SEMA4AI_GET_LANGUAGE_SERVER_PYTHON_INFO = "sema4ai.getLanguageServerPythonInfo"  # Get info suitable to start the language server {pythonExe, environ}
SEMA4AI_GET_PLUGINS_DIR = "sema4ai.getPluginsDir"  # Get the directory for plugins
SEMA4AI_CREATE_ROBOT = "sema4ai.createRobot"  # Create Task Package
SEMA4AI_CREATE_ACTION_PACKAGE = "sema4ai.createActionPackage"  # Create Action Package
SEMA4AI_CREATE_TASK_OR_ACTION_PACKAGE = "sema4ai.createTaskOrActionPackage"  # Create Action Package
SEMA4AI_LIST_ROBOT_TEMPLATES_INTERNAL = "sema4ai.listRobotTemplates.internal"  # Provides a list with the available Task Package templates
SEMA4AI_CREATE_ROBOT_INTERNAL = "sema4ai.createRobot.internal"  # Actually calls rcc to create the Task Package
SEMA4AI_UPLOAD_ROBOT_TO_CLOUD = "sema4ai.uploadRobotToCloud"  # Upload Task Package to Control Room
SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL = "sema4ai.localListRobots.internal"  # Lists the activities currently available in the workspace
SEMA4AI_IS_LOGIN_NEEDED_INTERNAL = "sema4ai.isLoginNeeded.internal"  # Checks if the user is already linked to an account
SEMA4AI_GET_LINKED_ACCOUNT_INFO_INTERNAL = "sema4ai.getLinkedAccountInfo.internal"  # Provides information related to the current linked account
SEMA4AI_CLOUD_LOGIN = "sema4ai.cloudLogin"  # Link to Control Room
SEMA4AI_CLOUD_LOGIN_INTERNAL = "sema4ai.cloudLogin.internal"  # Link to Control Room (receives credentials)
SEMA4AI_CLOUD_LIST_WORKSPACES_INTERNAL = "sema4ai.cloudListWorkspaces.internal"  # Lists the workspaces available for the user (in the Control Room)
SEMA4AI_UPLOAD_TO_NEW_ROBOT_INTERNAL = "sema4ai.uploadToNewRobot.internal"  # Uploads a Task Package as a new Task Package in the Control Room
SEMA4AI_UPLOAD_TO_EXISTING_ROBOT_INTERNAL = "sema4ai.uploadToExistingRobot.internal"  # Uploads a Task Package as an existing Task Package in the Control Room
SEMA4AI_RUN_IN_RCC_INTERNAL = "sema4ai.runInRcc.internal"  # Runs a custom command in RCC
SEMA4AI_RUN_ROBOT_RCC = "sema4ai.runRobotRcc"  # Run Task Package
SEMA4AI_RUN_ACTION_FROM_ACTION_PACKAGE = "sema4ai.runActionFromActionPackage"  # Run Action (from Action Package)
SEMA4AI_DEBUG_ROBOT_RCC = "sema4ai.debugRobotRcc"  # Debug Task Package
SEMA4AI_DEBUG_ACTION_FROM_ACTION_PACKAGE = "sema4ai.debugActionFromActionPackage"  # Debug Action (from Action Package)
SEMA4AI_ROBOTS_VIEW_TASK_RUN = "sema4ai.robotsViewTaskRun"  # Launch Task
SEMA4AI_ROBOTS_VIEW_TASK_DEBUG = "sema4ai.robotsViewTaskDebug"  # Debug Task
SEMA4AI_ROBOTS_VIEW_ACTION_RUN = "sema4ai.robotsViewActionRun"  # Launch Action
SEMA4AI_ROBOTS_VIEW_ACTION_DEBUG = "sema4ai.robotsViewActionDebug"  # Debug Action
SEMA4AI_ROBOTS_VIEW_ACTION_EDIT_INPUT = "sema4ai.robotsViewActionEditInput"  # Configure Action Input
SEMA4AI_ROBOTS_VIEW_ACTION_OPEN = "sema4ai.robotsViewActionOpen"  # Open Action
SEMA4AI_RUN_ROBOCORPS_PYTHON_TASK = "sema4ai.runRobocorpsPythonTask"  # Run Sema4.ai's Python Task
SEMA4AI_DEBUG_ROBOCORPS_PYTHON_TASK = "sema4ai.debugRobocorpsPythonTask"  # Debug Sema4.ai's Python Task
SEMA4AI_SAVE_IN_DISK_LRU = "sema4ai.saveInDiskLRU"  # Saves some data in an LRU in the disk
SEMA4AI_LOAD_FROM_DISK_LRU = "sema4ai.loadFromDiskLRU"  # Loads some LRU data from the disk
SEMA4AI_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH = "sema4ai.computeRobotLaunchFromRobocorpCodeLaunch"  # Computes a Task Package launch debug configuration based on the Sema4.ai launch debug configuration
SEMA4AI_SET_PYTHON_INTERPRETER = "sema4ai.setPythonInterpreter"  # Set python executable based on robot.yaml
SEMA4AI_RESOLVE_INTERPRETER = "sema4ai.resolveInterpreter"  # Resolves the interpreter to be used given a path
SEMA4AI_CLOUD_LOGOUT = "sema4ai.cloudLogout"  # Unlink and remove credentials from Control Room
SEMA4AI_CLOUD_LOGOUT_INTERNAL = "sema4ai.cloudLogout.internal"  # Unlink and remove credentials from Control Room internal
SEMA4AI_REFRESH_ROBOTS_VIEW = "sema4ai.refreshRobotsView"  # Refresh Task/Action Packages view
SEMA4AI_REFRESH_ROBOT_CONTENT_VIEW = "sema4ai.refreshRobotContentView"  # Refresh Task Package Content view
SEMA4AI_NEW_FILE_IN_ROBOT_CONTENT_VIEW = "sema4ai.newFileInRobotContentView"  # New File
SEMA4AI_NEW_FOLDER_IN_ROBOT_CONTENT_VIEW = "sema4ai.newFolderInRobotContentView"  # New Folder
SEMA4AI_DELETE_RESOURCE_IN_ROBOT_CONTENT_VIEW = "sema4ai.deleteResourceInRobotContentView"  # Delete
SEMA4AI_RENAME_RESOURCE_IN_ROBOT_CONTENT_VIEW = "sema4ai.renameResourceInRobotContentView"  # Rename
SEMA4AI_REFRESH_CLOUD_VIEW = "sema4ai.refreshCloudView"  # Refresh Sema4.ai view
SEMA4AI_GET_LOCATORS_JSON_INFO = "sema4ai.getLocatorsJsonInfo"  # Obtain information from the locators.json given a robot.yaml
SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL = "sema4ai.removeLocatorFromJson.internal"  # Remove a named locator from locators.json
SEMA4AI_REMOVE_LOCATOR_FROM_JSON = "sema4ai.removeLocatorFromJson"  # Remove Locator
SEMA4AI_OPEN_LOCATORS_JSON = "sema4ai.openLocatorsJson"  # Open locators.json
SEMA4AI_OPEN_CLOUD_HOME = "sema4ai.openCloudHome"  # Open cloud home
SEMA4AI_NEW_ROBOCORP_INSPECTOR_BROWSER = "sema4ai.newRobocorpInspectorBrowser"  # Add Web Locator
SEMA4AI_NEW_ROBOCORP_INSPECTOR_WINDOWS = "sema4ai.newRobocorpInspectorWindows"  # Add Windows Locator
SEMA4AI_NEW_ROBOCORP_INSPECTOR_IMAGE = "sema4ai.newRobocorpInspectorImage"  # Add Image Locator
SEMA4AI_NEW_ROBOCORP_INSPECTOR_JAVA = "sema4ai.newRobocorpInspectorJava"  # Add Java Locator
SEMA4AI_OPEN_PLAYWRIGHT_RECORDER = "sema4ai.openPlaywrightRecorder"  # Open Playwright Recorder
SEMA4AI_OPEN_PLAYWRIGHT_RECORDER_INTERNAL = "sema4ai.openPlaywrightRecorder.internal"  # Open Playwright Recorder Internal
SEMA4AI_EDIT_ROBOCORP_INSPECTOR_LOCATOR = "sema4ai.editRobocorpInspectorLocator"  # Edit locator
SEMA4AI_COPY_LOCATOR_TO_CLIPBOARD_INTERNAL = "sema4ai.copyLocatorToClipboard.internal"  # Copy locator name to clipboard
SEMA4AI_OPEN_ROBOT_TREE_SELECTION = "sema4ai.openRobotTreeSelection"  # Configure Task Package (robot.yaml)
SEMA4AI_OPEN_ROBOT_CONDA_TREE_SELECTION = "sema4ai.openRobotCondaTreeSelection"  # Configure Dependencies (conda.yaml)
SEMA4AI_OPEN_PACKAGE_YAML_TREE_SELECTION = "sema4ai.openPackageYamlTreeSelection"  # Configure Action Package (package.yaml)
SEMA4AI_OPEN_EXTERNALLY = "sema4ai.openExternally"  # Open externally
SEMA4AI_OPEN_IN_VS_CODE = "sema4ai.openInVSCode"  # Open in VSCode
SEMA4AI_REVEAL_IN_EXPLORER = "sema4ai.revealInExplorer"  # Reveal in File Explorer
SEMA4AI_REVEAL_ROBOT_IN_EXPLORER = "sema4ai.revealRobotInExplorer"  # Reveal robot.yaml in File Explorer
SEMA4AI_CLOUD_UPLOAD_ROBOT_TREE_SELECTION = "sema4ai.cloudUploadRobotTreeSelection"  # Upload Task Package to Control Room
SEMA4AI_RCC_TERMINAL_CREATE_ROBOT_TREE_SELECTION = "sema4ai.rccTerminalCreateRobotTreeSelection"  # Open terminal with Package Python environment
SEMA4AI_SEND_METRIC = "sema4ai.sendMetric"  # Send metric
SEMA4AI_SUBMIT_ISSUE_INTERNAL = "sema4ai.submitIssue.internal"  # Submit issue (internal)
SEMA4AI_SUBMIT_ISSUE = "sema4ai.submitIssue"  # Submit issue to Sema4.ai
SEMA4AI_INSPECTOR_INTERNAL = "sema4ai.inspector.internal"  # Inspector Manager (internal)
SEMA4AI_INSPECTOR = "sema4ai.inspector"  # Open Inspector
SEMA4AI_INSPECTOR_DUPLICATE = "sema4ai.inspector.duplicate"  # Create & manage locators
SEMA4AI_ERROR_FEEDBACK_INTERNAL = "sema4ai.errorFeedback.internal"  # Error feedback (internal)
SEMA4AI_FEEDBACK_INTERNAL = "sema4ai.feedback.internal"  # Feedback (internal)
SEMA4AI_CONFIGURATION_DIAGNOSTICS_INTERNAL = "sema4ai.configuration.diagnostics.internal"  # Task Package Configuration Diagnostics (internal)
SEMA4AI_CONFIGURATION_DIAGNOSTICS = "sema4ai.configuration.diagnostics"  # Task Package Configuration Diagnostics
SEMA4AI_RCC_TERMINAL_NEW = "sema4ai.rccTerminalNew"  # Terminal with Task Package environment
SEMA4AI_LIST_WORK_ITEMS_INTERNAL = "sema4ai.listWorkItems.internal"  # Lists the work items available for a Task Package
SEMA4AI_UPDATE_LAUNCH_ENV = "sema4ai.updateLaunchEnv"  # Updates the environment variables used for some launch (given a Task Package
SEMA4AI_UPDATE_LAUNCH_ENV_GET_VAULT_ENV_INTERNAL = "sema4ai.updateLaunchEnv.getVaultEnv.internal"  # Provides the environment variables related to the vault.
SEMA4AI_NEW_WORK_ITEM_IN_WORK_ITEMS_VIEW = "sema4ai.newWorkItemInWorkItemsView"  # New Work Item
SEMA4AI_DELETE_WORK_ITEM_IN_WORK_ITEMS_VIEW = "sema4ai.deleteWorkItemInWorkItemsView"  # Delete Work Item
SEMA4AI_HELP_WORK_ITEMS = "sema4ai.helpWorkItems"  # Work Items Help
SEMA4AI_CONVERT_OUTPUT_WORK_ITEM_TO_INPUT = "sema4ai.convertOutputWorkItemToInput"  # Convert output work item to input
SEMA4AI_VERIFY_LIBRARY_VERSION_INTERNAL = "sema4ai.verifyLibraryVersion.internal"  # Collect a library version and verify if it matches some expected version
SEMA4AI_CONNECT_WORKSPACE = "sema4ai.connectWorkspace"  # Connect to Control Room Workspace (vault, storage, ...)
SEMA4AI_DISCONNECT_WORKSPACE = "sema4ai.disconnectWorkspace"  # Disconnect from Control Room Workspace
SEMA4AI_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "sema4ai.getConnectedVaultWorkspace.internal"  # Gets workspace id currently connected
SEMA4AI_SET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "sema4ai.setConnectedVaultWorkspace.internal"  # Sets the currently connected Control Room Workspace
SEMA4AI_OPEN_VAULT_HELP = "sema4ai.openVaultHelp"  # Open vault help
SEMA4AI_CLEAR_ENV_AND_RESTART = "sema4ai.clearEnvAndRestart"  # Clear Sema4.ai (RCC) environments and restart Sema4.ai
SEMA4AI_SHOW_OUTPUT = "sema4ai.showOutput"  # Show Sema4.ai > Output logs
SEMA4AI_SHOW_INTERPRETER_ENV_ERROR = "sema4ai.showInterpreterEnvError"  # Show error related to interpreter env creation
SEMA4AI_OPEN_FLOW_EXPLORER_TREE_SELECTION = "sema4ai.openFlowExplorerTreeSelection"  # Open Flow Explorer
SEMA4AI_PROFILE_IMPORT = "sema4ai.profileImport"  # Import Profile
SEMA4AI_PROFILE_IMPORT_INTERNAL = "sema4ai.profileImport.internal"  # Import Profile (internal)
SEMA4AI_PROFILE_SWITCH = "sema4ai.profileSwitch"  # Switch Profile
SEMA4AI_PROFILE_SWITCH_INTERNAL = "sema4ai.profileSwitch.internal"  # Switch Profile
SEMA4AI_PROFILE_LIST_INTERNAL = "sema4ai.profileList.internal"  # List Profiles
SEMA4AI_HAS_PRE_RUN_SCRIPTS_INTERNAL = "sema4ai.hasPreRunScripts.internal"  # Has Pre Run Scripts
SEMA4AI_RUN_PRE_RUN_SCRIPTS_INTERNAL = "sema4ai.runPreRunScripts.internal"  # Run Pre Run Scripts
SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL = "sema4ai.getPyPiBaseUrls.internal"  # Get PyPi base urls
SEMA4AI_START_ACTION_SERVER = "sema4ai.startActionServer"  # Start Action Server
SEMA4AI_DOWNLOAD_ACTION_SERVER = "sema4ai.downloadActionServer"  # Download Action Server
SEMA4AI_START_ACTION_SERVER_INTERNAL = "sema4ai.startActionServer.internal"  # Start Action Server (internal)
SEMA4AI_LIST_ACTIONS_INTERNAL = "sema4ai.listActions.internal"  # Lists the actions available in an action package given a root dir (internal)
SEMA4AI_PACKAGE_ENVIRONMENT_REBUILD = "sema4ai.packageEnvironmentRebuild"  # Rebuild Package Environment
SEMA4AI_PACKAGE_PUBLISH_TO_DESKTOP_APP = "sema4ai.packagePublishToDesktopApp"  # Publish Package to Sema4.ai Desktop
SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL = "sema4ai.listActionTemplates.internal"  # Provides a list with the available Action templates
SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL = "sema4ai.createActionPackage.internal"  # Actually calls Action Server to create the Action Package
SEMA4AI_ACTION_SERVER_CLOUD_LOGIN = "sema4ai.actionServerCloudLogin"  # Authenticate the Action Server to Control Room
SEMA4AI_ACTION_SERVER_CLOUD_LOGIN_INTERNAL = "sema4ai.actionServerCloudLogin.internal"  # Authenticate the Action Server to Control Room (internal)
SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL = "sema4ai.actionServerCloudVerifyLogin.internal"  # Verify that the action server Control Room credentials are saved (internal)
SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL = "sema4ai.actionServerCloudListOrganizations.internal"  # List Action Server authenticated organizations (internal)
SEMA4AI_ACTION_SERVER_PACKAGE_BUILD = "sema4ai.actionServerPackageBuild"  # Build Action Package to Workspace
SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL = "sema4ai.actionServerPackageBuild.internal"  # Build Action Package (internal)
SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL = "sema4ai.actionServerPackageUpload.internal"  # Upload action package to the Control Room (internal)
SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL = "sema4ai.actionServerPackageStatus.internal"  # Get action package upload status from the Control Room (internal)
SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL = "sema4ai.actionServerPackageSetChangelog.internal"  # Set action package changelog entry in the Control Room (internal)
SEMA4AI_ACTION_SERVER_PACKAGE_PUBLISH = "sema4ai.actionServerPackagePublish"  # Publish Action Package to Control Room
SEMA4AI_ACTION_SERVER_PACKAGE_METADATA = "sema4ai.actionServerPackageMetadata"  # Open the Action Package OpenAPI Spec (metadata.json)
SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL = "sema4ai.actionServerPackageMetadata.internal"  # Open the Action Package OpenAPI Spec (metadata.json) (internal)
SEMA4AI_OAUTH2_LOGOUT = "sema4ai.oauth2.logout"  # OAuth2 logout
SEMA4AI_OAUTH2_OPEN_SETTINGS = "sema4ai.oauth2.open_settings"  # Open Oauth2 Settings
SEMA4AI_RCC_DOWNLOAD_INTERNAL = "sema4ai.rccDownload.internal"  # Downloads the RCC (internal)
SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL = "sema4ai.actionServerDownload.internal"  # Downloads the Action Server (internal)
SEMA4AI_AGENT_SERVER_DOWNLOAD_INTERNAL = "sema4ai.agentServerDownload.internal"  # Downloads the Agent Server (internal)
SEMA4AI_ACTION_SERVER_VERSION_INTERNAL = "sema4ai.actionServerVersion.internal"  # Get the Action Server's version (internal)
SEMA4AI_AGENT_SERVER_VERSION_INTERNAL = "sema4ai.agentServerVersion.internal"  # Get the Agent Server's version (internal)

ALL_SERVER_COMMANDS = [
    SEMA4AI_GET_PLUGINS_DIR,
    SEMA4AI_LIST_ROBOT_TEMPLATES_INTERNAL,
    SEMA4AI_CREATE_ROBOT_INTERNAL,
    SEMA4AI_LOCAL_LIST_ROBOTS_INTERNAL,
    SEMA4AI_IS_LOGIN_NEEDED_INTERNAL,
    SEMA4AI_GET_LINKED_ACCOUNT_INFO_INTERNAL,
    SEMA4AI_CLOUD_LOGIN_INTERNAL,
    SEMA4AI_CLOUD_LIST_WORKSPACES_INTERNAL,
    SEMA4AI_UPLOAD_TO_NEW_ROBOT_INTERNAL,
    SEMA4AI_UPLOAD_TO_EXISTING_ROBOT_INTERNAL,
    SEMA4AI_RUN_IN_RCC_INTERNAL,
    SEMA4AI_SAVE_IN_DISK_LRU,
    SEMA4AI_LOAD_FROM_DISK_LRU,
    SEMA4AI_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH,
    SEMA4AI_RESOLVE_INTERPRETER,
    SEMA4AI_CLOUD_LOGOUT_INTERNAL,
    SEMA4AI_GET_LOCATORS_JSON_INFO,
    SEMA4AI_REMOVE_LOCATOR_FROM_JSON_INTERNAL,
    SEMA4AI_OPEN_PLAYWRIGHT_RECORDER_INTERNAL,
    SEMA4AI_SEND_METRIC,
    SEMA4AI_CONFIGURATION_DIAGNOSTICS_INTERNAL,
    SEMA4AI_LIST_WORK_ITEMS_INTERNAL,
    SEMA4AI_UPDATE_LAUNCH_ENV_GET_VAULT_ENV_INTERNAL,
    SEMA4AI_VERIFY_LIBRARY_VERSION_INTERNAL,
    SEMA4AI_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL,
    SEMA4AI_SET_CONNECTED_VAULT_WORKSPACE_INTERNAL,
    SEMA4AI_PROFILE_IMPORT_INTERNAL,
    SEMA4AI_PROFILE_SWITCH_INTERNAL,
    SEMA4AI_PROFILE_LIST_INTERNAL,
    SEMA4AI_HAS_PRE_RUN_SCRIPTS_INTERNAL,
    SEMA4AI_RUN_PRE_RUN_SCRIPTS_INTERNAL,
    SEMA4AI_GET_PY_PI_BASE_URLS_INTERNAL,
    SEMA4AI_START_ACTION_SERVER_INTERNAL,
    SEMA4AI_LIST_ACTIONS_INTERNAL,
    SEMA4AI_LIST_ACTION_TEMPLATES_INTERNAL,
    SEMA4AI_CREATE_ACTION_PACKAGE_INTERNAL,
    SEMA4AI_ACTION_SERVER_CLOUD_LOGIN_INTERNAL,
    SEMA4AI_ACTION_SERVER_CLOUD_VERIFY_LOGIN_INTERNAL,
    SEMA4AI_ACTION_SERVER_CLOUD_LIST_ORGANIZATIONS_INTERNAL,
    SEMA4AI_ACTION_SERVER_PACKAGE_BUILD_INTERNAL,
    SEMA4AI_ACTION_SERVER_PACKAGE_UPLOAD_INTERNAL,
    SEMA4AI_ACTION_SERVER_PACKAGE_STATUS_INTERNAL,
    SEMA4AI_ACTION_SERVER_PACKAGE_SET_CHANGELOG_INTERNAL,
    SEMA4AI_ACTION_SERVER_PACKAGE_METADATA_INTERNAL,
    SEMA4AI_OAUTH2_OPEN_SETTINGS,
    SEMA4AI_RCC_DOWNLOAD_INTERNAL,
    SEMA4AI_ACTION_SERVER_DOWNLOAD_INTERNAL,
    SEMA4AI_AGENT_SERVER_DOWNLOAD_INTERNAL,
    SEMA4AI_ACTION_SERVER_VERSION_INTERNAL,
    SEMA4AI_AGENT_SERVER_VERSION_INTERNAL,
]

# fmt: on
