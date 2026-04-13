"""Documentation auditor service."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import p, r
from flext_infra import (
    FlextInfraDocAuditorMixin,
    c,
    m,
    s,
    t,
    u,
)


class FlextInfraDocAuditor(s[bool], FlextInfraDocAuditorMixin):
    """Audit governed docs scopes using code-backed and policy-backed checks."""

    selected_projects: Annotated[
        t.StrSequence | None,
        Field(
            default=None,
            alias="projects",
            description="Selected projects",
        ),
    ] = None
    docs_output_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            alias="output_dir",
            description="Docs output dir",
        ),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR
    strict_mode: Annotated[
        bool,
        Field(
            default=False,
            alias="strict",
            description="Strict audit mode",
        ),
    ] = False

    @staticmethod
    def forbidden_term_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return forbidden-term issues configured for one scope."""
        return u.Infra.docs_text_token_issues(
            scope,
            tokens=u.Infra.docs_policy_list(
                scope,
                section="audit",
                key="forbidden_terms",
            ),
            issue_type="forbidden_term",
        )

    @staticmethod
    def placeholder_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return placeholder-text issues for one scope."""
        return u.Infra.docs_text_token_issues(
            scope,
            tokens=u.Infra.docs_policy_list(
                scope,
                section="audit",
                key="placeholder_terms",
            ),
            issue_type="placeholder",
        )

    def audit(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        params: m.Infra.AuditScopeParams | None = None,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Audit root and governed project docs scopes."""
        resolved_params = self._audit_params(workspace_root, params)
        return u.Infra.run_scoped(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self.audit_scope(scope, params=resolved_params),
        )

    def audit_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        params: m.Infra.AuditScopeParams,
    ) -> m.Infra.DocsPhaseReport:
        """Audit one scope and persist the standard reports."""
        checks = sorted(self.resolve_checks(params.check))
        issues = self._collect_issues(scope, checks)
        default_budget, per_scope_budget = params.budgets or (None, {})
        scope_budget = per_scope_budget.get(scope.name, default_budget)
        issue_count = len(issues)
        passed = True
        if params.strict:
            passed = (
                issue_count == 0
                if scope_budget is None
                else issue_count <= scope_budget
            )
        result = (
            c.Infra.STATUS_OK
            if passed and issue_count == 0
            else c.Infra.STATUS_WARN
            if passed
            else c.Infra.STATUS_FAIL
        )
        reason = (
            f"issues:{issue_count}"
            if scope_budget is None
            else f"issues:{issue_count};budget:{scope_budget}"
        )
        message = (
            "audit passed" if issue_count == 0 else f"found {issue_count} issue(s)"
        )
        report = m.Infra.DocsPhaseReport(
            phase="audit",
            scope=scope.name,
            result=result,
            reason=reason,
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
        self.write_audit_reports(
            scope,
            issues,
            set(checks),
            strict=params.strict,
            to_markdown_fn=u.Infra.docs_audit_markdown,
        )
        self.logger.info(
            "docs_audit_scope_completed",
            project=scope.name,
            phase="audit",
            result=report.result,
            reason=report.reason,
        )
        return report

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs audit flow."""
        result = self.audit(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
            params=m.Infra.AuditScopeParams(
                check="all",
                strict=self.strict_mode,
            ),
        )
        if result.failure:
            return r[bool].fail(result.error or "audit failed")
        failures = sum(1 for report in result.value if not report.passed)
        if failures:
            return r[bool].fail(f"Audit found {failures} failing scope(s)")
        return r[bool].ok(True)

    def _audit_params(
        self,
        workspace_root: Path,
        params: m.Infra.AuditScopeParams | None,
    ) -> m.Infra.AuditScopeParams:
        """Resolve runtime audit parameters and load default budgets when absent."""
        if params is not None and params.budgets is not None:
            return params
        budgets = self.load_audit_budgets(workspace_root)
        if params is None:
            return m.Infra.AuditScopeParams(
                check="all",
                strict=self.strict_mode,
                budgets=budgets,
            )
        return m.Infra.AuditScopeParams(
            check=params.check,
            strict=params.strict,
            budgets=budgets,
        )

    def _collect_issues(
        self,
        scope: m.Infra.DocScope,
        checks: t.StrSequence,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect issues for the requested check set in canonical order."""
        issues: list[m.Infra.AuditIssue] = []
        if "links" in checks:
            issues.extend(u.Infra.docs_broken_link_issues(scope))
        if "forbidden-terms" in checks:
            issues.extend(self.forbidden_term_issues(scope))
        if "placeholders" in checks:
            issues.extend(self.placeholder_issues(scope))
        if "stale-symbols" in checks:
            issues.extend(u.Infra.docs_stale_symbol_issues(scope))
        if "scope-boundary" in checks:
            issues.extend(u.Infra.docs_scope_boundary_issues(scope))
        if "generated-ownership" in checks:
            issues.extend(u.Infra.docs_generated_ownership_issues(scope))
        if "docstrings" in checks:
            issues.extend(u.Infra.docs_public_docstring_issues(scope))
        return tuple(issues)


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = ["FlextInfraDocAuditor"]
