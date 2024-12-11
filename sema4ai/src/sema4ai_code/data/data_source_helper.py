import typing
from pathlib import Path

from sema4ai_ls_core.protocols import DatasourceInfoTypedDict

if typing.TYPE_CHECKING:
    from sema4ai_code.data.data_server_connection import DataServerConnection


class DataSourceHelper:
    def __init__(
        self,
        root_path: Path,
        datasource: "DatasourceInfoTypedDict",
        connection: "DataServerConnection",
    ):
        # model datasource: a model created in a project
        self._is_model_datasource = False

        # table datasource: it's either a file or a custom engine that creates a table
        self._is_table_datasource = False
        self._root_path = root_path
        self._custom_sql: tuple[str, ...] | None = None

        self.datasource = datasource
        self.connection = connection

        # Do as the last thing as it may update fields (such as custom_sql, is_model_datasource, is_table_datasource, etc.)
        error = self._compute_validation_error()
        self._validation_errors: tuple[str, ...] = (error,) if error else ()

    @property
    def is_model_datasource(self) -> bool:
        return self._is_model_datasource

    @property
    def is_table_datasource(self) -> bool:
        return self._is_table_datasource

    @property
    def custom_sql(self) -> tuple[str, ...] | None:
        return self._custom_sql

    @property
    def root_path(self) -> Path:
        return self._root_path

    def get_validation_errors(self) -> tuple[str, ...]:
        return self._validation_errors

    def _compute_validation_error(self) -> str | None:
        datasource = self.datasource
        datasource_name = datasource.get("name")

        if not datasource_name:
            return "It was not possible to statically discover the name of a datasource. Please specify the name of the datasource directly in the datasource definition."

        datasource_engine = datasource.get("engine")
        if not datasource_engine:
            return f"It was not possible to statically discover the engine of a datasource ({datasource_name}). Please specify the engine of the datasource directly in the datasource definition."

        created_table = datasource.get("created_table")
        model_name = datasource.get("model_name")

        if created_table and model_name:
            return f"DataSource: {datasource_name} - The datasource cannot specify both the created_table and model_name fields."

        if datasource_engine == "custom":
            # Custom engine must have sql
            error = self._update_custom_sql(datasource)
            if error:
                return error

            if created_table:
                self._is_model_datasource = True
            elif model_name:
                self._is_model_datasource = True
            return None

        if datasource_engine == "files":
            if not created_table:
                return f"DataSource: {datasource_name} - The files engine requires the created_table field to be set."

            relative_path = datasource.get("file")
            if not relative_path:
                return f"DataSource: {datasource_name} - The files engine requires the file field to be set."

            full_path = Path(self.root_path) / relative_path
            if not full_path.exists():
                return f"DataSource: {datasource_name} - The files engine requires the file field to be set to a valid file path. File does not exist: {full_path}"

            self._is_table_datasource = True
            return None
        else:
            if created_table:
                return f"DataSource: {datasource_name} - The engine: {datasource_engine} does not support the created_table field."

        if datasource_engine.startswith("prediction:"):
            error = self._update_custom_sql(datasource)
            if error:
                return error

            if not model_name:
                return f"DataSource: {datasource_name} - The prediction engine requires the model_name field to be set."
            self._is_model_datasource = True
            return None
        else:
            if model_name:
                return f"DataSource: {datasource_name} - The engine: {datasource_engine} does not support the model_name field."

        return None

    def _update_custom_sql(self, datasource: "DatasourceInfoTypedDict") -> None | str:
        datasource_name = datasource.get("name")
        setup_sql = datasource.get("setup_sql")
        setup_sql_files = datasource.get("setup_sql_files")
        if not setup_sql and not setup_sql_files:
            return f"DataSource: {datasource_name} - The custom engine requires the setup_sql or setup_sql_files field to be set."

        if setup_sql_files and setup_sql:
            return f"DataSource: {datasource_name} - The custom engine cannot specify both the setup_sql and setup_sql_files fields."

        if setup_sql:
            if isinstance(setup_sql, str):
                setup_sql = [setup_sql]
            if not isinstance(setup_sql, list):
                return f"DataSource: {datasource_name} - The setup_sql field must be a string or a list of strings."
            self._custom_sql = tuple(setup_sql)
        else:
            if isinstance(setup_sql_files, str):
                setup_sql_files = [setup_sql_files]
            if not isinstance(setup_sql_files, list):
                return f"DataSource: {datasource_name} - The setup_sql_files field must be a string or a list of strings."

            # read the files
            sqls = []
            for file in setup_sql_files:
                full_path = Path(self.root_path) / file
                if not full_path.exists():
                    return f"DataSource: {datasource_name} - The setup_sql_files field must be set to a list of valid file paths. File does not exist: {full_path}"
                txt = full_path.read_text()
                sqls.append(txt)
            self._custom_sql = tuple(sqls)
        return None
