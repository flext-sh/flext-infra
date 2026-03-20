"""Terminal output utility with ANSI color and structured formatting."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final, TextIO

from flext_infra import t
from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
from flext_infra.constants import FlextInfraConstants as c


class FlextInfraUtilitiesOutput:
    """Terminal output formatter with color and unicode support."""

    _stream: TextIO = sys.stderr
    _use_color: bool = False
    _use_unicode: bool = False

    @classmethod
    def setup(
        cls,
        *,
        color: bool | None = None,
        unicode: bool | None = None,
        stream: TextIO | None = None,
    ) -> None:
        """Initialize output settings."""
        cls._use_color = (
            FlextInfraUtilitiesTerminal.terminal_should_use_color()
            if color is None
            else color
        )
        cls._use_unicode = (
            FlextInfraUtilitiesTerminal.terminal_should_use_unicode()
            if unicode is None
            else unicode
        )
        if stream:
            cls._stream = stream

    @classmethod
    def _fmt(cls, level: str, color: str, message: str) -> None:
        reset = c.Infra.Style.RESET if cls._use_color else ""
        clr = color if cls._use_color else ""
        cls._stream.write(f"{clr}{level}{reset}: {message}\n")
        cls._stream.flush()

    @classmethod
    def info(cls, msg: str) -> None:
        cls._fmt("INFO", c.Infra.Style.BLUE, msg)

    @classmethod
    def error(cls, msg: str, detail: str | None = None) -> None:
        cls._fmt("ERROR", c.Infra.Style.RED, msg)
        if detail:
            cls._stream.write(f"  {detail}\n")

    @classmethod
    def warning(cls, msg: str) -> None:
        cls._fmt("WARN", c.Infra.Style.YELLOW, msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls._fmt("DEBUG", c.Infra.Style.GREEN, msg)

    @classmethod
    def header(cls, title: str) -> None:
        sep = "═" if cls._use_unicode else "="
        line = sep * 60
        cls._stream.write(
            f"\n{c.Infra.Style.BOLD if cls._use_color else ''}{line}\n  {title}\n{line}{c.Infra.Style.RESET if cls._use_color else ''}\n"
        )

    @classmethod
    def progress(cls, idx: int, total: int, proj: str, verb: str) -> None:
        w = len(str(total))
        cls._stream.write(f"[{idx:0{w}d}/{total:0{w}d}] {proj} {verb} ...\n")

    @classmethod
    def status(cls, verb: str, proj: str, result: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.Style.OK if cls._use_unicode else "[OK]")
            if result
            else (c.Infra.Style.FAIL if cls._use_unicode else "[FAIL]")
        )
        clr = (
            (c.Infra.Style.GREEN if result else c.Infra.Style.RED)
            if cls._use_color
            else ""
        )
        cls._stream.write(
            f"  {clr}{sym}{c.Infra.Style.RESET if cls._use_color else ''} {verb:<8} {proj:<24} {elapsed:.2f}s\n"
        )

    @classmethod
    def summary(
        cls, verb: str, total: int, ok: int, fail: int, skip: int, elapsed: float
    ) -> None:
        hdr = f"── {verb} summary ──" if cls._use_unicode else f"-- {verb} summary --"
        cls._stream.write(
            f"\n{hdr}\nTotal: {total}  Success: {ok}  Failed: {fail}  Skipped: {skip}  ({elapsed:.2f}s)\n"
        )

    @classmethod
    def gate_result(cls, gate: str, count: int, passed: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.Style.OK if passed else c.Infra.Style.FAIL)
            if cls._use_unicode
            else ("[OK]" if passed else "[FAIL]")
        )
        cls._stream.write(f"    {sym} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n")

    @staticmethod
    def metrics(
        *instances: t.Infra.MetricRecord, **kwargs: t.Infra.MetricValue
    ) -> None:
        for item in list(instances) + [kwargs]:
            for k, v in item.items() if isinstance(item, Mapping) else item:
                if isinstance(v, (*t.PRIMITIVES_TYPES, Path)) or v is None:
                    sys.stdout.write(f"{k}={v}\n")
        sys.stdout.flush()


# Initialize default state
FlextInfraUtilitiesOutput.setup()
output: Final[type[FlextInfraUtilitiesOutput]] = FlextInfraUtilitiesOutput

__all__ = ["FlextInfraUtilitiesOutput", "output"]
