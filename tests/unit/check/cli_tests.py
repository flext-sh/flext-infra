"""Tests for FlextCheckCli to achieve full coverage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm

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
