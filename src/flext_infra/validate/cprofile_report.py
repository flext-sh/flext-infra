"""Typed renderer for canonical focused cProfile artifacts."""

from __future__ import annotations

import io
import pstats
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Self, override

from flext_core import r
from pydantic import model_validator

from flext_infra import m, t, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCProfileReport(s[bool]):
    """Render one bounded human-readable report from a pstats artifact."""

    profile: Annotated[Path, m.Field(description="Input cProfile pstats path")]
    output: Annotated[Path, m.Field(description="Output text report path")]
    sort: Annotated[
        Literal[
            "calls",
            "cumulative",
            "filename",
            "line",
            "name",
            "nfl",
            "pcalls",
            "stdname",
            "time",
        ],
        m.Field(description="Validated pstats sort key"),
    ]
    limit: Annotated[int, m.Field(gt=0, le=1000, description="Maximum rows to print")]

    @model_validator(mode="after")
    def _validate_report_paths(self) -> Self:
        """Keep profile input and output inside the workspace report tree."""
        report_root = (self.workspace_root / ".reports").resolve()
        for path in (self.profile, self.output):
            try:
                path.resolve().relative_to(report_root)
            except ValueError as exc:
                msg = f"cProfile path must stay under {report_root}: {path}"
                raise ValueError(msg) from exc
        return self

    @override
    def execute(self) -> p.Result[bool]:
        """Load, sort, and render the profile without executing user code."""
        if not self.profile.is_file():
            return r[bool].fail(f"cProfile artifact does not exist: {self.profile}")
        try:
            stream = io.StringIO()
            stats = pstats.Stats(str(self.profile), stream=stream)
            stats.strip_dirs().sort_stats(self.sort).print_stats(self.limit)
            self.output.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, ValueError, TypeError) as exc:
            return r[bool].fail_op("render cProfile report", exc)
        written = u.Cli.atomic_write_text_file(self.output, stream.getvalue())
        if written.failure:
            return r[bool].fail(
                written.error or f"failed to write cProfile report: {self.output}"
            )
        return r[bool].ok(True)


class FlextInfraCProfileRun(FlextInfraCProfileReport):
    """Run one Python module under portable, timeout-bounded cProfile."""

    profile_module: Annotated[
        t.NonEmptyStr,
        m.Field(
            alias="profile-module",
            pattern=r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$",
            description="Importable Python module to profile",
        ),
    ]
    arguments: Annotated[
        tuple[t.NonEmptyStr, ...],
        m.BeforeValidator(
            lambda value: (value,) if isinstance(value, str) else tuple(value)
        ),
        m.Field(description="Arguments forwarded to the profiled module"),
    ] = ()
    timeout_seconds: Annotated[
        int, m.Field(gt=0, le=58, description="Portable subprocess timeout in seconds")
    ]

    @override
    def execute(self) -> p.Result[bool]:
        """Profile the selected module and render its bounded report."""
        try:
            self.profile.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op("prepare cProfile artifact directory", exc)
        command = (
            sys.executable,
            "-m",
            "cProfile",
            "-o",
            str(self.profile),
            "-m",
            self.profile_module,
            *self.arguments,
        )
        profiled = u.Cli.run_raw(
            command, cwd=self.workspace_root, timeout=self.timeout_seconds
        )
        if profiled.failure:
            return r[bool].fail(profiled.error or "cProfile subprocess failed")
        output = profiled.unwrap()
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            suffix = f": {detail}" if detail else ""
            return r[bool].fail(
                f"cProfile subprocess exited with {output.exit_code}{suffix}"
            )
        return super().execute()


__all__: list[str] = ["FlextInfraCProfileReport", "FlextInfraCProfileRun"]
