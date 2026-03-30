"""Tests for the centralized codegen CLI group.

Validates CLI argument parsing, command dispatch, and exit codes
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from flext_tests import t, tm

from flext_infra import main as infra_main
from flext_infra.codegen import cli as codegen_cli


class TestHandleLazyInit:
    """Tests for _handle_lazy_init with real service instances."""

    def test_success(self, tmp_path: Path) -> None:
        """_handle_lazy_init returns 0 on empty workspace."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=0)

    def test_check_mode(self, tmp_path: Path) -> None:
        """_handle_lazy_init respects --check flag."""
        result = infra_main([
            "codegen",
            "lazy-init",
            "--check",
            "--workspace",
            str(tmp_path),
        ])
        tm.that(result, eq=0)

    def test_enforce_mode(self, tmp_path: Path) -> None:
        """_handle_lazy_init in enforce mode (not check)."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=0)

    def test_returns_non_zero_when_generation_reports_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """_handle_lazy_init fails when the generator reports errors."""

        class _BrokenLazyInit:
            def __init__(self, workspace_root: Path) -> None:
                _ = workspace_root

            def run(self, *, check_only: bool = False) -> int:
                _ = check_only
                return 1

        monkeypatch.setattr(codegen_cli, "FlextInfraCodegenLazyInit", _BrokenLazyInit)
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=1)


class TestMainCommandDispatch:
    """Tests for main() command routing."""

    def test_lazy_init_command(self, tmp_path: Path) -> None:
        """main() with lazy-init command returns 0."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=0)

    def test_lazy_init_with_check_flag(self, tmp_path: Path) -> None:
        """main() lazy-init with --check flag parses correctly."""
        result = infra_main([
            "codegen",
            "lazy-init",
            "--check",
            "--workspace",
            str(tmp_path),
        ])
        tm.that(result, eq=0)

    def test_lazy_init_default_root(self) -> None:
        """main() lazy-init uses cwd as default root."""
        result = infra_main(["codegen", "lazy-init"])
        tm.that(result, eq=0)

    def test_unknown_command(self) -> None:
        """main() with unknown command returns non-zero exit code."""
        result = infra_main(["codegen", "unknown-command"])
        tm.that(result, ne=0)

    def test_no_command(self) -> None:
        """main() with no command returns non-zero exit code."""
        result = infra_main(["codegen"])
        tm.that(result, ne=0)

    def test_lazy_init_with_custom_root(self, tmp_path: Path) -> None:
        """main() lazy-init with custom root directory."""
        custom_root = tmp_path / "custom"
        result = infra_main(["codegen", "lazy-init", "--workspace", str(custom_root)])
        tm.that(result, eq=0)


class TestMainEntryPoint:
    """Tests for the centralized process entrypoint."""

    def test_entry_point_returns_int(self) -> None:
        """main() returns an integer exit code."""
        result = infra_main(["codegen", "lazy-init"])
        tm.that(type(result).__name__, eq="int")

    def test_entry_point_via_sys_exit(self) -> None:
        """The root process entrypoint works via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "flext_infra", "codegen", "lazy-init", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        tm.that(result.returncode, eq=0)
        tm.that(result.stdout, contains="lazy-init")


__all__: t.StrSequence = []
