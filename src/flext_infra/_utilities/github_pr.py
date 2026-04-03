"""GitHub PR orchestration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import MutableSequence
from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
    c,
    m,
    t,
)


class FlextInfraUtilitiesGithubPr(
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
    FlextInfraUtilitiesSubprocess,
):
    """Mixin for GitHub PR orchestration and execution."""

    @classmethod
    def github_pr_orchestrate(
        cls,
        workspace_root: Path,
        params: m.Infra.PrOrchestrateParams,
    ) -> r[m.Infra.PrOrchestrationResult]:
        """Run PR operations across workspace repositories."""
        projects_result = cls.resolve_projects(
            workspace_root,
            list(params.projects or []),
        )
        if projects_result.is_failure:
            return r[m.Infra.PrOrchestrationResult].fail(
                projects_result.error or "project resolution failed",
            )
        repos = [p.path for p in projects_result.value]
        if params.include_root:
            repos.append(workspace_root)
        effective_args = params.pr_args or {
            c.Infra.ReportKeys.ACTION: c.Infra.ReportKeys.STATUS,
            "base": c.Infra.Git.MAIN,
        }
        failures = 0
        results: MutableSequence[m.Infra.PrExecutionResultModel] = []
        pr_ctx = m.Infra.GithubPrRepoContext(
            workspace_root=workspace_root,
            effective_args=effective_args,
            branch=params.branch,
            checkpoint=params.checkpoint,
            results=results,
        )
        for repo_root in repos:
            failed = cls._github_pr_process_repo(repo_root, pr_ctx)
            if failed:
                failures += 1
                if params.fail_fast:
                    break
        total = len(repos)
        orchestration_results: t.Infra.VariadicTuple[m.Infra.PrExecutionResultModel] = (
            tuple(
                results,
            )
        )
        return r[m.Infra.PrOrchestrationResult].ok(
            m.Infra.PrOrchestrationResult(
                total=total,
                success=total - failures,
                fail=failures,
                results=orchestration_results,
            ),
        )

    @classmethod
    def _github_pr_process_repo(
        cls,
        repo_root: Path,
        ctx: m.Infra.GithubPrRepoContext,
    ) -> bool:
        """Process a single repo in PR orchestration. Returns True on failure."""
        if ctx.branch:
            cls.git_checkout(repo_root, ctx.branch)
        if ctx.checkpoint:
            cls._github_pr_checkpoint(repo_root, ctx.branch)
        run_result: r[m.Infra.PrExecutionResultModel] = cls.github_pr_run_single(
            repo_root,
            ctx.workspace_root,
            ctx.effective_args,
        )
        if run_result.is_success:
            pr_data = run_result.value
            ctx.results.append(pr_data)
            return pr_data.exit_code != 0
        return True

    @classmethod
    def _github_pr_checkpoint(cls, repo_root: Path, branch: str) -> r[bool]:
        changes_result = cls.git_has_changes(repo_root)
        if changes_result.is_failure:
            return r[bool].fail(changes_result.error or "changes check failed")
        if not changes_result.value:
            return r[bool].ok(True)
        add_result = cls.git_add(repo_root)
        if add_result.is_failure:
            return r[bool].fail(add_result.error or "git add failed")
        staged_result = cls.git_diff_names(repo_root, cached=True)
        if staged_result.is_success and (not staged_result.value.strip()):
            return r[bool].ok(True)
        commit_result = cls.git_commit(
            repo_root,
            "chore: checkpoint pending changes",
        )
        if commit_result.is_failure:
            return r[bool].fail(commit_result.error or "git commit failed")
        return cls.git_push(
            repo_root,
            remote=c.Infra.Git.ORIGIN if branch else "",
            branch=branch,
            upstream=bool(branch),
        )

    @classmethod
    def github_pr_run_single(
        cls,
        repo_root: Path,
        workspace_root: Path,
        pr_args: t.StrMapping,
    ) -> r[m.Infra.PrExecutionResultModel]:
        """Execute one PR command for a single repository."""
        display = workspace_root.name if repo_root == workspace_root else repo_root.name
        report_dir = cls.get_report_dir(
            workspace_root,
            c.Infra.ReportKeys.WORKSPACE,
            c.Infra.PR,
        )
        with contextlib.suppress(OSError):
            report_dir.mkdir(parents=True, exist_ok=True)
        log_path = report_dir / f"{display}.log"
        command = cls._github_build_pr_command(
            repo_root=repo_root,
            workspace_root=workspace_root,
            pr_args=pr_args,
        )
        started = time.monotonic()
        to_file_result: r[int] = cls.run_to_file(command, log_path)
        if to_file_result.is_failure:
            return r[m.Infra.PrExecutionResultModel].fail(
                to_file_result.error or "command execution error",
            )
        exit_code = to_file_result.value
        elapsed = int(time.monotonic() - started)
        status = c.Infra.Status.OK if exit_code == 0 else c.Infra.Status.FAIL
        return r[m.Infra.PrExecutionResultModel].ok(
            m.Infra.PrExecutionResultModel(
                display=display,
                status=status,
                elapsed=elapsed,
                exit_code=exit_code,
                log_path=str(log_path),
            ),
        )

    @staticmethod
    def _github_build_pr_command(
        *,
        repo_root: Path,
        workspace_root: Path,
        pr_args: t.StrMapping,
    ) -> list[str]:
        """Build the CLI command list for a single PR operation."""
        is_root = repo_root == workspace_root
        if is_root:
            command = [
                c.Infra.PYTHON,
                "-m",
                "flext_infra.github.pr",
                "--repo-root",
                str(repo_root),
                "--action",
                pr_args.get(c.Infra.ReportKeys.ACTION, c.Infra.ReportKeys.STATUS),
                "--base",
                pr_args.get("base", c.Infra.Git.MAIN),
                "--draft",
                pr_args.get("draft", "0"),
                "--merge-method",
                pr_args.get("merge_method", c.Infra.SQUASH),
                "--auto",
                pr_args.get("auto", "0"),
                "--delete-branch",
                pr_args.get("delete_branch", "0"),
                "--checks-strict",
                pr_args.get("checks_strict", "0"),
                "--release-on-merge",
                pr_args.get("release_on_merge", "1"),
            ]
        else:
            command = [
                c.Infra.MAKE,
                "-C",
                str(repo_root),
                c.Infra.PR,
                f"PR_ACTION={pr_args.get('action', 'status')}",
                f"PR_BASE={pr_args.get('base', 'main')}",
                f"PR_DRAFT={pr_args.get('draft', '0')}",
                f"PR_MERGE_METHOD={pr_args.get('merge_method', 'squash')}",
                f"PR_AUTO={pr_args.get('auto', '0')}",
                f"PR_DELETE_BRANCH={pr_args.get('delete_branch', '0')}",
                f"PR_CHECKS_STRICT={pr_args.get('checks_strict', '0')}",
                f"PR_RELEASE_ON_MERGE={pr_args.get('release_on_merge', '1')}",
            ]
        for key, flag in (
            ("head", "PR_HEAD"),
            ("number", "PR_NUMBER"),
            ("title", "PR_TITLE"),
            ("body", "PR_BODY"),
        ):
            value = pr_args.get(key, "")
            if value:
                if is_root:
                    command.extend([f"--{key}", value])
                else:
                    command.append(f"{flag}={value}")
        return command


__all__ = [
    "FlextInfraUtilitiesGithubPr",
]
