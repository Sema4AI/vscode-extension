from __future__ import annotations

import errno
import itertools
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Sequence, TypeVar, Union

from sema4ai_ls_core.callbacks import Callback
from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import LaunchActionResult, Sentinel

log = get_logger(__name__)

T = TypeVar("T")

PathLike = Union[str, Path]

IS_WINDOWS = sys.platform == "win32"


if sys.platform == "win32":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_SYNCHRONIZE = 0x00100000
    DWORD = ctypes.c_uint32
    BOOL = ctypes.c_int
    LPVOID = ctypes.c_void_p
    HANDLE = LPVOID

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [DWORD, BOOL, DWORD]
    OpenProcess.restype = HANDLE

    WaitForSingleObject = kernel32.WaitForSingleObject
    WaitForSingleObject.argtypes = [HANDLE, DWORD]
    WaitForSingleObject.restype = DWORD

    WAIT_TIMEOUT = 0x00000102
    WAIT_ABANDONED = 0x00000080
    WAIT_OBJECT_0 = 0
    WAIT_FAILED = 0xFFFFFFFF

    def is_process_alive(pid):
        """Check whether the process with the given pid is still alive.

        Running `os.kill()` on Windows always exits the process, so it can't be used to check for an alive process.
        see: https://docs.python.org/3/library/os.html?highlight=os%20kill#os.kill

        Hence ctypes is used to check for the process directly via windows API avoiding any other 3rd-party dependency.

        Args:
            pid (int): process ID

        Returns:
            bool: False if the process is not alive or don't have permission to check, True otherwise.
        """
        process = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid)
        if process != 0:
            try:
                wait_result = WaitForSingleObject(process, 0)
                if wait_result == WAIT_TIMEOUT:
                    return True
            finally:
                kernel32.CloseHandle(process)
        return False

else:

    def _is_process_alive(pid):
        """Check whether the process with the given pid is still alive.

        Args:
            pid (int): process ID

        Returns:
            bool: False if the process is not alive or don't have permission to check, True otherwise.
        """
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == errno.ESRCH:
                return False  # No such process.
            elif e.errno == errno.EPERM:
                return True  # permission denied.
            else:
                log.info("Unexpected errno: %s", e.errno)
                return False
        else:
            return True

    def is_process_alive(pid):
        if _is_process_alive(pid):
            # Check if zombie...
            try:
                cmd = ["ps", "-p", str(pid), "-o", "stat"]
                try:
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                except Exception:
                    log.exception("Error calling: %s.", " ".join(cmd))
                else:
                    stdout, _ = process.communicate()
                    stdout = stdout.decode("utf-8", "replace")
                    lines = [line.strip() for line in stdout.splitlines()]
                    if len(lines) > 1:
                        if lines[1].startswith("Z"):
                            return False  # It's a zombie
            except Exception:
                log.exception("Error checking if process is alive.")

            return True
        return False


def _stream_reader(stream, on_output):
    try:
        for line in iter(stream.readline, b""):
            if not line:
                break
            try:
                on_output(line)
            except Exception as e:
                log.error("Error reporting output line: %s", e)
    except Exception as e:
        log.error("Error reading stream: %s", e)


def _start_reader_threads(process, on_stdout, on_stderr):
    threads = []
    if on_stdout is not None:
        threads.append(
            threading.Thread(
                target=_stream_reader,
                args=(process.stdout, on_stdout),
                name="stream_reader_stdout",
            )
        )

    if on_stderr is not None:
        threads.append(
            threading.Thread(
                target=_stream_reader,
                args=(process.stderr, on_stderr),
                name="stream_reader_stderr",
            )
        )

    for t in threads:
        t.start()


