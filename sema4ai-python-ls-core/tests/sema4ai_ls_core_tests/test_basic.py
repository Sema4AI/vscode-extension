import pytest


def test_isinstance_name():
    from sema4ai_ls_core.basic import isinstance_name

    class A:
        pass

    class B(A):
        pass

    class C(B):
        pass

    for _ in range(2):
        assert isinstance_name(B(), "B")
        assert isinstance_name(B(), "A")
        assert isinstance_name(B(), "object")

        assert isinstance_name(B(), ("A", "C"))

        assert not isinstance_name(B(), "C")
        assert not isinstance_name(B(), ("C", "D"))


def test_notify_about_import(tmpdir):
    import io
    import sys

    from sema4ai_ls_core.basic import notify_about_import
    from sema4ai_ls_core.core_log import configure_logger

    tmpdir.join("my_test_notify_about_import.py").write_text("a = 10", "utf-8")
    path = sys.path[:]
    sys.path.append(str(tmpdir))
    try:
        s = io.StringIO()
        with configure_logger("", 1, s):
            with notify_about_import("my_test_notify_about_import"):
                import my_test_notify_about_import  # type: ignore  #noqa

                assert my_test_notify_about_import.a == 10
        assert (
            "import my_test_notify_about_import  # type: ignore  #noqa" in s.getvalue()
        )
        assert (
            "'my_test_notify_about_import' should not be imported in this process"
            in s.getvalue()
        )
    finally:
        sys.path = path


@pytest.mark.parametrize(
    "scenario",
    [
        "monitor",
        "future",
        "timeout",
    ],
)
def test_launch_and_return_future(scenario):
    import sys
    from concurrent.futures import CancelledError, TimeoutError

    from sema4ai_ls_core.basic import ProcessResultStatus, launch_and_return_future
    from sema4ai_ls_core.jsonrpc.monitor import Monitor

    code = """
import time
while True:
    time.sleep(1)
"""
    monitor = Monitor()
    future = launch_and_return_future(
        [sys.executable, "-c", code],
        environ={},
        cwd=".",
        monitor=monitor,
        timeout=1 if scenario == "timeout" else 30,
    )

    with pytest.raises(TimeoutError):
        future.result(1)

    if scenario == "monitor":
        monitor.cancel()
    elif scenario == "future":
        future.cancel()
    elif scenario == "timeout":
        pass
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    if scenario == "monitor":
        result = future.result(1)
        assert result.returncode != 0
        assert result.status == ProcessResultStatus.CANCELLED
    elif scenario == "future":
        with pytest.raises(CancelledError):
            future.result(1)
    elif scenario == "timeout":
        result = future.result()
        assert result.returncode != 0
        assert result.status == ProcessResultStatus.TIMED_OUT
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    process = future._process_weak_ref()
    assert process.poll() is not None
