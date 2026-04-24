"""Tests for FlextInfraNamespaceValidator."""

from __future__ import annotations

import re
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraNamespaceValidator
from tests import m, u

_FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"


def _read_fixture(name: str) -> str:
    fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name
    return (_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")


def _make_project_with_module(
    tmp_path: Path,
    *,
    module_source: str,
    module_name: str,
) -> Path:
    project_root = tmp_path / "project"
    package_dir = project_root / "src" / "flext_test"
    package_dir.mkdir(parents=True)
    _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")
    return project_root


class TestFlextInfraNamespaceValidator:
    """Test suite for namespace validator rules 0-3."""

    def test_public_project_layout_uses_flext_for_core_exception(
        self,
        tmp_path: Path,
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
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    def test_validate_ignores_untracked_git_files(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        tracked_module = package_dir / "models.py"
        tracked_module.write_text(_read_fixture("rule0_valid.py"), encoding="utf-8")
        untracked_module = package_dir / "constants.py"
        untracked_module.write_text(
            _read_fixture("rule0_multiple_classes.py"), encoding="utf-8"
        )
        init_result = u.Cli.run_raw(["git", "init"], cwd=project_root)
        assert init_result.success
        assert init_result.value.exit_code == 0
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_root,
        )
        assert email_result.success
        assert email_result.value.exit_code == 0
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"],
            cwd=project_root,
        )
        assert name_result.success
        assert name_result.value.exit_code == 0
        add_result = u.Cli.run_raw(
            ["git", "add", "src/flext_test/models.py", "src/flext_test/__init__.py"],
            cwd=project_root,
        )
        assert add_result.success
        assert add_result.value.exit_code == 0

        result = validator.validate(project_root)

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
        result = validator.validate(root)
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
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("No outer class found" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule0_wrong_prefix_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_wrong_prefix.py"),
            module_name="constants.py",
        )
        result = validator.validate(root)
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
        result = validator.validate(root)
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
            tmp_path,
            module_source=module_source,
            module_name="constants.py",
        )
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    def test_rule1_loose_constant_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_loose_constant.py"),
            module_name="models.py",
        )
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any("Loose Final constant" in v for v in result.value.violations),
            eq=True,
        )

    def test_rule1_loose_enum_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule1_loose_enum.py"),
            module_name="models.py",
        )
        result = validator.validate(root)
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
        result = validator.validate(root)
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
        result = validator.validate(root)
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
            tmp_path,
            module_source=module_source,
            module_name="typings.py",
        )
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    def test_rule3_direct_runtime_utilities_import_detected(
        self,
        tmp_path: Path,
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n"
            "from flext_infra import FlextInfraUtilitiesCodegen\n\n"
            "class FlextTestModels(Models):\n"
            "    pass\n"
        )
        root = _make_project_with_module(
            tmp_path,
            module_source=module_source,
            module_name="models.py",
        )

        result = validator.validate(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=False)
        tm.that(
            any(
                "must use u.Infra namespaced MRO access" in violation
                for violation in result.value.violations
            ),
            eq=True,
        )

    def test_rule3_utilities_facade_import_remains_allowed(
        self,
        tmp_path: Path,
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_cli import u\n"
            "from flext_infra import FlextInfraUtilitiesCodegen\n\n"
            "class FlextTestUtilities(u):\n"
            "    class Infra(FlextInfraUtilitiesCodegen):\n"
            "        pass\n"
        )
        root = _make_project_with_module(
            tmp_path,
            module_source=module_source,
            module_name="utilities.py",
        )

        result = validator.validate(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)

    def test_rule2_typevar_in_class_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule2_typevar_in_class.py"),
            module_name="typings.py",
        )
        result = validator.validate(root)
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
        result = validator.validate(root)
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
        result = validator.validate(root)
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
        result = validator.validate(root)
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
            _read_fixture("rule0_no_class.py"),
            encoding="utf-8",
        )
        _ = (package_dir / "test_rule.py").write_text(
            _read_fixture("rule0_no_class.py"),
            encoding="utf-8",
        )
        _ = (package_dir / "_private.py").write_text(
            _read_fixture("rule0_no_class.py"),
            encoding="utf-8",
        )
        result = validator.validate(project_root)
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
        result = validator.validate(root)
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
        result = validator.validate(root)
        tm.that(result.success, eq=True)
        tm.that(len(result.value.violations), gt=0)
        first = result.value.violations[0]
        tm.that(re.search(r"^\[NS-\d{3}-\d{3}\] .+\.py:\d+ — .+$", first), none=False)
