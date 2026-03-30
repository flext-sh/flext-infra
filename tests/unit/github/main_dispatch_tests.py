"""Tests for __main__.py pr-workspace dispatch."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import m, t, u
from flext_infra.github.__main__ import FlextInfraGithubCli


def _orch(*, fail: int = 0, total: int = 1) -> m.Infra.PrOrchestrationResult:
    return m.Infra.PrOrchestrationResult(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        results=(),
    )


class TestRunPrWorkspace:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _ok(**kw: t.Scalar) -> r[m.Infra.PrOrchestrationResult]:
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(u.Infra, "github_pr_orchestrate", staticmethod(_ok))
        result = FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _fail(**kw: t.Scalar) -> r[m.Infra.PrOrchestrationResult]:
            return r[m.Infra.PrOrchestrationResult].fail("orchestration failed")

        monkeypatch.setattr(u.Infra, "github_pr_orchestrate", staticmethod(_fail))
        result = FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_with_pr_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, t.StrMapping] = {}

        def _fake_orchestrate(
            **kw: t.StrMapping,
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        result = FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                pr_action="merge",
                pr_base="main",
                pr_head="feature/test",
            ),
        )
        tm.that(result.is_success, eq=True)
        pr_args_val = captured.get("pr_args", {})
        tm.that(str(pr_args_val), has="action")
        tm.that(str(pr_args_val), has="base")
        tm.that(str(pr_args_val), has="head")

    def test_with_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, str] = {}

        def _fake_orchestrate(**kw: str) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                branch="feature/test",
            ),
        )
        assert captured["branch"] == "feature/test"

    def test_with_checkpoint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, bool] = {}

        def _fake_orchestrate(**kw: bool) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path), checkpoint=True),
        )
        assert captured["checkpoint"] is True

    def test_with_fail_fast(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, bool] = {}

        def _fake_orchestrate(**kw: bool) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(workspace=str(tmp_path), fail_fast=True),
        )
        assert captured["fail_fast"] is True

    def test_with_selected_projects(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_projects: list[str] = []

        def _fake_orchestrate(
            *,
            projects: t.StrSequence | None = None,
            **kw: t.Scalar,
        ) -> r[m.Infra.PrOrchestrationResult]:
            del kw
            nonlocal captured_projects
            captured_projects = list(projects or [])
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        FlextInfraGithubCli._handle_pr_workspace(
            m.Infra.GithubPrWorkspaceInput(
                workspace=str(tmp_path),
                project=["flext-core", "flext-api"],
            ),
        )
        assert captured_projects == ["flext-core", "flext-api"]
