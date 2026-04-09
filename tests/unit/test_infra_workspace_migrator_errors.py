"""Tests for FlextInfraProjectMigrator — write/read failure scenarios.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import m as im, t, u


def _setup_basic(tmp_path: Path) -> tuple[Path, im.Infra.ProjectInfo]:
    root = tmp_path / "project-a"
    root.mkdir(parents=True)
    (root / ".git").mkdir()
    (root / "base.mk").write_text("base", encoding="utf-8")
    (root / "Makefile").write_text("content", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (root / ".gitignore").write_text("", encoding="utf-8")
    return root, u.Infra.Tests.create_migrator_project(root)


class TestMigratorWriteFailures:
    def test_gitignore_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _root, proj = _setup_basic(tmp_path)
        migrator = u.Infra.Tests.build_project_migrator(
            proj,
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )
        original_write = Path.write_text

        def _selective_write(self: Path, data: str, **kwargs: str | None) -> int:
            if self.name == ".gitignore":
                msg = "Write failed"
                raise OSError(msg)
            return original_write(self, data, **kwargs)

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("Write failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_basemk_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = tmp_path / "project-a"
        root.mkdir(parents=True)
        (root / ".git").mkdir()
        (root / "base.mk").write_text("old", encoding="utf-8")
        (root / "Makefile").write_text("content", encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (root / ".gitignore").write_text("", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "new content",
            workspace_root=tmp_path,
            dry_run=False,
        )

        def _write_fail(_self: Path, _data: str, **_kw: t.Scalar) -> int:
            msg = "Write failed"
            raise OSError(msg)

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("Write failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_makefile_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = tmp_path / "project-a"
        root.mkdir(parents=True)
        u.Infra.Tests.write_migrator_project(root)
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )
        original_write = Path.write_text

        def _selective_write(self: Path, data: str, **kwargs: str | None) -> int:
            if "Makefile" in str(self):
                msg = "Makefile write failed"
                raise OSError(msg)
            return original_write(self, data, **kwargs)

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("Makefile write failed" in err for err in migration[0].errors),
            eq=True,
        )

    def test_pyproject_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _root, proj = _setup_basic(tmp_path)
        migrator = u.Infra.Tests.build_project_migrator(
            proj,
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )
        original_write = Path.write_text

        def _selective_write(self: Path, data: str, **kwargs: str | None) -> int:
            if "pyproject.toml" in str(self):
                msg = "pyproject write failed"
                raise OSError(msg)
            return original_write(self, data, **kwargs)

        result = migrator.execute()
        migration = tm.ok(result)
        tm.that(
            any("pyproject write failed" in err for err in migration[0].errors),
            eq=True,
        )


class TestMigratorReadFailures:
    def test_gitignore_read_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = tmp_path / "project-a"
        root.mkdir(parents=True)
        (root / ".git").mkdir()
        (root / "base.mk").write_text("base", encoding="utf-8")
        (root / "Makefile").write_text("content", encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (root / ".gitignore").write_text("existing", encoding="utf-8")
        migrator = u.Infra.Tests.build_project_migrator(
            u.Infra.Tests.create_migrator_project(root),
            "base",
            workspace_root=tmp_path,
            dry_run=False,
        )
        original_read = Path.read_text

        def _selective_read(self: Path, **kwargs: str | None) -> str:
            if ".gitignore" in str(self):
                msg = ".gitignore read failed"
                raise OSError(msg)
            return original_read(self, **kwargs)

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
            workspace=tmp_path, dry_run=False, apply=True
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
        root = tmp_path / "project-a"
        root.mkdir(parents=True)
        (root / ".git").mkdir()
        (root / "base.mk").write_text("base.mk", encoding="utf-8")
        (root / "Makefile").write_text("content", encoding="utf-8")
        (root / "pyproject.toml").write_text("invalid toml {", encoding="utf-8")
        (root / ".gitignore").write_text("", encoding="utf-8")
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
