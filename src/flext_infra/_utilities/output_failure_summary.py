"""Failure summary rendering mixin shared by infra output utilities."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, t


class FlextInfraUtilitiesOutputFailureSummary:
    """Mixin that renders the standard failed-projects summary block."""

    _use_unicode: ClassVar[bool]
    _use_color: ClassVar[bool]
    _stream: ClassVar[t.Infra.TextStream]

    @classmethod
    def failure_summary(
        cls,
        verb: str,
        failures: Sequence[t.Infra.Triple[str, int, Path]],
    ) -> None:
        """Render the end-of-run failed-projects block."""
        if not failures:
            return
        hdr = (
            f"── {verb} failed projects ──"
            if cls._use_unicode
            else f"-- {verb} failed projects --"
        )
        color = c.Infra.RED if cls._use_color else ""
        reset = c.Infra.RESET if cls._use_color else ""
        fail_sym = c.Infra.FAIL if cls._use_unicode else "[FAIL]"
        cls._stream.write(f"\n{hdr}\n")
        for project, error_count, log_path in failures:
            count_label = f"{error_count} errors" if error_count > 0 else "failed"
            cls._stream.write(
                f"{color}{fail_sym}{reset} {project:<20} {count_label}  ({log_path})\n",
            )
        cls._stream.flush()


__all__ = [
    "FlextInfraUtilitiesOutputFailureSummary",
]
