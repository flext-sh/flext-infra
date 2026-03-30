"""CLI mixin for workspace commands."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import FlextCliOutput, cli
from flext_core import r

from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
)

if TYPE_CHECKING:
    import typer


class FlextInfraCliWorkspace:
    """Workspace CLI group — composed into FlextInfraCli via MRO."""

    def register_workspace(self, app: typer.Typer) -> None:
        """Register workspace commands on the given Typer app."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="detect",
                help_text="Detect workspace or standalone mode",
                model_cls=m.Infra.WorkspaceDetectInput,
                handler=self.handle_detect,
                failure_message="detection failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="sync",
                help_text="Sync base.mk to project root",
                model_cls=m.Infra.WorkspaceSyncInput,
                handler=self.handle_sync,
                failure_message="sync failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="orchestrate",
                help_text="Run make verb across projects",
                model_cls=m.Infra.WorkspaceOrchestrateInput,
                handler=self.handle_orchestrate,
                failure_message="orchestration failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="migrate",
                help_text="Migrate workspace projects to flext_infra tooling",
                model_cls=m.Infra.WorkspaceMigrateInput,
                handler=self.handle_migrate,
                failure_message="migration failed",
            ),
        )

    @staticmethod
    def handle_detect(params: m.Infra.WorkspaceDetectInput) -> r[bool]:
        """Detect workspace or standalone mode."""
        ws = Path(params.workspace)
        detector = FlextInfraWorkspaceDetector()
        result = detector.detect(ws)
        if result.is_failure:
            return r[bool].fail(result.error or "detection failed")
        return r[bool].ok(True)

    @staticmethod
    def handle_sync(params: m.Infra.WorkspaceSyncInput) -> r[bool]:
        """Sync base.mk to project root."""
        ws = Path(params.workspace)
        canonical_path = Path(params.canonical_root) if params.canonical_root else None
        service = FlextInfraSyncService(canonical_root=canonical_path)
        result = service.sync(workspace_root=ws, canonical_root=canonical_path)
        if result.is_failure:
            return r[bool].fail(result.error or "sync failed")
        return r[bool].ok(True)

    @staticmethod
    def handle_orchestrate(params: m.Infra.WorkspaceOrchestrateInput) -> r[bool]:
        """Run make verb across projects."""
        allowed_verbs = c.Infra.Make.ORCHESTRATED_PROJECT_VERBS
        if params.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            return r[bool].fail(
                f"unsupported orchestrate verb '{params.verb}' (allowed: {allowed})",
            )
        raw_projects = params.projects.replace(",", " ")
        filtered_projects = [p.strip() for p in raw_projects.split() if p.strip()]
        if not filtered_projects:
            return r[bool].fail("no projects specified")
        make_args = [
            make_arg.strip() for make_arg in params.make_arg if make_arg.strip()
        ]
        service = FlextInfraOrchestratorService()
        result = service.orchestrate(
            projects=filtered_projects,
            verb=params.verb,
            fail_fast=params.fail_fast,
            make_args=make_args,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "orchestration failed")
        outputs: Sequence[m.Infra.CommandOutput] = result.value
        failures = [item for item in outputs if item.exit_code != 0]
        if failures:
            return r[bool].fail("orchestration completed with failures")
        return r[bool].ok(True)

    @staticmethod
    def handle_migrate(params: m.Infra.WorkspaceMigrateInput) -> r[bool]:
        """Migrate workspace projects to flext_infra tooling."""
        ws = Path(params.workspace)
        dry_run = params.dry_run or not params.apply
        service = FlextInfraProjectMigrator()
        result = service.migrate(workspace_root=ws, dry_run=dry_run)
        if result.is_failure:
            return r[bool].fail(result.error or "migration failed")
        migrations: Sequence[m.Infra.MigrationResult] = result.value
        failed_projects = 0
        for migration in migrations:
            FlextCliOutput.display_message(
                f"{migration.project}:", c.Cli.MessageTypes.INFO
            )
            for change in migration.changes:
                FlextCliOutput.display_message(f"  + {change}", c.Cli.MessageTypes.INFO)
            for err in migration.errors:
                FlextCliOutput.display_message(f"  ! {err}", c.Cli.MessageTypes.WARNING)
            if migration.errors:
                failed_projects += 1
        total_changes = sum(len(migration.changes) for migration in migrations)
        total_errors = sum(len(migration.errors) for migration in migrations)
        FlextCliOutput.display_message(
            f"Total: {total_changes} change(s), {total_errors} error(s) across {len(migrations)} project(s)",
            c.Cli.MessageTypes.INFO,
        )
        if dry_run:
            FlextCliOutput.display_message(
                "(dry-run — no files modified)", c.Cli.MessageTypes.INFO
            )
        if failed_projects:
            return r[bool].fail(f"{failed_projects} project(s) had errors")
        return r[bool].ok(True)
