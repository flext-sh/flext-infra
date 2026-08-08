"""Generic external process runtime shared through ``u.Cli``."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from typing import BinaryIO, ClassVar, override

from flext_cli import c, m, p, r, t
from flext_cli._utilities._runtime_commands import FlextCliUtilitiesRuntimeCommandsMixin
from flext_cli._utilities._runtime_run_to_file import (
    FlextCliUtilitiesRuntimeRunToFileMixin,
)
from flext_core import u as core_u


class FlextCliUtilitiesRuntime(
    FlextCliUtilitiesRuntimeRunToFileMixin, FlextCliUtilitiesRuntimeCommandsMixin
):
    """Runtime helpers for external command execution."""

    _module_logger: ClassVar[p.Logger] = core_u.fetch_logger(__name__)

    @staticmethod
    def process_env(
        *, overrides: t.StrMapping | None = None, remove_keys: t.StrSequence = ()
    ) -> dict[str, str]:
        """Return one inherited process environment with optional overrides."""
        return m.Cli.ProcessEnvironmentSpec.model_validate({
            "base_env": dict(os.environ),
            "overrides": overrides if overrides is not None else {},
            "remove_keys": tuple(remove_keys),
        }).resolve()

    @staticmethod
    @override
    def _resolved_env(
        env: t.StrMapping | None, remove_env_keys: t.StrSequence = ()
    ) -> dict[str, str] | None:
        """Resolve the child environment with overrides and optional removals."""
        if env is None and not remove_env_keys:
            return None
        return FlextCliUtilitiesRuntime.process_env(
            overrides=env, remove_keys=remove_env_keys
        )

    @staticmethod
    @override
    def _spawn_streamed_process(
        cmd: t.StrSequence,
        cwd: t.Cli.TextPath | None,
        env: dict[str, str] | None,
        stdin_handle: BinaryIO | None,
        *,
        creation_flags: int,
    ) -> p.Cli.ProcessHandle:
        """Create the sole raw child owned by the streamed lifecycle."""
        return subprocess.Popen(
            list(cmd),
            cwd=cwd,
            stdin=subprocess.DEVNULL if stdin_handle is None else stdin_handle,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=0,
            env=env,
            start_new_session=os.name != "nt",
            creationflags=creation_flags,
        )

    @staticmethod
    @override
    def _streamed_creation_flags() -> int:
        """Return platform creation flags for pre-execution containment."""
        if os.name != "nt":
            return 0
        return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)) | int(
            getattr(subprocess, "CREATE_SUSPENDED", 0x00000004)
        )

    @staticmethod
    @override
    def run_raw(
        cmd: t.StrSequence,
        cwd: t.Cli.TextPath | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
        remove_env_keys: t.StrSequence = (),
        input_data: str | bytes | None = None,
        *,
        capture: bool = True,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run a command without enforcing a zero exit code.

        Accepts text or binary stdin (text is UTF-8 encoded). When ``capture``
        is True (default) stdout/stderr are captured and returned as text
        (UTF-8); non-UTF-8 output fails closed with a typed error instead of
        crashing or surfacing a generic error. When ``capture`` is False the
        child inherits the parent's stdout/stderr so its output streams live
        (for long-running makes/rollouts); the returned stdout/stderr are then
        empty and only the exit code is meaningful.
        """
        start = time.monotonic()
        stdin = (
            input_data.encode("utf-8") if isinstance(input_data, str) else input_data
        )
        try:
            result = subprocess.run(
                list(cmd),
                cwd=cwd,
                capture_output=capture,
                text=False,
                check=False,
                timeout=timeout,
                env=FlextCliUtilitiesRuntime._resolved_env(env, remove_env_keys),
                input=stdin,
            )
        except subprocess.TimeoutExpired as exc:
            return r[p.Cli.CommandOutput].fail(
                f"timeout {exc.timeout}s: {shlex.join(list(cmd))}"
            )
        except c.EXC_OS_VALUE as exc:
            return r[p.Cli.CommandOutput].fail(f"execution error: {exc}")
        try:
            stdout = (result.stdout or b"").decode("utf-8")
            stderr = (result.stderr or b"").decode("utf-8")
        except UnicodeDecodeError as exc:
            return r[p.Cli.CommandOutput].fail(
                f"non-UTF-8 output from {shlex.join(list(cmd))}: {exc}"
            )
        duration = max(0.0, time.monotonic() - start)
        return r[p.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
                duration=duration,
            )
        )

    @staticmethod
    def run_bytes(
        cmd: t.StrSequence,
        cwd: t.Cli.TextPath | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
        remove_env_keys: t.StrSequence = (),
        input_data: str | bytes | None = None,
    ) -> p.Result[p.Cli.CommandBytesOutput]:
        """Run a command capturing byte-exact stdout/stderr (no text decoding)."""
        start = time.monotonic()
        stdin = (
            input_data.encode("utf-8") if isinstance(input_data, str) else input_data
        )
        try:
            result = subprocess.run(
                list(cmd),
                cwd=cwd,
                capture_output=True,
                text=False,
                check=False,
                timeout=timeout,
                env=FlextCliUtilitiesRuntime._resolved_env(env, remove_env_keys),
                input=stdin,
            )
        except subprocess.TimeoutExpired as exc:
            return r[p.Cli.CommandBytesOutput].fail(
                f"timeout {exc.timeout}s: {shlex.join(list(cmd))}"
            )
        except c.EXC_OS_VALUE as exc:
            return r[p.Cli.CommandBytesOutput].fail(f"execution error: {exc}")
        duration = max(0.0, time.monotonic() - start)
        return r[p.Cli.CommandBytesOutput].ok(
            m.Cli.CommandBytesOutput(
                stdout=result.stdout or b"",
                stderr=result.stderr or b"",
                exit_code=result.returncode,
                duration=duration,
            )
        )


__all__: list[str] = ["FlextCliUtilitiesRuntime"]
