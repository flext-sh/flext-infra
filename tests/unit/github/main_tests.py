"""Tests for flext_infra.github.__main__ CLI entry point."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from flext_core import r

from flext_infra import u
from flext_infra.github.__main__ import run_lint, run_pr, run_workflows
from tests import m


class TestRunWorkflows:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflist",
            staticmethod(lambda **kw: r[Sequence[m.Infra.SyncOperation]].ok([])),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        assert run_workflows(cli, prune=False, report=None) == 0

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflist",
            staticmethod(
                lambda **kw: r[Sequence[m.Infra.SyncOperation]].fail("sync failed"),
            ),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        assert run_workflows(cli, prune=False, report=None) == 1

    def test_with_apply_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, bool] = {}

        def _fake_sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": True})())
        run_workflows(cli, prune=False, report=None)
        assert captured["apply"] is True

    def test_with_prune_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, bool] = {}

        def _fake_sync(**kw: bool) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        run_workflows(cli, prune=True, report=None)
        assert captured["prune"] is True

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Path | None] = {}

        def _fake_sync(**kw: Path | None) -> r[Sequence[m.Infra.SyncOperation]]:
            captured.update(kw)
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_fake_sync),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
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
        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(lambda **kw: ok),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        assert run_lint(cli, report=None, strict=False) == 0

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(
                lambda **kw: r[m.Infra.WorkflowLintResult].fail("lint failed"),
            ),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        assert run_lint(cli, report=None, strict=False) == 1

    def test_with_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: Mapping[str, Path | None] = {}
        ok = self._ok_lint()

        def _fake_lint(**kw: Path | None) -> r[m.Infra.WorkflowLintResult]:
            captured.update(kw)
            return ok

        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        report = tmp_path / "report.json"
        run_lint(cli, report=report, strict=False)
        assert captured["report_path"] == report

    def test_with_strict_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: Mapping[str, bool] = {}
        ok = self._ok_lint()

        def _fake_lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            captured.update(kw)
            return ok

        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(_fake_lint),
        )
        cli = u.Infra.resolve(type("NS", (), {"workspace": tmp_path, "apply": False})())
        run_lint(cli, report=None, strict=True)
        assert captured["strict"] is True


class TestRunPr:
    def test_delegates_to_pr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_run_single",
            staticmethod(
                lambda **kw: r[m.Infra.CommandOutput].ok(
                    m.Infra.CommandOutput(exit_code=0, stdout="ok", stderr=""),
                ),
            ),
        )
        assert run_pr(["--repo-root", "/tmp", "--action", "status"]) == 0

    def test_sets_sys_argv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_run_single",
            staticmethod(
                lambda **kw: r[m.Infra.CommandOutput].ok(
                    m.Infra.CommandOutput(exit_code=0, stdout="ok", stderr=""),
                ),
            ),
        )
        run_pr(["--repo-root", "/tmp", "--action", "status"])
