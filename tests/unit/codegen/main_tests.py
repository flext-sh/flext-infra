"""Tests for the centralized codegen CLI group.

Validates CLI argument parsing, command dispatch, and exit codes
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import p, r
from flext_infra import FlextInfraCodegenLazyInit, main as infra_main
from tests import t, u


class TestHandleLazyInit:
    """Tests for direct lazy-init command dispatch."""

    def test_success(self, tmp_path: Path) -> None:
        """lazy-init returns 0 on empty workspace."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=0)

    def test_check_mode(self, tmp_path: Path) -> None:
        """lazy-init respects --check flag."""
        result = infra_main([
            "codegen",
            "lazy-init",
            "--check",
            "--workspace",
            str(tmp_path),
        ])
        tm.that(result, eq=0)

    def test_enforce_mode(self, tmp_path: Path) -> None:
        """lazy-init in enforce mode (not check)."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(result, eq=0)

    def test_returns_non_zero_when_generation_reports_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """lazy-init fails when the generator reports errors."""

        def _fail_execute(_params) -> p.Result[bool]:
            return r[bool].fail("lazy-init failed")

        monkeypatch.setattr(
            FlextInfraCodegenLazyInit,
            "execute_command",
            staticmethod(_fail_execute),
        )
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

    def test_lazy_init_default_root(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """main() lazy-init uses cwd as default root."""
        monkeypatch.chdir(tmp_path)
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

    def test_entry_point_returns_int(self, tmp_path: Path) -> None:
        """main() returns an integer exit code."""
        result = infra_main(["codegen", "lazy-init", "--workspace", str(tmp_path)])
        tm.that(type(result).__name__, eq="int")

    def test_entry_point_via_sys_exit(self) -> None:
        """The root process entrypoint works via subprocess."""
        result = u.Cli.run_raw(
            [sys.executable, "-m", "flext_infra", "codegen", "lazy-init", "--help"],
        )
        tm.ok(result)
        tm.that(result.value.exit_code, eq=0)
        tm.that(result.value.stdout, contains="lazy-init")


__all__: t.StrSequence = []
