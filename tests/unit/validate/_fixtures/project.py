"""Project fixture helpers for namespace validator tests.

Provides reusable project creation patterns to eliminate duplication
in test setup code across rule-specific test files.
"""

from __future__ import annotations

from pathlib import Path

from tests import u


class TestsFlextInfraNamespaceProjectFixture:
    """Factory for common namespace test project configurations."""

    @staticmethod
    def valid_constants_module() -> str:
        """Valid constants module source following Rule 1."""
        return (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "from flext_test._constants.base import FlextTestConstantsBase\n"
            "from flext_test._constants.domain import FlextTestConstantsDomain\n\n\n"
            "class FlextTestConstants(c):\n"
            "    class Test(FlextTestConstantsBase, FlextTestConstantsDomain):\n"
            "        pass\n"
        )

    @staticmethod
    def valid_typings_module() -> str:
        """Valid typings module source following Rule 2."""
        return (
            "from __future__ import annotations\n\n"
            "from flext_core import t\n\n"
            "from flext_test._typings.base import FlextTestTypesBase\n"
            "from flext_test._typings.domain import FlextTestTypesDomain\n\n\n"
            "class FlextTestTypes(t):\n"
            "    class Test(FlextTestTypesBase, FlextTestTypesDomain):\n"
            "        pass\n"
        )

    @staticmethod
    def valid_models_module() -> str:
        """Valid models module source following Rule 1/3."""
        return u.Tests.namespace_fixture("rule0_valid.py")

    @staticmethod
    def valid_utilities_module() -> str:
        """Valid utilities module source following Rule 3."""
        return (
            "from __future__ import annotations\n\n"
            "from flext_cli import u\n"
            "from flext_test import FlextTestUtilitiesCodegen\n\n"
            "class FlextTestUtilities(u):\n"
            "    class Test(FlextTestUtilitiesCodegen, FlextTestUtilitiesBase):\n"
            "        pass\n"
        )

    @staticmethod
    def valid_settings_module() -> str:
        """Valid settings module source with D1 carve-out."""
        return (
            "from __future__ import annotations\n\n"
            "from flext_test import m, t, u\n\n"
            "class FlextTestSettings(FlextTestSettingsBase):\n"
            "    class _Test(m.BaseModel):\n"
            "        bag: t.MappingKV[str, str] = m.Field(default_factory=dict)\n"
            "    @u.model_validator(mode='before')\n"
            "    @classmethod\n"
            "    def _lift(cls, data: t.JsonValue) -> t.JsonValue:\n"
            "        return data\n"
        )

    @staticmethod
    def settings_with_c_import() -> str:
        """Settings module with c import (operator ruling 2026-09-19)."""
        return (
            "from __future__ import annotations\n\n"
            "from flext_test import c\n\n"
            "class FlextTestSettings(FlextTestSettingsBase):\n"
            "    pass\n"
        )

    @staticmethod
    def runtime_module() -> str:
        """Generic runtime module (non-namespace)."""
        return (
            "from __future__ import annotations\n\n"
            "VALUE = 1\n\n"
            "def helper() -> int:\n"
            "    return VALUE\n"
        )

    @staticmethod
    def create_project(tmp_path: Path, *, module_source: str, module_name: str) -> Path:
        """Create a test project with a single module."""
        return u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name=module_name
        )

    @staticmethod
    def create_project_at_path(
        tmp_path: Path, *, module_source: str, module_path: str
    ) -> tuple[Path, Path]:
        """Create a test project at a specific module path."""
        return u.Tests.namespace_project_path(
            tmp_path, module_source=module_source, module_path=module_path
        )


__all__: list[str] = ["TestsFlextInfraNamespaceProjectFixture"]
