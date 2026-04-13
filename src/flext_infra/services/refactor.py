"""Public refactor service mixin for the infra API facade."""

from __future__ import annotations

from flext_cli.api import cli as cli_service
from flext_infra import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)


class FlextInfraServiceRefactorMixin:
    """Expose refactor operations through the public infra facade."""

    def migrate_mro(
        self,
        params: m.Infra.RefactorMigrateMroInput,
    ) -> p.Result[m.Infra.MROMigrationReport]:
        """Run MRO migration through the public facade."""
        service = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=params.workspace_path,
        )
        report: m.Infra.MROMigrationReport = service.run(
            target=params.target,
            apply=params.apply,
        )
        cli_service.display_text(
            FlextInfraRefactorMigrateToClassMRO.render_text(report)
        )
        if report.errors:
            for error in report.errors:
                cli_service.display_message(
                    error,
                    message_type=c.Cli.MessageTypes.ERROR,
                )
            return r[m.Infra.MROMigrationReport].fail("MRO migration had errors")
        return r[m.Infra.MROMigrationReport].ok(report)

    def enforce_namespace(
        self,
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> p.Result[m.Infra.WorkspaceEnforcementReport]:
        """Run namespace enforcement through the public facade."""
        enforcer = FlextInfraNamespaceEnforcer(workspace_root=params.workspace_path)
        if params.diff:
            diff_output = enforcer.diff(project_names=params.project_names)
            cli_service.display_text(diff_output or "No changes detected.")
            report: m.Infra.WorkspaceEnforcementReport = enforcer.enforce(
                apply=False,
                project_names=params.project_names,
            )
            return r[m.Infra.WorkspaceEnforcementReport].ok(report)
        report: m.Infra.WorkspaceEnforcementReport = enforcer.enforce(
            apply=params.apply,
            project_names=params.project_names,
        )
        cli_service.display_text(FlextInfraNamespaceEnforcer.render_text(report))
        if report.has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found"
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)

    def run_refactor_census(
        self,
        params: m.Infra.RefactorCensusInput,
    ) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Run the public refactor census flow."""
        census = FlextInfraRefactorCensus()
        result = census.run(
            workspace_root=params.workspace_path,
            apply=params.apply,
            project_names=params.project_names,
            kind_names=params.kind_names,
            family_names=params.family_names,
            rule_names=params.rule_names,
            include_local_scopes=params.include_local_scopes,
        )
        if result.failure:
            return result
        report: m.Infra.Census.WorkspaceReport = result.unwrap()
        cli_service.display_text(FlextInfraRefactorCensus.render_text(report))
        if params.json_output_path is not None:
            json_path = params.json_output_path
            u.Infra.export_pydantic_json(report, json_path)
            cli_service.display_message(
                f"JSON report exported to: {json_path}",
                message_type=c.Cli.MessageTypes.INFO,
            )
        return r[m.Infra.Census.WorkspaceReport].ok(report)

    def run_accessor_migration(
        self,
        params: m.Infra.AccessorMigrationInput,
    ) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Run accessor migration preview/apply through the public facade."""
        service = FlextInfraAccessorMigrationOrchestrator(
            workspace=params.workspace_path,
            apply=params.apply,
            dry_run=params.dry_run,
            projects=list(params.project_names or []),
            preview_limit=params.preview_limit,
            gates=params.gates,
        )
        result = service.execute()
        if result.failure:
            return result
        report: m.Infra.AccessorMigrationReport = result.unwrap()
        cli_service.display_text(
            FlextInfraAccessorMigrationOrchestrator.render_text(report)
        )
        return r[m.Infra.AccessorMigrationReport].ok(report)


__all__: t.StrSequence = ("FlextInfraServiceRefactorMixin",)
