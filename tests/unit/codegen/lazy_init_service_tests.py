"""Public service tests for lazy-init execution."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c
from tests import u


# NOTE (multi-agent, mro-wkii.17.15): prove scoped writes and read-only drift publicly.
class TestsFlextInfraCodegenLazyInitService:
    """Validate real service execution without mocks or internal branching asserts."""

    def test_execute_applies_only_selected_root_artifact_set(
        self, tmp_path: Path
    ) -> None:
        """Apply writes one initializer for exactly the selected package root."""
        _, selected_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-selected",
            package_name="flext_test_selected",
        )
        _, unrelated_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-unrelated",
            package_name="flext_test_unrelated",
        )
        u.Tests.write_lazy_init_namespace_module(
            selected_root / "models.py",
            class_name="FlextTestsSelectedModels",
            alias="m",
        )
        u.Tests.write_lazy_init_namespace_module(
            unrelated_root / "models.py",
            class_name="FlextTestsUnrelatedModels",
            alias="m",
        )
        unrelated_init = unrelated_root / c.Infra.INIT_PY
        unrelated_before = unrelated_init.read_bytes()
        service = u.Tests.create_lazy_init_service(tmp_path)
        service.target_module = "flext_test_selected"
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=True)
        tm.that((selected_root / c.Infra.INIT_PY).read_bytes(), ne=b"")
        tm.that((selected_root / "__unit__.py").exists(), eq=False)
        tm.that(unrelated_init.read_bytes(), eq=unrelated_before)
        tm.that((unrelated_root / "__unit__.py").exists(), eq=False)
        tm.that(service.modified_files, eq=(str(selected_root / c.Infra.INIT_PY),))

    def test_selected_root_reads_its_own_declared_public_contract(
        self, tmp_path: Path
    ) -> None:
        """Keep distinct root ABI declarations isolated across source roots."""
        workspace_root, selected_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-selected",
            package_name="flext_test_selected",
        )
        _, unrelated_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-unrelated",
            package_name="flext_test_unrelated",
        )
        selected_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__ = ["FlextTestsSelectedModels", "m"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        unrelated_init = unrelated_root / c.Infra.INIT_PY
        unrelated_init.write_text(
            '__all__ = ["FlextTestsUnrelatedModels", "m"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Tests.write_lazy_init_namespace_module(
            selected_root / "models.py",
            class_name="FlextTestsSelectedModels",
            alias="m",
        )
        u.Tests.write_lazy_init_namespace_module(
            unrelated_root / "models.py",
            class_name="FlextTestsUnrelatedModels",
            alias="m",
        )
        unrelated_before = unrelated_init.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "flext_test_selected"
        service.apply_changes = True

        result = service.execute()
        selected_generated = selected_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        tm.that(result.success, eq=True)
        tm.that(selected_generated, contains="FlextTestsSelectedModels")
        tm.that(selected_generated, lacks="FlextTestsUnrelatedModels")
        tm.that(unrelated_init.read_bytes(), eq=unrelated_before)

    def test_target_plans_private_children_without_writing_them(
        self, tmp_path: Path
    ) -> None:
        """A selected root consumes child plans while writing only its own init."""
        workspace_root, selected_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-selected",
            package_name="flext_test_selected",
        )
        u.Tests.write_lazy_init_namespace_module(
            selected_root / "models.py",
            class_name="FlextTestsSelectedModels",
            alias="m",
        )
        private_child = selected_root / "_utilities"
        private_child.mkdir()
        child_init = private_child / c.Infra.INIT_PY
        child_init.write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        child_init_before = child_init.read_bytes()
        private_child.joinpath("conversion.py").write_text(
            "class FlextTestsConversion:\n"
            '    """Established direct root import."""\n\n'
            '__all__ = ["FlextTestsConversion"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        selected_root.joinpath(c.Infra.INIT_PY).write_text(
            "_DIRECT_IMPORTS = (\n"
            '    "FlextTestsConversion",\n'
            '    "FlextTestsSelectedModels",\n'
            '    "build_lazy_import_map",\n'
            '    "install_lazy_exports",\n'
            '    "m",\n'
            ")\n"
            '__all__ = ["FlextTestsSelectedModels", "m"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "flext_test_selected"
        service.apply_changes = True

        result = service.execute()
        generated_root = selected_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        tm.that(result.success, eq=True)
        tm.that(generated_root, lacks="FlextTestsConversion")
        tm.that(child_init.read_bytes(), eq=child_init_before)
        tm.that(service.modified_files, eq=(str(selected_root / c.Infra.INIT_PY),))

    def test_explicit_wrapper_target_generates_only_that_initializer(
        self, tmp_path: Path
    ) -> None:
        """Generate a declared examples root without widening default scope."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        production_init = package_root / c.Infra.INIT_PY
        production_before = production_init.read_bytes()
        examples_root = workspace_root / c.Infra.DIR_EXAMPLES
        examples_root.mkdir()
        examples_init = examples_root / c.Infra.INIT_PY
        examples_init.write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        examples_root.joinpath("demo.py").write_text(
            'class ExamplesDemo:\n    """Example boundary."""\n\n'
            '__all__ = ["ExamplesDemo"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = c.Infra.DIR_EXAMPLES
        service.apply_changes = True

        result = service.execute()
        generated = examples_init.read_text(encoding=c.Cli.ENCODING_DEFAULT)

        tm.that(result.success, eq=True)
        tm.that(generated, lacks="from .demo import ExamplesDemo")
        tm.that(generated, lacks="ExamplesDemo")
        tm.that(generated, contains="__all__: tuple[str, ...] = ()")
        tm.that(production_init.read_bytes(), eq=production_before)
        tm.that(service.modified_files, eq=(str(examples_init),))

    def test_explicit_tests_target_generates_only_facade_exports(
        self, tmp_path: Path
    ) -> None:
        """Keep test aliases while excluding collected test classes."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        tests_root = workspace_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_init = tests_root / c.Infra.INIT_PY
        tests_init.write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        u.Tests.write_lazy_init_namespace_module(
            tests_root / "constants.py",
            class_name="TestsFlextTestsConstants",
            alias="c",
        )
        u.Tests.write_lazy_init_namespace_module(
            tests_root / "utilities.py",
            class_name="TestsFlextTestsUtilities",
            alias="u",
        )
        unit_root = tests_root / "unit"
        unit_root.mkdir()
        unit_root.joinpath(c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
        )
        unit_root.joinpath("test_noise.py").write_text(
            'class TestsCollectedNoise:\n    """Collected test class."""\n\n'
            '__all__ = ["TestsCollectedNoise"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = c.Infra.DIR_TESTS
        service.apply_changes = True

        result = service.execute()
        generated = tests_init.read_text(encoding=c.Cli.ENCODING_DEFAULT)

        tm.that(result.success, eq=True)
        tm.that(generated, contains="TestsFlextTestsConstants")
        tm.that(generated, contains="TestsFlextTestsUtilities")
        tm.that(generated, contains="install_lazy_exports")
        tm.that(generated, contains='"tm"')
        tm.that(generated, lacks="TestsCollectedNoise")
        tm.that(generated, lacks=".unit.test_noise")
        child_generated = unit_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(child_generated, contains="__all__: tuple[str, ...] = ()")
        tm.that(child_generated, lacks="TestsCollectedNoise")
        tm.that(child_generated, lacks="install_lazy_exports")

    def test_check_mode_is_read_only_and_reports_drift(self, tmp_path: Path) -> None:
        """Check reports missing generated artifacts as a failure without writing."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextTestsModels", alias="m"
        )
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "flext_test_project"
        service.check_only = True

        result = service.execute()

        tm.that(result.success, eq=False)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that((package_root / "__unit__.py").exists(), eq=False)
        tm.that(service.modified_files, eq=(str(init_path),))

    def test_dry_run_is_read_only_even_when_apply_is_requested(
        self, tmp_path: Path
    ) -> None:
        """Explicit dry-run wins over apply and reports drift without writing."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextTestsModels", alias="m"
        )
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "flext_test_project"
        service.apply_changes = True
        service.dry_run = True

        result = service.execute()

        tm.that(result.success, eq=False)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that((package_root / "__unit__.py").exists(), eq=False)
        tm.that(service.modified_files, eq=(str(init_path),))

    def test_second_check_is_byte_idempotent(self, tmp_path: Path) -> None:
        """A check after apply succeeds and preserves the generated initializer."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextTestsModels", alias="m"
        )
        init_path = package_root / c.Infra.INIT_PY
        apply_service = u.Tests.create_lazy_init_service(workspace_root)
        apply_service.target_module = "flext_test_project"
        apply_service.apply_changes = True

        apply_result = apply_service.execute()
        generated_init = init_path.read_bytes()
        check_service = u.Tests.create_lazy_init_service(workspace_root)
        check_service.target_module = "flext_test_project"
        check_service.check_only = True
        check_result = check_service.execute()

        tm.that(apply_result.success, eq=True)
        tm.that(check_result.success, eq=True)
        tm.that(check_service.modified_files, eq=())
        tm.that(init_path.read_bytes(), eq=generated_init)
        tm.that((package_root / "__unit__.py").exists(), eq=False)

    def test_unknown_target_fails_without_workspace_fallback(
        self, tmp_path: Path
    ) -> None:
        """An unknown target fails loudly instead of planning the full workspace."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py", class_name="FlextTestsModels", alias="m"
        )
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "flext_missing"
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=False)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that((package_root / "__unit__.py").exists(), eq=False)
        tm.that(service.modified_files, eq=())

    def test_ambiguous_target_fails_without_writing_either_project(
        self, tmp_path: Path
    ) -> None:
        """Duplicate package roots fail instead of selecting a collapsed map entry."""
        _, first_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-test-first", package_name="flext_shared"
        )
        _, second_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-test-second", package_name="flext_shared"
        )
        u.Tests.write_lazy_init_namespace_module(
            first_root / "models.py", class_name="FlextTestsFirstModels", alias="m"
        )
        u.Tests.write_lazy_init_namespace_module(
            second_root / "models.py", class_name="FlextTestsSecondModels", alias="m"
        )
        first_init = first_root / c.Infra.INIT_PY
        second_init = second_root / c.Infra.INIT_PY
        first_before = first_init.read_bytes()
        second_before = second_init.read_bytes()
        service = u.Tests.create_lazy_init_service(tmp_path)
        service.target_module = "flext_shared"
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=False)
        tm.that(first_init.read_bytes(), eq=first_before)
        tm.that(second_init.read_bytes(), eq=second_before)
        tm.that((first_root / "__unit__.py").exists(), eq=False)
        tm.that((second_root / "__unit__.py").exists(), eq=False)
        tm.that(service.modified_files, eq=())


__all__: list[str] = ["TestsFlextInfraCodegenLazyInitService"]
