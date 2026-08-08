"""Resource ownership for one portable streamed process lifecycle."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from pathlib import Path
from typing import IO, BinaryIO

from flext_cli import c, p, t
from flext_cli._utilities._runtime_process_cleanup import (
    FlextCliUtilitiesRuntimeProcessCleanupMixin,
)
from flext_cli._utilities._runtime_process_outcome import (
    FlextCliUtilitiesRuntimeProcessOutcomeMixin,
)
from flext_cli._utilities._runtime_process_resources import (
    FlextCliUtilitiesRuntimeProcessResourcesMixin,
)
from flext_cli._utilities._runtime_process_start import (
    FlextCliUtilitiesRuntimeProcessStartMixin,
)


class FlextCliUtilitiesRuntimeProcessExecutionMixin(
    FlextCliUtilitiesRuntimeProcessCleanupMixin,
    FlextCliUtilitiesRuntimeProcessOutcomeMixin,
    FlextCliUtilitiesRuntimeProcessResourcesMixin,
    FlextCliUtilitiesRuntimeProcessStartMixin,
):
    """Own one child process and its streaming resources."""

    @classmethod
    def _execute_streamed_process(
        cls,
        cmd: t.StrSequence,
        output_path: Path,
        cwd: t.Cli.TextPath | None,
        env: dict[str, str] | None,
        input_data: str | bytes | None,
        *,
        live: bool,
        absolute_deadline: float | None,
        grace_seconds: float,
        timeout_exit_code: int,
        legacy_timeout: bool,
        legacy_timeout_seconds: int | None,
    ) -> p.Result[int]:
        """Own resources and complete one streamed child lifecycle."""
        process: p.Cli.ProcessHandle | None = None
        waiter: threading.Thread | None = None
        pump: threading.Thread | None = None
        source: IO[bytes] | None = None
        durable_log: BinaryIO | None = None
        job_handle = 0
        failures: list[str] = []
        cleanup_errors: list[str] = []
        live_diagnostics: list[str] = []
        restore_handlers: list[Callable[[], object]] = []
        forwarded_signals: list[int] = []
        received_signals: list[int] = []
        return_codes: list[int] = []
        pump_stop = threading.Event()
        process_done = threading.Event()
        wake = threading.Event()
        stack = contextlib.ExitStack()
        return_code: int | None = None
        timed_out = False
        final_deadline = absolute_deadline
        cleanup_complete = False

        def execute_lifecycle() -> None:
            nonlocal \
                cleanup_complete, \
                durable_log, \
                final_deadline, \
                job_handle, \
                process, \
                pump, \
                return_code, \
                source, \
                timed_out, \
                waiter
            if threading.current_thread() is threading.main_thread():
                restore_handlers.extend(
                    cls._install_forwarding_handlers(
                        received_signals, forwarded_signals, wake
                    )
                )
            prepared_cmd = tuple(cmd)
            if received_signals:
                wake.set()
                return
            output_path.parent.mkdir(parents=True, exist_ok=True)
            durable_log = stack.enter_context(output_path.open("wb", buffering=0))
            stdin_result = cls._prepare_streamed_stdin(stack, input_data)
            live_result = cls._prepare_live_descriptor(stack, live=live)
            if stdin_result.failure:
                failures.append(stdin_result.error or "stdin preparation failed")
            elif live_result.failure:
                failures.append(live_result.error or "live output preparation failed")
            elif received_signals:
                wake.set()
            elif cls._spawn_deadline_exhausted(absolute_deadline, grace_seconds):
                failures.append("process deadline exhausted before child spawn")
            else:
                started = cls._start_contained_process(
                    prepared_cmd, cwd, env, stdin_result.value[0]
                )
                if started.failure:
                    failures.append(started.error or "process start failed")
                else:
                    process, job_handle = started.unwrap()
                    source = process.stdout
                    if source is None:
                        failures.append("process stdout is not available")
                        return
                    stack.callback(source.close)
                    waiter = cls._start_root_waiter(
                        process, return_codes, failures, process_done, wake
                    )
                    pump = cls._start_output_pump(
                        source,
                        durable_log,
                        live_result.value[0],
                        failures,
                        live_diagnostics,
                        pump_stop,
                        wake,
                    )
                    timed_out, final_deadline = cls._monitor_process(
                        process,
                        process_done,
                        wake,
                        failures,
                        received_signals,
                        job_handle,
                        absolute_deadline,
                        grace_seconds,
                    )
                    return_code = cls._reap_and_drain(
                        process,
                        waiter,
                        pump,
                        process_done,
                        wake,
                        pump_stop,
                        source,
                        cleanup_errors,
                        job_handle,
                        final_deadline,
                        return_codes,
                    )
                    cleanup_complete = True

        try:
            execute_lifecycle()
        except c.EXC_OS_VALUE as exc:
            failures.append(f"execution error: {exc}")
        finally:
            if (
                process is not None
                and waiter is not None
                and pump is not None
                and source is not None
                and not cleanup_complete
            ):
                return_code = cls._reap_and_drain(
                    process,
                    waiter,
                    pump,
                    process_done,
                    wake,
                    pump_stop,
                    source,
                    cleanup_errors,
                    job_handle,
                    final_deadline,
                    return_codes,
                )
            if durable_log is not None:
                cleanup_errors.extend(
                    cls._flush_durable_log(durable_log, final_deadline)
                )
            close_error = cls._windows_job_close(job_handle)
            if close_error is not None:
                cleanup_errors.append(close_error)
            cleanup_errors.extend(cls._close_process_resources(stack))
            cleanup_errors.extend(cls._restore_forwarding_handlers(restore_handlers))
        return cls._process_exit_result(
            cmd,
            return_code,
            received_signals,
            (*failures, *cleanup_errors),
            nonfatal_diagnostics=tuple(live_diagnostics),
            timed_out=timed_out,
            legacy_timeout=legacy_timeout,
            legacy_timeout_seconds=legacy_timeout_seconds,
            timeout_exit_code=timeout_exit_code,
        )


__all__: list[str] = ["FlextCliUtilitiesRuntimeProcessExecutionMixin"]
