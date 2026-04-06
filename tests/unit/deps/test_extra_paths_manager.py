from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm
from tests import t
from tomlkit.toml_document import TOMLDocument

from flext_core import r
from flext_infra import FlextInfraExtraPathsManager, extra_paths as deps_extra_paths


def _manager() -> FlextInfraExtraPathsManager:
    return FlextInfraExtraPathsManager()


class TestFlextInfraExtraPathsManager:
    def test_manager_initialization(self) -> None:
        manager = FlextInfraExtraPathsManager()
        tm.that(manager.__class__.__name__, eq="FlextInfraExtraPathsManager")

    def test_manager_has_required_services(self) -> None:
        manager = FlextInfraExtraPathsManager()
        tm.that(hasattr(manager, "get_dep_paths"), eq=True)
        tm.that(hasattr(manager, "sync_one"), eq=True)


class TestGetDepPaths:
    def test_get_dep_paths_empty_doc(self) -> None:
        tm.that(_manager().get_dep_paths(tomlkit.document(), is_root=False), eq=[])

    def test_get_dep_paths_with_pep621_deps(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-core @ file:../flext-core"]}
        paths = _manager().get_dep_paths(doc, is_root=False)
        tm.that(any("flext-core" in item for item in paths), eq=True)

    def test_get_dep_paths_with_poetry_deps(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        paths = _manager().get_dep_paths(doc, is_root=False)
        tm.that(any("flext-core" in item for item in paths), eq=True)

    def test_get_dep_paths_is_root_true(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        tm.that(
            all(
                not item.startswith("../")
                for item in _manager().get_dep_paths(doc, is_root=True)
            ),
            eq=True,
        )

    def test_get_dep_paths_is_root_false(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        tm.that(
            all(
                item.startswith("../")
                for item in _manager().get_dep_paths(doc, is_root=False)
            ),
            eq=True,
        )

    def test_get_dep_paths_combined_sources(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-api @ file:../flext-api"]}
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        tm.that(len(_manager().get_dep_paths(doc, is_root=False)), gte=2)

    def test_get_dep_paths_with_is_root_true(self) -> None:
        doc = tomlkit.document()
        project = tomlkit.table()
        project["dependencies"] = ["flext-core @ file:flext-core"]
        doc["project"] = project
        result = _manager().get_dep_paths(doc, is_root=True)
        tm.that(any("flext-core/src" in item for item in result), eq=True)

    def test_get_dep_paths_with_is_root_false(self) -> None:
        doc = tomlkit.document()
        project = tomlkit.table()
        project["dependencies"] = ["flext-core @ file:../flext-core"]
        doc["project"] = project
        result = _manager().get_dep_paths(doc, is_root=False)
        tm.that(any("../flext-core/src" in item for item in result), eq=True)


class TestSyncOne:
    def test_sync_one_missing_file(self, tmp_path: Path) -> None:
        tm.that(
            not _manager().sync_one(tmp_path / "nonexistent.toml").is_success,
            eq=True,
        )

    def test_sync_one_no_tool_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        doc["project"] = {"name": "test"}
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        result = _manager().sync_one(pyproject)
        tm.that(result.is_success, eq=True)
        tm.that(result.value, eq=False)

    def test_sync_one_no_pyright_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        tool = tomlkit.table()
        tool["other"] = tomlkit.table()
        doc["tool"] = tool
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        result = _manager().sync_one(pyproject)
        tm.that(result.is_success, eq=True)
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
        tm.that(result.is_success, eq=True)

    def test_sync_one_dry_run(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        doc = tomlkit.document()
        doc["tool"] = {"pyright": {"extraPaths": ["old"]}}
        pyproject.write_text(doc.as_string(), encoding="utf-8")
        tm.ok(_manager().sync_one(pyproject, dry_run=True, is_root=True))
        tm.that(pyproject.read_text(encoding="utf-8"), contains="old")

    def test_sync_one_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.pyright]\nextraPaths = ["old"]\n', encoding="utf-8")

        def _broken_write(
            _path: Path,
            _doc: TOMLDocument,
        ) -> r[bool]:
            _ = _path, _doc
            return r[bool].fail("write error")

        monkeypatch.setattr(
            deps_extra_paths.u.Cli,
            "toml_write_document",
            staticmethod(_broken_write),
        )
        tm.fail(_manager().sync_one(pyproject, is_root=True), has="write error")


class TestConstants:
    def test_base_constants(self) -> None:
        manager = FlextInfraExtraPathsManager()
        tm.that(hasattr(manager, "ROOT"), eq=True)
        tm.that(manager.ROOT.is_absolute(), eq=True)


def test_pyrefly_search_paths_include_workspace_declared_dev_dependencies(
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

    manager = FlextInfraExtraPathsManager(workspace_root=tmp_path)
    result = manager.pyrefly_search_paths(project_dir=consumer, is_root=False)

    tm.that(result, has="../flext-infra/src")
    tm.that(result, has="../flext-tests/src")
