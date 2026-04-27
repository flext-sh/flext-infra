"""Tests for workspace migrator dependency behavior."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import u


class TestsFlextInfraInfraWorkspaceMigratorDeps:
    @staticmethod
    def _build_migrator(
        tmp_path: Path,
        *,
        pyproject: str,
        base_mk: str = "base",
    ) -> FlextInfraProjectMigrator:
        project_root = tmp_path / "project-a"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text(base_mk, encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator: FlextInfraProjectMigrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            base_mk,
            workspace_root=tmp_path,
            dry_run=True,
        )
        return migrator

    def test_existing_poetry_dependency_is_reported(self, tmp_path: Path) -> None:
        migrator = self._build_migrator(
            tmp_path,
            pyproject='[tool.poetry.dependencies]\nflext-core = "^0.1.0"\n',
            base_mk="base.mk",
        )
        migrations = tm.ok(migrator.execute())
        tm.that(
            any("already includes" in change for change in migrations[0].changes),
            eq=True,
        )

    def test_missing_poetry_table_adds_dependency_change(self, tmp_path: Path) -> None:
        migrator = self._build_migrator(
            tmp_path,
            pyproject="[tool]\n",
        )
        migrations = tm.ok(migrator.execute())
        tm.that(
            any("flext-core dependency" in change for change in migrations[0].changes),
            eq=True,
        )

    def test_non_mapping_poetry_dependencies_add_dependency_change(
        self,
        tmp_path: Path,
    ) -> None:
        migrator = self._build_migrator(
            tmp_path,
            pyproject="[tool.poetry]\ndependencies = []\n",
        )
        migrations = tm.ok(migrator.execute())
        tm.that(
            any("flext-core dependency" in change for change in migrations[0].changes),
            eq=True,
        )
