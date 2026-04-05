"""Tests for github CLI handlers registered by the centralized dispatcher."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, t

from flext_core import r
from flext_infra import FlextInfraGithubService, u as infra_u


def _sync_report() -> m.Infra.GithubWorkflowSyncReport:
    return m.Infra.GithubWorkflowSyncReport(
        mode="dry-run",
        summary={},
        operations=(),
    )


def _lint_outcome() -> m.Infra.GithubWorkflowLintOutcome:
    return m.Infra.GithubWorkflowLintOutcome(status="ok")


def _pull_request_outcome(*, exit_code: int = 0) -> m.Infra.GithubPullRequestOutcome:
    return m.Infra.GithubPullRequestOutcome(
        display="test-repo",
        status="ok" if exit_code == 0 else "fail",
        elapsed=0,
        exit_code=exit_code,
    )


class TestRunWorkflows:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            _ = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(_sync_report())

        monkeypatch.setattr(infra_u.Infra, "github_sync_workflows", staticmethod(_sync))
        result = FlextInfraGithubService().execute_workflow_sync(
            m.Infra.GithubWorkflowSyncRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            _ = request
            return r[m.Infra.GithubWorkflowSyncReport].fail("sync failed")

        monkeypatch.setattr(infra_u.Infra, "github_sync_workflows", staticmethod(_sync))
        result = FlextInfraGithubService().execute_workflow_sync(
            m.Infra.GithubWorkflowSyncRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_apply_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, m.Infra.GithubWorkflowSyncRequest] = {}

        def _fake_sync(
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            captured["request"] = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(_sync_report())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_sync_workflows",
            staticmethod(_fake_sync),
        )
        FlextInfraGithubService().execute_workflow_sync(
            m.Infra.GithubWorkflowSyncRequest(workspace=str(tmp_path), apply=True),
        )
        assert captured["request"].apply is True

    def test_with_prune_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, m.Infra.GithubWorkflowSyncRequest] = {}

        def _fake_sync(
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            captured["request"] = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(_sync_report())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_sync_workflows",
            staticmethod(_fake_sync),
        )
        FlextInfraGithubService().execute_workflow_sync(
            m.Infra.GithubWorkflowSyncRequest(workspace=str(tmp_path), prune=True),
        )
        assert captured["request"].prune is True

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: MutableMapping[str, m.Infra.GithubWorkflowSyncRequest] = {}

        def _fake_sync(
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            captured["request"] = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(_sync_report())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_sync_workflows",
            staticmethod(_fake_sync),
        )
        report = tmp_path / "report.json"
        FlextInfraGithubService().execute_workflow_sync(
            m.Infra.GithubWorkflowSyncRequest(
                workspace=str(tmp_path),
                report=str(report),
            ),
        )
        assert captured["request"].report_path == report


class TestRunLint:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _lint(
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            _ = request
            return r[m.Infra.GithubWorkflowLintOutcome].ok(_lint_outcome())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_lint_workflows",
            staticmethod(_lint),
        )
        result = FlextInfraGithubService().execute_workflow_lint(
            m.Infra.GithubWorkflowLintRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _lint(
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            _ = request
            return r[m.Infra.GithubWorkflowLintOutcome].fail("lint failed")

        monkeypatch.setattr(
            infra_u.Infra,
            "github_lint_workflows",
            staticmethod(_lint),
        )
        result = FlextInfraGithubService().execute_workflow_lint(
            m.Infra.GithubWorkflowLintRequest(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: MutableMapping[str, m.Infra.GithubWorkflowLintRequest] = {}

        def _fake_lint(
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            captured["request"] = request
            return r[m.Infra.GithubWorkflowLintOutcome].ok(_lint_outcome())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        report = tmp_path / "report.json"
        FlextInfraGithubService().execute_workflow_lint(
            m.Infra.GithubWorkflowLintRequest(
                workspace=str(tmp_path), report=str(report)
            ),
        )
        assert captured["request"].report_path == report

    def test_with_strict_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: t.MutableBoolMapping = {}

        def _fake_lint(
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            captured["strict"] = request.strict
            return r[m.Infra.GithubWorkflowLintOutcome].ok(_lint_outcome())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        FlextInfraGithubService().execute_workflow_lint(
            m.Infra.GithubWorkflowLintRequest(workspace=str(tmp_path), strict=True),
        )
        assert captured["strict"] is True


class TestRunPr:
    def test_delegates_to_pr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _pr(**kw: object) -> r[m.Infra.GithubPullRequestOutcome]:
            _ = kw
            return r[m.Infra.GithubPullRequestOutcome].ok(_pull_request_outcome())

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_pull_request",
            staticmethod(_pr),
        )
        result = FlextInfraGithubService().execute_pull_request(
            m.Infra.GithubPullRequestRequest(repo_root="/tmp", action="status"),
        )
        tm.that(result.is_success, eq=True)

    def test_nonzero_exit_becomes_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _pr(**kw: object) -> r[m.Infra.GithubPullRequestOutcome]:
            _ = kw
            return r[m.Infra.GithubPullRequestOutcome].ok(
                _pull_request_outcome(exit_code=1),
            )

        monkeypatch.setattr(
            infra_u.Infra,
            "github_run_pull_request",
            staticmethod(_pr),
        )
        result = FlextInfraGithubService().execute_pull_request(
            m.Infra.GithubPullRequestRequest(repo_root="/tmp", action="status"),
        )
        tm.that(result.is_failure, eq=True)
