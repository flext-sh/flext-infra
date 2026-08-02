"""Tests for FlextInfraWorkspaceChecker service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u as cli_u
from flext_infra import config, main, r
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_tests import tm
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
            config.Infra.codegen.make.check.gate_ids[0],
        ])

        tm.that(exit_code, eq=0)

    def test_resolve_gates_with_valid_gates(self) -> None:
        """Test that resolve_gates normalizes valid gate names."""
        expected_gate_ids = list(config.Infra.codegen.make.check.gate_ids)
        result = FlextInfraWorkspaceChecker.resolve_gates(expected_gate_ids)
        tm.ok(result)
        tm.that(result.value, eq=expected_gate_ids)

    def test_resolve_gates_defaults_to_configured_catalog(self) -> None:
        """Test that an empty selection resolves the complete typed catalog."""
        expected_gate_ids = list(config.Infra.codegen.make.check.gate_ids)
        result = FlextInfraWorkspaceChecker.resolve_gates([])
        tm.that(result, is_=r)
        tm.ok(result)
        tm.that(result.value, eq=expected_gate_ids)

    def test_resolve_gates_deduplicates(self) -> None:
        """Test that resolve_gates removes duplicate gate names."""
        gate_ids = config.Infra.codegen.make.check.gate_ids
        requested_gate_ids = [gate_ids[0], gate_ids[0], *gate_ids[1:2]]
        result = FlextInfraWorkspaceChecker.resolve_gates(requested_gate_ids)
        tm.ok(result)
        tm.that(result.value, eq=list(dict.fromkeys(requested_gate_ids)))

    def test_resolve_gates_with_invalid_gate(self) -> None:
        """Test that resolve_gates fails on invalid gate name."""
        result = FlextInfraWorkspaceChecker.resolve_gates(["invalid_gate"])
        tm.fail(result)

    def test_run_projects_with_missing_projects(self, tmp_path: Path) -> None:
        """Test that run_projects rejects missing project directories."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        result = checker.run_projects(
            ["nonexistent"],
            config.Infra.codegen.make.check.gate_ids,
            reports_dir=tmp_path / "reports",
        )
        tm.fail(result)
        tm.that(result.error, has="pyproject.toml")

    def test_run_projects_creates_reports_dir(self, tmp_path: Path) -> None:
        """Test that run_projects creates reports directory if missing."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        result = checker.run_projects(
            [], config.Infra.codegen.make.check.gate_ids, reports_dir=reports_dir
        )
        tm.that(result, is_=r)
        tm.ok(result)
        tm.that(reports_dir.exists(), eq=True)
