# Versions = Union[LegacyVersion, Version]
import datetime
import sys
import typing
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union

# Hack so that we don't break the runtime on versions prior to Python 3.8.
if sys.version_info[:2] < (3, 8):

    class Protocol(object):
        pass

    class TypedDict(object):
        pass

else:
    from typing import Protocol, TypedDict


VersionStr = str


class Versions(Protocol):
    def __lt__(self, other):
        pass


@dataclass
class ReleaseData:
    version: Versions
    version_str: VersionStr
    upload_time: Optional[str]  # "2020-02-05T14:11:38"

    def __lt__(self, other):
        return self.version < other.version


UrlDescription = str
UrlStr = str


class PyPiInfoTypedDict(TypedDict):
    description: str
    description_content_type: str
    home_page: str
    package_url: str
    project_urls: Dict[UrlDescription, UrlStr]

    # Info for the latest version
    # The constraints. i.e.: ['rpaframework-windows (>=7.3.2,<8.0.0) ; sys_platform == "win32"']
    # Something as ">=3.7,<4.0"
    requires_dist: List[str]
    requires_python: str
    version: VersionStr


class IPackageData(Protocol):
    package_name: str

    def add_release(self, version_str: VersionStr, release_info: List[dict]) -> None:
        """
        Args:
            version_str: The version we have info on.
            release_info: For each release we may have a list of files available.
        """

    @property
    def latest_version(self) -> VersionStr:
        pass

    def get_last_release_data(self) -> Optional[ReleaseData]:
        pass

    def iter_versions_released_after(
        self, after_datetime: datetime.datetime
    ) -> Iterator[ReleaseData]:
        pass

    def iter_versions_newer_than(self, version: Versions) -> Iterator[ReleaseData]:
        pass

    @property
    def info(self):
        pass

    def get_release_data(self, version: VersionStr) -> Optional[ReleaseData]:
        pass


class IPyPiCloud(Protocol):
    def get_package_data(self, package_name: str) -> Optional[IPackageData]:
        pass

    def get_versions_newer_than(
        self, package_name: str, version: Union[Versions, VersionStr]
    ) -> List[VersionStr]:
        """
        Args:
            package_name: The name of the package
            version: The minimum version (versions returned must be > than this one).

        Returns:
            A sorted list containing the versions > than the one passed (the last
            entry is the latest version).
        """


SubdirToBuildAndDependsJsonBytesType = Dict[str, List[Tuple[str, bytes]]]


@dataclass(unsafe_hash=True)
class CondaVersionInfo:
    package_name: str
    version: str  # This is the version from conda-forge.
    timestamp: int  # Max is given
    subdir_to_build_and_depends_json_bytes: SubdirToBuildAndDependsJsonBytesType


if typing.TYPE_CHECKING:
    # No need for sqlite3 until it's actually used.
    from sqlite3 import Cursor
else:
    Cursor = object


class LatestIndexInfoTypedDict(TypedDict):
    # The place where the index info is saved.
    index_dir: str
    timestamp: datetime.datetime


class ISqliteQueries(Protocol):
    @contextmanager
    def db_cursors(
        self, db_cursor: Optional[Sequence[Cursor]] = None
    ) -> Iterator[Sequence[Cursor]]:
        pass

    def query_names(self, db_cursors: Optional[Sequence[Cursor]] = None) -> Set[str]:
        pass

    def query_versions(
        self, package_name, db_cursors: Optional[Sequence[Cursor]] = None
    ) -> Set[str]:
        pass

    def query_version_info(
        self,
        package_name: str,
        version: str,
        db_cursors: Optional[Sequence[Cursor]] = None,
    ) -> CondaVersionInfo:
        pass


class IOnFinished(Protocol):
    def __call__(self):
        pass


class ICondaCloud(Protocol):
    def is_information_cached(self) -> bool:
        pass

    def sqlite_queries(self) -> Optional[ISqliteQueries]:
        pass

    def schedule_update(
        self, on_finished: Optional[IOnFinished] = None, wait=False, force=False
    ) -> None:
        pass
