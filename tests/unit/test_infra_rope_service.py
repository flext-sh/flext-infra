"""Public behavior tests for the Rope workspace DSL service."""

from __future__ import annotations

from pathlib import Path

import pytest
from rope.base.exceptions import RopeError

import flext_infra
from flext_infra import (
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeInventory,
)
from tests import c, m, p, t, u


class TestsFlextInfraInfraRopeService:
    """Validate the public Rope workspace DSL through public methods only."""

    def test_open_workspace_materializes_snapshot(self, tmp_path: Path) -> None:
        """Public service class exposes one typed workspace snapshot."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextTestsModels",
            alias="m",
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
            exports = rope.exports(
                module_path,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_assignments": True
                }),
            )
            assert "FlextTestsModels" in exports
            assert "m" in exports
        finally:
            rope.close()

    def test_public_facade_opens_rope_workspace(self, tmp_path: Path) -> None:
        """Public facade returns the same ergonomic Rope workspace DSL."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            state = rope.semantic(module_path)
            assert any(
                class_info.name == "FlextTestsModels"
                for class_info in state.class_infos
            )

    def test_open_workspace_keeps_project_scope_with_sibling_projects(
        self,
        tmp_path: Path,
    ) -> None:
        """Project-root and package-root calls stay scoped to the containing project."""
        monorepo_root = tmp_path / "repo"
        monorepo_root.mkdir()
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            monorepo_root,
            project_name="flext-infra",
            package_name="flext_infra",
        )
        u.Tests.create_lazy_init_workspace(
            monorepo_root,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextInfraModels",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            assert rope.rope_workspace_root == workspace_root.resolve()
            assert {entry.project_root for entry in rope.modules()} == {
                workspace_root.resolve()
            }

        with flext_infra.infra.rope_workspace(package_root) as rope:
            assert rope.rope_workspace_root == workspace_root.resolve()
            assert {entry.project_root for entry in rope.modules()} == {
                workspace_root.resolve()
            }

    def test_workspace_exports_fixture_functions_when_requested(
        self,
        tmp_path: Path,
    ) -> None:
        """Fixture modules can publish pytest fixtures through the Rope DSL."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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
            exports = rope.exports(
                fixture_module,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_functions": True
                }),
            )

        assert "reset_settings" in exports
        assert "settings_factory" in exports

    def test_workspace_dsl_centralizes_project_and_module_conventions(
        self,
        tmp_path: Path,
    ) -> None:
        """Public Rope DSL centralizes project discovery and module naming rules."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
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
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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

    def test_workspace_dsl_reload_refreshes_cached_objects(
        self, tmp_path: Path
    ) -> None:
        """Reload drops Rope caches and reflects updated module objects."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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

    def test_workspace_refresh_can_preserve_reverted_name_indexes(
        self,
        tmp_path: Path,
    ) -> None:
        """Refresh can retain the text index after preview-style reverted writes."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        original_source = (
            "from __future__ import annotations\n\ndef first() -> int:\n    return 1\n"
        )
        changed_source = (
            "from __future__ import annotations\n\n"
            "def first() -> int:\n"
            "    return 1\n\n"
            "def second() -> int:\n"
            "    return first()\n"
        )
        module_path.write_text(original_source, encoding="utf-8")

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            original_index = rope.name_index()
            assert "first" in original_index
            assert "second" not in original_index

            module_path.write_text(changed_source, encoding="utf-8")
            module_path.write_text(original_source, encoding="utf-8")
            rope.refresh(preserve_indexes=True)

            preserved_index = rope.name_index()
            assert preserved_index is original_index
            assert "second" not in preserved_index

            module_path.write_text(changed_source, encoding="utf-8")
            rope.refresh()

            rebuilt_index = rope.name_index()
            assert rebuilt_index is not original_index
            assert "second" in rebuilt_index

    def test_workspace_objects_raise_on_inventory_bootstrap_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Inventory bootstrap failures surface instead of pretending the module is empty."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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

        def _explode(*args: object, **kwargs: object) -> object:
            msg = "boom"
            raise RopeError(msg)

        monkeypatch.setattr(
            u.Infra,
            "get_pymodule",
            staticmethod(_explode),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError,
                match=r"rope inventory failed to load .*service\.py",
            ):
                rope.objects(module_path)

    def test_workspace_name_index_raises_on_module_read_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Name index failures surface instead of quietly dropping unreadable modules."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def public() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )
        original_read_text = type(module_path).read_text

        def _broken_read_text(
            path: Path,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> str:
            if path.resolve() == module_path.resolve():
                msg = "boom"
                raise OSError(msg)
            text: str = original_read_text(
                path,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
            return text

        monkeypatch.setattr(type(module_path), "read_text", _broken_read_text)

        with flext_infra.FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError,
                match=r"rope name index failed to read .*service\.py",
            ):
                rope.name_index()

    def test_workspace_objects_raise_on_indexed_resource_lookup_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Indexed reference search must fail loudly when a referenced module resource vanishes."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        service_path = package_root / "service.py"
        service_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def public() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )
        consumer_path = package_root / "consumer.py"
        consumer_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from flext_demo.service import public\n\n"
                "def consume() -> int:\n"
                "    return public()\n"
            ),
            encoding="utf-8",
        )
        original_resource = flext_infra.FlextInfraRopeWorkspace.resource

        def _broken_resource(
            rope: flext_infra.FlextInfraRopeWorkspace,
            file_path: Path,
        ) -> t.Infra.RopeResource | None:
            if file_path.resolve() == consumer_path.resolve():
                return None
            return original_resource(rope, file_path)

        monkeypatch.setattr(
            flext_infra.FlextInfraRopeWorkspace,
            "resource",
            _broken_resource,
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError,
                match=r"rope search resource unavailable for indexed path .*consumer\.py",
            ):
                rope.objects(service_path, include_local_scopes=False)

    def test_indexed_search_raises_on_invalid_import_dependents_result(
        self,
        tmp_path: Path,
    ) -> None:
        """Indexed dependency narrowing must reject invalid import_dependents payloads."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        examples_dir = workspace_root / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)
        example_path = examples_dir / "demo.py"
        example_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def helper() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )
        consumer_path = examples_dir / "consumer.py"
        consumer_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from demo import helper\n\n"
                "def consume() -> int:\n"
                "    return helper()\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(example_path)
            assert resource is not None

            class _BrokenWorkspace:
                def name_index(
                    self,
                ) -> t.MappingKV[str, tuple[tuple[Path, str, tuple[int, ...]], ...]]:
                    return rope.name_index()

                def resource(
                    self,
                    file_path: Path,
                ) -> t.Infra.RopeResource | None:
                    return rope.resource(file_path)

                def import_dependents(self, import_target: str) -> object:
                    del import_target
                    return object()

            with pytest.raises(
                TypeError,
                match=r"rope import_dependents returned non-tuple for demo",
            ):
                FlextInfraUtilitiesRopeImports.indexed_search_resources(
                    _BrokenWorkspace(),
                    resource=resource,
                    name="helper",
                    definition_path=example_path,
                    dependent_import_targets=("demo", "demo.helper"),
                )

    def test_workspace_dsl_classifies_test_only_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Public census objects keep runtime and test reference counts separate."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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

    def test_workspace_dsl_skips_reference_scan_for_facade_members(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Governed facade members skip expensive reference collection."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "class FlextDemoModels:\n"
                "    pass\n\n"
                "m = FlextDemoModels\n"
            ),
            encoding="utf-8",
        )

        def _explode(*args: object, **kwargs: object) -> object:
            msg = "facade members should not trigger reference scanning"
            raise AssertionError(msg)

        monkeypatch.setattr(
            FlextInfraUtilitiesRopeInventory,
            "_reference_sites",
            staticmethod(_explode),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.name: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        assert objects["FlextDemoModels"].is_facade_member
        assert objects["m"].is_facade_member

    def test_workspace_dsl_skips_reference_scan_for_private_names(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Private and dunder names do not trigger removal-only reference scans."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                '__all__: list[str] = ["public"]\n\n'
                "def public() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )

        original = FlextInfraUtilitiesRopeInventory._reference_sites
        seen_names: list[str] = []

        def _tracking(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
            *,
            source: str,
            module_name: str,
            name: str,
            line: int,
            rope_workspace: p.AttributeProbe | None = None,
        ) -> tuple[
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
            tuple[m.Infra.Census.ReferenceSite, ...],
        ]:
            seen_names.append(name)
            return original(
                rope_project,
                resource,
                source=source,
                module_name=module_name,
                name=name,
                line=line,
                rope_workspace=rope_workspace,
            )

        monkeypatch.setattr(
            FlextInfraUtilitiesRopeInventory,
            "_reference_sites",
            staticmethod(_tracking),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.name: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        assert "__all__" in objects
        assert objects["__all__"].references_count == 0
        assert "__all__" not in seen_names
        assert "public" in seen_names

    def test_workspace_dsl_tracks_example_importers_for_generic_names(
        self,
        tmp_path: Path,
    ) -> None:
        """Generic example names keep example references after resource narrowing."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        examples_dir = workspace_root / c.Infra.DIR_EXAMPLES
        examples_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
        producer_path = examples_dir / "producer.py"
        consumer_path = examples_dir / "consumer.py"
        producer_path.write_text(
            ("from __future__ import annotations\n\ndef run() -> int:\n    return 1\n"),
            encoding="utf-8",
        )
        consumer_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from examples.producer import run\n\n"
                "VALUE = run()\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(
                    producer_path,
                    include_local_scopes=False,
                )
            }

        candidate = objects["run"]
        assert candidate.references_count == 2
        assert candidate.runtime_references_count == 0
        assert candidate.test_references_count == 0
        assert candidate.example_references_count == 2
        assert candidate.script_references_count == 0
        assert {site.file_path for site in candidate.example_reference_sites} == {
            str(consumer_path)
        }
        assert sorted(site.line for site in candidate.example_reference_sites) == [3, 5]

    def test_workspace_dsl_tracks_example_base_class_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Example facade subclassing keeps shared base classes out of unused candidates."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        examples_dir = workspace_root / c.Infra.DIR_EXAMPLES
        models_dir = examples_dir / "_models"
        models_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
        (models_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
        shared_path = models_dir / "shared.py"
        shared_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "class ExampleSharedPerson:\n"
                "    pass\n"
            ),
            encoding="utf-8",
        )
        facade_path = examples_dir / "models.py"
        facade_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from examples._models.shared import ExampleSharedPerson\n\n"
                "class ExamplesModels:\n"
                "    class Person(ExampleSharedPerson):\n"
                "        pass\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(
                    shared_path,
                    include_local_scopes=False,
                )
            }

        candidate = objects["ExampleSharedPerson"]
        assert candidate.references_count == 2
        assert candidate.runtime_references_count == 0
        assert candidate.test_references_count == 0
        assert candidate.example_references_count == 2
        assert candidate.script_references_count == 0
        assert {site.file_path for site in candidate.example_reference_sites} == {
            str(facade_path)
        }
        assert sorted(site.line for site in candidate.example_reference_sites) == [3, 6]

    def test_workspace_dsl_tracks_same_file_references(self, tmp_path: Path) -> None:
        """Same-file uses must block the unused fast-path shortcut."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "class ExampleService:\n"
                "    pass\n\n"
                "DEFAULT_SERVICE = ExampleService()\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(
                    module_path,
                    include_local_scopes=False,
                )
            }

        candidate = objects["ExampleService"]
        assert candidate.references_count == 1
        assert candidate.runtime_references_count == 1
        assert candidate.test_references_count == 0
        assert candidate.example_references_count == 0
        assert candidate.script_references_count == 0
        assert {site.file_path for site in candidate.runtime_reference_sites} == {
            str(module_path)
        }
        assert [site.line for site in candidate.runtime_reference_sites] == [6]
