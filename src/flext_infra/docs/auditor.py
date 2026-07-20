"""Documentation auditor service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, override

from flext_infra import m, p, r, t, u
from flext_infra.docs._auditor_checks import FlextInfraDocAuditorChecksMixin
from flext_infra.docs._auditor_report import FlextInfraDocAuditorReportMixin
from flext_infra.docs.auditor_mixin import FlextInfraDocAuditorMixin
from flext_infra.docs.base import FlextInfraDocServiceBase

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraDocAuditor(
    FlextInfraDocServiceBase,
    FlextInfraDocAuditorMixin,
    FlextInfraDocAuditorChecksMixin,
    FlextInfraDocAuditorReportMixin,
):
    """Audit governed docs scopes using code-backed and policy-backed checks."""

    strict_mode: Annotated[
        bool, m.Field(alias="strict", description="Strict audit mode")
    ] = False

    # kimi-docs mro-3o9s: seletor de checks via CLI como --checks (flag --check é o
    # alias bool de check_only na base); default "all" = comportamento anterior.
    checks: Annotated[
        str, m.Field(description="Comma-separated audit checks (default: all)")
    ] = "all"

    # kimi-docs mro-3o9s: threshold de cobertura de docstrings via CLI
    # (--docstring-min); None = desativado. Substitui o interrogate paralelo.
    docstring_min: Annotated[
        float | None,
        m.Field(
            description="Minimum docstring coverage percent; breach fails the audit"
        ),
    ] = None

    def audit(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: Path | str | None = None,
        params: p.Infra.AuditScopeParams | None = None,
    ) -> p.Result[t.SequenceOf[p.Infra.DocsPhaseReport]]:
        """Audit root and governed project docs scopes."""
        resolved_params = self._audit_params(workspace_root, params)
        if resolved_params.failure:
            return r.fail(
                resolved_params.error or "audit parameter resolution failed",
                error_code=resolved_params.error_code,
            )
        return self.run_scoped_docs(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self.audit_scope(scope, params=resolved_params.value),
        )

    def audit_scope(
        self, scope: p.Infra.DocScope, *, params: p.Infra.AuditScopeParams
    ) -> p.Infra.DocsPhaseReport:
        """Audit one scope and persist the standard reports."""
        checks = sorted(self.resolve_checks(params.check))
        issues = self._collect_issues(scope, checks)
        docstring_coverage = (
            u.Infra.docs_public_docstring_coverage(scope)
            if "docstrings" in checks
            else None
        )
        report = self._audit_report(
            scope,
            issues=issues,
            checks=checks,
            params=params,
            docstring_coverage=docstring_coverage,
        )
        summary: t.JsonDict = {
            "scope": scope.name,
            "issues": len(issues),
            "checks": list(t.json_list_adapter().validate_python(sorted(checks))),
            "strict": params.strict,
            "report_dir": scope.report_dir.as_posix(),
        }
        if docstring_coverage is not None:
            summary["docstring_coverage"] = {
                "checked": docstring_coverage.checked,
                "documented": docstring_coverage.documented,
                "percent": docstring_coverage.percent,
            }
        issues_payload: t.JsonValueList = [
            {
                "file": issue.file,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "message": issue.message,
            }
            for issue in issues
        ]
        payload: t.JsonDict = {"summary": summary, "issues": issues_payload}
        _ = u.Cli.json_write(scope.report_dir / "audit-summary.json", payload)
        _ = u.Infra.write_markdown(
            scope.report_dir / "audit-report.md",
            u.Infra.docs_audit_markdown(scope, issues, docstring_coverage),
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
        return self._propagate_phase_outcome(
            "audit",
            self.audit(
                workspace_root=self.workspace_root,
                projects=self.selected_projects,
                output_dir=self.output_dir,
                params=m.Infra.AuditScopeParams(
                    check=self.checks,
                    strict=self.strict_mode,
                    docstring_min=self.docstring_min,
                ),
            ),
            failure_predicate=lambda report: not report.passed,
        )

    def _audit_params(
        self, workspace_root: Path, params: p.Infra.AuditScopeParams | None
    ) -> p.Result[p.Infra.AuditScopeParams]:
        """Resolve runtime audit parameters and load default budgets when absent."""
        if params is not None and params.budgets is not None:
            return r[p.Infra.AuditScopeParams].ok(params)
        budgets_result = self.load_audit_budgets(workspace_root)
        if budgets_result.failure:
            return r[p.Infra.AuditScopeParams].fail(
                budgets_result.error or "audit budget resolution failed",
                error_code=budgets_result.error_code,
            )
        budgets = budgets_result.value
        if params is None:
            resolved = m.Infra.AuditScopeParams(
                check="all",
                strict=self.strict_mode,
                docstring_min=self.docstring_min,
                budgets=budgets,
            )
        else:
            resolved = m.Infra.AuditScopeParams(
                check=params.check,
                strict=params.strict,
                docstring_min=params.docstring_min,
                budgets=budgets,
            )
        return r[p.Infra.AuditScopeParams].ok(resolved)


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = ["FlextInfraDocAuditor"]
