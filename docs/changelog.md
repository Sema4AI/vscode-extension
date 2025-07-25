## Unreleased

- Disable notifications for computing datasource status in background.
- Update Agent CLI to `v1.3.4`
- Enabled new organizations to be part of the Agent spec & the Actions folder in the Agent Package
- Support for the `v3` of the Agent spec.
  - Adds support for defining `mcp-servers` in the `agent-spec.yaml`.
- Properly handle `dev-dependencies` (lint and hover) in `package.yaml`.
- Fixed where the choice of forcing the creation of an action package from a template in a non-empty dir was not respected.
- Updated Action Server to `2.13.1`.

## New in 2.13.0 (2025-06-10)

- Check linting errors with ruff when we work with a python file inside an agent or action.
- Add support for knowledge bases
- Update data-server-cli to `1.1.9-alpha2`
- Add support for macOS ARM64 build
- Update Agent CLI to `v1.1.5`
- Update Action server to `2.10.0`
- Add better linting when an action is modified inside an agent.
- Add error message when an action from an agent inside Sema4ai folder is modified.
- Add `kill-lock-holder` flag to action server to kill the lock holder when starting action server for doing OAuth2 flows.
- Fixed issue with Publishing Action Package to Studio

## New in 2.12.0 (2025-05-07)

- Update RCC to `v20.1.1`
- Update Agent CLI to `v1.1.0`
- Changed agent package publishing to use the folder instead of the packaging it as zip if Studio supports it.
- Added `SEMA4AI_FILE_MANAGEMENT_URL` environment variable when running actions to `file://<path-to-package>/devdata/chat-files`.
- Updated Action Server to `2.9.0`

## New in 2.11.0 (2025-03-11)

- Pass datasource `name` and `engine` parameters to `sema4ai-data.database.add` call
- Update Agent CLI to `v1.0.0`
- Add semver version check for agent and action packages
- The `Package Resources` and `Control Room` are initially collapsed when the Sema4.ai
  extension is started the first time (after that, the state when vscode is closed is used).

## New in 2.10.0 (2025-02-28)

- Display a warning to alert users of any unsaved changes before publishing an agent or action package.
- Support launching tasks from code lenses with the `Python Debugger (PyDev)` extension.
- Support (validating) `external-endpoints` in `package.yaml` (to allow configuring firewall settings for egress rules).
- Using Action Server `2.6.0` now.
- Fix issue where the default values for the action run wouldn't be generated on some more complex use-cases.

## New in 2.9.2 (2025-01-20)

- Fixed error internally setting up the environment when running a task or action.
  - Note: this made running with work items locally fail.

## New in 2.9.1 (2025-01-20)

- Fixed error where the extension would not pass data server information when running a `@predict`.

## New in 2.9.0 (2025-01-20)

- Update Action Server to `2.5.1`
- Add `sema4ai.fixWrongAgentImport` command
- Show Output button when there are errors while running action or agent package commands
- Show datasource configuration status in the tree
- Add Data Sources to the Packages tree
  - Hover (tree item) action in root element to Setup all Data Sources
  - Hover (tree item) action in root element to Drop all Data Sources
  - Hover (tree item) action: remove Data Source
  - Hover (tree item) action: setup Data Source
    - Supports external Data Sources (requires `VSCode Sema4.ai Data Extension` to be installed)
    - Supports generated Data Sources (files, models and custom SQL)
      - A progress bar is shown until all models are actually ready
  - Hover (tree item) action: open Data Source definition location
  - Tooltip shows Data Source information
- New command to get actions metadata: `sema4ai.getActionsMetadata`
- Branding:
  - A new icon is used to represent the view and the extension.
  - The extension display name is now `Sema4.ai SDK`.
