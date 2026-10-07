"""
Finds the (64-bit) Java Access Bridge needed by the Java inspector.

The lookup order is:

1. The `RC_JAVA_ACCESS_BRIDGE_DLL` environment variable (if the file exists).
2. Known Java locations: `JAVA_HOME`, `java` in the `PATH`, the Windows registry,
   the usual installation folders in `Program Files` and `System32` (where the
   Java 8 installers put the Access Bridge).

Java 9+ has the files in `<java home>/bin`, Java 8 JDKs in `<java home>/jre/bin`.
"""

import os
import shutil
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)

ENV_VAR = "RC_JAVA_ACCESS_BRIDGE_DLL"
ACCESS_BRIDGE_DLL = "WindowsAccessBridge-64.dll"
JABSWITCH = "jabswitch.exe"

# Folders (inside `Program Files`) where the common Java distributions are installed.
_JAVA_VENDOR_FOLDERS = (
    "Java",
    "Eclipse Adoptium",
    "Eclipse Foundation",
    "AdoptOpenJDK",
    "Amazon Corretto",
    "Microsoft",
    "Zulu",
    "BellSoft",
    "Semeru",
    "OpenJDK",
)


class JavaAccessBridgeNotFound(Exception):
    pass


@dataclass
class JavaAccessBridge:
    dll: Path
    # May be None (e.g.: when the dll is in System32): enabling the bridge is then skipped.
    jabswitch: Path | None


def _is_dir(path: Path) -> bool:
    # Path.is_dir() raises on e.g. PermissionError: an unreadable location is
    # just skipped (so that the search continues and the user gets a proper message).
    try:
        return path.is_dir()
    except (OSError, ValueError) as e:
        log.info(f"JAVA: Unable to check {path}: {e}")
        return False


def _is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except (OSError, ValueError) as e:
        log.info(f"JAVA: Unable to check {path}: {e}")
        return False


def _clean_path(value: str) -> str:
    # i.e.: `set RC_JAVA_ACCESS_BRIDGE_DLL="C:\..."` in cmd keeps the quotes.
    return os.path.expandvars(value.strip().strip('"').strip("'").strip())


def _bin_dirs_of_java_home(java_home: str | Path) -> list[Path]:
    java_home = Path(java_home)
    return [java_home / "bin", java_home / "jre" / "bin"]


def _registry_java_homes() -> Iterator[str]:
    """
    Java homes registered in the Windows registry (Oracle/OpenJDK: `JavaSoft`,
    Eclipse Adoptium, Microsoft, Azul Zulu).
    """
    if sys.platform != "win32":
        return

    import winreg

    def subkeys(key) -> Iterator[str]:
        i = 0
        while True:
            try:
                yield winreg.EnumKey(key, i)
            except OSError:
                return
            i += 1

    def value(key, name: str) -> str | None:
        try:
            return str(winreg.QueryValueEx(key, name)[0])
        except OSError:
            return None

    # (registry path, path of the value inside each version key)
    locations = [
        (r"SOFTWARE\JavaSoft\JDK", ("", "JavaHome")),
        (r"SOFTWARE\JavaSoft\JRE", ("", "JavaHome")),
        (r"SOFTWARE\JavaSoft\Java Development Kit", ("", "JavaHome")),
        (r"SOFTWARE\JavaSoft\Java Runtime Environment", ("", "JavaHome")),
        (r"SOFTWARE\Eclipse Adoptium\JDK", (r"hotspot\MSI", "Path")),
        (r"SOFTWARE\Eclipse Adoptium\JRE", (r"hotspot\MSI", "Path")),
        (r"SOFTWARE\Microsoft\JDK", (r"hotspot\MSI", "Path")),
        (r"SOFTWARE\Azul Systems\Zulu", ("", "InstallationPath")),
    ]
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for path, (subpath, value_name) in locations:
            try:
                key = winreg.OpenKey(root, path)
            except OSError:
                continue
            with key:
                # Newest versions first.
                for version in sorted(subkeys(key), reverse=True):
                    try:
                        version_key = winreg.OpenKey(
                            key, f"{version}\\{subpath}" if subpath else version
                        )
                    except OSError:
                        continue
                    with version_key:
                        java_home = value(version_key, value_name)
                    if java_home:
                        yield _clean_path(java_home)


