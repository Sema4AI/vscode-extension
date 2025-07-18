# Original work Copyright 2017 Palantir Technologies, Inc. (MIT)
# See ThirdPartyNotices.txt in the project root for license information.
# All modifications Copyright (c) Robocorp Technologies Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http: // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools
import os
import sys
import threading
from collections.abc import Callable
from concurrent.futures import Future
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Optional, TypeVar

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.jsonrpc.exceptions import JsonRpcRequestCancelled
from sema4ai_ls_core.options import DEFAULT_TIMEOUT
from sema4ai_ls_core.protocols import IMonitor

PARENT_PROCESS_WATCH_INTERVAL = 3  # 3 s


def as_str(s) -> str:
    if isinstance(s, bytes):
        return s.decode("utf-8", "replace")
    return str(s)


log = get_logger(__name__)


def list_to_string(value):
    return ",".join(value) if isinstance(value, list) else value


def _popen(cmdline, **kwargs):
    import subprocess

    try:
        return subprocess.Popen(cmdline, **kwargs)
    except Exception:
        log.exception("Error running: %s", (" ".join(cmdline)))
        return None


def _call(cmdline, **kwargs):
    import subprocess

    try:
        subprocess.check_call(cmdline, **kwargs)
    except Exception:
        log.exception("Error running: %s", (" ".join(cmdline)))
        return None


_track_pids_to_exit = set()
_watching_thread_global = None


def exit_when_pid_exists(pid):
    _track_pids_to_exit.add(pid)
    global _watching_thread_global
    if _watching_thread_global is None:
        import time

        def watch_parent_process():
            # exit when any of the ids we're tracking exit.
            from sema4ai_ls_core.process import is_process_alive

            while True:
                for pid in _track_pids_to_exit:
                    if not is_process_alive(pid):
                        # Note: just exit since the parent process already
                        # exited.
                        log.info(
                            f"Force-quit process: %s because parent: %s exited",
                            os.getpid(),
                            pid,
                        )
                        os._exit(0)

                time.sleep(PARENT_PROCESS_WATCH_INTERVAL)

        _watching_thread_global = threading.Thread(target=watch_parent_process, args=())
        _watching_thread_global.daemon = True
        _watching_thread_global.start()


F = TypeVar("F", bound=Callable[..., Any])


def overrides(method: Any) -> Callable[[F], F]:
    """
    Meant to be used as

    class B:
        @overrides(A.m1)
        def m1(self):
            pass
    """

    @functools.wraps(method)
    def wrapper(func):
        if func.__name__ != method.__name__:
            msg = f"Wrong @override: {func.__name__!r} expected, but overwriting {method.__name__!r}."
            raise AssertionError(msg)

        return func

    return wrapper


def implements(method: Any) -> Callable[[F], F]:
    @functools.wraps(method)
    def wrapper(func):
        if func.__name__ != method.__name__:
            msg = f"Wrong @implements: {func.__name__!r} expected, but implementing {method.__name__!r}."
            raise AssertionError(msg)

        return func

    return wrapper


