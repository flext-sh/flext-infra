"""CLI mixin for workspace commands."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r
from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
    u,
)

if TYPE_CHECKING:
    import typer

_R = u.Infra.route  # shorthand


class FlextInfraCliWorkspace:
    """Workspace CLI group — composed into FlextInfraCli via MRO."""

    def register_workspace(self, app: typer.Typer) -> None:
        """Register workspace commands on the given Typer app."""
        u.Infra.register_routes(
            app,
            [
                _R(
                    "detect",
                    "Detect workspace or standalone mode",
                    m.Infra.WorkspaceDetectInput,
                    self.handle_detect,
                    fail_msg="detection failed",
                ),
                _R(
                    "sync",
                    "Sync base.mk to project root",
                    m.Infra.WorkspaceSyncInput,
                    self.handle_sync,
                ),
                _R(
                    "orchestrate",
                    "Run make verb across projects",
                    m.Infra.WorkspaceOrchestrateInput,
                    self.handle_orchestrate,
                    fail_msg="orchestration failed",
                ),
                _R(
                    "migrate",
                    "Migrate workspace projects to flext_infra tooling",
                    m.Infra.WorkspaceMigrateInput,
                    self.handle_migrate,
                    fail_msg="migration failed",
                ),
            ],
        )

    @staticmethod
    def handle_detect(params: m.Infra.WorkspaceDetectInput) -> r[bool]:
        """Detect workspace or standalone mode."""
        return (
            FlextInfraWorkspaceDetector()
            .detect(u.Infra.resolve_workspace(params))
            .map(lambda _: True)
        )

    @staticmethod
    def handle_sync(params: m.Infra.WorkspaceSyncInput) -> r[bool]:
        """Sync base.mk to project root."""
        ws = u.Infra.resolve_workspace(params)
        canonical_path = Path(params.canonical_root) if params.canonical_root else None
        return (
            FlextInfraSyncService(canonical_root=canonical_path)
            .sync(workspace_root=ws, canonical_root=canonical_path)
            .map(lambda _: True)
        )

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
        return u.Infra.then_count(
            FlextInfraOrchestratorService().orchestrate(
                projects=filtered_projects,
                verb=params.verb,
                fail_fast=params.fail_fast,
                make_args=make_args,
            ),
            predicate=lambda item: item.exit_code != 0,
            fail_msg="orchestration completed with failures",
        )

    @staticmethod
    def handle_migrate(params: m.Infra.WorkspaceMigrateInput) -> r[bool]:
        """Migrate workspace projects to flext_infra tooling."""
        ws = u.Infra.resolve_workspace(params)
        dry_run = params.dry_run or not params.apply
        result = FlextInfraProjectMigrator().migrate(workspace_root=ws, dry_run=dry_run)
        if result.is_failure:
            return r[bool].fail(result.error or "migration failed")
        migrations: Sequence[m.Infra.MigrationResult] = result.value
        failed_projects = 0
        for migration in migrations:
            cli.display_message(f"{migration.project}:", c.Cli.MessageTypes.INFO)
            for change in migration.changes:
                cli.display_message(f"  + {change}", c.Cli.MessageTypes.INFO)
            for err in migration.errors:
                cli.display_message(f"  ! {err}", c.Cli.MessageTypes.WARNING)
            if migration.errors:
                failed_projects += 1
        total_changes = sum(len(migration.changes) for migration in migrations)
        total_errors = sum(len(migration.errors) for migration in migrations)
        cli.display_message(
            f"Total: {total_changes} change(s), {total_errors} error(s) across {len(migrations)} project(s)",
            c.Cli.MessageTypes.INFO,
        )
        if dry_run:
            cli.display_message(
                "(dry-run — no files modified)", c.Cli.MessageTypes.INFO
            )
        if failed_projects:
            return r[bool].fail(f"{failed_projects} project(s) had errors")
        return r[bool].ok(True)
