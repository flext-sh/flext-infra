from __future__ import annotations

from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm

from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from tests.typings import t
from tests.unit.deps._extra_paths_support import ExtraPathsTestSupport


def _manager(
    workspace_root: Path | None = None,
) -> FlextInfraExtraPathsManager:
    return ExtraPathsTestSupport.manager(workspace_root)


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
        tool_doc: t.MappingKV[str, t.Infra.InfraValue],
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

        tm.fail(_manager().sync_one(pyproject, is_root=True), has="TOML write")

    def test_base_constants(self) -> None:
        manager = _manager()
        tm.that(manager.root.is_absolute(), eq=True)
