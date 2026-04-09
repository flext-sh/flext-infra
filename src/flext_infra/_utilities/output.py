"""Terminal output utility with ANSI color and structured formatting."""

from __future__ import annotations

import sys

from flext_infra import (
    FlextInfraUtilitiesOutputFailureSummary,
    FlextInfraUtilitiesTerminal,
    c,
    m,
    p,
)


class FlextInfraUtilitiesOutput(FlextInfraUtilitiesOutputFailureSummary):
    """Terminal output formatter with color and unicode support."""

    _stream: p.Infra.OutputStream = sys.stderr
    _use_color: bool = False
    _use_unicode: bool = False

    @classmethod
    def setup(
        cls,
        *,
        color: bool | None = None,
        unicode: bool | None = None,
        stream: p.Infra.OutputStream | None = None,
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
        reset = c.Infra.RESET if cls._use_color else ""
        clr = color if cls._use_color else ""
        cls._stream.write(f"{clr}{level}{reset}: {message}\n")
        cls._stream.flush()

    @classmethod
    def info(cls, msg: str) -> None:
        cls._fmt("INFO", c.Infra.BLUE, msg)

    @classmethod
    def error(cls, msg: str, detail: str | None = None) -> None:
        cls._fmt("ERROR", c.Infra.RED, msg)
        if detail:
            cls._stream.write(f"  {detail}\n")

    @classmethod
    def warning(cls, msg: str) -> None:
        cls._fmt("WARN", c.Infra.YELLOW, msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls._fmt("DEBUG", c.Infra.GREEN, msg)

    @classmethod
    def header(cls, title: str) -> None:
        sep = "═" if cls._use_unicode else "="
        line = sep * 60
        cls._stream.write(
            f"\n{c.Infra.BOLD if cls._use_color else ''}{line}\n  {title}\n{line}{c.Infra.RESET if cls._use_color else ''}\n",
        )

    @classmethod
    def progress(cls, idx: int, total: int, proj: str, verb: str) -> None:
        w = len(str(total))
        cls._stream.write(f"[{idx:0{w}d}/{total:0{w}d}] {proj} {verb} ...\n")

    @classmethod
    def status(cls, verb: str, proj: str, *, result: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.OK if cls._use_unicode else "[OK]")
            if result
            else (c.Infra.FAIL if cls._use_unicode else "[FAIL]")
        )
        clr = (c.Infra.GREEN if result else c.Infra.RED) if cls._use_color else ""
        cls._stream.write(
            f"  {clr}{sym}{c.Infra.RESET if cls._use_color else ''} {verb:<8} {proj:<24} {elapsed:.2f}s\n",
        )

    @classmethod
    def write(cls, text: str) -> None:
        """Write raw text to output stream."""
        cls._stream.write(text)
        cls._stream.flush()

    @classmethod
    def summary(cls, stats: m.Infra.SummaryStats) -> None:
        s = stats
        hdr = (
            f"── {s.verb} summary ──" if cls._use_unicode else f"-- {s.verb} summary --"
        )
        cls._stream.write(
            f"\n{hdr}\nTotal: {s.total}  Success: {s.success}  Failed: {s.failed}  Skipped: {s.skipped}  ({s.elapsed:.2f}s)\n",
        )

    @classmethod
    def gate_result(
        cls,
        gate: str,
        count: int,
        *,
        passed: bool,
        elapsed: float,
    ) -> None:
        sym = (
            (c.Infra.OK if passed else c.Infra.FAIL)
            if cls._use_unicode
            else ("[OK]" if passed else "[FAIL]")
        )
        cls._stream.write(f"    {sym} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n")

    @classmethod
    def project_failure(cls, info: m.Infra.ProjectFailureInfo) -> None:
        """Show failed project with error excerpt."""
        f = info
        clr = c.Infra.RED if cls._use_color else ""
        reset = c.Infra.RESET if cls._use_color else ""
        fail_sym = c.Infra.FAIL if cls._use_unicode else "[FAIL]"
        count_label = f"  [{f.error_count} errors]" if f.error_count > 0 else ""
        cls._stream.write(
            f"  {clr}{fail_sym}{reset} {f.project} completed in {int(f.elapsed)}s"
            f"{count_label}  ({f.log_path})\n",
        )
        for line in f.errors[: f.max_show]:
            cls._stream.write(f"      {line}\n")
        remaining = f.error_count - f.max_show
        if remaining > 0:
            cls._stream.write(f"      ... and {remaining} more (see log)\n")
        cls._stream.flush()


# Initialize default state
FlextInfraUtilitiesOutput.setup()
__all__ = [
    "FlextInfraUtilitiesOutput",
]
