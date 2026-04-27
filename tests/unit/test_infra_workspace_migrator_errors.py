"""Tests for workspace migrator failure handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import t, u


class TestsFlextInfraInfraWorkspaceMigratorErrors:
    @staticmethod
    def _make_read_only(path: Path) -> None:
        path.chmod(0o444)

    @pytest.mark.parametrize(
        ("base_mk", "read_only_name", "new_base_mk", "expected_error"),
        [
            ("base", ".gitignore", "base", ".gitignore update failed"),
            ("old", "base.mk", "new content", "base.mk update failed"),
        ],
    )
    def test_write_failure(
        self,
        tmp_path: Path,
        base_mk: str,
        read_only_name: str,
        new_base_mk: str,
        expected_error: str,
    ) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(tmp_path, base_mk=base_mk)
        self._make_read_only(root / read_only_name)
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            new_base_mk,
            workspace_root=tmp_path,
            dry_run=False,
        )

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(expected_error in err for err in migration[0].errors),
            eq=True,
        )

    def test_makefile_write_failure(self, tmp_path: Path) -> None:
        root = tmp_path / "project-a"
        root.mkdir(parents=True)
        u.Infra.Tests.write_migrator_project(root)
        self._make_read_only(root / "Makefile")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("Makefile update failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_gitignore_read_failure(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, base_mk="base", gitignore=None
        )
        (root / ".gitignore").mkdir()
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any(".gitignore read failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_basemk_generation_failure(self, tmp_path: Path) -> None:
        root = tmp_path
        (root / ".git").mkdir(parents=True, exist_ok=True)
        (root / "Makefile").write_text("content", encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (root / ".gitignore").write_text("", encoding="utf-8")
        proj = u.Infra.Tests.create_migrator_project(root, "workspace-root")
        migrator = FlextInfraProjectMigrator(
            workspace=tmp_path, dry_run=False, apply_changes=True
        )
        migrator.discovery = u.Infra.Tests.create_migrator_discovery([proj])
        migrator.generator = u.Infra.Tests.create_migrator_generator(
            fail="Generation failed"
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("Generation failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_pyproject_parse_failure(self, tmp_path: Path) -> None:
        root = u.Infra.Tests.create_migrator_dir_layout(
            tmp_path, pyproject="invalid toml {"
        )
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base.mk",
            workspace_root=tmp_path,
            dry_run=False,
        )
        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("parse failed" in err for err in migration[0].errors),
            eq=True,
        )


__all__: t.StrSequence = []
