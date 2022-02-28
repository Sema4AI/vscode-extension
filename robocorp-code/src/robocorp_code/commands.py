# fmt: off
# Warning: Don't edit file (autogenerated from python -m dev codegen).

ROBOCORP_GET_LANGUAGE_SERVER_PYTHON = "robocorp.getLanguageServerPython"  # Get a python executable suitable to start the language server
ROBOCORP_GET_LANGUAGE_SERVER_PYTHON_INFO = "robocorp.getLanguageServerPythonInfo"  # Get info suitable to start the language server {pythonExe, environ}
ROBOCORP_GET_PLUGINS_DIR = "robocorp.getPluginsDir"  # Get the directory for plugins
ROBOCORP_CREATE_ROBOT = "robocorp.createRobot"  # Create Robot
ROBOCORP_LIST_ROBOT_TEMPLATES_INTERNAL = "robocorp.listRobotTemplates.internal"  # Provides a list with the available robot templates
ROBOCORP_CREATE_ROBOT_INTERNAL = "robocorp.createRobot.internal"  # Actually calls rcc to create the robot
ROBOCORP_UPLOAD_ROBOT_TO_CLOUD = "robocorp.uploadRobotToCloud"  # Upload Robot to the Control Room
ROBOCORP_LOCAL_LIST_ROBOTS_INTERNAL = "robocorp.localListRobots.internal"  # Lists the activities currently available in the workspace
ROBOCORP_IS_LOGIN_NEEDED_INTERNAL = "robocorp.isLoginNeeded.internal"  # Checks if the user is already linked to an account
ROBOCORP_GET_LINKED_ACCOUNT_INFO_INTERNAL = "robocorp.getLinkedAccountInfo.internal"  # Provides information related to the current linked account
ROBOCORP_CLOUD_LOGIN = "robocorp.cloudLogin"  # Link to Control Room
ROBOCORP_CLOUD_LOGIN_INTERNAL = "robocorp.cloudLogin.internal"  # Link to Control Room (receives credentials)
ROBOCORP_CLOUD_LIST_WORKSPACES_INTERNAL = "robocorp.cloudListWorkspaces.internal"  # Lists the workspaces available for the user (in the Control Room)
ROBOCORP_UPLOAD_TO_NEW_ROBOT_INTERNAL = "robocorp.uploadToNewRobot.internal"  # Uploads a Robot as a new Robot in the Control Room
ROBOCORP_UPLOAD_TO_EXISTING_ROBOT_INTERNAL = "robocorp.uploadToExistingRobot.internal"  # Uploads a Robot as an existing Robot in the Control Room
ROBOCORP_RUN_IN_RCC_INTERNAL = "robocorp.runInRcc.internal"  # Runs a custom command in RCC
ROBOCORP_RUN_ROBOT_RCC = "robocorp.runRobotRcc"  # Run Robot
ROBOCORP_DEBUG_ROBOT_RCC = "robocorp.debugRobotRcc"  # Debug Robot
ROBOCORP_ROBOTS_VIEW_TASK_RUN = "robocorp.robotsViewTaskRun"  # Launch Task
ROBOCORP_ROBOTS_VIEW_TASK_DEBUG = "robocorp.robotsViewTaskDebug"  # Debug Task
ROBOCORP_SAVE_IN_DISK_LRU = "robocorp.saveInDiskLRU"  # Saves some data in an LRU in the disk
ROBOCORP_LOAD_FROM_DISK_LRU = "robocorp.loadFromDiskLRU"  # Loads some LRU data from the disk
ROBOCORP_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH = "robocorp.computeRobotLaunchFromRobocorpCodeLaunch"  # Computes a robot launch debug configuration based on the robocorp code launch debug configuration
ROBOCORP_SET_PYTHON_INTERPRETER = "robocorp.setPythonInterpreter"  # Set pythonPath based on robot.yaml
ROBOCORP_RESOLVE_INTERPRETER = "robocorp.resolveInterpreter"  # Resolves the interpreter to be used given a path
ROBOCORP_CLOUD_LOGOUT = "robocorp.cloudLogout"  # Unlink and remove credentials from Control Room
ROBOCORP_CLOUD_LOGOUT_INTERNAL = "robocorp.cloudLogout.internal"  # Unlink and remove credentials from Control Room internal
ROBOCORP_REFRESH_ROBOTS_VIEW = "robocorp.refreshRobotsView"  # Refresh Robots view
ROBOCORP_REFRESH_ROBOT_CONTENT_VIEW = "robocorp.refreshRobotContentView"  # Refresh Robot Content view
ROBOCORP_NEW_FILE_IN_ROBOT_CONTENT_VIEW = "robocorp.newFileInRobotContentView"  # New File
ROBOCORP_NEW_FOLDER_IN_ROBOT_CONTENT_VIEW = "robocorp.newFolderInRobotContentView"  # New Folder
ROBOCORP_DELETE_RESOURCE_IN_ROBOT_CONTENT_VIEW = "robocorp.deleteResourceInRobotContentView"  # Delete
ROBOCORP_RENAME_RESOURCE_IN_ROBOT_CONTENT_VIEW = "robocorp.renameResourceInRobotContentView"  # Rename
ROBOCORP_REFRESH_CLOUD_VIEW = "robocorp.refreshCloudView"  # Refresh Robocorp view
ROBOCORP_GET_LOCATORS_JSON_INFO = "robocorp.getLocatorsJsonInfo"  # Obtain information from the locators.json given a robot.yaml
ROBOCORP_REMOVE_LOCATOR_FROM_JSON_INTERNAL = "robocorp.removeLocatorFromJson.internal"  # Remove a named locator from locators.json
ROBOCORP_REMOVE_LOCATOR_FROM_JSON = "robocorp.removeLocatorFromJson"  # Remove Locator
ROBOCORP_OPEN_CLOUD_HOME = "robocorp.openCloudHome"  # Open cloud home
ROBOCORP_NEW_ROBOCORP_INSPECTOR_BROWSER = "robocorp.newRobocorpInspectorBrowser"  # Add Browser Locator
ROBOCORP_NEW_ROBOCORP_INSPECTOR_IMAGE = "robocorp.newRobocorpInspectorImage"  # Add Image Locator
ROBOCORP_EDIT_ROBOCORP_INSPECTOR_LOCATOR = "robocorp.editRobocorpInspectorLocator"  # Edit locator
ROBOCORP_COPY_LOCATOR_TO_CLIPBOARD_INTERNAL = "robocorp.copyLocatorToClipboard.internal"  # Copy locator name to clipboard
ROBOCORP_OPEN_ROBOT_TREE_SELECTION = "robocorp.openRobotTreeSelection"  # Open robot.yaml
ROBOCORP_OPEN_EXTERNALLY = "robocorp.openExternally"  # Open externally
ROBOCORP_OPEN_IN_VS_CODE = "robocorp.openInVSCode"  # Open in VSCode
ROBOCORP_REVEAL_IN_EXPLORER = "robocorp.revealInExplorer"  # Reveal in File Explorer
ROBOCORP_REVEAL_ROBOT_IN_EXPLORER = "robocorp.revealRobotInExplorer"  # Reveal robot.yaml in File Explorer
ROBOCORP_CLOUD_UPLOAD_ROBOT_TREE_SELECTION = "robocorp.cloudUploadRobotTreeSelection"  # Upload Robot to Control Room
ROBOCORP_CREATE_RCC_TERMINAL_TREE_SELECTION = "robocorp.rccTerminalCreateRobotTreeSelection"  # Open terminal with Robot environment
ROBOCORP_SEND_METRIC = "robocorp.sendMetric"  # Send metric
ROBOCORP_SUBMIT_ISSUE_INTERNAL = "robocorp.submitIssue.internal"  # Submit issue (internal)
ROBOCORP_SUBMIT_ISSUE = "robocorp.submitIssue"  # Submit issue to Robocorp
ROBOCORP_ERROR_FEEDBACK_INTERNAL = "robocorp.errorFeedback.internal"  # Error feedback (internal)
ROBOCORP_CONFIGURATION_DIAGNOSTICS_INTERNAL = "robocorp.configuration.diagnostics.internal"  # Robot Configuration Diagnostics (internal)
ROBOCORP_CONFIGURATION_DIAGNOSTICS = "robocorp.configuration.diagnostics"  # Robot Configuration Diagnostics
ROBOCORP_RCC_TERMINAL_NEW = "robocorp.rccTerminalNew"  # Terminal with Robot environment
ROBOCORP_LIST_WORK_ITEMS_INTERNAL = "robocorp.listWorkItems.internal"  # Lists the work items available for a Robot
ROBOCORP_UPDATE_LAUNCH_ENV = "robocorp.updateLaunchEnv"  # Updates the environment variables used for some launch (given a Robot)
ROBOCORP_UPDATE_LAUNCH_ENV_GET_VAULT_ENV_INTERNAL = "robocorp.updateLaunchEnv.getVaultEnv.internal"  # Provides the environment variables related to the vault.
ROBOCORP_NEW_WORK_ITEM_IN_WORK_ITEMS_VIEW = "robocorp.newWorkItemInWorkItemsView"  # New Work Item
ROBOCORP_DELETE_WORK_ITEM_IN_WORK_ITEMS_VIEW = "robocorp.deleteWorkItemInWorkItemsView"  # Delete Work Item
ROBOCORP_HELP_WORK_ITEMS = "robocorp.helpWorkItems"  # Work Items Help
ROBOCORP_CONVERT_OUTPUT_WORK_ITEM_TO_INPUT = "robocorp.convertOutputWorkItemToInput"  # Convert output work item to input
ROBOCORP_VERIFY_LIBRARY_VERSION_INTERNAL = "robocorp.verifyLibraryVersion.internal"  # Collect a library version and verify if it matches some expected version
ROBOCORP_CONNECT_VAULT = "robocorp.connectVault"  # Connect to online secrets vault
ROBOCORP_DISCONNECT_VAULT = "robocorp.disconnectVault"  # Disconnect from online secrets vault
ROBOCORP_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "robocorp.getConnectedVaultWorkspace.internal"  # Gets workspace id of the currently connected vault
ROBOCORP_SET_CONNECTED_VAULT_WORKSPACE_INTERNAL = "robocorp.setConnectedVaultWorkspace.internal"  # Sets the currently connected vault workspace
ROBOCORP_OPEN_VAULT_HELP = "robocorp.openVaultHelp"  # Open vault help
ROBOCORP_CLEAR_ENV_AND_RESTART = "robocorp.clearEnvAndRestart"  # Clear Robocorp (RCC) environments and restart Robocorp Code

