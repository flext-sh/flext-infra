"""GitHub single-repo pull-request execution — extracted concern."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r

from flext_infra import c, m, u
from flext_infra._utilities._github_pr_execution import (
    FlextInfraUtilitiesGithubPrExecutionMixin,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraUtilitiesGithubPrSingleMixin(FlextInfraUtilitiesGithubPrExecutionMixin):
    """Execute one pull-request command for a single repository.

    Composed into FlextInfraUtilitiesGithubPr via inheritance; the workspace
    orchestrator resolves ``_run_github_pull_request_for_repo`` through ``cls``
    MRO.
    """

    @classmethod
    def run_github_pull_request(
        cls, params: m.Infra.GithubPullRequestRequest
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Execute one pull-request command from the canonical single-repo payload."""
        result = cls._run_github_pull_request_for_repo(
            repo_root=params.repo_root_path,
            workspace_root=params.repo_root_path,
            request=params,
        )
        if result.success and result.value.exit_code != 0:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                f"PR operation exited with code {result.value.exit_code}"
            )
        return result

    @classmethod
    def _run_github_pull_request_for_repo(
        cls,
        *,
        repo_root: Path,
        workspace_root: Path,
        request: p.Infra.GithubPullRequestFields,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Execute one pull-request command for a single repository."""
        display = workspace_root.name if repo_root == workspace_root else repo_root.name
        common_dir = cls.git_common_dir(m.Infra.GitRepoRequest(repo_root=repo_root))
        if common_dir.failure:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                common_dir.error or "failed to resolve Git report owner"
            )
        report_dir = (
            common_dir.value.common_dir
            / "flext-reports"
            / c.Infra.RK_WORKSPACE
            / c.Infra.PR
        ).resolve()
        ensure_dir_result = u.Cli.ensure_dir(report_dir)
        if ensure_dir_result.failure:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                ensure_dir_result.error or "failed to create report directory"
            )
        report_dir = ensure_dir_result.value
        log_path = report_dir / f"{display}.log"
        return cls.execute_github_pull_request(
            request=request, repo_root=repo_root, display=display, log_path=log_path
        )


__all__: list[str] = ["FlextInfraUtilitiesGithubPrSingleMixin"]
