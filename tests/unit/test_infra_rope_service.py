"""Public behavior tests for the Rope workspace DSL service."""

from __future__ import annotations

from pathlib import Path

import flext_infra
from tests import c, u


class TestFlextInfraRopeWorkspace:
    """Validate the public Rope workspace DSL through public methods only."""

    def test_open_workspace_materializes_snapshot(self, tmp_path: Path) -> None:
        """Public service class exposes one typed workspace snapshot."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        rope = flext_infra.FlextInfraRopeWorkspace.open_workspace(workspace_root)
        try:
            snapshot_result = rope.execute()
            assert snapshot_result.success
            snapshot = snapshot_result.unwrap()
            assert snapshot.workspace_root == workspace_root.resolve()
            assert package_root in snapshot.workspace_index.package_dirs
            assert rope.module(module_path) is not None
            assert rope.package(package_root) is not None
            exports = rope.exports(module_path, allow_assignments=True)
            assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in exports
            assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS in exports
        finally:
            rope.close()

    def test_public_facade_opens_rope_workspace(self, tmp_path: Path) -> None:
        """Public facade returns the same ergonomic Rope workspace DSL."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            state = rope.semantic(module_path)
            assert any(
                class_info.name == c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS
                for class_info in state.class_infos
            )

    def test_workspace_exports_fixture_functions_when_requested(
        self,
        tmp_path: Path,
    ) -> None:
        """Fixture modules can publish pytest fixtures through the Rope DSL."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        fixtures_dir = package_root / "_fixtures"
        fixtures_dir.mkdir()
        fixture_module = fixtures_dir / "settings.py"
        fixture_module.write_text(
            "from __future__ import annotations\n\n"
            "def reset_settings() -> None:\n"
            "    return None\n\n"
            "def settings_factory() -> None:\n"
            "    return None\n",
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            exports = rope.exports(fixture_module, allow_functions=True)

        assert "reset_settings" in exports
        assert "settings_factory" in exports

    def test_workspace_dsl_centralizes_project_and_module_conventions(
        self,
        tmp_path: Path,
    ) -> None:
        """Public Rope DSL centralizes project discovery and module naming rules."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            projects = rope.projects()
            assert len(projects) == 1
            assert projects[0].name == "flext-demo"

            layout = rope.layout(workspace_root)
            assert layout is not None
            assert layout.project_name == "flext-demo"
            assert layout.package_name == "flext_demo"
            assert layout.package_alias == "demo"
            assert layout.class_stem == "FlextDemo"
            assert layout.package_dir == package_root
            assert layout.runtime_aliases == ("m",)

            convention = rope.convention(module_path)
            assert convention.module_name == "flext_demo.models"
            assert convention.package_name == "flext_demo"
            assert convention.package_context.current_pkg == "flext_demo"
            assert convention.module_policy.expected_alias == "m"
            assert convention.project_layout is not None
            assert convention.project_layout.class_stem == "FlextDemo"

    def test_workspace_dsl_exposes_direct_modules_source_and_objects(
        self,
        tmp_path: Path,
    ) -> None:
        """Public Rope DSL returns direct module inventory through census objects."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "VALUE = 1\n\n"
                "class FlextDemoModels:\n"
                "    FLAG = VALUE\n\n"
                "    def build(self, payload: int) -> int:\n"
                "        local = payload + VALUE\n\n"
                "        def nested(extra: int) -> int:\n"
                "            return local + extra\n\n"
                "        return nested(1)\n\n"
                "m = FlextDemoModels\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            assert any(entry.file_path == module_path for entry in rope.modules())
            assert "class FlextDemoModels" in rope.source(module_path)
            objects = {
                (item.scope_path, item.kind): item for item in rope.objects(module_path)
            }
            assert ("VALUE", "constant") in objects
            assert ("FlextDemoModels", "class") in objects
            assert ("FlextDemoModels.build", "method") in objects
            assert ("FlextDemoModels.build.payload", "parameter") in objects
            assert ("FlextDemoModels.build.local", "local") in objects
            assert ("FlextDemoModels.build.nested", "function") in objects
            assert objects["FlextDemoModels", "class"].is_facade_member
            assert objects["FlextDemoModels.build.local", "local"].references_count >= 1

    def test_workspace_dsl_reload_refreshes_cached_objects(
        self, tmp_path: Path
    ) -> None:
        """Reload drops Rope caches and reflects updated module objects."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def first() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            assert {item.name for item in rope.objects(module_path)} == {"first"}
            module_path.write_text(
                (
                    "from __future__ import annotations\n\n"
                    "def first() -> int:\n"
                    "    return 1\n\n"
                    "def second() -> int:\n"
                    "    return first()\n"
                ),
                encoding="utf-8",
            )
            rope.reload()
            assert {item.name for item in rope.objects(module_path)} == {
                "first",
                "second",
            }

    def test_workspace_dsl_classifies_test_only_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Public census objects keep runtime and test reference counts separate."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def only_for_tests(value: int) -> int:\n"
                "    return value + 1\n"
            ),
            encoding="utf-8",
        )
        test_path = workspace_root / "tests" / "test_service.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from flext_demo.service import only_for_tests\n\n"
                "def test_only_for_tests_returns_incremented_value() -> None:\n"
                "    assert only_for_tests(1) == 2\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        candidate = objects["only_for_tests"]
        assert candidate.references_count == 2
        assert candidate.runtime_references_count == 0
        assert candidate.test_references_count == 2
        assert candidate.example_references_count == 0
        assert candidate.script_references_count == 0
        assert len(candidate.test_reference_sites) == 2
        assert sorted(site.line for site in candidate.test_reference_sites) == [3, 6]
        assert {site.file_path for site in candidate.test_reference_sites} == {
            str(test_path)
        }
        assert {site.surface for site in candidate.test_reference_sites} == {
            c.Infra.DIR_TESTS
        }
