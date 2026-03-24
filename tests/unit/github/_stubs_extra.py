"""CLI-oriented test doubles for github test modules.

Stubs for PR management, syncing, linting, workspace orchestration,
and utility facades used by CLI integration tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_core import r

from flext_infra import m, t


class StubPrManager:
    """Stub for FlextInfraPrManager used in CLI tests."""

    def __init__(
        self,
        status_returns: Sequence[r[t.ScalarMapping]] | None = None,
        create_returns: Sequence[r[t.ScalarMapping]] | None = None,
        view_returns: Sequence[r[str]] | None = None,
        checks_returns: Sequence[r[t.ScalarMapping]] | None = None,
        merge_returns: Sequence[r[t.Container]] | None = None,
        close_returns: Sequence[r[bool]] | None = None,
    ) -> None:
        self._status: list[r[t.ScalarMapping]] = list(status_returns or [])
        self._create: list[r[t.ScalarMapping]] = list(create_returns or [])
        self._view: list[r[str]] = list(view_returns or [])
        self._checks: list[r[t.ScalarMapping]] = list(checks_returns or [])
        self._merge: list[r[t.Container]] = list(merge_returns or [])
        self._close: list[r[bool]] = list(close_returns or [])

    @staticmethod
    def _pop_status(
        returns: list[r[t.ScalarMapping]],
    ) -> r[t.ScalarMapping]:
        if not returns:
            return r[t.ScalarMapping].fail("no return configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_view(returns: list[r[str]]) -> r[str]:
        if not returns:
            return r[str].fail("no return configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_merge(
        returns: list[r[t.Container]],
    ) -> r[t.Container]:
        if not returns:
            return r[t.Container].fail("no return configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_close(returns: list[r[bool]]) -> r[bool]:
        if not returns:
            return r[bool].fail("no return configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    def status(
        self,
        repo_root: Path,
        base: str,
        head: str,
    ) -> r[t.ScalarMapping]:
        _ = repo_root, base, head
        return self._pop_status(self._status)

    def create(
        self,
        repo_root: Path,
        base: str,
        head: str,
        title: str,
        body: str,
        *,
        draft: bool = False,
    ) -> r[t.ScalarMapping]:
        _ = repo_root, base, head, title, body, draft
        return self._pop_status(self._create)

    def view(self, repo_root: Path, selector: str) -> r[str]:
        _ = repo_root, selector
        return self._pop_view(self._view)

    def checks(
        self,
        repo_root: Path,
        selector: str,
        *,
        strict: bool = False,
    ) -> r[t.ScalarMapping]:
        _ = repo_root, selector, strict
        return self._pop_status(self._checks)

    def merge(
        self,
        repo_root: Path,
        selector: str,
        head: str,
        *,
        method: str = "squash",
        auto: bool = False,
        delete_branch: bool = False,
        release_on_merge: bool = True,
    ) -> r[t.Container]:
        _ = repo_root, selector, head, method, auto, delete_branch, release_on_merge
        return self._pop_merge(self._merge)

    def close(self, repo_root: Path, selector: str) -> r[bool]:
        _ = repo_root, selector
        return self._pop_close(self._close)


class StubSyncer:
    """Stub for FlextInfraWorkflowSyncer used in CLI tests."""

    def __init__(
        self,
        sync_returns: r[Sequence[m.Infra.SyncOperation]] | None = None,
    ) -> None:
        self._sync_returns = (
            sync_returns
            if sync_returns is not None
            else r[Sequence[m.Infra.SyncOperation]].ok([])
        )
        self.sync_workspace_calls: list[Mapping[str, t.Infra.InfraValue]] = []

    def sync_workspace(
        self,
        workspace_root: Path,
        *,
        source_workflow: Path | None = None,
        report_path: Path | None = None,
        apply: bool = False,
        prune: bool = False,
    ) -> r[Sequence[m.Infra.SyncOperation]]:
        kwargs: Mapping[str, t.Infra.InfraValue] = {
            "workspace_root": str(workspace_root),
            "source_workflow": str(source_workflow) if source_workflow else None,
            "report_path": str(report_path) if report_path else None,
            "apply": apply,
            "prune": prune,
        }
        self.sync_workspace_calls.append(kwargs)
        return self._sync_returns


class StubLinter:
    """Stub for FlextInfraWorkflowLinter used in CLI tests."""

    def __init__(
        self,
        lint_returns: r[m.Infra.WorkflowLintResult] | None = None,
    ) -> None:
        self._lint_returns = (
            lint_returns
            if lint_returns is not None
            else r[m.Infra.WorkflowLintResult].ok(
                m.Infra.WorkflowLintResult(status="ok", exit_code=0),
            )
        )
        self.lint_calls: list[Mapping[str, t.Infra.InfraValue]] = []

    def lint(
        self,
        root: Path,
        *,
        report_path: Path | None = None,
        strict: bool = False,
    ) -> r[m.Infra.WorkflowLintResult]:
        kwargs: Mapping[str, t.Infra.InfraValue] = {
            "root": str(root),
            "report_path": str(report_path) if report_path else None,
            "strict": strict,
        }
        self.lint_calls.append(kwargs)
        return self._lint_returns


class StubWorkspaceManager:
    """Stub for FlextInfraPrWorkspaceManager used in CLI tests."""

    def __init__(
        self,
        orchestrate_returns: r[m.Infra.PrOrchestrationResult] | None = None,
    ) -> None:
        self._orchestrate_returns = (
            orchestrate_returns
            if orchestrate_returns is not None
            else r[m.Infra.PrOrchestrationResult].ok(
                m.Infra.PrOrchestrationResult(
                    total=0,
                    success=0,
                    fail=0,
                    results=(),
                ),
            )
        )
        self.orchestrate_calls: list[Mapping[str, t.Infra.InfraValue]] = []

    def orchestrate(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        include_root: bool = True,
        branch: str = "",
        checkpoint: bool = True,
        fail_fast: bool = False,
        pr_args: t.StrMapping | None = None,
    ) -> r[m.Infra.PrOrchestrationResult]:
        infra_projects: list[str] | None = (
            [str(p) for p in projects] if projects else None
        )
        infra_pr_args: dict[str, t.Infra.InfraValue] | None = (
            dict(pr_args) if pr_args else None
        )
        kwargs: Mapping[str, t.Infra.InfraValue] = {
            "workspace_root": str(workspace_root),
            "projects": infra_projects,
            "include_root": include_root,
            "branch": branch,
            "checkpoint": checkpoint,
            "fail_fast": fail_fast,
            "pr_args": infra_pr_args,
        }
        self.orchestrate_calls.append(kwargs)
        return self._orchestrate_returns


class StubUtilities:
    """Stub for u (FlextInfraUtilities) used in CLI tests."""

    class Infra:
        """Stub for u.Infra namespace."""

        _git_branch_returns: r[str] | None = None

        @classmethod
        def git_current_branch(cls, *_a: t.Scalar, **_kw: t.Scalar) -> r[str]:
            return cls._git_branch_returns or r[str].ok("feature")

        @classmethod
        def git_has_changes(cls, *_a: t.Scalar, **_kw: t.Scalar) -> r[bool]:
            return r[bool].ok(True)

        @classmethod
        def git_checkout(cls, *_a: t.Scalar, **_kw: t.Scalar) -> r[bool]:
            return r[bool].ok(True)

        @classmethod
        def git_add(cls, *_a: t.Scalar, **_kw: t.Scalar) -> r[bool]:
            return r[bool].ok(True)

        @classmethod
        def git_commit(cls, *_a: t.Scalar, **_kw: t.Scalar) -> r[bool]:
            return r[bool].ok(True)


__all__ = [
    "StubLinter",
    "StubPrManager",
    "StubSyncer",
    "StubUtilities",
    "StubWorkspaceManager",
]
