"""Public-behavior tests for FlextInfraProjectMigrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from tests import u

from tests import m



class TestsFlextInfraInfraWorkspaceMigratorInternal:
    @staticmethod
    def _write_project_files(
        tmp_path: Path,
        *,
        name: str = "project-a",
        makefile: str | None = "include base.mk\n",
        pyproject: str = "[project]\n",
        gitignore: str = "",
    ) -> Path:
        r"""File-specific defaults for ``create_migrator_dir_layout``.

        Pinned defaults (``base_mk="base"`` and Makefile=``include base.mk\n``)
        match this module's migration scenarios; scaffold logic is centralized
        in ``u.Tests.create_migrator_dir_layout`` (no duplication).
        """
        project_dir: Path = u.Tests.create_migrator_dir_layout(
            tmp_path,
            name=name,
            base_mk="base",
            makefile=makefile,
            pyproject=pyproject,
            gitignore=gitignore,
        )
        return project_dir

    @staticmethod
    def _make_read_only(path: Path) -> None:
        path.chmod(0o444)

    def test_execute_reports_missing_makefile_in_dry_run(self, tmp_path: Path) -> None:
        project_root = self._write_project_files(tmp_path, makefile=None)
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )

        migration: m.Infra.MigrationResult = tm.ok(migrator.execute())[0]

        tm.that(
            any(
                "[DRY-RUN] Makefile not found" in change for change in migration.changes
            ),
            eq=True,
        )

    def test_execute_surfaces_makefile_read_error(self, tmp_path: Path) -> None:
        project_root = self._write_project_files(tmp_path, makefile=None)
        (project_root / "Makefile").mkdir()
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
        )

        migration: m.Infra.MigrationResult = tm.ok(migrator.execute())[0]

        tm.that(any("Makefile read failed" in err for err in migration.errors), eq=True)

    def test_execute_tolerates_missing_makefile_non_dry_run(
        self, tmp_path: Path
    ) -> None:
        project_root = self._write_project_files(
            tmp_path,
            makefile=None,
            pyproject='[project]\ndependencies = ["flext-core"]\n',
            gitignore="\n".join(c.Infra.REQUIRED_GITIGNORE_ENTRIES) + "\n",
        )
        (project_root / "src" / "flext_infra").mkdir(parents=True, exist_ok=True)
        (project_root / "src" / "flext_infra" / "__init__.py").touch()
        (project_root / c.Infra.ENVRC_FILENAME).write_text(
            c.Infra.WORKSPACE_ENVRC_CONTENT, encoding="utf-8"
        )
        (project_root / c.Infra.MISE_TOML_FILENAME).write_text(
            c.Infra.WORKSPACE_MISE_TOML_CONTENT, encoding="utf-8"
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration: m.Infra.MigrationResult = tm.ok(migrator.execute())[0]

        tm.that(len(migration.errors), eq=0)
        tm.that(migration.changes, has="no changes needed")

    def test_execute_surfaces_pyproject_write_error(self, tmp_path: Path) -> None:
        project_root = self._write_project_files(
            tmp_path,
            pyproject="[tool.poetry]\n",
            gitignore="\n".join(c.Infra.REQUIRED_GITIGNORE_ENTRIES) + "\n",
        )
        self._make_read_only(project_root / "pyproject.toml")
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration: m.Infra.MigrationResult = tm.ok(migrator.execute())[0]

        tm.that(any("TOML write" in err for err in migration.errors), eq=True)

    def test_execute_skips_flext_core_dependency_changes(self, tmp_path: Path) -> None:
        project_root = self._write_project_files(
            tmp_path,
            name="flext-core",
            pyproject='[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            gitignore="\n".join(c.Infra.REQUIRED_GITIGNORE_ENTRIES) + "\n",
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "flext-core"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration: m.Infra.MigrationResult = tm.ok(migrator.execute())[0]

        tm.that(len(migration.errors), eq=0)
        tm.that(
            any("flext-core dependency" in change for change in migration.changes),
            eq=False,
        )

    def test_invalid_workspace(self) -> None:
        migrator = FlextInfraProjectMigrator(
            workspace_root=Path("/nonexistent"), dry_run=False, apply_changes=True
        )

        result = migrator.execute()

        tm.fail(result, has="workspace root does not exist")
