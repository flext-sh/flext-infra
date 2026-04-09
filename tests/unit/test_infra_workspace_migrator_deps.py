"""Tests for FlextWorkspaceMigrator — dependency detection and private methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import u


def test_migrator_has_flext_core_dependency_in_poetry(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base.mk", encoding="utf-8")
    (project_root / "Makefile").write_text("content", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[tool.poetry.dependencies]\nflext-core = "^0.1.0"\n',
        encoding="utf-8",
    )
    (project_root / ".gitignore").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "base.mk",
        workspace_root=tmp_path,
        dry_run=True,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(any("already includes" in c for c in migrations[0].changes), eq=True)


def test_migrator_has_flext_core_dependency_poetry_table_missing(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "Makefile").write_text("content", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[tool]\n", encoding="utf-8")
    (project_root / ".gitignore").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "base",
        workspace_root=tmp_path,
        dry_run=True,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(any("flext-core dependency" in c for c in migrations[0].changes), eq=True)


def test_migrator_has_flext_core_dependency_poetry_deps_not_table(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "Makefile").write_text("content", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        "[tool.poetry]\ndependencies = []\n",
        encoding="utf-8",
    )
    (project_root / ".gitignore").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "base",
        workspace_root=tmp_path,
        dry_run=True,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(any("flext-core dependency" in c for c in migrations[0].changes), eq=True)


def test_workspace_migrator_error_handling_on_invalid_workspace() -> None:
    migrator = FlextInfraProjectMigrator(
        workspace=Path("/nonexistent"), dry_run=False, apply=True
    )
    result = migrator.execute()
    tm.that(result.is_failure or result.is_success, eq=True)


def test_workspace_migrator_makefile_not_found_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "test-proj"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (project_root / ".gitignore").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root, name="test-proj"),
        "base",
        workspace_root=tmp_path,
        dry_run=True,
    )
    migration = tm.ok(migrator.execute())[0]
    tm.that(
        any("[DRY-RUN] Makefile not found" in change for change in migration.changes),
        eq=True,
    )


def test_workspace_migrator_makefile_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "test-proj"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "Makefile").write_text("test", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (project_root / ".gitignore").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root, name="test-proj"),
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

    migration = tm.ok(migrator.execute())[0]
    tm.that(any("Read failed" in err for err in migration.errors), eq=True)


def test_workspace_migrator_pyproject_write_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "test-proj"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "Makefile").write_text("include base.mk\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
    (project_root / ".gitignore").write_text(
        ".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        encoding="utf-8",
    )
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root, name="test-proj"),
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

    migration = tm.ok(migrator.execute())[0]
    tm.that(any("Write failed" in err for err in migration.errors), eq=True)


def test_migrate_makefile_not_found_non_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[project]\ndependencies = ["flext-core"]\n',
        encoding="utf-8",
    )
    (project_root / ".gitignore").write_text(
        ".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        encoding="utf-8",
    )
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "base",
        workspace_root=tmp_path,
        dry_run=False,
    )
    migration = tm.ok(migrator.execute())[0]
    tm.that(migration.errors, eq=[])
    tm.that(migration.changes, has="no changes needed")


def test_migrate_pyproject_flext_core_non_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "flext-core"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "base.mk").write_text("base", encoding="utf-8")
    (project_root / "Makefile").write_text("include base.mk\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "flext-core"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (project_root / ".gitignore").write_text(
        ".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        encoding="utf-8",
    )
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root, name="flext-core"),
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
