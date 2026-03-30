"""Tests for github CLI handlers registered by the centralized dispatcher."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import FlextInfraCliGithub, m, u


class TestRunWorkflows:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_sync),
        )
        result = FlextInfraCliGithub._handle_workflows(
            m.Infra.GithubWorkflowsInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].fail("sync failed")

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_sync),
        )
        result = FlextInfraCliGithub._handle_workflows(
            m.Infra.GithubWorkflowsInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_apply_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, m.Infra.WorkflowSyncParams] = {}

        def _fake_sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            captured["params"] = params
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        FlextInfraCliGithub._handle_workflows(
            m.Infra.GithubWorkflowsInput(workspace=str(tmp_path), apply=True),
        )
        assert captured["params"].apply is True

    def test_with_prune_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, m.Infra.WorkflowSyncParams] = {}

        def _fake_sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            captured["params"] = params
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        FlextInfraCliGithub._handle_workflows(
            m.Infra.GithubWorkflowsInput(workspace=str(tmp_path), prune=True),
        )
        assert captured["params"].prune is True

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: MutableMapping[str, m.Infra.WorkflowSyncParams] = {}

        def _fake_sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            captured["params"] = params
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        report = tmp_path / "report.json"
        FlextInfraCliGithub._handle_workflows(
            m.Infra.GithubWorkflowsInput(
                workspace=str(tmp_path),
                report=str(report),
            ),
        )
        assert captured["params"].report_path == report


class TestRunLint:
    def _ok_lint(
        self,
    ) -> r[m.Infra.WorkflowLintResult]:
        return r[m.Infra.WorkflowLintResult].ok(
            m.Infra.WorkflowLintResult(status="ok"),
        )

    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        ok = self._ok_lint()

        def _lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            return ok

        monkeypatch.setattr(u.Infra, "github_lint_workflows", staticmethod(_lint))
        result = FlextInfraCliGithub._handle_lint(
            m.Infra.GithubLintInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            return r[m.Infra.WorkflowLintResult].fail("lint failed")

        monkeypatch.setattr(u.Infra, "github_lint_workflows", staticmethod(_lint))
        result = FlextInfraCliGithub._handle_lint(
            m.Infra.GithubLintInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: MutableMapping[str, Path | None] = {}
        ok = self._ok_lint()

        def _fake_lint(**kw: Path | None) -> r[m.Infra.WorkflowLintResult]:
            captured.update(kw)
            return ok

        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        report = tmp_path / "report.json"
        FlextInfraCliGithub._handle_lint(
            m.Infra.GithubLintInput(workspace=str(tmp_path), report=str(report)),
        )
        assert captured["report_path"] == report

    def test_with_strict_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, bool] = {}
        ok = self._ok_lint()

        def _fake_lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            captured.update(kw)
            return ok

        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        FlextInfraCliGithub._handle_lint(
            m.Infra.GithubLintInput(workspace=str(tmp_path), strict=True),
        )
        assert captured["strict"] is True


class TestRunPr:
    def test_delegates_to_pr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _pr(**kw: str) -> r[m.Infra.PrExecutionResultModel]:
            return r[m.Infra.PrExecutionResultModel].ok(
                m.Infra.PrExecutionResultModel(
                    display="test-repo",
                    status="ok",
                    elapsed=0,
                    exit_code=0,
                ),
            )

        monkeypatch.setattr(u.Infra, "github_pr_run_single", staticmethod(_pr))
        result = FlextInfraCliGithub._handle_pr(
            m.Infra.GithubPrInput(repo_root="/tmp", action="status"),
        )
        tm.that(result.is_success, eq=True)
