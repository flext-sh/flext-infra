"""Tests for FlextInfraNamespaceValidator."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import c, m, u

_FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"


def _read_fixture(name: str) -> str:
    fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name
    return (_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")


def _make_project_with_module(
    tmp_path: Path, *, module_source: str, module_name: str
) -> Path:
    project_root = tmp_path / "project"
    package_dir = project_root / "src" / "flext_test"
    package_dir.mkdir(parents=True)
    _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
    # The validator grades the whole package, so the fixture is a package.
    u.Tests.write_canonical_package_layout(package_dir)
    _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")
    return project_root


def _make_project_with_module_path(
    tmp_path: Path, *, module_source: str, module_path: str
) -> Path:
    project_root = tmp_path / "project"
    package_dir = project_root / "src" / "flext_test"
    package_dir.mkdir(parents=True)
    _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
    u.Tests.write_canonical_package_layout(package_dir)
    target = package_dir / module_path
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_text(module_source, encoding="utf-8")
    return project_root


class TestFlextInfraNamespaceValidator:
    """Test suite for namespace validator rules 0-3."""

    def test_public_project_layout_uses_flext_for_core_exception(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "flext-core"
        package_dir = project_root / "src" / "flext_core"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        layout = u.Infra.layout(project_root)
        layout = tm.not_none(layout)
        tm.that(layout.class_stem, eq="Flext")

    def test_rule0_valid_module_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_valid.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    def test_validate_tracked_git_files(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        u.Tests.write_canonical_package_layout(package_dir)
        tracked_module = package_dir / "models.py"
        tracked_module.write_text(_read_fixture("rule0_valid.py"), encoding="utf-8")

        init_result = u.Cli.run_raw(["git", "init"], cwd=project_root)
        tm.ok(init_result)
        tm.that(u.Cli.process_succeeded(init_result.value.outcome), eq=True)
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"], cwd=project_root
        )
        tm.ok(email_result)
        tm.that(u.Cli.process_succeeded(email_result.value.outcome), eq=True)
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"], cwd=project_root
        )
        tm.ok(name_result)
        tm.that(u.Cli.process_succeeded(name_result.value.outcome), eq=True)
        add_result = u.Cli.run_raw(
            ["git", "add", "src/flext_test/models.py", "src/flext_test/__init__.py"],
            cwd=project_root,
        )
        tm.ok(add_result)
        tm.that(u.Cli.process_succeeded(add_result.value.outcome), eq=True)

        result = validator.validate_project(project_root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    @pytest.mark.parametrize(
        ("fixture_name", "module_name", "expected_violation_substr"),
        [
            pytest.param(
                "rule0_multiple_classes.py",
                "models.py",
                "module must declare exactly one top-level class; found 2",
                id="rule0-multiple-classes",
            ),
            pytest.param(
                "rule0_no_class.py",
                "models.py",
                "No outer class found",
                id="rule0-no-class",
            ),
            pytest.param(
                "rule0_wrong_prefix.py",
                "constants.py",
                "does not start with prefix 'FlextTest'",
                id="rule0-wrong-prefix",
            ),
            pytest.param(
                "rule0_loose_items.py",
                "models.py",
                "Disallowed top-level statement: FunctionDef",
                id="rule0-loose-items",
            ),
            pytest.param(
                "rule1_loose_constant.py",
                "models.py",
                "Loose Final constant",
                id="rule1-loose-constant",
            ),
            pytest.param(
                "rule1_loose_enum.py",
                "models.py",
                "Multiple outer classes found",
                id="rule1-loose-enum",
            ),
            pytest.param(
                "rule1_method_in_constants.py",
                "constants.py",
                "Method 'create_name' found in Constants class",
                id="rule1-method-in-constants",
            ),
            pytest.param(
                "rule1_magic_number.py",
                "models.py",
                "Loose collection constant",
                id="rule1-magic-number",
            ),
            pytest.param(
                "rule2_typevar_in_class.py",
                "typings.py",
                "must inherit from a Types base",
                id="rule2-typevar-in-class",
            ),
            pytest.param(
                "rule2_typevar_wrong_module.py",
                "models.py",
                "TypeVar 'T' belongs in typings.py",
                id="rule2-typevar-wrong-module",
            ),
            pytest.param(
                "rule2_composite_type_loose.py",
                "models.py",
                "TypeAlias 'LooseTypeAlias' belongs in typings.py",
                id="rule2-composite-type-loose",
            ),
            pytest.param(
                "rule2_protocol_in_types.py",
                "typings.py",
                "Inner class 'ProtocolInsideTypes'",
                id="rule2-protocol-in-types",
            ),
        ],
    )
    def test_fixture_module_reports_its_violation(
        self,
        tmp_path: Path,
        fixture_name: str,
        module_name: str,
        expected_violation_substr: str,
    ) -> None:
        """Each namespace-rule fixture fails the project with its own message."""
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path, module_source=_read_fixture(fixture_name), module_name=module_name
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                expected_violation_substr in violation
                for violation in result.value.violations
            ),
            eq=True,
        )

    def test_rule1_valid_constants_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = "from __future__ import annotations\n\nclass FlextTestConstants(Constants):\n    class Limits:\n        MAX_RETRIES = 3\n"
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="constants.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    def test_rule2_valid_types_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = 'from __future__ import annotations\nfrom typing import TypeVar\n\nT = TypeVar("T")\n\nclass FlextTestTypes(Types):\n    pass\n'
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="typings.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    @pytest.mark.parametrize(
        ("module_source", "module_name", "expected_violation_substr"),
        [
            (
                (
                    "from __future__ import annotations\n"
                    "from flext_test import FlextTestUtilitiesCodegen\n\n"
                    "class FlextTestModels(Models):\n"
                    "    pass\n"
                ),
                "models.py",
                "must use namespaced FLEXT aliases (c/m/p/t/u)",
            ),
            (
                (
                    "from __future__ import annotations\n"
                    "from flext_test import FlextTestModelsDeps\n\n"
                    "class FlextTestDetector:\n"
                    "    pass\n"
                ),
                "detector.py",
                "instead of direct import 'FlextTestModelsDeps'",
            ),
        ],
    )
    def test_rule3_direct_runtime_import_detected(
        self,
        tmp_path: Path,
        module_source: str,
        module_name: str,
        expected_violation_substr: str,
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name=module_name
        )
        result = validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=False)
        tm.that(
            any(
                expected_violation_substr in violation
                for violation in result.value.violations
            ),
            eq=True,
        )

    def test_rule3_utilities_facade_import_remains_allowed(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_cli import u\n"
            "from flext_test import FlextTestUtilitiesCodegen\n\n"
            "class FlextTestUtilities(u):\n"
            "    class Infra(FlextTestUtilitiesCodegen):\n"
            "        pass\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="utilities.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)

    def test_rule3_models_facade_import_remains_allowed(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n"
            "from flext_cli import m\n"
            "from flext_test import FlextTestModelsDeps\n\n"
            "class FlextTestModels(m):\n"
            "    class Infra(FlextTestModelsDeps):\n"
            "        pass\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)

    def test_rule0_does_not_flag_non_namespace_runtime_module(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "VALUE = 1\n\n"
            "def helper() -> int:\n"
            "    return VALUE\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="api.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                violation.startswith("[NS-000") for violation in result.value.violations
            ),
            eq=False,
        )

    def test_rule2_typevar_runtime_module_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source='from typing import TypeVar\n\nT = TypeVar("T")\n',
            module_name="base.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "TypeVar 'T' belongs in typings.py" in violation
                for violation in result.value.violations
            ),
            eq=True,
        )

    def test_exempt_files_skipped(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text(
            _read_fixture("rule0_no_class.py"), encoding="utf-8"
        )
        _ = (package_dir / "test_rule.py").write_text(
            _read_fixture("rule0_no_class.py"), encoding="utf-8"
        )
        _ = (package_dir / "_private.py").write_text(
            _read_fixture("rule0_no_class.py"), encoding="utf-8"
        )
        result = validator.validate_project(project_root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)
        tm.that(result.value.summary, has="0 files checked")

    def test_validate_returns_report(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_valid.py"),
            module_name="constants.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value, is_=m.Infra.ValidationReport)
        tm.that(result.value.summary, has="files checked")

    def test_violation_message_format(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_no_class.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(len(result.value.violations), gt=0)
        first = result.value.violations[0]
        tm.that(c.Infra.VIOLATION_PATTERN.search(first), none=False)

    @pytest.mark.parametrize(
        ("module_source", "forbidden_violation_substr"),
        [
            pytest.param(
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from collections.abc import Sequence\n\n"
                "class FlextTestModels(Models):\n"
                "    pass\n",
                "Disallowed top-level statement: If",
                id="rule0-allows-type-checking-block",
            ),
            pytest.param(
                "from __future__ import annotations\n\n"
                "class FlextTestModels(Models):\n"
                "    pass\n\n"
                '__all__: list[str] = ["FlextTestModels"]\n',
                "Disallowed top-level statement: AnnAssign",
                id="rule0-allows-annotated-dunder-assign",
            ),
        ],
    )
    def test_rule0_allows_top_level_statement(
        self, tmp_path: Path, module_source: str, forbidden_violation_substr: str
    ) -> None:
        """Rule 0 never rejects the top-level statements a namespace may carry."""
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                forbidden_violation_substr in violation
                for violation in result.value.violations
            ),
            eq=False,
        )

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
                "runtime namespace import",
                True,
                False,
                id="rule3-test-constants-runtime-reverse-import",
            ),
            pytest.param(
                "tests/_typings/domain.py",
                "from tests import u\n\nclass TestsFlextTestTypesDomain:\n    pass\n",
                "runtime namespace import",
                True,
                False,
                id="rule3-test-private-typings-runtime-reverse-import",
            ),
            pytest.param(
                "tests/typings.py",
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from tests import u\n\n"
                "class TestsFlextTestTypes:\n"
                "    pass\n",
                "runtime namespace import",
                False,
                None,
                id="rule3-test-type-checking-reverse-import-allowed",
            ),
            pytest.param(
                "tests/models.py",
                "from tests import helper\n\nclass TestsFlextTestModels:\n    pass\n",
                "test support module",
                True,
                False,
                id="rule3-test-facade-imports-tests-package",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.conftest import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "test support module",
                True,
                False,
                id="rule3-test-facade-imports-conftest",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.fixtures import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "test support module",
                True,
                False,
                id="rule3-test-facade-imports-fixtures",
            ),
            pytest.param(
                "tests/models.py",
                "from tests.unit.test_service import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
                "test support module",
                True,
                False,
                id="rule3-test-facade-imports-test-module",
            ),
            pytest.param(
                "tests/models.py",
                "from tests import c, t, p\n\nclass TestsFlextTestModels:\n    pass\n",
                "runtime namespace import",
                False,
                None,
                id="rule3-test-models-forward-owner-assembly-allowed",
            ),
            pytest.param(
                "tests/utilities.py",
                "from tests import c, t, p, m\n\n"
                "class TestsFlextTestUtilities:\n"
                "    pass\n",
                "runtime namespace import",
                False,
                None,
                id="rule3-test-utilities-forward-owner-assembly-allowed",
            ),
            pytest.param(
                "tests/models.py",
                "from tests._models.domain import TestsFlextTestModelsDomain\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n",
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
                "runtime namespace import",
                True,
                False,
                id="rule3-test-private-family-runtime-reverse-import",
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
        root = _make_project_with_module_path(
            tmp_path, module_source=module_source, module_path=module_path
        )

        result = validator.validate_project(root)

        tm.ok(result)
        if expect_passed is not None:
            tm.that(result.value.passed, eq=expect_passed)
        tm.that(
            any(violation_substr in v for v in result.value.violations),
            eq=expect_violation,
        )
