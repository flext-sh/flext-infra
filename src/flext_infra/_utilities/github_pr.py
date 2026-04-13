"""GitHub PR orchestration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import MutableSequence
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesReporting,
    c,
    m,
    p,
    r,
)


class FlextInfraUtilitiesGithubPr:
    """Mixin for GitHub pull-request execution."""

    @classmethod
    def github_run_workspace_pull_requests(
        cls,
        request: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]:
        """Run pull-request commands across workspace repositories."""
        workspace_root = request.workspace_path
        projects_result = FlextInfraUtilitiesDocsScope.resolve_projects(
            workspace_root,
            list(request.project_names or []),
        )
        if projects_result.failure:
            return r[m.Infra.GithubPullRequestWorkspaceReport].fail(
                projects_result.error or "project resolution failed",
            )
        repos = [project.path for project in projects_result.value]
        if request.include_root:
            repos.append(workspace_root)
        outcomes: MutableSequence[m.Infra.GithubPullRequestOutcome] = []
        context = m.Infra.GithubPullRequestWorkspaceContext(
            workspace_root=workspace_root,
            request=request,
            outcomes=outcomes,
        )
        failures = 0
        for repo_root in repos:
            failed = cls._github_pr_process_repo(repo_root, context)
            if failed:
                failures += 1
                if request.fail_fast:
                    break
        total = len(repos)
        return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
            m.Infra.GithubPullRequestWorkspaceReport(
                total=total,
                success=total - failures,
                fail=failures,
                outcomes=tuple(outcomes),
            ),
        )

    @classmethod
    def _github_pr_process_repo(
        cls,
        repo_root: Path,
        context: m.Infra.GithubPullRequestWorkspaceContext,
    ) -> bool:
        """Process one repository during workspace pull-request execution."""
        if context.request.branch:
            _ = u.Cli.run_checked(
                [c.Infra.GIT, "checkout", context.request.branch],
                cwd=repo_root,
            )
        if context.request.checkpoint:
            cls._github_pr_checkpoint(repo_root, context.request.branch)
        run_result: p.Result[m.Infra.GithubPullRequestOutcome] = (
            cls.github_run_pull_request(
                repo_root=repo_root,
                workspace_root=context.workspace_root,
                request=context.request,
            )
        )
        if run_result.success:
            outcome = run_result.value
            context.outcomes.append(outcome)
            return outcome.exit_code != 0
        return True

    @classmethod
    def _github_pr_checkpoint(cls, repo_root: Path, branch: str) -> p.Result[bool]:
        changes_capture = u.Cli.capture(
            [c.Infra.GIT, "status", "--porcelain"],
            cwd=repo_root,
        )
        if changes_capture.failure:
            return r[bool].fail(changes_capture.error or "changes check failed")
        if not changes_capture.unwrap().strip():
            return r[bool].ok(True)
        add_result = u.Cli.run_checked([c.Infra.GIT, "add", "-A"], cwd=repo_root)
        if add_result.failure:
            return r[bool].fail(add_result.error or "git add failed")
        staged_result = u.Cli.capture(
            [c.Infra.GIT, "diff", "--cached", "--name-only"],
            cwd=repo_root,
        )
        if staged_result.success and (not staged_result.value.strip()):
            return r[bool].ok(True)
        commit_result = u.Cli.run_checked(
            [c.Infra.GIT, "commit", "-m", "chore: checkpoint pending changes"],
            cwd=repo_root,
        )
        if commit_result.failure:
            return r[bool].fail(commit_result.error or "git commit failed")
        command = [c.Infra.GIT, "push"]
        if branch:
            command.extend(["-u", c.Infra.GIT_ORIGIN, branch])
        return u.Cli.run_checked(
            command,
            cwd=repo_root,
        )

    @classmethod
    def github_run_pull_request(
        cls,
        *,
        repo_root: Path,
        workspace_root: Path,
        request: (
            m.Infra.GithubPullRequestRequest | m.Infra.GithubPullRequestWorkspaceRequest
        ),
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Execute one pull-request command for a single repository."""
        display = workspace_root.name if repo_root == workspace_root else repo_root.name
        report_dir = FlextInfraUtilitiesReporting.get_report_dir(
            workspace_root,
            c.Infra.RK_WORKSPACE,
            c.Infra.PR,
        )
        with contextlib.suppress(OSError):
            report_dir.mkdir(parents=True, exist_ok=True)
        log_path = report_dir / f"{display}.log"
        command = cls._github_build_pr_command(
            repo_root=repo_root,
            workspace_root=workspace_root,
            request=request,
        )
        started = time.monotonic()
        to_file_result = u.Cli.run_to_file(command, log_path)
        if to_file_result.failure:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                to_file_result.error or "command execution error",
            )
        exit_code = to_file_result.value
        elapsed = int(time.monotonic() - started)
        status = c.Infra.STATUS_OK if exit_code == 0 else c.Infra.STATUS_FAIL
        return r[m.Infra.GithubPullRequestOutcome].ok(
            m.Infra.GithubPullRequestOutcome(
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
        request: (
            m.Infra.GithubPullRequestRequest | m.Infra.GithubPullRequestWorkspaceRequest
        ),
    ) -> list[str]:
        """Build the CLI command list for a single pull-request operation."""
        is_root = repo_root == workspace_root
        if is_root:
            command = [
                c.Infra.PYTHON,
                "-m",
                "flext_infra.github.pr",
                "--repo-root",
                str(repo_root),
                "--action",
                request.action,
                "--base",
                request.base,
                "--draft",
                "1" if request.draft else "0",
                "--merge-method",
                request.merge_method,
                "--auto",
                "1" if request.auto else "0",
                "--delete-branch",
                "1" if request.delete_branch else "0",
                "--checks-strict",
                "1" if request.checks_strict else "0",
                "--release-on-merge",
                "1" if request.release_on_merge else "0",
            ]
        else:
            command = [
                c.Infra.MAKE,
                "-C",
                str(repo_root),
                c.Infra.PR,
                f"PR_ACTION={request.action}",
                f"PR_BASE={request.base}",
                f"PR_DRAFT={1 if request.draft else 0}",
                f"PR_MERGE_METHOD={request.merge_method}",
                f"PR_AUTO={1 if request.auto else 0}",
                f"PR_DELETE_BRANCH={1 if request.delete_branch else 0}",
                f"PR_CHECKS_STRICT={1 if request.checks_strict else 0}",
                f"PR_RELEASE_ON_MERGE={1 if request.release_on_merge else 0}",
            ]
        for key, flag, value in (
            ("head", "PR_HEAD", request.head or ""),
            (
                "number",
                "PR_NUMBER",
                "" if request.number is None else str(request.number),
            ),
            ("title", "PR_TITLE", request.title or ""),
            ("body", "PR_BODY", request.body or ""),
        ):
            if value:
                if is_root:
                    command.extend([f"--{key}", value])
                else:
                    command.append(f"{flag}={value}")
        return command


__all__: list[str] = ["FlextInfraUtilitiesGithubPr"]
