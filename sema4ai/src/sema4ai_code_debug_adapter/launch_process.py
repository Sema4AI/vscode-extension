# Original work Copyright Fabio Zadrozny (EPL 1.0)
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

import itertools
import os.path
import threading
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import List, Optional

from sema4ai_ls_core.core_log import get_logger
from sema4ai_ls_core.protocols import IConfig

log = get_logger(__name__)


def _read_stream(stream, on_line, category):
    try:
        while True:
            output = stream.readline()
            if len(output) == 0:
                log.debug(f"Finished reading stream: {category}.\n")
                break
            output = output.decode("utf-8", errors="replace")
            on_line(output, category)
    except:
        log.exception("Error")


def _notify_on_exited_pid(on_exit, pid):
    try:
        import time

        from sema4ai_ls_core.process import is_process_alive

        log.debug("Waiting for pid to exit (_notify_on_exited_pid).")

        while True:
            if not is_process_alive(pid):
                break

            time.sleep(0.5)
        log.debug("pid exited (_notify_on_exited_pid).")
        on_exit()
    except:
        log.exception("Error")


class _DefaultConfigurationProvider:
    def __init__(self, config: IConfig):
        self.config = config


class LaunchProcess:
    __slots__ = [
        "_valid",
        "_cmdline",
        "_terminal",
        "_popen",
        "_weak_debug_adapter_comm",
        "__weakref__",
        "_cwd",
        "_run_in_debug_mode",
        "_debug_adapter_robot_target_comm",
        "_launch_response",
        "_next_seq",
        "_track_process_pid",
        "_sent_terminated",
        "_env",
        "_rcc_config_location",
        "_on_exit_callbacks",
    ]

    def __init__(  # pylint: disable=return-in-init
        self,
        request,
        launch_response,
        debug_adapter_comm,
        rcc_config_location: str | None,
    ) -> None:
        """
        :param LaunchRequest request:
        :param LaunchResponse launch_response:
        """
        import weakref

        from sema4ai_ls_core import yaml_wrapper
        from sema4ai_ls_core.basic import as_str
        from sema4ai_ls_core.config import Config
        from sema4ai_ls_core.core_log import get_log_level
        from sema4ai_ls_core.debug_adapter_core.dap.dap_schema import (
            OutputEvent,
            OutputEventBody,
        )
        from sema4ai_ls_core.protocols import ActionResult

        from sema4ai_code.protocols import IRobotYamlEnvInfo
        from sema4ai_code.rcc import Rcc
        from sema4ai_code.resolve_interpreter import get_conda_config_path
        from sema4ai_code_debug_adapter.constants import (
            TERMINAL_INTEGRATED,
            TERMINAL_NONE,
            VALID_TERMINAL_OPTIONS,
        )

        self._weak_debug_adapter_comm = weakref.ref(debug_adapter_comm)
        self._valid = True
        self._cmdline = []
        self._popen = None
        self._launch_response = launch_response
        self._next_seq = partial(next, itertools.count(0))
        self._track_process_pid = None
        self._sent_terminated = threading.Event()
        self._rcc_config_location = rcc_config_location
        self._on_exit_callbacks: list[Callable] = []

        def mark_invalid(message):
            launch_response.success = False
            launch_response.message = message
            self._valid = False

        robot_yaml = request.arguments.kwargs.get("robot")
        workspace_id = request.arguments.kwargs.get("workspaceId")
        self._terminal = request.arguments.kwargs.get("terminal", TERMINAL_INTEGRATED)

        task_name = request.arguments.kwargs.get("task", "")
        args = request.arguments.kwargs.get("args") or []
        if not isinstance(args, list):
            args = [args]
        args = [str(arg) for arg in args]

        env = {}
        request_env = request.arguments.kwargs.get("env")
        if isinstance(request_env, dict) and request_env:
            env.update(request_env)

        env = {as_str(key): as_str(value) for (key, value) in env.items()}

        self._env = env

        self._run_in_debug_mode = not request.arguments.noDebug

        if self._terminal not in VALID_TERMINAL_OPTIONS:
            return mark_invalid(
                "Invalid terminal option: %s (must be one of: %s)"
                % (self._terminal, VALID_TERMINAL_OPTIONS)
            )

        try:
            if robot_yaml is None:
                return mark_invalid("robot not provided in launch.")

            if not os.path.exists(robot_yaml):
                return mark_invalid(f"File: {robot_yaml} does not exist.")
        except:
            log.exception("Error")
            return mark_invalid(f"Error checking if robot ({robot_yaml}) exists.")

        self._cwd = os.path.dirname(robot_yaml)
        try:
            if self._cwd is not None:
                if not os.path.exists(self._cwd):
                    return mark_invalid(f"cwd specified does not exist: {self._cwd}")
        except:
            log.exception("Error")
            return mark_invalid(f"Error checking if cwd ({self._cwd}) exists.")

        if get_log_level() > 1:
            log.debug(f"Run in debug mode: {self._run_in_debug_mode}\n")

        try:
            config = Config()
            config_provider = _DefaultConfigurationProvider(config)
            rcc = Rcc(config_provider=config_provider)
            rcc_executable = rcc.get_rcc_location()

            if not os.path.exists(rcc_executable):
                return mark_invalid(f"Expected: {rcc_executable} to exist.")
        except:
            log.exception("Error")
            return mark_invalid("Error getting rcc executable location.")

        else:
            task_args = []
            if task_name:
                task_args.append("--task")
                task_args.append(task_name)

            env_json_path = Path(robot_yaml).parent / "devdata" / "env.json"
            exists_env_json = env_json_path.exists()

            # Compute the space name
            try:
                with open(robot_yaml) as stream:
                    yaml_contents = yaml_wrapper.load(stream)
            except:
                log.exception(f"Error loading {robot_yaml} as yaml.")
                return mark_invalid(f"Error loading {robot_yaml} as yaml.")

            if not isinstance(yaml_contents, dict):
                return mark_invalid(f"Expected dict as root in: {robot_yaml}.")

            parent: Path = Path(robot_yaml).parent

            conda_yaml_path = get_conda_config_path(
                parent, Path(robot_yaml), yaml_contents
            )
            if not conda_yaml_path:
                return mark_invalid(
                    f"Unable to resolve `condaConfigFile` related to {robot_yaml}"
                )

            try:
                conda_yaml_contents = conda_yaml_path.read_text("utf-8", "replace")
            except:
                log.exception(f"Error loading {conda_yaml_path} contents.")
                return mark_invalid(f"Error loading {conda_yaml_path} contents.")

            notify_event = threading.Event()

            import time

            def notify_elapsed_time():
                initial_time = time.time()

                notify_event.wait(5)
                if notify_event.is_set():
                    return

                output_event = OutputEvent(
                    OutputEventBody(
                        "Computing and creating environment (this can take some minutes)...\n",
                        category="stderr",
                    )
                )
                debug_adapter_comm.write_to_client_message(output_event)

                while True:
                    notify_event.wait(9.33)
                    elapsed = time.time() - initial_time
                    if not notify_event.is_set():
                        output_event = OutputEvent(
                            OutputEventBody(
                                f"Elapsed: {elapsed:.1f}s\n", category="stderr"
                            )
                        )
                        debug_adapter_comm.write_to_client_message(output_event)

            t = threading.Thread(target=notify_elapsed_time)
            t.daemon = True
            t.start()

            try:
                robot_yaml_env_info: ActionResult[IRobotYamlEnvInfo] = (
                    rcc.get_robot_yaml_env_info(
                        Path(robot_yaml),
                        conda_yaml_path,
                        conda_yaml_contents,
                        env_json_path if exists_env_json else None,
                    )
                )
            finally:
                notify_event.set()

            if not robot_yaml_env_info.success:
                return mark_invalid(robot_yaml_env_info.message)
            robot_yaml_env_info_result: IRobotYamlEnvInfo | None = (
                robot_yaml_env_info.result
            )
            if not robot_yaml_env_info_result:
                return mark_invalid(
                    "Internal error: robot_yaml_env_info_result not available."
                )

            space_name = robot_yaml_env_info_result.space_info.space_name

            workspace_args = []
            if workspace_id:
                workspace_args.append("--workspace")
                workspace_args.append(workspace_id)
                workspace_args.append("--account")
                workspace_args.append("sema4ai")

            # Run rcc task run --robot <robot> --space <space> ...
            cmdline = (
                [
                    rcc_executable,
                    "task",
                    "run",
                    "--robot",
                    robot_yaml,
                    "--space",
                    space_name,
                ]
                + workspace_args
                + task_args
                + args
            )
            if self._rcc_config_location:
                cmdline.append("--config")
                cmdline.append(self._rcc_config_location)

            if exists_env_json:
                use_path: str = str(env_json_path)

                for var_name in self.MANAGED_ENV_VARIABLES:
                    if var_name in self._env:
                        try:
                            use_path = self._collect_env_json_without_managed_vars(
                                env_json_path
                            )
                        except:
                            log.exception("Error collecting managed env json.")
                        break

                cmdline.append("-e")
                cmdline.append(use_path)

            cmdline.append("--bundled")
            cmdline.append("--sema4ai")
            cmdline.append("--controller")
            cmdline.append("Sema4aiCode")

        self._cmdline = cmdline

    MANAGED_ENV_VARIABLES = [
        "RPA_OUTPUT_WORKITEM_PATH",
        "RPA_INPUT_WORKITEM_PATH",
        "RPA_WORKITEMS_ADAPTER",
    ]

    def _collect_env_json_without_managed_vars(self, env_json_path: Path) -> str:
        """
        If the existing env.json has some managed environment variable, a new
        env.json without those variables is created and returned to be used for
        the RCC launch (otherwise the original is returned).
        """
        import json

        changed = False

        current_env_contents = json.loads(env_json_path.read_text("utf-8"))
        if not isinstance(current_env_contents, dict):
            raise RuntimeError(f"Expected {env_json_path} contents to be a json dict.")
        # Ok, let's update the file if there are work-item related
        # variables in the env.json.
        from tempfile import NamedTemporaryFile

        temp_file = NamedTemporaryFile(delete=False)

        # Environment variables managed by the extension should
        # be removed from the base env.json.
        for env_name in self.MANAGED_ENV_VARIABLES:
            if env_name in current_env_contents and env_name in self._env:
                changed = True
                del current_env_contents[env_name]

        if changed:
            temp_file.write(json.dumps(current_env_contents).encode("utf-8"))
            temp_file.close()

            def on_exit():
                try:
                    os.remove(temp_file.name)
                except:
                    # If it was already removed, that's ok.
                    pass

            self._on_exit_callbacks.append(on_exit)
            return str(temp_file.name)

        return str(env_json_path)

    @property
    def valid(self):
        return self._valid

    @property
    def run_in_debug_mode(self):
        return self._run_in_debug_mode

    def notify_exit(self):
        if self._sent_terminated.is_set():
            return
        try:
            self._sent_terminated.set()
            from sema4ai_ls_core.debug_adapter_core.dap.dap_schema import (
                TerminatedEvent,
                TerminatedEventBody,
            )

            debug_adapter_comm = self._weak_debug_adapter_comm()
            if debug_adapter_comm is not None:
                restart = False
                terminated_event = TerminatedEvent(
                    body=TerminatedEventBody(restart=restart)
                )
                debug_adapter_comm.write_to_client_message(terminated_event)
        finally:
            for c in self._on_exit_callbacks:
                try:
                    c()
                except:
                    log.exception("Error on exit callback.")

    def launch(self):
        import tempfile

        from sema4ai_ls_core import run_and_save_pid, run_with_env
        from sema4ai_ls_core.core_log import get_log_level
        from sema4ai_ls_core.debug_adapter_core.dap.dap_schema import (
            OutputEvent,
            OutputEventBody,
            RunInTerminalRequest,
            RunInTerminalRequestArguments,
        )

        from sema4ai_code_debug_adapter.constants import (
            TERMINAL_EXTERNAL,
            TERMINAL_INTEGRATED,
            TERMINAL_NONE,
        )

        # Note: using a weak-reference so that callbacks don't keep it alive
        weak_debug_adapter_comm = self._weak_debug_adapter_comm

        terminal = self._terminal
        if not weak_debug_adapter_comm().supports_run_in_terminal:
            # If the client doesn't support running in the terminal we fallback to using the debug console.
            terminal = TERMINAL_NONE

        elif run_with_env.disable_launch_env_script():
            terminal = TERMINAL_NONE

        threads = []
        if terminal == TERMINAL_NONE:
            import subprocess

            if get_log_level() > 1:
                log.debug(
                    "Launching in debug console (not in terminal): %s"
                    % (self._cmdline,)
                )

            env = os.environ.copy()
            env.update(self._env)
            self._popen = subprocess.Popen(
                self._cmdline,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=self._cwd,
                env=env,
            )

            def on_output(output, category):
                debug_adapter_comm = weak_debug_adapter_comm()
                if debug_adapter_comm is not None:
                    output_event = OutputEvent(
                        OutputEventBody(output, category=category)
                    )
                    debug_adapter_comm.write_to_client_message(output_event)

            stdout_stream_thread = threading.Thread(
                target=_read_stream,
                args=(self._popen.stdout, on_output, "stdout"),
                name="Read stdout",
            )
            stderr_stream_thread = threading.Thread(
                target=_read_stream,
                args=(self._popen.stderr, on_output, "stderr"),
                name="Read stderr",
            )

            threads.append(stdout_stream_thread)
            threads.append(stderr_stream_thread)

            self._track_process_pid = self._popen.pid

        elif terminal in (TERMINAL_INTEGRATED, TERMINAL_EXTERNAL):
            kind = terminal

            if get_log_level() > 1:
                log.debug(f'Launching in "{kind}" terminal: {self._cmdline}')

            debug_adapter_comm = weak_debug_adapter_comm()
            cmdline = self._cmdline
            if debug_adapter_comm is not None:
                env = self._env

                write_pid_to = tempfile.mktemp(".pid", "rf_")
                try:
                    cmdline, env = run_with_env.update_cmdline_and_env(
                        cmdline, env, write_pid_to=write_pid_to
                    )

                    debug_adapter_comm.write_to_client_message(
                        RunInTerminalRequest(
                            RunInTerminalRequestArguments(
                                cwd=self._cwd, args=cmdline, kind=kind, env=env
                            )
                        )
                    )
                    self._track_process_pid = run_and_save_pid.wait_for_pid_in_file(
                        write_pid_to
                    )
                finally:
                    try:
                        os.remove(write_pid_to)
                    except:
                        # Ignore if it failed (it's possible that it wasn't created at all...).
                        log.debug("Error removing: %s", write_pid_to)

        if self._track_process_pid is None:
            log.debug("Unable to track if pid is alive (pid unavailable).")
        else:
            threads.append(
                threading.Thread(
                    target=_notify_on_exited_pid,
                    args=(self.notify_exit, self._track_process_pid),
                    name="Track PID alive",
                )
            )

        for t in threads:
            t.daemon = True
            t.start()

    def disconnect(self, disconnect_request):
        from sema4ai_ls_core.process import kill_process_and_subprocesses

        if self._popen is not None:
            if self._popen.returncode is None:
                kill_process_and_subprocesses(self._popen.pid)
        else:
            kill_process_and_subprocesses(self._track_process_pid)

    def send_to_stdin(self, expression):
        popen = self._popen
        if popen is not None:
            try:
                log.debug(f"Sending: {expression} to stdin.")

                def write_to_stdin(popen, expression):
                    popen.stdin.write(expression)
                    if not expression.endswith("\r") and not expression.endswith("\n"):
                        popen.stdin.write("\n")
                    popen.stdin.flush()

                # Do it in a thread (in theory the OS could have that filled up and we would never complete
                # trying to write -- although probably a bit far fetched, let's code as if that could actually happen).
                t = threading.Thread(
                    target=write_to_stdin,
                    args=(popen, expression),
                    name="Send to STDIN",
                )
                t.daemon = True
                t.start()
            except:
                log.exception(f"Error writing: >>{expression}<< to stdin.")
