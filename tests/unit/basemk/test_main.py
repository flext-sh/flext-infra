"""Public CLI tests for the basemk command group."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flext_infra import main as infra_main
from flext_tests import tm


def basemk_main(argv: list[str]) -> int:
    """Run the public basemk command group with the supplied arguments."""
    return infra_main(["basemk", *argv])


class TestsFlextInfraBasemkMain:
    """Behavior contract for test_main."""

    def test_basemk_main_without_command_returns_failure(self) -> None:
        """Return the command-group failure status when no subcommand is supplied."""
        tm.that(basemk_main([]), eq=1)

    def test_basemk_main_with_generate_command_succeeds(self) -> None:
        """Generate base Make content successfully through the default CLI route."""
        tm.that(basemk_main(["generate"]), eq=0)

    def test_basemk_main_with_output_file_writes_content(self, tmp_path: Path) -> None:
        """Write nonempty generated Make content to an explicit output path."""
        output_file = tmp_path / "base.mk"

        tm.that(basemk_main(["generate", "--output", str(output_file)]), eq=0)
        tm.that(output_file.exists(), eq=True)
        tm.that(output_file.read_text(encoding="utf-8"), empty=False)

    def test_basemk_main_with_relative_output_writes_raw_content(self) -> None:
        """Resolve a repository-relative output without changing generated content."""
        workspace_root = Path.cwd()
        with tempfile.TemporaryDirectory(dir=workspace_root) as temp_dir:
            output_file = Path(temp_dir) / "nested" / "base.mk"
            relative_output = output_file.relative_to(workspace_root)

            exit_code = basemk_main([
                "generate",
                "--project-name",
                "ai-hub",
                "--output",
                str(relative_output),
            ])

            tm.that(exit_code, eq=0)
            generated = output_file.read_text(encoding="utf-8")
            tm.that(generated, has="PROJECT_NAME ?= ai-hub")
            tm.that(
                generated,
                has='PROJECT_INFRA_ROOT := test -x "$(FLEXT_INFRA_PYTHON)"',
                lacks="$(if $(wildcard $(VENV_PYTHON))",
            )

    def test_basemk_main_with_project_name_overrides_output(
        self, tmp_path: Path
    ) -> None:
        """Render the requested project name into the generated Make surface."""
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
        """Return the CLI usage status for an unknown basemk subcommand."""
        tm.that(basemk_main(["invalid"]), eq=2)

    def test_basemk_main_accepts_shared_apply_flag(self) -> None:
        """Accept the shared apply flag without changing generate semantics."""
        tm.that(basemk_main(["--apply", "generate"]), eq=0)

    def test_basemk_main_help_returns_success(self) -> None:
        """Render basemk help through the public CLI with a successful status."""
        tm.that(basemk_main(["--help"]), eq=0)

    def test_basemk_main_with_blocked_output_path_fails(self, tmp_path: Path) -> None:
        """Return failure when the requested output parent cannot be a directory."""
        blocked_parent = tmp_path / "blocked"
        blocked_parent.write_text("occupied", encoding="utf-8")

        tm.that(
            basemk_main(["generate", "--output", str(blocked_parent / "base.mk")]), eq=1
        )
