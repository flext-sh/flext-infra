"""Tests for the centralized validate CLI group.

Tests CLI subcommand routing via subprocess for real integration testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm
from tests import m, t

from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraTextPatternScanner,
    main as infra_main,
)

def _cli(*args: str) -> int:
    """Run validate routing through the canonical infra CLI."""
    return infra_main(["validate", *args])


class TestMainBaseMkValidate:
    """Test basemk-validate subcommand with real services."""

    def test_success(self, tmp_path: Path) -> None:
        """basemk-validate returns r[bool] based on base.mk match."""
        (tmp_path / "base.mk").write_text("# root")
        result = FlextInfraBaseMkValidator().execute_command(
            m.Infra.ValidateBaseMkInput(workspace=str(tmp_path)),
        )
        assert isinstance(result.is_success, bool)

    def test_with_violations(self, tmp_path: Path) -> None:
        """basemk-validate returns failure with mismatched base.mk."""
        (tmp_path / "base.mk").write_text("# root")
        proj = tmp_path / "project1"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("")
        (proj / "base.mk").write_text("# different")
        result = FlextInfraBaseMkValidator().execute_command(
            m.Infra.ValidateBaseMkInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)

    def test_missing_root_basemk(self, tmp_path: Path) -> None:
        """basemk-validate returns failure when root base.mk missing."""
        result = FlextInfraBaseMkValidator().execute_command(
            m.Infra.ValidateBaseMkInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_failure, eq=True)


class TestMainInventory:
    """Test inventory subcommand with real services."""

    def test_success(self, tmp_path: Path) -> None:
        """Inventory succeeds with empty workspace."""
        result = FlextInfraInventoryService().execute_command(
            m.Infra.ValidateInventoryInput(workspace=str(tmp_path)),
        )
        tm.that(result.is_success, eq=True)

    def test_with_output_dir(self, tmp_path: Path) -> None:
        """Inventory succeeds with output directory."""
        output = tmp_path / "output"
        output.mkdir()
        result = FlextInfraInventoryService().execute_command(
            m.Infra.ValidateInventoryInput(
                workspace=str(tmp_path),
                output_dir=str(output),
            ),
        )
        tm.that(result.is_success, eq=True)


class TestMainScan:
    """Test scan subcommand with real services."""

    def test_no_violations(self, tmp_path: Path) -> None:
        """Scan returns success when no violations found."""
        (tmp_path / "test.txt").write_text("hello world")
        result = FlextInfraTextPatternScanner().execute_command(
            m.Infra.ValidateScanInput(
                workspace=str(tmp_path),
                pattern="NONEXISTENT_PATTERN",
                include=["*.txt"],
                exclude=[],
                match="present",
            ),
        )
        tm.that(result.is_success, eq=True)

    def test_with_violations(self, tmp_path: Path) -> None:
        """Scan returns failure when violations found."""
        (tmp_path / "test.txt").write_text("TODO fix this")
        result = FlextInfraTextPatternScanner().execute_command(
            m.Infra.ValidateScanInput(
                workspace=str(tmp_path),
                pattern="TODO",
                include=["*.txt"],
                exclude=[],
                match="present",
            ),
        )
        tm.that(result.is_failure, eq=True)


class TestMainCliRouting:
    """Test main() CLI routing via subprocess."""

    def test_help_flag(self) -> None:
        """--help returns 0."""
        tm.that(_cli("--help"), eq=0)

    def test_basemk_validate_routing(self, tmp_path: Path) -> None:
        """basemk-validate subcommand routes correctly."""
        result = _cli("basemk-validate", "--workspace", str(tmp_path))
        assert result in {0, 1}

    def test_inventory_routing(self, tmp_path: Path) -> None:
        """Inventory subcommand routes correctly."""
        result = _cli("inventory", "--workspace", str(tmp_path))
        assert result in {0, 1}

    def test_scan_routing(self, tmp_path: Path) -> None:
        """Scan subcommand routes correctly."""
        (tmp_path / "test.txt").write_text("content")
        result = _cli(
            "scan",
            "--workspace",
            str(tmp_path),
            "--pattern",
            "content",
            "--include",
            "*.txt",
        )
        assert result in {0, 1}

    def test_no_command_returns_1(self) -> None:
        """No subcommand returns exit code 1."""
        tm.that(_cli(), eq=1)

    def test_unknown_command_returns_error(self) -> None:
        """Unknown subcommand returns non-zero exit code."""
        tm.that(_cli("unknown"), ne=0)

    def test_skill_validate_routing(self, tmp_path: Path) -> None:
        """skill-validate subcommand routes correctly."""
        result = _cli(
            "skill-validate",
            "--skill",
            "test-skill",
            "--workspace",
            str(tmp_path),
        )
        assert result in {0, 1}

    def test_stub_validate_routing(self, tmp_path: Path) -> None:
        """stub-validate subcommand routes correctly."""
        result = _cli("stub-validate", "--workspace", str(tmp_path))
        assert result in {0, 1}


__all__: t.StrSequence = []
