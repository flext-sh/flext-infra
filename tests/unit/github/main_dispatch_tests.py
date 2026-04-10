"""Workspace github PR service tests using real repositories."""

from __future__ import annotations

from pathlib import Path

from flext_infra import infra
from tests import m, u


def test_run_github_workspace_pull_requests_aggregates_results(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        pr_exit_codes={"flext-a": "0", "flext-b": "1"},
    )

    result = infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace),
            action="status",
            fail_fast=False,
        ),
    )

    assert result.is_success
    report = result.unwrap()
    assert report.total == 2
    assert report.success == 1
    assert report.fail == 1


def test_run_github_workspace_pull_requests_respects_project_selection(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b", "flext-c"),
        pr_exit_codes={"flext-a": "0", "flext-b": "0", "flext-c": "1"},
    )

    result = infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace),
            projects=["flext-a", "flext-b"],
            fail_fast=False,
        ),
    )

    assert result.is_success
    report = result.unwrap()
    report_dir = workspace / ".reports/workspace/pr"
    assert report.total == 2
    assert report.fail == 0
    assert (report_dir / "flext-a.log").is_file()
    assert (report_dir / "flext-b.log").is_file()
    assert not (report_dir / "flext-c.log").exists()


def test_run_github_workspace_pull_requests_honors_fail_fast(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        pr_exit_codes={"flext-a": "1", "flext-b": "0"},
    )

    result = infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace),
            fail_fast=True,
        ),
    )

    assert result.is_success
    report_dir = workspace / ".reports/workspace/pr"
    assert result.unwrap().fail == 1
    assert (report_dir / "flext-a.log").is_file()
    assert not (report_dir / "flext-b.log").exists()
