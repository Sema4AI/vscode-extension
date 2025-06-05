"""
Note: this code will actually run as a plugin in the RobotFramework Language
Server, or in the Sema4.ai environment, so, we need to be careful on the
imports so that it works on both cases.

Also, the required version must be checked in the client (in case imports or APIs
change in `sema4ai_ls_core` we need a compatible version both on robotframework-ls
as well as sema4ai).
"""

import itertools
import os.path
import sys
import time
import typing
import weakref
from collections import namedtuple
from pathlib import Path
from typing import Optional

from sema4ai_ls_core import uris
from sema4ai_ls_core.basic import implements
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.ep_resolve_interpreter import (
    DefaultInterpreterInfo,
    EPResolveInterpreter,
    IInterpreterInfo,
)
from sema4ai_ls_core.lsp import LSPMessages
from sema4ai_ls_core.pluginmanager import PluginManager
from sema4ai_ls_core.progress_report import (
    get_current_progress_reporter,
    progress_context,
)
from sema4ai_ls_core.protocols import IEndPoint, check_implements

from sema4ai_code.protocols import IRobotYamlEnvInfo
from sema4ai_code.rcc import Rcc

if typing.TYPE_CHECKING:
    from sema4ai_ls_core.ep_providers import EPConfigurationProvider, EPEndPointProvider

log = get_logger(__name__)

_CachedFileMTimeInfo = namedtuple("_CachedFileMTimeInfo", "st_mtime, st_size, path")

_CachedInterpreterMTime = tuple[Optional[_CachedFileMTimeInfo], ...]


def _get_mtime_cache_info(file_path: Path) -> _CachedFileMTimeInfo | None:
    """
    Cache based on the time/size of a given path.
    """
    try:
        stat = file_path.stat()
        return _CachedFileMTimeInfo(stat.st_mtime, stat.st_size, str(file_path))
    except Exception:
        # It could be removed in the meanwhile.
        log.exception(f"Unable to get mtime info for: {file_path}")
        return None


class _CachedFileInfo:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.mtime_info: _CachedFileMTimeInfo | None = _get_mtime_cache_info(file_path)
        self.contents: str = file_path.read_text(encoding="utf-8", errors="replace")
        self._yaml_contents: dict | None = None

    @property
    def yaml_contents(self) -> dict:
        yaml_contents = self._yaml_contents
        if yaml_contents is None:
            from io import StringIO

            try:
                from sema4ai_ls_core import yaml_wrapper
            except ImportError:
                from robocorp_ls_core import yaml_wrapper  # type: ignore

            s = StringIO(self.contents)
            yaml_contents = self._yaml_contents = yaml_wrapper.load(s)
        return yaml_contents

    def is_cache_valid(self) -> bool:
        return self.mtime_info == _get_mtime_cache_info(self.file_path)


