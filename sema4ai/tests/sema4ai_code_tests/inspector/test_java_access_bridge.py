import os
from pathlib import Path

import pytest

from sema4ai_code.inspector.java import java_access_bridge
from sema4ai_code.inspector.java.java_access_bridge import (
    ACCESS_BRIDGE_DLL,
    ENV_VAR,
    JABSWITCH,
    JavaAccessBridgeNotFound,
    find_java_access_bridge,
)


@pytest.fixture(autouse=True)
def no_registry(monkeypatch):
    # The tests must not depend on the Java installations of the machine.
    monkeypatch.setattr(java_access_bridge, "_registry_java_homes", lambda: iter(()))


def make_java(bin_dir: Path, dll=True, jabswitch=True, java=False) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    if dll:
        (bin_dir / ACCESS_BRIDGE_DLL).write_text("")
    if jabswitch:
        (bin_dir / JABSWITCH).write_text("")
    if java:
        for name in ("java", "java.exe"):
            exe = bin_dir / name
            exe.write_text("")
            exe.chmod(0o755)
    return bin_dir


def base_environ(tmp_path: Path, **kwargs) -> dict[str, str]:
    # Empty PATH: `java` is only found when the test adds it to the PATH.
    environ = {"PATH": str(tmp_path / "empty-path")}
    environ.update(kwargs)
    return environ


def test_env_var_is_used_first(tmp_path):
    env_bin = make_java(tmp_path / "custom")
    java_home = tmp_path / "jdk-21"
    make_java(java_home / "bin")

    bridge = find_java_access_bridge(
        base_environ(
            tmp_path,
            **{ENV_VAR: str(env_bin / ACCESS_BRIDGE_DLL), "JAVA_HOME": str(java_home)},
        )
    )
    assert bridge.dll == env_bin / ACCESS_BRIDGE_DLL
    assert bridge.jabswitch == env_bin / JABSWITCH


def test_env_var_missing_file_falls_back_to_java_home(tmp_path):
    java_home = tmp_path / "jdk-21"
    make_java(java_home / "bin")

    bridge = find_java_access_bridge(
        base_environ(
            tmp_path,
            **{
                ENV_VAR: str(tmp_path / "does-not-exist" / ACCESS_BRIDGE_DLL),
                "JAVA_HOME": str(java_home),
            },
        )
    )
    assert bridge.dll == java_home / "bin" / ACCESS_BRIDGE_DLL


def test_java_home_java_9_plus(tmp_path):
    # Java 9+: <java home>/bin (the case that didn't work before: CLOUD-5992).
    java_home = tmp_path / "jdk-21"
    make_java(java_home / "bin")

    bridge = find_java_access_bridge(base_environ(tmp_path, JAVA_HOME=str(java_home)))
    assert bridge.dll == java_home / "bin" / ACCESS_BRIDGE_DLL
    assert bridge.jabswitch == java_home / "bin" / JABSWITCH


def test_java_home_java_8_jdk(tmp_path):
    # Java 8 JDK: <java home>/jre/bin
    java_home = tmp_path / "jdk1.8.0_401"
    make_java(java_home / "jre" / "bin")

    bridge = find_java_access_bridge(base_environ(tmp_path, JAVA_HOME=str(java_home)))
    assert bridge.dll == java_home / "jre" / "bin" / ACCESS_BRIDGE_DLL


def test_java_in_path(tmp_path):
    java_bin = make_java(tmp_path / "jdk-17" / "bin", java=True)

    environ = base_environ(tmp_path)
    environ["PATH"] = str(java_bin)
    bridge = find_java_access_bridge(environ)
    assert bridge.dll.resolve() == (java_bin / ACCESS_BRIDGE_DLL).resolve()


def test_program_files_newest_first(tmp_path):
    program_files = tmp_path / "Program Files"
    make_java(program_files / "Eclipse Adoptium" / "jdk-17.0.19.10-hotspot" / "bin")
    make_java(program_files / "Eclipse Adoptium" / "jdk-21.0.11.10-hotspot" / "bin")

    bridge = find_java_access_bridge(
        base_environ(tmp_path, ProgramFiles=str(program_files))
    )
    assert bridge.dll == (
        program_files / "Eclipse Adoptium" / "jdk-21.0.11.10-hotspot" / "bin"
    ) / ACCESS_BRIDGE_DLL


def test_system32_without_jabswitch(tmp_path):
    # Java 8 JRE installers put the dll in System32 (no jabswitch there).
    system_root = tmp_path / "Windows"
    make_java(system_root / "System32", jabswitch=False)

    bridge = find_java_access_bridge(
        base_environ(tmp_path, SystemRoot=str(system_root))
    )
    assert bridge.dll == system_root / "System32" / ACCESS_BRIDGE_DLL
    assert bridge.jabswitch is None


def test_not_found_asks_user_to_set_env_var(tmp_path):
    java_home = tmp_path / "jdk-21"
    make_java(java_home / "bin", dll=False)
    missing = str(tmp_path / "missing" / ACCESS_BRIDGE_DLL)

    with pytest.raises(JavaAccessBridgeNotFound) as e:
        find_java_access_bridge(
            base_environ(tmp_path, JAVA_HOME=str(java_home), **{ENV_VAR: missing})
        )
    message = str(e.value)
    assert f"set the {ENV_VAR} environment variable" in message
    assert missing in message
    assert str(java_home / "bin") in message


def test_not_found_without_any_java(tmp_path):
    with pytest.raises(JavaAccessBridgeNotFound) as e:
        find_java_access_bridge(base_environ(tmp_path))
    assert ENV_VAR in str(e.value)
    assert "Searched in" not in str(e.value)


@pytest.mark.skipif(os.name != "nt", reason="Windows only")
def test_finds_access_bridge_on_this_machine_if_java_installed():
    # Smoke test with the real environment variables: only checks consistency,
    # as Java may not be installed.
    try:
        bridge = find_java_access_bridge()
    except JavaAccessBridgeNotFound:
        return
    assert bridge.dll.is_file()
