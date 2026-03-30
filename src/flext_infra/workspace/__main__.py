"""CLI entry point for workspace utilities.

Usage:
    python -m flext_infra workspace detect [--workspace PATH]
    python -m flext_infra workspace sync [--workspace PATH] [--apply]
    python -m flext_infra workspace orchestrate --verb <verb> [--fail-fast] [--make-arg KEY=VALUE ...] [projects...]
    python -m flext_infra workspace migrate [--workspace PATH] [--apply]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from flext_cli import FlextCliOutput, cli
from flext_core import FlextRuntime, r

from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
    t,
)

# ── Handlers ─────────────────────────────────────────────────


def _handle_detect(params: m.Infra.WorkspaceDetectInput) -> r[bool]:
    ws = Path(params.workspace)
    detector = FlextInfraWorkspaceDetector()
    result = detector.detect(ws)
    if result.is_failure:
        return r[bool].fail(result.error or "detection failed")
    return r[bool].ok(True)


def _handle_sync(params: m.Infra.WorkspaceSyncInput) -> r[bool]:
    ws = Path(params.workspace)
    canonical_path = Path(params.canonical_root) if params.canonical_root else None
    service = FlextInfraSyncService(canonical_root=canonical_path)
    result = service.sync(workspace_root=ws, canonical_root=canonical_path)
    if result.is_failure:
        return r[bool].fail(result.error or "sync failed")
    return r[bool].ok(True)


def _handle_orchestrate(params: m.Infra.WorkspaceOrchestrateInput) -> r[bool]:
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
    make_args = [make_arg.strip() for make_arg in params.make_arg if make_arg.strip()]
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


def _handle_migrate(params: m.Infra.WorkspaceMigrateInput) -> r[bool]:
    ws = Path(params.workspace)
    dry_run = not params.apply
    service = FlextInfraProjectMigrator()
    result = service.migrate(workspace_root=ws, dry_run=dry_run)
    if result.is_failure:
        return r[bool].fail(result.error or "migration failed")
    migrations: Sequence[m.Infra.MigrationResult] = result.value
    failed_projects = 0
    for migration in migrations:
        FlextCliOutput.display_message(f"{migration.project}:", c.Cli.MessageTypes.INFO)
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


# ── Router ───────────────────────────────────────────────────


class FlextInfraWorkspaceCli:
    """Declarative CLI router for workspace management operations."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="workspace",
            help_text="Workspace management utilities",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="workspace", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="detect",
                help_text="Detect workspace or standalone mode",
                model_cls=m.Infra.WorkspaceDetectInput,
                handler=_handle_detect,
                failure_message="detection failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="sync",
                help_text="Sync base.mk to project root",
                model_cls=m.Infra.WorkspaceSyncInput,
                handler=_handle_sync,
                failure_message="sync failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="orchestrate",
                help_text="Run make verb across projects",
                model_cls=m.Infra.WorkspaceOrchestrateInput,
                handler=_handle_orchestrate,
                failure_message="orchestration failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="migrate",
                help_text="Migrate workspace projects to flext_infra tooling",
                model_cls=m.Infra.WorkspaceMigrateInput,
                handler=_handle_migrate,
                failure_message="migration failed",
            ),
        )


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run workspace utilities: detect mode, sync base.mk, orchestrate projects."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraWorkspaceCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
