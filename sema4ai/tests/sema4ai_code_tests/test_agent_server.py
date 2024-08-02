import os


def test_agent_cli_download(tmpdir) -> None:
    from sema4ai_code.agent_cli import (
        download_agent_cli,
    )

    tmp_agent_cli_location = f"{tmpdir}/agent-cli-tmp"

    download_agent_cli(tmp_agent_cli_location)

    assert os.path.exists(tmp_agent_cli_location)
