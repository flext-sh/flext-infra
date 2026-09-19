"""Tests for Rule 1: Constants facade validation."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsFlextInfraRule1ConstantsFacade:
    """Test suite for the namespace validator rule under test."""

    """Test suite for namespace validator Rule 1 (constants facade)."""

    def test_rule1_valid_constants_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "from flext_test._constants.base import FlextTestConstantsBase\n"
            "from flext_test._constants.domain import FlextTestConstantsDomain\n\n\n"
            "class FlextTestConstants(c):\n"
            "    class Test(FlextTestConstantsBase, FlextTestConstantsDomain):\n"
            "        pass\n"
        )
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name="constants.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)


__all__: list[str] = ["TestsFlextInfraRule1ConstantsFacade"]
