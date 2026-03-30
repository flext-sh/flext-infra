"""CLI mixin for refactor commands."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r

from flext_infra import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    m,
    t,
    u,
)

if TYPE_CHECKING:
    import typer


class FlextInfraCliRefactor:
    """Refactor CLI group — composed into FlextInfraCli via MRO."""

    def register_refactor(self, app: typer.Typer) -> None:
        """Register refactor commands on the given Typer app."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="centralize-pydantic",
                help_text="Centralize BaseModel/TypedDict/dict-like aliases into _models.py",
                model_cls=m.Infra.RefactorCentralizeInput,
                handler=self._handle_centralize_pydantic,
                failure_message="Pydantic centralization failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="migrate-mro",
                help_text="Migrate loose declarations into MRO facade classes",
                model_cls=m.Infra.RefactorMigrateMroInput,
                handler=self._handle_migrate_mro,
                failure_message="MRO migration failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="namespace-enforce",
                help_text="Scan workspace for namespace governance violations",
                model_cls=m.Infra.RefactorNamespaceEnforceInput,
                handler=self._handle_namespace_enforce,
                failure_message="Namespace enforcement failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="ultrawork-models",
                help_text="Run full centralization + MRO + namespace workflow",
                model_cls=m.Infra.RefactorUltraworkModelsInput,
                handler=self._handle_ultrawork_models,
                failure_message="Ultrawork models failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="census",
                help_text="Run AST/CST census of MRO family method usage",
                model_cls=m.Infra.RefactorCensusInput,
                handler=self._handle_refactor_census,
                failure_message="Census failed",
            ),
        )

    @staticmethod
    def _handle_centralize_pydantic(
        params: m.Infra.RefactorCentralizeInput,
    ) -> r[Mapping[str, int]]:
        """Run pydantic centralization workflow for the workspace."""
        summary = u.Infra.centralize_workspace(
            Path(params.workspace),
            apply=params.apply,
            normalize_remaining=params.normalize_remaining,
        )
        return r[Mapping[str, int]].ok(summary)

    @staticmethod
    def _handle_migrate_mro(
        params: m.Infra.RefactorMigrateMroInput,
    ) -> r[m.Infra.MROMigrationReport]:
        """Run MRO migration workflow for the selected target scope."""
        service = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=Path(params.workspace),
        )
        report = service.run(target=params.target, apply=params.apply)
        cli.display_text(FlextInfraRefactorMigrateToClassMRO.render_text(report))
        if report.errors:
            for error in report.errors:
                cli.display_message(error, message_type="error")
            return r[m.Infra.MROMigrationReport].fail("MRO migration had errors")
        return r[m.Infra.MROMigrationReport].ok(report)

    @staticmethod
    def _handle_namespace_enforce(
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> r[m.Infra.WorkspaceEnforcementReport]:
        """Run namespace enforcement checks and optionally apply fixes."""
        project_names: t.StrSequence | None = None
        if params.project:
            project_names = u.Infra.project_names_from_values(params.project)
        enforcer = FlextInfraNamespaceEnforcer(
            workspace_root=Path(params.workspace),
        )
        if params.diff:
            diff_output = enforcer.diff(project_names=project_names)
            if diff_output:
                cli.display_text(diff_output)
            else:
                cli.display_text("No changes detected.")
            return r[m.Infra.WorkspaceEnforcementReport].ok(
                enforcer.enforce(apply=False, project_names=project_names),
            )
        report = enforcer.enforce(apply=params.apply, project_names=project_names)
        cli.display_text(FlextInfraNamespaceEnforcer.render_text(report))
        if report.has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found",
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)

    @staticmethod
    def _handle_ultrawork_models(
        params: m.Infra.RefactorUltraworkModelsInput,
    ) -> r[Mapping[str, int]]:
        """Run centralization, MRO migration, and namespace enforcement together."""
        workspace = Path(params.workspace)
        centralize_summary = u.Infra.centralize_workspace(
            workspace,
            apply=params.apply,
            normalize_remaining=params.normalize_remaining,
        )
        mro_report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=workspace,
        ).run(target="all", apply=params.apply)
        namespace_report = FlextInfraNamespaceEnforcer(
            workspace_root=workspace,
        ).enforce(apply=params.apply)

        combined: Mapping[str, int] = {
            **centralize_summary,
            "mro_remaining_violations": mro_report.remaining_violations,
            "mro_files_scanned": mro_report.files_scanned,
            "mro_files_with_candidates": mro_report.files_with_candidates,
            "mro_failures": mro_report.mro_failures,
            "namespace_loose_objects": namespace_report.total_loose_objects,
            "namespace_import_violations": namespace_report.total_import_violations,
            "namespace_cyclic_imports": namespace_report.total_cyclic_imports,
            "namespace_runtime_alias_violations": namespace_report.total_runtime_alias_violations,
            "namespace_manual_protocols": namespace_report.total_manual_protocol_violations,
            "namespace_manual_typing_aliases": namespace_report.total_manual_typing_violations,
            "namespace_compatibility_aliases": namespace_report.total_compatibility_alias_violations,
            "namespace_parse_failures": namespace_report.total_parse_failures,
            "namespace_files_scanned": namespace_report.total_files_scanned,
        }
        if mro_report.errors:
            for error in mro_report.errors:
                cli.display_message(error, message_type="error")
            return r[Mapping[str, int]].fail("MRO migration had errors")
        return r[Mapping[str, int]].ok(combined)

    @staticmethod
    def _handle_refactor_census(
        params: m.Infra.RefactorCensusInput,
    ) -> r[m.Infra.UtilitiesCensusReport]:
        """Run method-usage census and optionally export JSON report."""
        census = FlextInfraRefactorCensus()
        target = u.Infra.build_mro_target(params.family)
        result = census.run(workspace_root=Path(params.workspace), target=target)
        if result.is_failure:
            return result
        report = result.value
        cli.display_text(FlextInfraRefactorCensus.render_text(report))
        if params.json_output:
            json_path = Path(params.json_output).resolve()
            u.Infra.export_pydantic_json(report, json_path)
            cli.display_message(
                f"JSON report exported to: {json_path}",
                message_type="info",
            )
        return result
