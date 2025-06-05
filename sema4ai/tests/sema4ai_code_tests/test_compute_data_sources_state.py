import logging
from typing import Any

import pytest
from sema4ai_ls_core.protocols import DataSourceStateDict

from sema4ai_code.protocols import DataServerConfigTypedDict
from sema4ai_code_tests.data_server_cli_wrapper import DataServerCliWrapper

log = logging.getLogger(__name__)


@pytest.fixture
def cleanup_data_sources(data_server_cli: DataServerCliWrapper):
    assert data_server_cli.http_connection is not None
    data_server_cli.http_connection.run_sql("""CREATE PROJECT IF NOT EXISTS sema4ai""")
    data_server_cli.http_connection.run_sql("""CREATE PROJECT IF NOT EXISTS models""")

    data_server_cli.http_connection.run_sql(
        "DROP DATABASE IF EXISTS test_compute_data_sources_state"
    )
    yield
    data_server_cli.http_connection.run_sql(
        "DROP TABLE IF EXISTS files.customers_in_test_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP DATABASE IF EXISTS test_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP KNOWLEDGE_BASE IF EXISTS sema4ai.wikipedia_kb;"
    )


def create_setup_config(
    data_server_cli: DataServerCliWrapper,
) -> DataServerConfigTypedDict:
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
        "is_running": True,
        "pid": -1,
        "pid_file_path": "",
    }
    return data_server_info


def setup_knowledge_base(data_server_cli: DataServerCliWrapper) -> None:
    create_kb = """
    CREATE KNOWLEDGE_BASE sema4ai.wikipedia_kb
    USING
        metadata_columns = ['wiki_id', 'infobox'],
        content_columns = ['wikitext', 'categories', 'general'],
        id_column = 'title';
    """
    data_server_cli.http_connection.run_sql(create_kb)


@pytest.fixture
def collect_data_source_state(
    language_server_initialized, data_server_cli, ws_root_path
) -> Any:
    language_server = language_server_initialized

    data_server_info: DataServerConfigTypedDict = create_setup_config(data_server_cli)

    def func() -> DataSourceStateDict:
        import json

        from sema4ai_ls_core import uris

        result = language_server.request(
            {
                "jsonrpc": "2.0",
                "id": language_server.next_id(),
                "method": "computeDataSourceState",
                "params": {
                    "action_package_yaml_directory_uri": uris.from_fs_path(
                        ws_root_path
                    ),
                    "data_server_info": data_server_info,
                },
            }
        )["result"]
        assert result["success"], (
            f"Expected success. Full result: {json.dumps(result, indent=2)}"
        )
        ret = result["result"]
        fixed_result = fix_data_sources_state_result(ret)
        return fixed_result

    return func


@pytest.mark.data_server
def test_setup_datasource(
    data_server_cli: DataServerCliWrapper,
    data_regression,
    cleanup_data_sources,
    collect_data_source_state,
    datadir,
    ws_root_path,
    language_server_initialized,
    tmpdir,
):
    import json
    import shutil

    from sema4ai_ls_core import uris
    from sema4ai_ls_core.protocols import DatasourceInfoTypedDict

    shutil.copytree(datadir / "package", ws_root_path)

    data_server_info: DataServerConfigTypedDict = create_setup_config(data_server_cli)

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_all")

    # Now, let's configure the file data source.
    unconfigured_data_sources = fixed_result["unconfigured_data_sources"]
    assert len(unconfigured_data_sources) == 3
    files_data_sources = [
        data_source
        for data_source in unconfigured_data_sources
        if data_source["engine"] == "files"
    ]

    assert len(files_data_sources) == 1
    assert files_data_sources[0]["file"] == "files/customers.csv"

    def setup_data_source(datasource: DatasourceInfoTypedDict):
        result = language_server_initialized.request(
            {
                "jsonrpc": "2.0",
                "id": language_server_initialized.next_id(),
                "method": "setupDataSource",
                "params": {
                    "action_package_yaml_directory_uri": uris.from_fs_path(
                        ws_root_path
                    ),
                    "datasource": datasource,
                    "data_server_info": data_server_info,
                },
            }
        )
        if "result" not in result:
            raise RuntimeError(
                f"Expected result to be in the response. Full response: {json.dumps(result, indent=2)}"
            )
        return result["result"]

    result = setup_data_source(files_data_sources[0])
    setup_knowledge_base(data_server_cli)

    assert result["success"], (
        f"Expected success. Full result: {json.dumps(result, indent=2)}"
    )
    assert "Uploaded file" in str(result["result"]), (
        "Expected 'Uploaded file' in the result. Full result: {json.dumps(result, indent=2)}"
    )

    fixed_result = collect_data_source_state()
    unconfigured_data_sources = fixed_result["unconfigured_data_sources"]
    data_regression.check(fixed_result, basename="missing_data_source_sqlite")
    assert len(unconfigured_data_sources) == 1

    setup_sqlite_data_source(data_server_cli, tmpdir)

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_none")
    unconfigured_data_sources = fixed_result["unconfigured_data_sources"]
    assert len(unconfigured_data_sources) == 0


