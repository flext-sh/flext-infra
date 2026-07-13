"""Workspace github PR service tests using real repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def test_run_github_workspace_pull_requests_aggregates_results(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        pr_exit_codes={"flext-a": "0", "flext-b": "1"},
    )

    result = u.Infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace), action="status", fail_fast=False
        )
    )

    tm.ok(result)
    report = result.unwrap()
    tm.that(report.total, eq=2)
    tm.that(report.success, eq=1)
    tm.that(report.fail, eq=1)


def test_run_github_workspace_pull_requests_respects_project_selection(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b", "flext-c"),
        pr_exit_codes={"flext-a": "0", "flext-b": "0", "flext-c": "1"},
    )

    result = u.Infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace), projects=["flext-a", "flext-b"], fail_fast=False
        )
    )

    tm.ok(result)
    report = result.unwrap()
    report_dir = workspace / ".reports/workspace/pr"
    tm.that(report.total, eq=2)
    tm.that(report.fail, eq=0)
    assert (report_dir / "flext-a.log").is_file()
    assert (report_dir / "flext-b.log").is_file()
    assert not (report_dir / "flext-c.log").exists()


def test_run_github_workspace_pull_requests_honors_fail_fast(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        pr_exit_codes={"flext-a": "1", "flext-b": "0"},
    )

    result = u.Infra.run_github_workspace_pull_requests(
        m.Infra.GithubPullRequestWorkspaceRequest(
            workspace=str(workspace), fail_fast=True
        )
    )

    tm.ok(result)
    report_dir = workspace / ".reports/workspace/pr"
    tm.that(result.unwrap().fail, eq=1)
    assert (report_dir / "flext-a.log").is_file()
    assert not (report_dir / "flext-b.log").exists()
