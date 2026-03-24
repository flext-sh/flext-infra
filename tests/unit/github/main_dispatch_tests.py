"""Tests for __main__.py run_pr_workspace dispatch."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import m, u
from flext_infra.github.__main__ import run_pr_workspace


def _orch(*, fail: int = 0, total: int = 1) -> m.Infra.PrOrchestrationResult:
    return m.Infra.PrOrchestrationResult(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        results=(),
    )


def _cli(tmp_path: Path) -> u.Infra.CliArgs:
    return u.Infra.resolve(
        type("NS", (), {"workspace": tmp_path, "apply": False, "projects": None})(),
    )


def _pr_args(**overrides: str | bool) -> m.Infra.PrWorkspaceArgs:
    defaults: Mapping[str, str | bool] = {
        "include_root": True,
        "branch": "",
        "checkpoint": True,
        "fail_fast": False,
        "pr_action": "status",
        "pr_base": "main",
        "pr_head": "",
        "pr_number": "",
        "pr_title": "",
        "pr_body": "",
        "pr_draft": False,
        "pr_merge_method": "squash",
        "pr_auto": False,
        "pr_delete_branch": False,
        "pr_checks_strict": False,
        "pr_release_on_merge": True,
    }
    defaults.update(overrides)
    return m.Infra.PrWorkspaceArgs.model_validate(defaults)


class TestRunPrWorkspace:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(
                lambda **kw: r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0)),
            ),
        )
        assert run_pr_workspace(_cli(tmp_path), _pr_args()) == 0

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(
                lambda **kw: r[m.Infra.PrOrchestrationResult].fail(
                    "orchestration failed",
                ),
            ),
        )
        assert run_pr_workspace(_cli(tmp_path), _pr_args()) == 1

    def test_with_failures(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(
                lambda **kw: r[m.Infra.PrOrchestrationResult].fail(
                    "orchestration had failures",
                ),
            ),
        )
        assert run_pr_workspace(_cli(tmp_path), _pr_args()) == 1

    def test_with_pr_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: Mapping[str, Mapping[str, str]] = {}

        def _fake_orchestrate(
            **kw: Mapping[str, str],
        ) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        pr = _pr_args(pr_action="merge", pr_base="main", pr_head="feature/test")
        assert run_pr_workspace(_cli(tmp_path), pr) == 0
        pr_args_val = captured.get("pr_args", {})
        tm.that(str(pr_args_val), has="action")
        tm.that(str(pr_args_val), has="base")
        tm.that(str(pr_args_val), has="head")

    def test_with_branch(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: Mapping[str, str] = {}

        def _fake_orchestrate(**kw: str) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        pr = _pr_args(branch="feature/test")
        run_pr_workspace(_cli(tmp_path), pr)
        assert captured["branch"] == "feature/test"

    def test_with_checkpoint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: Mapping[str, bool] = {}

        def _fake_orchestrate(**kw: bool) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        pr = _pr_args(checkpoint=True)
        run_pr_workspace(_cli(tmp_path), pr)
        assert captured["checkpoint"] is True

    def test_with_fail_fast(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: Mapping[str, bool] = {}

        def _fake_orchestrate(**kw: bool) -> r[m.Infra.PrOrchestrationResult]:
            captured.update(kw)
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_fake_orchestrate),
        )
        pr = _pr_args(fail_fast=True)
        run_pr_workspace(_cli(tmp_path), pr)
        assert captured["fail_fast"] is True
