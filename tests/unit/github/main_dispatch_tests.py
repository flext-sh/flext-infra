"""Tests for github pr-workspace dispatch in the centralized CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m

from flext_core import r
from flext_infra import FlextInfraGithubService, u as infra_u


def _workspace_report(
    *,
    fail: int = 0,
    total: int = 1,
) -> m.Infra.GithubPullRequestWorkspaceReport:
    return m.Infra.GithubPullRequestWorkspaceReport(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        outcomes=(),
    )


class TestRunPrWorkspace:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _ok(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            _ = request
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_ok),
        )
        result = FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _fail(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            _ = request
            return r[m.Infra.GithubPullRequestWorkspaceReport].fail(
                "orchestration failed",
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fail),
        )
        result = FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_pr_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_requests: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

        def _fake_orchestrate(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            captured_requests.append(request)
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fake_orchestrate),
        )
        result = FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(tmp_path),
                action="merge",
                base="main",
                head="feature/test",
            ),
        )
        tm.that(result.is_success, eq=True)
        assert captured_requests[0].action == "merge"
        assert captured_requests[0].base == "main"
        assert captured_requests[0].head == "feature/test"

    def test_with_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_requests: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

        def _fake_orchestrate(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            captured_requests.append(request)
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(tmp_path),
                branch="feature/test",
            ),
        )
        assert captured_requests[0].branch == "feature/test"

    def test_with_checkpoint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_requests: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

        def _fake_orchestrate(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            captured_requests.append(request)
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(tmp_path),
                checkpoint=True,
            ),
        )
        assert captured_requests[0].checkpoint is True

    def test_with_fail_fast(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_requests: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

        def _fake_orchestrate(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            captured_requests.append(request)
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(tmp_path),
                fail_fast=True,
            ),
        )
        assert captured_requests[0].fail_fast is True

    def test_with_selected_projects(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_requests: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

        def _fake_orchestrate(
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            captured_requests.append(request)
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
                _workspace_report(fail=0),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_workspace_pull_requests",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubService().execute_workspace_pull_requests(
            m.Infra.GithubPullRequestWorkspaceRequest(
                workspace=str(tmp_path),
                projects=["flext-core", "flext-api"],
            ),
        )
        assert captured_requests[0].project_names == ["flext-core", "flext-api"]
