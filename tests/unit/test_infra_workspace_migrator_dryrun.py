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
        project_root = tmp_path / "flext-core"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base.mk", encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, name="flext-core"),
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
        project_root = tmp_path / "project-a"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base", encoding="utf-8")
        (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root),
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
        project_root = tmp_path / "project-a"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base", encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root),
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
        project_root = tmp_path / "flext-core"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base", encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root, name="flext-core"),
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
        project_root = tmp_path / "project-a"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base", encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (project_root / ".gitignore").write_text(
            ".reports/\n.venv/\n__pycache__/\nbase.mk\n",
            encoding="utf-8",
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root),
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
        project_root = tmp_path / "project-a"
        project_root.mkdir(parents=True)
        (project_root / ".git").mkdir()
        (project_root / "base.mk").write_text("base.mk", encoding="utf-8")
        (project_root / "Makefile").write_text("content", encoding="utf-8")
        (project_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (project_root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(project_root),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=False,
        )
        result = migrator.execute()
        tm.ok(result)
