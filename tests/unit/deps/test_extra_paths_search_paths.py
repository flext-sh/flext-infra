"""Search-path contract tests for the dependency modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from tests import c, tm
from tests.unit.deps.extra_paths_support import TestsFlextInfraExtraPathsSupport

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraExtraPathsSearchPaths:
    """Tests for ``FlextInfraExtraPathsSearchPaths``."""

    @staticmethod
    def test_pyrefly_search_paths_include_declared_generated_roots(
        tmp_path: Path,
    ) -> None:
        """Test pyrefly search paths include declared generated roots."""
        manager = FlextInfraExtraPathsManager(
            repository_root=tmp_path,
            generated_python_roots=("src", "tests"),
        )

        result = manager.pyrefly_search_paths(project_dir=tmp_path)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(
                tmp_path, manager.generated_python_roots
            ),
        )

    @staticmethod
    def test_included_scripts_root_obeys_declared_search_paths(tmp_path: Path) -> None:
        """Analysis inclusion does not introduce an undeclared import identity."""
        (tmp_path / "src").mkdir()
        scripts = tmp_path / "scripts" / "lib"
        scripts.mkdir(parents=True)
        (scripts / "workspace_command.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path)
        includes = manager.pyrefly_project_includes(project_dir=tmp_path, is_root=True)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(tmp_path),
        )
        tm.that(
            "scripts/**/*.py*" in includes,
            eq="scripts" in config.Infra.tooling.tools.pyrefly.path_rules.env_dirs,
        )

    """Verify productive, existing Pyrefly search roots."""

    @staticmethod
    def test_pyrefly_search_paths_only_use_local_project_dirs(
        tmp_path: Path,
    ) -> None:
        """Keep project-local roots when dependencies are development-only."""
        consumer = tmp_path / "flext-core"
        consumer.mkdir()
        (consumer / c.GIT_DIR_NAME).mkdir()
        (consumer / "src").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        (consumer / c.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                "name = 'flext-core'\n"
                "[project.optional-dependencies]\n"
                "dev = ['flext-infra', 'flext-tests']\n"
            ),
            encoding="utf-8",
        )
        for dep_name, package_name in (
            ("flext-infra", "flext_infra"),
            ("flext-tests", "flext_tests"),
        ):
            dep_root = tmp_path / dep_name
            dep_root.mkdir()
            (dep_root / c.GIT_DIR_NAME).mkdir()
            (dep_root / "Makefile").write_text("", encoding="utf-8")
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_root / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname = '{dep_name}'\n",
                encoding="utf-8",
            )
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(consumer),
        )

    @staticmethod
    def test_pyrefly_search_paths_include_project_root_for_tests_package(
        tmp_path: Path,
    ) -> None:
        """Importable tests retain only the configured import identities."""
        consumer = tmp_path / "flext-infra"
        consumer.mkdir()
        (consumer / c.GIT_DIR_NAME).mkdir()
        (consumer / "src").mkdir()
        (consumer / "tests").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        (consumer / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'flext-infra'\n",
            encoding="utf-8",
        )
        (consumer / "tests" / "__init__.py").write_text("", encoding="utf-8")

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(consumer),
        )

    @staticmethod
    def test_pyrefly_search_paths_ignore_non_path_dependencies_at_root(
        tmp_path: Path,
    ) -> None:
        """Ignore undeclared local roots for ordinary dependencies."""
        _ = TestsFlextInfraExtraPathsSupport.workspace_with_dependency(
            tmp_path,
            uv_workspace=False,
        )

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(tmp_path),
        )

    @staticmethod
    def test_pyrefly_search_paths_omit_workspace_dependency_src_dirs_at_root(
        tmp_path: Path,
    ) -> None:
        """Keep declared workspace projects out of the root's search path."""
        (tmp_path / c.GIT_DIR_NAME).mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                "name = 'flext'\n"
                "dependencies = ['flext-core', 'flext-tests']\n"
                "[tool.uv.workspace]\n"
                "members = ['flext-core', 'flext-tests']\n"
            ),
            encoding="utf-8",
        )
        for dep_name, package_name in (
            ("flext-core", "flext_core"),
            ("flext-tests", "flext_tests"),
        ):
            dep_root = tmp_path / dep_name
            dep_root.mkdir()
            (dep_root / c.GIT_DIR_NAME).mkdir()
            (dep_root / "Makefile").write_text("", encoding="utf-8")
            (dep_root / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname = '{dep_name}'\n",
                encoding="utf-8",
            )
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(tmp_path),
        )

    @staticmethod
    def test_pyrefly_search_paths_exclude_dependency_dirs_at_root(
        tmp_path: Path,
    ) -> None:
        """Exclude every dependency directory, environments included."""
        _, dep_root = TestsFlextInfraExtraPathsSupport.workspace_with_dependency(
            tmp_path,
        )
        dep_venv = dep_root / "venv" / "bin"
        dep_venv.mkdir(parents=True)
        (dep_venv / "python").write_text("", encoding="utf-8")

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(tmp_path),
        )
