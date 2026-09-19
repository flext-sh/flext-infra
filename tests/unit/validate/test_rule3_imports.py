"""Tests for Rule 3: Import rules (runtime vs TYPE_CHECKING)."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsFlextInfraRule3ImportRules:
    """Test suite for the namespace validator rule under test."""

    """Test suite for namespace validator Rule 3 (import rules)."""

    @pytest.mark.parametrize(
        ("module_source", "module_name", "expected_violation_substr"),
        [
            (
                (
                    "from __future__ import annotations\n"
                    "from flext_test import u\n\n"
                    "class FlextTestModels(Models):\n"
                    "    pass\n"
                ),
                "models.py",
                "reverse runtime import; later layers are TYPE_CHECKING-only: u",
            ),
            (
                (
                    "from __future__ import annotations\n"
                    "from flext_test._models.base import FlextTestModelsDeps\n\n"
                    "class FlextTestDetector:\n"
                    "    pass\n"
                ),
                "detector.py",
                "import through the public facade, not 'flext_test._models.base'",
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
        root = u.Tests.namespace_project(
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
            "    class Test(FlextTestUtilitiesCodegen, FlextTestUtilitiesBase):\n"
            "        pass\n"
        )
        root = u.Tests.namespace_project(
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
            "    class Test(FlextTestModelsDeps, FlextTestModelsBase):\n"
            "        pass\n"
        )
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)

    def test_rule3_settings_owner_declaration_facade_runtime_imports_allowed(
        self, tmp_path: Path
    ) -> None:
        """D1 carve-out: settings/config owners may runtime-import m/t/u.

        Nested Pydantic namespace-models in ``_settings.py`` require
        ``BaseModel``/``Field``/``MappingKV``/``model_validator``/``JsonValue``
        from the declaration facades at runtime; the fleet's canonical pattern
        (flext-auth/_settings.py, flext-api/_settings.py) depends on this.
        """
        validator = FlextInfraNamespaceValidator()
        module_source = (
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
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name="_settings.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value))

    def test_rule3_settings_owner_c_import_allowed(self, tmp_path: Path) -> None:
        """Operator ruling 2026-09-19: settings defaults read declared constants.

        Settings owners bind Pydantic field defaults to ``c.<Ns>.CONSTANT``, so
        the runtime ``c`` import is part of the declaration-layer carve-out;
        operational facades stay flagged.
        """
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_test import c\n\n"
            "class FlextTestSettings(FlextTestSettingsBase):\n"
            "    pass\n"
        )
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name="_settings.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "reverse runtime import" in violation
                for violation in result.value.violations
            ),
            eq=False,
            msg=str(result.value),
        )


__all__: list[str] = ["TestsFlextInfraRule3ImportRules"]
