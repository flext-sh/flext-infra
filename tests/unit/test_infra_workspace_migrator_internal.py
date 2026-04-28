"""Public-behavior tests for FlextInfraProjectMigrator."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests.utilities import TestsFlextInfraUtilities as u


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
        return u.Tests.create_migrator_dir_layout(
            tmp_path,
            name=name,
            base_mk="base",
            makefile=makefile,
            pyproject=pyproject,
            gitignore=gitignore,
        )

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

        migration = tm.ok(migrator.execute())[0]

        tm.that(
            any(
                "[DRY-RUN] Makefile not found" in change for change in migration.changes
            ),
            eq=True,
        )

    def test_execute_surfaces_makefile_read_error(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = self._write_project_files(tmp_path, makefile=None)
        (project_root / "Makefile").mkdir()
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(any("Makefile read failed" in err for err in migration.errors), eq=True)

    def test_execute_tolerates_missing_makefile_non_dry_run(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = self._write_project_files(
            tmp_path,
            makefile=None,
            pyproject='[project]\ndependencies = ["flext-core"]\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(len(migration.errors), eq=0)
        tm.that(migration.changes, has="no changes needed")

    def test_execute_surfaces_pyproject_write_error(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = self._write_project_files(
            tmp_path,
            pyproject="[tool.poetry]\n",
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        self._make_read_only(project_root / "pyproject.toml")
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(
            any("TOML write error" in err for err in migration.errors),
            eq=True,
        )

    def test_execute_skips_flext_core_dependency_changes(self, tmp_path: Path) -> None:
        project_root = self._write_project_files(
            tmp_path,
            name="flext-core",
            pyproject='[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, "flext-core"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(len(migration.errors), eq=0)
        tm.that(
            any("flext-core dependency" in change for change in migration.changes),
            eq=False,
        )

    def test_invalid_workspace(self) -> None:
        migrator = FlextInfraProjectMigrator(
            workspace=Path("/nonexistent"),
            dry_run=False,
            apply_changes=True,
        )

        result = migrator.execute()

        tm.fail(result, has="workspace root does not exist")
