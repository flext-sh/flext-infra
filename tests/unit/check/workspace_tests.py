"""Tests for FlextInfraWorkspaceChecker service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_core import r
from flext_infra import c, main
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestFlextInfraWorkspaceChecker:
    """Test suite for FlextInfraWorkspaceChecker."""

    @pytest.fixture(autouse=True)
    def _clear_make_ci_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(c.Infra.PYTEST_ENV_CI, raising=False)

    def test_init_creates_instance(self) -> None:
        """Test that checker initializes with default workspace root."""
        checker = FlextInfraWorkspaceChecker()
        tm.that(checker, none=False)

    def test_init_with_custom_workspace_root(self, tmp_path: Path) -> None:
        """Test that checker accepts custom workspace root."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        tm.that(checker, none=False)

    def test_execute_returns_failure(self) -> None:
        """Test that execute() returns failure with helpful message."""
        checker = FlextInfraWorkspaceChecker()
        result = checker.execute()
        tm.fail(result)
        tm.that(result.error, is_=str)
        tm.that(result.error, is_=str)
        tm.that(result.error, has="Use execute_command() directly")

    def test_cli_returns_error_without_discovered_projects(
        self, tmp_path: Path
    ) -> None:
        """Test that check run fails when a workspace has no projects."""
        exit_code = main(["check", "run", "--workspace", str(tmp_path)])
        tm.that(exit_code, eq=1)

    def test_resolve_gates_with_valid_gates(self) -> None:
        """Test that resolve_gates normalizes valid gate names."""
        result = FlextInfraWorkspaceChecker.resolve_gates([
            "lint",
            "pyrefly",
            "mypy",
            "pyright",
        ])
        tm.ok(result)
        tm.that(result.value, eq=["lint", "pyrefly", "mypy", "pyright"])

    def test_resolve_gates_deduplicates(self) -> None:
        """Test that resolve_gates removes duplicate gate names."""
        result = FlextInfraWorkspaceChecker.resolve_gates(["lint", "lint", "format"])
        tm.ok(result)
        tm.that(result.value.count("lint"), eq=1)

    def test_resolve_gates_with_invalid_gate(self) -> None:
        """Test that resolve_gates fails on invalid gate name."""
        result = FlextInfraWorkspaceChecker.resolve_gates(["invalid_gate"])
        tm.fail(result)

    def test_run_projects_with_missing_projects(self, tmp_path: Path) -> None:
        """Test that run_projects handles missing project directories gracefully."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        result = checker.run_projects(
            ["nonexistent"], ["lint"], reports_dir=tmp_path / "reports"
        )
        tm.ok(result)
        tm.that(result.value, eq=[])

    def test_run_projects_creates_reports_dir(self, tmp_path: Path) -> None:
        """Test that run_projects creates reports directory if missing."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        result = checker.run_projects([], ["lint"], reports_dir=reports_dir)
        tm.ok(result)
        tm.that(reports_dir.exists(), eq=True)

    def test_lint_returns_gate_result(self, tmp_path: Path) -> None:
        """Test that lint() returns a GateResult."""
        checker = FlextInfraWorkspaceChecker()
        result = checker.lint(tmp_path)
        tm.that(result, is_=r)
        tm.ok(result)

    def test_format_returns_gate_result(self, tmp_path: Path) -> None:
        """Test that format() returns a GateResult."""
        checker = FlextInfraWorkspaceChecker()
        result = checker.format(tmp_path)
        tm.that(result, is_=r)
        tm.ok(result)
