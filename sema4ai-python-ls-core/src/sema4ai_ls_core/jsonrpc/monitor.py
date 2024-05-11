from sema4ai_ls_core.protocols import IMonitor
from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


class Monitor(object):
    def __init__(self, title: str = ""):
        self._title = title
        self._cancelled: bool = False

    def cancel(self) -> None:
        if self._title:
            log.info("Cancelled: %s", self._title)
        self._cancelled = True

    def check_cancelled(self) -> None:
        if self._cancelled:
            from sema4ai_ls_core.jsonrpc.exceptions import JsonRpcRequestCancelled

            raise JsonRpcRequestCancelled()

    def __typecheckself__(self) -> None:
        from sema4ai_ls_core.protocols import check_implements

        _: IMonitor = check_implements(self)
