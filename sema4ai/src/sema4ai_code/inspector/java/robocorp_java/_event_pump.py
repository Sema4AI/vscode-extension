import ctypes
import platform
import queue
import threading
from collections.abc import Callable
from concurrent import futures

from JABWrapper.jab_wrapper import JavaAccessBridgeWrapper
from sema4ai_ls_core.core_log import get_logger

log = get_logger(__name__)


REMOVE_FROM_QUEUE = 0x0001


class _DllCallsInPumpThread:
    """
    Proxy for the Java Access Bridge dll (`JavaAccessBridgeWrapper._wab`) which
    runs every call in the event pump thread (the thread which initialized the
    dll and which pumps its messages).

    The dll isn't thread-safe: calling it from another thread while the pump
    thread is still registering the Java VMs (i.e.: the first listing right
    after it's started) may raise an access violation inside the dll, which
    leaves an internal lock held by the calling thread. Calls from that thread
    still work (the lock is reentrant), but any other thread (i.e.: the Java
    inspector thread recreated after a `killMe`) would hang forever.
    """

    def __init__(self, dll, event_pump_thread: "EventPumpThread") -> None:
        self._dll = dll
        self._event_pump_thread = event_pump_thread

    def __getattr__(self, name: str):
        func = getattr(self._dll, name)
        if not callable(func):
            return func

        event_pump_thread = self._event_pump_thread

        def call_in_pump_thread(*args):
            return event_pump_thread.run_in_thread(func, *args)

        return call_in_pump_thread


class EventPumpThread(threading.Thread):
    def __init__(
        self,
    ) -> None:
        super().__init__()
        # Jab wrapper needs to be part of the thread that pumps the window events
        self._jab_wrapper: JavaAccessBridgeWrapper = None
        self._future: futures.Future = futures.Future()
        self._quit_event_loop = threading.Event()
        # Calls to the dll to be done in this thread (see: _DllCallsInPumpThread).
        self._calls: "queue.Queue[tuple[futures.Future, Callable, tuple]]" = (
            queue.Queue()
        )

    def run_in_thread(self, func: Callable, *args):
        if threading.current_thread() is self:
            return func(*args)

        if not self.is_alive():
            raise RuntimeError("The Java Access Bridge event pump is not running.")

        future: futures.Future = futures.Future()
        self._calls.put((future, func, args))
        return future.result()

    def _run_call(self, call: "tuple[futures.Future, Callable, tuple]") -> None:
        future, func, args = call
        try:
            result = func(*args)
        except BaseException as e:
            future.set_exception(e)
        else:
            future.set_result(result)

    def _run_pending_calls(self) -> bool:
        ran = False
        while True:
            try:
                call = self._calls.get_nowait()
            except queue.Empty:
                return ran
            self._run_call(call)
            ran = True

    def _pump_background(self) -> bool:
        try:
            PeekMessage = ctypes.windll.user32.PeekMessageW  # type: ignore
            TranslateMessage = ctypes.windll.user32.TranslateMessage  # type: ignore
            DispatchMessage = ctypes.windll.user32.DispatchMessageW  # type: ignore

            message = ctypes.byref(ctypes.wintypes.MSG())
            # Nonblocking API to get windows window events from the queue.
            # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-peekmessagea
            # Use non blocing API here so that the thread can quit.
            if PeekMessage(message, 0, 0, 0, REMOVE_FROM_QUEUE):
                TranslateMessage(message)
                log.debug(f"Dispatching msg={repr(message)}")
                DispatchMessage(message)
                return True
        except Exception as err:
            log.error(f"Pump error: {err}")
        return False

    def run(self) -> None:
        if platform.system() != "Windows":
            return

        # Raise the error to the main thread from here (otherwise `get_wrapper()`
        # would wait forever).
        try:
            self._jab_wrapper = JavaAccessBridgeWrapper(ignore_callbacks=True)
        except Exception as e:
            import os

            dll = os.environ.get("RC_JAVA_ACCESS_BRIDGE_DLL")
            log.exception(f"Error loading the Java Access Bridge: {dll}")
            self._future.set_exception(
                RuntimeError(
                    f"Unable to load the Java Access Bridge ({dll}): {e}. Make sure it's "
                    "a 64-bit Java installation that can be read by the current user, or "
                    "set the RC_JAVA_ACCESS_BRIDGE_DLL environment variable to another "
                    "WindowsAccessBridge-64.dll and restart VS Code."
                )
            )
            return
        # All the calls to the dll are done in this thread.
        self._jab_wrapper._wab = _DllCallsInPumpThread(self._jab_wrapper._wab, self)
        self._future.set_result(self._jab_wrapper)
        try:
            while not self._quit_event_loop.is_set():
                ran_calls = self._run_pending_calls()
                if self._pump_background() or ran_calls:
                    continue
                # The pump is non blocking. If there is no message in the queue
                # wait for 100 milliseconds until check again to prevent too
                # fast loop (but wake up right away when a dll call is requested).
                # The pump needs time to recover, otherwise it gets cluttered and hangs.
                # Possibly a limitation in the Java Access Bridge that needs investigating.
                try:
                    call = self._calls.get(timeout=0.1)
                except queue.Empty:
                    continue
                self._run_call(call)
        finally:
            # Don't leave callers waiting forever.
            while True:
                try:
                    future, _func, _args = self._calls.get_nowait()
                except queue.Empty:
                    break
                future.set_exception(
                    RuntimeError("The Java Access Bridge event pump was stopped.")
                )

    def stop(self):
        self._quit_event_loop.set()
        self._jab_wrapper = None
        if not self._future.done():
            self._future.cancel()

    def get_wrapper(self) -> JavaAccessBridgeWrapper:
        return self._future.result()


# The Java Access Bridge dll is a process-wide singleton, so it's initialized
# (`Windows_run()`) only once and the thread which owns it (which pumps its
# messages and does all the calls to it) is shared and kept alive for the whole
# process (and not recreated when the Java inspector is recreated after a `killMe`).
_shared_lock = threading.Lock()
_shared_event_pump_thread: EventPumpThread | None = None


def get_shared_event_pump_thread() -> EventPumpThread:
    global _shared_event_pump_thread
    with _shared_lock:
        if _shared_event_pump_thread is None:
            _shared_event_pump_thread = EventPumpThread()
            _shared_event_pump_thread.daemon = True
            _shared_event_pump_thread.start()
        return _shared_event_pump_thread


def new_wrapper_sharing_dll(
    wrapper: JavaAccessBridgeWrapper,
) -> JavaAccessBridgeWrapper:
    """
    Provides a new wrapper which shares the dll of the given one (and so, its
    event pump thread: `Windows_run()` isn't called again), but with its own
    state for the selected window / Java VM (`_hwnd`, `_vmID`, `context`).

    Each `ElementInspector` needs its own: when the Java inspector is recreated
    (i.e.: after a `killMe`) a picker of the previous one may still be running
    and it must keep using the Java VM it was started for (and not the one
    selected afterwards).
    """
    import copy
    from ctypes import c_long

    from JABWrapper.jab_types import JavaObject

    ret = copy.copy(wrapper)
    ret._context_callbacks = {}
    ret._hwnd = None
    ret._vmID = c_long()
    ret.context = JavaObject()
    return ret


def reset_shared_event_pump_thread(event_pump_thread: EventPumpThread) -> None:
    """
    To be called only if the Java Access Bridge could not be loaded (so that
    it's possible to retry later on).
    """
    global _shared_event_pump_thread
    with _shared_lock:
        if _shared_event_pump_thread is event_pump_thread:
            event_pump_thread.stop()
            _shared_event_pump_thread = None
