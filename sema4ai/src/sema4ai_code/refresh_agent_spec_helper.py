import typing
from pathlib import Path
from typing import TypedDict

if typing.TYPE_CHECKING:
    from sema4ai_code.agents.list_actions_from_agent import ActionPackageInFilesystem

SEMA4AI = "sema4ai"


class ActionPackage(TypedDict, total=False):
    name: str | None
    organization: str
    type: str
    version: str | None
    whitelist: str
    path: str
    seen: bool


def _update_whitelist(
    action_package: ActionPackage,
    whitelist_map: dict[str, ActionPackage],
    match_key: str,
) -> bool:
    found_package = whitelist_map.get(match_key)

    if found_package and not found_package.get("seen"):
        action_package["whitelist"] = found_package["whitelist"]
        found_package["seen"] = True
        return True

    return False


def _update_agent_spec_with_actions(
    agent_spec: dict,
    action_packages_in_filesystem: list["ActionPackageInFilesystem"],
    whitelist_map: dict[str, ActionPackage],
) -> None:
    new_action_packages: list[ActionPackage] = [
        {
            "name": action_package.get_name(),
            "organization": action_package.organization,
            "version": action_package.get_version(),
            "path": action_package.relative_path,
            "type": "zip" if action_package.zip_path else "folder",
            "whitelist": "",
        }
        for action_package in action_packages_in_filesystem
        if action_package.organization.replace(".", "").lower() != SEMA4AI
    ]

    missing = []

    # First try to match by path.
    for action_package in new_action_packages:
        if not _update_whitelist(
            action_package,
            whitelist_map,
            match_key=action_package["path"],
        ):
            missing.append(action_package)

    # Couldn't find a path match, try to match by name.
    for action_package in missing:
        if action_package["name"]:
            _update_whitelist(
                action_package, whitelist_map, match_key=action_package["name"]
            )

    # If there was a whitelisted action and it wasn't matched, keep the old config
    # around so that the user can fix it.
    for whitelisted_action in whitelist_map.values():
        if not whitelisted_action.get("seen"):
            new_action_packages.append(whitelisted_action)
            whitelisted_action["seen"] = True

    for action in new_action_packages:
        action.pop("seen", None)

    agent_spec["agent-package"]["agents"][0]["action-packages"] = new_action_packages


def _get_whitelist_mapping(agent_spec: dict) -> dict[str, ActionPackage]:
    whitelist_mapping = {}

    for action_package in agent_spec["agent-package"]["agents"][0].get(
        "action-packages", []
    ):
        if action_package.get("whitelist"):
            if action_package.get("name"):
                whitelist_mapping[action_package["name"]] = action_package

            if action_package.get("path"):
                whitelist_mapping[action_package["path"]] = action_package

    return whitelist_mapping


def _fix_agent_spec(agent_spec: dict) -> None:
    """Updates the provided agent-spec configuration with default values
    where missing, ensuring the structure conforms to the expected format.

    The function compares the `agent_spec` dictionary against a predefined
    `default_spec` structure. For each key in `default_spec`, if the key is
    missing in `agent_spec`, it is added. If the key exists but contains a
    nested dictionary, the function recursively ensures that all default keys
    and values are present within the nested structure.
    """
    default_spec = {
        "agent-package": {
            "spec-version": "v2",
            "agents": [
                {
                    "name": "My Agent",
                    "description": "My Agent description",
                    "model": {"provider": "OpenAI", "name": "gpt-4o"},
                    "version": "0.0.1",
                    "architecture": "agent",
                    "reasoning": "disabled",
                    "runbook": "runbook.md",
                    "action-packages": [],
                    "knowledge": [],
                    "metadata": {"mode": "conversational"},
                }
            ],
        }
    }

    def recursive_update(original: dict, defaults: dict) -> dict:
        for key, value in defaults.items():
            if key not in original:
                original[key] = value
            elif isinstance(value, dict) and isinstance(original.get(key), dict):
                recursive_update(original[key], value)
            elif key == "agents":
                if not isinstance(original[key], list) or len(original[key]) == 0:
                    original[key] = [{}]
                recursive_update(original[key][0], value[0])

        return original

    recursive_update(agent_spec, default_spec)


def update_agent_spec(agent_spec_path: Path) -> None:
    from ruamel.yaml import YAML

    from sema4ai_code.agents.list_actions_from_agent import list_actions_from_agent

    yaml = YAML()
    yaml.preserve_quotes = True

    with agent_spec_path.open("r") as file:
        agent_spec = yaml.load(file)

    _fix_agent_spec(agent_spec)

    action_packages_in_filesystem = list(
        list_actions_from_agent(agent_spec_path.parent).values()
    )
    current_whitelist_map = _get_whitelist_mapping(agent_spec)

    _update_agent_spec_with_actions(
        agent_spec,
        action_packages_in_filesystem,
        current_whitelist_map,
    )

    with agent_spec_path.open("w") as file:
        yaml.dump(agent_spec, file)
