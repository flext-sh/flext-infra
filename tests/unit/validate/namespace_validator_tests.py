"""Tests for FlextInfraNamespaceValidator."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest
from flext_tests import tm

from flext_infra import config
from flext_infra.validate import FlextInfraNamespaceValidator
from tests import c, m, t, u


class TestsFlextInfraNamespaceValidator:
    """Test suite for namespace validator rules 0-3."""

    _FIXTURES_DIR: ClassVar[Path] = (
        Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"
    )

    @classmethod
    def _read_fixture(cls, name: str) -> str:
        fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name
        return (cls._FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")

    @classmethod
    def _make_project_with_module(
        cls, tmp_path: Path, *, module_source: str, module_name: str
    ) -> Path:
        root, _ = cls._make_project_with_module_path(
            tmp_path, module_source=module_source, module_path=module_name
        )
        return root

    @staticmethod
    def _make_project_with_module_path(
        tmp_path: Path, *, module_source: str, module_path: str
    ) -> t.Pair[Path, Path]:
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        # The validator grades the whole package, so the fixture is a package.
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

    @pytest.mark.parametrize("family", tuple(c.Infra.FAMILY_SUFFIXES))
    def test_required_public_facade_alias_passes(
        self, tmp_path: Path, family: str
    ) -> None:
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule0_valid.py"),
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
        source = self._read_fixture("rule0_valid.py").replace(
            "m = FlextTestModels", assignment
        )
        root, target = self._make_project_with_module_path(
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
        source = self._read_fixture("rule0_valid.py").replace("m = FlextTestModels", "")
        source = source.replace(
            "class FlextTestModels(m):",
            "m = FlextTestModels\n\nclass FlextTestModels(m):",
        )
        root = self._make_project_with_module(
            tmp_path, module_source=source, module_name="models.py"
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=False)
        tm.that(
            any("module alias/data declaration" in item for item in report.violations),
            eq=True,
        )

    @pytest.mark.parametrize(
        ("fixture_name", "legacy"),
        [
            ("pydantic_binding_callable_param_unimported.py", False),
            ("pydantic_binding_param_shadows_import.py", False),
            ("pydantic_binding_param_shadows_alias.py", False),
            ("pydantic_binding_local_assignment_shadows_import.py", False),
            ("pydantic_binding_nested_def_shadows_import.py", False),
            ("pydantic_binding_unrelated_decorator.py", False),
            ("pydantic_binding_unrelated_module_alias.py", False),
            ("pydantic_binding_validator_decorator.py", True),
            ("pydantic_binding_validator_alias_decorator.py", True),
            ("pydantic_binding_v1_root_validator_alias_call.py", True),
            ("pydantic_binding_root_validator_alias_bare.py", True),
            ("pydantic_binding_module_alias_validator.py", True),
            ("pydantic_binding_v1_module_alias_root_validator.py", True),
            ("pydantic_binding_local_import_call.py", True),
            ("pydantic_binding_unicode_line_call.py", True),
            ("pydantic_binding_field_validator_alias.py", False),
        ],
    )
    def test_pydantic_decorator_binding_provenance(
        self, tmp_path: Path, fixture_name: str, *, legacy: bool
    ) -> None:
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture(fixture_name),
            module_name="validation.py",
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=not legacy, msg=str(report.violations))
        tm.that(
            sum("legacy Pydantic member" in item for item in report.violations),
            eq=int(legacy),
        )

    @pytest.mark.parametrize(
        ("call", "legacy"),
        [
            ("response.json()", False),
            ("response.dict()", False),
            ("model.parse_obj({})", True),
            ("model.parse_raw(b'{}')", True),
        ],
    )
    def test_pydantic_method_detection_requires_unambiguous_member(
        self, tmp_path: Path, call: str, *, legacy: bool
    ) -> None:
        root = self._make_project_with_module(
            tmp_path,
            module_source=(
                "from __future__ import annotations\n\n"
                "class FlextTestClient:\n"
                "    def execute(self, response, model) -> None:\n"
                f"        {call}\n"
            ),
            module_name="client.py",
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(
            sum("legacy Pydantic member" in item for item in report.violations),
            eq=int(legacy),
        )

    def test_public_project_layout_uses_flext_for_core_exception(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "flext-core"
        package_dir = project_root / "src" / "flext_core"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        layout = u.Infra.layout(project_root)
        layout = tm.not_none(layout)
        tm.that(layout.class_stem, eq="Flext")

    def test_rule0_valid_module_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule0_valid.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    def test_validate_tracked_git_files(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        u.Tests.write_canonical_package_layout(package_dir)
        tracked_module = package_dir / "models.py"
        tracked_module.write_text(
            self._read_fixture("rule0_valid.py"), encoding="utf-8"
        )

        init_result = u.Cli.run_raw(["git", "init"], cwd=project_root)
        tm.ok(init_result)
        tm.that(u.Cli.process_succeeded(init_result.value.outcome), eq=True)
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"], cwd=project_root
        )
        tm.ok(email_result)
        tm.that(u.Cli.process_succeeded(email_result.value.outcome), eq=True)
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"], cwd=project_root
        )
        tm.ok(name_result)
        tm.that(u.Cli.process_succeeded(name_result.value.outcome), eq=True)
        add_result = u.Cli.run_raw(
            ["git", "add", "src/flext_test/models.py", "src/flext_test/__init__.py"],
            cwd=project_root,
        )
        tm.ok(add_result)
        tm.that(u.Cli.process_succeeded(add_result.value.outcome), eq=True)

        result = validator.validate_project(project_root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)

    def test_logical_loc_ceiling_reads_config_ssot(self, tmp_path: Path) -> None:
        """The per-module ceiling is the loc_cap SSOT, never a constant.

        The fixture size derives from the configured value, so this test
        tracks the SSOT instead of pinning either the old 200 or the current
        1000 number.
        """
        cap = config.Infra.codegen.loc_cap.max_lines
        assignments = "\n".join(
            f"        attr_{index} = {index}" for index in range(cap + 1)
        )
        module_source = self._read_fixture("rule0_valid.py").replace(
            "        pass\n", f"        pass\n{assignments}\n"
        )
        project_root = self._make_project_with_module(
            tmp_path, module_source=module_source, module_name="models.py"
        )

        result = FlextInfraNamespaceValidator().validate_project(project_root)

        tm.ok(result)
        locator = f"exceed the {cap} limit"
        tm.that(
            any(locator in violation for violation in result.value.violations), eq=True
        )

    @pytest.mark.parametrize(
        ("fixture_name", "module_name", "expected_violation_substr"),
        [
            pytest.param(
                "rule0_no_class.py",
                "models.py",
                "module must declare at least one top-level class; found 0",
                id="rule0-no-class",
            ),
            pytest.param(
                "rule0_wrong_prefix.py",
                "constants.py",
                "module must declare at least one class starting with 'FlextTest'",
                id="rule0-wrong-prefix",
            ),
            pytest.param(
                "rule0_loose_items.py",
                "models.py",
                "top-level function is forbidden; nest behavior in the module class",
                id="rule0-loose-items",
            ),
            pytest.param(
                "rule1_loose_constant.py",
                "models.py",
                "module alias/data declaration is forbidden; use the canonical "
                "facade class",
                id="rule1-loose-constant",
            ),
            pytest.param(
                "rule1_method_in_constants.py",
                "constants.py",
                "facade must inherit canonical 'c'",
                id="rule1-method-in-constants",
            ),
            pytest.param(
                "rule1_magic_number.py",
                "models.py",
                "module alias/data declaration is forbidden; use the canonical "
                "facade class",
                id="rule1-magic-number",
            ),
            pytest.param(
                "rule2_typevar_in_class.py",
                "typings.py",
                "facade must inherit canonical 't'",
                id="rule2-typevar-in-class",
            ),
            pytest.param(
                "rule2_typevar_wrong_module.py",
                "models.py",
                "module alias/data declaration is forbidden; use the canonical "
                "facade class",
                id="rule2-typevar-wrong-module",
            ),
            pytest.param(
                "rule2_composite_type_loose.py",
                "models.py",
                "module alias/data declaration is forbidden; use the canonical "
                "facade class",
                id="rule2-composite-type-loose",
            ),
            pytest.param(
                "rule2_protocol_in_types.py",
                "typings.py",
                "facade must declare one nested Test MRO",
                id="rule2-protocol-in-types",
            ),
        ],
    )
    def test_fixture_module_reports_its_violation(
        self,
        tmp_path: Path,
        fixture_name: str,
        module_name: str,
        expected_violation_substr: str,
    ) -> None:
        """Each namespace-rule fixture fails the project with its own message."""
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture(fixture_name),
            module_name=module_name,
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(not result.value.passed, eq=True)
        tm.that(
            any(
                expected_violation_substr in violation
                for violation in result.value.violations
            ),
            eq=True,
        )

    def test_rule1_valid_constants_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule1_valid_constants.py"),
            module_name="constants.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    def test_rule2_valid_types_passes(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule2_valid_types.py"),
            module_name="typings.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)

    @pytest.mark.parametrize(
        ("fixture_name", "module_name", "expected_violation_substr"),
        [
            (
                "rule3_reverse_runtime_import.py",
                "models.py",
                "reverse runtime import; later layers are TYPE_CHECKING-only: u",
            ),
            (
                "rule3_private_module_import.py",
                "detector.py",
                "import through the public facade, not 'flext_test._models.base'",
            ),
        ],
    )
    def test_rule3_direct_runtime_import_detected(
        self,
        tmp_path: Path,
        fixture_name: str,
        module_name: str,
        expected_violation_substr: str,
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture(fixture_name),
            module_name=module_name,
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
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule3_utilities_facade_import.py"),
            module_name="utilities.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True)

    def test_rule3_models_facade_import_remains_allowed(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule3_models_facade_import.py"),
            module_name="models.py",
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
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule3_settings_owner_facade_imports.py"),
            module_name="_settings.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value))

    def test_rule3_settings_owner_c_import_still_flagged(self, tmp_path: Path) -> None:
        """D1 is bounded: ``c`` and operational facades are not covered."""
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule3_settings_owner_c_import.py"),
            module_name="_settings.py",
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
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule4_annotated_field_factory.py"),
            module_name="_settings.py",
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
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule4_banned_annotation.py"),
            module_name="services.py",
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
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule4_singleton_trailing_docstring.py"),
            module_name="api.py",
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

    def test_rule0_does_not_flag_non_namespace_runtime_module(
        self, tmp_path: Path
    ) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule0_non_namespace_runtime_module.py"),
            module_name="api.py",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        tm.that(
            any(
                violation.startswith("[NS-000") for violation in result.value.violations
            ),
            eq=False,
        )

    def test_rule2_typevar_runtime_module_detected(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
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

    def test_initializer_and_version_roles_are_scanned(self, tmp_path: Path) -> None:
        """Role-specific validation must not pass because discovery is empty."""
        validator = FlextInfraNamespaceValidator()
        project_root = tmp_path / "project"
        package_dir = project_root / "src" / "flext_test"
        package_dir.mkdir(parents=True)
        _ = (package_dir / "__init__.py").write_text(
            self._read_fixture("rule0_no_class.py"), encoding="utf-8"
        )
        _ = (package_dir / "__version__.py").write_text(
            self._read_fixture("rule0_no_class.py"), encoding="utf-8"
        )
        u.Tests.write_canonical_package_layout(package_dir)
        u.Tests.initialize_git_repo(project_root)
        files = tm.ok(
            u.Infra.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(project_root,))
            )
        )
        tm.that(files, has=package_dir / "__init__.py")
        tm.that(files, has=package_dir / "__version__.py")
        result = validator.validate_project(project_root)
        tm.that(result.success, eq=True)
        tm.that(result.value.passed, eq=True)
        tm.that(result.value.violations, empty=True)
        tm.that(result.value.summary, has="files checked")

    def test_validate_returns_report(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule0_valid.py"),
            module_name="constants.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(result.value, is_=m.Infra.ValidationReport)
        tm.that(result.value.summary, has="files checked")

    def test_violation_message_format(self, tmp_path: Path) -> None:
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture("rule0_no_class.py"),
            module_name="models.py",
        )
        result = validator.validate_project(root)
        tm.that(result.success, eq=True)
        tm.that(len(result.value.violations), gt=0)
        first = result.value.violations[0]
        tm.that(first, has="[NS-STRUCT-")
        tm.that(first, has="] src/flext_test/models.py:1 — ")

    @pytest.mark.parametrize(
        ("fixture_id", "forbidden_violation_substr"),
        [
            pytest.param(case_id, substr, id=case_id)
            for case_id, substr in (
                (
                    "rule0-allows-type-checking-block",
                    "Disallowed top-level statement: If",
                ),
                (
                    "rule0-allows-annotated-dunder-assign",
                    "Disallowed top-level statement: AnnAssign",
                ),
            )
        ],
    )
    def test_rule0_allows_top_level_statement(
        self, tmp_path: Path, fixture_id: str, forbidden_violation_substr: str
    ) -> None:
        """Rule 0 never rejects the top-level statements a namespace may carry."""
        validator = FlextInfraNamespaceValidator()
        root = self._make_project_with_module(
            tmp_path,
            module_source=self._read_fixture(f"{fixture_id}.py"),
            module_name="models.py",
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

    @pytest.mark.parametrize(
        (
            "fixture_id",
            "module_path",
            "violation_substr",
            "expect_violation",
            "expect_passed",
        ),
        [
            pytest.param(*row, id=row[0])
            for row in (
                (
                    "rule1-skips-enum-inside-private-constants-dir",
                    "_constants/sample.py",
                    "Loose Enum 'Status' belongs in constants.py",
                    False,
                    None,
                ),
                (
                    "rule2-skips-typealias-inside-private-typings-dir",
                    "_typings/typeadapters.py",
                    "PEP 695 TypeAlias 'LocalAlias' belongs in typings.py",
                    False,
                    None,
                ),
                (
                    "rule3-skips-direct-imports-inside-private-dirs",
                    "_utilities/private_runtime.py",
                    "instead of direct import 'FlextTestModelsSomething'",
                    False,
                    None,
                ),
                (
                    "rule3-test-constants-facade-shape-required",
                    "tests/constants.py",
                    "facade must inherit canonical 'c'",
                    True,
                    False,
                ),
                (
                    "rule3-test-private-typings-nonfacade-passes",
                    "tests/_typings/domain.py",
                    "facade must inherit canonical",
                    False,
                    True,
                ),
                (
                    "rule3-test-type-checking-reverse-import-allowed",
                    "tests/typings.py",
                    "runtime namespace import",
                    False,
                    True,
                ),
                (
                    "rule3-test-facade-imports-tests-package",
                    "tests/models.py",
                    "facade must inherit canonical 'm'",
                    True,
                    False,
                ),
                (
                    "rule3-test-facade-imports-conftest",
                    "tests/models.py",
                    "facade must inherit canonical 'm'",
                    True,
                    False,
                ),
                (
                    "rule3-test-facade-imports-fixtures",
                    "tests/models.py",
                    "facade must inherit canonical 'm'",
                    True,
                    False,
                ),
                (
                    "rule3-test-facade-imports-test-module",
                    "tests/models.py",
                    "facade must inherit canonical 'm'",
                    True,
                    False,
                ),
                (
                    "rule3-test-models-forward-owner-assembly-allowed",
                    "tests/models.py",
                    "facade must inherit canonical",
                    False,
                    True,
                ),
                (
                    "rule3-test-utilities-forward-owner-assembly-allowed",
                    "tests/utilities.py",
                    "facade must inherit canonical",
                    False,
                    True,
                ),
                (
                    "rule3-test-matching-private-family-assembly-allowed",
                    "tests/models.py",
                    "test support module",
                    False,
                    True,
                ),
                (
                    "rule3-test-private-family-cross-import-passes",
                    "tests/_typings/domain.py",
                    "facade must inherit canonical",
                    False,
                    True,
                ),
            )
        ],
    )
    def test_module_path_violation_presence(
        self,
        tmp_path: Path,
        fixture_id: str,
        module_path: str,
        violation_substr: str,
        *,
        expect_violation: bool,
        expect_passed: bool | None,
    ) -> None:
        """Namespace rules key on the module path a project actually declares."""
        validator = FlextInfraNamespaceValidator()
        root, target = self._make_project_with_module_path(
            tmp_path,
            module_source=self._read_fixture(f"{fixture_id}.py"),
            module_path=module_path,
        )
        files = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(root,))
        )
        tm.ok(files)
        tm.that(
            target in files.value,
            eq=True,
            msg=f"namespace fixture omitted from source inventory: {target}; {files.value}",
        )

        result = validator.validate_project(root)

        tm.ok(result)
        if expect_passed is not None:
            tm.that(result.value.passed, eq=expect_passed, msg=str(result.value))
        tm.that(
            any(violation_substr in v for v in result.value.violations),
            eq=expect_violation,
        )


__all__: list[str] = ["TestsFlextInfraNamespaceValidator"]
