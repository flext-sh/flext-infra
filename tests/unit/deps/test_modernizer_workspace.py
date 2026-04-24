"""Workspace/parser helper tests for deps modernizer."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import main
from tests import c, u


class TestsFlextInfraDepsModernizerWorkspace:
    """Validate helper behavior through public utilities and entrypoints."""

    @pytest.mark.parametrize(
        ("content", "exists", "expected"),
        [
            pytest.param('key = "value"\n', True, True, id="valid"),
            pytest.param("invalid toml content [[[", True, False, id="invalid"),
            pytest.param("", False, False, id="missing"),
        ],
    )
    def test_toml_read_handles_public_file_cases(
        self,
        tmp_path: Path,
        content: str,
        exists: bool,
        expected: bool,
    ) -> None:
        toml_file = tmp_path / "test.toml"
        if exists:
            toml_file.write_text(content, encoding="utf-8")
        result = u.Cli.toml_read(toml_file)
        tm.that(result is not None, eq=expected)

    def test_workspace_root_returns_explicit_path(self, tmp_path: Path) -> None:
        explicit = tmp_path / "explicit"
        explicit.mkdir()
        result = u.Infra.resolve_workspace_root_or_cwd(explicit)
        tm.that(str(result), eq=str(explicit.resolve()))

    def test_workspace_root_fallback_returns_non_empty_path(
        self,
        tmp_path: Path,
    ) -> None:
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True, exist_ok=True)
        result = u.Infra.resolve_workspace_root_or_cwd(deep_path)
        tm.that(str(result), ne="")

    def test_main_applies_only_selected_projects(
        self,
        modernizer_workspace_with_projects: Path,
    ) -> None:
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.Infra.PYPROJECT_FILENAME
        )
        ignored_pyproject = (
            modernizer_workspace_with_projects / "ignored" / c.Infra.PYPROJECT_FILENAME
        )
        tm.that(
            main(
                [
                    "deps",
                    "modernize",
                    "--workspace",
                    str(modernizer_workspace_with_projects),
                    "--apply",
                    "--skip-check",
                    "--projects",
                    "selected",
                ],
            ),
            eq=0,
        )
        tm.that(
            selected_pyproject.read_text(encoding="utf-8"),
            has='build-backend = "hatchling.build"',
        )
        tm.that(
            ignored_pyproject.read_text(encoding="utf-8"),
            has='name = "ignored"',
        )
