"""GitHub PR orchestration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra import c, m, p, r, t
from flext_infra._utilities._github_pr_single import (
    FlextInfraUtilitiesGithubPrSingleMixin,
)
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesGithubPr(FlextInfraUtilitiesGithubPrSingleMixin):
    """Mixin for GitHub pull-request execution."""

    @classmethod
    def run_github_workspace_pull_requests(
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
        outcomes: t.MutableSequenceOf[m.Infra.GithubPullRequestOutcome] = []
        context = m.Infra.GithubPullRequestWorkspaceContext(
            workspace_root=workspace_root,
            request=request,
            outcomes=outcomes,
        )
        failures = 0
        for repo_root in repos:
            outcome_result = cls._github_pr_process_repo(repo_root, context)
            failed = outcome_result.failure or outcome_result.unwrap().exit_code != 0
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
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Process one repository during workspace pull-request execution.

        ``r.ok(outcome)`` when the per-repo run produced an outcome (which
        the caller appends to ``context.outcomes``); the outcome's
        ``exit_code`` still has to be inspected to know if it succeeded.
        ``r.fail(reason)`` when the underlying ``_run_github_pull_request_for_repo``
        could not produce an outcome at all.
        """
        if context.request.branch:
            _ = u.Cli.run_checked(
                [c.Infra.GIT, "checkout", context.request.branch],
                cwd=repo_root,
            )
        if context.request.checkpoint:
            _ = cls._github_pr_checkpoint(repo_root, context.request.branch)
        run_result: p.Result[m.Infra.GithubPullRequestOutcome] = (
            cls._run_github_pull_request_for_repo(
                repo_root=repo_root,
                workspace_root=context.workspace_root,
                request=context.request,
            )
        )
        if run_result.failure:
            return run_result
        outcome = run_result.value
        context.outcomes.append(outcome)
        return r[m.Infra.GithubPullRequestOutcome].ok(outcome)

    @classmethod
    def _github_pr_checkpoint(cls, repo_root: Path, branch: str) -> p.Result[bool]:
        """Github pr checkpoint."""
        changes_capture = u.Cli.capture(
            [c.Infra.GIT, "status", "--porcelain"],
            cwd=repo_root,
        )
        result: p.Result[bool]
        if changes_capture.failure:
            result = r[bool].fail(changes_capture.error or "changes check failed")
        elif not changes_capture.unwrap().strip():
            result = r[bool].ok(True)
        else:
            add_result = u.Cli.run_checked([c.Infra.GIT, "add", "-A"], cwd=repo_root)
            if add_result.failure:
                result = r[bool].fail(add_result.error or "git add failed")
            else:
                staged_result = u.Cli.capture(
                    [c.Infra.GIT, "diff", "--cached", "--name-only"],
                    cwd=repo_root,
                )
                if staged_result.success and (not staged_result.value.strip()):
                    result = r[bool].ok(True)
                else:
                    commit_result = u.Cli.run_checked(
                        [
                            c.Infra.GIT,
                            "commit",
                            "-m",
                            "chore: checkpoint pending changes",
                        ],
                        cwd=repo_root,
                    )
                    if commit_result.failure:
                        result = r[bool].fail(
                            commit_result.error or "git commit failed"
                        )
                    else:
                        command = [c.Infra.GIT, "push"]
                        if branch:
                            command.extend(["-u", c.Infra.GIT_ORIGIN, branch])
                        result = u.Cli.run_checked(
                            command,
                            cwd=repo_root,
                        )
        return result


__all__: list[str] = ["FlextInfraUtilitiesGithubPr"]
