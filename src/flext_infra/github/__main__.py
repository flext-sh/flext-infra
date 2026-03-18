"""CLI entry point for GitHub integration services."""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

from flext_core import r

from flext_infra import c, m, u
from flext_infra.github.linter import FlextInfraWorkflowLinter
from flext_infra.github.pr import main as pr_main
from flext_infra.github.pr_workspace import FlextInfraPrWorkspaceManager
from flext_infra.github.workflows import FlextInfraWorkflowSyncer, SyncOperation


class FlextInfraGithubCommand:
    @staticmethod
    def run(argv: list[str] | None = None) -> int:
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
        FlextInfraGithubCommand.configure_workflows_parser(subs["workflows"])
        FlextInfraGithubCommand.configure_lint_parser(subs[c.Infra.Toml.LINT_SECTION])
        FlextInfraGithubCommand.configure_pr_workspace_parser(subs["pr-workspace"])

        args = parser.parse_args(argv)
        if not args.command:
            parser.print_help()
            return 1
        cli = u.Infra.resolve(args)
        if args.command == "workflows":
            return FlextInfraGithubCommand.run_workflows(
                cli,
                prune=args.prune,
                report=args.report,
            )
        if args.command == c.Infra.Toml.LINT_SECTION:
            return FlextInfraGithubCommand.run_lint(
                cli,
                report=args.report,
                strict=args.strict,
            )
        if args.command == c.Infra.Cli.GhCmd.PR:
            return FlextInfraGithubCommand.run_pr(
                argv[2:] if argv is not None else sys.argv[2:],
            )
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
            return FlextInfraGithubCommand.run_pr_workspace(cli, pr_args)
        parser.print_help()
        return 1

    @staticmethod
    def run_workflows(
        cli: u.Infra.CliArgs,
        *,
        prune: bool,
        report: Path | None,
    ) -> int:
        syncer = FlextInfraWorkflowSyncer()
        result: r[list[SyncOperation]] = syncer.sync_workspace(
            workspace_root=cli.workspace,
            apply=cli.apply,
            prune=prune,
            report_path=report,
        )
        return u.Infra.exit_code(result, failure_msg="workflow sync failed")

    @staticmethod
    def run_lint(
        cli: u.Infra.CliArgs,
        *,
        report: Path | None,
        strict: bool,
    ) -> int:
        linter = FlextInfraWorkflowLinter()
        lint_result: r[m.Infra.WorkflowLintResult] = linter.lint(
            root=cli.workspace,
            report_path=report,
            strict=strict,
        )
        return u.Infra.exit_code(lint_result, failure_msg="lint failed")

    @staticmethod
    def run_pr(argv: list[str]) -> int:
        sys.argv = ["flext-infra github pr", *argv]
        return pr_main()

    @staticmethod
    def run_pr_workspace(
        cli: u.Infra.CliArgs,
        pr_args: m.Infra.PrWorkspaceArgs,
    ) -> int:
        pr_mapping: dict[str, str] = {
            c.Infra.ReportKeys.ACTION: pr_args.pr_action,
            "base": pr_args.pr_base,
            "head": pr_args.pr_head,
            "number": pr_args.pr_number,
            "title": pr_args.pr_title,
            "body": pr_args.pr_body,
            "draft": str(int(pr_args.pr_draft)),
            "merge_method": pr_args.pr_merge_method,
            "auto": str(int(pr_args.pr_auto)),
            "delete_branch": str(int(pr_args.pr_delete_branch)),
            "checks_strict": str(int(pr_args.pr_checks_strict)),
            "release_on_merge": str(int(pr_args.pr_release_on_merge)),
        }
        manager = FlextInfraPrWorkspaceManager()
        orch_result = manager.orchestrate(
            workspace_root=cli.workspace,
            projects=cli.project_names(),
            include_root=pr_args.include_root,
            branch=pr_args.branch,
            checkpoint=pr_args.checkpoint,
            fail_fast=pr_args.fail_fast,
            pr_args=pr_mapping,
        )
        if orch_result.is_failure:
            return u.Infra.exit_code(orch_result, failure_msg="pr-workspace failed")
        data = orch_result.value
        return 1 if data.fail else 0

    @staticmethod
    def configure_workflows_parser(parser: ArgumentParser) -> None:
        _ = parser.add_argument("--prune", action="store_true", default=False)
        _ = parser.add_argument("--report", type=Path, default=None)

    @staticmethod
    def configure_lint_parser(parser: ArgumentParser) -> None:
        _ = parser.add_argument("--report", type=Path, default=None)
        _ = parser.add_argument("--strict", action="store_true", default=False)

    @staticmethod
    def configure_pr_workspace_parser(parser: ArgumentParser) -> None:
        _ = parser.add_argument("--include-root", type=int, default=1)
        _ = parser.add_argument("--branch", default="")
        _ = parser.add_argument("--checkpoint", type=int, default=1)
        _ = parser.add_argument("--fail-fast", type=int, default=0)
        _ = parser.add_argument("--pr-action", default=c.Infra.ReportKeys.STATUS)
        _ = parser.add_argument("--pr-base", default=c.Infra.Git.MAIN)
        _ = parser.add_argument("--pr-head", default="")
        _ = parser.add_argument("--pr-number", default="")
        _ = parser.add_argument("--pr-title", default="")
        _ = parser.add_argument("--pr-body", default="")
        _ = parser.add_argument("--pr-draft", type=int, default=0)
        _ = parser.add_argument("--pr-merge-method", default=c.Infra.Cli.GhCmd.SQUASH)
        _ = parser.add_argument("--pr-auto", type=int, default=0)
        _ = parser.add_argument("--pr-delete-branch", type=int, default=0)
        _ = parser.add_argument("--pr-checks-strict", type=int, default=0)
        _ = parser.add_argument("--pr-release-on-merge", type=int, default=1)


def main() -> int:
    """CLI entry point wrapped with centralized helpers."""
    return u.Infra.run_cli(FlextInfraGithubCommand.run)


if __name__ == "__main__":
    sys.exit(main())
