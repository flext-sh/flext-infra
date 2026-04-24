"""Public-behavior tests for FlextInfraProjectMigrator."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import u


class TestsFlextInfraInfraWorkspaceMigratorInternal:
    @staticmethod
    def _write_project_files(
        project_root: Path,
        *,
        base_mk: str = "base",
        makefile: str | None = "include base.mk\n",
        pyproject: str = "[project]\n",
        gitignore: str = "",
    ) -> None:
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / ".git").mkdir(exist_ok=True)
        (project_root / "base.mk").write_text(base_mk, encoding="utf-8")
        if makefile is not None:
            (project_root / "Makefile").write_text(makefile, encoding="utf-8")
        (project_root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        (project_root / ".gitignore").write_text(gitignore, encoding="utf-8")

    @staticmethod
    def _make_read_only(path: Path) -> None:
        path.chmod(0o444)

    def test_execute_reports_missing_makefile_in_dry_run(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project-a"
        self._write_project_files(project_root, makefile=None)
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, "test-proj"),
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
        project_root = tmp_path / "project-a"
        self._write_project_files(project_root, makefile=None)
        (project_root / "Makefile").mkdir()
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(any("Makefile read failed" in err for err in migration.errors), eq=True)

    def test_execute_tolerates_missing_makefile_non_dry_run(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = tmp_path / "project-a"
        self._write_project_files(
            project_root,
            makefile=None,
            pyproject='[project]\ndependencies = ["flext-core"]\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root),
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
        project_root = tmp_path / "project-a"
        self._write_project_files(
            project_root,
            pyproject="[tool.poetry]\n",
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        self._make_read_only(project_root / "pyproject.toml")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, "test-proj"),
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
        project_root = tmp_path / "flext-core"
        self._write_project_files(
            project_root,
            pyproject='[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, "flext-core"),
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
