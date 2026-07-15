"""Tests for the centralized codegen CLI group.

Validates CLI argument parsing, command dispatch, and exit codes
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_tests import tm

from flext_infra import main as infra_main
from tests import t, u


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

    # mro-wkii.17.26 (codex): every gRPC apply route is transaction-owned.
    def test_grpc_dry_run_validates_patch_without_writing_live_tree(
        self, real_git_repo: Path
    ) -> None:
        """Run gRPC generation through the complete worktree transaction."""
        package_root = real_git_repo / "src" / "demo_grpc"
        proto_root = package_root / "protos"
        proto_root.mkdir(parents=True)
        (real_git_repo / "pyproject.toml").write_text(
            '[project]\nname = "demo-grpc"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        package_root.joinpath("__init__.py").write_text("", encoding="utf-8")
        proto_root.joinpath("__init__.py").write_text("", encoding="utf-8")
        proto_root.joinpath("demo.proto").write_text(
            (
                'syntax = "proto3";\n'
                "package demo;\n"
                "message PingRequest {}\n"
                "message PingReply {}\n"
                "service Demo { rpc Ping(PingRequest) returns (PingReply); }\n"
            ),
            encoding="utf-8",
        )

        result = infra_main(["codegen", "grpc", "--workspace", str(real_git_repo)])

        tm.that(result, eq=0)
        tm.that(proto_root.joinpath("demo_pb2.py").exists(), eq=False)
        tm.that(proto_root.joinpath("demo_pb2_grpc.py").exists(), eq=False)


class TestMainEntryPoint:
    """Tests for the centralized process entrypoint."""

    def test_entry_point_returns_int(self, real_git_repo: Path) -> None:
        """main() returns an integer exit code."""
        result = infra_main(["codegen", "init", "--workspace", str(real_git_repo)])
        tm.that(type(result).__name__, eq="int")
        tm.that(result, eq=0)

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
        tm.that(result.value.stdout, contains="--projects")

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
