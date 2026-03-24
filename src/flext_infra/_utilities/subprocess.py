"""Subprocess execution utilities for infrastructure operations."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from flext_core import r

from flext_infra import c, m, t


class FlextInfraUtilitiesSubprocess:
    """Subprocess execution helpers with r-wrapped error handling."""

    @staticmethod
    def run_raw(
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
        input_data: bytes | None = None,
    ) -> r[m.Infra.CommandOutput]:
        """Run command without enforcing exit code."""
        try:
            res = subprocess.run(
                list(cmd),
                cwd=cwd,
                capture_output=True,
                text=input_data is None,
                check=False,
                timeout=timeout,
                env=env,
                input=input_data,
            )
            stdout_raw = res.stdout or (b"" if input_data else "")
            stderr_raw = res.stderr or (b"" if input_data else "")
            return r[m.Infra.CommandOutput].ok(
                m.Infra.CommandOutput(
                    stdout=stdout_raw.decode() if isinstance(stdout_raw, bytes) else stdout_raw,
                    stderr=stderr_raw.decode() if isinstance(stderr_raw, bytes) else stderr_raw,
                    exit_code=res.returncode,
                ),
            )
        except subprocess.TimeoutExpired as exc:
            return r[m.Infra.CommandOutput].fail(
                f"timeout {exc.timeout}s: {shlex.join(list(cmd))}",
            )
        except (OSError, ValueError) as exc:
            return r[m.Infra.CommandOutput].fail(f"execution error: {exc}")

    @staticmethod
    def run(
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Infra.CommandOutput]:
        """Run command with zero-exit enforcement."""
        res = FlextInfraUtilitiesSubprocess.run_raw(cmd, cwd, timeout, env)
        if res.is_failure:
            return res
        out = res.value
        if out.exit_code != 0:
            return r[m.Infra.CommandOutput].fail(
                f"failed ({out.exit_code}): {shlex.join(list(cmd))}: {(out.stderr or out.stdout).strip()}",
            )
        return res

    @staticmethod
    def run_checked(
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[bool]:
        """Run command and return status."""
        return FlextInfraUtilitiesSubprocess.run(cmd, cwd, timeout, env).map(
            lambda _: True,
        )

    @staticmethod
    def capture(
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[str]:
        """Capture stripped stdout."""
        return FlextInfraUtilitiesSubprocess.run(cmd, cwd, timeout, env).map(
            lambda v: v.stdout.strip(),
        )

    @staticmethod
    def run_to_file(
        cmd: t.StrSequence,
        output_file: Path,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[int]:
        """Stream combined output to file."""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding=c.Infra.Encoding.DEFAULT) as h:
                res = subprocess.run(
                    list(cmd),
                    cwd=cwd,
                    stdout=h,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=timeout,
                    env=env,
                )
            return r[int].ok(res.returncode)
        except subprocess.TimeoutExpired as exc:
            return r[int].fail(f"timeout {exc.timeout}s: {shlex.join(list(cmd))}")
        except (OSError, ValueError) as exc:
            return r[int].fail(f"execution error: {exc}")


__all__ = ["FlextInfraUtilitiesSubprocess"]
