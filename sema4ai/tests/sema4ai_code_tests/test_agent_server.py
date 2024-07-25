import os


def test_agent_server_download(tmpdir) -> None:
    from sema4ai_code.agent_server import (
        download_agent_server,
    )

    tmp_agent_server_location = f"{tmpdir}/agent-server-tmp"

    download_agent_server(tmp_agent_server_location)

    assert os.path.exists(tmp_agent_server_location)
