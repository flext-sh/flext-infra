"""Tests for FlextWorkspaceMigrator — dry-run and skip scenarios.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestsFlextInfraInfraWorkspaceMigratorDryrun:
    """Behavior contract for test_infra_workspace_migrator_dryrun."""

    def test_migrator_flext_core_project_skipped(self, tmp_path: Path) -> None:
        project_root = u.Tests.create_migrator_dir_layout(tmp_path, name="flext-core")
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, name="flext-core"),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migrations = tm.ok(result)
        tm.that(
            any("unchanged for flext-core" in c for c in migrations[0].changes),
            eq=True,
        )

    def test_migrator_makefile_not_found_dry_run(self, tmp_path: Path) -> None:
        project_root = u.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", makefile=None
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migrations = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "Makefile not found" in c
                for c in migrations[0].changes
            ),
            eq=True,
        )

    def test_migrator_pyproject_not_found_dry_run(self, tmp_path: Path) -> None:
        project_root = u.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", pyproject=None
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migrations = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "pyproject.toml not found" in c
                for c in migrations[0].changes
            ),
            eq=True,
        )

    def test_migrator_flext_core_dry_run(self, tmp_path: Path) -> None:
        project_root = u.Tests.create_migrator_dir_layout(
            tmp_path, name="flext-core", base_mk="base"
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root, name="flext-core"),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migrations = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and "unchanged for flext-core" in c
                for c in migrations[0].changes
            ),
            eq=True,
        )

    def test_migrator_gitignore_already_normalized_dry_run(
        self, tmp_path: Path
    ) -> None:
        project_root = u.Tests.create_migrator_dir_layout(
            tmp_path,
            base_mk="base",
            gitignore=".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        )
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base",
            workspace_root=tmp_path,
            dry_run=True,
        )
        result = migrator.execute()
        migrations = tm.ok(result)
        tm.that(
            any(
                "[DRY-RUN]" in c and ".gitignore already normalized" in c
                for c in migrations[0].changes
            ),
            eq=True,
        )

    def test_migrator_makefile_read_failure(self, tmp_path: Path) -> None:
        project_root = u.Tests.create_migrator_dir_layout(tmp_path)
        migrator = u.Tests.build_project_migrator(
            u.Tests.create_migrator_project(project_root),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=False,
        )
        result = migrator.execute()
        tm.ok(result)
