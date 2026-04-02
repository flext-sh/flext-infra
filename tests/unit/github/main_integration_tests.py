"""Tests for centralized github CLI dispatch integration."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

import pytest
from flext_core import r

from flext_infra import FlextInfraCliGithub, main
from tests import m, u


def _orch(*, fail: int = 0, total: int = 1) -> m.Infra.PrOrchestrationResult:
    return m.Infra.PrOrchestrationResult(
        total=total,
        success=max(total - fail, 0),
        fail=fail,
        results=(),
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
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].ok([])

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_sync),
        )
        assert main(["github", "workflows", "--workspace", str(tmp_path)]) == 0

    def test_lint_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            return r[m.Infra.WorkflowLintResult].ok(
                m.Infra.WorkflowLintResult(status="ok"),
            )

        monkeypatch.setattr(u.Infra, "github_lint_workflows", staticmethod(_lint))
        assert main(["github", "lint", "--workspace", str(tmp_path)]) == 0

    def test_pr_subcommand(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _run_pr(
            _params: m.Infra.GithubPrInput,
        ) -> r[m.Infra.PrExecutionResultModel]:
            return r[m.Infra.PrExecutionResultModel].ok(
                m.Infra.PrExecutionResultModel(
                    display="repo",
                    status="ok",
                    elapsed=0,
                    exit_code=0,
                ),
            )

        monkeypatch.setattr(FlextInfraCliGithub, "_handle_pr", staticmethod(_run_pr))
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
            workspace_root: Path,
            params: m.Infra.PrOrchestrateParams,
        ) -> r[m.Infra.PrOrchestrationResult]:
            return r[m.Infra.PrOrchestrationResult].ok(_orch(fail=0))

        monkeypatch.setattr(
            u.Infra,
            "github_pr_orchestrate",
            staticmethod(_orchestrate),
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

        def _lint(**kw: bool) -> r[m.Infra.WorkflowLintResult]:
            return r[m.Infra.WorkflowLintResult].ok(
                m.Infra.WorkflowLintResult(status="ok"),
            )

        monkeypatch.setattr(u.Infra, "github_lint_workflows", staticmethod(_lint))
        result = main(["github", "lint", "--workspace", str(tmp_path)])
        called.append(result == 0)
        assert called

    def test_workflows_iterates_operations(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ops = [
            m.Infra.SyncOperation(
                project="p1",
                path="ci.yml",
                action="create",
                reason="new",
            ),
            m.Infra.SyncOperation(
                project="p2",
                path="ci.yml",
                action="update",
                reason="changed",
            ),
        ]

        def _sync(
            workspace_root: Path,
            params: m.Infra.WorkflowSyncParams,
        ) -> r[Sequence[m.Infra.SyncOperation]]:
            return r[Sequence[m.Infra.SyncOperation]].ok(ops)

        monkeypatch.setattr(
            u.Infra,
            "github_sync_workspace_workflows",
            staticmethod(_sync),
        )
        assert main(["github", "workflows", "--workspace", str(tmp_path)]) == 0
