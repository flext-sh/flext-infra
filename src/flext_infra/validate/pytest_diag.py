"""Pytest diagnostics extraction service.

Extracts strict pytest diagnostics from JUnit XML and log outputs,
producing structured failure/error/warning/skip/slow-test reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, m, u
from flext_infra.base import s

from ._pytest_diag_xml import FlextInfraPytestDiagXmlMixin

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraPytestDiagExtractor(FlextInfraPytestDiagXmlMixin, s[bool]):
    """Extracts pytest diagnostics from JUnit XML and log files.

    Parses required JUnit XML for structured failure/error/skip/timing data
    and the required pytest log for warning data.
    """

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
    def _extract_warnings(lines: t.StrSequence, diag: m.Infra.DiagResult) -> None:
        """Extract every warning line from the canonical pytest log."""
        diag.warning_lines = [
            line for line in lines if c.Infra.PYTEST_WARNING_LINE_RE.search(line)
        ]

    def extract(
        self, junit_path: Path, log_path: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics from JUnit XML and pytest log.

        Args:
            junit_path: Path to JUnit XML result file.
            log_path: Path to raw pytest log output.

        Returns:
            r with diagnostics dict containing counts and entries.

        """
        return self._extract_diagnostics(junit_path, log_path)

    @staticmethod
    def _read_log_text(log_path: Path) -> str:
        """Read the required pytest log without exception normalization."""
        return log_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)

    @staticmethod
    def _diagnostics_model(diag: m.Infra.DiagResult) -> m.Infra.PytestDiagnostics:
        """Convert mutable extraction state to the canonical diagnostics model."""
        return m.Infra.PytestDiagnostics(
            failed_count=len(diag.failed_cases),
            error_count=len(diag.error_cases),
            warning_count=len(diag.warning_lines),
            skipped_count=len(diag.skip_cases),
            failed_cases=diag.failed_cases,
            error_traces=diag.error_traces,
            warning_lines=diag.warning_lines,
            skip_cases=diag.skip_cases,
            slow_entries=diag.slow_entries,
        )

    def _extract_diagnostics(
        self, junit_path: Path, log_path: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract pytest diagnostics after input normalization."""
        lines = self._read_log_text(log_path).splitlines()
        diag = m.Infra.DiagResult()
        self._parse_xml(junit_path, diag)
        self._extract_warnings(lines, diag)
        return r[m.Infra.PytestDiagnostics].ok(self._diagnostics_model(diag))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the pytest diagnostics CLI flow."""
        diagnostics = self.extract(self.junit, self.log_path).unwrap()
        for output_path, attr_name, separator in [
            (self.failed, "failed_cases", "\n\n"),
            (self.errors, "error_traces", "\n\n"),
            (self.warnings, "warning_lines", "\n"),
            (self.slowest, "slow_entries", "\n"),
            (self.skips, "skip_cases", "\n"),
        ]:
            if output_path is None:
                continue
            items = getattr(diagnostics, attr_name)
            u.Cli.atomic_write_text_file(
                output_path, separator.join(items) + "\n"
            ).unwrap()
        sys.stdout.write(
            f"failed_count={diagnostics.failed_count}\n"
            f"error_count={diagnostics.error_count}\n"
            f"warning_count={diagnostics.warning_count}\n"
            f"skipped_count={diagnostics.skipped_count}\n"
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPytestDiagExtractor"]
