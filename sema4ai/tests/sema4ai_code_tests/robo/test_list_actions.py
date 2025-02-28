import os
from pathlib import Path

import pytest
from sema4ai_code_tests.protocols import IRobocorpLanguageServerClient
from sema4ai_ls_core import uris
from sema4ai_ls_core.protocols import ActionInfoTypedDict, DatasourceInfoTypedDict

from sema4ai_code.robo.collect_actions import get_metadata


@pytest.mark.parametrize("action_name", ["get_churn_data", "predict_churn"])
def test_get_action_signature(cases, data_regression, action_name):
    from sema4ai_ls_core.jsonrpc.monitor import Monitor

    from sema4ai_code.robo.collect_actions_ast import get_action_signature

    action_package_path = Path(cases.get_path("action_package", must_exist=True))
    action_relative_path = "data_actions.py"
    monitor = Monitor()
    result = get_action_signature(
        action_relative_path, action_package_path, action_name, monitor
    )
    assert result.success, result.message
    data_regression.check(result.result)


def test_list_actions_and_datasources_simple(cases, data_regression):
    action_package_path = Path(cases.get_path("action_package", must_exist=True))

    from sema4ai_code.robo.collect_actions_ast import iter_actions_and_datasources

    result = list(
        iter_actions_and_datasources(action_package_path, collect_datasources=True)
    )
    result = _fix_result(result)

    data_regression.check(result)


def _fix_result(result: list[ActionInfoTypedDict | DatasourceInfoTypedDict]):
    for entry in result:
        entry["uri"] = os.path.basename(entry["uri"])

    result = sorted(result, key=lambda x: x["name"])
    return result


def test_list_actions(
    language_server_initialized: IRobocorpLanguageServerClient,
    ws_root_path,
    cases,
    data_regression,
):
    from sema4ai_code import commands

    cases.copy_to("action_package", ws_root_path)

    language_server = language_server_initialized
    result = language_server.execute_command(
        commands.SEMA4AI_LIST_ACTIONS_INTERNAL,
        [
            {
                "action_package": uris.from_fs_path(ws_root_path),
                "collect_datasources": True,
            }
        ],
    )["result"]["result"]
    result = _fix_result(result)

    data_regression.check(result)


def multiple_types() -> str:
    return """
from sema4ai.actions import action, Secret
from typing import List
import pydantic
from enum import Enum

class SomeEnum(str, Enum):
    A = "a"
    B = "b"

class AnotherModel(pydantic.BaseModel):
    name: str
    age: int

class UseModel(pydantic.BaseModel):
    name: str
    lst: List[int]
    other: dict[str, int]
    another: AnotherModel
    some_enum: SomeEnum

@action
def my_action(a:int,b:float,c:str,d:bool, model: UseModel, secret: Secret) -> str:
    return "result"
"""


def just_enum() -> str:
    return """
from sema4ai.actions import action, Secret
from typing import List
import pydantic
from enum import Enum

class SomeEnum(str, Enum):
    A = "a"
    B = "b"


class UseModel(pydantic.BaseModel):

    some_enum: SomeEnum

@action
def my_action(model: UseModel) -> str:
    return "result"
"""


def complex_type() -> str:
    return """
from pydantic import BaseModel, Field
from sema4ai.actions import action, Secret, OAuth2Secret
from typing import List, Literal, Annotated
import pydantic


class Link(BaseModel):
    href: str = Field(description="The URL of the link")
    text: str = Field(description="The text of the link")


class Links(BaseModel):
    links: Annotated[list[Link], Field(description="A list of links", default=[])]


class Option(BaseModel):
    value: str = Field(description="The value of the option")
    text: str = Field(description="The text of the option")


class FormElement(BaseModel):
    type: str = Field(description="The type of the form element")
    text: str = Field(description="The text of the form element", default="")
    placeholder: str = Field(
        description="The placeholder of the form element", default=""
    )
    aria_label: str = Field(
        description="The aria label of the form element", default=""
    )
    id: str = Field(description="The id of the form element", default="")
    name: str = Field(description="The name of the form element", default="")
    class_: str = Field(description="The class of the form element", default="")
    value_type: str = Field(
        description="The type of the form element value", default=""
    )
    value_to_fill: str = Field(
        description="The value to fill in the form element", default=""
    )
    options: Annotated[
        list[Option], Field(description="A list of select options", default=[])
    ]
    count: int = Field(description="The count of the form element", default=1)


class Form(BaseModel):
    url: str = Field(description="The URL of the website")
    elements: Annotated[
        list[FormElement], Field(description="A list of form elements", default=[])
    ]


class WebPage(BaseModel):
    url: str = Field(description="The URL of the website")
    text_content: str = Field(description="The text content of the website")
    form: Form
    links: Links


class DownloadedFile(BaseModel):
    content: str = Field(description="The content of the downloaded file")
    filepath: str = Field(description="The path of the downloaded file")
    status: str = Field(description="The status of the download")
    request_status: int = Field(description="The status of the request")
    content_type: str = Field(description="The content type of the file")
    content_length: int = Field(description="The size of the content in bytes")

@action
def my_action(entry: WebPage) -> str:
    return "result"
"""


