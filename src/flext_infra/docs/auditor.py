"""Documentation auditor service."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.base import s
from flext_infra.docs._auditor_mixin import FlextInfraDocAuditorMixin


class FlextInfraDocAuditor(s[bool], FlextInfraDocAuditorMixin):
    """Audit governed docs scopes using code-backed and policy-backed checks."""

    selected_projects: Annotated[
        t.StrSequence | None,
        Field(default=None, description="Selected projects", exclude=True),
    ] = None
    docs_output_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            description="Docs output dir",
            exclude=True,
        ),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR
    strict_mode: Annotated[
        bool,
        Field(default=False, description="Strict audit mode", exclude=True),
    ] = False

    @staticmethod
    def normalize_link(target: str) -> str:
        """Normalize one markdown link target."""
        return u.Infra.docs_normalize_link(target)

    @staticmethod
    def should_skip_target(raw: str, target: str) -> bool:
        """Return whether one raw markdown target should be ignored."""
        return u.Infra.docs_should_skip_target(raw, target)

    @staticmethod
    def is_external(target: str) -> bool:
        """Return whether one target points outside the repository."""
        return u.Infra.docs_is_external(target)

    @staticmethod
    def to_markdown(
        scope: m.Infra.DocScope,
        issues: Sequence[m.Infra.AuditIssue],
    ) -> t.StrSequence:
        """Render the canonical markdown report for one audit scope."""
        return u.Infra.docs_audit_markdown(scope, issues)

    @staticmethod
    def broken_link_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return broken internal link issues for one scope."""
        return u.Infra.docs_broken_link_issues(scope)

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

    @staticmethod
    def stale_symbol_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return stale forward-guidance symbol issues for one scope."""
        return u.Infra.docs_stale_symbol_issues(scope)

    @staticmethod
    def scope_boundary_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return root scope-boundary violations."""
        return u.Infra.docs_scope_boundary_issues(scope)

    @staticmethod
    def generated_ownership_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return manual API page ownership violations."""
        return u.Infra.docs_generated_ownership_issues(scope)

    @staticmethod
    def public_docstring_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return missing public docstring issues."""
        return u.Infra.docs_public_docstring_issues(scope)

    def audit(
        self,
        workspace_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        params: m.Infra.AuditScopeParams | None = None,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
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
            c.Infra.Status.OK
            if passed and issue_count == 0
            else c.Infra.Status.WARN
            if passed
            else c.Infra.Status.FAIL
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
            to_markdown_fn=self.to_markdown,
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
    def execute(self) -> r[bool]:
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
        if result.is_failure:
            return r[bool].fail(result.error or "audit failed")
        failures = sum(1 for report in result.value if not report.passed)
        if failures:
            return r[bool].fail(f"Audit found {failures} failing scope(s)")
        return r[bool].ok(True)

    @classmethod
    @override
    def execute_command(
        cls,
        params: s[bool] | m.Infra.DocsAuditInput,
    ) -> r[bool]:
        """Normalize docs CLI input into the canonical auditor service model."""
        if isinstance(params, m.Infra.DocsAuditInput):
            service = cls.model_validate({
                "workspace_root": params.workspace_path,
                "apply_changes": params.apply,
                "check_only": params.check,
                "selected_projects": params.project_names,
                "docs_output_dir": params.output_dir,
                "strict_mode": params.strict,
            })
            return service.execute()
        return params.execute()

    @classmethod
    def main(cls, argv: t.StrSequence | None = None) -> int:
        """CLI entrypoint retained for compatibility with the existing tests."""
        parser = u.Infra.create_parser(
            "flext-infra docs audit",
            "Audit generated and curated FLEXT documentation.",
            flags=u.Infra.SharedFlags(
                include_apply=False,
                include_check=True,
                include_project=True,
            ),
        )
        _ = parser.add_argument(
            "--output-dir",
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            help="Report output directory",
        )
        _ = parser.add_argument(
            "--strict",
            action="store_true",
            default=False,
            help="Fail when issues exceed the allowed budget",
        )
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        result = cls().audit(
            cli.workspace,
            projects=cli.projects,
            output_dir=str(args.output_dir),
            params=m.Infra.AuditScopeParams(
                check="all",
                strict=bool(args.strict),
            ),
        )
        if result.is_failure:
            return 1
        return 0 if all(report.passed for report in result.value) else 1

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
        checks: Sequence[str],
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect issues for the requested check set in canonical order."""
        issues: list[m.Infra.AuditIssue] = []
        if "links" in checks:
            issues.extend(self.broken_link_issues(scope))
        if "forbidden-terms" in checks:
            issues.extend(self.forbidden_term_issues(scope))
        if "placeholders" in checks:
            issues.extend(self.placeholder_issues(scope))
        if "stale-symbols" in checks:
            issues.extend(self.stale_symbol_issues(scope))
        if "scope-boundary" in checks:
            issues.extend(self.scope_boundary_issues(scope))
        if "generated-ownership" in checks:
            issues.extend(self.generated_ownership_issues(scope))
        if "docstrings" in checks:
            issues.extend(self.public_docstring_issues(scope))
        return tuple(issues)


main = FlextInfraDocAuditor.main


if __name__ == "__main__":
    sys.exit(FlextInfraDocAuditor.main())


__all__ = ["FlextInfraDocAuditor", "main"]