def _program_files_java_homes(environ: Mapping[str, str]) -> Iterator[Path]:
    seen: set[str] = set()
    for var in ("ProgramW6432", "ProgramFiles"):
        program_files = environ.get(var)
        if not program_files or program_files.lower() in seen:
            continue
        seen.add(program_files.lower())
        for vendor in _JAVA_VENDOR_FOLDERS:
            vendor_dir = Path(program_files) / vendor
            try:
                # Newest versions first (i.e.: jdk-21... before jdk-17...).
                children = sorted(vendor_dir.iterdir(), reverse=True)
            except OSError:
                continue
            for child in children:
                if _is_dir(child):
                    yield child


def iter_java_bin_dirs(environ: Mapping[str, str] | None = None) -> Iterator[Path]:
    """
    Provides the (existing) directories where the Access Bridge may be, in the
    order in which they should be checked (without duplicates).
    """
    if environ is None:
        environ = os.environ

    def candidates() -> Iterator[Path]:
        java_home = environ.get("JAVA_HOME")
        if java_home:
            yield from _bin_dirs_of_java_home(_clean_path(java_home))

        try:
            java = shutil.which("java", path=environ.get("PATH"))
            if java:
                # <java home>/bin/java.exe or <java home>/jre/bin/java.exe
                yield Path(java).resolve().parent
        except (OSError, ValueError) as e:
            log.info(f"JAVA: Unable to check `java` in the PATH: {e}")

        for registry_java_home in _registry_java_homes():
            yield from _bin_dirs_of_java_home(registry_java_home)

        for program_files_java_home in _program_files_java_homes(environ):
            yield from _bin_dirs_of_java_home(program_files_java_home)

        system_root = environ.get("SystemRoot")
        if system_root:
            yield Path(system_root) / "System32"

    seen: set[str] = set()
    for candidate in candidates():
        key = os.path.normcase(os.path.normpath(str(candidate)))
        if key in seen:
            continue
        seen.add(key)
        if _is_dir(candidate):
            yield candidate


def _not_found_message(searched: list[Path], env_var_value: str | None) -> str:
    lines = [
        f"Unable to find the Java Access Bridge ({ACCESS_BRIDGE_DLL}), which is needed to inspect Java applications.",
    ]
    if env_var_value:
        lines.append(
            f"The {ENV_VAR} environment variable points to a file that does not exist (or can't be read): {env_var_value}"
        )
    lines.append(
        "Install a 64-bit Java (8 or newer), or set the "
        f"{ENV_VAR} environment variable to the full path of {ACCESS_BRIDGE_DLL} "
        rf"(e.g.: C:\Program Files\Java\jdk-21\bin\{ACCESS_BRIDGE_DLL}) "
        "and restart VS Code."
    )
    if searched:
        lines.append("Searched in: " + ", ".join(str(p) for p in searched))
    return "\n".join(lines)


def find_java_access_bridge(
    environ: Mapping[str, str] | None = None,
) -> JavaAccessBridge:
    """
    Raises:
        JavaAccessBridgeNotFound: if the Access Bridge dll could not be found.
    """
    if environ is None:
        environ = os.environ

    bin_dirs = list(iter_java_bin_dirs(environ))

    def find_jabswitch(preferred_dir: Path) -> Path | None:
        for directory in [preferred_dir] + bin_dirs:
            jabswitch = directory / JABSWITCH
            if _is_file(jabswitch):
                return jabswitch
        return None

    # 1. The user-defined environment variable.
    env_var_value = _clean_path(environ.get(ENV_VAR) or "")
    if env_var_value:
        dll = Path(env_var_value)
        if _is_file(dll):
            log.info(f"JAVA: Using {ENV_VAR}: {dll}")
            return JavaAccessBridge(dll, find_jabswitch(dll.parent))
        log.info(
            f"JAVA: {ENV_VAR} points to a file that does not exist (or can't be read): {env_var_value}. "
            "Searching for the Java Access Bridge in the known locations."
        )

    # 2. Known locations.
    for directory in bin_dirs:
        dll = directory / ACCESS_BRIDGE_DLL
        if _is_file(dll):
            log.info(f"JAVA: Found the Java Access Bridge at: {dll}")
            return JavaAccessBridge(dll, find_jabswitch(directory))

    raise JavaAccessBridgeNotFound(_not_found_message(bin_dirs, env_var_value))
