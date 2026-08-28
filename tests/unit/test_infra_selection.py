"""Repository-local project selection contracts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from tests import m, t


class TestsFlextInfraInfraSelection:
    """Prove selection never discovers or dispatches to another repository."""

    @pytest.fixture
    def repository(self, tmp_path: Path) -> Path:
        package = tmp_path / "src" / "demo_package"
        package.mkdir(parents=True)
        (package / "__init__.py").touch()
        (tmp_path / "Makefile").touch()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo-project"\ndependencies = ["flext-core"]\n',
            encoding="utf-8",
        )
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "Makefile").touch()
        (nested / "pyproject.toml").write_text(
            '[project]\nname = "nested-project"\ndependencies = ["flext-core"]\n',
            encoding="utf-8",
        )
        return tmp_path

    def test_empty_selection_returns_only_supplied_repository(
        self, repository: Path
    ) -> None:
        projects: t.SequenceOf[m.Infra.ProjectInfo] = tm.ok(
            u.Infra.resolve_projects(repository, ())
        )
        tm.that([project.name for project in projects], eq=["demo-project"])

    @pytest.mark.parametrize("selector", [".", "demo-project"])
    def test_repository_aliases_select_the_same_project(
        self, repository: Path, selector: str
    ) -> None:
        projects: t.SequenceOf[m.Infra.ProjectInfo] = tm.ok(
            u.Infra.resolve_projects(repository, (selector,))
        )
        tm.that([project.name for project in projects], eq=["demo-project"])

    def test_nested_or_unknown_selector_fails(self, repository: Path) -> None:
        tm.fail(
            u.Infra.resolve_projects(repository, ("nested-project",)),
            has="unknown projects",
        )

    def test_invalid_repository_fails(self, tmp_path: Path) -> None:
        tm.fail(u.Infra.resolve_projects(tmp_path / "missing", ()))
