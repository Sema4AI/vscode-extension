import logging
from pathlib import Path
from typing import TypedDict

log = logging.getLogger(__name__)


def get_release_artifact_relative_path(sys_platform: str, executable_name: str) -> str:
    """
    Helper function for getting the release artifact relative path as defined in S3 bucket.

    Args:
        sys_platform: Platform for which the release artifact is being retrieved.
        executable_name: Name of the executable we want to get the path for.
    """
    import platform

    machine = platform.machine()
    is_64 = not machine or "64" in machine

    if sys_platform == "win32":
        if is_64:
            return f"windows64/{executable_name}.exe"
        else:
            return f"windows32/{executable_name}.exe"

    elif sys_platform == "darwin":
        return f"macos_arm64/{executable_name}"

    else:
        if is_64:
            return f"linux64/{executable_name}"
        else:
            return f"linux32/{executable_name}"


class HttpNamedTypedDict(TypedDict):
    host: str
    port: str


class MysqlNamedTypedDict(TypedDict):
    database: str
    host: str
    port: str
    ssl: bool


class ApiNamedTypedDict(TypedDict):
    http: HttpNamedTypedDict
    mysql: MysqlNamedTypedDict


class AuthNamedTypedDict(TypedDict):
    http_auth_enabled: bool
    password: str
    username: str


class LaunchJsonDataTypedDict(TypedDict):
    api: ApiNamedTypedDict
    auth: AuthNamedTypedDict
    is_running: bool
    pid: int
    pid_file_path: str


class LaunchJsonTypedDict(TypedDict):
    success: bool
    data: LaunchJsonDataTypedDict


# {
#   "success": true,
#   "data": {
#     "api": {
#       "http": {
#         "host": "127.0.0.1",
#         "port": "47334"
#       },
#       "mysql": {
#         "database": "mindsdb",
#         "host": "127.0.0.1",
#         "port": "47335",
#         "ssl": false
#       }
#     },
#     "auth": {
#       "http_auth_enabled": false,
#       "password": "",
#       "username": "mindsdb"
#     },
#     "is_running": true,
#     "pid": 14848,
#     "pid_file_path": "%localappdata%\\sema4ai\\data-server\\data_server.pid"
#   }
# }


class DataServerCliWrapper:
    VERSION = "1.0.2"

    def __init__(self, tmpdir: Path) -> None:
        from typing import Optional

        self.target = self.get_default_target()
        self._launch_json: Optional[LaunchJsonTypedDict] = None
        self._tmpdir = tmpdir
        from sema4ai_code.data.data_server_connection import DataServerConnection

        self.http_connection: Optional[DataServerConnection] = None

    @property
    def launch_json(self) -> LaunchJsonTypedDict:
        if self._launch_json is None:
            raise RuntimeError("Data server cli not started")
        return self._launch_json

    def get_default_target(self) -> Path:
        import os
        import sys

        if sys.platform == "win32":
            localappdata = os.environ.get("LOCALAPPDATA")
            if not localappdata:
                raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
            home = Path(localappdata) / "sema4ai"
        else:
            # Linux/Mac
            home = Path("~/.sema4ai").expanduser()

        directory = home / "data-server-cli" / self.VERSION
        directory.mkdir(parents=True, exist_ok=True)
        executable_name = "data-server-cli"
        if sys.platform == "win32":
            executable_name += ".exe"
        ret = directory / executable_name
        return ret

    def download_data_server_cli(self):
        if self.target.exists():
            return

        import sys

        relative_path = get_release_artifact_relative_path(
            sys.platform, "data-server-cli"
        )
        url = (
            f"https://cdn.sema4.ai/data-server-cli/beta/v{self.VERSION}/{relative_path}"
        )
        import sema4ai_http

        result = sema4ai_http.download_with_resume(
            url, self.target, make_executable=True
        )
        assert result.status in (
            sema4ai_http.DownloadStatus.DONE,
            sema4ai_http.DownloadStatus.ALREADY_EXISTS,
        )

    def start(self):
        import json
        import subprocess
        import time

        log.info(f"Starting data server cli at {self.target}")
        curtime = time.time()
        output = subprocess.check_output(
            [self.target, "launch", "-i", "-j", "--wait"],
            cwd=self._tmpdir,
            stderr=subprocess.PIPE,
        )
        log.info(f"Time taken: {time.time() - curtime} seconds")
        contents = output.decode("utf-8")
        json_contents = json.loads(contents)

        if not json_contents.get("success"):
            raise RuntimeError(f"Failed to launch data server cli: {contents}")

        self._launch_json = json_contents

    def print_log(self):
        import subprocess

        process = subprocess.Popen(
            [self.target, "log"],
            cwd=self._tmpdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, _ = process.communicate()
        # Print the last 100 lines
        log_contents = "\n".join(stdout.decode("utf-8").splitlines()[-100:])
        print(log_contents)

    def get_username(self) -> str:
        return self.launch_json["data"]["auth"]["username"]

    def get_password(self) -> str:
        return self.launch_json["data"]["auth"]["password"]

    def get_http_and_mysql_ports(self) -> tuple[int, int]:
        return (
            int(self.launch_json["data"]["api"]["http"]["port"]),
            int(self.launch_json["data"]["api"]["mysql"]["port"]),
        )