class _CachedInterpreterInfo:
    def __init__(
        self,
        robot_yaml_file_info: _CachedFileInfo | None,
        conda_or_package_file_info: _CachedFileInfo,
        env_json_path_file_info: _CachedFileInfo | None,
        pm: PluginManager,
    ):
        from sema4ai_code.commands import SEMA4AI_SHOW_INTERPRETER_ENV_ERROR

        self._mtime: _CachedInterpreterMTime = self._obtain_mtime(
            robot_yaml_file_info, conda_or_package_file_info, env_json_path_file_info
        )

        configuration_provider: "EPConfigurationProvider" = pm[
            "EPConfigurationProvider"
        ]
        endpoint_provider: "EPEndPointProvider" = pm["EPEndPointProvider"]
        rcc = Rcc(configuration_provider)

        if robot_yaml_file_info is not None:
            interpreter_id = str(robot_yaml_file_info.file_path)
        else:
            interpreter_id = str(conda_or_package_file_info.file_path)

        progress_reporter = get_current_progress_reporter()

        def on_env_creation_error(result) -> None:
            import tempfile

            # Note: called only on environment creation (not on all failures).
            endpoint: IEndPoint = endpoint_provider.endpoint
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".log", prefix="sema4ai_code_env_error_"
            ) as f:
                if progress_reporter is not None and progress_reporter.cancelled:
                    file_contents = f"""
Sema4.ai: Environment creation cancelled
===============================================

The process to create the the environment for:

"{conda_or_package_file_info.file_path}"

was cancelled.

In this case, open "{conda_or_package_file_info.file_path}"
and update the dependencies accordingly (after saving
the environment will be automatically updated).

If the environment file should be already correct, chose one of the options below:

- Retry restarting VSCode using the command:

  "Developer: Reload Window"

- Clear all environments and restart Sema4.ai (advised if you suspect
  that some environment was partially created and is corrupt):

  "Sema4.ai: Clear Sema4.ai (RCC) environments and restart Sema4.ai"

Full error message
====================

{result.message}
"""

                else:
                    file_contents = f"""
Sema4.ai: Unable to create environment
=============================================

There was an error creating the environment for:

"{conda_or_package_file_info.file_path}"

The full output to diagnose the issue is shown below.
The most common reasons and fixes for this failure are:

1. Dependencies specified are not resolvable.

    In this case, open "{conda_or_package_file_info.file_path}"
    and update the dependencies accordingly (after saving
    the environment will be automatically updated).

2. There's some intermittent network failure or some active firewall.

    In this case, fix the network connectivity issue and chose one of the options below:

    - Retry restarting VSCode using the command:

      "Developer: Reload Window"

    - Clear all environments and restart Sema4.ai code (advised if you suspect
      that some environment was partially created and is corrupt):

      "Sema4.ai: Clear Sema4.ai (RCC) environments and restart Sema4.ai"

If you still can't get it to work, please submit an issue to Sema4.ai using the command:

  "Sema4.ai: Submit issue to Sema4.ai".


Full error message
====================

{result.message}
"""
                f.write(file_contents.encode("utf-8"))
                message = result.message
                if message:
                    f.write(message.encode("utf-8"))

            lsp_messages = LSPMessages(endpoint)
            lsp_messages.execute_workspace_command(
                SEMA4AI_SHOW_INTERPRETER_ENV_ERROR,
                {
                    "fileWithError": str(f.name),
                    "condaYaml": str(conda_or_package_file_info.file_path),
                },
            )

        result = rcc.get_robot_yaml_env_info(
            robot_yaml_file_info.file_path if robot_yaml_file_info else None,
            conda_or_package_file_info.file_path,
            conda_or_package_file_info.contents,
            env_json_path_file_info.file_path
            if env_json_path_file_info is not None
            else None,
            on_env_creation_error=on_env_creation_error,
        )
        if not result.success:
            raise RuntimeError(f"Unable to get env details. Error: {result.message}.")

        robot_yaml_env_info: IRobotYamlEnvInfo | None = result.result
        if robot_yaml_env_info is None:
            raise RuntimeError(f"Unable to get env details. Error: {result.message}.")

        environ = robot_yaml_env_info.env

        root = (
            str(robot_yaml_file_info.file_path.parent)
            if robot_yaml_file_info is not None
            else str(conda_or_package_file_info.file_path.parent)
        )

        pythonpath_lst: list[str]

        if robot_yaml_file_info is not None:
            pythonpath_lst = robot_yaml_file_info.yaml_contents.get("PYTHONPATH", [])
        else:
            pythonpath_lst = conda_or_package_file_info.yaml_contents.get(
                "pythonpath", []
            )

        additional_pythonpath_entries: list[str] = []
        if isinstance(pythonpath_lst, list):
            for v in pythonpath_lst:
                v = str(v)
                if os.path.isabs(v):
                    additional_pythonpath_entries.append(v)
                else:
                    additional_pythonpath_entries.append(os.path.join(root, v))
        else:
            log.critical(
                f"Expected PYTHONPATH to be a list. Found: {pythonpath_lst}. In: {interpreter_id}"
            )

        self.robot_yaml_env_info: IRobotYamlEnvInfo = robot_yaml_env_info
        self.info: IInterpreterInfo = DefaultInterpreterInfo(
            interpreter_id,
            environ["PYTHON_EXE"],
            environ,
            additional_pythonpath_entries,
        )

    def _obtain_mtime(
        self,
        robot_yaml_file_info: _CachedFileInfo | None,
        conda_or_package_file_info: _CachedFileInfo | None,
        env_json_path_file_info: _CachedFileInfo | None,
    ) -> _CachedInterpreterMTime:
        assert (
            robot_yaml_file_info is not None or conda_or_package_file_info is not None
        ), (
            "Either the robot.yaml or conda.yaml/package.yaml must not be None at this point"
        )
        return (
            robot_yaml_file_info.mtime_info if robot_yaml_file_info else None,
            conda_or_package_file_info.mtime_info
            if conda_or_package_file_info
            else None,
            env_json_path_file_info.mtime_info if env_json_path_file_info else None,
        )

    def is_cache_valid(
        self,
        robot_yaml_file_info: _CachedFileInfo | None,
        conda_or_package_file_info: _CachedFileInfo | None,
        env_json_path_file_info: _CachedFileInfo | None,
    ) -> bool:
        return self._mtime == self._obtain_mtime(
            robot_yaml_file_info, conda_or_package_file_info, env_json_path_file_info
        )


