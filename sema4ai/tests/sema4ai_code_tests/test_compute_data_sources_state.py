import logging

import pytest
from sema4ai_ls_core.protocols import DataSourceStateDict

from sema4ai_code_tests.data_server_cli_wrapper import DataServerCliWrapper

log = logging.getLogger(__name__)


@pytest.fixture
def cleanup_data_sources(data_server_cli: DataServerCliWrapper):
    assert data_server_cli.http_connection is not None
    data_server_cli.http_connection.run_sql(
        "DROP TABLE IF EXISTS files.customers_in_test_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP DATABASE IF EXISTS test_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP MODEL IF EXISTS models.predict_compute_data_sources_state"
    )
    yield
    data_server_cli.http_connection.run_sql(
        "DROP TABLE IF EXISTS files.customers_in_test_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP MODEL IF EXISTS models.predict_compute_data_sources_state"
    )
    data_server_cli.http_connection.run_sql(
        "DROP DATABASE IF EXISTS test_compute_data_sources_state"
    )


def wait_for_models_to_be_ready(
    data_server_cli: DataServerCliWrapper, project_name_to_model_names: dict
):
    import time

    while project_name_to_model_names:
        still_training: dict[str, list[str]] = {}

        for project, models in project_name_to_model_names.items():
            for model in models:
                assert data_server_cli.http_connection is not None
                result = data_server_cli.http_connection.query(
                    database_name=project,
                    query=f"SELECT status, error FROM models WHERE name = '{model}'",
                )
                assert (
                    result is not None
                ), f"Failed to get model {model} from project {project}"
                if not result:
                    continue  # Someone else removed it in the meanwhile?

                row = next(result.iter_as_dicts())
                status = row.get("status", "").lower()

                if status in ("generating", "training"):
                    still_training.setdefault(project, []).append(model)
                    log.info(
                        f"Waiting for model {project}.{model} to complete. Current status: {status}"
                    )
                elif status == "error":
                    raise RuntimeError(
                        f"Model {project}.{model} failed to generate. Error: {row.get('error')}"
                    )
                elif status == "complete":
                    break
                else:
                    log.warning(f"Unexpected model status: {status}")

        if not still_training:
            break

        time.sleep(2)
        project_name_to_model_names = still_training


@pytest.mark.data_server
def test_compute_data_sources_state(
    data_server_cli: DataServerCliWrapper,
    language_server_initialized,
    ws_root_path,
    datadir,
    data_regression,
    cleanup_data_sources,
    tmpdir,
):
    import json
    import shutil

    from sema4ai_ls_core import uris

    from sema4ai_code.protocols import DataServerConfigTypedDict
    from sema4ai_code_tests.data_server_fixtures import create_another_sqlite_sample_db

    shutil.copytree(datadir / "package", ws_root_path)

    language_server = language_server_initialized

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

    def collect_data_source_state() -> DataSourceStateDict:
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
        assert result[
            "success"
        ], f"Expected success. Full result: {json.dumps(result, indent=2)}"

        assert result["result"] is not None, "Expected result to be not None"
        fixed_result: DataSourceStateDict = fix_data_sources_state_result(
            result["result"]
        )
        return fixed_result

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_all")

    # Now, let's configure the file data source.
    assert data_server_cli.http_connection is not None
    data_server_cli.http_connection.upload_file(
        datadir / "package" / "files" / "customers.csv",
        "customers_in_test_compute_data_sources_state",
    )
    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_sqlite")

    params = json.dumps({"db_file": str(create_another_sqlite_sample_db(tmpdir))})
    engine = "sqlite"
    data_server_cli.http_connection.run_sql(
        f"CREATE DATABASE `test_compute_data_sources_state` ENGINE = '{engine}' , PARAMETERS = {params}",
    )

    fixed_result = collect_data_source_state()
    data_regression.check(fixed_result, basename="missing_data_source_prediction")

    data_server_cli.http_connection.run_sql("""CREATE PROJECT IF NOT EXISTS models""")
    data_server_cli.http_connection.run_sql(
        """CREATE MODEL models.predict_compute_data_sources_state
FROM files
(SELECT * FROM customers_in_test_compute_data_sources_state)
PREDICT Index
WINDOW 8
HORIZON 4;"""
    )
    wait_for_models_to_be_ready(
        data_server_cli, {"models": ["predict_compute_data_sources_state"]}
    )

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
