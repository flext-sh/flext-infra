from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests.unit.deps._extra_paths_support import ExtraPathsTestSupport

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraExtraPathsSearchPaths:
    def test_pyrefly_search_paths_only_use_local_project_dirs(
        self, tmp_path: Path
    ) -> None:
        consumer = tmp_path / "flext-core"
        consumer.mkdir()
        (consumer / ".git").mkdir()
        (consumer / "src").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        (consumer / "pyproject.toml").write_text(
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
            (dep_root / ".git").mkdir()
            (dep_root / "Makefile").write_text("", encoding="utf-8")
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_root / "pyproject.toml").write_text(
                f"[project]\nname = '{dep_name}'\n", encoding="utf-8"
            )
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = ExtraPathsTestSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer, is_root=False)

        tm.that(result, eq=["src"])

    def test_pyrefly_search_paths_include_project_root_for_tests_package(
        self, tmp_path: Path
    ) -> None:
        consumer = tmp_path / "flext-infra"
        consumer.mkdir()
        (consumer / ".git").mkdir()
        (consumer / "src").mkdir()
        (consumer / "tests").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        (consumer / "pyproject.toml").write_text(
            "[project]\nname = 'flext-infra'\n", encoding="utf-8"
        )
        (consumer / "tests" / "__init__.py").write_text("", encoding="utf-8")

        manager = ExtraPathsTestSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer, is_root=False)

        tm.that(result, eq=[".", "src"])

    def test_pyrefly_search_paths_ignore_non_path_dependencies_at_root(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "pyproject.toml").write_text(
            ("[project]\nname = 'flext'\ndependencies = ['flext-core']\n"),
            encoding="utf-8",
        )
        dep_root = tmp_path / "flext-core"
        dep_root.mkdir()
        (dep_root / ".git").mkdir()
        (dep_root / "Makefile").write_text("", encoding="utf-8")
        (dep_root / "pyproject.toml").write_text(
            "[project]\nname = 'flext-core'\n", encoding="utf-8"
        )
        (dep_root / "src" / "flext_core").mkdir(parents=True)
        (dep_root / "src" / "flext_core" / "__init__.py").write_text(
            "", encoding="utf-8"
        )

        manager = ExtraPathsTestSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path, is_root=True)

        tm.that(result, eq=["src"])

    def test_pyrefly_search_paths_include_workspace_dependency_src_dirs_at_root(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
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
            (dep_root / ".git").mkdir()
            (dep_root / "Makefile").write_text("", encoding="utf-8")
            (dep_root / "pyproject.toml").write_text(
                f"[project]\nname = '{dep_name}'\n", encoding="utf-8"
            )
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = ExtraPathsTestSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path, is_root=True)

        tm.that(result, eq=[".", "flext-core/src", "flext-tests/src", "src"])

    def test_pyrefly_search_paths_exclude_dependency_venv_dirs_at_root(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "pyproject.toml").write_text(
            (
                "[project]\n"
                "name = 'flext'\n"
                "dependencies = ['flext-core']\n"
                "[tool.uv.workspace]\n"
                "members = ['flext-core']\n"
            ),
            encoding="utf-8",
        )
        dep_root = tmp_path / "flext-core"
        dep_root.mkdir()
        (dep_root / ".git").mkdir()
        (dep_root / "Makefile").write_text("", encoding="utf-8")
        (dep_root / "pyproject.toml").write_text(
            "[project]\nname = 'flext-core'\n", encoding="utf-8"
        )
        dep_src = dep_root / "src" / "flext_core"
        dep_src.mkdir(parents=True)
        (dep_src / "__init__.py").write_text("", encoding="utf-8")
        dep_venv = dep_root / "venv" / "bin"
        dep_venv.mkdir(parents=True)
        (dep_venv / "python").write_text("", encoding="utf-8")

        manager = ExtraPathsTestSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path, is_root=True)

        tm.that(result, eq=["flext-core/src", "src"])
