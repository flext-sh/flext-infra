"""CLI entry point for GitHub integration services."""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from flext_core import r

from flext_infra import c, m, output, t, u


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
    result: r[Sequence[m.Infra.SyncOperation]] = (
        u.Infra.github_sync_workspace_workflows(
            workspace_root=cli.workspace,
            apply=cli.apply,
            prune=prune,
            report_path=report,
        )
    )
    return u.Infra.exit_code(result, failure_msg="Workflow sync failed")


def run_lint(
    cli: u.Infra.CliArgs,
    *,
    report: Path | None,
    strict: bool,
) -> int:
    """Lint GitHub workflow files across workspace."""
    result: r[m.Infra.WorkflowLintResult] = u.Infra.github_lint_workflows(
        workspace_root=cli.workspace,
        report_path=report,
        strict=strict,
    )
    if result.is_failure:
        output.error(f"Workflow lint failed: {result.error}")
        return 1
    if result.value.status != "ok" and strict:
        output.error(f"Workflow lint found issues: {result.value.detail}")
        return 1
    return 0


def run_pr(argv: t.StrSequence) -> int:
    """Manage pull requests for a single project."""
    parser = u.Infra.create_parser(
        "flext-infra github pr",
        "Pull request lifecycle management",
    )
    _ = parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Repository root directory",
    )
    _ = parser.add_argument(
        "--action",
        choices=["status", "create", "view", "checks", "merge", "close"],
        default="status",
        help="PR action to perform",
    )
    _ = parser.add_argument("--base", default=c.Infra.Git.MAIN, help="Base branch")
    _ = parser.add_argument("--head", help="Head branch (default: current)")
    _ = parser.add_argument("--number", type=int, help="PR number")
    _ = parser.add_argument("--title", help="PR title (for create)")
    _ = parser.add_argument("--body", help="PR body (for create)")
    _ = parser.add_argument(
        "--draft",
        type=int,
        default=0,
        choices=[0, 1],
        help="Create as draft",
    )
    _ = parser.add_argument(
        "--merge-method",
        choices=["merge", "squash", "rebase"],
        default="squash",
        help="Merge method",
    )
    _ = parser.add_argument(
        "--auto",
        type=int,
        default=0,
        choices=[0, 1],
        help="Auto-merge",
    )
    _ = parser.add_argument(
        "--delete-branch",
        type=int,
        default=1,
        choices=[0, 1],
        help="Delete head branch on merge",
    )
    _ = parser.add_argument(
        "--checks-strict",
        type=int,
        default=1,
        choices=[0, 1],
        help="Fail if checks fail",
    )
    _ = parser.add_argument(
        "--release-on-merge",
        type=int,
        default=1,
        choices=[0, 1],
        help="Run release workflow on merge",
    )
    args = parser.parse_args(argv)

    pr_args = {
        "action": args.action,
        "base": args.base,
        "head": args.head,
        "number": str(args.number) if args.number else "",
        "title": args.title,
        "body": args.body,
        "draft": str(args.draft),
        "merge_method": args.merge_method,
        "auto": str(args.auto),
        "delete_branch": str(args.delete_branch),
        "checks_strict": str(args.checks_strict),
        "release_on_merge": str(args.release_on_merge),
    }

    result = u.Infra.github_pr_run_single(
        repo_root=args.repo_root,
        workspace_root=args.repo_root,
        pr_args=pr_args,
    )

    if result.is_failure:
        output.error(result.error or "status failed")
        return 1

    if result.value.exit_code != 0:
        return result.value.exit_code
    return 0


def run_pr_workspace(
    cli: u.Infra.CliArgs,
    pr_args: m.Infra.PrWorkspaceArgs,
) -> int:
    """Manage PRs across workspace."""
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
    result = u.Infra.github_pr_orchestrate(
        workspace_root=cli.workspace,
        projects=cli.projects if isinstance(cli.projects, list) else [],
        include_root=pr_args.include_root,
        branch=pr_args.branch,
        checkpoint=pr_args.checkpoint,
        fail_fast=pr_args.fail_fast,
        pr_args=pr_dict,
    )
    return u.Infra.exit_code(result, failure_msg="PR workspace orchestration failed")


def run(argv: t.StrSequence | None = None) -> int:
    """Run GitHub command dispatcher."""
    parser, subs = u.Infra.create_subcommand_parser(
        "flext-infra github",
        "GitHub integration services",
        subcommands={
            "workflows": "Sync GitHub workflow files across workspace",
            c.Infra.LINT_SECTION: "Lint GitHub workflow files",
            c.Cli.GhCmd.PR: "Manage pull requests for a single project",
            "pr-workspace": "Manage pull requests across workspace projects",
        },
        include_apply=True,
        include_project=True,
    )
    configure_workflows_parser(subs["workflows"])
    configure_lint_parser(subs[c.Infra.LINT_SECTION])
    configure_pr_workspace_parser(subs["pr-workspace"])

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    cli = u.Infra.resolve(args)
    if args.command == "workflows":
        return run_workflows(cli, prune=args.prune, report=args.report)
    if args.command == c.Infra.LINT_SECTION:
        return run_lint(cli, report=args.report, strict=args.strict)
    if args.command == c.Cli.GhCmd.PR:
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
            pr_number=str(args.pr_number) if args.pr_number else "",
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
