"""Pytest diagnostics extraction service.

Extracts strict pytest diagnostics from JUnit XML and structured report-log outputs,
producing structured failure/error/warning/skip/slow-test reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, config, m, u

from ..base import s
from ._pytest_diag_xml import FlextInfraPytestDiagXmlMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPytestDiagExtractor(FlextInfraPytestDiagXmlMixin, s[bool]):
    """Extracts pytest diagnostics from the runner's required report artifacts.

    Parses required JUnit XML for structured failure/error/skip/timing data
    and the explicit report-log for every warning occurrence.
    The human-readable pytest log remains required diagnostic evidence.
    """

    junit: Annotated[Path, m.Field(description="JUnit XML path")]
    log_path: Annotated[Path, m.Field(description="Pytest log path")] = m.Field(
        alias="log"
    )
    report_log: Annotated[Path, m.Field(description="Pytest report-log JSONL path")]
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
    def _suspended_warning_categories() -> t.Set[str]:
        """Resolve category-wide visible exceptions from the typed pytest policy."""
        suspended: t.Set[str] = set()
        for spec in config.Infra.tooling.tools.pytest.filter_warnings:
            parts = spec.split(":")
            action = parts[0]
            if spec == "error":
                suspended.clear()
                continue
            if len(parts) != 3 or parts[1] or not parts[2]:
                msg = f"diagnostics requires a category-wide warning policy: {spec}"
                raise ValueError(msg)
            if action not in {"error", "always", "default", "module", "once"}:
                msg = f"warning policy must retain visible evidence: {spec}"
                raise ValueError(msg)
            module_name, _, category_name = parts[2].rpartition(".")
            category = getattr(import_module(module_name or "builtins"), category_name)
            if not isinstance(category, type) or not issubclass(category, Warning):
                msg = f"warning policy category is not a Warning: {spec}"
                raise TypeError(msg)
            pending = [category]
            while pending:
                current = pending.pop()
                if action == "error":
                    suspended.discard(current.__name__)
                else:
                    suspended.add(current.__name__)
                pending.extend(current.__subclasses__())
        return suspended

    @classmethod
    def _extract_warnings(cls, report_log: Path, diag: m.Infra.DiagResult) -> None:
        """Count warning events independently of class names or terminal grouping."""
        lines = report_log.read_text(encoding=c.Cli.ENCODING_DEFAULT).splitlines()
        if not lines:
            msg = f"pytest report log contains no events: {report_log}"
            raise ValueError(msg)
        suspended = cls._suspended_warning_categories()
        for line in lines:
            event = m.Infra.PytestReportEvent.model_validate_json(line)
            if event.report_type == "WarningMessage":
                warning = (
                    f"{event.filename}:{event.lineno}: {event.category}: {event.message}"
                )
                diag.warning_lines.append(warning)
                if event.category in suspended:
                    diag.suspended_warning_lines.append(warning)

    def extract(
        self, junit_path: Path, log_path: Path, *, report_log: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics from JUnit XML, pytest log and explicit report-log.

        Args:
            junit_path: Path to JUnit XML result file.
            log_path: Path to raw pytest log output.
            report_log: Path to the structured pytest report-log.

        Returns:
            r with diagnostics dict containing counts and entries.

        """
        return self._extract_diagnostics(junit_path, log_path, report_log=report_log)

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
            blocking_warning_count=(
                len(diag.warning_lines) - len(diag.suspended_warning_lines)
            ),
            suspended_warning_count=len(diag.suspended_warning_lines),
            skipped_count=len(diag.skip_cases),
            failed_cases=diag.failed_cases,
            error_traces=diag.error_traces,
            warning_lines=diag.warning_lines,
            suspended_warning_lines=diag.suspended_warning_lines,
            skip_cases=diag.skip_cases,
            slow_entries=diag.slow_entries,
        )

    def _extract_diagnostics(
        self, junit_path: Path, log_path: Path, *, report_log: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract pytest diagnostics after input normalization."""
        self._read_log_text(log_path)
        diag = m.Infra.DiagResult()
        self._parse_xml(junit_path, diag)
        self._extract_warnings(report_log, diag)
        return r[m.Infra.PytestDiagnostics].ok(self._diagnostics_model(diag))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the pytest diagnostics CLI flow."""
        diagnostics = self.extract(
            self.junit, self.log_path, report_log=self.report_log
        ).unwrap()
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
            f"blocking_warning_count={diagnostics.blocking_warning_count}\n"
            f"suspended_warning_count={diagnostics.suspended_warning_count}\n"
            f"skipped_count={diagnostics.skipped_count}\n"
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPytestDiagExtractor"]
