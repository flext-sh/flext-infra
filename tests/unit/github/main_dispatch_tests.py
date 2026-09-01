"""Workspace github PR service tests using real repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, u as infra_u
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def test_run_github_workspace_pull_requests_stops_on_first_failure(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = infra_u.Infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace),
            action=c.Infra.PullRequestAction.STATUS,
        )
    )

    tm.ok(result)
    report = result.unwrap()
    tm.that(report.total, eq=1)
    tm.that(report.success, eq=0)
    tm.that(report.fail, eq=1)


def test_run_github_workspace_pull_requests_respects_project_selection(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path, project_names=("flext-a", "flext-b", "flext-c")
    )

    result = infra_u.Infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace), projects=["flext-a", "flext-b"]
        )
    )

    tm.ok(result)
    report = result.unwrap()
    report_dir = workspace / ".reports/workspace/pr"
    tm.that(report.total, eq=1)
    tm.that(report.fail, eq=1)
    tm.that((report_dir / "flext-a.log").exists(), eq=False)
    tm.that((report_dir / "flext-b.log").exists(), eq=False)
    tm.that((report_dir / "flext-c.log").exists(), eq=False)


def test_run_github_workspace_pull_requests_honors_fail_fast(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    request = m.Infra.GithubPullRequestWorkspaceRequest(
        workspace=str(workspace), fail_fast=True
    )
    tm.that(request.fail_fast, eq=True)
    result = infra_u.Infra.run_github_workspace_pull_requests(request)

    tm.ok(result)
    report = result.unwrap()
    report_dir = workspace / ".reports/workspace/pr"
    tm.that(report.total, eq=1)
    tm.that(report.success, eq=0)
    tm.that(report.fail, eq=1)
    tm.that((report_dir / "flext-a.log").exists(), eq=False)
    tm.that((report_dir / "flext-b.log").exists(), eq=False)
