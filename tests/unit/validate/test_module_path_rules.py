"""Tests for module path-based namespace rules (test directory patterns)."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import m, t, u


class TestsModulePathRules:
    """Namespace rules key on the module path a project actually declares."""

    _FIXTURES_DIR = (
        Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"
    )

    def _read_fixture(self, name: str) -> str:

        fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name

        return (self._FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")

    def _make_project_with_module_path(
        self, tmp_path: Path, *, module_source: str, module_path: str
    ) -> t.Pair[Path, Path]:

        project_root = tmp_path / "project"

        package_dir = project_root / "src" / "flext_test"

        package_dir.mkdir(parents=True)

        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")

        u.Tests.write_canonical_package_layout(package_dir)

        relative = Path(module_path)

        target = (
            project_root / relative
            if relative.parts[0] == "tests"
            else package_dir / relative
        )

        target.parent.mkdir(parents=True, exist_ok=True)

        _ = target.write_text(module_source, encoding="utf-8")

        u.Tests.initialize_git_repo(project_root)

        return project_root, target

    """Namespace rules key on the module path a project actually declares."""

    @pytest.mark.parametrize(
        (
            "module_path",
            "module_source",
            "violation_substr",
            "expect_violation",
            "expect_passed",
        ),
        [
            pytest.param(
                "_constants/sample.py",
                "from __future__ import annotations\n"
                "from enum import Enum\n\n"
                "class FlextTestModelsConstants:\n"
                "    class Status(Enum):\n"
                '        OK = "ok"\n',
                "Loose Enum 'Status' belongs in constants.py",
                False,
                None,
                id="rule1-skips-enum-inside-private-constants-dir",
            ),
            pytest.param(
                "_typings/typeadapters.py",
                "from __future__ import annotations\n\ntype LocalAlias = str | int\n",
                "PEP 695 TypeAlias 'LocalAlias' belongs in typings.py",
                False,
                None,
                id="rule2-skips-typealias-inside-private-typings-dir",
            ),
            pytest.param(
                "_utilities/private_runtime.py",
                "from __future__ import annotations\n"
                "from flext_test import FlextTestModelsSomething\n\n"
                "class FlextTestModelsThing(Models):\n"
                "    pass\n",
                "instead of direct import 'FlextTestModelsSomething'",
                False,
                None,
                id="rule3-skips-direct-imports-inside-private-dirs",
            ),
            pytest.param(
                "tests/constants.py",
                "from tests import m\n\nclass TestsFlextTestConstants:\n    pass\n",
                "facade must inherit canonical 'c'",
                True,
                False,
                id="rule3-test-constants-facade-shape-required",
            ),
            pytest.param(
                "tests/_typings/domain.py",
                "from tests import u\n\nclass TestsFlextTestTypesDomain:\n    pass\n",
                "facade must inherit canonical",
                False,
                True,
                id="rule3-test-private-typings-nonfacade-passes",
            ),
            pytest.param(
                "tests/typings.py",
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from tests import u\n\n"
                "class TestsFlextTestTypes(t):\n"
                "    class TestsFlextTest(TestsFlextTestTypesBase, "
                "TestsFlextTestTypesDomain):\n"
                "        pass\n",
                "runtime namespace import",
                False,
                True,
                id="rule3-test-type-checking-reverse-import-allowed",
            ),
            pytest.param(
                "tests/models.py",
                "from tests import helper\n\nclass TestsFlextTestModels:\n    pass\n",
                "facade must inherit canonical 'm'",
                True,
                False,
                id="rule3-test-facade-imports-tests-package",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.conftest import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "facade must inherit canonical 'm'",
                True,
                False,
                id="rule3-test-facade-imports-conftest",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.fixtures import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "facade must inherit canonical 'm'",
                True,
                False,
                id="rule3-test-facade-imports-fixtures",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.unit.test_service import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "facade must inherit canonical 'm'",
                True,
                False,
                id="rule3-test-facade-imports-test-module",
            ),
            pytest.param(
                "tests/models.py",
                "from tests import c, t, p, m\n\n"
                "class TestsFlextTestModels(m):\n"
                "    class TestsFlextTest(c, t, p):\n"
                "        pass\n",
                "facade must inherit canonical",
                False,
                True,
                id="rule3-test-models-forward-owner-assembly-allowed",
            ),
            pytest.param(
                "tests/utilities.py",
                "from tests import c, t, p, m, u\n\n"
                "class TestsFlextTestUtilities(u):\n"
                "    class TestsFlextTest(c, t, p):\n"
                "        pass\n",
                "facade must inherit canonical",
                False,
                True,
                id="rule3-test-utilities-forward-owner-assembly-allowed",
            ),
            pytest.param(
                "tests/models.py",
                "from tests import m\n"
                "from tests._models.domain import TestsFlextTestModelsDomain\n\n"
                "class TestsFlextTestModels(m):\n"
                "    class TestsFlextTest(TestsFlextTestModelsDomain, "
                "TestsFlextTestModelsBase):\n"
                "        pass\n",
                "test support module",
                False,
                True,
                id="rule3-test-matching-private-family-assembly-allowed",
            ),
            pytest.param(
                "tests/_typings/domain.py",
                "from tests._utilities.domain import TestsFlextTestUtilitiesDomain\n\n"
                "class TestsFlextTestTypesDomain:\n"
                "    pass\n",
                "facade must inherit canonical",
                False,
                True,
                id="rule3-test-private-family-cross-import-passes",
            ),
        ],
    )
    def test_module_path_violation_presence(
        self,
        tmp_path: Path,
        module_path: str,
        module_source: str,
        violation_substr: str,
        *,
        expect_violation: bool,
        expect_passed: bool | None,
    ) -> None:
        """Namespace rules key on the module path a project actually declares."""
        validator = FlextInfraNamespaceValidator()
        root, target = self._make_project_with_module_path(
            tmp_path, module_source=module_source, module_path=module_path
        )
        files = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(root,))
        )
        tm.ok(files)
        tm.that(
            target in files.value,
            eq=True,
            msg=f"namespace fixture omitted from source inventory: {target}; {files.value}",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        if expect_passed is not None:
            tm.that(result.value.passed, eq=expect_passed, msg=str(result.value))
        tm.that(
            any(violation_substr in v for v in result.value.violations),
            eq=expect_violation,
        )


__all__: list[str] = ["TestsModulePathRules"]
