import os
from pathlib import Path
from typing import Dict, List, Optional, cast

from sema4ai_ls_core.protocols import IWorkspace
from sema4ai_ls_core.cache import CachedFileInfo
from sema4ai_ls_core.core_log import get_logger

from sema4ai_code.protocols import (
    PackageType,
    PackageYamlName,
    LocalPackageMetadataInfoDict,
    LocalAgentPackageMetadataInfoDict,
    LocalAgentPackageOrganizationInfoDict,
)

from sema4ai_code.agent_cli import get_agent_package_actions_sub_directory

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
                        [PackageYamlName.ROBOT, PackageYamlName.ACTION],
                        p,
                        curr_cache,
                        new_cache,
                    )

                    if robot_metadata is not None:
                        robots.append(robot_metadata)
                    elif p.is_dir():
                        for sub in p.iterdir():
                            robot_metadata = self._get_package_metadata(
                                [PackageYamlName.ROBOT, PackageYamlName.ACTION],
                                sub,
                                curr_cache,
                                new_cache,
                            )
                            if robot_metadata is not None:
                                robots.append(robot_metadata)

            robots.sort(key=lambda dct: dct["name"])
        except Exception as e:
            # We use try-except, so we can update the cache in "finally" block - therefore
            # we simply rethrow on exception.
            raise e
        finally:
            # Set the new cache after we finished computing all entries.
            self._local_list_robots_cache = new_cache

        return robots

    def get_local_agent_packages(self) -> List[LocalAgentPackageMetadataInfoDict]:
        """
        Returns all local Agent packages present in the workspace, either at root or first level.
        Ignores Robot/Action packages.
        """
        curr_cache = self._local_list_agent_packages_cache
        # We don't need additional information that come with LocalAgentPackageMetadataInfoDict in cache,
        # therefore we use the base class.
        new_cache: Dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]] = {}

        agent_packages: List[LocalAgentPackageMetadataInfoDict] = []

        def append_if_exists(base_metadata: LocalPackageMetadataInfoDict | None):
            if base_metadata is not None:
                agent_package_metadata = cast(
                    LocalAgentPackageMetadataInfoDict,
                    {**base_metadata, "organizations": []},
                )

                agent_packages.append(agent_package_metadata)

        try:
            ws = self.workspace
            if ws:
                for folder_path in ws.get_folder_paths():
                    # Check the root directory itself for the agent-spec.yaml.
                    p = Path(folder_path)

                    base_agent_package_metadata = self._get_package_metadata(
                        [PackageYamlName.AGENT],
                        p,
                        curr_cache,
                        new_cache,
                    )

                    append_if_exists(base_agent_package_metadata)

                    if base_agent_package_metadata is None and p.is_dir():
                        for sub in p.iterdir():
                            base_agent_package_metadata = self._get_package_metadata(
                                [PackageYamlName.AGENT],
                                sub,
                                curr_cache,
                                new_cache,
                            )

                            append_if_exists(base_agent_package_metadata)

            for agent_package in agent_packages:
                agent_package["organizations"] = self._get_agent_package_organizations(
                    agent_package["directory"],
                    new_cache,
                )

            agent_packages.sort(key=lambda dct: dct["name"])
        except Exception as e:
            # We use try-except, so we can update the cache in "finally" block - therefore
            # we simply rethrow on exception.
            raise e
        finally:
            # Set the new cache after we finished computing all entries.
            self._local_list_agent_packages_cache = new_cache

        return agent_packages

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

            # Organization name is the name of the directory the Action Package exists in.
            organization_name = os.path.basename(org_directory)
            organization: LocalAgentPackageOrganizationInfoDict = {
                "name": organization_name,
                "actionPackages": [],
            }

            for sub in org_directory.iterdir():
                action_package_metadata = self._get_package_metadata(
                    [PackageYamlName.ACTION], sub, curr_cache, new_cache
                )

                if action_package_metadata is not None:
                    action_package_metadata["organization"] = organization_name
                    organization["actionPackages"].append(action_package_metadata)

            organizations.append(organization)

        return organizations

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

        cached_file_info: Optional[
            CachedFileInfo[LocalPackageMetadataInfoDict]
        ] = curr_cache.get(sub)
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
                        name = yaml_file_path.parent.name

                        with yaml_file_path.open("r", encoding="utf-8") as stream:
                            yaml_contents = yaml_wrapper.load(stream)

                            # Agent Packages do not have names defined in the YAML file,
                            # therefore we use directory name.
                            name = (
                                os.path.basename(sub)
                                if package_yaml_name == PackageYamlName.AGENT
                                else yaml_contents.get("name", name)
                            )

                        robot_metadata: LocalPackageMetadataInfoDict = {
                            "packageType": self._package_type_by_package_yaml_name(
                                package_yaml_name
                            ),
                            "directory": str(sub),
                            "filePath": str(yaml_file_path),
                            "name": name,
                            "yamlContents": yaml_contents,
                            "organization": None,
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
