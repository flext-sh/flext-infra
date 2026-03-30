"""CLI entry point for refactoring and modernization tools."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from flext_cli import cli
from flext_core import FlextRuntime, r
from pydantic import BaseModel, Field

from flext_infra import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    m,
    t,
    u,
)

# ── Input Models ─────────────────────────────────────────────


class CentralizePydanticInput(BaseModel):
    """CLI input for pydantic centralization — fields become CLI options."""

    workspace: Annotated[str, Field(default=".", description="Workspace root")]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    normalize_remaining: Annotated[
        bool,
        Field(
            default=False,
            description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
        ),
    ]


class MigrateMroInput(BaseModel):
    """CLI input for MRO migration — fields become CLI options."""

    workspace: Annotated[str, Field(default=".", description="Workspace root")]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    target: Annotated[
        str,
        Field(
            default="all",
            description="Migration target scope (constants/typings/protocols/models/utilities/all)",
        ),
    ]


class NamespaceEnforceInput(BaseModel):
    """CLI input for namespace enforcement — fields become CLI options."""

    workspace: Annotated[str, Field(default=".", description="Workspace root")]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    diff: Annotated[
        bool, Field(default=False, description="Show diff without applying")
    ]
    project: Annotated[
        str | None,
        Field(
            default=None,
            description="Project to process (comma-separated for multiple)",
        ),
    ]


class UltraworkModelsInput(BaseModel):
    """CLI input for ultrawork-models — fields become CLI options."""

    workspace: Annotated[str, Field(default=".", description="Workspace root")]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    normalize_remaining: Annotated[
        bool,
        Field(
            default=False,
            description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
        ),
    ]


class CensusInput(BaseModel):
    """CLI input for MRO family census — fields become CLI options."""

    workspace: Annotated[str, Field(default=".", description="Workspace root")]
    family: Annotated[
        str,
        Field(
            default="u",
            description="MRO family to census (c/t/p/m/u)",
        ),
    ]
    json_output: Annotated[
        str | None,
        Field(default=None, description="Path to write JSON report"),
    ]


# ── Router ───────────────────────────────────────────────────


class FlextInfraRefactorCli:
    """Declarative CLI router for refactoring and modernization tools."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="refactor",
            help_text="Refactor and modernization tools for flext workspace",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="refactor", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="centralize-pydantic",
                help_text="Centralize BaseModel/TypedDict/dict-like aliases into _models.py",
                model_cls=CentralizePydanticInput,
                handler=self._handle_centralize_pydantic,
                failure_message="Pydantic centralization failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="migrate-mro",
                help_text="Migrate loose declarations into MRO facade classes",
                model_cls=MigrateMroInput,
                handler=self._handle_migrate_mro,
                failure_message="MRO migration failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="namespace-enforce",
                help_text="Scan workspace for namespace governance violations",
                model_cls=NamespaceEnforceInput,
                handler=self._handle_namespace_enforce,
                failure_message="Namespace enforcement failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="ultrawork-models",
                help_text="Run full centralization + MRO + namespace workflow",
                model_cls=UltraworkModelsInput,
                handler=self._handle_ultrawork_models,
                failure_message="Ultrawork models failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="census",
                help_text="Run AST/CST census of MRO family method usage",
                model_cls=CensusInput,
                handler=self._handle_census,
                failure_message="Census failed",
            ),
        )

    @staticmethod
    def _handle_centralize_pydantic(
        params: CentralizePydanticInput,
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
        params: MigrateMroInput,
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
        params: NamespaceEnforceInput,
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
        params: UltraworkModelsInput,
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
    def _handle_census(params: CensusInput) -> r[m.Infra.UtilitiesCensusReport]:
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


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run the refactor CLI entrypoint."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraRefactorCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