ALL_SERVER_COMMANDS = [
    ROBOCORP_GET_PLUGINS_DIR,
    ROBOCORP_LIST_ROBOT_TEMPLATES_INTERNAL,
    ROBOCORP_CREATE_ROBOT_INTERNAL,
    ROBOCORP_LOCAL_LIST_ROBOTS_INTERNAL,
    ROBOCORP_IS_LOGIN_NEEDED_INTERNAL,
    ROBOCORP_GET_LINKED_ACCOUNT_INFO_INTERNAL,
    ROBOCORP_CLOUD_LOGIN_INTERNAL,
    ROBOCORP_CLOUD_LIST_WORKSPACES_INTERNAL,
    ROBOCORP_UPLOAD_TO_NEW_ROBOT_INTERNAL,
    ROBOCORP_UPLOAD_TO_EXISTING_ROBOT_INTERNAL,
    ROBOCORP_RUN_IN_RCC_INTERNAL,
    ROBOCORP_SAVE_IN_DISK_LRU,
    ROBOCORP_LOAD_FROM_DISK_LRU,
    ROBOCORP_COMPUTE_ROBOT_LAUNCH_FROM_ROBOCORP_CODE_LAUNCH,
    ROBOCORP_RESOLVE_INTERPRETER,
    ROBOCORP_CLOUD_LOGOUT_INTERNAL,
    ROBOCORP_GET_LOCATORS_JSON_INFO,
    ROBOCORP_REMOVE_LOCATOR_FROM_JSON_INTERNAL,
    ROBOCORP_SEND_METRIC,
    ROBOCORP_CONFIGURATION_DIAGNOSTICS_INTERNAL,
    ROBOCORP_LIST_WORK_ITEMS_INTERNAL,
    ROBOCORP_UPDATE_LAUNCH_ENV_GET_VAULT_ENV_INTERNAL,
    ROBOCORP_VERIFY_LIBRARY_VERSION_INTERNAL,
    ROBOCORP_GET_CONNECTED_VAULT_WORKSPACE_INTERNAL,
    ROBOCORP_SET_CONNECTED_VAULT_WORKSPACE_INTERNAL,
]

# fmt: on