def setup_sqlite_data_source(data_server_cli, tmpdir):
    import json

    from sema4ai_code_tests.data_server_fixtures import create_another_sqlite_sample_db

    params = json.dumps({"db_file": str(create_another_sqlite_sample_db(tmpdir))})
    engine = "sqlite"
    data_server_cli.http_connection.run_sql(
        f"CREATE DATABASE `test_compute_data_sources_state` ENGINE = '{engine}' , PARAMETERS = {params}",
    )


@pytest.mark.data_server
def test_compute_data_sources_state(
    data_server_cli: DataServerCliWrapper,
    ws_root_path,
    datadir,
    data_regression,
    cleanup_data_sources,
    tmpdir,
    collect_data_source_state,
):
    import shutil

    shutil.copytree(datadir / "package", ws_root_path)

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_all")

    # Now, let's configure the file data source.
    assert data_server_cli.http_connection is not None
    data_server_cli.http_connection.upload_file(
        datadir / "package" / "files" / "customers.csv",
        "customers_in_test_compute_data_sources_state",
    )
    setup_knowledge_base(data_server_cli)
    fixed_result = collect_data_source_state()

    data_regression.check(fixed_result, basename="missing_data_source_sqlite")

    setup_sqlite_data_source(data_server_cli, tmpdir)

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_none")


def fix_data_sources_state_result(result: DataSourceStateDict) -> DataSourceStateDict:
    """
    Args:
        result: The result to fix (we should change all `uri` to just the basename).
    """
    import os.path

    # We don't want existing data sources to affect the test.
    result["data_sources_in_data_server"] = []

    def _fix_uri(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "uri" and isinstance(value, str):
                    obj[key] = os.path.basename(value)
                elif isinstance(value, (dict, list)):
                    _fix_uri(value)
        elif isinstance(obj, list):
            for item in obj:
                _fix_uri(item)

    _fix_uri(result)
    return result


@pytest.mark.data_server
def test_drop_data_sources(
    data_server_cli: DataServerCliWrapper,
    language_server_initialized,
    ws_root_path,
    datadir,
    cleanup_data_sources,
    collect_data_source_state,
    tmpdir,
):
    import json
    import shutil

    from sema4ai_code_tests.data_server_fixtures import create_another_sqlite_sample_db

    shutil.copytree(datadir / "package", ws_root_path)

    language_server = language_server_initialized
    data_server_info = create_setup_config(data_server_cli)

    assert data_server_cli.http_connection is not None
    data_server_cli.http_connection.upload_file(
        datadir / "package" / "files" / "customers.csv",
        "customers_in_test_compute_data_sources_state",
    )
    setup_knowledge_base(data_server_cli)

    params = json.dumps({"db_file": str(create_another_sqlite_sample_db(tmpdir))})
    engine = "sqlite"
    data_server_cli.http_connection.run_sql(
        f"CREATE DATABASE `test_compute_data_sources_state` ENGINE = '{engine}' , PARAMETERS = {params}",
    )

    data_sources_state = collect_data_source_state()

    for data_source in data_sources_state["required_data_sources"]:
        result = language_server.request(
            {
                "jsonrpc": "2.0",
                "id": language_server.next_id(),
                "method": "dropDataSource",
                "params": {
                    "datasource": data_source,
                    "data_server_info": data_server_info,
                },
            }
        )["result"]
        assert result["success"], (
            f"Expected success. Full result: {json.dumps(result, indent=2)}"
        )
        assert result["message"] == "Data Source dropped successfully."

    # DROP again, should return success but with no action message
    for data_source in data_sources_state["required_data_sources"]:
        result = language_server.request(
            {
                "jsonrpc": "2.0",
                "id": language_server.next_id(),
                "method": "dropDataSource",
                "params": {
                    "datasource": data_source,
                    "data_server_info": data_server_info,
                },
            }
        )["result"]
        assert result["success"], (
            f"Expected success. Full result: {json.dumps(result, indent=2)}"
        )
        assert result["message"] == "Data source does not exist, no action needed."
