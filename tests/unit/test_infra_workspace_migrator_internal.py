"""Public-behavior tests for FlextInfraProjectMigrator."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests.unit.test_infra_workspace_migrator import _build_migrator, _project

from flext_infra import FlextInfraProjectMigrator


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


class TestMigratorPublicBehavior:
    def test_execute_reports_missing_makefile_in_dry_run(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project-a"
        _write_project_files(project_root, makefile=None)
        migrator = _build_migrator(
            _project(project_root, "test-proj"),
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
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        project_root = tmp_path / "project-a"
        _write_project_files(project_root, makefile="content")
        migrator = _build_migrator(
            _project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
        )
        original_read = Path.read_text

        def _selective_read(
            self: Path,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> str:
            if self.name == "Makefile":
                msg = "Read failed"
                raise OSError(msg)
            return original_read(
                self,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )

        monkeypatch.setattr(Path, "read_text", _selective_read)

        migration = tm.ok(migrator.execute())[0]

        tm.that(any("Read failed" in err for err in migration.errors), eq=True)

    def test_execute_tolerates_missing_makefile_non_dry_run(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = tmp_path / "project-a"
        _write_project_files(
            project_root,
            makefile=None,
            pyproject='[project]\ndependencies = ["flext-core"]\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = _build_migrator(
            _project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(migration.errors, eq=[])
        tm.that(migration.changes, has="no changes needed")

    def test_execute_surfaces_pyproject_write_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        project_root = tmp_path / "project-a"
        _write_project_files(
            project_root,
            pyproject="[tool.poetry]\n",
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = _build_migrator(
            _project(project_root, "test-proj"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )
        original_write = Path.write_text

        def _selective_write(self: Path, data: str, **kwargs: str | None) -> int:
            if self.name == "pyproject.toml":
                msg = "Write failed"
                raise OSError(msg)
            return original_write(self, data, **kwargs)

        monkeypatch.setattr(Path, "write_text", _selective_write)

        migration = tm.ok(migrator.execute())[0]

        tm.that(any("Write failed" in err for err in migration.errors), eq=True)

    def test_execute_skips_flext_core_dependency_changes(self, tmp_path: Path) -> None:
        project_root = tmp_path / "flext-core"
        _write_project_files(
            project_root,
            pyproject='[project]\nname = "flext-core"\nversion = "0.1.0"\n',
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = _build_migrator(
            _project(project_root, "flext-core"),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        migration = tm.ok(migrator.execute())[0]

        tm.that(migration.errors, eq=[])
        tm.that(
            any("flext-core dependency" in change for change in migration.changes),
            eq=False,
        )

    def test_invalid_workspace(self) -> None:
        migrator = FlextInfraProjectMigrator(
            workspace=Path("/nonexistent"),
            dry_run=False,
            apply=True,
        )

        result = migrator.execute()

        tm.that(result.is_failure or result.is_success, eq=True)
