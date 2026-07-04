"""Report construction helpers for FlextInfraDocAuditor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraDocAuditorReportMixin:
    """Mixin for documentation audit report construction."""

    @staticmethod
    def _audit_passed(
        *,
        issue_count: int,
        params: m.Infra.AuditScopeParams,
        scope_budget: int | None,
    ) -> bool:
        """Return strict/non-strict audit pass decision."""
        if not params.strict:
            return True
        return issue_count == 0 if scope_budget is None else issue_count <= scope_budget

    def _audit_report(
        self,
        scope: m.Infra.DocScope,
        *,
        issues: t.SequenceOf[m.Infra.AuditIssue],
        checks: t.StrSequence,
        params: m.Infra.AuditScopeParams,
    ) -> m.Infra.DocsPhaseReport:
        """Build the standard docs audit phase report."""
        default_budget, per_scope_budget = params.budgets or (None, {})
        scope_budget = per_scope_budget.get(scope.name, default_budget)
        issue_count = len(issues)
        passed = self._audit_passed(
            issue_count=issue_count,
            params=params,
            scope_budget=scope_budget,
        )
        result = (
            c.Infra.ResultStatus.OK
            if passed and issue_count == 0
            else c.Infra.ResultStatus.WARN
            if passed
            else c.Infra.ResultStatus.FAIL
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
            message=(
                "audit passed" if issue_count == 0 else f"found {issue_count} issue(s)"
            ),
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
