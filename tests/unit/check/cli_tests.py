"""Tests for FlextCheckCli to achieve full coverage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flext_core import r
from flext_tests import tm

from flext_infra import FlextInfraWorkspaceChecker
from tests import m, t

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
        "--project",
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
        "--project",
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
        "--project",
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
        "--project",
        "proj1",
        "--project",
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
        "--project",
        "flext-core",
    ])
    assert exit_code == 0
    assert mock.captured_fail_fast is True


def test_run_cli_run_forwards_fix_and_tool_args(monkeypatch: MonkeyPatch) -> None:
    captured_projects: list[str] = []
    captured_gates: list[str] = []
    captured_fix = False
    captured_check_only = False
    captured_ruff_args: list[str] = []
    captured_pyright_args: list[str] = []

    def _fake_run_projects(
        _self: FlextInfraWorkspaceChecker,
        projects: t.StrSequence,
        gates: t.StrSequence,
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        fix: bool = False,
        check_only: bool = False,
        ruff_args: t.StrSequence | None = None,
        pyright_args: t.StrSequence | None = None,
    ) -> r[list[m.Infra.ProjectResult]]:
        nonlocal \
            captured_fix, \
            captured_check_only, \
            captured_ruff_args, \
            captured_pyright_args
        del reports_dir, fail_fast
        captured_projects.extend(projects)
        captured_gates.extend(gates)
        captured_fix = fix
        captured_check_only = check_only
        captured_ruff_args = list(ruff_args or [])
        captured_pyright_args = list(pyright_args or [])
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
        "--project",
        "flext-core",
    ])
    assert exit_code == 0
    assert captured_projects == ["flext-core"]
    assert captured_gates == ["lint", "pyright"]
    assert captured_fix is True
    assert captured_check_only is True
    assert captured_ruff_args == ["--select", "E501"]
    assert captured_pyright_args == ["--level", "basic"]


def test_run_cli_rejects_fix_flags_for_run() -> None:
    with pytest.raises(SystemExit) as exc_info:
        FlextInfraWorkspaceChecker.run_cli([
            "--dry-run",
            "run",
            "--project",
            "flext-core",
        ])
    assert exc_info.value.code == 2
