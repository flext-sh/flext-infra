"""Public service tests for lazy-init execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, u


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

    def test_project_selection_without_module_updates_only_selected_project(
        self, tmp_path: Path
    ) -> None:
        """Filter writes by project while retaining one workspace Rope index."""
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
        service.selected_projects = ("flext-test-selected",)
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=True)
        tm.that((selected_root / c.Infra.INIT_PY).read_bytes(), ne=b"")
        tm.that(unrelated_init.read_bytes(), eq=unrelated_before)
        tm.that(service.modified_files, eq=(str(selected_root / c.Infra.INIT_PY),))

    def test_target_generates_private_descendant_initializers(
        self, tmp_path: Path
    ) -> None:
        """Generate every initializer below an explicitly selected facade."""
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
        # mro-wkii.17.26 (Codex): descendants own their static exports.
        tm.that(generated_root, lacks="FlextTestsConversion")
        tm.that(
            child_init.read_text(encoding=c.Cli.ENCODING_DEFAULT),
            contains=(
                "from .conversion import FlextTestsConversion as FlextTestsConversion"
            ),
        )
        tm.that(
            service.modified_files,
            eq=(str(selected_root / c.Infra.INIT_PY), str(child_init)),
        )

    def test_nested_target_updates_only_selected_initializer(
        self, tmp_path: Path
    ) -> None:
        """Keep descendant drift untouched for an exact nested target."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        tests_root = workspace_root / c.Infra.DIR_TESTS
        unit_root = tests_root / "unit"
        child_root = unit_root / "child"
        child_root.mkdir(parents=True)
        for package_root in (tests_root, unit_root, child_root):
            package_root.joinpath(c.Infra.INIT_PY).write_text(
                "", encoding=c.Cli.ENCODING_DEFAULT
            )
        unit_root.joinpath("constants.py").write_text(
            "class TestsUnitConstants:\n"
            '    """Nested target export."""\n\n'
            '__all__ = ["TestsUnitConstants"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        child_init = child_root / c.Infra.INIT_PY
        child_before = child_init.read_bytes()
        child_root.joinpath("models.py").write_text(
            "class TestsChildModels:\n"
            '    """Unrelated descendant export."""\n\n'
            '__all__ = ["TestsChildModels"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.target_module = "tests.unit"
        service.apply_changes = True

        result = service.execute()
        unit_init = unit_root.joinpath(c.Infra.INIT_PY)

        tm.that(result.success, eq=True)
        tm.that(
            unit_init.read_text(encoding=c.Cli.ENCODING_DEFAULT),
            contains="from .constants import TestsUnitConstants",
        )
        tm.that(child_init.read_bytes(), eq=child_before)
        tm.that(service.modified_files, eq=(str(unit_init),))

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
        # mro-wkii.17.26.2 (codex): every declared wrapper has one lazy root;
        # static identity imports begin only below this boundary.
        tm.that(generated, contains='".demo": ("ExamplesDemo",)')
        tm.that(generated, contains='__all__: tuple[str, ...] = ("ExamplesDemo",)')
        tm.that(generated, contains="_install_lazy_exports(")
        tm.that(production_init.read_bytes(), eq=production_before)
        tm.that(service.modified_files, eq=(str(examples_init),))

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

    def test_child_and_root_targets_render_byte_identical_static_init(
        self, tmp_path: Path
    ) -> None:
        """Keep one static child byte-identical across surgical and root runs."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        models_root = package_root / "_models"
        models_root.mkdir()
        models_init = models_root / c.Infra.INIT_PY
        models_init.write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        models_root.joinpath("_auth.py").write_text(
            "class FlextTestsModelsAuth:\n"
            '    """Generated static export."""\n\n'
            '__all__ = ["FlextTestsModelsAuth"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        child_service = u.Tests.create_lazy_init_service(workspace_root)
        child_service.target_module = "flext_test_project._models"
        child_service.apply_changes = True

        child_result = child_service.execute()
        child_bytes = models_init.read_bytes()
        root_service = u.Tests.create_lazy_init_service(workspace_root)
        root_service.target_module = "flext_test_project"
        root_service.apply_changes = True
        root_result = root_service.execute()
        check_service = u.Tests.create_lazy_init_service(workspace_root)
        check_service.target_module = "flext_test_project"
        check_service.check_only = True
        check_result = check_service.execute()

        tm.that(child_result.success, eq=True)
        tm.that(
            child_bytes.decode(c.Cli.ENCODING_DEFAULT),
            contains=(
                "from ._auth import FlextTestsModelsAuth as FlextTestsModelsAuth"
            ),
        )
        tm.that(root_result.success, eq=True)
        tm.that(models_init.read_bytes(), eq=child_bytes)
        tm.that(str(models_init) in root_service.modified_files, eq=False)
        tm.that(check_result.success, eq=True)
        tm.that(check_service.modified_files, eq=())

    def test_unknown_selected_project_fails_loudly(self, tmp_path: Path) -> None:
        """Reject an unknown project instead of widening to the workspace."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        init_path = package_root / c.Infra.INIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)
        service.selected_projects = ("flext-missing",)
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=False)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that(service.modified_files, eq=())

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

    def test_project_selection_qualifies_repeated_wrapper_target(
        self, tmp_path: Path
    ) -> None:
        """Select one project's wrapper without touching an identically named peer."""
        first_project, _first_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-test-first", package_name="flext_test_first"
        )
        second_project, _second_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-test-second", package_name="flext_test_second"
        )
        first_tests = first_project / c.Infra.DIR_TESTS
        second_tests = second_project / c.Infra.DIR_TESTS
        for tests_root, class_name in (
            (first_tests, "TestsFlextFirstConstants"),
            (second_tests, "TestsFlextSecondConstants"),
        ):
            tests_root.mkdir()
            tests_root.joinpath(c.Infra.INIT_PY).write_text(
                "", encoding=c.Cli.ENCODING_DEFAULT
            )
            tests_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
                f'class {class_name}:\n    pass\n\n__all__ = ["{class_name}"]\n',
                encoding=c.Cli.ENCODING_DEFAULT,
            )
        second_before = second_tests.joinpath(c.Infra.INIT_PY).read_bytes()
        service = u.Tests.create_lazy_init_service(tmp_path)
        service.target_module = c.Infra.DIR_TESTS
        service.selected_projects = ("flext-test-first",)
        service.apply_changes = True

        result = service.execute()

        tm.that(result.success, eq=True)
        tm.that(
            first_tests.joinpath(c.Infra.INIT_PY).read_text(
                encoding=c.Cli.ENCODING_DEFAULT
            ),
            contains="TestsFlextFirstConstants",
        )
        tm.that(second_tests.joinpath(c.Infra.INIT_PY).read_bytes(), eq=second_before)
        tm.that(service.modified_files, eq=(str(first_tests / c.Infra.INIT_PY),))


__all__: list[str] = ["TestsFlextInfraCodegenLazyInitService"]
