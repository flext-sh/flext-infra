"""Public tests for docs-related write helpers."""

from __future__ import annotations

from pathlib import Path

from tests import m, u


def test_json_write_round_trips_dict_payload(tmp_path: Path) -> None:
    json_file = tmp_path / "nested/data.json"

    result = u.Cli.json_write(json_file, {"key": "value", "number": 42})
    read_result = u.Cli.json_read(json_file)

    assert result.success
    assert read_result.success
    assert read_result.unwrap() == {"key": "value", "number": 42}


def test_json_write_accepts_pydantic_model(tmp_path: Path) -> None:
    json_file = tmp_path / "report.json"
    report = m.Infra.DocsPhaseReport(
        phase="audit",
        scope="root",
        items=[],
        checks=[],
        strict=False,
        passed=True,
    )

    result = u.Cli.json_write(json_file, report)

    assert result.success
    assert json_file.exists()


def test_write_markdown_writes_exact_content(tmp_path: Path) -> None:
    md_file = tmp_path / "exact.md"
    lines = ["Line 1", "Line 2", "Line 3"]

    result = u.Infra.write_markdown(md_file, lines)

    assert result.success
    assert md_file.read_text() == "Line 1\nLine 2\nLine 3\n"


def test_write_markdown_preserves_empty_lines(tmp_path: Path) -> None:
    md_file = tmp_path / "empty-lines.md"

    result = u.Infra.write_markdown(md_file, ["# Title", "", "", "Content"])

    assert result.success
    assert md_file.read_text().count("\n") >= 3


def test_write_markdown_fails_for_non_directory_parent() -> None:
    result = u.Infra.write_markdown(Path("/dev/null/test.md"), ["test"])

    assert result.failure
    assert "markdown write error" in (result.error or "")
