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
    FlextInfraConstantsBase,
    FlextInfraGithubModels,
    FlextInfraModelsCliInputsOps,
    FlextInfraSharedInfraConstants,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
)


class FlextInfraUtilitiesGithubPr(
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesReporting,
    FlextInfraUtilitiesSelection,
):
    """Mixin for GitHub pull-request execution."""

    @classmethod
    def github_run_workspace_pull_requests(
        cls,
        request: FlextInfraModelsCliInputsOps.GithubPullRequestWorkspaceRequest,
    ) -> r[FlextInfraGithubModels.GithubPullRequestWorkspaceReport]:
        """Run pull-request commands across workspace repositories."""
        workspace_root = request.workspace_path
        projects_result = cls.resolve_projects(
            workspace_root,
            list(request.project_names or []),
        )
        if projects_result.is_failure:
            return r[FlextInfraGithubModels.GithubPullRequestWorkspaceReport].fail(
                projects_result.error or "project resolution failed",
            )
        repos = [project.path for project in projects_result.value]
        if request.include_root:
            repos.append(workspace_root)
        outcomes: MutableSequence[FlextInfraGithubModels.GithubPullRequestOutcome] = []
        context = FlextInfraGithubModels.GithubPullRequestWorkspaceContext(
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
        return r[FlextInfraGithubModels.GithubPullRequestWorkspaceReport].ok(
            FlextInfraGithubModels.GithubPullRequestWorkspaceReport(
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
        context: FlextInfraGithubModels.GithubPullRequestWorkspaceContext,
    ) -> bool:
        """Process one repository during workspace pull-request execution."""
        if context.request.branch:
            cls.git_checkout(repo_root, context.request.branch)
        if context.request.checkpoint:
            cls._github_pr_checkpoint(repo_root, context.request.branch)
        run_result: r[FlextInfraGithubModels.GithubPullRequestOutcome] = (
            cls.github_run_pull_request(
                repo_root=repo_root,
                workspace_root=context.workspace_root,
                request=context.request,
            )
        )
        if run_result.is_success:
            outcome = run_result.value
            context.outcomes.append(outcome)
            return outcome.exit_code != 0
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
            remote=FlextInfraSharedInfraConstants.Git.ORIGIN if branch else "",
            branch=branch,
            upstream=bool(branch),
        )

    @classmethod
    def github_run_pull_request(
        cls,
        *,
        repo_root: Path,
        workspace_root: Path,
        request: (
            FlextInfraModelsCliInputsOps.GithubPullRequestRequest
            | FlextInfraModelsCliInputsOps.GithubPullRequestWorkspaceRequest
        ),
    ) -> r[FlextInfraGithubModels.GithubPullRequestOutcome]:
        """Execute one pull-request command for a single repository."""
        display = workspace_root.name if repo_root == workspace_root else repo_root.name
        report_dir = cls.get_report_dir(
            workspace_root,
            FlextInfraConstantsBase.ReportKeys.WORKSPACE,
            FlextInfraConstantsBase.PR,
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
        to_file_result: r[int] = cls.run_to_file(command, log_path)
        if to_file_result.is_failure:
            return r[FlextInfraGithubModels.GithubPullRequestOutcome].fail(
                to_file_result.error or "command execution error",
            )
        exit_code = to_file_result.value
        elapsed = int(time.monotonic() - started)
        status = (
            FlextInfraConstantsBase.Status.OK
            if exit_code == 0
            else FlextInfraConstantsBase.Status.FAIL
        )
        return r[FlextInfraGithubModels.GithubPullRequestOutcome].ok(
            FlextInfraGithubModels.GithubPullRequestOutcome(
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
            FlextInfraModelsCliInputsOps.GithubPullRequestRequest
            | FlextInfraModelsCliInputsOps.GithubPullRequestWorkspaceRequest
        ),
    ) -> list[str]:
        """Build the CLI command list for a single pull-request operation."""
        is_root = repo_root == workspace_root
        if is_root:
            command = [
                FlextInfraConstantsBase.PYTHON,
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
                FlextInfraConstantsBase.MAKE,
                "-C",
                str(repo_root),
                FlextInfraConstantsBase.PR,
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


__all__ = ["FlextInfraUtilitiesGithubPr"]
