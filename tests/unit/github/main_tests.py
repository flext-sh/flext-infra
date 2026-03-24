"""Tests for flext_infra.github.__main__ CLI entry point."""

from __future__ import annotations

import argparse
from collections.abc import MutableMapping, Sequence
from pathlib import Path

import pytest
from flext_core import r

from flext_infra import u
from flext_infra.github.__main__ import run_lint, run_pr, run_workflows
from tests import m


def _ns(tmp_path: Path, *, apply: bool = False) -> argparse.Namespace:
    return argparse.Namespace(workspace=tmp_path, apply=apply)


class TestRunWorkflows:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra, "github_sync_workspace_workflows", staticmethod(_sync),
        )
        cli = u.Infra.resolve(_ns(tmp_path))
        assert run_workflows(cli, prune=False, report=None) == 0

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].fail("sync failed")

        monkeypatch.setattr(
            u.Infra, "github_sync_workspace_workflows", staticmethod(_sync),
        )
        cli = u.Infra.resolve(_ns(tmp_path))
        assert run_workflows(cli, prune=False, report=None) == 1

    def test_with_apply_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, bool] = {}

        def _fake_sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(_ns(tmp_path, apply=True))
        run_workflows(cli, prune=False, report=None)
        assert captured["apply"] is True

    def test_with_prune_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: MutableMapping[str, bool] = {}

        def _fake_sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(_ns(tmp_path))
        run_workflows(cli, prune=True, report=None)
        assert captured["prune"] is True

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: MutableMapping[str, Path | None] = {}

        def _fake_sync(**kw: Path | None) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(_ns(tmp_path))
        report = tmp_path / "report.json"
        run_workflows(cli, prune=False, report=report)
        assert captured["report_path"] == report


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
        cli = u.Infra.resolve(_ns(tmp_path))
        assert run_lint(cli, report=None, strict=False) == 0

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def _lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            return r[m.Infra.WorkflowLintResult].fail("lint failed")

        monkeypatch.setattr(u.Infra, "github_lint_workflows", staticmethod(_lint))
        cli = u.Infra.resolve(_ns(tmp_path))
        assert run_lint(cli, report=None, strict=False) == 1

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
        cli = u.Infra.resolve(_ns(tmp_path))
        report = tmp_path / "report.json"
        run_lint(cli, report=report, strict=False)
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
        cli = u.Infra.resolve(_ns(tmp_path))
        run_lint(cli, report=None, strict=True)
        assert captured["strict"] is True


class TestRunPr:
    def test_delegates_to_pr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _pr(**kw: str) -> r[m.Infra.CommandOutput]:
            return r[m.Infra.CommandOutput].ok(
                m.Infra.CommandOutput(exit_code=0, stdout="ok", stderr=""),
            )

        monkeypatch.setattr(u.Infra, "github_pr_run_single", staticmethod(_pr))
        assert run_pr(["--repo-root", "/tmp", "--action", "status"]) == 0

    def test_sets_sys_argv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _pr(**kw: str) -> r[m.Infra.CommandOutput]:
            return r[m.Infra.CommandOutput].ok(
                m.Infra.CommandOutput(exit_code=0, stdout="ok", stderr=""),
            )

        monkeypatch.setattr(u.Infra, "github_pr_run_single", staticmethod(_pr))
        run_pr(["--repo-root", "/tmp", "--action", "status"])
