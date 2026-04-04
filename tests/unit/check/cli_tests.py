"""Tests for FlextCheckCli to achieve full coverage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm
from tests import m, t

from flext_core import r
from flext_infra import FlextInfraWorkspaceChecker

from ._shared_fixtures import create_fake_run_projects


def test_resolve_gates_maps_type_alias() -> None:
    result = FlextInfraWorkspaceChecker.resolve_gates(["lint", "type", "lint"])
    tm.ok(result)
    assert result.value == ["lint", "pyrefly"]


def test_run_cli_run_returns_zero_for_pass(monkeypatch: MonkeyPatch) -> None:
    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        create_fake_run_projects(),
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint,type",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 0


def test_run_cli_run_returns_one_for_fail(monkeypatch: MonkeyPatch) -> None:
    """Test that run_cli returns 1 when projects fail checks."""
    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        create_fake_run_projects(passed=False),
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 1


def test_run_cli_run_returns_two_for_error(monkeypatch: MonkeyPatch) -> None:
    """Test that run_cli returns 2 when run_projects fails."""
    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        create_fake_run_projects(error_msg="test error"),
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 2


def test_run_cli_with_multiple_projects(monkeypatch: MonkeyPatch) -> None:
    """Test that run_cli handles multiple projects."""
    mock = create_fake_run_projects()
    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        mock,
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint",
        "--projects",
        "proj1",
        "--projects",
        "proj2",
    ])
    assert exit_code == 0
    assert "proj1" in mock.captured_projects
    assert "proj2" in mock.captured_projects


def test_run_cli_with_fail_fast_flag(monkeypatch: MonkeyPatch) -> None:
    """Test that run_cli passes fail_fast flag to run_projects."""
    mock = create_fake_run_projects()
    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        mock,
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint",
        "--fail-fast",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 0
    assert mock.captured_fail_fast is True


def test_run_cli_run_forwards_fix_and_tool_args(monkeypatch: MonkeyPatch) -> None:
    captured_projects: list[str] = []
    captured_gates: list[str] = []
    captured_ctx: list[m.Infra.GateContext] = []

    def _fake_run_projects(
        _self: FlextInfraWorkspaceChecker,
        projects: t.StrSequence,
        gates: t.StrSequence,
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        ctx: m.Infra.GateContext | None = None,
    ) -> r[list[m.Infra.ProjectResult]]:
        del reports_dir, fail_fast
        captured_projects.extend(projects)
        captured_gates.extend(gates)
        if ctx is not None:
            captured_ctx.append(ctx)
        project = m.Infra.ProjectResult(project="flext-core", gates={})
        return r[list[m.Infra.ProjectResult]].ok([project])

    _ = monkeypatch.setattr(
        FlextInfraWorkspaceChecker,
        "run_projects",
        _fake_run_projects,
    )
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "run",
        "--gates",
        "lint,pyright",
        "--fix",
        "--check-only",
        "--ruff-args",
        "--select E501",
        "--pyright-args",
        "--level basic",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 0
    assert captured_projects == ["flext-core"]
    assert captured_gates == ["lint", "pyright"]
    assert len(captured_ctx) == 1
    assert captured_ctx[0].apply_fixes is True
    assert captured_ctx[0].check_only is True
    assert list(captured_ctx[0].ruff_args) == ["--select", "E501"]
    assert list(captured_ctx[0].pyright_args) == ["--level", "basic"]


def test_run_cli_accepts_shared_dry_run_flag() -> None:
    exit_code = FlextInfraWorkspaceChecker.run_cli([
        "--dry-run",
        "run",
        "--projects",
        "flext-core",
    ])
    assert exit_code == 0
