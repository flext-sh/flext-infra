"""GitHub single-repo pull-request execution — extracted concern."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraUtilitiesGithubPrSingleMixin:
    """Execute one pull-request command for a single repository.

    Composed into FlextInfraUtilitiesGithubPr via inheritance; the workspace
    orchestrator resolves ``_run_github_pull_request_for_repo`` through ``cls``
    MRO.
    """

    @classmethod
    def run_github_pull_request(
        cls,
        params: m.Infra.GithubPullRequestRequest,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Execute one pull-request command from the canonical single-repo payload."""
        result = cls._run_github_pull_request_for_repo(
            repo_root=params.repo_root_path,
            workspace_root=params.repo_root_path,
            request=params,
        )
        if result.success and result.value.exit_code != 0:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                f"PR operation exited with code {result.value.exit_code}",
            )
        return result

    @classmethod
    def _run_github_pull_request_for_repo(
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
        report_dir = (
            workspace_root
            / c.Infra.REPORTS_DIR_NAME
            / c.Infra.RK_WORKSPACE
            / c.Infra.PR
        ).resolve()
        ensure_dir_result = u.Cli.ensure_dir(report_dir)
        if ensure_dir_result.failure:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                ensure_dir_result.error or "failed to create report directory",
            )
        report_dir = ensure_dir_result.value
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
        status = (
            c.Infra.ResultStatus.OK if exit_code == 0 else c.Infra.ResultStatus.FAIL
        )
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


__all__: list[str] = ["FlextInfraUtilitiesGithubPrSingleMixin"]
