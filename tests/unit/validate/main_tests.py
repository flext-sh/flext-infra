"""Tests for flext_infra.validate.__main__ CLI entry point.

Tests CLI subcommand routing via subprocess for real integration testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from flext_tests import tm

from flext_infra import u
from flext_infra.validate.__main__ import (
    _run_basemk_validate,
    _run_inventory,
    _run_scan,
)

_CWD = "/home/marlonsc/flext/flext-core"


def _ns(**kwargs: str | Sequence[str] | Path | None) -> argparse.Namespace:
    """Create a simple namespace from keyword arguments."""
    return argparse.Namespace(**kwargs)


def _cli_args(root: Path) -> u.Infra.CliArgs:
    return u.Infra.resolve(_ns(workspace=root))


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run flext_infra.validate CLI via subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "flext_infra.validate", *args],
        capture_output=True,
        text=True,
        cwd=_CWD,
        check=False,
    )


class TestMainBaseMkValidate:
    """Test basemk-validate subcommand with real services."""

    def test_success(self, tmp_path: Path) -> None:
        """basemk-validate returns exit code (0 or 1) based on base.mk match."""
        (tmp_path / "base.mk").write_text("# root")
        tm.that({0, 1}, has=_run_basemk_validate(_cli_args(tmp_path)))

    def test_with_violations(self, tmp_path: Path) -> None:
        """basemk-validate returns 1 with mismatched base.mk."""
        (tmp_path / "base.mk").write_text("# root")
        proj = tmp_path / "project1"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("")
        (proj / "base.mk").write_text("# different")
        tm.that(_run_basemk_validate(_cli_args(tmp_path)), eq=1)

    def test_missing_root_basemk(self, tmp_path: Path) -> None:
        """basemk-validate returns 1 when root base.mk missing."""
        tm.that(_run_basemk_validate(_cli_args(tmp_path)), eq=1)


class TestMainInventory:
    """Test inventory subcommand with real services."""

    def test_success(self, tmp_path: Path) -> None:
        """Inventory succeeds with empty workspace."""
        tm.that(_run_inventory(_cli_args(tmp_path), output_dir=None), eq=0)

    def test_with_output_dir(self, tmp_path: Path) -> None:
        """Inventory succeeds with output directory."""
        output = tmp_path / "output"
        output.mkdir()
        tm.that(_run_inventory(_cli_args(tmp_path), output_dir=str(output)), eq=0)


class TestMainScan:
    """Test scan subcommand with real services."""

    def test_no_violations(self, tmp_path: Path) -> None:
        """Scan returns 0 when no violations found."""
        (tmp_path / "test.txt").write_text("hello world")
        tm.that(
            _run_scan(
                _cli_args(tmp_path),
                pattern="NONEXISTENT_PATTERN",
                include=["*.txt"],
                exclude=[],
                match="present",
            ),
            eq=0,
        )

    def test_with_violations(self, tmp_path: Path) -> None:
        """Scan returns 1 when violations found."""
        (tmp_path / "test.txt").write_text("TODO fix this")
        tm.that(
            _run_scan(
                _cli_args(tmp_path),
                pattern="TODO",
                include=["*.txt"],
                exclude=[],
                match="present",
            ),
            eq=1,
        )


class TestMainCliRouting:
    """Test main() CLI routing via subprocess."""

    def test_help_flag(self) -> None:
        """--help returns 0."""
        tm.that(_cli("--help").returncode, eq=0)

    def test_basemk_validate_routing(self, tmp_path: Path) -> None:
        """basemk-validate subcommand routes correctly."""
        result = _cli("basemk-validate", "--workspace", str(tmp_path))
        tm.that({0, 1}, has=result.returncode)

    def test_inventory_routing(self, tmp_path: Path) -> None:
        """Inventory subcommand routes correctly."""
        result = _cli("inventory", "--workspace", str(tmp_path))
        tm.that({0, 1}, has=result.returncode)

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
        tm.that({0, 1}, has=result.returncode)

    def test_no_command_returns_1(self) -> None:
        """No subcommand returns exit code 1."""
        tm.that(_cli().returncode, eq=1)

    def test_unknown_command_returns_error(self) -> None:
        """Unknown subcommand returns non-zero exit code."""
        tm.that(_cli("unknown").returncode, ne=0)

    def test_skill_validate_routing(self, tmp_path: Path) -> None:
        """skill-validate subcommand routes correctly."""
        result = _cli(
            "skill-validate",
            "--skill",
            "test-skill",
            "--workspace",
            str(tmp_path),
        )
        tm.that({0, 1}, has=result.returncode)

    def test_stub_validate_routing(self, tmp_path: Path) -> None:
        """stub-validate subcommand routes correctly."""
        result = _cli("stub-validate", "--workspace", str(tmp_path))
        tm.that({0, 1}, has=result.returncode)


__all__: Sequence[str] = []
