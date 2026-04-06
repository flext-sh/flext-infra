from __future__ import annotations

from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraExtraPathsManager

_TEST_WORKSPACE_ROOT = Path(__file__).resolve().parent


@pytest.fixture
def manager() -> FlextInfraExtraPathsManager:
    return FlextInfraExtraPathsManager(workspace_root=_TEST_WORKSPACE_ROOT)


class TestPathDepPathsPep621:
    def test_pep621_empty_doc(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        tm.that(manager.path_dep_paths_pep621(doc), eq=[])

    def test_pep621_no_project(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        doc["other"] = tomlkit.table()
        tm.that(manager.path_dep_paths_pep621(doc), eq=[])

    def test_pep621_no_dependencies(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {"name": "test"}
        tm.that(manager.path_dep_paths_pep621(doc), eq=[])

    def test_pep621_with_file_deps(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "flext-core @ file:../flext-core",
                "flext-api @ file:../flext-api",
            ],
        }
        result = manager.path_dep_paths_pep621(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)
        tm.that(any("flext-api" in item for item in result), eq=True)

    def test_pep621_with_relative_deps(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-core @ ./flext-core"]}
        result = manager.path_dep_paths_pep621(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)

    def test_pep621_mixed_deps(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "requests>=2.0",
                "flext-core @ file:../flext-core",
                "pydantic",
            ],
        }
        result = manager.path_dep_paths_pep621(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)
        tm.that(len(result), eq=1)

    def test_pep621_with_file_prefix(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-core @ file://flext-core"]}
        result = manager.path_dep_paths_pep621(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)

    def test_pep621_ignores_git_dependencies(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "dbt-common @ git+https://github.com/flext-sh/dbt-common.git@main",
                "flext-core @ file:../flext-core",
            ],
        }
        result = manager.path_dep_paths_pep621(doc)
        tm.that(result, has="../flext-core")
        tm.that(any("git+https" in item for item in result), eq=False)

    def test_pep621_ignores_https_dependencies(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "custom-lib @ https://example.com/custom-lib.whl",
                "flext-core @ ../flext-core",
            ],
        }
        result = manager.path_dep_paths_pep621(doc)
        tm.that(result, has="../flext-core")
        tm.that(any("https://" in item for item in result), eq=False)


class TestPathDepPathsPoetry:
    def test_poetry_empty_doc(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        tm.that(manager.path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_tool(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        doc["project"] = tomlkit.table()
        tm.that(manager.path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_poetry_section(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        tool = tomlkit.table()
        tool["other"] = tomlkit.table()
        doc["tool"] = tool
        tm.that(manager.path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_dependencies(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["tool"] = {"poetry": {"name": "test"}}
        tm.that(manager.path_dep_paths_poetry(doc), eq=[])

    def test_poetry_with_path_deps(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {
                "dependencies": {
                    "flext-core": {"path": "../flext-core"},
                    "flext-api": {"path": "../flext-api"},
                },
            },
        }
        result = manager.path_dep_paths_poetry(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)
        tm.that(any("flext-api" in item for item in result), eq=True)

    def test_poetry_with_relative_paths(
        self,
        manager: FlextInfraExtraPathsManager,
    ) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "./flext-core"}}},
        }
        result = manager.path_dep_paths_poetry(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)

    def test_poetry_mixed_deps(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {
                "dependencies": {
                    "requests": "^2.0",
                    "flext-core": {"path": "../flext-core"},
                    "pydantic": "^2.0",
                },
            },
        }
        result = manager.path_dep_paths_poetry(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)
        tm.that(len(result), eq=1)

    def test_poetry_with_path(self, manager: FlextInfraExtraPathsManager) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        result = manager.path_dep_paths_poetry(doc)
        tm.that(any("flext-core" in item for item in result), eq=True)
