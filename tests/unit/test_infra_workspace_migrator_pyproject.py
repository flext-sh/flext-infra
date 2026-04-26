"""Tests for FlextInfraProjectMigrator — pyproject and dry-run scenarios.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import t, u


class TestsFlextInfraInfraWorkspaceMigratorPyproject:
    def test_flext_core_skipped(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(tmp_path, name="flext-core")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root, "flext-core"),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("unchanged for flext-core" in c for c in migration[0].changes),
            eq=True,
        )

    def test_flext_core_dry_run(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, name="flext-core", base_mk="base"
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root, "flext-core"),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "unchanged for flext-core" in c
                for c in migration[0].changes
            ),
            eq=True,
        )

    def test_has_flext_core_in_poetry(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path,
            pyproject='[tool.poetry.dependencies]\nflext-core = "^0.1.0"\n',
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("already includes" in c for c in migration[0].changes),
            eq=True,
        )

    def test_poetry_table_missing(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", pyproject="[tool]\n"
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("flext-core dependency" in c for c in migration[0].changes),
            eq=True,
        )

    def test_poetry_deps_not_table(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path,
            base_mk="base",
            pyproject="[tool.poetry]\ndependencies = []\n",
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("flext-core dependency" in c for c in migration[0].changes),
            eq=True,
        )

    def test_makefile_not_found(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", makefile=None
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "Makefile not found" in c
                for c in migration[0].changes
            ),
            eq=True,
        )

    def test_pyproject_not_found(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", pyproject=None
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "pyproject.toml not found" in c
                for c in migration[0].changes
            ),
            eq=True,
        )

    def test_gitignore_already_normalized(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path,
            base_mk="base",
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and ".gitignore already normalized" in c
                for c in migration[0].changes
            ),
            eq=True,
        )

    def test_makefile_read_failure(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(tmp_path)
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=False,
        )
        tm.ok(migrator.execute())


__all__: t.StrSequence = []
