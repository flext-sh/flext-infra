"""Tests for Rule 3: Import rules (runtime vs TYPE_CHECKING)."""

from __future__ import annotations

from pathlib import Path

import pytest
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


class TestsRule3ImportRules:
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
            "    class Test(FlextTestUtilitiesCodegen, FlextTestUtilitiesBase):\n"
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
            "    class Test(FlextTestModelsDeps, FlextTestModelsBase):\n"
            "        pass\n"
        )
        root = _make_project_with_module(
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
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="_settings.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value))

    def test_rule3_settings_owner_c_import_still_flagged(self, tmp_path: Path) -> None:
        """D1 is bounded: ``c`` and operational facades are not covered."""
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "from flext_test import c\n\n"
            "class FlextTestSettings(FlextTestSettingsBase):\n"
            "    pass\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="_settings.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "reverse runtime import" in violation
                for violation in result.value.violations
            ),
            eq=True,
            msg=str(result.value),
        )


__all__: list[str] = ["TestsRule3ImportRules"]