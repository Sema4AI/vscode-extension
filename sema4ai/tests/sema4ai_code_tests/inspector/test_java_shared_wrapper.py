"""
The Java Access Bridge dll (and its event pump thread) is shared by all the Java
inspectors of the process, but each one must keep its own selected Java VM: a
picker of a previous inspector may still be running after a `killMe`.
"""

import threading
from ctypes import c_long

import pytest

pytest.importorskip("win32process")  # JABWrapper is Windows only.


class _FakeDll:
    """Records the (vmID, context) pairs of the native calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def getAccessibleChildFromContext(self, vm_id, context, index):
        self.calls.append((vm_id.value, context.value))
        return context


class _FakeEventPumpThread:
    def __init__(self, wrapper) -> None:
        self._wrapper = wrapper

    def get_wrapper(self):
        return self._wrapper


def _shared_wrapper(dll):
    from JABWrapper.jab_types import JavaObject
    from JABWrapper.jab_wrapper import JavaAccessBridgeWrapper

    # As created by the event pump thread (without loading a real dll).
    wrapper = JavaAccessBridgeWrapper.__new__(JavaAccessBridgeWrapper)
    wrapper.ignore_callbacks = True
    wrapper._wab = dll
    wrapper._context_callbacks = {}
    wrapper._hwnd = None
    wrapper._vmID = c_long()
    wrapper.context = JavaObject()
    return wrapper


def _new_inspector(shared_wrapper):
    from sema4ai_code.inspector.java.robocorp_java._inspector import (
        ElementInspector,
    )

    inspector = ElementInspector()
    inspector._event_pump_thread = _FakeEventPumpThread(shared_wrapper)
    return inspector


def _select_vm(wrapper, vm_id: int, context: int) -> None:
    from JABWrapper.jab_types import JavaObject

    # What `switch_window_by_title()` does once the window is found.
    wrapper._vmID = c_long(vm_id)
    wrapper.context = JavaObject(context)


def test_inspectors_share_the_dll_but_not_the_selected_vm() -> None:
    dll = _FakeDll()
    shared = _shared_wrapper(dll)

    wrapper_a = _new_inspector(shared).jab_wrapper
    wrapper_b = _new_inspector(shared).jab_wrapper

    assert wrapper_a is not wrapper_b
    assert wrapper_a._wab is dll and wrapper_b._wab is dll

    _select_vm(wrapper_b, vm_id=2, context=200)
    assert wrapper_a._vmID.value == 0
    assert shared._vmID.value == 0


def test_picker_scan_of_previous_inspector_keeps_its_vm() -> None:
    from JABWrapper.jab_types import JavaObject

    dll = _FakeDll()
    shared = _shared_wrapper(dll)

    # Inspector A selects JVM A and its picker starts scanning.
    wrapper_a = _new_inspector(shared).jab_wrapper
    _select_vm(wrapper_a, vm_id=1, context=100)

    resume_scan = threading.Event()

    def picker_scan():
        assert resume_scan.wait(5)
        wrapper_a.get_child_context(JavaObject(100), 0)

    scan_thread = threading.Thread(target=picker_scan)
    scan_thread.start()
    try:
        # killMe: a new inspector selects JVM B while the scan is paused.
        wrapper_b = _new_inspector(shared).jab_wrapper
        _select_vm(wrapper_b, vm_id=2, context=200)
    finally:
        resume_scan.set()
        scan_thread.join(5)

    assert dll.calls == [(1, 100)]
    assert (2, 100) not in dll.calls
