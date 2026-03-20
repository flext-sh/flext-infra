"""CLI entry point for GitHub integration services."""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c
from flext_infra.github.linter import FlextInfraWorkflowLinter
from flext_infra.github.pr import main as pr_main
from flext_infra.github.pr_workspace import FlextInfraPrWorkspaceManager
from flext_infra.github.workflows import FlextInfraWorkflowSyncer
from flext_infra.models import m
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra import SyncOperation


def configure_workflows_parser(parser: ArgumentParser) -> None:
    """Configure parser for the workflows command."""
    _ = parser.add_argument("--prune", action="store_true", help="Remove unknown files")
    _ = parser.add_argument("--report", type=Path, help="Output report file")


def configure_lint_parser(parser: ArgumentParser) -> None:
    """Configure parser for the lint command."""
    _ = parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on strict mode warnings",
    )
    _ = parser.add_argument("--report", type=Path, help="Output report file")


def configure_pr_workspace_parser(parser: ArgumentParser) -> None:
    """Configure parser for the pr-workspace command."""
    _ = parser.add_argument("--include-root", type=int, default=0, choices=[0, 1])
    _ = parser.add_argument("--branch", type=str, default="")
    _ = parser.add_argument("--checkpoint", type=int, default=1, choices=[0, 1])
    _ = parser.add_argument("--fail-fast", type=int, default=1, choices=[0, 1])
    _ = parser.add_argument(
        "--pr-action",
        type=str,
        default="status",
        choices=["status", "create", "merge", "close"],
    )
    _ = parser.add_argument("--pr-base", type=str, default="")
    _ = parser.add_argument("--pr-head", type=str, default="")
    _ = parser.add_argument("--pr-number", type=int, default=0)
    _ = parser.add_argument("--pr-title", type=str, default="")
    _ = parser.add_argument("--pr-body", type=str, default="")
    _ = parser.add_argument("--pr-draft", type=int, default=0, choices=[0, 1])
    _ = parser.add_argument(
        "--pr-merge-method",
        type=str,
        default="squash",
        choices=["merge", "squash", "rebase"],
    )
    _ = parser.add_argument("--pr-auto", type=int, default=0, choices=[0, 1])
    _ = parser.add_argument("--pr-delete-branch", type=int, default=1, choices=[0, 1])
    _ = parser.add_argument("--pr-checks-strict", type=int, default=1, choices=[0, 1])
    _ = parser.add_argument(
        "--pr-release-on-merge",
        type=int,
        default=0,
        choices=[0, 1],
    )


def run_workflows(
    cli: u.Infra.CliArgs,
    *,
    prune: bool,
    report: Path | None,
) -> int:
    """Sync GitHub workflow files."""
    syncer = FlextInfraWorkflowSyncer()
    result: r[list[SyncOperation]] = syncer.sync_workspace(
        workspace_root=cli.workspace,
        apply=cli.apply,
        prune=prune,
        report_path=report,
    )
    return u.Infra.exit_code(result, failure_msg="Workflow sync failed")


def run_lint(
    cli: u.Infra.CliArgs,
    *,
    report: Path | None,
    strict: bool,
) -> int:
    """Lint GitHub workflow files across workspace."""
    linter = FlextInfraWorkflowLinter()
    result: r[m.Infra.WorkflowLintResult] = linter.lint(
        root=cli.workspace,
        report_path=report,
        strict=strict,
    )
    return u.Infra.exit_code(result, failure_msg="Workflow lint failed")


def run_pr(argv: list[str]) -> int:
    """Delegate PR logic managing arguments."""
    original_argv = sys.argv.copy()
    sys.argv = [sys.argv[0], *argv]
    try:
        return pr_main()
    finally:
        sys.argv = original_argv


def run_pr_workspace(
    cli: u.Infra.CliArgs,
    pr_args: m.Infra.PrWorkspaceArgs,
) -> int:
    """Manage PRs across workspace."""
    manager = FlextInfraPrWorkspaceManager()
    pr_dict = {
        c.Infra.ReportKeys.ACTION: pr_args.pr_action,
        "base": pr_args.pr_base,
        "head": pr_args.pr_head,
        "number": str(pr_args.pr_number) if pr_args.pr_number else "",
        "title": pr_args.pr_title,
        "body": pr_args.pr_body,
        "draft": "1" if pr_args.pr_draft else "0",
        "merge_method": pr_args.pr_merge_method,
        "auto": "1" if pr_args.pr_auto else "0",
        "delete_branch": "1" if pr_args.pr_delete_branch else "0",
        "checks_strict": "1" if pr_args.pr_checks_strict else "0",
        "release_on_merge": "1" if pr_args.pr_release_on_merge else "0",
    }
    result = manager.orchestrate(
        workspace_root=cli.workspace,
        projects=[cli.projects] if cli.projects else [],
        include_root=pr_args.include_root,
        branch=pr_args.branch,
        checkpoint=pr_args.checkpoint,
        fail_fast=pr_args.fail_fast,
        pr_args=pr_dict,
    )
    return u.Infra.exit_code(result, failure_msg="PR workspace orchestration failed")


def run(argv: list[str] | None = None) -> int:
    """Run GitHub command dispatcher."""
    parser, subs = u.Infra.create_subcommand_parser(
        "flext-infra github",
        "GitHub integration services",
        subcommands={
            "workflows": "Sync GitHub workflow files across workspace",
            c.Infra.Toml.LINT_SECTION: "Lint GitHub workflow files",
            c.Infra.Cli.GhCmd.PR: "Manage pull requests for a single project",
            "pr-workspace": "Manage pull requests across workspace projects",
        },
        include_apply=True,
        include_project=True,
    )
    configure_workflows_parser(subs["workflows"])
    configure_lint_parser(subs[c.Infra.Toml.LINT_SECTION])
    configure_pr_workspace_parser(subs["pr-workspace"])

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    cli = u.Infra.resolve(args)
    if args.command == "workflows":
        return run_workflows(cli, prune=args.prune, report=args.report)
    if args.command == c.Infra.Toml.LINT_SECTION:
        return run_lint(cli, report=args.report, strict=args.strict)
    if args.command == c.Infra.Cli.GhCmd.PR:
        return run_pr(argv[2:] if argv is not None else sys.argv[2:])
    if args.command == "pr-workspace":
        pr_args = m.Infra.PrWorkspaceArgs(
            include_root=args.include_root == 1,
            branch=args.branch,
            checkpoint=args.checkpoint == 1,
            fail_fast=args.fail_fast == 1,
            pr_action=args.pr_action,
            pr_base=args.pr_base,
            pr_head=args.pr_head,
            pr_number=args.pr_number,
            pr_title=args.pr_title,
            pr_body=args.pr_body,
            pr_draft=args.pr_draft == 1,
            pr_merge_method=args.pr_merge_method,
            pr_auto=args.pr_auto == 1,
            pr_delete_branch=args.pr_delete_branch == 1,
            pr_checks_strict=args.pr_checks_strict == 1,
            pr_release_on_merge=args.pr_release_on_merge == 1,
        )
        return run_pr_workspace(cli, pr_args)
    parser.print_help()
    return 1


def main() -> int:
    """Entry point."""
    return u.Infra.run_cli(run)


if __name__ == "__main__":
    sys.exit(main())
