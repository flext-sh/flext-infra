"""Test extra paths manager behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import tm, u
from tests.unit.deps.extra_paths_support import TestsFlextInfraExtraPathsSupport

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraExtraPathsManager:
    """Test flext infra extra paths manager behavior."""

    @staticmethod
    def test_pyrefly_includes_skip_empty_declared_directory(
        tmp_path: Path,
    ) -> None:
        """An existing empty env_dir is not reintroduced after conform removes it."""
        project = u.Tests.mk_project(tmp_path, "demo")
        (project / "src" / "demo").mkdir(parents=True)
        (project / "src" / "demo" / "__init__.py").write_text("", encoding="utf-8")
        (project / "tests").mkdir()
        (project / "tests" / "test_demo.py").write_text("", encoding="utf-8")
        (project / "examples").mkdir()

        includes = TestsFlextInfraExtraPathsSupport.manager(
            project,
        ).pyrefly_project_includes(
            project_dir=project,
            is_root=False,
        )

        tm.that(includes, eq=["src/**/*.py*", "tests/**/*.py*"])

    @staticmethod
    def test_base_constants() -> None:
        """Verify base constants."""
        manager = TestsFlextInfraExtraPathsSupport.manager()
        tm.ok(manager.root.is_absolute())
