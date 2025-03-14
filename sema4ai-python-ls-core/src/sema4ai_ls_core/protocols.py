import sys
import threading
import typing
from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if typing.TYPE_CHECKING:
    # This would lead to a circular import, so, do it only when type-checking.
    from sema4ai_ls_core.callbacks import Callback
    from sema4ai_ls_core.lsp import (
        CodeLensTypedDict,
        CompletionItemTypedDict,
        CompletionResolveResponseTypedDict,
        CompletionsResponseTypedDict,
        DiagnosticsTypedDict,
        DocumentHighlightResponseTypedDict,
        HoverResponseTypedDict,
        PositionTypedDict,
        RangeTypedDict,
        ReferencesResponseTypedDict,
        ResponseTypedDict,
        TextDocumentContentChangeEvent,
        TextDocumentItem,
        TextDocumentTypedDict,
        TextEditTypedDict,
    )

# Hack so that we don't break the runtime on versions prior to Python 3.8.
if sys.version_info[:2] < (3, 8):

    class Protocol:
        pass

    class TypedDict:
        def __init_subclass__(self, *args, **kwargs):
            pass

else:
    from typing import Protocol, TypedDict


T = TypeVar("T")
Y = TypeVar("Y", covariant=True)


class Sentinel(Enum):
    SENTINEL = 0
    USE_DEFAULT_TIMEOUT = 1


def check_implements(x: T) -> T:
    """
    Helper to check if a class implements some protocol.

    :important: It must be the last method in a class due to
                https://github.com/python/mypy/issues/9266

        Example:

    def __typecheckself__(self) -> None:
        _: IExpectedProtocol = check_implements(self)

    Mypy should complain if `self` is not implementing the IExpectedProtocol.
    """
    return x


class IFuture(Generic[Y], Protocol):
    def result(self, timeout: int | None = None) -> Y:
        """Return the result of the call that the future represents.

        Args:
            timeout: The number of seconds to wait for the result if the future
                isn't done. If None, then there is no limit on the wait time.

        Returns:
            The result of the call that the future represents.

        Raises:
            CancelledError: If the future was cancelled.
            TimeoutError: If the future didn't finish executing before the given
                timeout.
            Exception: If the call raised then that exception will be raised.
        """

    def add_done_callback(self, fn: Callable[["IFuture"], Any]):
        """Attaches a callable that will be called when the future finishes.

        Args:
            fn: A callable that will be called with this future as its only
                argument when the future completes or is cancelled. The callable
                will always be called by a thread in the same process in which
                it was added. If the future has already completed or been
                cancelled then the callable will be called immediately. These
                callables are called in the order that they were added.
        """


class IEndPoint(Protocol):
    def notify(self, method: str, params: Any = None):
        """Send a JSON RPC notification to the client.

        Args:
            method (str): The method name of the notification to send
            params (any): The payload of the notification
        """

    def request(self, method: str, params=None) -> IFuture:
        """Send a JSON RPC request to the client.

        Args:
            method (str): The method name of the message to send
            params (any): The payload of the message

        Returns:
            Future that will resolve once a response has been received
        """

    def consume(self, message: dict):
        """Consume a JSON RPC message from the client.

        Args:
            message (dict): The JSON RPC message sent by the client
        """


class IProgressReporter(Protocol):
    @property
    def cancelled(self) -> bool:
        pass

    def set_additional_info(self, additional_info: str) -> None:
        """
        The progress reporter shows the title and elapsed time automatically.

        With this API it's possible to add additional info for the user to see.
        """


class CommunicationDropped:
    def __str__(self):
        return "CommunicationDropped"

    __repr__ = __str__


class IMessageMatcher(Generic[T], Protocol):
    event: threading.Event
    msg: T


class IIdMessageMatcher(Generic[T], Protocol):
    message_id: str
    event: threading.Event
    msg: T


class IResultMessage(TypedDict):
    jsonrpc: str  # Literal["2.0"] (not available on python 3.7)
    id: int
    result: Any


class IErrorTypedDict(TypedDict):
    code: int
    message: str


class IErrorMessage(TypedDict):
    jsonrpc: str  # Literal["2.0"] (not available on python 3.7)
    id: int
    error: IErrorTypedDict


COMMUNICATION_DROPPED = CommunicationDropped()


class IRequestCancellable(Protocol):
    def request_cancel(self, message_id) -> None:
        """
        Requests that some processing is cancelled.
        """


