"""Tests for Rule 0: Namespace structure and facade aliases."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import c, u

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


def _make_project_with_module_path(
    tmp_path: Path, *, module_source: str, module_path: str
) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    package_dir = project_root / "src" / "flext_test"
    package_dir.mkdir(parents=True)
    _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
    u.Tests.write_canonical_package_layout(package_dir)
    relative = Path(module_path)
    target = (
        project_root / relative
        if relative.parts[0] == c.Infra.DIR_TESTS
        else package_dir / relative
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_text(module_source, encoding="utf-8")
    u.Tests.initialize_git_repo(project_root)
    return project_root, target


class TestsRule0NamespaceStructure:
    """Test suite for namespace validator Rule 0."""

    @pytest.mark.parametrize("family", tuple(c.Infra.FAMILY_SUFFIXES))
    def test_required_public_facade_alias_passes(
        self, tmp_path: Path, family: str
    ) -> None:
        root = _make_project_with_module(
            tmp_path,
            module_source=_read_fixture("rule0_valid.py"),
            module_name="models.py",
        )
        layout = tm.not_none(u.Infra.layout(root))
        facade = layout.package_dir / c.Infra.FAMILY_FILES[family].lstrip("*")
        alias, suffix = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS[facade.name]
        class_name = f"{layout.class_stem}{suffix}"
        if family != "m":
            facade.write_text(
                facade.read_text(encoding="utf-8")
                + f"\n{alias} = {class_name}\n"
                + f"__all__ = [{class_name!r}, {alias!r}]\n",
                encoding="utf-8",
            )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=True, msg=str(report.violations))
        tm.that(report.violations, empty=True)

    @pytest.mark.parametrize(
        ("module_path", "assignment"),
        [
            ("models.py", "other = FlextTestModels"),
            ("models.py", "m = FlextTestModelsBase"),
            ("models.py", "m = FlextTestModels.Test"),
            ("models.py", "m = other = FlextTestModels"),
            ("models.py", "m, other = FlextTestModels, FlextTestModels"),
            ("models.py", "VALUE = 42"),
            ("models.py", "m = FlextTestModels\nother = FlextTestModels"),
            ("models.py", "m = FlextTestModels\nm = FlextTestModels"),
            ("_models/models.py", "m = FlextTestModels"),
            ("services/models.py", "m = FlextTestModels"),
        ],
    )
    def test_noncanonical_facade_assignments_still_fail(
        self, tmp_path: Path, module_path: str, assignment: str
    ) -> None:
        source = _read_fixture("rule0_valid.py").replace(
            "m = FlextTestModels", assignment
        )
        root, target = _make_project_with_module_path(
            tmp_path, module_source=source, module_path=module_path
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=False)
        tm.that(
            any(
                str(target.relative_to(root)) in violation
                and "module alias/data declaration is forbidden" in violation
                for violation in report.violations
            ),
            eq=True,
        )

    def test_facade_alias_before_class_is_not_canonical(self, tmp_path: Path) -> None:
        source = _read_fixture("rule0_valid.py").replace("m = FlextTestModels", "")
        source = source.replace(
            "class FlextTestModels(m):",
            "m = FlextTestModels\n\nclass FlextTestModels(m):",
        )
        root = _make_project_with_module(
            tmp_path, module_source=source, module_name="models.py"
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=False)
        tm.that(
            any("module alias/data declaration" in item for item in report.violations),
            eq=True,
        )

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
                violation.startswith("[NS-000")
                for violation in result.value.violations
            ),
            eq=False,
        )

    @pytest.mark.parametrize(
        ("module_source", "forbidden_violation_substr"),
        [
            pytest.param(
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n\n"
                "if TYPE_CHECKING:\n"
                "    from collections.abc import Sequence\n\n"
                "class FlextTestModels(Models):\n"
                "    pass\n",
                "Disallowed top-level statement: If",
                id="rule0-allows-type-checking-block",
            ),
            pytest.param(
                "from __future__ import annotations\n\n"
                "class FlextTestModels(Models):\n"
                "    pass\n\n"
                '__all__: list[str] = ["FlextTestModels"]\n',
                "Disallowed top-level statement: AnnAssign",
                id="rule0-allows-annotated-dunder-assign",
            ),
        ],
    )
    def test_rule0_allows_top_level_statement(
        self, tmp_path: Path, module_source: str, forbidden_violation_substr: str
    ) -> None:
        """Rule 0 never rejects the top-level statements a namespace may carry."""
        validator = FlextInfraNamespaceValidator()
        root = _make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                forbidden_violation_substr in violation
                for violation in result.value.violations
            ),
            eq=False,
        )


__all__: list[str] = ["TestsRule0NamespaceStructure"]
