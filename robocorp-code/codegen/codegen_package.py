import os.path

from commands import (
    get_activation_events_for_json,
    get_commands_for_json,
    get_keybindings_for_json,
    COMMANDS,
)
from settings import get_settings_for_json, SETTINGS


def convert_case_to_constant(name):
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return (
        re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        .replace(".", "_")
        .replace("-", "_")
        .upper()
    )


def convert_case_to_camel(name):
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return (
        re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        .replace(".", "_")
        .replace("-", "_")
        .upper()
    )


def get_json_contents():
    from robocorp_code import __version__

    base_package_contents = {
        "name": "robocorp-code",
        "displayName": "Robocorp Code",
        "description": "Extension for Robot development in VSCode using Robocorp Cloud",
        "author": "Fabio Zadrozny",
        "homepage": "https://github.com/robocorp/robotframework-lsp/blob/master/robocorp-code/README.md",
        "repository": {
            "type": "git",
            "url": "https://github.com/robocorp/robotframework-lsp.git",
        },
        "license": "Apache 2.0",
        "version": __version__,
        "icon": "images/icon.png",
        "publisher": "robocorp",
        "engines": {"vscode": "^1.43.0"},
        "extensionDependencies": ["robocorp.robotframework-lsp"],
        "categories": [],
        "activationEvents": get_activation_events_for_json(),
        "contributes": {
            "configuration": {
                "title": "Robocorp Code Language Server Configuration",
                "type": "object",
                "properties": get_settings_for_json(),
            },
            "languages": [],
            "grammars": [],
            "debuggers": [],
            "keybindings": get_keybindings_for_json(),
            "commands": get_commands_for_json(),
        },
        "main": "./vscode-client/out/extension",
        "scripts": {
            "vscode:prepublish": "cd vscode-client && npm run compile && cd ..",
            "compile": "cd vscode-client && tsc -p ./ && cd ..",
            "watch": "cd vscode-client && tsc -watch -p ./ && cd ..",
            "postinstall": "node ./node_modules/vscode/bin/install",
        },
        "devDependencies": {
            "typescript": "^3.8.2",
            "vscode": "^1.1.37",
            "@types/node": "^10.0.0",
            "@types/mocha": "^2.2.32",
        },
        "dependencies": {
            "vscode-languageclient": "^6.1.3",
            "path-exists": "^4.0.0",
            "http-proxy-agent": "^2.1.0",
            "https-proxy-agent": "^2.2.4",
            "vscode-nls": "^4.1.2",
        },
    }
    return base_package_contents


def write_to_package_json():
    import json

    json_contents = get_json_contents()
    as_str = json.dumps(json_contents, indent=4)
    root = os.path.dirname(os.path.dirname(__file__))
    package_json_location = os.path.join(root, "package.json")
    with open(package_json_location, "w") as stream:
        stream.write(as_str)
    print("Written: %s" % (package_json_location,))


root_dir = os.path.dirname(os.path.dirname(__file__))
vscode_js_client_src_dir = os.path.join(root_dir, "vscode-client", "src")
vscode_py_src_dir = os.path.join(root_dir, "src")


def write_js_commands():
    commands_ts_file = os.path.join(vscode_js_client_src_dir, "robocorpCommands.ts")

    command_constants = []

    for contributed_command in COMMANDS:
        command_id = contributed_command.name
        command_name = convert_case_to_constant(command_id)
        command_constants.append(
            'export const %s = "%s";  // %s'
            % (command_name, command_id, contributed_command.title)
        )

    with open(commands_ts_file, "w") as stream:
        stream.write(
            "// Warning: Don't edit file (autogenerated from python -m dev codegen).\n\n"
            + "\n".join(command_constants)
        )
    print("Written: %s" % (commands_ts_file,))


def write_py_commands():
    commands_py_file = os.path.join(vscode_py_src_dir, "robocorp_code", "commands.py")

    command_constants = []

    all_server_commands = []

    for contributed_command in COMMANDS:
        command_id = contributed_command.name
        command_name = convert_case_to_constant(command_id)
        command_constants.append(
            '%s = "%s"  # %s' % (command_name, command_id, contributed_command.title)
        )
        if contributed_command.server_handled:
            all_server_commands.append(command_name)

    with open(commands_py_file, "w") as stream:
        stream.write(
            "# Warning: Don't edit file (autogenerated from python -m dev codegen).\n\n"
            + "\n".join(command_constants)
        )

        stream.write("\n\nALL_SERVER_COMMANDS = [\n    ")
        stream.write(",\n    ".join(all_server_commands))
        stream.write(",\n]\n")
    print("Written: %s" % (commands_py_file,))


def write_py_settings():
    settings_py_file = os.path.join(vscode_py_src_dir, "robocorp_code", "settings.py")

    settings_template = [
        """# Warning: Don't edit file (autogenerated from python -m dev codegen).
"""
    ]

    setting_constant_template = '%s = "%s"'

    # Create the constants
    for setting in SETTINGS:
        # : :type setting: Setting
        settings_template.append(
            setting_constant_template
            % (convert_case_to_constant(setting.name), setting.name)
        )

    settings_template.append(
        """
ALL_ROBOCORP_OPTIONS = frozenset(
    ("""
    )

    for setting in SETTINGS:
        # : :type setting: Setting
        settings_template.append(f"        {convert_case_to_constant(setting.name)},")

    settings_template.append(
        """    )
)
"""
    )

    with open(settings_py_file, "w") as stream:
        stream.write("\n".join(settings_template))

    print("Written: %s" % (settings_py_file,))


def write_js_settings():
    settings_ts_file = os.path.join(vscode_js_client_src_dir, "robocorpSettings.ts")
    settings_template = [
        """// Warning: Don't edit file (autogenerated from python -m dev codegen).

import { WorkspaceConfiguration, workspace } from "vscode";

export function get<T>(key: string): T | undefined {
    var dot = key.lastIndexOf('.');
    var section = key.substring(0, dot);
    var name = key.substring(dot + 1);
    return workspace.getConfiguration(section).get(name);
}
"""
    ]

    setting_constant_template = 'export const %s = "%s";'

    # Create the constants
    for setting in SETTINGS:
        # : :type setting: Setting
        settings_template.append(
            setting_constant_template
            % (convert_case_to_constant(setting.name), setting.name)
        )

    getter_template = """
export function get%s(): %s {
    let key = %s;
    return get<%s>(key);
}
"""
    # Create the getters
    for setting in SETTINGS:
        js_type = setting.js_type or setting.setting_type
        if js_type == "array":
            raise AssertionError("Expected js_type for array.")
        name = "_".join(setting.name.split(".")[1:])
        name = name.title().replace(" ", "").replace("_", "").replace("-", "")
        settings_template.append(
            getter_template
            % (name, js_type, convert_case_to_constant(setting.name), js_type)
        )

    with open(settings_ts_file, "w") as stream:
        stream.write("\n".join(settings_template))

    print("Written: %s" % (settings_ts_file,))


def main():
    write_to_package_json()

    write_js_commands()
    write_js_settings()

    write_py_commands()
    write_py_settings()


if __name__ == "__main__":
    main()
