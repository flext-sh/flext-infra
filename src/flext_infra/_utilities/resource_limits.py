"""Validated process resource-limit command builders.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, ClassVar

from flext_cli import u
from flext_infra import c, m, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesResourceLimits:
    """Build resource-bounded commands for memory-intensive quality tools."""

    _MEMORY_FAILURE_MARKERS: ClassVar[tuple[str, ...]] = (
        "cannot allocate memory",
        "failed to map segment",
        "memoryerror",
        "out of memory",
    )

    @staticmethod
    def _required_executable(command: str) -> str:
        """Resolve one required resource-control executable or fail loud."""
        executable = shutil.which(command)
        if executable is None:
            msg = f"required executable not found: {command}"
            raise RuntimeError(msg)
        return executable

    @staticmethod
    def _environment_integer(process_env: t.StrMapping, name: str, default: int) -> int:
        """Convert one ASCII integer environment value at the ingress boundary."""
        raw_value = process_env.get(name)
        if raw_value is None:
            return default
        if not raw_value.isascii() or not raw_value.isdecimal():
            msg = f"{name} must be a positive integer"
            raise ValueError(msg)
        return int(raw_value)

    @staticmethod
    def mypy_resource_limit() -> p.Infra.MypyResourceLimit:
        """Validate the external Mypy memory and time settings exactly once."""
        process_env = u.Cli.process_env()
        return m.Infra.MypyResourceLimit(
            memory_limit_mb=FlextInfraUtilitiesResourceLimits._environment_integer(
                process_env,
                c.Infra.MYPY_MEMORY_LIMIT_MB_ENV,
                c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            ),
            timeout_seconds=FlextInfraUtilitiesResourceLimits._environment_integer(
                process_env,
                c.Infra.MYPY_TIMEOUT_SECONDS_ENV,
                c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
            ),
        )

    @staticmethod
    def mypy_limited_command(
        command: t.StrSequence, limit: p.Infra.MypyResourceLimit | None = None
    ) -> t.StrSequence:
        """Prefix one Mypy command with validated memory and wall-time limits."""
        validated_limit = (
            limit or FlextInfraUtilitiesResourceLimits.mypy_resource_limit()
        )
        prlimit_executable = FlextInfraUtilitiesResourceLimits._required_executable(
            c.Infra.PRLIMIT_COMMAND
        )
        timeout_executable = FlextInfraUtilitiesResourceLimits._required_executable(
            c.Infra.TIMEOUT_COMMAND
        )
        return (
            timeout_executable,
            "--signal=TERM",
            f"--kill-after={c.Infra.TIMEOUT_KILL_AFTER_SECONDS}s",
            f"{validated_limit.timeout_seconds}s",
            prlimit_executable,
            (
                f"{c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION}="
                f"{validated_limit.memory_limit_mb * 1024 * 1024}:"
                f"{validated_limit.memory_limit_mb * 1024 * 1024}"
            ),
            "--",
            *command,
        )

    @staticmethod
    def mypy_runner_timeout(limit: p.Infra.MypyResourceLimit | None = None) -> int:
        """Return the outer runner timeout after the controlled child deadline."""
        validated_limit = (
            limit or FlextInfraUtilitiesResourceLimits.mypy_resource_limit()
        )
        return validated_limit.timeout_seconds + c.Infra.MYPY_TIMEOUT_GRACE_SECONDS

    @staticmethod
    def _bounded_mypy_diagnostic(
        limit: p.Infra.MypyResourceLimit,
        *,
        detail: str,
        exit_code: int | str,
        signal: int | str,
    ) -> str:
        """Render the single controlled Mypy resource-failure diagnostic."""
        return (
            "bounded Mypy execution failed: "
            f"memory_limit={limit.memory_limit_mb} MiB; "
            f"timeout={limit.timeout_seconds}s; "
            f"exit={exit_code}; signal={signal}; detail={detail}"
        )

    @classmethod
    def mypy_launch_failure_diagnostic(
        cls, detail: str, limit: p.Infra.MypyResourceLimit | None = None
    ) -> str:
        """Report an outer-runner failure that precluded a process exit status."""
        validated_limit = limit or cls.mypy_resource_limit()
        return cls._bounded_mypy_diagnostic(
            validated_limit, detail=detail, exit_code="unavailable", signal="none"
        )

    @classmethod
    def mypy_failure_diagnostic(
        cls, output: p.Cli.CommandOutput, limit: p.Infra.MypyResourceLimit | None = None
    ) -> str | None:
        """Return a controlled diagnostic only for timeout or memory exhaustion."""
        validated_limit = limit or cls.mypy_resource_limit()
        combined = f"{output.stdout}\n{output.stderr}".lower()
        resource_failure = (
            output.exit_code == c.Infra.MYPY_TIMEOUT_EXIT_CODE
            or output.exit_code < 0
            or output.exit_code >= c.Infra.MYPY_SIGNAL_EXIT_OFFSET
            or any(marker in combined for marker in cls._MEMORY_FAILURE_MARKERS)
        )
        if not resource_failure:
            return None
        signal = (
            -output.exit_code
            if output.exit_code < 0
            else output.exit_code - c.Infra.MYPY_SIGNAL_EXIT_OFFSET
            if output.exit_code >= c.Infra.MYPY_SIGNAL_EXIT_OFFSET
            else "none"
        )
        detail = (output.stderr or output.stdout).strip() or "resource limit reached"
        return cls._bounded_mypy_diagnostic(
            validated_limit, detail=detail, exit_code=output.exit_code, signal=signal
        )


__all__: list[str] = ["FlextInfraUtilitiesResourceLimits"]
