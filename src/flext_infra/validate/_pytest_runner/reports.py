"""Durable diagnostics and execution accounting for pytest."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from defusedxml import ElementTree as DefusedET

from flext_core import r
from flext_infra import c, m, u
from flext_infra.validate._pytest_runner.base import FlextInfraPytestRunnerBase
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraPytestRunnerReports(FlextInfraPytestRunnerBase):
    """Validate and persist pytest evidence."""

    @staticmethod
    def _failure_detail(message: str, pytest_log: Path) -> str:
        """Attach the bounded log tail to an artifact failure."""
        tail = "\n".join(pytest_log.read_text(encoding="utf-8").splitlines()[-40:])
        return f"{message}\n--- pytest.log (tail) ---\n{tail}" if tail else message

    def _accounting(
        self, junit: Path, log: Path, *, cache_restored: bool
    ) -> p.Result[m.Infra.TestmonRunAccounting]:
        """Parse typed executed/deselected accounting from durable artifacts."""
        if not junit.exists():
            raise FileNotFoundError(junit)
        if not junit.is_file():
            msg = f"JUnit must be a regular file: {junit}"
            raise ValueError(msg)
        if junit.stat().st_size == 0:
            msg = self._failure_detail(f"empty JUnit: {junit}", log)
            raise ValueError(msg)
        root = DefusedET.parse(junit).getroot()
        if root is None:
            msg = self._failure_detail(f"JUnit has no document root: {junit}", log)
            raise ValueError(msg)
        executed = sum(1 for _ in root.iter("testcase"))
        log_text = log.read_text(encoding="utf-8")
        deselected = sum(
            int(match.group("count"))
            for match in c.Infra.PYTEST_DESELECTED_RE.finditer(log_text)
        )
        accounting = m.Infra.TestmonRunAccounting(
            executed_count=executed,
            deselected_count=deselected,
            cache_restored=cache_restored,
        )
        if executed:
            return r.ok(accounting)
        msg = self._failure_detail("pytest executed zero tests", log)
        raise RuntimeError(msg)

    def _diagnostics(self, report_dir: Path) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics through the canonical typed service."""
        extractor = FlextInfraPytestDiagExtractor(
            repository_root=self.root,
            junit=report_dir / "junit.xml",
            log_path=report_dir / "pytest.log",
        )
        return extractor.extract(extractor.junit, extractor.log_path)

    def _validate_coverage(self, report_dir: Path) -> p.Result[bool]:
        """Require a non-empty coverage artifact and no hidden threshold failure."""
        coverage = report_dir / "coverage.xml"
        log = report_dir / "pytest.log"
        if not coverage.exists():
            raise FileNotFoundError(coverage)
        if not coverage.is_file():
            msg = f"coverage artifact must be a regular file: {coverage}"
            raise ValueError(msg)
        if coverage.stat().st_size == 0:
            msg = self._failure_detail(f"empty coverage artifact: {coverage}", log)
            raise ValueError(msg)
        body = log.read_text(encoding="utf-8")
        if c.Infra.PYTEST_COVERAGE_FAILURE_RE.search(body):
            msg = self._failure_detail("coverage threshold failed", log)
            raise RuntimeError(msg)
        return r.ok(True)

    @staticmethod
    def _write_diagnostics(
        report_dir: Path, diagnostics: m.Infra.PytestDiagnostics
    ) -> None:
        """Persist each typed diagnostics channel."""
        outputs: tuple[tuple[str, t.StrSequence, str], ...] = (
            ("failed-tests.txt", diagnostics.failed_cases, "\n\n"),
            ("errors.txt", diagnostics.error_traces, "\n\n"),
            ("warnings.txt", diagnostics.warning_lines, "\n"),
            ("skipped-tests.txt", diagnostics.skip_cases, "\n"),
            ("slowest-tests.txt", diagnostics.slow_entries, "\n"),
        )
        for filename, values, separator in outputs:
            body = separator.join(values) + ("\n" if values else "")
            u.Cli.atomic_write_text_file(report_dir / filename, body).unwrap()


__all__: list[str] = ["FlextInfraPytestRunnerReports"]
