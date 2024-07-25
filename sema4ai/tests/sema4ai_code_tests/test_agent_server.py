import os


def test_agent_server_download() -> None:
    from sema4ai_code.agent_server import (
        download_agent_server,
    )

    from sema4ai_code import get_bin_folder

    tmp_agent_server_location = f"{get_bin_folder()}/agent-server-tmp"

    download_agent_server(tmp_agent_server_location)

    assert os.path.exists(tmp_agent_server_location)

    os.remove(tmp_agent_server_location)
