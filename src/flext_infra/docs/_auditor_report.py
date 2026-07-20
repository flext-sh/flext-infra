"""Report construction helpers for FlextInfraDocAuditor.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, p, t


class FlextInfraDocAuditorReportMixin:
    """Mixin for documentation audit report construction."""

    @staticmethod
    def _audit_passed(
        *, issue_count: int, params: p.Infra.AuditScopeParams, scope_budget: int | None
    ) -> bool:
        """Return strict/non-strict audit pass decision."""
        if not params.strict:
            return True
        return issue_count == 0 if scope_budget is None else issue_count <= scope_budget

    def _audit_report(
        self,
        scope: p.Infra.DocScope,
        *,
        issues: t.SequenceOf[p.Infra.AuditIssue],
        checks: t.StrSequence,
        params: p.Infra.AuditScopeParams,
        docstring_coverage: p.Infra.DocstringCoverage | None = None,
    ) -> p.Infra.DocsPhaseReport:
        """Build the standard docs audit phase report."""
        budgets: tuple[int | None, t.IntMapping] = params.budgets or (None, {})
        default_budget, per_scope_budget = budgets
        scope_budget = per_scope_budget.get(scope.name, default_budget)
        issue_count = len(issues)
        coverage_breached = (
            params.docstring_min is not None
            and docstring_coverage is not None
            and docstring_coverage.percent < params.docstring_min
        )
        passed = (
            self._audit_passed(
                issue_count=issue_count, params=params, scope_budget=scope_budget
            )
            and not coverage_breached
        )
        result = (
            c.Infra.ResultStatus.OK
            if passed and issue_count == 0
            else c.Infra.ResultStatus.WARN
            if passed
            else c.Infra.ResultStatus.FAIL
        )
        message = (
            f"docstring coverage {docstring_coverage.percent}% below minimum "
            f"{params.docstring_min}%"
            if coverage_breached and docstring_coverage is not None
            else "audit passed"
            if issue_count == 0
            else f"found {issue_count} issue(s)"
        )
        return m.Infra.DocsPhaseReport(
            phase="audit",
            scope=scope.name,
            result=result,
            reason=(
                f"issues:{issue_count}"
                if scope_budget is None
                else f"issues:{issue_count};budget:{scope_budget}"
            ),
            message=message,
            checks=checks,
            strict=params.strict,
            passed=passed,
            items=[
                m.Infra.DocsPhaseItemModel(
                    phase="audit",
                    file=issue.file,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    message=issue.message,
                )
                for issue in issues
            ],
        )


__all__: list[str] = ["FlextInfraDocAuditorReportMixin"]