- Search for `actions`/`queries`/`predictions` considering all glob patterns supported by `sema4ai.actions`.
- Use `package.yaml` directory as the `cwd` when searching for `actions`/`queries`/`predictions` if available (otherwise imports could fail).
- Progress is shown when creating the input file for an `action`/`query`/`prediction`.
- Integrate with the `VSCode Sema4.ai Data Extension` to get the Data Server info to run data actions.
- `robocorp-trustore` is no longer used (it's not needed anymore).
- `sema4ai-http-helper` is now used to make http requests (to the Data Server).
- `Python 3.11` is now used as the base interpreter.
- When launching, if the Data Sources are not properly configured, show error message to the user.
- It's now possible to run `@query` and `@predict` decorated methods from the tree.
- Code lenses are now shown to run `@query` and `@predict` decorated methods.
- Agent CLI updated to `0.2.2`
- Action input format automatically updated to `v3` (now have a `kind` field and an `actionSignature` field).
  - If the signature changes between action launches, the input file metadata is automatically updated.
- Don't warn the user if the `uv` version is not the latest in `package.yaml`.

## New in 2.8.1 (2024-11-21)

- Version bump due to error in deploy pipeline.
- For more info see `New in 2.8.0`

## New in 2.8.0 (2024-11-20)

- Listing actions now will include `query` and `predict` decorators.
- Add `Configure Action Input` internal command.
- Set `SEMA4AI_CREDENTIAL_API` environment variable if port is communicated from Studio
- Add packages and tools information when submitting an issue.
- Update Action Server to `2.0.0`.
- Update RCC to `v18.5.0`.
- Using RCC directly to build the environment using `package.yaml` (instead of creating a `conda.yaml` first).
- When dealing with a `package.yaml`, always consider the `dev-environment` when building the environment.
- Add code lenses to:
  - `Run Dev Task` (for `dev-tasks` inside a `package.yaml`)
  - `Run Action` (for `@action` decorated methods in `.py` files)
  - `Debug Action` (for `@action` decorated methods in `.py` files)
- Fixed vulnerability when creating temp file to create terminal (it could create a `.bat` / `.sh` file in a directory which could be shared by multiple users).
- Add `Import Action Package` command to sidebar UI.
- Include Sema4ai actions when refreshing the agent spec.

## New in 2.7.0 (2024-10-22)

- Fix error message when importing or creating a new agent.
- Update Action Server dep to 1.1.1
- Use `SEMA4AI_VSCODE_X_ACTION_CONTEXT` instead of `SEMA4AI-VSCODE-X-ACTION-CONTEXT` when launching actions (using `-` is not a valid env variable name in some situations)
- Add `Sema4.ai: Collpase All Entries` command and button in Agent/Action view.
- Added command to import action packages from Sema4.ai Gallery or zip files.
- Updated icons.
- Update Agent CLI to `v0.0.27`
- Update Action Server to `v1.1.2`

## New in 2.6.6 (2024-10-07)

- Add `Refresh Agent Configuration` command as a Quick Fix for issues in the `agent-spec.yaml`.
- Fixed issue where the `Action Server` was not downloaded automatically when requesting OAuth2 settings.
- Providing progress on all situations when downloading the `Action Server`.

## New in 2.6.5 (2024-10-04)

- Fixed issue generating the input for an action when there are complex types inside a list.

## New in 2.6.4 (2024-10-03)

- Fixed integration with `Robot Framework Language Server` (requires `Robot Framework Language Server` **1.13.0**).
- Warn user when the format of the action input file is not `v2`.

## New in 2.6.3 (2024-10-02)

- Focus newly created action or agent package when the user is in the extension view
- When creating the input (json) for an action, it's now pre-populated based on the action's parameters.
- The action input (json) file now supports multiple inputs.
- Expand the view when there is only one Agent / Action
- Fix `Publish Agent to Studio` from sidebar agent selection
- Fixed edge cases with the `Refresh Agent Configuration` command
- New command: `Sema4.ai: Refresh Agent Configuration`
- New command: `Sema4.ai: Update Agent Version`
- Add additional analysis to make sure that action packages are unzipped when in VSCode.

## New in 2.5.0 (2024-09-18)

- Add `Create Action Package` command to side-bar.
- Action packages commands now supports selection from agents.
- New command: `Sema4.ai: Import Agent Package (Zip)`.
- New Command: `Sema4.ai: Open Agent Runbook`.
- When an action package is created inside an agent, the agent spec is updated accordingly.
- Renamed Commands:
  - Open Agent Spec (agent-spec.yaml) → Configure Agent
  - Configure Action Package (package.yaml) → Configure Action Package
  - Build Action Package to Workspace -> Build Action Package (zip)
  - Open the Action Package OpenAPI Spec (metadata.json) -> Preview the Package OpenAPI Spec (metadata.json)
  - Pack Agent Package -> Export Agent Package (zip)
- UI Update: Moved `Configure Agent` and `Configure Action Package` from the `Commands` section to the top level of the agent/action.
- Hover for `agent-spec.yaml` (using new spec format for v2)
- Code analysis for `agent-spec.yaml` (using new spec format for v2)
  - Basic analysis for the full spec based on paths/types
  - Checks if the `zip`, `folder` type matches the actual referenced type
  - Checks if the action package `name` matches the referenced value
  - Checks if the action package `version` matches the referenced value
  - Checks that all the actions found under `actions` are properly referenced in the `agent-spec.yaml`
  - Note: handles both .zip and expanded action packages.
- New dependency required: `tree-sitter`
- Update `robocorp-trustore` dependency to 0.9.1
- No longer use `requests` (due to breakage with truststore)
- Make downloads with resume
- Update `agent-cli` to `v0.0.19`
- Location for agent cli and action server is no longer customizable
  - It's now always downloaded in a default path in the extension.
  - Current version: `0.0.19`
- Add `Publish Agent  to Studio` command
- Add `Export Agent Pack` sidebar command
- When running `rcc task run`, add `--bundled` and `--sema4ai` flags.
- Upgrade to `Action Server` to `0.23.2`
- Accept OAuth2 without `clientSecret` (using `pkce` flow).
- The yaml for `OAuth2` is now different (saved in new location with new structure).
  - There's now a `mode` which can specify `mode: sema4ai` to use `Sema4.ai` provided configuration (without `clientSecret` required).

## New in 2.4.2 (2024-08-26)

- Fixes creating an Action Package.

## New in 2.4.0 (2024-08-21)

- Updated RCC to `v18.1.5`.
- Properly collect Sema4.ai Extension logs when submitting an issue.
- New Command: `Pack Agent Package`.

## New in 2.3.0 (2024-08-19) -- first `Sema4.ai` extension stable release

- Agent Packages present in the workspace are now shown
  - Each Agent Package entry contains a list of organizations (living under `/actions/` directory inside an Agent Package)
  - Each organization can contain multiple Action Packages
- A new command `Create Agent Package` is available
  - It will create a new Agent Package in the current workspace
  - Command can be run from Command Palette or `Agent Packages` section in the extension's sidebar
- When using `Sema4.ai: Create Action Package` command, it's now possible to specify an Agent Package and organization
  to create the Action Package in (if at least one Agent Package is present in the workspace)
- Option to open `agent-spec.yaml` is shown as a `Command` for an agent.
- Basic code analysis added to the agent-spec.yaml.
- Using `sema4ai` folders instead of `robocorp` folders to build the python environments.
- Update icons.

## New in 2.2.0 (2024-07-16) -- pre-release

- A new command: `Sema4.ai: Open the Action Package OpenAPI Spec (metadata.json)` is available.
  - It'll create a file showing the `metadata.json` for the Action Package.
  - Also available under `Activities` in the `TASK/ACTION PACKAGES` View.
- A prompt allowing to restart the Action Server will appear now when an environment file (`package.yaml`) is modified in an Action Package.
- Fix build Action Package command to add selection step to select the Action Package in case there are multiple in the workspace.
- The extension now uses `sema4ai` folders instead of `robocorp`.
  - The `SEMA4AI_HOME` environment variable can be used to configure the environments directory instead of `ROBOCORP_HOME`.
  - In Windows the environments are now in now in `%LOCALAPPDATA%/sema4ai`
  - In Linux/Mac the environments are now in now in `<home>/.sema4ai`
- When configuring the input.json for an `@action`, it's possible to do the OAuth2 flow automatically when the action is
  run by adding a `"vscode:request:oauth2"` entry to the input.

The example below shows a case where a `count` parameter is specified as `1` and
OAuth2 will be requested for the `google_secret` parameter.

```json
{
  "count": 1,
  "vscode:request:oauth2": {
    "google_secret": {
      "type": "OAuth2Secret",
      "scopes": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/gmail.send"
      ],
      "provider": "google"
    }
  }
}
```

- A new command: `Sema4.ai: Open OAuth2 Settings` is available.
  - It can be used to open the file where the OAuth2 settings must be configured.
- A new command: `Sema4.ai: OAuth2 Logout` is available.
  - It can be used to logout of a given OAuth2 provider which was previously logged in when a launch was done.

## New in 2.1.0 (2024-06-25) -- pre-release

- Improvements when running actions:
  - Logs will show local variables (ROBOT_ROOT is no longer set).
  - ROBOT_ARTIFACTS set to a better place for the log.html.
  - If using `sema4ai-actions 0.7.0` or newer, the results of running an action are printed to the terminal.
- `Sema4.ai: Create Action Package` allows to specify a template to use now (for Action Server v0.10.0 or newer).
- `Robo Tasks Output` tab has been renamed to `Task/Action Output`, and it now shows logs from Action runs.
- A prompt allowing to restart the Action Server will appear now, when a Python file is modified in an Action package with active Action Server.
- Add command to authenticate Action Server to Control Room
- Add command to publish Action Package to Control Room
- Hide command to authenticate the Action Server to Control Room
- Hide command for publishing Action Package to Control Room
- Add command to build Action Package to current workspace
- Add UI element under activities to build Action Package to current workspace

## New in 2.0.1 (2024-05-24) -- pre-release

- Add functionality to publish Action Package to Sema4 Desktop Application

## New in 2.0.0 (2024-05-23) -- pre-release

- Rename Robocorp references to Sema4.ai

## New in 1.22.4 (2024-05-22) -- pre-release

- First `Sema4.ai` VSCode Extension release

# Below is the changelog for what was `Robocorp Code`, the precursor of `Sema4.ai`

## New in 1.22.2 (2024-05-20)

- If `Action Server 0.10.0` onwards is being used, creates a project using the `--template minimal`.
- In the new project, if the project is not empty and the user agreed to proceed, create the contents even if it means overriding what's there.

## New in 1.22.1 (2024-05-04)

- `--use-feature=truststore` is no longer added to rcc conda.yaml when using uv.

## New in 1.22.0 (2024-05-03)

- Updated RCC to `v17.28.4`.

- Fixed issue in the Caching system for the RCC Python Env.

- Added command for rebuilding the rcc environment.

- Added shortcut to the Activities for the task/action package.

- Added listeners for workspace files that trigger question for user to rebuild env or refresh view

- Activating the Terminal command. Correcting the environment injection to have the proper Python env set up

- Terminal opens CMD Prompt for Windows (environment activation is better)

- Added new param to rcc `--no-pyc-management`.

## New in 1.21.0 (2024-04-25)

- `sema4ai-actions` is now supported (`robocorp-actions` is still supported, although it's
  now considered deprecated as `sema4ai-actions` is a drop-in replacement).

## New in 1.20.2 (2024-04-23)

- Fixed issue where automatically installing browser would fail (on Windows).

## New in 1.20.1 (2024-04-12)

- New Java Inspector available!
  - The Java Inspector will be supported only on Windows OS.
- (Action Package support) Properly supports robocorp-actions 0.2.0 (for linting actions).
- (Action Package support) When subitems of a task package are selected it's possible that the work-items aren't shown in the package tree.
- (Action Package support) Preferred action server version is now 0.3.2.
- Updated dependency versions (to fix CVEs).

## New in 1.19.0 (2024-03-12)

- New action: `Sema4.ai: Download Action Server` (downloads the latest version of the Action Server).

## New in 1.18.0 (2024-02-29)

- (Action Package support) `package.yaml` file is now linted.
- (Action Package support) Hover support to get versions on `package.yaml`.
- (Action Package support) New action to `Run Action (from Action Package)`
- (Action Package support) New action to `Debug Action (from Action Package)`
- (Action Package support) Fixed issue collecting actions as `@action(is_consequential=True)`
- (Action Package support) It's now possible to create a new Action Package directly from VSCode
- (Action Package support) Suggests the download of a newer version of the Action Server
- (Web Inspector) Added the isolated environment to the browser configuration every time the browser is initialized and when it's getting installed
- (Web Inspector) Fixing the issues on MacOS with the browser getting stuck until user restarts VSCode
- (Web Inspector) New feature of changing the viewport resolution from the Web Inspector UI
- (Web Inspector) Updated the vendored `robocorp-browser` to the latest version
- RCC upgraded to to `v17.18.0`.

## New in 1.17.0 (2024-02-23)

- Support for Action Packages for the [Action Server](https://robocorp.com/docs/action-server)
  - Expected support with `package.yaml`, available on action server `0.0.21`.
  - Download and run action server.
  - List `@action`s (refresh is not automatic at this point).
  - Open `@action`.
  - Note: Task Packages (Robots) will still use `robot.yaml` and `conda.yaml`.
- Improved Image inspector
- Fixed issue recognizing `--use-feature=trustore` in the validation of `conda.yaml`.

## New in 1.16.0 (2024-02-02)

- Added linting for methods marked as `@action`.

## New in 1.15.1 (2024-01-25)

- Fixed issue where using `action-server.yaml` for the action server environment
  didn't do the semantic checks done for `conda.yaml`.

## New in 1.15.0 (2024-01-24)

- Accept`action-server.yaml` for the action server environment bootstrap
  (still requires `robot.yaml` alongside it).

## New in 1.14.2 (2024-01-12)

- Several improvements to the Robocorp Inspector
  - Note: First experimental version, looking for feedback!
- Renaming to the new terminology for the Side Bar
  - Note: Part of moving to Task Packages & Tasks & Actions

## New in 1.14.0 (2023-12-21)

- New Browser/Windows inspector/recorder available!
  - Note: First experimental version, looking for feedback!
- RCC upgraded to to `v17.12.0`.

## New in 1.12.0 (2023-09-28)

- RCC upgraded to to `v16.5.0`.
- `robocorp-trustore` is now used (so, SSL should use certificates from the machine).
- `ROBO TASKS OUTPUT` updated:
  - It's now possible to click icon to show details (so, items without a message are also clickable)
  - The copy to clipboard button for variables no longer hides variable content.

## New in 1.11.0 (2023-09-07)

- When hovering over conda dependencies in `conda.yaml`, information from conda-forge is shown.
- Warning if the versions for conda-forge in `conda.yaml` have updates.
- RCC is now distributed along with `Sema4.ai` (so, it'll no longer be downloaded in the first activation).
- A warning is no longer shown if a pre-release is available in pypi and the latest version is actually being used already.
- Fixed issue where a parse exception was shown when a git url was used to install a pip dependency.
- Fixed issue where a method decorated with `@task_cache` would have code lenses which should only appear to `@task`.

## New in 1.10.0 (2023-08-21)

- RCC upgraded from `v14.6.0` to `v14.15.4`.
- Information from pypi is shown on hover for pypi packages in `conda.yaml`.
- Warning if the versions for pypi in `conda.yaml` have updates.
- Warning if `python` version is not `>= 3.8` in `conda.yaml`
- Warning if `pip` version is not `>= 22.0` in `conda.yaml`
- `ROBO TASKS OUTPUT` updated to latest version:
  - Support for `robocorp-log 2.7.0`:
    - `if` statements now create a scope in `log.html` (when the function is not a generator).
    - If an exception has a cause or context the context/cause is now shown in the log
      - (i.e.: when an exception is raised from another exception or is raised while handling another exception all exceptions are shown).
    - `continue` and `break` inside a loop are properly handled.
    - `continue` and `break` are now shown in the logs.
    - It's now possible to expand / collapse recursively in `log.html`.
    - `log.html`: When navigating using left arrow, if the element is already collapsed the parent is focused.

## New in 1.9.0 (2023-08-04)

- If the robot has additional pythonpath entries, set those in the VSCode settings (`python.analysis.extraPaths`).
- If there's some issue computing the Robot environment for a launch that's now shown in the UI.
- `ROBO TASKS OUTPUT` updated to latest version (added status level filtering, tree navigation and search).
- Fixed issue with `preRunScripts` (when target executable is a `.py`, it's searched in the `PATH`).
- Converter now has DOT as a target language.

## New in 1.8.1 (2023-08-04)

- Fixed issue with `preRunScripts` (launching python now always uses python in the robot target environment).

## New in 1.8.0 (2023-07-21)

- Conversion accelerator now accepts Python as a target language.
- When linking an account the workspace to connect to is asked right away.
- The UI now makes it clearer that when connecting a workspace both the vault and the storage work with it.
- `ROBO TASKS OUTPUT` updated to latest version (needed for seeing failed `assert` statements properly).
- Fixed issue which could prevent the playwright recorder from opening.

## New in 1.7.0 (2023-07-12)

- Created action to start the Playwright recorder (`Robocorp: Open Playwright Recorder`).
- Fixed editing of existing locators (used with `rpaframework`).

## New in 1.6.0 (2023-07-10)

- Updated `ROBO TASKS OUTPUT` so that places showing the file/line of messages are now clickable and
  can be used to open the file location inside of VSCode.

- In the `ROBO TASKS OUTPUT`, it's possible to view log messages along with the terminal
  output.

## New in 1.5.0 (2023-07-06)

- Fixed issues in `Run Task` / `Debug Task` (launching `robocorp.tasks`):

  - Robot environment properly used when robot is available.
  - The input work item is properly selected when available.
  - If multiple entry points in the same file were available the selected one will be run.

- If a `robot.yaml` has `preRunScripts` they'll be run prior to launching.

- Integrated `ROBO TASKS OUTPUT` view which shows the output of running with `robocorp.tasks`.
  Note: Requires `robocorp.tasks` version `2.1.1`.

## New in 1.4.0 (2023-06-22)

- When `Robocorp Log` with html target is found on the terminal, properly add option to open the html in the browser.
- Created code-lenses to `Run Task` and `Debug Task` from `robocorp.tasks`.

## New in 1.3.2 (2023-06-20)

- Improvements in the `Conversion Accelerator` integration.

## New in 1.3.0 (2023-05-10)

- RCC upgraded to `v14.6.0`.
- Improvements in the `Conversion Accelerator` integration.

## New in 1.2.0 (2023-03-17)

- RCC upgraded to `v13.9.2`.
- Multiple Inspector improvements (upgraded to `v0.9.1`).
  \_- Critical fix opening inspector a 2nd time.
- Created action: `Robocorp: Import Profile`.
- Created action: `Robocorp: Switch Profile`.
- Showing current profile in Robocorp view.

## New in 1.1.3 (2023-02-13)

- `environmentConfigs` is now properly used in `Sema4.ai` (so, it's possible to use conda freeze files).

## New in 1.1.0 (2023-02-03)

- If the `TEMP` folder being used in the environment is removed the extension properly deals with it.
- Inspector upgrades:
  - Browser Actions Recorder: Improvements in performance and other bug fixes.
  - Browser Actions Recorder: Auto-scroll for the keyword list.
  - Browser Actions Recorder: Code Editor no longer readonly (note: still indifferent to user changes as it will always update).
  - Browser Locator: Fixed buttons not displaying if no matches available.
  - Improved approach to close the browser and app window.

## New in 1.0.2 (2023-01-18)

- Upgrade RCC to `v13.0.1`.

## New in 1.0.0 (2023-01-16)

- `Webview2 Runtime` requirement checked before starting inspector.
- `Web Recorder (BETA)` is now available.
  - Records multiple interactions with Browser.
  - Use `Copy Code` to copy the code for the actions.
  - Allows post-processing to save the locators in locators.json and use aliases or use the locator directly.
- RCC was upgraded to `v12.2.0`.
- Faster Startup (after a successful startup, cached information is used so that subsequent startups are faster).
- When specifying the timeout for the vault, the token is guaranteed to have that as the minimum value (in previous versions it could reuse it for `75%` of the time, so, a `2h` timeout request could return a `0:30h` minutes token).
  - Timeout limits are now in place so that the minimum timeout is 5 minutes and maximum is 1 hour (but the token requested may be a bit higher so that the extension can cache it and reuse it for more time).
  - Note: if a longer timeout is needed for testing, a managed environment such as `Robocorp Control Room` or `Robocorp Assistant` is recommended.

## New in 0.43.0 (2023-01-05)

- New UI for Conversion accelerator from third party RPA to Robocorp Robot.
- Renamed action to `Conversion Accelerator from third party RPA to Robocorp Robot`.

## New in 0.42.0 (2022-12-22)

- RCC was upgraded to `v11.36.3`.
- No longer showing warnings regarding locks at startup.
- It's now possible to proceed even with long paths disabled.
- New setting: `robocorp.vaultTokenTimeoutInMinutes` can be used to change the timeout for the token used for vault access when launching.

## New in 0.41.0 (2022-12-13)

- RCC was upgraded to `v11.33.2`.
- Support for launching RCC when target is not the last argument.

## New in 0.40.2 (2022-12-05)

- Fixed regression where `noDebug` was not being properly set in generated launch.

## New in 0.40.1 (2022-12-03)

- Fixed issue enabling long path support on Windows requiring elevated shell.

## New in 0.40.0 (2022-12-03)

- Robot runs now appear in the `Robot Output` view.
- Upgrades to robocorp-inspector.

## New in 0.39.0 (2022-11-02)

- RCC was upgraded to `v11.30.0`.
- Base environment now requires OpenSSL 3.0.7.
- Upgrades to robocorp-inspector.
- More information is provided when rcc configure longpaths fails.
- Updates in third party RPA conversor.

## New in 0.38.0 (2022-09-28)

- Integration of converter from third party RPA to Robocorp Robots.
  - Activate through the `Robocorp: Convert third party RPA file to Robocorp Robot` command.
- Entries are now properly sorted in the `ROBOT CONTENT` view.

## New in 0.37.0 (2022-09-14)

- Reorganization of the Rocorp Views
  - Actions added as items in the tree and not only on hover to help on discoverability.
  - `Work items` and `Locators` are now in the same `Resources` tree (so that there's a clear place to extend with new features in the future).
- Improved UI for submit issue.
- RCC was upgraded to `v11.26.3`.
- Locators:
  - `robocorp-inspector` was upgraded to `0.7.1`.
  - Added recording functionality to command palette

## New in 0.36.0 (2022-07-20)

- VSCode 1.65.0 is now required to support HTML in markdown contents.
- Cancellation support for RCC environment creation.
- Fix python environment activation (since vscode-python changed the `setActiveInterpreter` API to `setActiveEnvironment`).

## New in 0.35.0 (2022-07-04)

- `RCC` was upgraded to to `v11.14.5`.
- RCC is now configured to put the holotree contents in a location shared by multiple users (which allows
  for the import of pre-created environments from a .zip file).
- The base environment created for the extension bootstrap is now imported from a base environment downloaded from .zip
  (which is _much_ faster).

## New in 0.34.0 (2022-06-07)

- When an error happens creating env, details (and possible solutions) are shown in an editor.

## New in 0.33.0 (2022-05-30)

- `python.terminal.activateEnvironment` is only set to false when making a launch or creating a Robot terminal.
- Debug console is no longer opened when launching in the terminal.

## New in 0.32.0 (2022-04-19)

- Locators: `robocorp-inspector` was upgraded to `0.6.5`.

## New in 0.31.0 (2022-04-13)

- Locators: `robocorp-inspector` was upgraded to `0.6.4`.
- `RCC` was upgraded to to `v11.9.16`.

## New in 0.30.0 (2022-04-05)

- If only a .vscode folder is created, force creation of robot.

## New in 0.29.0 (2022-04-04)

- Automatically set `"python.terminal.activateEnvironment": false`. [#636](https://github.com/Sema4AI/vscode-extension//issues/636)
  - This fixes the case where the `ms-python` extension tries to activate an environment when starting a Robot terminal.
  - It's possible to disable this by setting `"robocorp.autoSetPythonExtensionDisableActivateTerminal": false`.
- `Set pythonPath based on robot.yaml` was renamed to `Set python executable based on robot.yaml`.
- When setting the default interpreter to match the python from the robot, only the internal API is used as `python.pythonPath` is now deprecated.
- When launching the python debugger, the python executable is properly set in the generated launch configuration with `python` instead of `pythonPath`.

## New in 0.28.0 (2022-03-14)

- Created action: `Robocorp: Clear Robocorp (RCC) environments and restart Sema4.ai`.
- RCC updated to v11.6.6.
- New Windows locator integrated.
- Properly notify of timeouts executing RCC.
- Raised timeout for uploading Robots.
- Fix case where Path and PATH could conflict on Windows.
- Pre-releases now available from VSCode marketplace.

## New in 0.27.1 (2022-02-04)

- Fix issue where run failed with error if vault connection was not set.

## New in 0.27.0 (2022-02-03)

- It's now possible to use the online vault secrets from within VSCode.
  - A new `Vault` item is added to the `Robocorp` view which allows setting the workspace for the vault.
  - Note: each new run obtains a new token (valid for 2 hours) to communicate with the vault.

## New in 0.26.0 (2022-01-26)

- The organization is shown when listing workspaces for workspace upload.
- Robot tasks are expanded by default.
- Fixed case where the computed pythonpath entries for a Robot could be wrong.

## New in 0.25.0 (2022-01-19)

- The Python extension interpreter is automatically set to use the Robot environment
  - It's possible to opt out by setting `robocorp.autoSetPythonExtensionInterpreter` to `false`.
  - Action now uses `python.defaultInterpreterPath` or the new (unreleased) API to set the interpreter if available.
- The Robot Framework Language Server `0.37.0` is now required for a critical fix:
  - Handle the case where the target robot is passed as an array for resolving the interpreter (launching with the test explorer could fail due to this).

## New in 0.24.0 (2022-01-17)

- RCC updated to v11.6.3
- The extension now runs with `-v` by default (to show info level messages on `OUTPUT > Sema4.ai`).

## New in 0.23.0 (2021-12-22)

- RCC downgraded to v11.5.5 to avoid regression in v11.6.0
- Environment variables from env.json are properly escaped (new line chars are now properly handled).
- Minimum Robot Framework Language Server version required is now 0.35.0
- Minimum VSCode version required is now 1.61.0

## New in 0.22.0 (2021-12-15)

- Selecting html file in Robot content view properly opens it in external browser by default.

## New in 0.21.0 (2021-12-14)

- RCC updated to v11.6.0.

- robocorp-inspector updated to 0.5.0.

- When sending an issue a confirmation is shown.

- Robots view:

  - A Robot is always auto-selected if available in the workspace.
  - A proper message is shown to guide users on the case where there's no Robot in the workspace.
  - Added option to reveal in explorer.
  - Added button to create new robot.
  - Context menu filled with actions.

- Robot content view:

  - Added option to reveal in explorer.
  - Context menu filled with actions to open file externally or internally.
  - When clicking an item, it's opened even if already selected.

- Robocorp view:

  - Updated labels

- Improvements in the upload Robot UI.
  - Labels
  - Workspaces that the user cannot read are no longer shown.

## New in 0.20.0 (2021-11-16)

- It's now possible to create a Robot in the workspace root folder. [#497](https://github.com/Sema4AI/vscode-extension//issues/497)
- Clicking on inspector button multiple times no longer opens multiple inspectors. [#493](https://github.com/Sema4AI/vscode-extension//issues/493)
- When creating an environment, its output is shown in the `Output` tab interactively and the last line is shown in the progress. [#491](https://github.com/Sema4AI/vscode-extension//issues/491)
- RCC updated to `11.5.5`.

## New in 0.19.0 (2021-11-08)

- When a command line is too big to be launched in the terminal, a wrapper script is used [#394](https://github.com/Sema4AI/vscode-extension//issues/394)
- The default is now launching in the terminal and not in the debug console.

## New in 0.18.0 (2021-11-01)

- When relocating robot, make sure that the `PYTHONPATH` entries are properly forwarded.
- Robot Framework Language Server `0.26.0` is now required.

## New in 0.17.0 (2021-10-21)

- In the Robot view, the commands related to `Robot` and `Task` items are now shown inline.
- The extension now handles the case where an `env.json` with non-string values is used.
- RCC updated to 11.4.2
- When a `work item` selection is cancelled, the related launch is also cancelled.
- When `ROBOCORP_OVERRIDE_SYSTEM_REQUIREMENTS` is set, it's now possible to initialize the extension.

## New in 0.16.0 (2021-10-13)

- Notify of errors during initialization of extension.
- Fix `ROBOT_ROOT` when environment is reused.
- Update RCC to v11.3.2 .
- Improved Robot Template selection from RCC.
- Work items support:
  - See: [Using Work Items](https://robocorp.com/docs/developer-tools/visual-studio-code/extension-features#using-work-items) for details.
  - Variables should not be defined in `env.json` anymore and the support is simplified to only accept items in `devdata/work-items-in` and `devdata/work-items-out`.
  - `devdata/work-items-in` is expected to be added to source conrtol (i.e.: `git`), whereas `devdata/work-items-out` is expected to be ignored.
  - The `RPA_OUTPUT_WORKITEM_PATH` is now set automatically to a new folder in `work-items-out`
    - Later it's possible to convert this folder into an input by using the button which appears in the item in the work items view.
  - When a run is made, it should present a dialog which allows the input selection (to set to `RPA_INPUT_WORKITEM_PATH`)
    - Note that it's possible to use some output in `devdata/work-items-out` as the input for the next run.
  - Only the last 5 runs are kept in the output. To keep older items, rename the folder or move it to `devdata/work-items-in`.
  - For previously existing items, those should be moved to `devdata/work-items-in` so that they are shown.
  - Changing `env.json` should not be needed anymore (in fact, changes to the related variables will be ignored to avoid clashes with other tools).
  - The latest `rpaframework` is required for the integration.

## New in 0.15.0 (2021-10-04)

- Update to RCC v11.2.0.
- If the Robot Framework Language Server is not installed, python debug launches can still resolve the interpreter.

## New in 0.14.0 (2021-09-21)

- Robocorp panel redesigned.
- robocorp-inspector updated to 0.3.8.

## New in 0.13.3 (2021-09-08)

- Fix case where the python used in debug did not match the one used in the environment.
- Two different `conda.yaml` files with only cosmetic changes (such as comments) now map to the same environment.
- Fixes related to `TEMP` directories managed in the environment.
- The default `cwd` when resolving environments is now properly managed so that conflicts don't arise due to having a `robot.yaml` in the `cwd`.
- `--controller` is properly set when making an `rcc` run.

## New in 0.13.2 (2021-09-06)

- Improved detection of whether an environment is corrupt to regenerate it when starting the extension.
- Fixes in inspector integration.

## New in 0.13.1 (2021-08-31)

- Critical fix: if the base environment was removed the extension could fail to initialize.

## New in 0.13.0 (2021-08-30)

- Improved UI is now used to create and edit browser and image locators.
- If it was not possible to create some environment, it won't be retried until the `conda.yaml` is changed or `VSCode` is restarted.
- The language server environment is no longer refreshed on startup (so startup is faster).

## New in 0.12.1 (2021-08-23)

- At most 10 environment are created, using Holotree from RCC (environments are now recycled).
- Upgraded to RCC 10.7.0.
- Deal with `pythonDeprecatePythonPath` when setting the python executable path for vscode-python from a Robot.
- If the Robot Framework Language Server extension is installed in VSCode, at least 0.21.0 is now required.

## New in 0.11.1 (2021-05-27)

- Fixed issue where the Robot environment wasn't being properly forwarded when debugging a plain python Robot.

## New in 0.11.0 (2021-05-26)

- The Robocorp view now has a tree showing the contents of the currently selected robot.
- RCC upgraded to 9.16.0.

## New in 0.10.0 (2021-05-12)

- Support to create a terminal with access to the environment of a `Robot`.
  - It's accessible in the Robot tree view or by executing the `Robocorp: Terminal with Robot environment` action.

## New in 0.9.2 (2021-04-21)

- Fix issue where completions were requested on .yaml files when that shouldn't be the case.
- Support for robot tasks with a `shell` or `robotTaskName`.

## New in 0.9.1 (2021-04-19)

- Upgrade to RCC 9.9.15.

## New in 0.9.0 (2021-04-08)

- New action: `Robocorp: Robot Configuration Diagnostics` to validate a Robot on request.
- Robot configuration is now validated automatically when a `robot.yaml` or `conda.yaml` is opened or saved.

## New in 0.8.2 (2021-03-29)

- Ignoring environment variables starting with `=` (which could end up breaking the language server startup).

## New in 0.8.1 (2021-03-24)

- Upgrade to RCC 9.7.4.

## New in 0.8.0 (2021-02-24)

- Upgrade to RCC 9.4.3. #242
- Fix creating browser locator with rpaframework-core 6.0.0.
- New `Robocorp: Submit issue` command.
  - Allows reporting issues to Robocorp from within VSCode.
  - Attaches logging and system information.

## New in 0.7.1 (2021-01-22)

- Fixed issue starting Sema4.ai on Mac OS and Linux.

## New in 0.7.0 (2021-01-20)

- Tree for Robocorp Cloud info. #225
  - Link credentials.
  - Unlink credentials.
  - Refresh.
  - Workspaces/Robots available.
- Cloud credentials not entered in Sema4.ai are no longer used as a fallback. #230
- Credentials now stored as `sema4ai` instead of `--sema4ai`.
- Upload Robot selected in Robots tree to the cloud.
- Check that the Windows Long Path support is enabled. #235
- Metrics for feature usage. #234
- Properly uploading to a new Robot in the cloud. #229

## New in 0.6.2 (2021-01-07)

- Update RCC to version 7.1.5. #227

## New in 0.6.1 (2020-12-28)

- Improved support for `Image Locators` #220
  - Command to create a new `Image Locator` available from the Locators tree.
  - Command to open selected locator from the Locators tree.
  - When hovering over a `"path"` or `"source"` element in the `locators.json`, a preview is shown.
- If the Robot Framework Language Server extension is not installed, suggest its installation. #212

## New in 0.6.0 (2020-12-21)

- Improved support for [locators](https://robocorp.com/docs/development-howtos/browser/how-to-find-user-interface-elements-using-locators-in-web-applications):
  - Locators from locators.json are shown in the Locators tree.
  - An action to create a new `Browser Locator' by selecting an element in a browser is now available in the tree.
  - When hovering over a `"screenshot"` element in the `locators.json`, a preview is shown.

## New in 0.5.3 (2020-12-08)

- Update RCC to version 7.0.4. #206

## New in 0.5.2 (2020-12-02)

- Unlink user from Robocorp Cloud

## New in 0.5.1 (2020-11-29)

- If `ROBOCORP_HOME` has spaces in the path, detect it and ask for a new path without spaces. #200
- Created `robocorp.home` setting to specify `ROBOCORP_HOME`.

## New in 0.5.0 (2020-11-25)

- New Robots view (lists robots and allows launching/debugging them). #183
- New action to set the pythonPath to be used by the Python extension based on the `robot.yaml`. #185
- Templates available now have a description. #181
- The account used to login is now tied to Sema4.ai. #189
- Initial debug configurations are now provided. #184
- Upgraded to use RCC v6.1.3. #194

## New in 0.4.0 (2020-11-08)

- Plain python Robot Tasks from `robot.yaml` can now also be debugged (note:
  the Python plugin must also be installed). #179
- In the login action, pressing enter without any information will open the
  proper url to obtain the credentials. #177
- If there's only one task to run in the workspace, use it in the Debug/Run Robot
  action. #175
- Upgraded to use RCC v4.

## New in 0.3.0 (2020-10-26)

- Debugging Robot Tasks from `robot.yaml` is now available
  (as long as they start with `python -m robot` and finish with the folder/filename to be run).

## New in 0.2.0 (2020-10-15)

- Launching Robot Tasks from `robot.yaml` is now available.

## New in 0.1.3 (2020-10-12)

- Improved logo
- Feedback metrics incorporated.

## New in 0.1.2 (2020-10-01)

- If a workspace cannot be loaded, other (valid) workspaces should still be loaded. #164

## New in 0.1.1 (2020-09-29)

- Make sure that we use rcc env variables from robot.yaml in the launch too. #159

## New in 0.1.0 (2020-09-29)

- Properly load devdata/env.json when available.

## New in 0.1.0 (2020-09-28)

- Updated logo
- First version to be published to the VSCode marketplace.

## New in 0.0.5 (2020-09-23)

- Working with [robot.yaml](https://robocorp.com/docs/setup/robot-yaml-format) instead of the deprecated `package.yaml`.
- New action to log in Robocorp Cloud.
- Terminology update (`Activity Package` is now `Robot`).
- Improvements uploading Robot to Robocorp Cloud.
- Detecting if a robot.yaml is in a workspace root folder and not only in a subfolder.

## New in 0.0.4 (2020-09-02)

- The extension name changed to Sema4.ai (so, if upgrading from 0.0.3, please
  remove the previous version manually).
- When a package.yaml is found, it's used to provide a different python environment
  when running/debugging `.robot` files using the RobotFramework Language Server.

## New in 0.0.3 (2020-08-12)

- Polishments submiting activity package to the Robocorp Cloud.
- Fixed issue starting RCC after download on Mac.

## New in 0.0.2 (2020-08-06)

- Submit activity package to the Robocorp Cloud (preliminary version)

## New in 0.0.1 (2020-07-27)

- Download rcc (conda manager)
- Use rcc to create conda env to start the language server
- Create an activity using rcc
