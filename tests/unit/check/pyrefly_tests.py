"""Tests for FlextInfraConfigFixer service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer

if TYPE_CHECKING:
    from pathlib import Path


class TestFlextInfraConfigFixer:
    """Test suite for FlextInfraConfigFixer."""

    def test_init_creates_instance(self) -> None:
        """Test that fixer initializes with default workspace root."""
        fixer = FlextInfraConfigFixer()
        tm.that(fixer, none=False)

    def test_init_with_custom_workspace_root(self, tmp_path: Path) -> None:
        """Test that fixer accepts custom workspace root."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.that(fixer, none=False)

    def test_execute_returns_failure(self) -> None:
        """Test that execute() returns failure with helpful message."""
        fixer = FlextInfraConfigFixer()
        result = fixer.execute()
        tm.fail(result)
        tm.that(result.error, is_=str)
        tm.that(result.error, is_=str)
        tm.that(result.error, has="Use execute_command() directly")

    def test_run_with_empty_projects(self, tmp_path: Path) -> None:
        """Test that run() handles empty project list."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.run([])
        tm.ok(result)
        tm.that(result.value, is_=list)

    def test_run_with_nonexistent_projects(self, tmp_path: Path) -> None:
        """Test that run() handles nonexistent projects gracefully."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.run(["nonexistent"])
        tm.ok(result)

    def test_run_with_dry_run_flag(self, tmp_path: Path) -> None:
        """Test that run() respects dry_run flag."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.run([], dry_run=True)
        tm.ok(result)

    def test_run_with_verbose_flag(self, tmp_path: Path) -> None:
        """Test that run() respects verbose flag."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.run([], verbose=True)
        tm.ok(result)

    def test_process_file_with_missing_file(self, tmp_path: Path) -> None:
        """Test that process_file handles missing files gracefully."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        missing_file = tmp_path / "nonexistent.toml"
        result = fixer.process_file(missing_file)
        tm.fail(result)
        tm.that(result.error, is_=str)
        assert "not found" in result.error or "failed to read" in result.error

    def test_process_file_with_valid_toml(self, tmp_path: Path) -> None:
        """Test that process_file handles valid TOML without pyrefly section."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool]\nother = true\n")
        result = fixer.process_file(pyproject)
        tm.ok(result)
        tm.that(result.value, eq=[])

    def test_process_file_with_invalid_toml(self, tmp_path: Path) -> None:
        """Test that process_file handles invalid TOML gracefully."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[invalid toml")
        result = fixer.process_file(pyproject)
        tm.fail(result)
        tm.that(result.error, is_=str)
        tm.that(result.error, has="TOML parse failed")

    def test_process_file_with_dry_run(self, tmp_path: Path) -> None:
        """Test that process_file with dry_run doesn't modify file."""
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        original_content = "[tool]\nother = true\n"
        pyproject.write_text(original_content)
        result = fixer.process_file(pyproject, dry_run=True)
        tm.ok(result)
        tm.that(pyproject.read_text(), eq=original_content)
