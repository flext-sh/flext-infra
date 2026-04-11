"""Public refactor service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_cli.api import cli as cli_service
from flext_core import r
from flext_infra import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
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
    ) -> r[m.Infra.MROMigrationReport]:
        """Run MRO migration through the public facade."""
        service = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=params.workspace_path,
        )
        report = service.run(target=params.target, apply=params.apply)
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
    ) -> r[m.Infra.WorkspaceEnforcementReport]:
        """Run namespace enforcement through the public facade."""
        enforcer = FlextInfraNamespaceEnforcer(workspace_root=params.workspace_path)
        if params.diff:
            diff_output = enforcer.diff(project_names=params.project_names)
            cli_service.display_text(diff_output or "No changes detected.")
            return r[m.Infra.WorkspaceEnforcementReport].ok(
                enforcer.enforce(apply=False, project_names=params.project_names)
            )
        report = enforcer.enforce(
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
    ) -> r[m.Infra.UtilitiesCensusReport]:
        """Run the public refactor census flow."""
        census = FlextInfraRefactorCensus()
        result = census.run(
            workspace_root=params.workspace_path,
            target=u.Infra.build_mro_target(params.family),
        )
        if result.failure:
            return result
        report = result.value
        cli_service.display_text(FlextInfraRefactorCensus.render_text(report))
        if params.json_output:
            json_path = Path(params.json_output).resolve()
            u.Infra.export_pydantic_json(report, json_path)
            cli_service.display_message(
                f"JSON report exported to: {json_path}",
                message_type=c.Cli.MessageTypes.INFO,
            )
        return result

    def run_accessor_migration(
        self,
        params: m.Infra.AccessorMigrationInput,
    ) -> r[m.Infra.AccessorMigrationReport]:
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
        cli_service.display_text(
            FlextInfraAccessorMigrationOrchestrator.render_text(result.value)
        )
        return result


__all__: Sequence[str] = ("FlextInfraServiceRefactorMixin",)
