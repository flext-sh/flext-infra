"""CLI mixin for refactor commands."""

from __future__ import annotations

from pathlib import Path

from flext_cli import cli as cli_service
from flext_core import r
from flext_infra import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    m,
    t,
    u,
)


class FlextInfraCliRefactor:
    """Refactor CLI group — composed into FlextInfraCli via MRO."""

    def register_refactor(self, app: t.Cli.TyperApp) -> None:
        """Register refactor commands on the given Typer app."""
        cls = type(self)
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="centralize-pydantic",
                    help_text="Centralize BaseModel/TypedDict/dict-like aliases into _models.py",
                    model_cls=m.Infra.RefactorCentralizeInput,
                    handler=cls._handle_centralize_pydantic,
                    failure_message="Pydantic centralization failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="migrate-mro",
                    help_text="Migrate loose declarations into MRO facade classes",
                    model_cls=m.Infra.RefactorMigrateMroInput,
                    handler=cls._handle_migrate_mro,
                    failure_message="MRO migration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="namespace-enforce",
                    help_text="Scan workspace for namespace governance violations",
                    model_cls=m.Infra.RefactorNamespaceEnforceInput,
                    handler=cls._handle_namespace_enforce,
                    failure_message="Namespace enforcement failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="migrate-runtime-alias-imports",
                    help_text="Move runtime aliases like r/s from flext_core to local MRO imports",
                    model_cls=m.Infra.RefactorMigrateRuntimeAliasImportsInput,
                    handler=cls._handle_migrate_runtime_alias_imports,
                    failure_message="Runtime alias import migration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="ultrawork-models",
                    help_text="Run full centralization + MRO + namespace workflow",
                    model_cls=m.Infra.RefactorUltraworkModelsInput,
                    handler=cls._handle_ultrawork_models,
                    failure_message="Ultrawork models failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="census",
                    help_text="Run AST/CST census of MRO family method usage",
                    model_cls=m.Infra.RefactorCensusInput,
                    handler=cls._handle_refactor_census,
                    failure_message="Census failed",
                ),
            ],
        )

    @staticmethod
    def _handle_centralize_pydantic(
        params: m.Infra.RefactorCentralizeInput,
    ) -> r[t.IntMapping]:
        """Run pydantic centralization workflow for the workspace."""
        summary = u.Infra.centralize_workspace(
            params.workspace_path,
            apply=params.apply,
            normalize_remaining=params.normalize_remaining,
        )
        return r[t.IntMapping].ok(summary)

    @staticmethod
    def _handle_migrate_mro(
        params: m.Infra.RefactorMigrateMroInput,
    ) -> r[m.Infra.MROMigrationReport]:
        """Run MRO migration workflow for the selected target scope."""
        service = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=params.workspace_path,
        )
        report = service.run(target=params.target, apply=params.apply)
        cli_service.display_text(
            FlextInfraRefactorMigrateToClassMRO.render_text(report)
        )
        if report.errors:
            for error in report.errors:
                cli_service.display_message(error, message_type="error")
            return r[m.Infra.MROMigrationReport].fail("MRO migration had errors")
        return r[m.Infra.MROMigrationReport].ok(report)

    @staticmethod
    def _handle_namespace_enforce(
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> r[m.Infra.WorkspaceEnforcementReport]:
        """Run namespace enforcement checks and optionally apply fixes."""
        project_names: t.StrSequence | None = None
        if params.project:
            project_names = u.Cli.project_names_from_values(params.project)
        enforcer = FlextInfraNamespaceEnforcer(
            workspace_root=params.workspace_path,
        )
        if params.diff:
            diff_output = enforcer.diff(project_names=project_names)
            if diff_output:
                cli_service.display_text(diff_output)
            else:
                cli_service.display_text("No changes detected.")
            return r[m.Infra.WorkspaceEnforcementReport].ok(
                enforcer.enforce(apply=False, project_names=project_names),
            )
        report = enforcer.enforce(apply=params.apply, project_names=project_names)
        cli_service.display_text(FlextInfraNamespaceEnforcer.render_text(report))
        if report.has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found",
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)

    @staticmethod
    def _handle_migrate_runtime_alias_imports(
        params: m.Infra.RefactorMigrateRuntimeAliasImportsInput,
    ) -> r[t.IntMapping]:
        """Move selected runtime aliases from `flext_core` to the local MRO root."""
        project_names: t.StrSequence | None = None
        if params.project:
            project_names = u.Cli.project_names_from_values(params.project)
        aliases = [item.strip() for item in params.aliases.split(",") if item.strip()]
        results = u.Infra.migrate_runtime_alias_imports(
            workspace_root=params.workspace_path,
            aliases=aliases,
            apply=params.apply,
            project_names=project_names,
        )
        summary: t.MutableIntMapping = {
            "files_changed": 0,
            "files_failed": 0,
            "files_planned": 0,
            "aliases_migrated": 0,
            "aliases_skipped_unsafe": 0,
            "aliases_skipped_missing_export": 0,
        }
        for result in results:
            if not result.success:
                summary["files_failed"] += 1
                continue
            if result.modified:
                summary["files_changed"] += 1
            elif any(
                change.startswith("planned runtime alias import")
                for change in result.changes
            ):
                summary["files_planned"] += 1
            for change in result.changes:
                if "runtime alias import" not in change:
                    continue
                if change.startswith("migrated"):
                    summary["aliases_migrated"] += 1
                elif "unsafe" in change:
                    summary["aliases_skipped_unsafe"] += 1
                elif "missing export" in change:
                    summary["aliases_skipped_missing_export"] += 1
        cli_service.display_text(
            "\n".join([
                f"Files changed: {summary['files_changed']}",
                f"Files planned: {summary['files_planned']}",
                f"Files failed: {summary['files_failed']}",
                f"Aliases migrated: {summary['aliases_migrated']}",
                f"Unsafe aliases skipped: {summary['aliases_skipped_unsafe']}",
                (
                    "Missing local exports skipped: "
                    f"{summary['aliases_skipped_missing_export']}"
                ),
            ])
            + "\n",
        )
        if summary["files_failed"] > 0:
            return r[t.IntMapping].fail("Runtime alias import migration had errors")
        return r[t.IntMapping].ok(summary)

    @staticmethod
    def _handle_ultrawork_models(
        params: m.Infra.RefactorUltraworkModelsInput,
    ) -> r[t.IntMapping]:
        """Run centralization, MRO migration, and namespace enforcement together."""
        workspace = params.workspace_path
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

        combined: t.IntMapping = {
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
                cli_service.display_message(error, message_type="error")
            return r[t.IntMapping].fail("MRO migration had errors")
        return r[t.IntMapping].ok(combined)

    @staticmethod
    def _handle_refactor_census(
        params: m.Infra.RefactorCensusInput,
    ) -> r[m.Infra.UtilitiesCensusReport]:
        """Run method-usage census and optionally export JSON report."""
        census = FlextInfraRefactorCensus()
        target = u.Infra.build_mro_target(params.family)
        result = census.run(
            workspace_root=params.workspace_path,
            target=target,
        )
        if result.is_failure:
            return result
        report = result.value
        cli_service.display_text(FlextInfraRefactorCensus.render_text(report))
        if params.json_output:
            json_path = Path(params.json_output).resolve()
            u.Infra.export_pydantic_json(report, json_path)
            cli_service.display_message(
                f"JSON report exported to: {json_path}",
                message_type="info",
            )
        return result


__all__ = ["FlextInfraCliRefactor"]
