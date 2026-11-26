from pathlib import Path

from sema4ai_ls_core.cache import CachedFileInfo
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import IWorkspace

from sema4ai_code.protocols import (
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

        self._local_list_robots_cache: dict[
            Path, CachedFileInfo[LocalPackageMetadataInfoDict]
        ] = {}

    def get_local_robots(self) -> list[LocalPackageMetadataInfoDict]:
        """
        Returns all local Task Packages (robot.yaml) present in the workspace, either at root or first level.
        """
        curr_cache = self._local_list_robots_cache
        new_cache: dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]] = {}

        robots: list[LocalPackageMetadataInfoDict] = []
        try:
            ws = self.workspace
            if ws:
                for folder_path in ws.get_folder_paths():
                    # Check the root directory itself for the robot.yaml.
                    p = Path(folder_path)
                    robot_metadata = self._get_package_metadata(
                        p, curr_cache, new_cache
                    )

                    if robot_metadata is not None:
                        robots.append(robot_metadata)
                    elif p.is_dir():
                        for sub in p.iterdir():
                            robot_metadata = self._get_package_metadata(
                                sub, curr_cache, new_cache
                            )
                            if robot_metadata is not None:
                                robots.append(robot_metadata)

            robots.sort(key=lambda dct: dct["name"].lower())

        finally:
            # Set the new cache after we finished computing all entries.
            self._local_list_robots_cache = new_cache

        return robots

    def _get_package_metadata(
        self,
        sub: Path,
        curr_cache: dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]],
        new_cache: dict[Path, CachedFileInfo[LocalPackageMetadataInfoDict]],
    ) -> LocalPackageMetadataInfoDict | None:
        """
        Note that we get the value from the current cache and then put it in
        the new cache if it's still valid (that way we don't have to mutate
        the old cache to remove stale values... all that's valid is put in
        the new cache).
        """

        cached_file_info: CachedFileInfo[LocalPackageMetadataInfoDict] | None = (
            curr_cache.get(sub)
        )
        if cached_file_info is not None:
            if cached_file_info.is_cache_valid():
                new_cache[sub] = cached_file_info
                return cached_file_info.value

        yaml_file = sub / PackageYamlName.ROBOT.value

        if yaml_file.exists():
            from sema4ai_ls_core import yaml_wrapper

            try:

                def get_package_metadata(yaml_file_path: Path):
                    with yaml_file_path.open("r", encoding="utf-8") as stream:
                        yaml_contents = yaml_wrapper.load(stream)

                    name = yaml_contents.get("name", yaml_file_path.parent.name)

                    robot_metadata: LocalPackageMetadataInfoDict = {
                        "packageType": PackageType.TASK.value,
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
