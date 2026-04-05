"""CLI entry points for workspace checker."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import flext_infra.check.workspace_check as workspace_check_module
from flext_infra import (
    c,
    m,
    r,
    t,
    u,
)
from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer


class FlextInfraWorkspaceCheckerCli:
    """CLI builder and entry points for workspace check commands."""

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build the workspace check CLI parser."""
        parser, subs = u.Infra.create_subcommand_parser(
            "flext-infra check",
            "FLEXT check utilities",
            subcommands={
                c.Infra.Verbs.RUN: "Run quality gates",
                "fix-pyrefly-config": "Repair [tool.pyrefly] blocks",
            },
            flags=u.Infra.SharedFlags(include_project=True),
            subcommand_flags={
                "fix-pyrefly-config": {
                    "include_apply": True,
                    "include_diff": False,
                },
            },
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--gates",
            default=c.Infra.DEFAULT_CSV,
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--reports-dir",
            default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/check",
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument("--fail-fast", action="store_true")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--fix", action="store_true")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--check-only", action="store_true")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--ruff-args")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--pyright-args")
        _ = subs["fix-pyrefly-config"].add_argument("--verbose", action="store_true")
        return parser

    @staticmethod
    def run_cli(argv: Sequence[str] | None = None) -> int:
        """Run the subcommand-based workspace check CLI."""
        parser = FlextInfraWorkspaceCheckerCli.build_parser()
        args = u.Infra.parse_subcommand_args(parser, argv)
        cli = u.Infra.resolve(args)
        if args.command == c.Infra.Verbs.RUN:
            env_workspace = os.getenv("FLEXT_WORKSPACE_ROOT")
            checker_workspace = (
                Path(env_workspace).resolve() if env_workspace else cli.workspace
            )
            project_names = cli.project_names()
            if not project_names:
                u.Infra.error("no projects specified")
                return 1
            if args.dry_run:
                u.Infra.info("dry-run: skipping gate execution")
                return 0
            checker = workspace_check_module.FlextInfraWorkspaceChecker(
                workspace_root=checker_workspace
            )
            gates = workspace_check_module.FlextInfraWorkspaceChecker.parse_gate_csv(
                args.gates
            )
            ruff_args = (
                workspace_check_module.FlextInfraWorkspaceChecker.parse_tool_args(
                    args.ruff_args
                )
            )
            pyright_args = (
                workspace_check_module.FlextInfraWorkspaceChecker.parse_tool_args(
                    args.pyright_args,
                )
            )
            reports_dir = Path(args.reports_dir).expanduser()
            if not reports_dir.is_absolute():
                reports_dir = (Path.cwd() / reports_dir).resolve()
            gate_ctx = m.Infra.GateContext(
                workspace=checker_workspace,
                reports_dir=reports_dir,
                apply_fixes=args.fix,
                check_only=args.check_only,
                ruff_args=tuple(ruff_args),
                pyright_args=tuple(pyright_args),
            )
            run_result = checker.run_projects(
                projects=project_names,
                gates=gates,
                reports_dir=reports_dir,
                fail_fast=args.fail_fast,
                ctx=gate_ctx,
            )
            if run_result.is_failure:
                u.Infra.error(run_result.error or "check failed")
                return 2
            run_results: Sequence[m.Infra.ProjectResult] = run_result.value
            failed_projects = [project for project in run_results if not project.passed]
            return 1 if failed_projects else 0
        if args.command == "fix-pyrefly-config":
            fixer: FlextInfraConfigFixer = FlextInfraConfigFixer()
            fix_result: r[t.StrSequence] = fixer.run(
                projects=cli.project_names() or [],
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
            if fix_result.is_failure:
                u.Infra.error(fix_result.error or "pyrefly config fix failed")
                return 1
            return 0
        parser.print_help()
        return 1

    @staticmethod
    def main(argv: Sequence[str] | None = None) -> int:
        """Run the legacy workspace check CLI entrypoint."""
        parser = u.Infra.create_parser(
            "flext-infra check-workspace",
            "FLEXT Workspace Check",
            flags=u.Infra.SharedFlags(include_project=True),
        )
        _ = parser.add_argument("--gates", default=c.Infra.DEFAULT_CSV)
        _ = parser.add_argument(
            "--reports-dir",
            default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/check",
        )
        _ = parser.add_argument("--fail-fast", action="store_true")
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        project_names = cli.project_names()
        if not project_names:
            u.Infra.error("no projects specified")
            return 1
        checker = workspace_check_module.FlextInfraWorkspaceChecker()
        gates = workspace_check_module.FlextInfraWorkspaceChecker.parse_gate_csv(
            args.gates
        )
        reports_dir = Path(args.reports_dir).expanduser()
        if not reports_dir.is_absolute():
            reports_dir = (Path.cwd() / reports_dir).resolve()
        result = checker.run_projects(
            projects=project_names,
            gates=gates,
            reports_dir=reports_dir,
            fail_fast=args.fail_fast,
        )
        if result.is_failure:
            u.Infra.error(result.error or "workspace check failed")
            return 2
        projects = result.value
        failed_projects = [project for project in projects if not project.passed]
        return 1 if failed_projects else 0


__all__ = ["FlextInfraWorkspaceCheckerCli"]