def table_type() -> str:
    return """
from sema4ai.actions import action, Secret, OAuth2Secret
from typing import List, Literal
import pydantic

from typing import Annotated

from pydantic import BaseModel, Field


class Row(BaseModel):
    cells: Annotated[list[str], Field(description="Row cells")]


class Table(BaseModel):
    rows: Annotated[list[Row], Field(description="The rows that need to be added")]

@action
def my_action(entry: Table) -> str:
    return "result"
"""


def just_oauth2() -> str:
    return """
from sema4ai.actions import action, Secret, OAuth2Secret
from typing import List, Literal
import pydantic


@action
def my_action(google_secret: OAuth2Secret[
        Literal["google"],
        list[
            Literal[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ]
        ],
    ]) -> str:
    return "result"
"""


def bug_form_data() -> str:
    return """
from sema4ai.actions import action, Secret, Response
import os
from typing import List, Annotated
from pydantic import BaseModel, Field


class SearchService(BaseModel):
    name: Annotated[str, Field(
        description="The fully-qualified name of the Cortex Search Service (e.g., 'database.schema.cortex_search_service')."
    )]
    max_results: Annotated[int, Field(
        default=4, description="Maximum number of search results to provide."
    )]
    title_column: Annotated[str, Field(
        default="", description="Column to serve as the document title."
    )]
    id_column: Annotated[str, Field(
        default="", description="Column to serve as the document ID."
    )]
    filter: Annotated[dict, Field(
        default_factory=dict,
        description="A filter object to apply to the search results.",
    )]

class SemanticModel(BaseModel):
    file: str = Field(
        default="",
        description="Path to the semantic model YAML file (e.g., '@my_db.my_schema.my_stage/my_semantic_model.yaml').",
    )
    inline: str = Field(
        default="", description="A string containing the entire semantic model YAML."
    )


class SearchServicesList(BaseModel):
    services: Annotated[List[SearchService], Field(description="List of search services.")]


class SemanticModelsList(BaseModel):
    models: Annotated[List[SemanticModel], Field(description="List of semantic models.")]


@action
def send_chat_message_with_options(
    query: str,
    account_url: Secret,
    search_services: SearchServicesList = SearchServicesList(services=[]),
    semantic_models: SemanticModelsList = SemanticModelsList(models=[]),
    model: str = "llama3.1-405b",
    messages: list[dict] = [],
    debug: bool = False,
    authorization_token: Secret = Secret.model_validate(
        os.getenv("authorization_token", "")
    ),
) -> Response[str]:
    return Response(result="result")
"""


def data_types() -> str:
    return """
from datasources import ChurnPredictionDataSource, FileChurnDataSource
from sema4ai.actions import action, Secret, OAuth2Secret
from sema4ai.data import DataSource, query, predict
from typing import List, Literal
import pydantic

from typing import Annotated

from pydantic import BaseModel, Field


class Row(BaseModel):
    cells: Annotated[list[str], Field(description="Row cells")]


class Table(BaseModel):
    rows: Annotated[list[Row], Field(description="The rows that need to be added")]

@action
def my_action(entry: Table) -> str:
    return "result"

@query
def get_churn_data(datasource: FileChurnDataSource) -> str:
    result = datasource.query("SELECT * FROM churn LIMIT 10;")
    return result.to_markdown()

@predict
def predict_churn(
    datasource: Annotated[DataSource, ChurnPredictionDataSource | FileChurnDataSource],
    limit: int=10,
) -> str:
    sql = "SELECT churn FROM churn ORDER BY churn DESC"
    result = datasource.query(sql, params={"limit": limit})
    return result.to_markdown()
"""


def data_sources() -> str:
    return """
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

FileChurnDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="churn",
        file="files/customer-churn.csv",
        engine="files",
        description="Datasource which provides a table named 'churn' with customer churn data.",
    ),
]

ChurnPredictionDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which provides along with a table named `customer_churn_predictor`.",
        setup_sql="CREATE MODEL IF NOT EXISTS customer_churn_predictor FROM files (SELECT * FROM churn) PREDICT Churn;",
    ),
]
"""


