"""Public CLI tests for the basemk command group.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import main as infra_main


def basemk_main(argv: list[str]) -> int:
    """Run the public base.mk CLI command.

    Args:
        argv: Arguments for the base.mk command group.

    Returns:
        The CLI exit code.
    """
    return infra_main(["basemk", *argv])


class TestsFlextInfraBasemkMain:
    """Behavior contract for test_main."""

    def test_basemk_main_without_command_returns_failure(self) -> None:
        """Return failure when no base.mk subcommand is provided."""
        tm.that(basemk_main([]), eq=1)

    def test_basemk_main_with_generate_command_succeeds(self) -> None:
        """Generate base.mk content with the default command."""
        tm.that(basemk_main(["generate"]), eq=0)

    def test_basemk_main_with_output_file_writes_content(self, tmp_path: Path) -> None:
        """Write generated base.mk content to the requested output file."""
        output_file = tmp_path / "base.mk"

        tm.that(basemk_main(["generate", "--output", str(output_file)]), eq=0)
        tm.that(output_file.exists(), eq=True)
        tm.that(output_file.read_text(encoding="utf-8"), empty=False)

    def test_basemk_main_with_project_name_overrides_output(
        self, tmp_path: Path
    ) -> None:
        """Apply an explicit project name to generated base.mk content."""
        output_file = tmp_path / "base.mk"

        tm.that(
            basemk_main([
                "generate",
                "--project-name",
                "my-project",
                "--output",
                str(output_file),
            ]),
            eq=0,
        )
        tm.that(
            output_file.read_text(encoding="utf-8"), has="PROJECT_NAME ?= my-project"
        )

    def test_basemk_main_with_invalid_command_returns_usage_error(self) -> None:
        """Return the usage exit code for an invalid base.mk command."""
        tm.that(basemk_main(["invalid"]), eq=2)

    def test_basemk_main_accepts_shared_apply_flag(self) -> None:
        """Accept the shared apply flag before the base.mk subcommand."""
        tm.that(basemk_main(["--apply", "generate"]), eq=0)

    def test_basemk_main_help_returns_success(self) -> None:
        """Return success for base.mk command help."""
        tm.that(basemk_main(["--help"]), eq=0)

    def test_basemk_main_with_blocked_output_path_fails(self, tmp_path: Path) -> None:
        """Return failure when the requested output path is blocked."""
        blocked_parent = tmp_path / "blocked"
        blocked_parent.write_text("occupied", encoding="utf-8")

        tm.that(
            basemk_main(["generate", "--output", str(blocked_parent / "base.mk")]), eq=1
        )