class _CacheInfo:
    """
    As a new instance of the RobocorpResolveInterpreter is created for each call,
    we need to store cached info outside it.
    """

    _cached_file_info: dict[Path, _CachedFileInfo] = {}
    _cached_interpreter_info: dict[Path, _CachedInterpreterInfo] = {}
    _cache_hit_files = 0  # Just for testing
    _cache_hit_interpreter = 0  # Just for testing

    @classmethod
    def clear_cache(cls):
        cls._cached_file_info.clear()
        cls._cached_interpreter_info.clear()
        cls._cache_hit_files = 0  # Just for testing
        cls._cache_hit_interpreter = 0  # Just for testing

    @classmethod
    def get_file_info(cls, file_path: Path) -> _CachedFileInfo:
        file_info = cls._cached_file_info.get(file_path)
        if file_info is not None and file_info.is_cache_valid():
            cls._cache_hit_files += 1
            return file_info

        # If it got here, it's not cached or the cache doesn't match.
        file_info = _CachedFileInfo(file_path)
        cls._cached_file_info[file_path] = file_info
        return file_info

    @classmethod
    def get_interpreter_info(
        cls,
        robot_yaml_file_info: _CachedFileInfo | None,
        conda_or_package_file_info: _CachedFileInfo,
        env_json_path_file_info: _CachedFileInfo | None,
        pm: PluginManager,
    ) -> IInterpreterInfo:
        interpreter_info: _CachedInterpreterInfo | None
        if robot_yaml_file_info is not None:
            interpreter_info = cls._cached_interpreter_info.get(
                robot_yaml_file_info.file_path
            )
        elif conda_or_package_file_info is not None:
            interpreter_info = cls._cached_interpreter_info.get(
                conda_or_package_file_info.file_path
            )
        else:
            raise AssertionError(
                "Either the robot.yaml or conda.yaml/package.yaml must not be None at this point"
            )

        if interpreter_info is not None and interpreter_info.is_cache_valid(
            robot_yaml_file_info, conda_or_package_file_info, env_json_path_file_info
        ):
            space_info = interpreter_info.robot_yaml_env_info.space_info
            environ = interpreter_info.info.get_environ()
            if environ is not None:
                ok = True
                conda_prefix = environ.get("CONDA_PREFIX")
                if conda_prefix is None:
                    log.critical(
                        f"Expected CONDA_PREFIX to be available in the environ. Found: {environ}."
                    )
                    ok = False
                else:
                    conda_id = Path(conda_prefix) / "identity.yaml"
                    space_info = interpreter_info.robot_yaml_env_info.space_info
                    if not space_info.matches_conda_identity_yaml(
                        Rcc(pm["EPConfigurationProvider"]), conda_id
                    ):
                        log.critical(
                            f"The conda contents in: {conda_id} no longer match the contents from {conda_or_package_file_info.file_path}."
                        )
                        ok = False

                if ok:
                    space_info.update_last_usage()
                    _CacheInfo._cache_hit_interpreter += 1
                    _touch_temp(interpreter_info.info)
                    return interpreter_info.info

        endpoint = pm["EPEndPointProvider"].endpoint

        if robot_yaml_file_info is not None:
            cache_path = robot_yaml_file_info.file_path
        else:
            cache_path = conda_or_package_file_info.file_path

        show_name = "/".join(Path(cache_path).parts[-3:])

        with progress_context(
            endpoint, f"Obtain env for {show_name}", dir_cache=None, cancellable=True
        ):
            # If it got here, it's not cached or the cache doesn't match.
            # This may take a while...
            interpreter_info = cls._cached_interpreter_info[cache_path] = (
                _CachedInterpreterInfo(
                    robot_yaml_file_info,
                    conda_or_package_file_info,
                    env_json_path_file_info,
                    pm,
                )
            )

            _touch_temp(interpreter_info.info)
            return interpreter_info.info


class _TouchInfo:
    def __init__(self):
        self._last_touch = 0

    def touch(self, info: IInterpreterInfo, force: bool = False):
        curr_time = time.time()
        diff = curr_time - self._last_touch

        one_hour_in_seconds = 60 * 60

        if diff > one_hour_in_seconds or force:  # i.e.: verify it at most once/hour.
            self._last_touch = curr_time
            environ = info.get_environ()
            if environ:
                temp_dir: str | None = environ.get("TEMP")
                if temp_dir:
                    temp_dir_path = Path(temp_dir)
                    try:
                        temp_dir_path.mkdir(exist_ok=True)
                    except Exception:
                        log.exception(f"Error making dir: {temp_dir_path}")

                    try:
                        recycle_path: Path = temp_dir_path / "recycle.now"
                        recycle_path.touch()
                    except Exception:
                        log.exception(f"Error touching: {recycle_path}")