def data_sources_2() -> str:
    return """
import typing
from sema4ai.data import DataSource, DataSourceSpec

FileChurnDataSource = typing.Annotated[
    DataSource,
    DataSourceSpec(
        created_table="churn",
        file="files/customer-churn.csv",
        engine="files",
        description="Datasource which provides a table named 'churn' with customer churn data.",
    ),
]

ChurnPredictionDataSource = typing.Annotated[
    DataSource,
    DataSourceSpec(
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which provides along with a table named `customer_churn_predictor`.",
        setup_sql="CREATE MODEL IF NOT EXISTS customer_churn_predictor FROM files (SELECT * FROM churn) PREDICT Churn;",
    ),
]
"""


def data_sources_3() -> str:
    return """
import typing
from sema4ai.data import DataSource, DataSourceSpec

ChurnPredictionDataSource = typing.Annotated[
    DataSource,
    DataSourceSpec(
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which provides along with a table named `customer_churn_predictor`.",
        setup_sql=["CREATE MODEL IF NOT EXISTS customer_churn_predictor FROM files (SELECT * FROM churn) PREDICT Churn;"],
    ),
]
"""


@pytest.mark.parametrize(
    "scenario",
    [
        data_sources,
        data_sources_2,
        data_sources_3,
    ],
)
def test_list_actions_and_datasources_mutiple(data_regression, scenario, tmpdir):
    action_package_path = Path(tmpdir)
    scenario_path = action_package_path / "data_sources.py"
    scenario_path.write_text(scenario(), "utf-8")

    from sema4ai_code.robo.collect_actions_ast import iter_actions_and_datasources

    result = list(
        iter_actions_and_datasources(action_package_path, collect_datasources=True)
    )
    result = _fix_result(result)

    data_regression.check(result)


@pytest.mark.parametrize(
    "scenario",
    [
        just_oauth2,
        multiple_types,
        just_enum,
        table_type,
        complex_type,
        bug_form_data,
    ],
)
def test_list_actions_full(
    tmpdir, actions_version_fixture, scenario, data_regression
) -> None:
    from sema4ai_code.robo.collect_actions import (
        collect_actions_full_and_slow,
        extract_info,
    )

    root: Path
    uri: str
    actions_version, pm, monitor, uri, root = actions_version_fixture

    action_path = root / "my_action.py"
    action_path.write_text(scenario(), "utf-8")

    uri = uris.from_fs_path(str(root))

    result = collect_actions_full_and_slow(pm, uri, str(root), monitor)
    assert result.success, result.message
    lst = result.result
    assert lst
    action_name_to_schema = extract_info(lst, str(root))
    data_regression.check(action_name_to_schema)


def normalize_paths(data, base_path):
    """
    Recursively replace dynamic paths in the data with a fixed placeholder.

    Args:
        data: The data structure to normalize (dict, list, str).
        base_path: The base temporary directory path to replace.

    Returns:
        Normalized data with paths replaced by a placeholder.
    """
    base_path = Path(base_path).resolve()  # Resolve to an absolute, normalized path

    def replace_path(value):
        try:
            path_value = Path(value).resolve()
            if base_path in path_value.parents or base_path == path_value:
                return (
                    str(path_value)
                    .replace(str(base_path), "<tmpdir>")
                    .replace("\\", "/")
                )
        except Exception:
            pass
        return value

    if isinstance(data, dict):
        return {k: normalize_paths(v, base_path) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_paths(item, base_path) for item in data]
    elif isinstance(data, str):
        return replace_path(data)
    return data


@pytest.mark.parametrize(
    "scenario",
    [complex_type, data_types],
)
def test_get_actions_metadata_above_version(
    data_regression, actions_version_fixture, scenario
) -> None:
    actions_version, pm, monitor, uri, root = actions_version_fixture
    if actions_version <= (1, 0, 1):
        pytest.skip("Skipping test for actions version <= 1.0.1")

    action_path = root / "my_action.py"
    action_path.write_text(scenario(), "utf-8")

    if "query" in scenario():
        datasources_path = root / "datasources.py"
        datasources_path.write_text(data_sources(), "utf-8")

    result = get_metadata(pm, uri, monitor)
    assert result.success, result.message

    lst = normalize_paths(result.result, str(root))
    assert lst

    data_regression.check(lst)


@pytest.mark.parametrize("scenario", [complex_type])
def test_get_actions_metadata_below_version(
    data_regression, actions_version_fixture, scenario
) -> None:
    actions_version, pm, monitor, uri, root = actions_version_fixture
    if actions_version > (1, 0, 1):
        pytest.skip("Skipping test for actions version > 1.0.1")

    action_path = root / "my_action.py"
    action_path.write_text(scenario(), "utf-8")

    result = get_metadata(pm, uri, monitor)
    assert result.success, result.message

    lst = normalize_paths(result.result, str(root))
    assert lst

    data_regression.check(lst)
