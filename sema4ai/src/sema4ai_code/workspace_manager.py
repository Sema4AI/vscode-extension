import os
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from pprint import pformat
from typing import Dict, List, Optional, Tuple

from sema4ai_ls_core.cache import CachedFileInfo
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import IWorkspace

from sema4ai_code.agent_cli import get_agent_package_actions_sub_directory
from sema4ai_code.protocols import (
    LocalAgentPackageOrganizationInfoDict,
    LocalPackageMetadataInfoDict,
    PackageType,
    PackageYamlName,
)

log = get_logger(__name__)


class WorkspaceManager:
    """
    An entity responsible for workspace-specific operations, like workspace filesystem traversal.
    """

    def __init__(self, workspace: IWorkspace | None) -> None:
        self.workspace = workspace

        self._local_list_robots_cache: Dict[
            Path, CachedFileInfo[LocalPackageMetadataInfoDict]
        ] = {}

        self._local_list_agent_packages_cache: Dict[
            Path, CachedFileInfo[LocalPackageMetadataInfoDict]
        ] = {}

    def get_local_robots(self) -> List[LocalPackageMetadataInfoDict]:
        """
        Returns all local Robot/Action packages present in the workspace, either at root or first level.
        Ignores Agent packages.
        """
        curr_cache = self._local_list_robots_cache
        new_cache: Dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]] = {}

        robots: List[LocalPackageMetadataInfoDict] = []
        try:
            ws = self.workspace
            if ws:
                for folder_path in ws.get_folder_paths():
                    # Check the root directory itself for the robot.yaml.
                    p = Path(folder_path)
                    robot_metadata = self._get_package_metadata(
                        [
                            PackageYamlName.ROBOT,
                            PackageYamlName.ACTION,
                            PackageYamlName.AGENT,
                        ],
                        p,
                        curr_cache,
                        new_cache,
                    )

                    if robot_metadata is not None:
                        robots.append(robot_metadata)
                    elif p.is_dir():
                        for sub in p.iterdir():
                            robot_metadata = self._get_package_metadata(
                                [
                                    PackageYamlName.ROBOT,
                                    PackageYamlName.ACTION,
                                    PackageYamlName.AGENT,
                                ],
                                sub,
                                curr_cache,
                                new_cache,
                            )
                            if robot_metadata is not None:
                                robots.append(robot_metadata)

            def get_key(dct):
                package_type = dct["packageType"]
                priority = 2
                if package_type == PackageType.AGENT.value:
                    priority = 0
                elif package_type == PackageType.ACTION.value:
                    priority = 1
                return priority, dct["name"].lower()

            robots.sort(key=get_key)

            for package in robots:
                if package["packageType"] == PackageType.AGENT.value:
                    package["organizations"] = self._get_agent_package_organizations(
                        package["directory"],
                        new_cache,
                    )

        finally:
            # Set the new cache after we finished computing all entries.
            self._local_list_robots_cache = new_cache

        return robots

    def _get_agent_package_organizations(
        self,
        actions_directory: str,
        new_cache: Dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]],
    ) -> List[LocalAgentPackageOrganizationInfoDict]:
        curr_cache = self._local_list_agent_packages_cache

        actions_path = (
            Path(actions_directory) / get_agent_package_actions_sub_directory()
        )

        organizations: List[LocalAgentPackageOrganizationInfoDict] = []

        if not actions_path.is_dir():
            return []

        for org_directory in actions_path.iterdir():
            if not org_directory.is_dir():
                continue

            action_packages: Dict[List[Tuple[str, LocalPackageMetadataInfoDict]]] = (
                defaultdict(list)
            )

            # Organization name is the name of the directory the Action Package exists in.
            organization_name = os.path.basename(org_directory)

            organization = {
                "name": organization_name,
                "actionPackages": [],
            }

            for action_package_metadata in self._get_action_package_from_dir(
                org_directory, curr_cache, new_cache
            ):
                log.info(
                    f"[metadata] {action_package_metadata}",
                )

                action_packages[action_package_metadata["name"]].append(
                    (
                        action_package_metadata["yamlContents"]["version"],
                        action_package_metadata,
                    )
                )

            for action_name, action_versions in action_packages.items():
                if len(action_versions) == 1:
                    organization["actionPackages"].append(action_versions[0][1])
                else:
                    for version_number, action_package in action_versions:
                        action_package["name"] = (
                            f"{action_package['name']}/v{version_number}"
                        )

                        organization["actionPackages"].append(action_package)
                        log.info(f"[debug 2] {action_package}")

            organizations.append(organization)
            log.info(f"[organizations] {pformat(organizations)}")

        return organizations

    def _get_action_package_from_dir(
        self, directory: Path, current_cache, new_cache
    ) -> Iterator[LocalPackageMetadataInfoDict]:
        for sub_directory in directory.iterdir():
            if sub_directory.is_dir():
                yield from self._get_action_package_from_dir(
                    sub_directory, current_cache, new_cache
                )

        if action_package_metadata := self._get_package_metadata(
            [PackageYamlName.ACTION], directory, current_cache, new_cache
        ):
            yield action_package_metadata

        # if action_package_metadata is not None:
        #     organization["actionPackages"].append(action_package_metadata)

    def _get_package_metadata(
        self,
        yaml_file_names: list[PackageYamlName],
        sub: Path,
        curr_cache: Dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]],
        new_cache: Dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]],
    ) -> Optional[LocalPackageMetadataInfoDict]:
        """
        Note that we get the value from the current cache and then put it in
        the new cache if it's still valid (that way we don't have to mutate
        the old cache to remove stale values... all that's valid is put in
        the new cache).
        """

        cached_file_info: Optional[CachedFileInfo[LocalPackageMetadataInfoDict]] = (
            curr_cache.get(sub)
        )
        if cached_file_info is not None:
            if cached_file_info.is_cache_valid():
                new_cache[sub] = cached_file_info
                return cached_file_info.value

        for package_yaml_name in yaml_file_names:
            yaml_file = sub / package_yaml_name.value

            if yaml_file.exists():
                from sema4ai_ls_core import yaml_wrapper

                try:

                    def get_package_metadata(yaml_file_path: Path):
                        with yaml_file_path.open("r", encoding="utf-8") as stream:
                            yaml_contents = yaml_wrapper.load(stream)

                        name = yaml_contents.get("name", yaml_file_path.parent.name)
                        if package_yaml_name == PackageYamlName.AGENT:
                            try:
                                name = yaml_contents["agent-package"]["agents"][0][
                                    "name"
                                ]
                            except Exception:
                                pass

                        robot_metadata: LocalPackageMetadataInfoDict = {
                            "packageType": self._package_type_by_package_yaml_name(
                                package_yaml_name
                            ),
                            "directory": str(sub),
                            "filePath": str(yaml_file_path),
                            "name": name,
                            "yamlContents": yaml_contents,
                        }

                        return robot_metadata

                    cached_file_info = new_cache[sub] = CachedFileInfo(
                        yaml_file, get_package_metadata
                    )
                    return cached_file_info.value

                except Exception:
                    log.exception(f"Unable to get load metadata for: {yaml_file}")

        return None

    def _package_type_by_package_yaml_name(
        self, package_yaml_name: PackageYamlName
    ) -> str:
        if package_yaml_name == PackageYamlName.AGENT:
            return PackageType.AGENT.value
        if package_yaml_name == PackageYamlName.ACTION:
            return PackageType.ACTION.value
        if package_yaml_name == PackageYamlName.ROBOT:
            return PackageType.TASK.value

        return ""
