"""Public CLI tests for the basemk command group."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main


def basemk_main(argv: list[str]) -> int:
    return infra_main(["basemk", *argv])


def test_basemk_main_without_command_returns_failure() -> None:
    assert basemk_main([]) == 1


def test_basemk_main_with_generate_command_succeeds() -> None:
    assert basemk_main(["generate"]) == 0


def test_basemk_main_with_output_file_writes_content(tmp_path: Path) -> None:
    output_file = tmp_path / "base.mk"

    assert basemk_main(["generate", "--output", str(output_file)]) == 0
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8")


def test_basemk_main_with_project_name_overrides_output(tmp_path: Path) -> None:
    output_file = tmp_path / "base.mk"

    assert (
        basemk_main(
            [
                "generate",
                "--project-name",
                "my-project",
                "--output",
                str(output_file),
            ],
        )
        == 0
    )
    assert "PROJECT_NAME ?= my-project" in output_file.read_text(encoding="utf-8")


def test_basemk_main_with_invalid_command_returns_usage_error() -> None:
    assert basemk_main(["invalid"]) == 2


def test_basemk_main_accepts_shared_apply_flag() -> None:
    assert basemk_main(["--apply", "generate"]) == 0


def test_basemk_main_help_returns_success() -> None:
    assert basemk_main(["--help"]) == 0


def test_basemk_main_with_blocked_output_path_fails(tmp_path: Path) -> None:
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("occupied", encoding="utf-8")

    assert basemk_main(["generate", "--output", str(blocked_parent / "base.mk")]) == 1