class IRequestHandler(Protocol):
    def __call__(self, request_name: str, msg_id: Any, params: Any) -> bool:
        """
        :param request_name:
            The name of the request to be handled.

        :param msg_id:
            The id of the message (to which a response should be generated).

        :param params:
            The parameters received in the request.

        :return:
            True if the request was handled (in which case, if multiple request
            handlers are registered, others aren't processed anymore) and False
            otherwise.
        """


class ILanguageServerClientBase(IRequestCancellable, Protocol):
    on_message: "Callback"

    def request_async(self, contents: dict) -> IIdMessageMatcher | None:
        """
        API which allows to wait for the message to complete.

        To use:
            message_matcher = client.request_async(contents)
            if message_matcher is not None:
                if message_matcher.event.wait(5):
                    ...
                    msg = message_matcher.msg
                else:
                    # Timed out

        :param contents:
            Something as:
            {"jsonrpc": "2.0", "id": msg_id, "method": method_name, "params": params}

        :return _MessageMatcher:
        """

    def request(
        self,
        contents,
        timeout: int | Sentinel = Sentinel.USE_DEFAULT_TIMEOUT,
        default: Any = COMMUNICATION_DROPPED,
    ) -> IResultMessage | IErrorMessage:
        """
        :param contents:
            {"jsonrpc": "2.0", "id": msg_id, "method": method_name, "params": params}

        :param timeout:
        :return:
            The returned message if everything goes ok.
            `default` if the communication dropped in the meanwhile and timeout was None.

        :raises:
            TimeoutError if the timeout was given and no answer was given at the available time
            (including if the communication was dropped).
        """

    def request_sync(self, method, **params):
        """
        This API is is a bit simpler than the `request` as it builds the message
        internally.

        It's the same thing as:

            return self.request(
                {
                    "jsonrpc": "2.0",
                    "id": self.next_id(),
                    "method": method,
                    "params": params,
                }
            )
        """

    def obtain_pattern_message_matcher(
        self, message_pattern: dict[str, str], remove_on_match: bool = True
    ) -> IMessageMatcher | None:
        """
        Can be used as:

        message_matcher = language_server.obtain_pattern_message_matcher(
            {"method": "textDocument/publishDiagnostics"}
        )
        """

    def obtain_id_message_matcher(self, message_id) -> IMessageMatcher:
        pass

    def register_request_handler(self, message: str, handler: IRequestHandler) -> None:
        pass

    def write(self, contents):
        pass

    def shutdown(self):
        pass

    def exit(self):
        pass


