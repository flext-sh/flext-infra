"""Tests for Rule 2: Typings facade validation."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u

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
    u.Tests.write_canonical_package_layout(package_dir)
    _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")
    u.Tests.initialize_git_repo(project_root)
    return project_root


class TestsRule2TypingsFacade:
    """Test suite for namespace validator Rule 2 (typings facade)."""

    def test_rule2_valid_types_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_core import t\n\n"
            "from flext_test._typings.base import FlextTestTypesBase\n"
            "from flext_test._typings.domain import FlextTestTypesDomain\n\n\n"
            "class FlextTestTypes(t):\n"
            "    class Test(FlextTestTypesBase, FlextTestTypesDomain):\n"
            "        pass\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="typings.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

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
                "module alias/data declaration is forbidden" in violation
                for violation in result.value.violations
            ),
            eq=True,
        )


__all__: list[str] = ["TestsRule2TypingsFacade"]
