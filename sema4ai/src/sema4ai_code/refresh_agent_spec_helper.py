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
        if not whitelisted_action.pop("seen", False):
            new_action_packages.append(whitelisted_action)

    agent_spec["agent-package"]["agents"][0]["action-packages"] = new_action_packages


def _create_whitelist_mapping(agent_spec: dict) -> dict[str, ActionPackage]:
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


def update_agent_spec(agent_spec_path: Path) -> None:
    from ruamel.yaml import YAML

    from sema4ai_code.agents.list_actions_from_agent import list_actions_from_agent

    yaml = YAML()
    yaml.preserve_quotes = True

    with agent_spec_path.open("r") as file:
        agent_spec = yaml.load(file)

    action_packages_in_filesystem = list(
        list_actions_from_agent(agent_spec_path.parent).values()
    )
    current_whitelist_mapping = _create_whitelist_mapping(agent_spec)

    _update_agent_spec_with_actions(
        agent_spec, action_packages_in_filesystem, current_whitelist_mapping
    )

    with agent_spec_path.open("w") as file:
        yaml.dump(agent_spec, file)
