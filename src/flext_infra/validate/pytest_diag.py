"""Typed service adapter for the low-import pytest diagnostic owner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import m
from flext_infra._pytest_diag_fast import (
    PytestDiagnosticsData,
    extract_diagnostics,
    write_diagnostic_files,
)
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPytestDiagExtractor(s[bool]):
    """Expose the single lightweight extractor through the typed service API."""

    junit: Annotated[Path, m.Field(description="JUnit XML path")]
    log_path: Annotated[Path, m.Field(description="Pytest log path")] = m.Field(
        alias="log"
    )
    failed: Annotated[
        Path | None, m.Field(description="Path to write failed cases")
    ] = None
    errors: Annotated[
        Path | None, m.Field(description="Path to write error traces")
    ] = None
    warnings: Annotated[Path | None, m.Field(description="Path to write warnings")] = (
        None
    )
    slowest: Annotated[
        Path | None, m.Field(description="Path to write slowest entries")
    ] = None
    skips: Annotated[
        Path | None, m.Field(description="Path to write skipped cases")
    ] = None

    @staticmethod
    def _diagnostics_model(
        diagnostics: PytestDiagnosticsData,
    ) -> m.Infra.PytestDiagnostics:
        """Convert the transport-neutral result to the canonical model."""
        return m.Infra.PytestDiagnostics(
            failed_count=diagnostics.failed_count,
            error_count=diagnostics.error_count,
            warning_count=diagnostics.warning_count,
            skipped_count=diagnostics.skipped_count,
            failed_cases=diagnostics.failed_cases,
            error_traces=diagnostics.error_traces,
            warning_lines=diagnostics.warning_lines,
            skip_cases=diagnostics.skip_cases,
            slow_entries=diagnostics.slow_entries,
        )

    def extract(
        self, junit_path: Path, log_path: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics through the single low-import implementation."""
        try:
            diagnostics = extract_diagnostics(junit_path, log_path)
        except (OSError, ValueError) as exc:
            return r[m.Infra.PytestDiagnostics].fail_op(
                "pytest diagnostics extraction", exc
            )
        return r[m.Infra.PytestDiagnostics].ok(self._diagnostics_model(diagnostics))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the typed pytest diagnostics CLI flow."""
        result = self.extract(self.junit, self.log_path)
        if result.failure:
            return r[bool].fail(result.error or "extraction failed")
        diagnostics = PytestDiagnosticsData(
            failed_cases=list(result.value.failed_cases),
            error_traces=list(result.value.error_traces),
            warning_lines=list(result.value.warning_lines),
            skip_cases=list(result.value.skip_cases),
            slow_entries=list(result.value.slow_entries),
        )
        try:
            write_diagnostic_files(
                diagnostics,
                failed=self.failed,
                errors=self.errors,
                warnings=self.warnings,
                slowest=self.slowest,
                skips=self.skips,
            )
        except OSError as exc:
            return r[bool].fail_op("pytest diagnostic report write", exc)
        sys.stdout.write(
            f"failed_count={result.value.failed_count}\n"
            f"error_count={result.value.error_count}\n"
            f"warning_count={result.value.warning_count}\n"
            f"skipped_count={result.value.skipped_count}\n"
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPytestDiagExtractor"]
