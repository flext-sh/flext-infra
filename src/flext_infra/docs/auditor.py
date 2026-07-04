"""Documentation auditor service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, override

from flext_infra.docs._auditor_checks import FlextInfraDocAuditorChecksMixin
from flext_infra.docs._auditor_report import FlextInfraDocAuditorReportMixin
from flext_infra.docs.auditor_mixin import FlextInfraDocAuditorMixin
from flext_infra.docs.base import FlextInfraDocServiceBase
from flext_infra.models import m
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraDocAuditor(
    FlextInfraDocServiceBase,
    FlextInfraDocAuditorMixin,
    FlextInfraDocAuditorChecksMixin,
    FlextInfraDocAuditorReportMixin,
):
    """Audit governed docs scopes using code-backed and policy-backed checks."""

    strict_mode: Annotated[
        bool,
        m.Field(
            alias="strict",
            description="Strict audit mode",
        ),
    ] = False

    def audit(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: Path | str | None = None,
        params: m.Infra.AuditScopeParams | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Audit root and governed project docs scopes."""
        resolved_params = self._audit_params(workspace_root, params)
        return self.run_scoped_docs(
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
        report = self._audit_report(
            scope,
            issues=issues,
            checks=checks,
            params=params,
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
        return self._propagate_phase_outcome(
            "audit",
            self.audit(
                workspace_root=self.workspace_root,
                projects=self.selected_projects,
                output_dir=self.output_dir,
                params=m.Infra.AuditScopeParams(
                    check="all",
                    strict=self.strict_mode,
                ),
            ),
            failure_predicate=lambda report: not report.passed,
        )

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


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = ["FlextInfraDocAuditor"]
