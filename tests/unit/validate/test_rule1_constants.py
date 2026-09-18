"""Tests for Rule 1: Constants facade validation."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsRule1ConstantsFacade:
    """Test suite for the namespace validator rule under test."""

    _FIXTURES_DIR = (
        Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"
    )

    def _read_fixture(self, name: str) -> str:

        fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name

        return (self._FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")

    def _make_project_with_module(
        self, tmp_path: Path, *, module_source: str, module_name: str
    ) -> Path:

        project_root = tmp_path / "project"

        package_dir = project_root / "src" / "flext_test"

        package_dir.mkdir(parents=True)

        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")

        u.Tests.write_canonical_package_layout(package_dir)

        _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")

        u.Tests.initialize_git_repo(project_root)

        return project_root

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
        root = self._make_project_with_module(
            tmp_path, module_source=module_source, module_name="constants.py"
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)


__all__: list[str] = ["TestsRule1ConstantsFacade"]
