from sema4ai_ls_core.protocols import IMonitor, IMonitorListener
from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


class Monitor(object):
    def __init__(self, title: str = ""):
        self._title = title
        self._cancelled: bool = False
        self._listeners: tuple[IMonitorListener, ...] = ()

    def add_listener(self, listener):
        if self._cancelled:
            listener()
        else:
            self._listeners += (listener,)

    def cancel(self) -> None:
        if self._title:
            log.info("Cancelled: %s", self._title)
        self._cancelled = True

        for listener in self._listeners:
            listener()
        self._listeners = ()

    def check_cancelled(self) -> None:
        if self._cancelled:
            from sema4ai_ls_core.jsonrpc.exceptions import JsonRpcRequestCancelled

            raise JsonRpcRequestCancelled()

    def __typecheckself__(self) -> None:
        from sema4ai_ls_core.protocols import check_implements

        _: IMonitor = check_implements(self)
