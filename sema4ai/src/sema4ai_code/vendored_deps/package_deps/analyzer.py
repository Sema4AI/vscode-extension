"""
This package should be independent of the rest as we can potentially make
it a standalone package in the future (maybe with a command line UI).
"""

import pathlib
import typing
from collections.abc import Iterator
from typing import Optional, Union

from ..ls_protocols import _DiagnosticSeverity, _DiagnosticsTypedDict
from ._deps_protocols import ICondaCloud, IPyPiCloud

if typing.TYPE_CHECKING:
    from ._conda_deps import CondaDepInfo, CondaDeps
    from ._package_deps import PackageDepsConda, PackageDepsPip
    from ._pip_deps import PipDepInfo, PipDeps


class BaseAnalyzer:
    _pypi_cloud: IPyPiCloud
    _conda_cloud: ICondaCloud

    _pip_deps: "Union[PipDeps, PackageDepsPip]"
    _conda_deps: "Union[CondaDeps, PackageDepsConda]"

    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        """
        Args:
            contents: The contents of the conda.yaml/action-server.yaml.
            path: The path for the conda yaml.
        """
        from .pypi_cloud import PyPiCloud

        self.contents = contents
        self.path = path

        self._loaded_yaml = False
        self._load_errors: list[_DiagnosticsTypedDict] = []
        self._yaml_data: dict | None = None

        if pypi_cloud is None:
            self._pypi_cloud = PyPiCloud()
        else:
            self._pypi_cloud = pypi_cloud

        self._conda_cloud = conda_cloud

    def _load_yaml_info(self) -> None:
        """
        Loads the base information and creates errors for syntax errors
        loading the yaml.
        """

        if self._loaded_yaml:
            return
        self._loaded_yaml = True

        from yaml.error import MarkedYAMLError

        from ..yaml_with_location import LoaderWithLines, create_range_from_location

        diagnostic: _DiagnosticsTypedDict

        try:
            loader = LoaderWithLines(self.contents)
            path: pathlib.Path = pathlib.Path(self.path)

            loader.name = f".../{path.parent.name}/{path.name}"
            data = loader.get_single_data()
            if isinstance(data, dict):
                self._yaml_data = data
            else:
                diagnostic = {
                    "range": create_range_from_location(0, 0),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": "Error: expected dict to be root of yaml",
                }
                self._load_errors.append(diagnostic)

        except MarkedYAMLError as e:
            if e.problem_mark:
                diagnostic = {
                    "range": create_range_from_location(
                        e.problem_mark.line, e.problem_mark.column
                    ),
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": f"Syntax error: {e}",
                }
                self._load_errors.append(diagnostic)

    def iter_pip_issues(self):
        from .pip_impl import pip_packaging_version

        for dep_info in self._pip_deps.iter_deps_infos():
            if dep_info.error_msg:
                diagnostic = {
                    "range": dep_info.dep_range,
                    "severity": _DiagnosticSeverity.Error,
                    "source": "sema4ai",
                    "message": dep_info.error_msg,
                }

                yield diagnostic

                continue

            if dep_info.constraints and len(dep_info.constraints) == 1:
                # For now just checking versions '=='.
                constraint = next(iter(dep_info.constraints))
                if constraint[0] == "==":
                    local_version = constraint[1]
                    newer_cloud_versions = self._pypi_cloud.get_versions_newer_than(
                        dep_info.name, pip_packaging_version.parse(local_version)
                    )
                    if newer_cloud_versions:
                        latest_cloud_version = newer_cloud_versions[-1]
                        diagnostic = {
                            "range": dep_info.dep_range,
                            "severity": _DiagnosticSeverity.Warning,
                            "source": "sema4ai",
                            "message": f"Consider updating '{dep_info.name}' to the latest version: '{latest_cloud_version}'. "
                            + f"Found {len(newer_cloud_versions)} versions newer than the current one: {', '.join(newer_cloud_versions)}.",
                        }

                        yield diagnostic

    def iter_conda_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        from .conda_cloud import sort_conda_versions
        from .conda_impl.conda_version import VersionSpec

        diagnostic: _DiagnosticsTypedDict
        dep_vspec = self._conda_deps.get_dep_vspec("python")

        # See: https://devguide.python.org/versions/

        if dep_vspec is not None:
            # We have the dep spec, not the actual version
            # (so, it could be something as >3.3 <4)
            # So, if an old version may be gotten from that spec, we warn about it.
            vspec = VersionSpec(dep_vspec)
            for old_version in "2 3.1 3.2 3.3 3.4 3.5 3.6 3.7".split(" "):
                if vspec.match(old_version):
                    dep_range = self._conda_deps.get_dep_range("python")

                    diagnostic = {
                        "range": dep_range,
                        "severity": _DiagnosticSeverity.Warning,
                        "source": "sema4ai",
                        "message": "The official support for versions lower than Python 3.8 has ended. "
                        + " It is advisable to transition to a newer version "
                        + "(Python 3.9 or newer is recommended).",
                    }

                    yield diagnostic
                    break

        dep_vspec = self._conda_deps.get_dep_vspec("pip")

        if dep_vspec is not None:
            vspec = VersionSpec(dep_vspec)
            # pip should be 22 or newer, so, check if an older version matches.
            for old_version in (str(x) for x in range(1, 22)):
                if vspec.match(old_version):
                    dep_range = self._conda_deps.get_dep_range("pip")

                    diagnostic = {
                        "range": dep_range,
                        "severity": _DiagnosticSeverity.Warning,
                        "source": "sema4ai",
                        "message": "Consider updating pip to a newer version (at least pip 22 onwards is recommended).",
                    }

                    yield diagnostic
                    break

        sqlite_queries = self._conda_cloud.sqlite_queries()
        if sqlite_queries:
            with sqlite_queries.db_cursors() as db_cursors:
                for conda_dep in self._conda_deps.iter_deps_infos():
                    if conda_dep.name in ("python", "pip", "uv"):
                        continue

                    if conda_dep.error_msg:
                        diagnostic = {
                            "range": conda_dep.dep_range,
                            "severity": _DiagnosticSeverity.Error,
                            "source": "sema4ai",
                            "message": conda_dep.error_msg,
                        }

                        yield diagnostic

                        continue

                    version_spec = conda_dep.get_dep_vspec()
                    if version_spec is None:
                        continue

                    versions = sqlite_queries.query_versions(conda_dep.name, db_cursors)
                    if not versions:
                        continue

                    sorted_versions = sort_conda_versions(versions)
                    last_version = sorted_versions[-1]
                    if not version_spec.match(last_version):
                        # The latest version doesn't match, let's show a warning.
                        newer_cloud_versions = []
                        for v in reversed(sorted_versions):
                            if not version_spec.match(v):
                                newer_cloud_versions.append(v)
                            else:
                                break

                        diagnostic = {
                            "range": conda_dep.dep_range,
                            "severity": _DiagnosticSeverity.Warning,
                            "source": "sema4ai",
                            "message": f"Consider updating '{conda_dep.name}' to match the latest version: '{last_version}'. "
                            + f"Found {len(newer_cloud_versions)} versions that don't match the version specification: {', '.join(newer_cloud_versions)}.",
                        }

                        yield diagnostic

    def find_pip_dep_at(self, line, col) -> "Optional[PipDepInfo]":
        """
        Args:
            line: 0-based line
        """
        from ..yaml_with_location import is_inside

        self._load_yaml_info()
        for dep_info in self._pip_deps.iter_deps_infos():
            if is_inside(dep_info.dep_range, line, col):
                return dep_info
        return None

    def find_conda_dep_at(self, line, col) -> "Optional[CondaDepInfo]":
        from ..yaml_with_location import is_inside

        self._load_yaml_info()
        for dep_info in self._conda_deps.iter_deps_infos():
            if is_inside(dep_info.dep_range, line, col):
                return dep_info
        return None


class PackageYamlAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        from ._package_deps import PackageDepsConda, PackageDepsPip

        self._pip_deps = PackageDepsPip()
        self._conda_deps = PackageDepsConda()
        self._additional_load_errors: list[_DiagnosticsTypedDict] = []

        BaseAnalyzer.__init__(self, contents, path, conda_cloud, pypi_cloud=pypi_cloud)

    def iter_package_yaml_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        self._load_yaml_info()
        if self._load_errors:
            yield from iter(self._load_errors)
            return

        data = self._yaml_data
        if not data:
            return

        yield from iter(self._additional_load_errors)
        yield from self.iter_conda_issues()
        yield from self.iter_pip_issues()

    def _load_yaml_info(self) -> None:
        if self._loaded_yaml:
            return

        from ..yaml_with_location import (
            create_range_from_location,
            str_with_location,
            str_with_location_capture,
        )

        BaseAnalyzer._load_yaml_info(self)
        data = self._yaml_data
        if not data:
            return

        diagnostic: _DiagnosticsTypedDict
        dependencies_key_entry: str_with_location_capture = str_with_location_capture(
            "dependencies"
        )

        dependencies = data.get(dependencies_key_entry)
        if dependencies is None:
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: 'dependencies' entry not found",
            }
            self._additional_load_errors.append(diagnostic)
            return

        if not dependencies:
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": "Error: 'dependencies' entry must not be empty",
            }
            self._additional_load_errors.append(diagnostic)

        elif not isinstance(dependencies, dict):
            diagnostic = {
                "range": create_range_from_location(0, 0),
                "severity": _DiagnosticSeverity.Error,
                "source": "sema4ai",
                "message": f"Error: expected 'dependencies' entry to be a dict (with 'conda-forge' and 'pypi' entries). Found: '{type(dependencies)}'",
            }
            self._additional_load_errors.append(diagnostic)
        else:
            for dep_name, dep in dependencies.items():
                if isinstance(dep_name, str_with_location):
                    if dep_name == "pypi":
                        if not isinstance(dep, list):
                            diagnostic = {
                                "range": dep_name.as_range(),
                                "severity": _DiagnosticSeverity.Error,
                                "source": "sema4ai",
                                "message": f"Error: expected the entries of pypi to be a list. Found: {type(dep)}",
                            }
                            self._additional_load_errors.append(diagnostic)
                            continue

                        for entry in dep:
                            if not isinstance(entry, str_with_location):
                                diagnostic = {
                                    "range": dep_name.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Error: expected the entries of pypi to be strings. Found: {type(entry)}: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            if entry.replace(" ", "") == "--use-feature=truststore":
                                diagnostic = {
                                    "range": entry.as_range(),
                                    "severity": _DiagnosticSeverity.Warning,
                                    "source": "sema4ai",
                                    "message": (
                                        "--use-feature=truststore flag does not need to "
                                        "be specified (it is automatically used when a "
                                        '"robocorp-truststore" or "truststore" dependency is added).'
                                    ),
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            if entry.startswith("--"):
                                diagnostic = {
                                    "range": entry.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Invalid entry in pypi: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            self._pip_deps.add_dep(entry, entry.as_range())

                    elif dep_name == "conda-forge":
                        for entry in dep:
                            if not isinstance(entry, str_with_location):
                                diagnostic = {
                                    "range": dep_name.as_range(),
                                    "severity": _DiagnosticSeverity.Error,
                                    "source": "sema4ai",
                                    "message": f"Error: expected the entries of conda-forge to be strings. Found: {type(entry)}: {entry}",
                                }
                                self._additional_load_errors.append(diagnostic)
                                continue

                            self._conda_deps.add_dep(entry, entry.as_range())

                    else:
                        diagnostic = {
                            "range": dep_name.as_range(),
                            "severity": _DiagnosticSeverity.Error,
                            "source": "sema4ai",
                            "message": (
                                "Error: only expected children are pypi and conda (dict entries). "
                                f"Found: {dep_name}"
                            ),
                        }
                        self._additional_load_errors.append(diagnostic)
                else:
                    diagnostic = {
                        "range": dependencies_key_entry.as_range(),
                        "severity": _DiagnosticSeverity.Error,
                        "source": "sema4ai",
                        "message": "Error: found unexpected entry in dependencies.",
                    }
                    self._additional_load_errors.append(diagnostic)


class CondaYamlAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        contents: str,
        path: str,
        conda_cloud: ICondaCloud,
        pypi_cloud: IPyPiCloud | None = None,
    ):
        from ._conda_deps import CondaDeps
        from ._pip_deps import PipDeps

        self._pip_deps = PipDeps()
        self._conda_deps = CondaDeps()

        BaseAnalyzer.__init__(self, contents, path, conda_cloud, pypi_cloud=pypi_cloud)

    def _load_yaml_info(self) -> None:
        if self._loaded_yaml:
            return

        from ..yaml_with_location import str_with_location

        BaseAnalyzer._load_yaml_info(self)
        data = self._yaml_data
        if not data:
            return

        dependencies = data.get("dependencies")

        conda_versions = self._conda_deps
        pip_versions = self._pip_deps
        if dependencies:
            for dep in dependencies:
                # At this level we're seeing conda versions. The spec is:
                # https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications
                # A bunch of code from conda was copied to handle that so that we
                # can just `conda_match_spec.parse_spec_str` to identify the version
                # we're dealing with.
                if isinstance(dep, str_with_location):
                    conda_versions.add_dep(dep, dep.as_range())
                elif isinstance(dep, dict):
                    pip_deps = dep.get("pip")
                    if pip_deps:
                        for dep in pip_deps:
                            if isinstance(dep, str_with_location) and isinstance(
                                dep, str
                            ):
                                pip_versions.add_dep(dep, dep.as_range())

    def iter_conda_yaml_issues(self) -> Iterator[_DiagnosticsTypedDict]:
        self._load_yaml_info()
        if self._load_errors:
            yield from iter(self._load_errors)
            return

        data = self._yaml_data
        if not data:
            return

        yield from self.iter_conda_issues()
        yield from self.iter_pip_issues()
