class Setting:
    def __init__(
        self,
        name,
        default,
        description,
        setting_type=["string", "null"],
        enum=None,
        js_type=None,
        add_to_json=True,
    ):
        """
        :param name:
        :param default:
        :param description:
        :param setting_type:
            Can be something as 'string', 'array', 'number', 'boolean'.
        :param enum:
            If it must be a predefined value, this can be a list with the values
            i.e.: ['alpha','bravo','charlie']
        :param js_type:
            If it's an array of strings, this should be something as string[]
        """
        self.name = name
        self.default = default
        self.description = description
        self.setting_type = setting_type
        self.enum = enum
        self.js_type = js_type
        self.add_to_json = add_to_json


SETTINGS = [
    Setting(
        "sema4ai.language-server.tcp-port",
        0,
        "If the port is specified, connect to the language server previously started at the given port. Requires a VSCode restart to take effect.",
        setting_type="number",
    ),
    Setting(
        "sema4ai.language-server.args",
        [],
        'Specifies the arguments to be passed to the Sema4.ai language server (i.e.: ["-vv", "--log-file=~/sema4ai_code.log"]). Requires a VSCode restart to take effect.',
        setting_type="array",
        js_type="string[]",
    ),
    Setting(
        "sema4ai.language-server.python",
        "",
        "Specifies the path to the python executable to be used for the Sema4.ai Language Server (the default is searching python on the PATH). Requires a VSCode restart to take effect.",
        setting_type="string",
    ),
    Setting(
        "sema4ai.rcc.location",
        "",
        "Specifies the location of the rcc tool.",
        setting_type="string",
    ),
    Setting(
        "sema4ai.rcc.endpoint",
        "",
        "Can be used to specify a different endpoint for rcc.",
        setting_type="string",
    ),
    Setting(
        "sema4ai.rcc.config_location",
        "",
        "Specifies the config location used by rcc.",
        setting_type="string",
    ),
    Setting(
        "sema4ai.home",
        "",
        "Specifies the value for SEMA4AI_HOME (where the conda environments will be downloaded). Must point to a directory without spaces in it.",
        setting_type="string",
    ),
    Setting(
        "sema4ai.verifyLSP",
        True,
        "Verify if the Robot Framework Language Server is installed?",
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.autoSetPythonExtensionInterpreter",
        True,
        "If a file in a Robot is opened, the python extension interpreter is automatically set to match the Robot interpreter.",
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.autoSetPythonExtensionDisableActivateTerminal",
        True,
        'Automatically sets the value of "python.terminal.activateEnvironment" to false to avoid wrong auto-activation when Robot terminal is created.',
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.proceedWithLongPathsDisabled",
        False,
        "Enables Sema4.ai to be started even with long paths disabled.",
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.vaultTokenTimeoutInMinutes",
        30,
        "Specifies the timeout in minutes for the token generated to access the vault when a launch is made. Note: max 60, min 5, additional timeout may be added internally to reuse the token in future runs (please use Sema4.ai Control Room for longer runs).",
        setting_type="number",
    ),
    Setting(
        "sema4ai.codeLens.roboLaunch",
        True,
        "Specifies whether the 'Run Task' and 'Debug Task' code lenses should be shown.",
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.codeLens.actionsLaunch",
        True,
        "Specifies whether the 'Run Action' and 'Debug Action' code lenses should be shown.",
        setting_type="boolean",
    ),
    Setting(
        "sema4ai.codeLens.devTask",
        True,
        "Specifies whether the 'Run Task' and 'Debug Task' code lenses should be shown in `dev-tasks` in `package.yaml`.",
        setting_type="boolean",
    ),
]


def get_settings_for_json():
    settings_contributed = {}
    for setting in SETTINGS:
        if not setting.add_to_json:
            continue
        dct = {
            "type": setting.setting_type,
            "default": setting.default,
            "description": setting.description,
        }
        if setting.enum:
            dct["enum"] = setting.enum
        settings_contributed[setting.name] = dct
    return settings_contributed
