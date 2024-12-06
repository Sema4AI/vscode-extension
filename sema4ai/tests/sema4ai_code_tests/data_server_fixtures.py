from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator

import pytest

if TYPE_CHECKING:
    from sema4ai_code_tests.data_server_cli_wrapper import DataServerCliWrapper

    from sema4ai_code.data.data_server_connection import DataServerConnection

INSERT_SQL_DATA = [
    ("Alice", 30),
    ("Bob", 25),
    ("Charlie", 35),
    ("O'Neill", 40),
    ('O"no', 45),
]

DEFAULT_SQL_DATA = [
    (1, "Alice", 30),
    (2, "Bob", 25),
    (3, "Charlie", 35),
    (4, "O'Neill", 40),
    (5, 'O"no', 45),
]

INSERT_PRICES_DATA = [
    ("Apple", 1.0),
    ("Banana", 2.0),
    ("Cherry", 3.0),
    ("Durian", 4.0),
    ("Elderberry", 5.0),
]

DEFAULT_PRICES_DATA = [
    (1, "Apple", 1.0),
    (2, "Banana", 2.0),
    (3, "Cherry", 3.0),
    (4, "Durian", 4.0),
    (5, "Elderberry", 5.0),
]


@contextmanager
def _bootstrap_test_datasources(data_server_cli: "DataServerCliWrapper", tmpdir):
    """
    Note: many tests may use the same db name, so we need to ensure that the db is
    created with the expected data (even when running in parallel with pytest-xdist).
    """
    import time

    from sema4ai_ls_core.basic import wait_for_non_error_condition

    http_port, _mysql_port = data_server_cli.get_http_and_mysql_ports()

    http_connection = None

    def make_connection():
        from sema4ai_code.data.data_server_connection import DataServerConnection

        nonlocal http_connection
        curtime = time.time()
        http_connection = DataServerConnection(
            http_url=f"http://localhost:{http_port}",
            http_user=data_server_cli.get_username(),
            http_password=data_server_cli.get_password(),
        )
        http_connection.login()
        print(f"Took {time.time() - curtime:.2f} seconds to connect/login")

    # Bootstrapping it can take a really long time...
    wait_for_non_error_condition(make_connection, timeout=60 * 10, sleep=2)

    curtime = time.time()
    assert http_connection is not None
    result_set = http_connection.query(
        "", "select NAME, ENGINE from information_schema.databases where TYPE='data'"
    )
    columns = result_set.columns
    assert columns[0].lower() == "name"
    databases_info = list(result_set.iter_as_tuples())
    print(f"Took {time.time() - curtime:.2f} seconds to list databases")
    _create_db_if_needed(
        http_connection,
        test_db_name,
        databases_info,
        DEFAULT_SQL_DATA,
        create_sqlite_sample_db,
        tmpdir,
        "user_info",
    )
    _create_db_if_needed(
        http_connection,
        another_test_db_name,
        databases_info,
        DEFAULT_PRICES_DATA,
        create_another_sqlite_sample_db,
        tmpdir,
        "prices",
    )

    yield http_connection


def _create_db_if_needed(
    http_connection: "DataServerConnection",
    db_name: str,
    databases_info: list,
    default_data: list,
    create_db_fn: Callable[[Path], Path],
    tmpdir: Path,
    table_name: str,
):
    import json

    found_test_db = False
    needs_to_create = True
    for db in databases_info:
        if db[0] == db_name:
            found_test_db = True
            break

    if found_test_db:
        needs_to_create = False
        # Check that the existing version has the data we expect.
        current_db_data_valid = _is_current_db_data_valid(
            http_connection, db_name, default_data, table_name
        )

        if not current_db_data_valid:
            http_connection.run_sql(f"DROP DATABASE `{db_name}`")
            needs_to_create = True

    if needs_to_create:
        params = json.dumps({"db_file": str(create_db_fn(tmpdir))})
        engine = "sqlite"
        http_connection.run_sql(
            f"CREATE DATABASE `{db_name}` ENGINE = '{engine}' , PARAMETERS = {params}",
        )

        _is_current_db_data_valid(
            http_connection, db_name, default_data, table_name, make_assert=True
        )


def _is_current_db_data_valid(
    http_connection: "DataServerConnection",
    db_name: str,
    default_data: list,
    table_name: str,
    make_assert: bool = False,
) -> bool:
    try:
        result = http_connection.query("", f"SELECT * FROM `{db_name}`.{table_name}")
    except Exception:
        return False
    assert result is not None
    rows = list(result.iter_as_tuples())

    expected = default_data
    current_db_data_valid = rows == expected
    if make_assert:
        assert (
            current_db_data_valid
        ), f"Current data is not valid. Found: {rows}. Expected: {expected}"
    return current_db_data_valid


@pytest.fixture(scope="session")
def data_server_cli(request, tmpdir_factory) -> Iterator["DataServerCliWrapper"]:
    from sema4ai_code_tests.data_server_cli_wrapper import DataServerCliWrapper
    from sema4ai_ls_core.system_mutex import timed_acquire_mutex

    from sema4ai_code.rcc import RCC_CLOUD_ROBOT_MUTEX_NAME

    wrapper = DataServerCliWrapper(Path(str(tmpdir_factory.mktemp("data-server-cli"))))
    # This can be pretty slow (and may be common with pytest-xdist).
    with timed_acquire_mutex(RCC_CLOUD_ROBOT_MUTEX_NAME, timeout=60 * 20):
        wrapper.download_data_server_cli()
        wrapper.start()

        def teardown():
            if request.session.testsfailed:
                wrapper.print_log()

        request.addfinalizer(teardown)

        with _bootstrap_test_datasources(
            wrapper, tmpdir_factory.mktemp("tmpdir")
        ) as http_connection:
            wrapper.http_connection = http_connection
            yield wrapper


test_db_name = "sqlite-test-db"
another_test_db_name = "another-sqlite-test-db"


def create_sqlite_sample_db(tmpdir) -> Path:
    import sqlite3

    # Create a sample sqlite db in the tmpdir
    db_path = Path(tmpdir.join("sample.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a sample table
    cursor.execute(
        """
        CREATE TABLE user_info (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER
        )
    """
    )

    # Insert sample data
    cursor.executemany(
        """
        INSERT INTO user_info (name, age) VALUES (?, ?)
    """,
        INSERT_SQL_DATA,
    )

    cursor.execute("SELECT * FROM user_info")
    result = cursor.fetchall()
    assert result == DEFAULT_SQL_DATA

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    return db_path


def create_another_sqlite_sample_db(tmpdir) -> Path:
    import sqlite3

    # Create a sample sqlite db in the tmpdir
    db_path = Path(tmpdir.join("another_sample.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a sample table
    cursor.execute(
        """
        CREATE TABLE prices (
            id INTEGER PRIMARY KEY,
            item_name TEXT NOT NULL,
            price REAL
        )
    """
    )

    # Insert sample data
    cursor.executemany(
        """
        INSERT INTO prices (item_name, price) VALUES (?, ?)
    """,
        INSERT_PRICES_DATA,
    )

    cursor.execute("SELECT * FROM prices")
    result = cursor.fetchall()
    assert result == DEFAULT_PRICES_DATA

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    return db_path
