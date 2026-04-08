"""Public refactor service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence
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


class FlextInfraServiceRefactorMixin:
    """Expose refactor operations through the public infra facade."""

    @staticmethod
    def _runtime_alias_import_summary(
        results: Sequence[m.Infra.Result],
    ) -> t.MutableIntMapping:
        successful = [result for result in results if result.success]
        alias_changes = [
            change
            for result in successful
            for change in result.changes
            if "runtime alias import" in change
        ]
        return {
            "files_changed": sum(1 for result in successful if result.modified),
            "files_failed": len(results) - len(successful),
            "files_planned": sum(
                1
                for result in successful
                if (not result.modified)
                and any(
                    change.startswith("planned runtime alias import")
                    for change in result.changes
                )
            ),
            "aliases_migrated": sum(
                1 for change in alias_changes if change.startswith("migrated")
            ),
            "aliases_skipped_unsafe": sum(
                1 for change in alias_changes if "unsafe" in change
            ),
            "aliases_skipped_missing_export": sum(
                1 for change in alias_changes if "missing export" in change
            ),
        }

    def centralize_pydantic(
        self,
        params: m.Infra.RefactorCentralizeInput,
    ) -> r[t.IntMapping]:
        """Run pydantic centralization through the public facade."""
        return r[t.IntMapping].ok(
            u.Infra.centralize_workspace(
                params.workspace_path,
                apply=params.apply,
                normalize_remaining=params.normalize_remaining,
            )
        )

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
                cli_service.display_message(error, message_type="error")
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

    def migrate_runtime_alias_imports(
        self,
        params: m.Infra.RefactorMigrateRuntimeAliasImportsInput,
    ) -> r[t.IntMapping]:
        """Normalize canonical alias imports through the public facade."""
        aliases = [item.strip() for item in params.aliases.split(",") if item.strip()]
        results = u.Infra.migrate_runtime_alias_imports(
            workspace_root=params.workspace_path,
            aliases=aliases,
            apply=params.apply,
            project_names=params.project_names,
        )
        summary = self._runtime_alias_import_summary(results)
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
            + "\n"
        )
        if summary["files_failed"] > 0:
            return r[t.IntMapping].fail("Runtime alias import migration had errors")
        return r[t.IntMapping].ok(summary)

    def ultrawork_models(
        self,
        params: m.Infra.RefactorUltraworkModelsInput,
    ) -> r[t.IntMapping]:
        """Run the full centralization/MRO/namespace workflow."""
        centralize_summary = u.Infra.centralize_workspace(
            params.workspace_path,
            apply=params.apply,
            normalize_remaining=params.normalize_remaining,
        )
        mro_report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=params.workspace_path,
        ).run(target="all", apply=params.apply)
        namespace_report = FlextInfraNamespaceEnforcer(
            workspace_root=params.workspace_path,
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


__all__: Sequence[str] = ("FlextInfraServiceRefactorMixin",)
