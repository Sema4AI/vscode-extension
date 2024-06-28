from convert import convert_case_to_constant


class Command(object):
    def __init__(
        self,
        name,
        title,
        add_to_package_json=True,
        keybinding="",
        server_handled=True,
        icon=None,  # https://microsoft.github.io/vscode-codicons/dist/codicon.html
        enablement=None,
        hide_from_command_palette=False,
        constant="",
        when_clause=None,
    ):
        """
        :param add_to_package_json:
            If a command should not appear to the user, add_to_package_json should be False.
        :param server_handled:
            If True this is a command handled in the server (and not in the client) and
            thus will be registered as such.
        :param constant:
            If given the internal constant used will be this one (used when a command
            is renamed and we want to keep compatibility).
        """
        self.name = name
        self.title = title
        self.add_to_package_json = add_to_package_json
        self.keybinding = keybinding
        self.server_handled = server_handled
        self.icon = icon
        self.enablement = enablement

        if hide_from_command_palette:
            assert (
                not when_clause
            ), "hide_from_command_palette and when_clause may not be both specified."
            when_clause = "false"

        self.when_clause = when_clause

        if not constant:
            constant = convert_case_to_constant(name)
        self.constant = constant


COMMANDS = [
    Command(
        "sema4ai.getLanguageServerPython",
        "Get a python executable suitable to start the language server",
        add_to_package_json=False,
        server_handled=False,
    ),
    Command(
        "sema4ai.getLanguageServerPythonInfo",
        "Get info suitable to start the language server {pythonExe, environ}",
        add_to_package_json=False,
        server_handled=False,
    ),
    Command(
        "sema4ai.getPluginsDir",
        "Get the directory for plugins",
        add_to_package_json=False,
        server_handled=True,
    ),
    # Note: this command is started from the client (due to needing window.showQuickPick)
    # and the proceeds to ask for the server for the actual implementation.
    Command(
        "sema4ai.createRobot",
        "Create Task Package",
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.createActionPackage",
        "Create Action Package",
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.createTaskOrActionPackage",
        "Create Action Package",
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(add)",
    ),
    # Internal commands for sema4ai.createRobot.
    Command(
        "sema4ai.listRobotTemplates.internal",
        "Provides a list with the available Task Package templates",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.createRobot.internal",
        "Actually calls rcc to create the Task Package",
        add_to_package_json=False,
        server_handled=True,
    ),
    # Started from the client due to needing UI actions.
    Command(
        "sema4ai.uploadRobotToCloud",
        "Upload Task Package to Control Room",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.localListRobots.internal",
        "Lists the activities currently available in the workspace",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.isLoginNeeded.internal",
        "Checks if the user is already linked to an account",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.getLinkedAccountInfo.internal",
        "Provides information related to the current linked account",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.cloudLogin",
        "Link to Control Room",
        add_to_package_json=True,
        server_handled=False,
        icon="$(link)",
    ),
    Command(
        "sema4ai.cloudLogin.internal",
        "Link to Control Room (receives credentials)",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.cloudListWorkspaces.internal",
        "Lists the workspaces available for the user (in the Control Room)",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.uploadToNewRobot.internal",
        "Uploads a Task Package as a new Task Package in the Control Room",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.uploadToExistingRobot.internal",
        "Uploads a Task Package as an existing Task Package in the Control Room",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.runInRcc.internal",
        "Runs a custom command in RCC",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.runRobotRcc",
        "Run Task Package",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.runActionFromActionPackage",
        "Run Action (from Action Package)",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.debugRobotRcc",
        "Debug Task Package",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.debugActionFromActionPackage",
        "Debug Action (from Action Package)",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.robotsViewTaskRun",
        "Launch Task",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/run.svg", "dark": "images/dark/run.svg"},
    ),
    Command(
        "sema4ai.robotsViewTaskDebug",
        "Debug Task",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/debug.svg", "dark": "images/dark/debug.svg"},
    ),
    Command(
        "sema4ai.robotsViewActionRun",
        "Launch Action",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/run.svg", "dark": "images/dark/run.svg"},
    ),
    Command(
        "sema4ai.robotsViewActionDebug",
        "Debug Action",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/debug.svg", "dark": "images/dark/debug.svg"},
    ),
    Command(
        "sema4ai.robotsViewActionEditInput",
        "Configure Action Input",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(symbol-variable)",
    ),
    Command(
        "sema4ai.robotsViewActionOpen",
        "Open Action",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(go-to-file)",
    ),
    Command(
        "sema4ai.runRobocorpsPythonTask",
        "Run Sema4.ai's Python Task",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/run.svg", "dark": "images/dark/run.svg"},
    ),
    Command(
        "sema4ai.debugRobocorpsPythonTask",
        "Debug Sema4.ai's Python Task",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon={"light": "images/light/debug.svg", "dark": "images/dark/debug.svg"},
    ),
    Command(
        "sema4ai.saveInDiskLRU",
        "Saves some data in an LRU in the disk",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.loadFromDiskLRU",
        "Loads some LRU data from the disk",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.computeRobotLaunchFromRobocorpCodeLaunch",
        "Computes a Task Package launch debug configuration based on the Sema4.ai launch debug configuration",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.setPythonInterpreter",
        "Set python executable based on robot.yaml",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.resolveInterpreter",
        "Resolves the interpreter to be used given a path",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.cloudLogout",
        "Unlink and remove credentials from Control Room",
        add_to_package_json=True,
        server_handled=False,
        icon="$(debug-disconnect)",
    ),
    Command(
        "sema4ai.cloudLogout.internal",
        "Unlink and remove credentials from Control Room internal",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.refreshRobotsView",
        "Refresh Task/Action Packages view",
        add_to_package_json=True,
        server_handled=False,
        icon={"light": "images/light/refresh.svg", "dark": "images/dark/refresh.svg"},
    ),
    Command(
        "sema4ai.refreshRobotContentView",
        "Refresh Task Package Content view",
        add_to_package_json=True,
        server_handled=False,
        icon={"light": "images/light/refresh.svg", "dark": "images/dark/refresh.svg"},
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.newFileInRobotContentView",
        "New File",
        add_to_package_json=True,
        server_handled=False,
        icon="$(new-file)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.newFolderInRobotContentView",
        "New Folder",
        add_to_package_json=True,
        server_handled=False,
        icon="$(new-folder)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.deleteResourceInRobotContentView",
        "Delete",
        add_to_package_json=True,
        server_handled=False,
        icon="$(close)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.renameResourceInRobotContentView",
        "Rename",
        add_to_package_json=True,
        server_handled=False,
        icon="$(edit)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.refreshCloudView",
        "Refresh Sema4.ai view",
        add_to_package_json=True,
        server_handled=False,
        icon={"light": "images/light/refresh.svg", "dark": "images/dark/refresh.svg"},
    ),
    Command(
        "sema4ai.getLocatorsJsonInfo",
        "Obtain information from the locators.json given a robot.yaml",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.removeLocatorFromJson.internal",
        "Remove a named locator from locators.json",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.removeLocatorFromJson",
        "Remove Locator",
        add_to_package_json=True,
        hide_from_command_palette=True,
        server_handled=False,
        icon="$(trash)",
    ),
    Command(
        "sema4ai.openLocatorsJson",
        "Open locators.json",
        add_to_package_json=True,
        hide_from_command_palette=True,
        server_handled=False,
        icon="$(go-to-file)",
    ),
    Command(
        "sema4ai.openCloudHome",
        "Open cloud home",
        add_to_package_json=True,
        hide_from_command_palette=True,
        server_handled=False,
        icon="$(cloud)",
    ),
    # This is the same as the one above, but it won't ask what's the robot, it'll
    # just use the one selected in the robots tree.
    Command(
        "sema4ai.newRobocorpInspectorBrowser",
        "Add Web Locator",
        add_to_package_json=True,
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.newRobocorpInspectorWindows",
        "Add Windows Locator",
        add_to_package_json=True,
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.newRobocorpInspectorImage",
        "Add Image Locator",
        add_to_package_json=True,
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.newRobocorpInspectorJava",
        "Add Java Locator",
        add_to_package_json=True,
        server_handled=False,
        icon="$(add)",
    ),
    Command(
        "sema4ai.openPlaywrightRecorder",
        "Open Playwright Recorder",
        add_to_package_json=True,
        server_handled=False,
        icon={"light": "images/light/run.svg", "dark": "images/dark/run.svg"},
    ),
    Command(
        "sema4ai.openPlaywrightRecorder.internal",
        "Open Playwright Recorder Internal",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
        icon={"light": "images/light/run.svg", "dark": "images/dark/run.svg"},
    ),
    Command(
        "sema4ai.editRobocorpInspectorLocator",
        "Edit locator",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(edit)",
    ),
    Command(
        "sema4ai.copyLocatorToClipboard.internal",
        "Copy locator name to clipboard",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(clippy)",
    ),
    Command(
        "sema4ai.openRobotTreeSelection",
        "Configure Task Package (robot.yaml)",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(go-to-file)",
    ),
    Command(
        "sema4ai.openRobotCondaTreeSelection",
        "Configure Dependencies (conda.yaml)",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(list-tree)",
    ),
    Command(
        "sema4ai.openPackageYamlTreeSelection",
        "Configure Action Package (package.yaml)",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(list-tree)",
    ),
    Command(
        "sema4ai.openExternally",
        "Open externally",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(go-to-file)",
    ),
    Command(
        "sema4ai.openInVSCode",
        "Open in VSCode",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(file)",
    ),
    Command(
        "sema4ai.revealInExplorer",
        "Reveal in File Explorer",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(file-submodule)",
    ),
    Command(
        "sema4ai.revealRobotInExplorer",
        "Reveal robot.yaml in File Explorer",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(file-submodule)",
    ),
    Command(
        "sema4ai.cloudUploadRobotTreeSelection",
        "Upload Task Package to Control Room",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(cloud-upload)",
    ),
    Command(
        "sema4ai.rccTerminalCreateRobotTreeSelection",
        "Open terminal with Package Python environment",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=False,
        icon="$(terminal)",
    ),
    Command(
        "sema4ai.sendMetric",
        "Send metric",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.submitIssue.internal",
        "Submit issue (internal)",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command("sema4ai.submitIssue", "Submit issue to Sema4.ai", server_handled=False),
    Command(
        "sema4ai.inspector.internal",
        "Inspector Manager (internal)",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.inspector",
        "Open Inspector",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.inspector.duplicate",
        "Create & manage locators",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.errorFeedback.internal",
        "Error feedback (internal)",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.feedback.internal",
        "Feedback (internal)",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.configuration.diagnostics.internal",
        "Task Package Configuration Diagnostics (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.configuration.diagnostics",
        "Task Package Configuration Diagnostics",
        server_handled=False,
    ),
    Command(
        "sema4ai.rccTerminalNew",
        "Terminal with Task Package environment",
        server_handled=False,
        icon="$(terminal)",
    ),
    Command(
        "sema4ai.listWorkItems.internal",
        "Lists the work items available for a Task Package",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.updateLaunchEnv",
        "Updates the environment variables used for some launch (given a Task Package",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.updateLaunchEnv.getVaultEnv.internal",
        "Provides the environment variables related to the vault.",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.newWorkItemInWorkItemsView",
        "New Work Item",
        add_to_package_json=True,
        server_handled=False,
        icon="$(add)",
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.deleteWorkItemInWorkItemsView",
        "Delete Work Item",
        add_to_package_json=True,
        server_handled=False,
        icon="$(trash)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.helpWorkItems",
        "Work Items Help",
        add_to_package_json=True,
        server_handled=False,
        icon="$(question)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.convertOutputWorkItemToInput",
        "Convert output work item to input",
        add_to_package_json=True,
        server_handled=False,
        icon="$(fold-up)",
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.verifyLibraryVersion.internal",
        "Collect a library version and verify if it matches some expected version",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.connectWorkspace",
        "Connect to Control Room Workspace (vault, storage, ...)",
        icon="$(lock)",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.disconnectWorkspace",
        "Disconnect from Control Room Workspace",
        icon="$(unlock)",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.getConnectedVaultWorkspace.internal",
        "Gets workspace id currently connected",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.setConnectedVaultWorkspace.internal",
        "Sets the currently connected Control Room Workspace",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.openVaultHelp",
        "Open vault help",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.clearEnvAndRestart",
        "Clear Sema4.ai (RCC) environments and restart Sema4.ai",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.showOutput",
        "Show Sema4.ai > Output logs",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.showInterpreterEnvError",
        "Show error related to interpreter env creation",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.openFlowExplorerTreeSelection",
        "Open Flow Explorer",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=True,
        icon="$(type-hierarchy-sub)",
    ),
    Command(
        "sema4ai.profileImport",
        "Import Profile",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=False,
        icon="$(file-symlink-file)",
    ),
    Command(
        "sema4ai.profileImport.internal",
        "Import Profile (internal)",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.profileSwitch",
        "Switch Profile",
        add_to_package_json=True,
        server_handled=False,
        hide_from_command_palette=False,
        icon="$(git-pull-request)",
    ),
    Command(
        "sema4ai.profileSwitch.internal",
        "Switch Profile",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.profileList.internal",
        "List Profiles",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.hasPreRunScripts.internal",
        "Has Pre Run Scripts",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.runPreRunScripts.internal",
        "Run Pre Run Scripts",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.getPyPiBaseUrls.internal",
        "Get PyPi base urls",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.startActionServer",
        "Start Action Server",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.downloadActionServer",
        "Download Action Server",
        add_to_package_json=True,
        server_handled=False,
    ),
    Command(
        "sema4ai.startActionServer.internal",
        "Start Action Server (internal)",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.listActions.internal",
        "Lists the actions available in an action package given a root dir (internal)",
        add_to_package_json=True,
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.packageEnvironmentRebuild",
        "Rebuild Package Environment",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.packagePublishToDesktopApp",
        "Publish Package to Sema4.ai Desktop",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.listActionTemplates.internal",
        "Provides a list with the available Action templates",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.createActionPackage.internal",
        "Actually calls Action Server to create the Action Package",
        add_to_package_json=False,
        server_handled=True,
    ),
    Command(
        "sema4ai.actionServerCloudLogin",
        "Authenticate the Action Server to Control Room",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerCloudLogin.internal",
        "Authenticate the Action Server to Control Room (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerCloudVerifyLogin.internal",
        "Verify that the action server Control Room credentials are saved (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerCloudListOrganizations.internal",
        "List Action Server authenticated organizations (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackageBuild",
        "Build Action Package to Workspace",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.actionServerPackageBuild.internal",
        "Build Action Package (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackageUpload.internal",
        "Upload action package to the Control Room (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackageStatus.internal",
        "Get action package upload status from the Control Room (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackageSetChangelog.internal",
        "Set action package changelog entry in the Control Room (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackagePublish",
        "Publish Action Package to Control Room",
        server_handled=False,
        hide_from_command_palette=True,
    ),
    Command(
        "sema4ai.actionServerPackageMetadata",
        "Create Action Package metadata file",
        server_handled=False,
        hide_from_command_palette=False,
    ),
    Command(
        "sema4ai.actionServerPackageMetadata.internal",
        "Create Action Package metadata file (internal)",
        server_handled=True,
        hide_from_command_palette=True,
    ),
]


def get_keybindings_for_json():
    keybinds_contributed = []
    for command in COMMANDS:
        if not command.add_to_package_json:
            continue

        if command.keybinding:
            keybinds_contributed.append(
                {
                    "key": command.keybinding,
                    "command": command.name,
                    "when": "editorTextFocus",
                }
            )

    return keybinds_contributed


def get_commands_for_json():
    commands_contributed = []
    for command in COMMANDS:
        if not command.add_to_package_json:
            continue
        dct = {"command": command.name, "title": command.title, "category": "Sema4.ai"}
        if command.icon:
            dct["icon"] = command.icon
        if command.enablement:
            dct["enablement"] = command.enablement
        commands_contributed.append(dct)

    return commands_contributed


def get_activation_events_for_json():
    activation_events = []
    for command in COMMANDS:
        activation_events.append("onCommand:" + command.name)

    activation_events.append("onDebugInitialConfigurations")
    activation_events.append("onDebugResolve:sema4ai")

    return activation_events
