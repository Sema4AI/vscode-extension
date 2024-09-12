from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


@dataclass
class ActionPackageInFilesystem:
    relative_path: str

    package_yaml_path: Optional[Path] = None
    zip_path: Optional[Path] = None
    package_yaml_contents: Optional[str] = None

    _loaded_yaml: Optional[dict] = None
    _loaded_yaml_error: Optional[str] = None

    referenced_from_agent_spec: bool = False

    def __post_init__(self) -> None:
        if self.zip_path is None:
            assert (
                self.package_yaml_path is not None
            ), "When the zip path is not provided, package_yaml_path is expected to be provided."
        else:
            assert (
                self.package_yaml_path is None
            ), "When zip path is provided, package_yaml_path is not expected."

    def is_zip(self) -> bool:
        return self.zip_path is not None

    def get_as_dict(self) -> dict:
        if self._loaded_yaml is not None:
            return self._loaded_yaml

        if self._loaded_yaml_error is not None:
            raise RuntimeError(self._loaded_yaml_error)

        import yaml

        try:
            if self.is_zip() and self.package_yaml_contents is None:
                raise RuntimeError(
                    "It was not possible to load the agent-spec.yaml from the referenced .zip file."
                )
            if self.package_yaml_contents is not None:
                contents = yaml.safe_load(self.package_yaml_contents)
            else:
                if self.package_yaml_path is None:
                    raise RuntimeError(
                        "Internal error. Either package_yaml_path or package_yaml_contents must be provided"
                    )
                with self.package_yaml_path.open("r") as stream:
                    contents = yaml.safe_load(stream)

            if not isinstance(contents, dict):
                raise RuntimeError("Unable to get contents as dict.")

            self._loaded_yaml = contents
            return self._loaded_yaml
        except Exception as e:
            if self.is_zip():
                log.error(
                    f"Error getting agent-spec.yaml from {self.zip_path} as yaml."
                )
            else:
                log.error(f"Error getting {self.package_yaml_path} as yaml.")

            self._loaded_yaml_error = str(e)
            raise

    def get_version(self) -> str:
        try:
            contents = self.get_as_dict()
        except Exception as e:
            return str(e)

        return str(contents.get("version", "Unable to get version from package.yaml"))

    def get_name(self) -> str:
        try:
            contents = self.get_as_dict()
        except Exception as e:
            return str(e)

        return str(contents.get("name", "Unable to get name from package.yaml"))


def list_actions_from_agent(
    agent_root_dir: Path,
) -> dict[Path, ActionPackageInFilesystem]:
    """
    Helper function to list the action packages from a given agent.

    Args:
        agent_root_dir: This is the agent root directory (i.e.: the directory containing the `agent-spec.yaml`).

    Returns:
        A dictionary where the key is the Path to the action package.yaml or the .zip (if zipped) and the value
        is an object with information about the action package.
    """
    found: dict[Path, ActionPackageInFilesystem] = {}
    actions_dir: Path = (agent_root_dir / "actions").absolute()
    if actions_dir.exists():
        for package_yaml in actions_dir.rglob("package.yaml"):
            package_yaml = package_yaml.absolute()
            relative_path: str = package_yaml.parent.relative_to(actions_dir).as_posix()
            found[package_yaml] = ActionPackageInFilesystem(
                package_yaml_path=package_yaml, relative_path=relative_path
            )

        for zip_path in actions_dir.rglob("*.zip"):
            zip_path = zip_path.absolute()
            package_yaml_contents = get_package_yaml_from_zip(zip_path)
            relative_path = zip_path.relative_to(actions_dir).as_posix()
            found[zip_path] = ActionPackageInFilesystem(
                package_yaml_path=None,
                zip_path=zip_path,
                package_yaml_contents=package_yaml_contents,
                relative_path=relative_path,
            )

    return found


def get_package_yaml_from_zip(zip_path: Path) -> Optional[str]:
    """
    Provides the contents of the package.yaml in the zip or None if it
    couldn't be found.

    Args:
        zip_path: The path to the zip.

    Returns:
        string with the package.yaml contents from the zip or None if
        it couldn't be gotten.
    """
    import zipfile

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            with zip_ref.open("package.yaml") as file:
                content = file.read()
                decoded = content.decode("utf-8")
                return decoded
    except Exception:
        return None
