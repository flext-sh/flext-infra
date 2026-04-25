from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraExtraPathsManager
from tests import t

_TEST_WORKSPACE_ROOT = Path(__file__).resolve().parent


def _manager(
    workspace_root: Path | None = None,
) -> FlextInfraExtraPathsManager:
    return FlextInfraExtraPathsManager(workspace=workspace_root or _TEST_WORKSPACE_ROOT)


class TestsFlextInfraExtraPathsManager:
    def test_manager_initialization(self) -> None:
        manager = _manager()
        tm.that(manager.__class__.__name__, eq="FlextInfraExtraPathsManager")

    def test_manager_has_required_services(self) -> None:
        _manager()

    def test_sync_one_missing_file(self, tmp_path: Path) -> None:
        tm.that(
            not _manager().sync_one(tmp_path / "nonexistent.toml").success,
            eq=True,
        )

    def test_sync_one_no_tool_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        doc["project"] = {"name": "test"}
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        result = _manager().sync_one(pyproject)
        tm.that(result.success, eq=True)
        tm.that(result.value, eq=False)

    def test_sync_one_no_pyright_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        tool = tomlkit.table()
        tool["other"] = tomlkit.table()
        doc["tool"] = tool
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        result = _manager().sync_one(pyproject)
        tm.that(result.success, eq=True)
        tm.that(result.value, eq=False)

    @pytest.mark.parametrize(
        "tool_doc",
        [
            {"pyright": {"extraPaths": ["src"]}},
            {"pyright": {"extraPaths": []}, "mypy": {"mypy_path": ["src"]}},
            {"pyright": {"extraPaths": []}, "pyrefly": {"search-path": ["."]}},
        ],
    )
    def test_sync_one_success_cases(
        self,
        tmp_path: Path,
        tool_doc: Mapping[str, t.Infra.InfraValue],
    ) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        doc["tool"] = tool_doc
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        result = _manager().sync_one(pyproject, is_root="pyrefly" not in tool_doc)
        tm.that(result.success, eq=True)

    def test_sync_one_dry_run(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        doc["tool"] = {"pyright": {"extraPaths": ["old"]}}
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        tm.ok(_manager().sync_one(pyproject, dry_run=True, is_root=True))
        tm.that(pyproject.read_text(encoding="utf-8"), contains="old")

    def test_sync_one_write_failure(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.pyright]\nextraPaths = ["old"]\n', encoding="utf-8")
        pyproject.chmod(0o444)

        tm.fail(_manager().sync_one(pyproject, is_root=True), has="TOML write error")

    def test_base_constants(self) -> None:
        manager = _manager()
        tm.that(manager.root.is_absolute(), eq=True)

    """Behavior contract for test_extra_paths_manager."""

    def test_pyrefly_search_paths_only_use_local_project_dirs(
        self,
        tmp_path: Path,
    ) -> None:
        consumer = tmp_path / "flext-core"
        consumer.mkdir()
        (consumer / ".git").mkdir()
        (consumer / "src").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        pyproject = consumer / "pyproject.toml"
        pyproject.write_text(
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
                f"[project]\nname = '{dep_name}'\n",
                encoding="utf-8",
            )
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = FlextInfraExtraPathsManager(workspace=tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer, is_root=False)

        tm.that(result, eq=["src"])

    def test_pyrefly_search_paths_include_project_root_for_tests_package(
        self,
        tmp_path: Path,
    ) -> None:
        consumer = tmp_path / "flext-infra"
        consumer.mkdir()
        (consumer / ".git").mkdir()
        (consumer / "src").mkdir()
        (consumer / "tests").mkdir()
        (consumer / "Makefile").write_text("", encoding="utf-8")
        (consumer / "pyproject.toml").write_text(
            "[project]\nname = 'flext-infra'\n",
            encoding="utf-8",
        )
        (consumer / "tests" / "__init__.py").write_text("", encoding="utf-8")

        manager = FlextInfraExtraPathsManager(workspace=tmp_path)
        result = manager.pyrefly_search_paths(project_dir=consumer, is_root=False)

        tm.that(result, eq=[".", "src"])

    def test_pyrefly_search_paths_ignore_non_path_dependencies_at_root(
        self,
        tmp_path: Path,
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
            "[project]\nname = 'flext-core'\n",
            encoding="utf-8",
        )
        (dep_root / "src" / "flext_core").mkdir(parents=True)
        (dep_root / "src" / "flext_core" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )

        manager = FlextInfraExtraPathsManager(workspace=tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path, is_root=True)

        tm.that(result, eq=["src"])

    def test_pyrefly_search_paths_include_workspace_dependency_src_dirs_at_root(
        self,
        tmp_path: Path,
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
                f"[project]\nname = '{dep_name}'\n",
                encoding="utf-8",
            )
            dep_src = dep_root / "src" / package_name
            dep_src.mkdir(parents=True)
            (dep_src / "__init__.py").write_text("", encoding="utf-8")

        manager = FlextInfraExtraPathsManager(workspace=tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path, is_root=True)

        tm.that(result, eq=[".", "flext-core/src", "flext-tests/src", "src"])
