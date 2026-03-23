"""Tests for __main__.py main() dispatch integration."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_core import r

from flext_infra import u
from flext_infra.github import __main__ as github_main
from tests import m

main = github_main.main


def _orch(*, fail: int = 0, total: int = 1) -> m.Infra.PrOrchestrationResult:
    return m.Infra.PrOrchestrationResult(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        results=(),
    )


class TestMain:
    def test_help_flag(self) -> None:
        original = sys.argv.copy()
        try:
            sys.argv = ["flext-infra", "-h"]
            assert main() == 0
        finally:
            sys.argv = original

    def test_no_args(self) -> None:
        original = sys.argv.copy()
        try:
            sys.argv = ["flext-infra"]
            assert main() == 1
        finally:
            sys.argv = original

    def test_workflows_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(
                lambda **kw: r[Sequence[m.Infra.SyncOperation]].ok([]),
            ),
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "workflows",
                "--workspace",
                str(tmp_path),
            ]
            assert main() == 0
        finally:
            sys.argv = original

    def test_lint_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(
                lambda **kw: r[m.Infra.WorkflowLintResult].ok(
                    m.Infra.WorkflowLintResult(status="ok"),
                ),
            ),
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "lint",
                "--workspace",
                str(tmp_path),
            ]
            assert main() == 0
        finally:
            sys.argv = original

    def test_pr_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            github_main,
            "run_pr",
            lambda argv: 0,
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "pr",
            ]
            assert main() == 0
        finally:
            sys.argv = original

    def test_pr_workspace_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(
                lambda **kw: r[m.Infra.PrOrchestrationResult].ok(
                    _orch(fail=0),
                ),
            ),
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "pr-workspace",
                "--workspace",
                str(tmp_path),
            ]
            assert main() == 0
        finally:
            sys.argv = original

    def test_unknown_subcommand(self) -> None:
        original = sys.argv.copy()
        try:
            sys.argv = ["flext-infra", "unknown"]
            # argparse exits with code 2 for unrecognized arguments;
            # run_cli catches SystemExit and forwards the exit code.
            assert main() == 2
        finally:
            sys.argv = original

    def test_ensures_structlog_configured(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        called: Sequence[bool] = []
        monkeypatch.setattr(
            u.Infra,
            "github_lint_workflows",
            staticmethod(
                lambda **kw: r[m.Infra.WorkflowLintResult].ok(
                    m.Infra.WorkflowLintResult(status="ok"),
                ),
            ),
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "lint",
                "--workspace",
                str(tmp_path),
            ]
            result = main()
            called.append(result == 0)
            assert called
        finally:
            sys.argv = original

    def test_workflows_iterates_operations(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ops = [
            m.Infra.SyncOperation(
                project="p1", path="ci.yml", action="create", reason="new"
            ),
            m.Infra.SyncOperation(
                project="p2",
                path="ci.yml",
                action="update",
                reason="changed",
            ),
        ]
        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(lambda **kw: r[Sequence[m.Infra.SyncOperation]].ok(ops)),
        )
        original = sys.argv.copy()
        try:
            sys.argv = [
                "flext-infra",
                "workflows",
                "--workspace",
                str(tmp_path),
            ]
            assert main() == 0
        finally:
            sys.argv = original
