"""Behavior tests for docstring coverage in the docs audit pipeline.

Real packages on disk (no mocks): a synthetic project with one documented
and one undocumented public export must report 50% coverage through both
the utility metric and the persisted audit reports.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.utilities import u
from tests import m
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

_PACKAGE_INIT = '''"""Demo package."""


def documented_fn() -> str:
    """Return a documented value."""
    return "documented"


def undocumented_fn() -> str:
    return "undocumented"


__all__ = ["documented_fn", "undocumented_fn"]
'''


def _write_project(tmp_path: Path) -> Path:
    project = tmp_path / "flext-demo"
    package = project / "src" / "flext_demo"
    package.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "flext-demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (package / "__init__.py").write_text(_PACKAGE_INIT, encoding="utf-8")
    return project


class TestsDocstringCoverage:
    """Unit under test: docstring coverage metric + audit report integration."""

    class TestCoverageUtility:
        """u.Infra.docstring_coverage aggregates the public target set."""

        def test_partial_docstrings_report_ratio(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)
            contract = u.Infra.public_contract(project, "flext_demo")

            coverage = u.Infra.docstring_coverage(project, contract)

            assert coverage.checked > 0
            assert coverage.documented > 0
            assert coverage.documented < coverage.checked
            tm.that(
                coverage.percent,
                eq=round(100.0 * coverage.documented / coverage.checked, 1),
            )

        def test_empty_contract_reports_full_coverage(self, tmp_path: Path) -> None:
            coverage = u.Infra.docstring_coverage(tmp_path, {})

            tm.that(coverage.checked, eq=0)
            tm.that(coverage.documented, eq=0)
            tm.that(coverage.percent, eq=pytest.approx(100.0))

        def test_root_scope_has_no_coverage_metric(self, tmp_path: Path) -> None:
            scope = m.Infra.DocScope(
                name="root", path=tmp_path, report_dir=tmp_path / ".reports/docs"
            )

            tm.that(u.Infra.docs_public_docstring_coverage(scope), none=True)

    class TestAuditReportIntegration:
        """audit_scope persists the coverage metric in markdown and JSON."""

        def test_project_scope_reports_include_coverage(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)
            report_dir = project / ".reports/docs"
            scope = m.Infra.DocScope(
                name="flext-demo",
                path=project,
                report_dir=report_dir,
                project_class="project",
                package_name="flext_demo",
            )

            FlextInfraDocAuditor().audit_scope(
                scope, params=m.Infra.AuditScopeParams(check="docstrings", strict=False)
            )

            markdown = (report_dir / "audit-report.md").read_text(encoding="utf-8")
            tm.that(markdown, has="Docstring coverage:")
            summary = json.loads(
                (report_dir / "audit-summary.json").read_text(encoding="utf-8")
            )
            metric = summary["summary"]["docstring_coverage"]
            assert metric["checked"] > 0
            assert 0.0 <= metric["percent"] < 100.0

    class TestExecuteChecksSelector:
        """execute() honors the CLI --checks selector (no hardcoded "all")."""

        def test_checks_docstrings_runs_only_that_check(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)

            result = FlextInfraDocAuditor(
                workspace_root=project, checks="docstrings"
            ).execute()

            tm.ok(result)
            summary = json.loads(
                (project / ".reports/docs/audit-summary.json").read_text(
                    encoding="utf-8"
                )
            )["summary"]
            tm.that(summary["checks"], eq=["docstrings"])
            assert summary["docstring_coverage"]["checked"] > 0

        def test_default_checks_runs_full_suite(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)

            result = FlextInfraDocAuditor(workspace_root=project).execute()

            tm.ok(result)
            summary = json.loads(
                (project / ".reports/docs/audit-summary.json").read_text(
                    encoding="utf-8"
                )
            )["summary"]
            tm.that(summary["checks"], has="docstrings")
            tm.that(summary["checks"], has="links")

    class TestDocstringMinThreshold:
        """--docstring-min replaces the interrogate --fail-under gate."""

        def test_coverage_below_minimum_fails_the_audit(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)

            result = FlextInfraDocAuditor(
                workspace_root=project, checks="docstrings", docstring_min=80.0
            ).execute()

            tm.fail(result)
            summary = json.loads(
                (project / ".reports/docs/audit-summary.json").read_text(
                    encoding="utf-8"
                )
            )["summary"]
            assert summary["docstring_coverage"]["percent"] < 80.0

        def test_coverage_above_minimum_keeps_audit_green(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)

            result = FlextInfraDocAuditor(
                workspace_root=project, checks="docstrings", docstring_min=40.0
            ).execute()

            tm.ok(result)

        def test_no_threshold_disables_the_gate(self, tmp_path: Path) -> None:
            project = _write_project(tmp_path)

            result = FlextInfraDocAuditor(
                workspace_root=project, checks="docstrings"
            ).execute()

            tm.ok(result)
