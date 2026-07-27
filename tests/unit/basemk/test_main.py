"""Public CLI tests for the basemk command group."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flext_tests import tm

from flext_infra import main as infra_main


def basemk_main(argv: list[str]) -> int:
    return infra_main(["basemk", *argv])


class TestsFlextInfraBasemkMain:
    """Behavior contract for test_main."""

    def test_basemk_main_without_command_returns_failure(self) -> None:
        tm.that(basemk_main([]), eq=1)

    def test_basemk_main_with_generate_command_succeeds(self) -> None:
        tm.that(basemk_main(["generate"]), eq=0)

    def test_basemk_main_with_output_file_writes_content(self, tmp_path: Path) -> None:
        output_file = tmp_path / "base.mk"

        tm.that(basemk_main(["generate", "--output", str(output_file)]), eq=0)
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8")

    def test_basemk_main_with_relative_output_writes_raw_content(self) -> None:
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
            tm.that(generated, has="$(if $(wildcard $(VENV_PYTHON))")

    def test_basemk_main_with_project_name_overrides_output(
        self, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "base.mk"

        assert (
            basemk_main([
                "generate",
                "--project-name",
                "my-project",
                "--output",
                str(output_file),
            ])
            == 0
        )
        tm.that(
            output_file.read_text(encoding="utf-8"), has="PROJECT_NAME ?= my-project"
        )

    def test_basemk_main_with_invalid_command_returns_usage_error(self) -> None:
        tm.that(basemk_main(["invalid"]), eq=2)

    def test_basemk_main_accepts_shared_apply_flag(self) -> None:
        tm.that(basemk_main(["--apply", "generate"]), eq=0)

    def test_basemk_main_help_returns_success(self) -> None:
        tm.that(basemk_main(["--help"]), eq=0)

    def test_basemk_main_with_blocked_output_path_fails(self, tmp_path: Path) -> None:
        blocked_parent = tmp_path / "blocked"
        blocked_parent.write_text("occupied", encoding="utf-8")

        assert (
            basemk_main(["generate", "--output", str(blocked_parent / "base.mk")]) == 1
        )
