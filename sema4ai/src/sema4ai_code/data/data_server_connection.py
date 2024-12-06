import logging
import typing
from pathlib import Path
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from .result_set import ResultSet

log = logging.getLogger(__name__)


class _HttpConnectionHelper:
    """
    Helper class to manage connections to the http server.
    """

    def __init__(self, http_url: str, http_user: str, http_password: str) -> None:
        self._http_url = http_url
        self._http_user = http_user
        self._http_password = http_password
        self._session_headers: dict[str, str] = {}

    def login(self) -> None:
        from http.cookies import SimpleCookie

        import sema4ai_http

        login_url = f"{self._http_url}/api/login"

        login_response = sema4ai_http.post(
            login_url,
            json={"password": self._http_password, "username": self._http_user},
        )

        if login_response.status != 200:
            raise Exception(
                f"Failed to login. Status: {login_response.status}. Data: {login_response.data.decode('utf-8', errors='backslashreplace')}"
            )

        cookies = SimpleCookie()
        session_cookies = {}
        if "set-cookie" in login_response.headers:
            cookies.load(login_response.headers["set-cookie"])
            session_cookies = {key: morsel.value for key, morsel in cookies.items()}
        cookie_header = "; ".join([f"{k}={v}" for k, v in session_cookies.items()])
        self._session_headers = {"Cookie": cookie_header}

    def _is_login_info_available(self) -> bool:
        return bool(self._http_user and self._http_password)

    def _login_if_needed(self) -> None:
        if not self._session_headers and self._is_login_info_available():
            self.login()

    def upload_file(self, file_path: Path, table_name: str) -> None:
        self._login_if_needed()
        try:
            self._upload_file(file_path, table_name)
        except Exception:
            if not self._is_login_info_available():
                raise

            # Retry once with a new session
            self._session_headers = {}
            self._login_if_needed()
            self._upload_file(file_path, table_name)

    def run_sql(
        self, sql: str, database: str | None = None
    ) -> tuple[list[str], list[list[Any]]] | None:
        """
        Args:
            sql:
            database:

        Returns:
            A tuple of columns and rows.
        """
        import sema4ai_http

        log.info(f"Running sql:\n{sql}")
        self._login_if_needed()

        url = self._http_url + "/api/sql/query"

        result = sema4ai_http.post(
            url,
            json={"query": sql, "context": {"db": database or ""}},
            headers=self._session_headers,
        )
        if result.status != 200:
            raise Exception(
                f"Failed to run sql. Status: {result.status}. Data: {result.data.decode('utf-8', errors='backslashreplace')}"
            )

        data = result.json()
        data_type = data["type"]
        if data_type == "table":
            columns: list[str] = [x for x in data["column_names"]]
            rows: list[list[Any]] = data["data"]
            return columns, rows
        if data_type == "ok":
            return None
        if data_type == "error":
            raise RuntimeError(data["error_message"])
        log.debug(f"Unexpected sql result type: {data_type}")
        return None

    def _upload_file(self, file_path: Path, table_name: str) -> None:
        import json

        import sema4ai_http

        file_name = file_path.name
        data = file_path.read_bytes()
        result = sema4ai_http.put(
            f"{self._http_url}/api/files/{table_name}",
            fields={
                "file": (file_name, data),
                "data": json.dumps(
                    {
                        "original_file_name": file_name,
                        "name": table_name,
                        "source_type": "file",
                    }
                ).encode("utf-8"),
            },
            headers=self._session_headers,
        )
        if result.status != 200:
            raise Exception(
                f"Failed to upload file. Status: {result.status}. Data: {result.data.decode('utf-8', errors='backslashreplace')}"
            )


class DataServerConnection:
    def __init__(
        self, http_url: str, http_user: Optional[str], http_password: Optional[str]
    ):
        """
        Creates a connection to the data server.
        """
        # Not using mysql connection for now (had issues with pymysql not giving
        # errors when the connection was closed by the server).
        self._http_connection = _HttpConnectionHelper(
            http_url, http_user or "", http_password or ""
        )

    def login(self) -> None:
        self._http_connection.login()

    def query(
        self,
        database_name: str,
        query: str,
        params: Optional[dict[str, str | int | float] | list[str | int | float]] = None,
    ) -> "ResultSet":
        """
        Simple API to query a database in MindsDB with parameters. Always loads
        all the results into memory.

        Args:
            database_name: The name of the database to query.
            query: The SQL query to execute.
            params: A list of parameters to inject into the query.

        Returns:
            ResultSet: The query result as a ResultSet.
        """
        from .result_set import ResultSet
        from .sql_handling import (
            build_query_from_dict_params,
            build_query_from_list_params,
        )

        if isinstance(params, list):
            query = build_query_from_list_params(query, params)
        else:
            query = build_query_from_dict_params(query, params)

        result = self._http_connection.run_sql(query, database_name)
        if result is None:
            raise RuntimeError(
                "Unexpected result from the data server (expected table but received just 'ok')"
            )

        columns, rows = result
        return ResultSet([x.lower() for x in columns], [tuple(row) for row in rows])

    # It's actually the same thing internally, so we can just alias it.
    predict = query

    def run_sql(
        self,
        sql: str,
        params: Optional[dict[str, str | int | float] | list[str | int | float]] = None,
    ) -> None:
        database_name = ""
        from .sql_handling import (
            build_query_from_dict_params,
            build_query_from_list_params,
        )

        if isinstance(params, list):
            sql = build_query_from_list_params(sql, params)
        else:
            sql = build_query_from_dict_params(sql, params)

        self._http_connection.run_sql(sql, database_name)

    def upload_file(self, file_path: Path, table_name: str) -> None:
        self._http_connection.upload_file(file_path, table_name)