def _touch_temp(info: IInterpreterInfo):
    # When reusing some space, account that the cached TEMP folder we have
    # may be removed and refresh its time accordingly.

    # Dynamically assign a _TouchInfo to this instance to manage doing the actual touch.
    touch_info = getattr(info, "__touch_info__", None)
    if touch_info is None:
        touch_info = _TouchInfo()
        setattr(info, "__touch_info__", touch_info)
    touch_info.touch(info)


class _PackageYamlCachedInfo:
    def __init__(
        self,
        robot_yaml: Path,
        conda_yaml: Path,
        package_yaml_file_info: _CachedFileInfo,
        cached_package_mtime_info: _CachedFileMTimeInfo | None,
        cached_package_contents: str | None,
    ):
        self.robot_yaml = robot_yaml
        self.conda_yaml = conda_yaml
        self.package_yaml_file_info: _CachedFileInfo = package_yaml_file_info
        self.cached_package_mtime_info = cached_package_mtime_info
        self.cached_package_contents = cached_package_contents

    def is_valid(self, package_yaml_file_info: _CachedFileInfo) -> bool:
        return (
            package_yaml_file_info.mtime_info == self.cached_package_mtime_info
            and package_yaml_file_info.contents == self.cached_package_contents
        )

    def get_cached(self) -> tuple[Path, Path]:
        return self.robot_yaml, self.conda_yaml


class RobocorpResolveInterpreter:
    """
    Resolves the interpreter based on the robot.yaml found.
    """

    def __init__(self, weak_pm: "weakref.ReferenceType[PluginManager]"):
        self._pm = weak_pm

    @implements(EPResolveInterpreter.get_interpreter_info_for_doc_uri)
    def get_interpreter_info_for_doc_uri(self, doc_uri) -> IInterpreterInfo | None:
        info = self._compute_base_interpreter_info_for_doc_uri(doc_uri)
        if info is None:
            return None
        return self._relocate_robot_root(info)

    def _relocate_robot_root(
        self, interpreter_info: IInterpreterInfo
    ) -> IInterpreterInfo | None:
        environ = interpreter_info.get_environ()
        if not environ:
            return interpreter_info

        robot_yaml = interpreter_info.get_interpreter_id()

        existing_robot_root = environ.get("ROBOT_ROOT")
        if existing_robot_root is None:
            return interpreter_info

        new_robot_root = self._fix_path(os.path.dirname(robot_yaml))
        existing_robot_root = self._fix_path(existing_robot_root)

        if new_robot_root.endswith(("/", "\\")):
            new_robot_root = new_robot_root[:-1]

        if existing_robot_root.endswith(("/", "\\")):
            existing_robot_root = existing_robot_root[:-1]

        fix_entry = self._fix_entry

        new_environ = {}
        for key, val in environ.items():
            new_environ[key] = os.pathsep.join(
                fix_entry(entry, existing_robot_root, new_robot_root)
                for entry in val.split(os.pathsep)
            )

        # Note: these should already be correct.
        # new_additional_pythonpath_entries: List[str] = []
        # for entry in interpreter_info.get_additional_pythonpath_entries():
        #     new_additional_pythonpath_entries.append(
        #         fix_entry(entry, existing_robot_root, new_robot_root)
        #     )

        return DefaultInterpreterInfo(
            robot_yaml,
            interpreter_info.get_python_exe(),
            new_environ,
            interpreter_info.get_additional_pythonpath_entries(),
        )

    @classmethod
    def _fix_entry(cls, entry: str, existing_robot_root: str, new_robot_root: str):
        if existing_robot_root == new_robot_root:
            # Nothing to do.
            return entry
        entry = cls._fix_path(entry)
        return entry.replace(existing_robot_root, new_robot_root)

    @classmethod
    def _fix_path(cls, path: str) -> str:
        if sys.platform == "win32":
            # On windows we need to fix the drive letter as we want to
            # replace 'C:' and 'c:'.
            if len(path) > 2 and path[1] == ":":
                drive_letter = path[0]
                if drive_letter.lower() == drive_letter:
                    return path

                return drive_letter.lower() + path[1:]

        return path

    def _compute_base_interpreter_info_for_doc_uri(
        self, doc_uri
    ) -> IInterpreterInfo | None:
        try:
            pm = self._pm()
            if pm is None:
                log.critical("Did not expect PluginManager to be None at this point.")
                return None

            # Check that our requirements are there.
            pm["EPConfigurationProvider"]
            pm["EPEndPointProvider"]

            fs_path = Path(uris.to_fs_path(doc_uri))
            # Note: there's a use-case where a directory may be passed to
            # compute as the doc_uri, so, handle that too.
            found_package_yaml = False

            for path in itertools.chain(iter([fs_path]), fs_path.parents):
                # Give higher priority to package.yaml (in case conda.yaml became
                # package.yaml but robot.yaml is still lingering around).
                package_yaml: Path = path / "package.yaml"
                if package_yaml.exists():
                    found_package_yaml = True
                    break

                robot_yaml: Path = path / "robot.yaml"
                if robot_yaml.exists():
                    break

            else:
                # i.e.: Could not find any package.yaml nor robot.yaml in the structure.
                log.debug("Could not find package.yaml nor robot.yaml for: %s", fs_path)
                return None

            robot_yaml_file_info: _CachedFileInfo | None
            parent: Path
            if found_package_yaml:
                # Dealing with a package.yaml.
                parent = package_yaml.parent
                robot_yaml_file_info = None
                try:
                    conda_or_package_file_info = _CacheInfo.get_file_info(package_yaml)
                except Exception:
                    log.exception("Error collecting info from: %s", package_yaml)
                    return None

            else:
                # Dealing with a robot.yaml (which must have an associated conda.yaml).
                try:
                    robot_yaml_file_info = _CacheInfo.get_file_info(robot_yaml)
                except Exception:
                    log.exception("Error collecting info from: %s", robot_yaml)
                    return None

                yaml_contents = robot_yaml_file_info.yaml_contents
                if not isinstance(yaml_contents, dict):
                    log.critical(f"Expected dict as root in: {robot_yaml}")
                    return None

                parent = robot_yaml.parent
                conda_config_path = get_conda_config_path(
                    parent, robot_yaml, yaml_contents
                )
                if not conda_config_path:
                    return None

                try:
                    conda_or_package_file_info = _CacheInfo.get_file_info(
                        conda_config_path
                    )
                except Exception:
                    log.exception("Error collecting info from: %s", conda_config_path)
                    return None

            # Feature: read devdata/env.json and add it to the environment.
            env_json_path = parent / "devdata" / "env.json"
            env_json_path_file_info = None
            if env_json_path.exists():
                try:
                    env_json_path_file_info = _CacheInfo.get_file_info(env_json_path)
                except Exception:
                    log.exception("Error collecting info from: %s", env_json_path)
                    return None

            return _CacheInfo.get_interpreter_info(
                robot_yaml_file_info,
                conda_or_package_file_info,
                env_json_path_file_info,
                pm,
            )
        except Exception as e:
            log.exception(f"Error getting interpreter info for: {doc_uri}: {e}")
        return None

    def __typecheckself__(self) -> None:
        _: EPResolveInterpreter = check_implements(self)


