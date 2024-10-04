import os

import pytest
from sema4ai_code_tests.protocols import IRobocorpLanguageServerClient
from sema4ai_ls_core import uris
from sema4ai_ls_core.ep_resolve_interpreter import IInterpreterInfo


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
        [{"action_package": uris.from_fs_path(ws_root_path)}],
    )["result"]["result"]
    for entry in result:
        entry["uri"] = os.path.basename(entry["uri"])
    data_regression.check(result)


class ResolveInterpreterCurrentEnv:
    def get_interpreter_info_for_doc_uri(self, doc_uri) -> IInterpreterInfo | None:
        """
        Provides a customized interpreter for a given document uri.
        """
        import sys

        from sema4ai_ls_core.ep_resolve_interpreter import DefaultInterpreterInfo

        return DefaultInterpreterInfo("interpreter_id", sys.executable, {}, [])


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


@pytest.mark.parametrize(
    "scenario",
    [
        just_oauth2,
        multiple_types,
        just_enum,
        table_type,
        complex_type,
    ],
)
def test_list_actions_full(tmpdir, scenario, data_regression) -> None:
    from pathlib import Path

    from sema4ai_ls_core import pluginmanager
    from sema4ai_ls_core.ep_resolve_interpreter import EPResolveInterpreter
    from sema4ai_ls_core.jsonrpc.monitor import Monitor

    from sema4ai_code.robo.collect_actions import (
        collect_actions_full_and_slow,
        extract_info,
    )

    root = Path(tmpdir) / "check"
    root.mkdir(parents=True, exist_ok=True)

    pm = pluginmanager.PluginManager()
    pm.register(EPResolveInterpreter, ResolveInterpreterCurrentEnv)

    action_path = root / "my_action.py"
    action_path.write_text(scenario(), "utf-8")

    uri = uris.from_fs_path(str(root))

    monitor = Monitor()
    result = collect_actions_full_and_slow(pm, uri, monitor)
    assert result.success, result.message
    lst = result.result
    assert lst
    action_name_to_schema = extract_info(lst, str(root))
    data_regression.check(action_name_to_schema)