def log_and_silence_errors(logger, return_on_error=None):
    def inner(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except JsonRpcRequestCancelled:
                logger.info("Cancelled handling: %s", func)
                raise  # Don't silence cancelled exceptions
            except Exception:
                logger.exception("Error calling: %s", func)
                return return_on_error

        return new_func

    return inner


def log_but_dont_silence_errors(logger):
    def inner(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except JsonRpcRequestCancelled:
                logger.info("Cancelled handling: %s", func)
                raise  # Don't silence cancelled exceptions
            except:
                logger.exception("Error calling: %s", func)
                raise

        return new_func

    return inner


@contextmanager
def after(obj, method_name, callback):
    original_method = getattr(obj, method_name)

    @functools.wraps(original_method)
    def new_method(*args, **kwargs):
        ret = original_method(*args, **kwargs)
        callback(*args, **kwargs)
        return ret

    setattr(obj, method_name, new_method)
    try:
        yield
    finally:
        setattr(obj, method_name, original_method)


@contextmanager
def before(obj, method_name, callback):
    original_method = getattr(obj, method_name)

    @functools.wraps(original_method)
    def new_method(*args, **kwargs):
        callback(*args, **kwargs)
        ret = original_method(*args, **kwargs)
        return ret

    setattr(obj, method_name, new_method)
    try:
        yield
    finally:
        setattr(obj, method_name, original_method)


def check_min_version(version: str, min_version: tuple[int, int]) -> bool:
    """
    :param version:
        This is the version of robotframework.

    :param min_version:
        This is the minimum version to match.

    :return bool:
        True if version >= min_versiond and False otherwise.
    """
    try:
        v = tuple(int(x) for x in version.split("."))
    except Exception:
        return False

    return v >= min_version


def wait_for_condition(condition, msg=None, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0):
    """
    Note: wait_for_expected_func_return is usually a better API to use as
    the error message is automatically built.
    """
    import time

    curtime = time.time()

    while True:
        if condition():
            break
        if timeout is not None and (time.time() - curtime > timeout):
            error_msg = f"Condition not reached in {timeout} seconds"
            if msg is not None:
                error_msg += "\n"
                if callable(msg):
                    error_msg += msg()
                else:
                    error_msg += str(msg)

            raise TimeoutError(error_msg)
        time.sleep(sleep)


def wait_for_non_error_condition(
    generate_error_or_none, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0
):
    import time

    curtime = time.time()

    while True:
        error_msg = generate_error_or_none()
        if error_msg is None:
            break

        if timeout is not None and (time.time() - curtime > timeout):
            raise TimeoutError(
                f"Condition not reached in {timeout} seconds\n{error_msg}"
            )
        time.sleep(sleep)


def wait_for_expected_func_return(
    func, expected_return, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0
):
    def check():
        found = func()
        if found != expected_return:
            return f"Expected: {expected_return}. Found: {found}"

        return None

    wait_for_non_error_condition(check, timeout, sleep)


def isinstance_name(obj, classname, memo={}):
    """
    Checks if a given object is instance of a class with the given name.
    """
    if classname.__class__ in (list, tuple):
        for c in classname:
            if isinstance_name(obj, c):
                return True
        return False

    cls = obj.__class__
    key = (cls, classname)
    try:
        return memo[key]
    except KeyError:
        if cls.__name__ == classname:
            memo[key] = True
        else:
            for check in obj.__class__.__mro__:
                if check.__name__ == classname:
                    memo[key] = True
                    break
            else:
                memo[key] = False

        return memo[key]


def build_subprocess_kwargs(cwd, env, **kwargs) -> dict:
    import subprocess

    startupinfo = None
    if sys.platform == "win32":
        # We don't want to show the shell on windows!
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        startupinfo = startupinfo

    if cwd:
        kwargs["cwd"] = cwd
    if env:
        kwargs["env"] = env
    kwargs["startupinfo"] = startupinfo
    return kwargs


def make_unique(lst):
    seen = set()
    return [x for x in lst if x not in seen and not seen.add(x)]


@lru_cache(maxsize=3000)
def normalize_filename(filename):
    return os.path.abspath(os.path.normpath(os.path.normcase(filename)))


class _RestoreCtxManager:
    def __init__(self, original_import):
        self._original_import = original_import

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        import builtins

        builtins.__import__ = self._original_import


def notify_about_import(import_name):
    """
    :param str import_name:
        The name of the import we don't want in this process.

    Use case: `robot` should not be imported in the Robot Framework Language
    Server process. It should only be imported in the subprocess which is
    spawned specifically for that robot framework version (we should only parse
    the AST at those subprocesses -- if the import is done at the main process
    something needs to be re-engineered to forward the request to a subprocess).

    If used as a context manager restores the previous __import__.
    """
    import builtins

    original_import = builtins.__import__

    import_name_with_dot = import_name + "."

    def new_import(name, *args, **kwargs):
        if name == import_name or name.startswith(import_name_with_dot):
            import traceback
            from io import StringIO

            stream = StringIO()
            stream.write(f"'{name}' should not be imported in this process.\nStack:\n")

            traceback.print_stack(file=stream)

            log.critical(stream.getvalue())

        return original_import(name, *args, **kwargs)

    builtins.__import__ = new_import
    return _RestoreCtxManager(original_import)


class ProcessResultStatus(Enum):
    FINISHED = 0
    TIMED_OUT = 1
    CANCELLED = 2


@dataclass
class ProcessRunResult:
    stdout: str
    stderr: str
    returncode: int
    status: ProcessResultStatus


def launch_and_return_future(
    cmd,
    environ,
    cwd,
    timeout=100,
    stdin: bytes = b"\n",
    monitor: Optional[IMonitor] = None,
) -> "Future[ProcessRunResult]":
    """
    Launches a process and returns a future that can be used to wait for the process to
    finish and get its output. If the monitor is cancelled, the timeout is reached or
    regular completion is reached, a ProcessRunResult will be returned with the status
    set accordingly.

    If the future itself is cancelled the process will be killed and an exception
    will set in the future.
    """
    import subprocess
    import weakref

    full_env = dict(os.environ)
    full_env.update(environ)
    kwargs: dict = build_subprocess_kwargs(
        cwd,
        full_env,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )

    def stream_reader(stream, write_to):
        try:
            for line in iter(stream.readline, b""):
                if not line:
                    break
                write_to.write(line.decode("utf-8", "replace"))
        except Exception as e:
            log.error("Error reading stream:", e)

    log.info(f"Running: {' '.join(str(x) for x in cmd)}")
    process = subprocess.Popen(cmd, **kwargs)

    # Not sure why, but (just when running in VSCode) something as:
    # launching sys.executable actually got stuck unless a \n was written
    # (even if stdin was closed it wasn't enough).
    # -- note: this may be particular to my machine (fabioz), but it
    # may also be related to VSCode + Windows 11 + Windows Defender + python
    _stdin_write(process, stdin)

    import io

    stderr_contens = io.StringIO()
    stdout_contens = io.StringIO()

    threads = [
        threading.Thread(
            target=stream_reader,
            args=(process.stdout, stdout_contens),
            name="stream_reader_stdout",
        ),
        threading.Thread(
            target=stream_reader,
            args=(process.stderr, stderr_contens),
            name="stream_reader_stderr",
        ),
    ]
    for t in threads:
        t.start()

    future: "Future[ProcessRunResult]" = Future()

    force_status: ProcessResultStatus | None = None

    def kill_if_running(*args, **kwargs):
        from sema4ai_ls_core.process import kill_process_and_subprocesses

        if process.poll() is None:  # i.e.: still running.
            kill_process_and_subprocesses(process.pid)

    def on_monitor_cancelled():
        nonlocal force_status
        force_status = ProcessResultStatus.CANCELLED
        kill_if_running()

    if monitor is not None:
        monitor.add_listener(on_monitor_cancelled)

    def cancel_if_needed(*args, **kwargs):
        if future.cancelled():
            kill_if_running()

    future.add_done_callback(cancel_if_needed)
    setattr(future, "_process_weak_ref", weakref.ref(process))

    def report_output():
        nonlocal force_status
        from concurrent.futures import InvalidStateError
        from subprocess import TimeoutExpired

        try:
            try:
                process.wait(timeout)
            except TimeoutExpired:
                log.info("Timeout expired, killing process.")
                kill_if_running()  # if it was still running after the timeout elapses, kill it.
                try:
                    for t in threads:
                        t.join(2)
                except Exception:
                    pass
                future.set_result(
                    ProcessRunResult(
                        stdout=stdout_contens.getvalue(),
                        stderr=stderr_contens.getvalue(),
                        returncode=process.poll(),
                        status=force_status
                        if force_status is not None
                        else ProcessResultStatus.TIMED_OUT,
                    )
                )
                return

            try:
                for t in threads:
                    t.join(2)
            except Exception:
                pass

            if not future.cancelled():
                future.set_result(
                    ProcessRunResult(
                        stdout=stdout_contens.getvalue(),
                        stderr=stderr_contens.getvalue(),
                        returncode=process.poll(),
                        status=force_status
                        if force_status is not None
                        else ProcessResultStatus.FINISHED,
                    )
                )
        except BaseException as e:
            try:
                future.set_exception(e)
            except InvalidStateError:
                pass  # That's fine, in a race condition the future may already be cancelled.

    threading.Thread(target=report_output, daemon=True).start()
    return future


def _stdin_write(process, input):
    if process.stdin is None:
        if sys.platform == "win32":
            log.critical(
                "Unable to write to stdin in `_stdin_write` because process.stdin is None (sema4ai_ls_core/basic.py)."
            )
        return

    import errno

    if input:
        try:
            process.stdin.write(input)
        except BrokenPipeError:
            pass  # communicate() must ignore broken pipe errors.
        except OSError as exc:
            if exc.errno == errno.EINVAL:
                # bpo-19612, bpo-30418: On Windows, stdin.write() fails
                # with EINVAL if the child process exited or if the child
                # process is still running but closed the pipe.
                pass
            else:
                raise

    try:
        process.stdin.close()
    except BrokenPipeError:
        pass  # communicate() must ignore broken pipe errors.
    except OSError as exc:
        if exc.errno == errno.EINVAL:
            pass
        else:
            raise


def slugify(value, allow_unicode=False):
    """
    Gotten from django: https://github.com/django/django/blob/main/django/utils/text.py

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    import re
    import unicodedata

    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