class Process:
    _UID = itertools.count(0)

    def __init__(
        self,
        args: List[str],
        cwd: Optional[PathLike] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        self._args = args
        self._uid = next(self._UID)
        self._cwd = cwd or Path.cwd()
        self._env = {**os.environ, **(env or {})}
        self._proc: Optional[subprocess.Popen] = None
        self.on_stderr = Callback()
        self.on_stdout = Callback()

    def is_alive(self):
        if self._proc is None:
            raise RuntimeError(
                "Process is still None (start() not called before is_alive)."
            )

        return is_process_alive(self._proc.pid)

    @property
    def returncode(self):
        if self._proc is None:
            raise RuntimeError(
                "Process is still None (start() not called before returncode)."
            )
        return self._proc.poll()

    def join(self, timeout: Optional[int] = None):
        if self._proc is None:
            raise RuntimeError(
                "Process is still None (start() not called before join)."
            )
        self._proc.wait(timeout=timeout)

    def start(
        self, read_stderr: bool = True, read_stdout: bool = True, **kwargs
    ) -> None:
        new_kwargs = build_subprocess_kwargs(
            self._cwd, self._env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        new_kwargs.update(kwargs)
        log.info(
            "Subprocess start [args=%s,cwd=%s,uid=%d]", self._args, self._cwd, self._uid
        )
        proc = self._proc = _popen_raise(self._args, **new_kwargs)
        log.info("Subprocess started [pid=%s,uid=%d]", proc.pid, self._uid)
        on_stdout = None
        if read_stdout:
            on_stdout = self._on_stdout

        on_stderr = None
        if read_stderr:
            on_stderr = self._on_stderr
        _start_reader_threads(self._proc, on_stdout, on_stderr)

    def _on_stderr(self, line):
        if len(self.on_stderr) > 0:
            self.on_stderr(line.decode("utf-8", "replace"))

    def _on_stdout(self, line):
        if len(self.on_stdout) > 0:
            self.on_stdout(line.decode("utf-8", "replace"))

    def stop(self) -> None:
        if not self._proc:
            return
        if self._proc.poll() is not None:
            return
        if not self.is_alive():
            return

        log.debug("Subprocess kill [pid=%s,uid=%d]", self._proc.pid, self._uid)
        kill_process_and_subprocesses(self._proc.pid)

    @property
    def pid(self):
        return self._proc.pid


def build_subprocess_kwargs(cwd, env, **kwargs) -> dict:
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


def build_python_launch_env(new_env_vars: dict[str, str]) -> dict[str, str]:
    """
    Args:
        new_env_vars: If empty this means that this is an unmanaged env. In this
            case the environment used will be the same one used to run the
            action server itself.
    """
    if sys.platform == "win32":
        env = {}
        for k, v in os.environ.items():
            env[k.upper()] = v
    else:
        env = dict(os.environ)

    if new_env_vars:
        env.pop("PYTHONPATH", "")
        env.pop("PYTHONHOME", "")
        env.pop("VIRTUAL_ENV", "")

    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env.update(new_env_vars)

    # for k, v in env.items():
    #     if k in new_env_vars:
    #         print("FROM RCC", k, "=", v)
    # for k, v in env.items():
    #     if k not in new_env_vars:
    #         print("FROM SYS", k, "=", v)

    return env


def _popen(cmdline, **kwargs):
    try:
        popen = subprocess.Popen(cmdline, **kwargs)
        # Not sure why, but (just when running in VSCode) something as:
        # launching sys.executable actually got stuck unless a \n was written
        # (even if stdin was closed it wasn't enough).
        # -- note: this may be particular to my machine (fabioz), but it
        # may also be related to VSCode + Windows 11 + Windows Defender + python
        _stdin_write(popen, b"\n")
        return popen
    except Exception:
        log.exception("Error running: %s", (" ".join(cmdline)))
        return None


def _popen_raise(cmdline, **kwargs):
    try:
        popen = subprocess.Popen(cmdline, **kwargs)
        # Not sure why, but (just when running in VSCode) something as:
        # launching sys.executable actually got stuck unless a \n was written
        # (even if stdin was closed it wasn't enough).
        # -- note: this may be particular to my machine (fabioz), but it
        # may also be related to VSCode + Windows 11 + Windows Defender + python
        _stdin_write(popen, b"\n")
        return popen
    except Exception:
        log.exception("Error running: %s", (" ".join(cmdline)))
        raise


def _stdin_write(process, input):
    if process.stdin is not None:
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


def _call(cmdline, **kwargs):
    try:
        subprocess.check_call(cmdline, **kwargs)
    except Exception:
        log.exception("Error running: %s", (" ".join(cmdline)))
        return None


def _kill_process_and_subprocess_linux(pid):
    initial_pid = pid

    def list_children_and_stop_forking(ppid):
        children_pids = []
        _call(
            ["kill", "-STOP", str(ppid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        list_popen = _popen(
            ["pgrep", "-P", str(ppid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if list_popen is not None:
            stdout, _ = list_popen.communicate()
            for line in stdout.splitlines():
                line = line.decode("ascii").strip()
                if line:
                    pid = str(line)
                    children_pids.append(pid)
                    # Recursively get children.
                    children_pids.extend(list_children_and_stop_forking(pid))
        return children_pids

    previously_found = set()

    for _ in range(50):  # Try this at most 50 times before giving up.
        children_pids = list_children_and_stop_forking(initial_pid)
        found_new = False

        for pid in children_pids:
            if pid not in previously_found:
                found_new = True
                previously_found.add(pid)
                _call(
                    ["kill", "-KILL", str(pid)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

        if not found_new:
            break

    # Now, finish the initial one.
    _call(
        ["kill", "-KILL", str(initial_pid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def kill_process_and_subprocesses(pid):
    log.debug("Killing process and subprocesses of: %s", pid)
    from subprocess import CalledProcessError

    if sys.platform == "win32":
        args = ["taskkill", "/F", "/PID", str(pid), "/T"]
        retcode = subprocess.call(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
        )
        if retcode not in (0, 128, 255):
            raise CalledProcessError(retcode, args)
    else:
        _kill_process_and_subprocess_linux(pid)


class IProgressReporter(Protocol):
    @property
    def cancelled(self) -> bool:
        pass

    def set_additional_info(self, additional_info: str) -> None:
        """
        The progress reporter shows the title and elapsed time automatically.

        With this API it's possible to add additional info for the user to see.
        """


def check_output_interactive(
    *popenargs,
    timeout=None,
    progress_reporter: Optional[IProgressReporter] = None,
    on_stderr=lambda *args, **kwargs: None,
    on_stdout=lambda *args, **kwargs: None,
    **kwargs,
) -> bytes:
    """
    This has the same API as subprocess.check_output, but allows us to work with
    the contents being generated by the subprocess before the subprocess actually
    finishes.

    :param on_stderr:
        A callable(string) (called from another thread) whenever output is
        written with stderr contents.

    :param on_stdout:
        A callable(string) (called from another thread) whenever output is
        written with stdout contents.

    :return: the stdout generated by the command.
    """
    if kwargs.get("stdout", subprocess.PIPE) != subprocess.PIPE:
        raise AssertionError("stdout must be subprocess.PIPE")

    if kwargs.get("stderr", subprocess.PIPE) != subprocess.PIPE:
        # We could potentially also accept `subprocess.STDOUT`, but let's leave
        # this as a future improvement for now.
        raise AssertionError("stderr must be subprocess.PIPE")

    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE
    kwargs["stdin"] = subprocess.PIPE  # Needed to write '\n' to stdin.

    stdout_contents: List[bytes] = []
    stderr_contents: List[bytes] = []

    def stream_reader(stream, callback, contents_list: List[bytes]):
        for line in iter(stream.readline, b""):
            if not line:
                break
            contents_list.append(line)
            callback(line)

    def check_progress_cancelled(process, progress_reporter: IProgressReporter):
        try:
            while process.poll() is None:
                try:
                    process.wait(1)
                except BaseException:
                    if progress_reporter.cancelled:
                        retcode = process.poll()
                        if retcode is None:
                            msg_str = f"Progress was cancelled (Process pid: {process.pid} was killed).\n"
                            msg = msg_str.encode("utf-8")
                            log.info(msg_str)
                            stderr_contents.insert(0, msg)
                            stderr_contents.append(msg)
                            on_stderr(msg)
                            kill_process_and_subprocesses(process.pid)
        except BaseException:
            log.exception("Error checking that progress was cancelled.")

    with _popen_raise(*popenargs, **kwargs) as process:  # Already writes \n to stdin
        threads = [
            threading.Thread(
                target=stream_reader,
                args=(process.stdout, on_stdout, stdout_contents),
                name="stream_reader_stdout",
            ),
            threading.Thread(
                target=stream_reader,
                args=(process.stderr, on_stderr, stderr_contents),
                name="stream_reader_stderr",
            ),
        ]
        if progress_reporter is not None:
            t = threading.Thread(
                target=check_progress_cancelled,
                args=(process, progress_reporter),
                name="check_progress_cancelled",
            )
            t.start()

        for t in threads:
            t.start()

        retcode: Optional[int]
        try:
            try:
                retcode = process.wait(timeout)
            except BaseException:
                # i.e.: KeyboardInterrupt / TimeoutExpired
                retcode = process.poll()

                if retcode is None:
                    # It still hasn't completed: kill it.
                    try:
                        kill_process_and_subprocesses(process.pid)
                    except BaseException:
                        log.exception("Error killing pid: %s" % (process.pid,))

                    retcode = process.wait()
                raise

        finally:
            for t in threads:
                t.join()

        if retcode:
            raise subprocess.CalledProcessError(
                retcode,
                process.args,
                output=b"".join(stdout_contents),
                stderr=b"".join(stderr_contents),
            )

        return b"".join(stdout_contents)


def launch(
    args: Union[Sequence[str], str],
    timeout: float = 35,
    error_msg: str = "",
    mutex_name=None,
    cwd: Optional[str] = None,
    log_errors=True,
    stderr=Sentinel.SENTINEL,
    show_interactive_output: bool = False,
    hide_in_log: Optional[str] = None,
    env: Optional[dict] = None,
    **kwargs,
) -> LaunchActionResult:
    """
    Returns a LaunchActionResult where the result is the stdout of the executed command.

    :param log_errors:
        If false, errors won't be logged (i.e.: should be false when errors
        are expected).

    :param stderr:
        If given sets the stderr redirection (by default it's subprocess.PIPE,
        but users could change it to something as subprocess.STDOUT).

    :param hide_in_log:
        A string which should be hidden in logs.
    """
    import time
    from subprocess import (
        CalledProcessError,
        TimeoutExpired,
        check_output,
        list2cmdline,
    )

    from sema4ai_ls_core.basic import as_str, build_subprocess_kwargs
    from sema4ai_ls_core.constants import NULL
    from sema4ai_ls_core.core_log import get_log_level

    if stderr is Sentinel.SENTINEL:
        stderr = subprocess.PIPE

    new_env = os.environ.copy()
    new_env.pop("PYTHONPATH", "")
    new_env.pop("PYTHONHOME", "")
    new_env.pop("VIRTUAL_ENV", "")
    new_env["PYTHONIOENCODING"] = "utf-8"
    new_env["PYTHONUNBUFFERED"] = "1"

    if env:
        new_env.update(env)

    suprocesskwargs: dict = build_subprocess_kwargs(
        cwd, new_env, stderr=stderr, **kwargs
    )
    cmdline: str
    if isinstance(args, str):
        # When shell=True args should be a string.
        cmdline = args
    else:
        cmdline = list2cmdline([str(x) for x in args])

    try:
        if mutex_name:
            from sema4ai_ls_core.system_mutex import timed_acquire_mutex
        else:
            timed_acquire_mutex = NULL
        with timed_acquire_mutex(mutex_name, timeout=15):
            if get_log_level() >= 2:
                msg = f"Running: {cmdline}"
                if hide_in_log:
                    msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")

                log.debug(msg)

            curtime = time.time()

            boutput: bytes
            # We have 2 main modes here: one in which we can print the output
            # interactively while the command is running and another where
            # we only print if some error happened.
            if not show_interactive_output:
                # Not sure why, but (just when running in VSCode) something as:
                # launching sys.executable actually got stuck unless a \n was written
                # (even if stdin was closed it wasn't enough).
                # -- note: this may be particular to my machine (fabioz), but it
                # may also be related to VSCode + Windows 11 + Windows Defender + python
                suprocesskwargs["input"] = b"\n"
                boutput = check_output(args, timeout=timeout, **suprocesskwargs)
            else:
                from sema4ai_ls_core.progress_report import (
                    get_current_progress_reporter,
                )

                progress_reporter = get_current_progress_reporter()

                def on_output(content):
                    try:
                        sys.stderr.buffer.write(content)

                        # Besides writing it to stderr, let's also add more
                        # info to our current progress (if any).
                        if progress_reporter is not None:
                            progress_reporter.set_additional_info(
                                content.decode("utf-8", "replace")
                            )
                    except Exception:
                        log.exception("Error reporting interactive output.")

                boutput = check_output_interactive(
                    args,
                    timeout=timeout,
                    on_stderr=on_output,
                    on_stdout=on_output,
                    progress_reporter=progress_reporter,
                    **suprocesskwargs,
                )

    except CalledProcessError as e:
        stdout = as_str(e.stdout)
        stderr = as_str(e.stderr)
        msg = f"Error running: {cmdline}.\n\nStdout: {stdout}\nStderr: {stderr}"
        if hide_in_log:
            msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")

        if log_errors:
            log.exception(msg)
        if not error_msg:
            return LaunchActionResult(cmdline, success=False, message=msg)
        else:
            additional_info = [error_msg]
            if stdout or stderr:
                if stdout and stderr:
                    additional_info.append("\nDetails: ")
                    additional_info.append("\nStdout")
                    additional_info.append(stdout)
                    additional_info.append("\nStderr")
                    additional_info.append(stderr)

                elif stdout:
                    additional_info.append("\nDetails: ")
                    additional_info.append(stdout)

                elif stderr:
                    additional_info.append("\nDetails: ")
                    additional_info.append(stderr)

            return LaunchActionResult(
                cmdline, success=False, message="".join(additional_info)
            )

    except TimeoutExpired:
        msg = f"Timed out ({timeout}s elapsed) when running: {cmdline}"
        log.exception(msg)
        return LaunchActionResult(cmdline, success=False, message=msg)

    except Exception:
        msg = f"Error running: {cmdline}"
        log.exception(msg)
        return LaunchActionResult(cmdline, success=False, message=msg)

    output = boutput.decode("utf-8", "replace")

    do_log_as_info = not show_interactive_output and (
        (log_errors and get_log_level() >= 1) or get_log_level() >= 2
    )
    if do_log_as_info:
        elapsed = time.time() - curtime
        msg = f"Output from: {cmdline} (took: {elapsed:.2f}s): {output}"
        if hide_in_log:
            msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")
        log.info(msg)

    return LaunchActionResult(cmdline, success=True, message=None, result=output)
