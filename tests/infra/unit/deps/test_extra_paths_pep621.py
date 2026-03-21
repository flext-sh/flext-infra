from __future__ import annotations

import tomlkit
from flext_tests import u

from flext_infra import FlextInfraExtraPathsManager


def _manager() -> FlextInfraExtraPathsManager:
    return FlextInfraExtraPathsManager()


class TestPathDepPathsPep621:
    def test_pep621_empty_doc(self) -> None:
        doc = tomlkit.document()
        u.Tests.Matchers.that(_manager().path_dep_paths_pep621(doc), eq=[])

    def test_pep621_no_project(self) -> None:
        doc = tomlkit.document()
        doc["other"] = tomlkit.table()
        u.Tests.Matchers.that(_manager().path_dep_paths_pep621(doc), eq=[])

    def test_pep621_no_dependencies(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {"name": "test"}
        u.Tests.Matchers.that(_manager().path_dep_paths_pep621(doc), eq=[])

    def test_pep621_with_file_deps(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "flext-core @ file:../flext-core",
                "flext-api @ file:../flext-api",
            ],
        }
        result = _manager().path_dep_paths_pep621(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)
        u.Tests.Matchers.that(any("flext-api" in item for item in result), eq=True)

    def test_pep621_with_relative_deps(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-core @ ./flext-core"]}
        result = _manager().path_dep_paths_pep621(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)

    def test_pep621_mixed_deps(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": [
                "requests>=2.0",
                "flext-core @ file:../flext-core",
                "pydantic",
            ],
        }
        result = _manager().path_dep_paths_pep621(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)
        u.Tests.Matchers.that(len(result), eq=1)

    def test_pep621_with_file_prefix(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {"dependencies": ["flext-core @ file://flext-core"]}
        result = _manager().path_dep_paths_pep621(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)


class TestPathDepPathsPoetry:
    def test_poetry_empty_doc(self) -> None:
        doc = tomlkit.document()
        u.Tests.Matchers.that(_manager().path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_tool(self) -> None:
        doc = tomlkit.document()
        doc["project"] = tomlkit.table()
        u.Tests.Matchers.that(_manager().path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_poetry_section(self) -> None:
        doc = tomlkit.document()
        tool = tomlkit.table()
        tool["other"] = tomlkit.table()
        doc["tool"] = tool
        u.Tests.Matchers.that(_manager().path_dep_paths_poetry(doc), eq=[])

    def test_poetry_no_dependencies(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {"poetry": {"name": "test"}}
        u.Tests.Matchers.that(_manager().path_dep_paths_poetry(doc), eq=[])

    def test_poetry_with_path_deps(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {
                "dependencies": {
                    "flext-core": {"path": "../flext-core"},
                    "flext-api": {"path": "../flext-api"},
                },
            },
        }
        result = _manager().path_dep_paths_poetry(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)
        u.Tests.Matchers.that(any("flext-api" in item for item in result), eq=True)

    def test_poetry_with_relative_paths(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "./flext-core"}}},
        }
        result = _manager().path_dep_paths_poetry(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)

    def test_poetry_mixed_deps(self) -> None:
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
        result = _manager().path_dep_paths_poetry(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)
        u.Tests.Matchers.that(len(result), eq=1)

    def test_poetry_with_path(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "poetry": {"dependencies": {"flext-core": {"path": "../flext-core"}}},
        }
        result = _manager().path_dep_paths_poetry(doc)
        u.Tests.Matchers.that(any("flext-core" in item for item in result), eq=True)