class IRobotFrameworkApiClient(ILanguageServerClientBase, Protocol):
    def initialize(
        self, msg_id=None, process_id=None, root_uri="", workspace_folders=()
    ):
        pass

    def get_version(self) -> str:
        pass

    def lint(self, doc_uri: str) -> "ResponseTypedDict":
        pass

    def request_lint(self, doc_uri: str) -> IIdMessageMatcher | None:
        pass

    def request_semantic_tokens_full(
        self, text_document: "TextDocumentTypedDict"
    ) -> IIdMessageMatcher | None:
        pass

    def forward(self, method_name, params):
        pass

    def forward_async(self, method_name, params) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def open(self, uri, version, source):
        pass

    def request_complete_all(
        self, doc_uri, line, col
    ) -> IIdMessageMatcher["CompletionsResponseTypedDict"] | None:
        """
        Completes: sectionName, keyword, variables
        :Note: async complete.
        """

    def request_resolve_completion_item(
        self, completion_item: "CompletionItemTypedDict"
    ) -> IIdMessageMatcher["CompletionResolveResponseTypedDict"] | None:
        pass

    def request_find_definition(self, doc_uri, line, col) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_flow_explorer_model(self, doc_uri) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_rename(
        self, doc_uri: str, line: int, col: int, new_name: str
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_prepare_rename(
        self, doc_uri: str, line: int, col: int
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_source_format(self, text_document, options) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_signature_help(
        self, doc_uri: str, line: int, col: int
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_folding_range(self, doc_uri: str) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_on_type_formatting(
        self, doc_uri: str, ch: str, line: int, col: int
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_selection_range(
        self, doc_uri: str, positions: list["PositionTypedDict"]
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_hover(
        self, doc_uri: str, line: int, col: int
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_references(
        self, doc_uri: str, line: int, col: int, include_declaration: bool
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_workspace_symbols(
        self, query: str | None = None
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def settings(self, settings: dict):
        pass

    def request_wait_for_full_test_collection(self) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_evaluatable_expression(
        self, doc_uri: str, position: "PositionTypedDict"
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_collect_robot_documentation(
        self,
        doc_uri,
        library_name: str | None = None,
        line: int | None = None,
        col: int | None = None,
    ) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """

    def request_rf_info(self, doc_uri: str) -> IIdMessageMatcher | None:
        """
        :Note: async complete.
        """


class EvaluatableExpressionTypedDict(TypedDict):
    """
    Note: this is actually a custom message return:

    "robot/provideEvaluatableExpression"
    """

    range: "RangeTypedDict"
    expression: str | None


class ITestInfoTypedDict(TypedDict):
    uri: str
    path: str
    name: str
    range: "RangeTypedDict"


class ITestInfoFromSymbolsCacheTypedDict(TypedDict):
    name: str
    range: "RangeTypedDict"


class ITestInfoFromUriTypedDict(TypedDict):
    uri: str
    testInfo: list[ITestInfoFromSymbolsCacheTypedDict]


class ILanguageServerClient(ILanguageServerClientBase, Protocol):
    pid: int | None

    DEFAULT_TIMEOUT: int | None = None

    def settings(self, settings: dict):
        """
        :param settings:
            Something as:
            {"settings": {"robot": {"pythonpath": [case4_path]}}}
        """

    def initialize(
        self, root_path: str, msg_id=None, process_id=None, initialization_options=None
    ):
        pass

    def change_workspace_folders(
        self, added_folders: list[str], removed_folders: list[str]
    ) -> None:
        pass

    def open_doc(self, uri: str, version: int = 1, text: str | None = None):
        """
        :param text:
            If None (default), the contents will be loaded from the disk.
        """

    def close_doc(self, uri: str):
        pass

    def change_doc(self, uri: str, version: int, text: str):
        pass

    def get_completions(
        self, uri: str, line: int, col: int
    ) -> "CompletionsResponseTypedDict":
        """
        :param uri:
            The uri for the request.
        :param line:
            0-based line.
        :param col:
            0-based col.
        """

    def get_completions_async(
        self, uri: str, line: int, col: int
    ) -> IIdMessageMatcher["CompletionsResponseTypedDict"] | None:
        """
        :param uri:
            The uri for the request.
        :param line:
            0-based line.
        :param col:
            0-based col.
        """

    def request_source_format(self, uri: str):
        """
        :param uri:
            The uri for the request.
        """

    def request_code_action(
        self, uri: str, line: int, col: int, endline: int, endcol: int
    ):
        """
        :param uri:
            The uri for the request.
        """

    def find_definitions(self, uri, line: int, col: int):
        """
        :param uri:
            The uri for the request.
        :param line:
            0-based line.
        :param col:
            0-based col.
        """

    def execute_command(
        self, command: str, arguments: list, timeout=None
    ) -> Mapping[str, Any]:
        pass

    def execute_command_async(
        self, command: str, arguments: list
    ) -> IIdMessageMatcher | None:
        pass

    def request_signature_help(self, uri: str, line: int, col: int):
        pass

    def request_hover(self, uri: str, line: int, col: int) -> "HoverResponseTypedDict":
        pass

    def request_text_document_highlight(
        self, uri: str, line: int, col: int
    ) -> "DocumentHighlightResponseTypedDict":
        pass

    def request_references(
        self, uri: str, line: int, col: int, include_declaration: bool
    ) -> "ReferencesResponseTypedDict":
        pass

    def request_folding_range(self, uri: str):
        pass

    def request_on_type_formatting(
        self, uri: str, ch: str, line: int, col: int
    ) -> "Optional[List[TextEditTypedDict]]":
        pass

    def request_selection_range(
        self, doc_uri: str, positions: list["PositionTypedDict"]
    ):
        pass

    def request_code_lens(self, uri: str):
        pass

    def request_resolve_code_lens(self, code_lens: "CodeLensTypedDict"):
        pass

    def request_document_symbol(self, uri: str):
        pass

    def request_rename(self, uri: str, line: int, col: int, new_name: str):
        pass

    def request_prepare_rename(self, uri: str, line: int, col: int):
        pass

    def request_provide_evaluatable_expression(
        self, uri: str, line: int, col: int
    ):  # -> "Response(dict) with EvaluatableExpressionTypedDict (result)"
        pass  # Note: not part of the language server spec (custom request).

    def request_workspace_symbols(self, query: str | None = None):
        pass

    def request_resolve_completion(
        self, completion_item: "CompletionItemTypedDict"
    ) -> "CompletionResolveResponseTypedDict":
        pass

    def hover(self, uri: str, line: int, col: int):
        """
        :param uri:
            The uri for the request.
        :param line:
            0-based line.
        :param col:
            0-based col.
        """


class IConfig(Protocol):
    def get_setting(
        self, key: str, expected_type: Any, default=Sentinel.SENTINEL
    ) -> Any:
        """
        :param key:
            The setting to be gotten (i.e.: my.setting.to.get)

        :param expected_type:
            The type which we're expecting.

        :param default:
            If given, return this value instead of throwing a KeyError.

        :raises:
            KeyError if the setting could not be found and default was not provided.
        """

    def update(self, settings: dict) -> None:
        """Recursively merge the given settings into the current settings."""

    def get_full_settings(self) -> dict:
        pass

    def set_override_settings(self, override_settings: dict) -> None:
        """
        Used to override settings with the keys given (note: any existing
        override setting will be removed and all the keys here will be set to
        override the initial settings -- use update_override_settings to keep
        other existing overrides).v
        """

    def update_override_settings(self, override_settings: dict) -> None:
        """
        Used to update existing override settings with the keys given.
        """

    def set_workspace_dir(self, workspace: str) -> None:
        pass


class ILog(Protocol):
    def critical(self, msg: str = "", *args: Any):
        pass

    def info(self, msg: str = "", *args: Any):
        pass

    def warn(self, msg: str = "", *args: Any):
        pass  # same as info

    def warning(self, msg: str = "", *args: Any):
        pass  # same as info

    def debug(self, msg: str = "", *args: Any):
        pass

    def exception(self, msg: str = "", *args: Any):
        pass

    def error(self, msg: str = "", *args: Any):
        pass  # same as exception


class IConfigProvider(Protocol):
    @property
    def config(self) -> IConfig:
        pass


class ILanguageServer(IConfigProvider):
    pass


class IDirCache(Protocol):
    """ """

    def store(self, key: Any, value: Any) -> None:
        """
        Persists the given key and value.

        :param key:
            The key to be persisted. It's repr(key) is used to calculate
            the key filename on the disk.

        :note that the values do a round-trip with json (so, caveats
        such as saving a tuple and loading a list apply).
        """

    def load(self, key: Any, expected_class: type) -> Any:
        """
        Loads a previously persisted value.

        If it doesn't exist, there's some error loading or the expected
        class doesn't match the loaded value a KeyError is thrown.

        :note: users should check that the cache value is what's expected when it's
           gotten (as the data may become corrupted on disk or may change across
           versions).
        """

    def discard(self, key: Any) -> None:
        """
        Removes some key from the cache.
        """


class IDocumentSelection(Protocol):
    doc: "IDocument"
    line: int
    col: int

    @property
    def offset_at_position(self):
        """Return the byte-offset pointed at by the given position."""
        pass

    @property
    def current_line(self) -> str:
        pass

    @property
    def line_to_column(self) -> str:
        pass

    @property
    def line_to_end(self) -> str:
        pass

    @property
    def word_at_column(self) -> str:
        pass

    @property
    def word_to_column(self) -> str:
        pass

    @property
    def word_from_column(self) -> str:
        pass


class IDocument(Protocol):
    uri: str
    version: str | None
    path: str

    immutable: bool

    def selection(self, line: int, col: int) -> IDocumentSelection:
        pass

    @property
    def source(self) -> str:
        pass

    @source.setter
    def source(self, source: str) -> None:
        pass

    def get_line(self, line: int) -> str:
        pass

    def offset_to_line_col(self, offset: int) -> tuple[int, int]:
        pass

    def get_range(self, line: int, col: int, endline: int, endcol: int) -> str:
        pass

    def get_last_line(self) -> str:
        pass

    def get_last_line_col(self) -> tuple[int, int]:
        pass

    def get_last_line_col_with_contents(self, contents: str) -> tuple[int, int]:
        pass

    def get_line_count(self) -> int:
        pass

    def apply_change(self, change: "TextDocumentContentChangeEvent") -> None:
        pass

    def is_source_in_sync(self) -> bool:
        """
        If the document is backed up by a file, returns true if the sources are
        in sync.
        """

    def find_line_with_contents(self, contents: str) -> int:
        pass

    def set_custom_data(self, key: str, value: Any) -> None:
        pass

    def get_custom_data(self, key: str) -> Any:
        pass


class IWorkspaceFolder(Protocol):
    uri: str
    name: str


class IWorkspace(Protocol):
    on_file_changed: "Callback"

    def on_changed_config(self, config: IConfig) -> None:
        pass

    @property
    def root_path(self):
        pass

    @property
    def root_uri(self):
        pass

    def iter_documents(self) -> Iterable[IDocument]:
        """
        Note: can only be called in the main thread.
        """

    def iter_folders(self) -> Iterable[IWorkspaceFolder]:
        """
        Note: the lock must be obtained when iterating folders.
        """

    def remove_document(self, uri: str) -> None:
        pass

    def put_document(self, text_document: "TextDocumentItem") -> IDocument:
        pass

    def get_document(self, doc_uri: str, accept_from_file: bool) -> IDocument | None:
        """
        Return a managed document if-present, otherwise, create one pointing at
        the disk if accept_from_file == True (if the file exists, and we're able to
        load it, otherwise, return None).
        """

    def get_folder_paths(self) -> list[str]:
        """
        Retuns the folders which are set as workspace folders.
        """

    def dispose(self):
        pass


class ITimeoutHandle(Protocol):
    def exec_on_timeout(self):
        pass


class IMonitorListener(Protocol):
    def __call__(self) -> Any:
        pass


class IMonitor(Protocol):
    def cancel(self) -> None:
        pass

    def check_cancelled(self) -> None:
        """
        raises JsonRpcRequestCancelled if cancelled.
        """

    def add_listener(self, listener: IMonitorListener):
        """
        Adds a listener that'll be called when the monitor is cancelled.
        """


class ActionResultDict(TypedDict, Generic[T]):
    success: bool
    message: None | (
        str
    )  # if success == False, this can be some message to show to the user
    result: T | None


class ActionResult(Generic[T]):
    success: bool
    message: None | (
        str
    )  # if success == False, this can be some message to show to the user
    result: T | None

    def __init__(
        self, success: bool, message: str | None = None, result: T | None = None
    ):
        self.success = success
        self.message = message
        self.result = result

    def as_dict(self) -> ActionResultDict[T]:
        return {"success": self.success, "message": self.message, "result": self.result}

    def __str__(self):
        return f"ActionResult(success={self.success!r}, message={self.message!r}, result={self.result!r})"

    __repr__ = __str__

    @classmethod
    def make_failure(cls, message: str) -> "ActionResult[T]":
        return ActionResult(success=False, message=message, result=None)

    @classmethod
    def make_success(cls, result: T) -> "ActionResult[T]":
        return ActionResult(success=True, message=None, result=result)


class LaunchActionResult(ActionResult[T]):
    # A string-representation of the command line.
    command_line: str

    def __init__(
        self,
        command_line: str,
        success: bool,
        message: str | None = None,
        result: T | None = None,
    ):
        ActionResult.__init__(self, success, message, result)
        self.command_line = command_line


class EnvEntry(TypedDict):
    key: str
    value: str


class LibraryVersionDict(TypedDict):
    library: str
    version: str


class LibraryVersionInfoDict(TypedDict):
    success: bool

    # if success == False, this can be some message to show to the user
    message: str | None

    # Note that if the library was found but the version doesn't match, the
    # result should still be provided.
    result: LibraryVersionDict | None


class ActionInfoTypedDict(TypedDict):
    range: "RangeTypedDict"
    name: str
    uri: str
    kind: str


class ModelStateTypedDict(TypedDict):
    status: Literal["complete", "error", "generating", "training", "creating"]
    error: str | None


class DatasourceInfoTypedDict(TypedDict):
    python_variable_name: str | None
    range: "RangeTypedDict"
    name: str
    uri: str
    kind: Literal["datasource"]
    engine: str
    model_name: str | None
    created_table: str | None
    setup_sql: str | list[str] | None
    setup_sql_files: list[str] | str | None
    description: str | None
    file: str | None


class DatasourceInfoWithStatusTypedDict(DatasourceInfoTypedDict):
    # --- Data Source State below ---
    # if None, it means it wasn't set yet
    configured: bool | None
    # if None, it means it wasn't set yet or it's not a model
    model_state: ModelStateTypedDict | None
    configuration_valid: bool | None
    configuration_errors: list[str] | None


class DataSourceStateDict(TypedDict):
    # Unconfigured Data Sources (kind of redundant now that DataSourceInfoTypedDict has the 'configured' field
    # but it's kept for backward compatibility).
    unconfigured_data_sources: list[DatasourceInfoWithStatusTypedDict]
    # Error messages on Data Sources.
    uri_to_error_messages: dict[str, list["DiagnosticsTypedDict"]]
    # All the required Data Sources.
    required_data_sources: list[DatasourceInfoWithStatusTypedDict]
    # All Data Sources in the data server.
    data_sources_in_data_server: list[str]