def get_conda_config_path(
    parent: Path, robot_yaml: Path, yaml_contents: dict
) -> Path | None:
    environments_config = yaml_contents.get("environmentConfigs")
    if environments_config:
        if isinstance(environments_config, (tuple, list)):
            # The arch is tricky. For instance, in Mac, the user would like to
            # have the target in aarch64 or amd64? It may not match the flavor
            # of the binary we're in and not even the processor... Should
            # this be specified in the robot? For now we simply don't filter
            # through the arch.

            if sys.platform == "win32":
                plat = "windows"

            elif sys.platform == "darwin":
                plat = "darwin"

            else:
                plat = "linux"

            for conda_env_conf in environments_config:
                if plat not in conda_env_conf:
                    import re

                    m = re.match(".*(windows|darwin|linux).*", conda_env_conf)
                    if m:
                        continue

                    # It doesn't have any platform to match (so, it matches any platform).

                p = parent / conda_env_conf
                try:
                    if not p.exists():
                        continue

                    return p
                except Exception:
                    log.exception("Error collecting info from: %s", p)

    conda_config = yaml_contents.get("condaConfigFile")

    if not conda_config:
        log.critical(
            "Dif not find env match in environmentConfigs/condaConfigFile in %s",
            robot_yaml,
        )
        return None

    conda_config_path = parent / conda_config
    if not conda_config_path.exists():
        log.critical(
            f"{conda_config} (defined from condaConfigFile) does not exist in %s",
            conda_config_path,
        )
        return None

    return conda_config_path


def register_plugins(pm: PluginManager):
    pm.register(
        EPResolveInterpreter,
        RobocorpResolveInterpreter,
        kwargs={"weak_pm": weakref.ref(pm)},
    )
