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
    _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")
    return project_root


def _make_project_with_module_path(
    tmp_path: Path, *, module_source: str, module_path: str
) -> Path:
    project_root = tmp_path / "project"
    package_dir = project_root / "src" / "flext_test"
    package_dir.mkdir(parents=True)
    _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
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
        assert layout is not None
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
        tracked_module = package_dir / "models.py"
        tracked_module.write_text(_read_fixture("rule0_valid.py"), encoding="utf-8")

        init_result = u.Cli.run_raw(["git", "init"], cwd=project_root)
        tm.ok(init_result)
        tm.that(init_result.value.exit_code, eq=0)
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"], cwd=project_root
        )
        tm.ok(email_result)
        tm.that(email_result.value.exit_code, eq=0)
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"], cwd=project_root
        )
        tm.ok(name_result)
        tm.that(name_result.value.exit_code, eq=0)
        add_result = u.Cli.run_raw(
            ["git", "add", "src/flext_test/models.py", "src/flext_test/__init__.py"],
            cwd=project_root,
        )
        tm.ok(add_result)
        tm.that(add_result.value.exit_code, eq=0)

        result = validator.validate_project(project_root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    def test_rule0_multiple_classes_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_multiple_classes.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("Multiple outer classes found" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule0_no_class_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_no_class.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("No outer class found" in v for v in result.value.violations), eq=True
        )

    def test_rule0_wrong_prefix_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_wrong_prefix.py"),
            module_name="constants.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "does not start with prefix 'FlextTest'" in v
                for v in result.value.violations
            ),
            eq=True,
        )

    def test_rule0_loose_items_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_loose_items.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "Disallowed top-level statement: FunctionDef" in v
                for v in result.value.violations
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

    def test_rule1_loose_constant_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_loose_constant.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("Loose Final constant" in v for v in result.value.violations), eq=True
        )

    def test_rule1_loose_enum_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_loose_enum.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("Multiple outer classes found" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule1_method_in_constants_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_method_in_constants.py"),
            module_name="constants.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "Method 'create_name' found in Constants class" in v
                for v in result.value.violations
            ),
            eq=True,
        )

    def test_rule1_magic_number_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_magic_number.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("Loose collection constant" in v for v in result.value.violations),
            eq=True,
        )

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
                "must use namespaced MRO aliases (c/m/p/t/u)",
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

    def test_rule2_typevar_in_class_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule2_typevar_in_class.py"),
            module_name="typings.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("must inherit from a Types base" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule2_typevar_wrong_module_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule2_typevar_wrong_module.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "TypeVar 'T' belongs in typings.py" in v
                for v in result.value.violations
            ),
            eq=True,
        )

    def test_rule2_composite_type_loose_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule2_composite_type_loose.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "TypeAlias 'LooseTypeAlias' belongs in typings.py" in v
                for v in result.value.violations
            ),
            eq=True,
        )

    def test_rule2_protocol_in_types_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule2_protocol_in_types.py"),
            module_name="typings.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                "Inner class 'ProtocolInsideTypes'" in v
                for v in result.value.violations
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

    def test_rule0_allows_type_checking_block(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from collections.abc import Sequence\n\n"
            "class FlextTestModels(Models):\n"
            "    pass\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "Disallowed top-level statement: If" in violation
                for violation in result.value.violations
            ),
            eq=False,
        )

    def test_rule0_allows_annotated_dunder_assign(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "class FlextTestModels(Models):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextTestModels"]\n'
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "Disallowed top-level statement: AnnAssign" in violation
                for violation in result.value.violations
            ),
            eq=False,
        )

    def test_rule1_skips_enum_detection_inside_private_constants_dir(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n"
            "from enum import Enum\n\n"
            "class FlextTestModelsConstants:\n"
            "    class Status(Enum):\n"
            '        OK = "ok"\n'
        )
        root = _make_project_with_module_path(
            tmp_path, module_source=module_source, module_path="_constants/sample.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "Loose Enum 'Status' belongs in constants.py" in v
                for v in result.value.violations
            ),
            eq=False,
        )

    def test_rule2_skips_typealias_detection_inside_private_typings_dir(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\ntype LocalAlias = str | int\n"
        )
        root = _make_project_with_module_path(
            tmp_path,
            module_source=module_source,
            module_path="_typings/typeadapters.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "PEP 695 TypeAlias 'LocalAlias' belongs in typings.py" in v
                for v in result.value.violations
            ),
            eq=False,
        )

    def test_rule3_skips_direct_imports_inside_private_dirs(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n"
            "from flext_test import FlextTestModelsSomething\n\n"
            "class FlextTestModelsThing(Models):\n"
            "    pass\n"
        )
        root = _make_project_with_module_path(
            tmp_path,
            module_source=module_source,
            module_path="_utilities/private_runtime.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "instead of direct import 'FlextTestModelsSomething'" in v
                for v in result.value.violations
            ),
            eq=False,
        )

    @pytest.mark.parametrize(
        ("module_path", "module_source"),
        [
            (
                "tests/constants.py",
                "from tests import m\n\nclass TestsFlextTestConstants:\n    pass\n",
            ),
            (
                "tests/_typings/domain.py",
                "from tests import u\n\nclass TestsFlextTestTypesDomain:\n    pass\n",
            ),
        ],
    )
    def test_rule3_test_namespace_runtime_reverse_import_detected(
        self, tmp_path: Path, module_path: str, module_source: str
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path, module_source=module_source, module_path=module_path
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=False)
        tm.that(
            any("runtime namespace import" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule3_test_namespace_type_checking_reverse_import_allowed(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path,
            module_source=(
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from tests import u\n\n"
                "class TestsFlextTestTypes:\n"
                "    pass\n"
            ),
            module_path="tests/typings.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any("runtime namespace import" in v for v in result.value.violations),
            eq=False,
        )

    @pytest.mark.parametrize(
        "forbidden_module",
        ["tests", "tests.conftest", "tests.fixtures", "tests.unit.test_service"],
    )
    def test_rule3_test_facade_importing_test_support_detected(
        self, tmp_path: Path, forbidden_module: str
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path,
            module_source=(
                f"from {forbidden_module} import helper\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n"
            ),
            module_path="tests/models.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=False)
        tm.that(
            any("test support module" in v for v in result.value.violations), eq=True
        )

    @pytest.mark.parametrize(
        ("module_path", "module_source"),
        [
            (
                "tests/models.py",
                "from tests import c, t, p\n\nclass TestsFlextTestModels:\n    pass\n",
            ),
            (
                "tests/utilities.py",
                "from tests import c, t, p, m\n\nclass TestsFlextTestUtilities:\n    pass\n",
            ),
        ],
    )
    def test_rule3_test_facade_forward_owner_assembly_allowed(
        self, tmp_path: Path, module_path: str, module_source: str
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path, module_source=module_source, module_path=module_path
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any("runtime namespace import" in v for v in result.value.violations),
            eq=False,
        )

    def test_rule3_test_facade_matching_private_family_assembly_allowed(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path,
            module_source=(
                "from tests._models.domain import TestsFlextTestModelsDomain\n\n"
                "class TestsFlextTestModels:\n"
                "    pass\n"
            ),
            module_path="tests/models.py",
        )
        result = validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=True)
        tm.that(
            any("test support module" in v for v in result.value.violations), eq=False
        )

    def test_rule3_test_private_family_runtime_reverse_import_detected(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module_path(
            tmp_path,
            module_source=(
                "from tests._utilities.domain import TestsFlextTestUtilitiesDomain\n\n"
                "class TestsFlextTestTypesDomain:\n"
                "    pass\n"
            ),
            module_path="tests/_typings/domain.py",
        )
        result = validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=False)
        tm.that(
            any("runtime namespace import" in v for v in result.value.violations),
            eq=True,
        )
