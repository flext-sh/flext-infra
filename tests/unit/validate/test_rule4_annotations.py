"""Tests for Rule 4: Annotation rules."""

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


class TestsRule4Annotations:
    """Test suite for namespace validator Rule 4 (annotations)."""

    def test_rule4_annotated_field_factory_not_flagged_as_banned(
        self, tmp_path: Path
    ) -> None:
        """D1-precision: Annotated metadata factory values are not annotations.

        The canonical Flext<X>Settings pattern embeds the Pydantic field factory
        in the annotation metadata:
        ``Annotated[t.MappingKV[str, str], m.Field(default_factory=dict)]``.
        The ``dict`` there is a runtime factory value, not a type declaration,
        so NS-CONTRACT must not flag it.
        """
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "import typing\n\n"
            "from flext_test import m, t\n\n"
            "class FlextTestSettings:\n"
            "    default_headers: typing.Annotated["
            "t.MappingKV[str, str], m.Field(default_factory=dict)] = None\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="_settings.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            [v for v in result.value.violations if "NS-CONTRACT" in v],
            eq=[],
            msg=str(result.value),
        )

    def test_rule4_banned_annotation_still_flagged(self, tmp_path: Path) -> None:
        """D1-precision non-regression: genuine banned annotations are flagged."""
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "class FlextTestServices:\n"
            "    def transform(self, data: dict) -> object:\n"
            "        return data\n"
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="services.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                "banned annotation" in violation
                for violation in result.value.violations
            ),
            eq=True,
            msg=str(result.value),
        )

    def test_rule4_canonical_singleton_with_trailing_docstring_allowed(
        self, tmp_path: Path
    ) -> None:
        """D1-precision: canonical `api: Class = Class.fetch_global()` allows a trailing docstring.

        Mirrors the generated api.py.j2:20 singleton plus a hand-placed docstring
        (the flext-api api.py / _settings.py shape). A trailing module-alias
        declaration is still forbidden; only a docstring or ``__all__`` may follow.
        """
        validator = FlextInfraNamespaceValidator()
        module_source = (
            "from __future__ import annotations\n\n"
            "class FlextTest:\n"
            "    pass\n\n"
            "api: FlextTest = FlextTest.fetch_global()\n"
            '"""Global FlextTest facade instance."""\n'
            '__all__: list[str] = ["FlextTest", "api"]\n'
        )
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="api.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            not any(
                "module alias/data declaration" in v for v in result.value.violations
            ),
            eq=True,
            msg=str(result.value),
        )


__all__: list[str] = ["TestsRule4Annotations"]
