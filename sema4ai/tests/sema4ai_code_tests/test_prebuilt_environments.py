import sys
from pathlib import Path

from sema4ai_ls_core.core_log import get_logger

from sema4ai_code.protocols import IRcc

log = get_logger(__name__)


def test_prebuilt_environments(rcc: IRcc, tmpdir):
    # We download the env and check that we can create it in the ci.
    import io
    import platform

    from sema4ai_ls_core import http

    import sema4ai_code

    robocorp_code_root = Path(sema4ai_code.__file__).parent.parent.parent

    rcc_ts = robocorp_code_root / "vscode-client" / "src" / "rcc.ts"
    if not rcc_ts.exists():
        # In GitHub we're in the site-packages.
        import os

        robocorp_code_root = Path(os.environ["GITHUB_WORKSPACE"]) / "sema4ai"
        if not robocorp_code_root.exists():
            msg = [f"{robocorp_code_root} does not exist.", "Environment:"]
            for key, val in sorted(os.environ.items()):
                msg.append(f"{key}={val}")
            raise AssertionError("\n".join(msg))
        rcc_ts = robocorp_code_root / "vscode-client" / "src" / "rcc.ts"

    text = rcc_ts.read_text("utf-8")
    conda_yaml = robocorp_code_root / "bin" / "create_env"

    if sys.platform == "win32":
        check = "const BASENAME_PREBUILT_WIN_AMD64 = "
        conda_yaml /= "conda_vscode_windows_amd64.yaml"
    elif "linux" in sys.platform:
        check = "const BASENAME_PREBUILT_LINUX_AMD64 = "
        conda_yaml /= "conda_vscode_linux_amd64.yaml"
    elif sys.platform == "darwin":
        if platform.machine() == "arm64":
            check = "const BASENAME_PREBUILT_DARWIN_ARM64 = "
            conda_yaml /= "conda_vscode_darwin_arm64.yaml"
        else:
            check = "const BASENAME_PREBUILT_DARWIN_AMD64 = "
            conda_yaml /= "conda_vscode_darwin_amd64.yaml"
    else:
        raise AssertionError(f"Unexpected platform: {sys.platform}.")

    assert conda_yaml.exists()

    # The code we're searching for is something as:
    # const BASENAME_PREBUILT_WIN_AMD64 = "978947424da5b5d4_windows_amd64.zip";
    for line in text.splitlines():
        if line.startswith(check):
            break
    else:
        raise AssertionError(f"Could not find line starting with: {check}.")

    basename_url = line.split("=")[-1].strip().replace('"', "").replace(";", "")
    full_url = f"https://cdn.sema4.ai/holotree/sema4ai/{basename_url}"
    p = Path(str(tmpdir / basename_url))

    if not p.exists():
        log.info(f"Downloading to: {p}")

        response = http.get(full_url)
        assert response.status_code == 200
        b = io.BytesIO(response.content)
        p.write_bytes(b.read())
        log.info(f"Finished downloading to: {p}")

    assert rcc.holotree_import(p, enable_shared=True).success

    assert rcc.holotree_variables(
        conda_yaml, "test-prebuilt-environments", no_build=True
    ).success
