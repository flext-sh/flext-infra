"""Tests for the centralized codegen CLI group.

Validates CLI argument parsing, command dispatch, and exit codes
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import main as infra_main
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestHandleLazyInit:
    """Tests for direct init command dispatch."""

    def test_success(self, real_git_repo: Path) -> None:
        """Init returns 0 on empty workspace."""
        result = infra_main(["codegen", "init", "--workspace", str(real_git_repo)])
        tm.that(result, eq=0)

    def test_check_mode(self, real_git_repo: Path) -> None:
        """Init respects --check flag."""
        result = infra_main([
            "codegen",
            "init",
            "--check",
            "--workspace",
            str(real_git_repo),
        ])
        tm.that(result, eq=0)

    def test_enforce_mode(self, real_git_repo: Path) -> None:
        """Init in enforce mode (not check)."""
        result = infra_main(["codegen", "init", "--workspace", str(real_git_repo)])
        tm.that(result, eq=0)


class TestMainCommandDispatch:
    """Tests for main() command routing."""

    def test_init_command(self, real_git_repo: Path) -> None:
        """main() with init command returns 0."""
        result = infra_main(["codegen", "init", "--workspace", str(real_git_repo)])
        tm.that(result, eq=0)

    def test_init_with_check_flag(self, real_git_repo: Path) -> None:
        """main() init with --check flag parses correctly."""
        result = infra_main([
            "codegen",
            "init",
            "--check",
            "--workspace",
            str(real_git_repo),
        ])
        tm.that(result, eq=0)

    def test_unknown_command(self) -> None:
        """main() with unknown command returns non-zero exit code."""
        result = infra_main(["codegen", "unknown-command"])
        tm.that(result, ne=0)

    def test_no_command(self) -> None:
        """main() with no command returns non-zero exit code."""
        result = infra_main(["codegen"])
        tm.that(result, ne=0)

    def test_init_with_custom_root(self, real_git_repo: Path) -> None:
        """main() init with custom root directory."""
        custom_root = real_git_repo / "custom"
        custom_root.mkdir()
        result = infra_main(["codegen", "init", "--workspace", str(custom_root)])
        tm.that(result, eq=0)


class TestMainEntryPoint:
    """Tests for the centralized process entrypoint."""

    def test_entry_point_returns_int(self, real_git_repo: Path) -> None:
        """main() returns an integer exit code."""
        result = infra_main(["codegen", "init", "--workspace", str(real_git_repo)])
        tm.that(type(result).__name__, eq="int")

    def test_entry_point_via_sys_exit(self) -> None:
        """The root process entrypoint works via subprocess."""
        result = u.Cli.run_raw([
            sys.executable,
            "-m",
            "flext_infra",
            "codegen",
            "init",
            "--help",
        ])
        tm.ok(result)
        tm.that(result.value.exit_code, eq=0)
        tm.that(result.value.stdout, contains="Generate/refresh PEP 562 lazy-import")

    def test_unknown_command_surfaces_root_cause_via_subprocess(self) -> None:
        """Unknown codegen subcommands must print the actual CLI failure."""
        result = u.Cli.run_raw([
            sys.executable,
            "-m",
            "flext_infra",
            "codegen",
            "unknown-command",
        ])

        tm.ok(result)
        tm.that(result.value.exit_code, eq=2)
        tm.that(
            result.value.stdout + result.value.stderr,
            contains="No such command 'unknown-command'",
        )


__all__: t.StrSequence = []
