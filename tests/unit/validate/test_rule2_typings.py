"""Tests for Rule 2: Typings facade validation."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsFlextInfraRule2TypingsFacade:
    """Test suite for the namespace validator rule under test."""

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
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name="typings.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    def test_rule2_typevar_runtime_module_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = u.Tests.namespace_project(
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


__all__: list[str] = ["TestsFlextInfraRule2TypingsFacade"]
