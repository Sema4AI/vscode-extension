import os


def test_agent_server_download() -> None:
    from sema4ai_code.agent_server import (
        get_default_agent_server_location,
        download_agent_server,
    )

    agent_server_location = get_default_agent_server_location()

    if os.path.exists(agent_server_location):
        os.remove(agent_server_location)

    download_agent_server(agent_server_location)

    assert os.path.exists(agent_server_location)
