"""Tests for FlextInfraWorkspaceChecker service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import r, tm

from flext_cli import u as cli_u
from flext_infra import main
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import u as test_u

if TYPE_CHECKING:
    from pathlib import Path


class TestFlextInfraWorkspaceChecker:
    """Test suite for FlextInfraWorkspaceChecker."""

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

    def test_cli_auto_discovers_projects(self, tmp_path: Path) -> None:
        """Test that check run discovers workspace projects by default."""
        project_dir = test_u.Tests.mk_project(
            tmp_path,
            "flext-core",
            pyproject=(
                '[project]\nname = "flext-core"\nversion = "0.1.0"\n'
                "[tool.hatch.build.targets.wheel]\n"
                'packages = ["src/flext_core"]\n'
            ),
            with_src=True,
        )
        package_dir = project_dir / "src" / "flext_core"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "module.py").write_text("value = 1\n", encoding="utf-8")
        init_result = cli_u.Cli.run_raw(["git", "init"], cwd=tmp_path)
        add_result = cli_u.Cli.run_raw(["git", "add", "flext-core"], cwd=tmp_path)
        tm.ok(init_result)
        tm.ok(add_result)

        exit_code = main([
            "check",
            "run",
            "--workspace",
            str(tmp_path),
            "--gates",
            "lint",
        ])

        tm.that(exit_code, eq=0)

    def test_resolve_gates_with_valid_gates(self) -> None:
        """Test that resolve_gates normalizes valid gate names."""
        result = FlextInfraWorkspaceChecker.resolve_gates(["lint", "type"])
        tm.ok(result)
        tm.that(result.value, has="lint")
        tm.that(result.value, has="pyrefly")

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
        assert not result.value

    def test_run_projects_creates_reports_dir(self, tmp_path: Path) -> None:
        """Test that run_projects creates reports directory if missing."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        result = checker.run_projects([], ["lint"], reports_dir=reports_dir)
        tm.ok(result)
        assert reports_dir.exists()

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
