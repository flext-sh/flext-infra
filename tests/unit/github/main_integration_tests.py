"""Tests for centralized github CLI dispatch integration."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import pytest

from flext_infra import FlextInfra, infra, main
from tests import m, r


def _orch(
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


class TestMain:
    def test_help_flag(self) -> None:
        assert main(["github", "--help"]) == 0

    def test_no_args(self) -> None:
        assert main(["github"]) == 1

    def test_workflows_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _sync(
            _self: FlextInfra,
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            _ = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(
                m.Infra.GithubWorkflowSyncReport(
                    mode="dry-run",
                    summary={},
                    operations=(),
                ),
            )

        assert main(["github", "workflows", "--workspace", str(tmp_path)]) == 0

    def test_lint_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _lint(
            _self: FlextInfra,
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            _ = request
            return r[m.Infra.GithubWorkflowLintOutcome].ok(
                m.Infra.GithubWorkflowLintOutcome(status="ok"),
            )

        assert main(["github", "lint", "--workspace", str(tmp_path)]) == 0

    def test_pr_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _run_pr(
            _self: FlextInfra,
            _params: m.Infra.GithubPullRequestRequest,
        ) -> r[m.Infra.GithubPullRequestOutcome]:
            return r[m.Infra.GithubPullRequestOutcome].ok(
                m.Infra.GithubPullRequestOutcome(
                    display="repo",
                    status="ok",
                    elapsed=0,
                    exit_code=0,
                ),
            )

        assert (
            main(["github", "pr", "--repo-root", str(tmp_path), "--action", "status"])
            == 0
        )

    def test_pr_workspace_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _orchestrate(
            _self: FlextInfra,
            request: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
            _ = request
            return r[m.Infra.GithubPullRequestWorkspaceReport].ok(_orch(fail=0))

        monkeypatch.setattr(
            type(infra),
            "run_github_workspace_pull_requests",
            _orchestrate,
        )
        assert main(["github", "pr-workspace", "--workspace", str(tmp_path)]) == 0

    def test_unknown_subcommand(self) -> None:
        assert main(["github", "unknown"]) == 2

    def test_ensures_structlog_configured(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        called: MutableSequence[bool] = []

        def _lint(
            _self: FlextInfra,
            request: m.Infra.GithubWorkflowLintRequest,
        ) -> r[m.Infra.GithubWorkflowLintOutcome]:
            _ = request
            return r[m.Infra.GithubWorkflowLintOutcome].ok(
                m.Infra.GithubWorkflowLintOutcome(status="ok"),
            )

        result = main(["github", "lint", "--workspace", str(tmp_path)])
        called.append(result == 0)
        assert called

    def test_workflows_iterates_operations(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ops = [
            m.Infra.GithubWorkflowSyncOperation(
                project="p1",
                path="ci.yml",
                action="create",
                reason="new",
            ),
            m.Infra.GithubWorkflowSyncOperation(
                project="p2",
                path="ci.yml",
                action="update",
                reason="changed",
            ),
        ]

        def _sync(
            _self: FlextInfra,
            request: m.Infra.GithubWorkflowSyncRequest,
        ) -> r[m.Infra.GithubWorkflowSyncReport]:
            _ = request
            return r[m.Infra.GithubWorkflowSyncReport].ok(
                m.Infra.GithubWorkflowSyncReport.from_operations(
                    apply=False,
                    operations=list(ops),
                ),
            )

        assert main(["github", "workflows", "--workspace", str(tmp_path)]) == 0
