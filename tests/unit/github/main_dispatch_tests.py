"""Tests for github pr-workspace dispatch in the centralized CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, u

from flext_core import r
from flext_infra import FlextInfraCliGithub


def _orch(*, fail: int = 0, total: int = 1) -> m.Infra.PrOrchestrationResult:
    return m.Infra.PrOrchestrationResult(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        results=(),
    )


class TestRunPrWorkspace:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _ok(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(u.Infra, "github_pr_orchestrate", staticmethod(_ok))
        result = FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _fail(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            return r[m.Infra.PrOrchestrationResult].fail("orchestration failed")

        monkeypatch.setattr(u.Infra, "github_pr_orchestrate", staticmethod(_fail))
        result = FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_pr_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_params: list[m.Infra.PrOrchestrateParams] = []

        def _fake_orchestrate(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured_params.append(params)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        result = FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                pr_action="merge",
                pr_base="main",
                pr_head="feature/test",
            ),
        )
        tm.that(result.is_success, eq=True)
        pr_args_val = captured_params[0].pr_args or {}
        tm.that(str(pr_args_val), has="action")
        tm.that(str(pr_args_val), has="base")
        tm.that(str(pr_args_val), has="head")

    def test_with_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_params: list[m.Infra.PrOrchestrateParams] = []

        def _fake_orchestrate(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured_params.append(params)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                branch="feature/test",
            ),
        )
        assert captured_params[0].branch == "feature/test"

    def test_with_checkpoint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_params: list[m.Infra.PrOrchestrateParams] = []

        def _fake_orchestrate(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured_params.append(params)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path), checkpoint=True),
        )
        assert captured_params[0].checkpoint is True

    def test_with_fail_fast(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_params: list[m.Infra.PrOrchestrateParams] = []

        def _fake_orchestrate(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured_params.append(params)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path), fail_fast=True),
        )
        assert captured_params[0].fail_fast is True

    def test_with_selected_projects(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_params: list[m.Infra.PrOrchestrateParams] = []

        def _fake_orchestrate(
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured_params.append(params)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraCliGithub._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                project=["flext-core", "flext-api"],
            ),
        )
        assert captured_params[0].projects == ["flext-core", "flext-api"]
