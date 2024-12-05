from sema4ai_code_tests.data_server_cli_wrapper import DataServerCliWrapper


def test_compute_data_sources_state(
    data_server_cli: DataServerCliWrapper,
    language_server_initialized,
    cases,
    ws_root_path,
):
    import json

    from sema4ai_ls_core import uris

    from sema4ai_code.protocols import DataServerConfigTypedDict

    language_server = language_server_initialized
    cases.copy_to("action_package", ws_root_path)

    http_port, mysql_port = data_server_cli.get_http_and_mysql_ports()

    data_server_info: DataServerConfigTypedDict = {
        "api": {
            "http": {"host": "localhost", "port": str(http_port)},
            "mysql": {
                "host": "localhost",
                "port": str(mysql_port),
                "ssl": False,
            },
        },
        "auth": {
            "http_auth_enabled": False,
            "password": data_server_cli.get_password(),
            "username": data_server_cli.get_username(),
        },
        "isRunning": True,
        "pid": -1,
        "pidFilePath": "",
    }

    result = language_server.request(
        {
            "jsonrpc": "2.0",
            "id": language_server.next_id(),
            "method": "computeDataSourceState",
            "params": {
                "action_package_yaml_directory_uri": uris.from_fs_path(ws_root_path),
                "data_server_info": data_server_info,
            },
        }
    )
    print(json.dumps(result, indent=2))
