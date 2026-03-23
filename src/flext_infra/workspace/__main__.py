"""CLI entry point for workspace utilities.

Usage:
    python -m flext_infra workspace detect [--workspace PATH]
    python -m flext_infra workspace sync [--workspace PATH]
    python -m flext_infra workspace orchestrate --verb <verb> [--fail-fast] [projects...]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r

from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    output,
    u,
)

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraWorkspaceCommand:
    @staticmethod
    def run_detect(cli: u.Infra.CliArgs) -> int:
        """Detect workspace or standalone mode."""
        detector = FlextInfraWorkspaceDetector()
        result = detector.detect(cli.workspace)
        return u.Infra.exit_code(result, failure_msg="detection failed")

    @staticmethod
    def run_sync(cli: u.Infra.CliArgs, canonical_root: str | None) -> int:
        """Sync base.mk to project root."""
        canonical_path = Path(canonical_root) if canonical_root else None
        service = FlextInfraSyncService(canonical_root=canonical_path)
        result = service.sync(
            workspace_root=cli.workspace,
            canonical_root=canonical_path,
        )
        return u.Infra.exit_code(result, failure_msg="sync failed")

    @staticmethod
    def run_orchestrate(
        projects: list[str],
        verb: str,
        *,
        fail_fast: bool,
        make_args: list[str],
    ) -> int:
        """Run make verb across projects."""
        filtered_projects = [project for project in projects if project]
        if not filtered_projects:
            return u.Infra.exit_code(
                r[str].fail("no projects specified"),
                failure_msg="no projects specified",
            )
        service = FlextInfraOrchestratorService()
        result = service.orchestrate(
            projects=filtered_projects,
            verb=verb,
            fail_fast=fail_fast,
            make_args=make_args,
        )
        if result.is_success:
            outputs: list[m.Infra.CommandOutput] = result.value
            failures = [item for item in outputs if item.exit_code != 0]
            return max((item.exit_code for item in failures), default=0)
        return u.Infra.exit_code(result, failure_msg="orchestration failed")

    @staticmethod
    def run_migrate(cli: u.Infra.CliArgs) -> int:
        """Migrate workspace projects to flext_infra tooling."""
        service = FlextInfraProjectMigrator()
        result = service.migrate(workspace_root=cli.workspace, dry_run=cli.dry_run)
        if result.is_failure:
            return u.Infra.exit_code(result, failure_msg="migration failed")
        migrations: list[m.Infra.MigrationResult] = result.value
        failed_projects = 0
        for migration in migrations:
            output.info(f"{migration.project}:")
            for change in migration.changes:
                output.info(f"  + {change}")
            for err in migration.errors:
                output.warning(f"  ! {err}")
            if migration.errors:
                failed_projects += 1
        total_changes = sum(len(migration.changes) for migration in migrations)
        total_errors = sum(len(migration.errors) for migration in migrations)
        output.info(
            f"Total: {total_changes} change(s), {total_errors} error(s) across {len(migrations)} project(s)",
        )
        if cli.dry_run:
            output.info("(dry-run — no files modified)")
        return 1 if failed_projects else 0

    @staticmethod
    def run(argv: list[str] | None = None) -> int:
        """Dispatch workspace subcommands and return process exit code."""
        parser, subs = u.Infra.create_subcommand_parser(
            "flext_infra workspace",
            "Workspace management utilities",
            subcommands={
                "detect": "Detect workspace or standalone mode",
                "sync": "Sync base.mk to project root",
                "orchestrate": "Run make verb across projects",
                "migrate": "Migrate workspace projects to flext_infra tooling",
            },
            include_apply=True,
        )

        _ = subs["sync"].add_argument(
            "--canonical-root",
            type=str,
            default=None,
            help="Canonical workspace root",
        )

        _ = subs["orchestrate"].add_argument(
            "--verb",
            required=True,
            help="Make verb to execute",
        )
        _ = subs["orchestrate"].add_argument(
            "--fail-fast",
            action="store_true",
            help="Stop on first failure",
        )
        _ = subs["orchestrate"].add_argument(
            "--make-arg",
            action="append",
            default=[],
            help="Additional make arguments",
        )
        _ = subs["orchestrate"].add_argument(
            "projects",
            nargs="*",
            help="Project directories to orchestrate",
        )

        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)

        if args.command == "detect":
            return _run_detect(cli)
        if args.command == "sync":
            return _run_sync(
                cli,
                getattr(args, "canonical_root", None),
            )
        if args.command == "orchestrate":
            return _run_orchestrate(
                args.projects,
                args.verb,
                fail_fast=args.fail_fast,
                make_args=args.make_arg,
            )
        if args.command == "migrate":
            return _run_migrate(cli)
        parser.print_help()
        return 1


def _run_detect(cli: u.Infra.CliArgs) -> int:
    return FlextInfraWorkspaceCommand.run_detect(cli)


def _run_sync(cli: u.Infra.CliArgs, canonical_root: str | None) -> int:
    return FlextInfraWorkspaceCommand.run_sync(cli, canonical_root)


def _run_orchestrate(
    projects: list[str],
    verb: str,
    *,
    fail_fast: bool,
    make_args: list[str],
) -> int:
    return FlextInfraWorkspaceCommand.run_orchestrate(
        projects,
        verb,
        fail_fast=fail_fast,
        make_args=make_args,
    )


def _run_migrate(cli: u.Infra.CliArgs) -> int:
    return FlextInfraWorkspaceCommand.run_migrate(cli)


def _main_inner(argv: list[str] | None = None) -> int:
    return FlextInfraWorkspaceCommand.run(argv)


def main(argv: list[str] | None = None) -> int:
    """Run workspace utilities: detect mode, sync base.mk, orchestrate projects."""
    return u.Infra.run_cli(_main_inner, argv)


if __name__ == "__main__":
    sys.exit(u.Infra.run_cli(main))
