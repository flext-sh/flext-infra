"""CLI registration for the refactor domain."""

from __future__ import annotations

from flext_cli import cli
from flext_core import r

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)
from flext_infra.refactor.census import FlextInfraRefactorCensus
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCliRefactor(FlextInfraCliGroupBase):
    """Owns refactor CLI route declarations."""

    @staticmethod
    def _migrate_mro(
        params: m.Infra.RefactorMigrateMroInput,
    ) -> p.Result[m.Infra.MROMigrationReport]:
        service = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=params.workspace_path
        )
        report: m.Infra.MROMigrationReport = service.run(
            target=params.target,
            apply=params.apply,
            project_names=params.project_names,
        )
        cli.display_text(FlextInfraRefactorMigrateToClassMRO.render_text(report))
        if report.errors:
            for error in report.errors:
                cli.display_message(error, message_type=c.Cli.MessageTypes.ERROR)
            return r[m.Infra.MROMigrationReport].fail("MRO migration had errors")
        return r[m.Infra.MROMigrationReport].ok(report)

    @staticmethod
    def _enforce_namespace(
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> p.Result[m.Infra.WorkspaceEnforcementReport]:
        enforcer = FlextInfraNamespaceEnforcer(workspace_root=params.workspace_path)
        if params.diff:
            diff_output = enforcer.diff(project_names=params.project_names)
            cli.display_text(diff_output or "No changes detected.")
            report: m.Infra.WorkspaceEnforcementReport = enforcer.enforce(
                apply=False,
                project_names=params.project_names,
            )
            return r[m.Infra.WorkspaceEnforcementReport].ok(report)
        report = enforcer.enforce(
            apply=params.apply, project_names=params.project_names
        )
        cli.display_text(FlextInfraNamespaceEnforcer.render_text(report))
        if report.has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found"
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)

    @staticmethod
    def _run_refactor_census(
        params: m.Infra.RefactorCensusInput,
    ) -> p.Result[m.Infra.Census.WorkspaceReport]:
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
        cli.display_text(FlextInfraRefactorCensus.render_text(report))
        if params.json_output_path is not None:
            u.Infra.export_pydantic_json(report, params.json_output_path)
            cli.display_message(
                f"JSON report exported to: {params.json_output_path}",
                message_type=c.Cli.MessageTypes.INFO,
            )
        return result

    @staticmethod
    def _run_accessor_migration(
        params: m.Infra.AccessorMigrationInput,
    ) -> p.Result[m.Infra.AccessorMigrationReport]:
        service = FlextInfraAccessorMigrationOrchestrator(
            workspace=params.workspace_path,
            dry_run=params.dry_run,
            projects=list(params.project_names or []),
            preview_limit=params.preview_limit,
            gates=params.gates,
        )
        result: p.Result[m.Infra.AccessorMigrationReport] = type(
            service
        ).execute_command(
            service,
        )
        if result.failure:
            return result
        cli.display_text(
            FlextInfraAccessorMigrationOrchestrator.render_text(result.unwrap())
        )
        return result

    routes = (
        FlextInfraCliGroupBase.route(
            name="migrate-mro",
            help_text="Migrate loose declarations into MRO facade classes",
            model_cls=m.Infra.RefactorMigrateMroInput,
            handler=_migrate_mro,
        ),
        FlextInfraCliGroupBase.route(
            name="namespace-enforce",
            help_text="Scan workspace for namespace governance violations",
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=_enforce_namespace,
        ),
        FlextInfraCliGroupBase.route(
            name="census",
            help_text="Run a Rope-only workspace census for Python objects",
            model_cls=m.Infra.RefactorCensusInput,
            handler=_run_refactor_census,
        ),
        FlextInfraCliGroupBase.route(
            name="accessor-migrate",
            help_text="Preview or apply automated get_/set_/is_ migration",
            model_cls=m.Infra.AccessorMigrationInput,
            handler=_run_accessor_migration,
        ),
    )

    def register_refactor(self, app: t.Cli.CliApp) -> None:
        """Register refactor routes."""
        FlextInfraCliRefactor.register_routes(app)


__all__: list[str] = ["FlextInfraCliRefactor"]
