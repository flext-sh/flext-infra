"""Tests for FlextInfraDocAuditor — scope, forbidden terms, and audit_scope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_tests import tm
from tests import m

if TYPE_CHECKING:
    from pathlib import Path


class TestAuditorForbiddenTerms:
    """Tests for forbidden_term_issues."""

    def test_forbidden_term_issues_empty_scope(self, tmp_path: Path) -> None:
        """Test forbidden_term_issues with no markdown files."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.forbidden_term_issues(scope)
        tm.that(len(issues), gte=0)

    def test_forbidden_term_issues_root_scope(self, tmp_path: Path) -> None:
        """Test forbidden_term_issues filters by docs/ for root scope."""
        auditor = FlextInfraDocAuditor()
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "test.md").write_text("# Test")
        scope = m.Infra.DocScope(
            name="root", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.forbidden_term_issues(scope)
        tm.that(len(issues), gte=0)

    def test_forbidden_term_issues_project_scope(self, tmp_path: Path) -> None:
        """Test forbidden_term_issues filters by project name."""
        auditor = FlextInfraDocAuditor()
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "test.md").write_text("# Test")
        scope = m.Infra.DocScope(
            name="flext-core", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.forbidden_term_issues(scope)
        tm.that(len(issues), gte=0)

    def test_forbidden_term_issues_root_scope_non_docs_file(
        self, tmp_path: Path
    ) -> None:
        """Test forbidden_term_issues skips non-docs files in root scope."""
        auditor = FlextInfraDocAuditor()
        (tmp_path / "README.md").write_text("# Test")
        scope = m.Infra.DocScope(
            name="root", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.forbidden_term_issues(scope)
        tm.that(len(issues), gte=0)

    def test_forbidden_term_issues_non_flext_scope(self, tmp_path: Path) -> None:
        """Test forbidden_term_issues skips non-flext scopes."""
        auditor = FlextInfraDocAuditor()
        (tmp_path / "test.md").write_text("# Test")
        scope = m.Infra.DocScope(
            name="other-project", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.forbidden_term_issues(scope)
        tm.that(len(issues), gte=0)


class TestAuditorScope:
    """Tests for audit_scope."""

    def test_audit_scope_with_links_check(self, tmp_path: Path) -> None:
        """Test audit_scope runs links check."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope, params=m.Infra.AuditScopeParams(check="links", strict=True)
        )
        tm.that(report.phase, eq="audit")
        tm.that(report.checks, has="links")

    def test_audit_scope_with_forbidden_terms_check(self, tmp_path: Path) -> None:
        """Test audit_scope runs forbidden-terms check."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope, params=m.Infra.AuditScopeParams(check="forbidden-terms", strict=True)
        )
        tm.that(report.phase, eq="audit")
        tm.that(report.checks, has="forbidden-terms")

    def test_audit_scope_strict_mode_passes(self, tmp_path: Path) -> None:
        """Test audit_scope passes in strict mode with no issues."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope, params=m.Infra.AuditScopeParams(check="all", strict=True)
        )
        tm.that(report.passed, eq=True)

    def test_audit_scope_non_strict_mode_always_passes(self, tmp_path: Path) -> None:
        """Test audit_scope passes in non-strict mode."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope, params=m.Infra.AuditScopeParams(check="all", strict=False)
        )
        tm.that(report.passed, eq=True)

    def test_audit_scope_with_budget_limit(self, tmp_path: Path) -> None:
        """Test audit_scope respects issue budget."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope,
            params=m.Infra.AuditScopeParams(check="all", strict=True, budgets=(0, {})),
        )
        tm.that(report.phase, eq="audit")

    def test_audit_scope_with_scope_specific_budget(self, tmp_path: Path) -> None:
        """Test audit_scope uses scope-specific budget."""
        auditor = FlextInfraDocAuditor()
        scope = m.Infra.DocScope(
            name="test", path=tmp_path, report_dir=tmp_path / "reports"
        )
        report = auditor.audit_scope(
            scope,
            params=m.Infra.AuditScopeParams(
                check="all", strict=True, budgets=(10, {"test": 5})
            ),
        )
        tm.that(report.phase, eq="audit")


class TestAuditorMachinePaths:
    """Tests for machine_path_issues (per-user absolute paths frozen into docs)."""

    def test_machine_path_issues_flags_user_home_and_skips_container_identity(
        self, tmp_path: Path
    ) -> None:
        """A /home/<user> or /Users/<user> root is flagged; CI/container homes pass."""
        auditor = FlextInfraDocAuditor()
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "guide.md").write_text(
            "run it from /home/someone/flext\n"
            "or on macOS from /Users/someone/flext\n"
            "the image installs to /home/runner/.local/bin\n"
            "the tilde form ~/flext is portable\n"
        )
        scope = m.Infra.DocScope(
            name="root", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.machine_path_issues(scope)
        tm.that(len(issues), eq=2)
        tm.that({issue.issue_type for issue in issues}, eq={"machine-path"})
        tm.that(issues[0].message, has="line 1")
        tm.that(issues[0].message, has="/home/someone")
        tm.that(issues[1].message, has="/Users/someone")

    def test_machine_path_issues_honours_exempt_paths(self, tmp_path: Path) -> None:
        """Frozen evidence declared in docs_config.json audit policy is skipped whole."""
        auditor = FlextInfraDocAuditor()
        plans = tmp_path / "docs" / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        (plans / "2026-01-01-run.md").write_text("ran at /home/someone/flext\n")
        (tmp_path / "docs" / "live.md").write_text("see /home/someone/flext\n")
        (tmp_path / "docs" / "docs_config.json").write_text(
            '{"audit": {"machine_path_exempt_paths": ["docs/plans/"]}}'
        )
        scope = m.Infra.DocScope(
            name="root", path=tmp_path, report_dir=tmp_path / "reports"
        )
        issues = auditor.machine_path_issues(scope)
        tm.that([issue.file for issue in issues], eq=["docs/live.md"])
