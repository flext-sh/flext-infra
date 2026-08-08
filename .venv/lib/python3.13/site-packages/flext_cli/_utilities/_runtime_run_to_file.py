"""Canonical streamed process runner exposed through ``u.Cli``."""

from __future__ import annotations

import shlex
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import p, r, t
from flext_cli._utilities._runtime_process_execution import (
    FlextCliUtilitiesRuntimeProcessExecutionMixin,
)


class FlextCliUtilitiesRuntimeRunToFileMixin(
    FlextCliUtilitiesRuntimeProcessExecutionMixin
):
    """Validate and dispatch one portable streamed process lifecycle."""

    if TYPE_CHECKING:

        @staticmethod
        def _resolved_env(
            env: t.StrMapping | None, remove_env_keys: t.StrSequence = ()
        ) -> dict[str, str] | None: ...

    @classmethod
    def run_to_file(
        cls,
        cmd: t.StrSequence,
        output_file: t.Cli.TextPath,
        cwd: t.Cli.TextPath | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
        remove_env_keys: t.StrSequence = (),
        input_data: str | bytes | None = None,
        *,
        live: bool = False,
        deadline: p.Cli.ProcessDeadline | None = None,
    ) -> p.Result[int]:
        """Stream combined bytes live and durably under one absolute deadline.

        Containment owns the inherited POSIX process group or Windows Job
        Object. Trusted project tools remain inside that boundary; deliberate
        POSIX ``setsid()`` escape is outside this contract. The deadline covers
        child execution, termination, reaping, stream drain, and durable flush.
        An outer caller wall remains responsible for an OS syscall that becomes
        uninterruptible.
        """
        if timeout is not None and deadline is not None:
            return r[int].fail("timeout and deadline are mutually exclusive")
        if (live or deadline is not None) and (
            threading.current_thread() is not threading.main_thread()
        ):
            return r[int].fail(
                "live/deadline process execution requires the main interpreter thread"
            )
        started = time.monotonic()
        absolute_deadline: float | None = None
        grace_seconds = 0.0
        timeout_exit_code = 124
        legacy_timeout = timeout is not None
        if deadline is not None:
            absolute_deadline = deadline.expires_at_monotonic
            grace_seconds = deadline.termination_grace_seconds
            timeout_exit_code = deadline.timeout_exit_code
        elif timeout is not None:
            if timeout <= 0:
                return r[int].fail(f"timeout {timeout}s: {shlex.join(list(cmd))}")
            absolute_deadline = started + timeout
            grace_seconds = min(max(timeout * 0.1, 0.05), timeout * 0.5)
        if absolute_deadline is not None:
            remaining = absolute_deadline - started
            if remaining <= 0 or grace_seconds <= 0 or grace_seconds >= remaining:
                return r[int].fail(
                    "process deadline must leave a positive grace reserve"
                )
        return cls._execute_streamed_process(
            cmd,
            Path(output_file),
            cwd,
            cls._resolved_env(env, remove_env_keys),
            input_data,
            live=live,
            absolute_deadline=absolute_deadline,
            grace_seconds=grace_seconds,
            timeout_exit_code=timeout_exit_code,
            legacy_timeout=legacy_timeout,
            legacy_timeout_seconds=timeout,
        )


__all__: list[str] = ["FlextCliUtilitiesRuntimeRunToFileMixin"]
