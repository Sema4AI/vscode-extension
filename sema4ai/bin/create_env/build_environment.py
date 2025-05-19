import json
import platform
import subprocess
from pathlib import Path

import requests


def get_working_dir() -> Path:
    """Return the directory current task was run in."""
    return Path(".").absolute()


def get_rcc() -> Path:
    working_dir = get_working_dir()
    system = platform.system().lower()

    if system == "windows":
        return working_dir / "rcc.exe"
    else:
        return working_dir / "rcc"


def run_rcc_command(
    args: list[str], shell: bool = False
) -> subprocess.CompletedProcess[str]:
    executable_path = get_rcc()

    # Gallery is sema4.ai specific, so no need to handle robocorp flag.
    args.append("--sema4ai")

    if not executable_path.is_file():
        raise FileNotFoundError(f"Could not find rcc executable at {executable_path}")

    return subprocess.run(
        [str(executable_path), *args],
        capture_output=True,
        text=True,
        shell=shell,
        cwd=str(get_working_dir())
    )


def os_architecture():
    result = run_rcc_command(["conf", "diag", "-j"])
    assert result.returncode == 0, f"Could not run diagnostics!"

    parsed = json.loads(result.stdout)
    details = parsed.get("details", {})
    assert details, "Could not get diagnostics details!"

    label = details.get("os", None)
    assert label, "Could not get OS from details!"

    return label


def ensure_holotree_shared():
    diagnostics_result = run_rcc_command(["conf", "diag", "-j"])

    diagnostics = json.loads(diagnostics_result.stdout)
    holotree_shared = diagnostics["details"]["holotree-shared"]

    if holotree_shared == "false":
        run_rcc_command(["ht", "shared", "--enable", "--once"])
        run_rcc_command(["ht", "init"])


def url_exists(url: str) -> bool:
    try:
        result = requests.head(url)
        return result.status_code == 200
    except requests.RequestException:
        return False


def blueprint_for(condafile):
    result = run_rcc_command(["ht", "blueprint", "-j", str(condafile)])
    assert result.returncode == 0, f"Could not run blueprint! Reason: {result.stderr}"

    try:
        parsed = json.loads(result.stdout)
        fingerprint = parsed.get("hash", None)

        if not fingerprint:
            raise RuntimeError("Could not get hash!")
        return fingerprint
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse blueprint output: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to parse blueprint output: {e}, {result.stdout}, {result.stderr}")


def get_environment_url(fingerprint: str) -> str:
    base_environments_url = "https://cdn.sema4.ai/vscode-extension/holotree/"
    return f"{base_environments_url}{fingerprint}"


def build_vscode_environment() -> None:
    ensure_holotree_shared()

    architecture = os_architecture()
    yaml_file = f"conda_vscode_{architecture}.yaml"
    fingerprint = blueprint_for(yaml_file)
    environment_url = get_environment_url(fingerprint)

    if url_exists(environment_url):
        print(f"Environment with hash {fingerprint} already exists, skipping")
        return

    working_dir = get_working_dir()
    package_yaml_path = working_dir / yaml_file

    # Ensure we're in the correct directory structure for CI
    environments_dir = working_dir / "environments"
    if not environments_dir.exists():
        environments_dir.mkdir(parents=True, exist_ok=True)

    result_zip_path = environments_dir / f"{fingerprint}-{architecture}.zip"

    print(f"Building: {yaml_file}")
    run_rcc_command(
        ["ht", "prebuild", str(package_yaml_path), "--export", str(result_zip_path)]
    )
    print(f"Environment built: {result_zip_path}")


if __name__ == "__main__":
    build_vscode_environment()
