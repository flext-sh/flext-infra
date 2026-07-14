"""Public behavior tests for the Rope workspace DSL service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import flext_infra
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra.workspace.rope import FlextInfraRopeWorkspace
from tests import c
from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p
    from tests import t


class TestsFlextInfraInfraRopeService:
    """Validate the public Rope workspace DSL through public methods only."""

    def test_open_workspace_materializes_snapshot(self, tmp_path: Path) -> None:
        """Public service class exposes one typed workspace snapshot."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path, class_name="FlextTestsModels", alias="m", docstring="Models."
        )

        rope = FlextInfraRopeWorkspace.open_workspace(workspace_root)
        try:
            snapshot_result = rope.execute()
            tm.ok(snapshot_result)
            snapshot = snapshot_result.unwrap()
            tm.that(snapshot.workspace_root, eq=workspace_root.resolve())
            tm.that(snapshot.workspace_index.package_dirs, has=package_root)
            tm.that(rope.module(module_path), none=False)
            tm.that(rope.package(package_root), none=False)
            exports = rope.exports(
                module_path,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_assignments": True
                }),
            )
            tm.that(exports, has="FlextTestsModels")
            tm.that(exports, has="m")
        finally:
            rope.close()

    def test_public_facade_opens_rope_workspace(self, tmp_path: Path) -> None:
        """Public facade returns the same ergonomic Rope workspace DSL."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path, class_name="FlextTestsModels", alias="m", docstring="Models."
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            state = rope.semantic(module_path)
            assert any(
                class_info.name == "FlextTestsModels"
                for class_info in state.class_infos
            )

    def test_open_workspace_indexes_parent_workspace_from_each_member(
        self, tmp_path: Path
    ) -> None:
        """Member invocations share the complete enclosing workspace index."""
        monorepo_root = tmp_path / "repo"
        monorepo_root.mkdir()
        (monorepo_root / ".gitmodules").write_text(
            (
                '[submodule "flext-infra"]\n'
                "\tpath = flext-infra\n"
                "\turl = ../flext-infra.git\n"
                '[submodule "flext-demo"]\n'
                "\tpath = flext-demo\n"
                "\turl = ../flext-demo.git\n"
            ),
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        infra_root, package_root = u.Tests.create_lazy_init_workspace(
            monorepo_root, project_name="flext-infra", package_name="flext_infra"
        )
        demo_root, _demo_package_root = u.Tests.create_lazy_init_workspace(
            monorepo_root, project_name="flext-demo", package_name="flext_demo"
        )
        indexed_paths: set[Path] = set()
        for project_root in (infra_root, demo_root):
            test_path = project_root / "tests" / "test_public.py"
            example_path = project_root / "examples" / "public_usage.py"
            test_path.parent.mkdir()
            example_path.parent.mkdir()
            test_path.write_text(
                "def test_public() -> None:\n    pass\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            example_path.write_text(
                "def public_usage() -> None:\n    pass\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            indexed_paths.update({test_path.resolve(), example_path.resolve()})
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path, class_name="FlextInfraModels", alias="m", docstring="Models."
        )

        with flext_infra.infra.rope_workspace(infra_root) as rope:
            tm.that(rope.rope_workspace_root, eq=monorepo_root.resolve())
            tm.that(
                {entry.project_root for entry in rope.modules()},
                eq={infra_root.resolve(), demo_root.resolve()},
            )
            tm.that(
                indexed_paths.issubset({entry.file_path for entry in rope.modules()}),
                eq=True,
            )

        with flext_infra.infra.rope_workspace(package_root) as rope:
            tm.that(rope.rope_workspace_root, eq=monorepo_root.resolve())
            tm.that(
                {entry.project_root for entry in rope.modules()},
                eq={infra_root.resolve(), demo_root.resolve()},
            )

    def test_workspace_exports_fixture_functions_when_requested(
        self, tmp_path: Path
    ) -> None:
        """Fixture modules can publish pytest fixtures through the Rope DSL."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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

        tm.that(exports, has="reset_settings")
        tm.that(exports, has="settings_factory")

    def test_workspace_dsl_centralizes_project_and_module_conventions(
        self, tmp_path: Path
    ) -> None:
        """Public Rope DSL centralizes project discovery and module naming rules."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path, class_name="FlextDemoModels", alias="m", docstring="Models."
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            projects = rope.projects()
            tm.that(len(projects), eq=1)
            tm.that(projects[0].name, eq="flext-demo")

            layout = rope.layout(workspace_root)
            tm.that(layout, none=False)
            tm.that(layout.project_name, eq="flext-demo")
            tm.that(layout.package_name, eq="flext_demo")
            tm.that(layout.package_alias, eq="demo")
            tm.that(layout.class_stem, eq="FlextDemo")
            tm.that(layout.package_dir, eq=package_root)
            tm.that(layout.runtime_aliases, eq=("m",))

            convention = rope.convention(module_path)
            tm.that(convention.module_name, eq="flext_demo.models")
            tm.that(convention.package_name, eq="flext_demo")
            tm.that(convention.package_context.current_pkg, eq="flext_demo")
            tm.that(convention.module_policy.expected_alias, eq="m")
            tm.that(convention.project_layout, none=False)
            tm.that(convention.project_layout.class_stem, eq="FlextDemo")

    def test_workspace_dsl_exposes_direct_modules_source_and_objects(
        self, tmp_path: Path
    ) -> None:
        """Public Rope DSL returns direct module inventory through census objects."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
            tm.that(
                any(entry.file_path == module_path for entry in rope.modules()), eq=True
            )
            tm.that(rope.source(module_path), has="class FlextDemoModels")
            objects = {
                (item.scope_path, item.kind): item for item in rope.objects(module_path)
            }
            expected_objects = {
                ("VALUE", "constant"),
                ("FlextDemoModels", "class"),
                ("FlextDemoModels.build", "method"),
                ("FlextDemoModels.build.payload", "parameter"),
                ("FlextDemoModels.build.local", "local"),
                ("FlextDemoModels.build.nested", "function"),
            }
            tm.that(expected_objects.issubset(objects), eq=True)
            tm.that(objects["FlextDemoModels", "class"].is_facade_member, eq=True)

    def test_workspace_dsl_reload_refreshes_cached_objects(
        self, tmp_path: Path
    ) -> None:
        """Reload drops Rope caches and reflects updated module objects."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
            tm.that({item.name for item in rope.objects(module_path)}, eq={"first"})
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
            tm.that(
                {item.name for item in rope.objects(module_path)},
                eq={"first", "second"},
            )

    def test_workspace_refresh_can_preserve_reverted_name_indexes(
        self, tmp_path: Path
    ) -> None:
        """Refresh can retain the text index after preview-style reverted writes."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
            tm.that(original_index, has="first")
            tm.that(original_index, lacks="second")

            module_path.write_text(changed_source, encoding="utf-8")
            module_path.write_text(original_source, encoding="utf-8")
            rope.refresh(preserve_indexes=True)

            preserved_index = rope.name_index()
            assert preserved_index is original_index
            tm.that(preserved_index, lacks="second")

            module_path.write_text(changed_source, encoding="utf-8")
            rope.refresh()

            rebuilt_index = rope.name_index()
            assert rebuilt_index is not original_index
            tm.that(rebuilt_index, has="second")

    def test_workspace_objects_raise_on_inventory_bootstrap_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inventory bootstrap failures surface instead of pretending the module is empty."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
            raise c.Infra.ROPE_ERROR_TYPES[0](msg)

        monkeypatch.setattr(u.Infra, "get_pymodule", staticmethod(_explode))

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError, match=r"rope inventory failed to load .*service\.py"
            ):
                rope.objects(module_path)

    def test_workspace_name_index_raises_on_module_read_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Name index failures surface instead of quietly dropping unreadable modules."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
                path, encoding=encoding, errors=errors, newline=newline
            )
            return text

        monkeypatch.setattr(type(module_path), "read_text", _broken_read_text)

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError, match=r"rope name index failed to read .*service\.py"
            ):
                rope.name_index()

    def test_workspace_objects_raise_on_indexed_resource_lookup_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Indexed reference search must fail loudly when a referenced module resource vanishes."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
        original_resource = FlextInfraRopeWorkspace.resource

        def _broken_resource(
            rope: FlextInfraRopeWorkspace, file_path: Path
        ) -> t.Infra.RopeResource | None:
            if file_path.resolve() == consumer_path.resolve():
                return None
            return original_resource(rope, file_path)

        monkeypatch.setattr(FlextInfraRopeWorkspace, "resource", _broken_resource)

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            with pytest.raises(
                RuntimeError,
                match=r"rope search resource unavailable for indexed path .*consumer\.py",
            ):
                rope.objects(service_path, include_local_scopes=False)

    def test_indexed_search_raises_on_invalid_import_dependents_result(
        self, tmp_path: Path
    ) -> None:
        """Indexed dependency narrowing must reject invalid import_dependents payloads."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(example_path)
            tm.that(resource, none=False)

            class _BrokenWorkspace:
                def name_index(
                    self,
                ) -> t.MappingKV[str, tuple[tuple[Path, str, tuple[int, ...]], ...]]:
                    return rope.name_index()

                def resource(self, file_path: Path) -> t.Infra.RopeResource | None:
                    return rope.resource(file_path)

                def import_dependents(self, import_target: str) -> object:
                    del import_target
                    return object()

            with pytest.raises(
                TypeError, match=r"rope import_dependents returned non-tuple for demo"
            ):
                FlextInfraUtilitiesRopeImports.indexed_search_resources(
                    _BrokenWorkspace(),
                    resource=resource,
                    name="helper",
                    definition_path=example_path,
                    dependent_import_targets=("demo", "demo.helper"),
                )

    def test_workspace_dsl_classifies_test_only_references(
        self, tmp_path: Path
    ) -> None:
        """Public census objects keep runtime and test reference counts separate."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
        tm.that(candidate.references_count, eq=2)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.test_references_count, eq=2)
        tm.that(candidate.example_references_count, eq=0)
        tm.that(candidate.script_references_count, eq=0)
        tm.that(len(candidate.test_reference_sites), eq=2)
        tm.that(sorted(site.line for site in candidate.test_reference_sites), eq=[3, 6])
        tm.that(
            {site.file_path for site in candidate.test_reference_sites},
            eq={str(test_path)},
        )
        tm.that(
            {site.surface for site in candidate.test_reference_sites},
            eq={c.Infra.DIR_TESTS},
        )

    def test_workspace_dsl_skips_reference_scan_for_facade_members(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Governed facade members skip expensive reference collection."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
            FlextInfraUtilitiesRopeInventory, "_reference_sites", staticmethod(_explode)
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            objects = {
                item.name: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        assert objects["FlextDemoModels"].is_facade_member
        assert objects["m"].is_facade_member

    def test_workspace_dsl_skips_reference_scan_for_private_names(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Private and dunder names do not trigger removal-only reference scans."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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

        tm.that(objects, has="__all__")
        tm.that(objects["__all__"].references_count, eq=0)
        tm.that(seen_names, lacks="__all__")
        tm.that(seen_names, has="public")

    def test_workspace_dsl_tracks_example_importers_for_generic_names(
        self, tmp_path: Path
    ) -> None:
        """Generic example names keep example references after resource narrowing."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        examples_dir = workspace_root / c.Infra.DIR_EXAMPLES
        examples_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n", encoding="utf-8"
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
                for item in rope.objects(producer_path, include_local_scopes=False)
            }

        candidate = objects["run"]
        tm.that(candidate.references_count, eq=2)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.test_references_count, eq=0)
        tm.that(candidate.example_references_count, eq=2)
        tm.that(candidate.script_references_count, eq=0)
        tm.that(
            {site.file_path for site in candidate.example_reference_sites},
            eq={str(consumer_path)},
        )
        tm.that(
            sorted(site.line for site in candidate.example_reference_sites), eq=[3, 5]
        )

    def test_workspace_dsl_tracks_example_base_class_references(
        self, tmp_path: Path
    ) -> None:
        """Example facade subclassing keeps shared base classes out of unused candidates."""
        workspace_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        examples_dir = workspace_root / c.Infra.DIR_EXAMPLES
        models_dir = examples_dir / "_models"
        models_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n", encoding="utf-8"
        )
        (models_dir / c.Infra.INIT_PY).write_text(
            "from __future__ import annotations\n", encoding="utf-8"
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
                for item in rope.objects(shared_path, include_local_scopes=False)
            }

        candidate = objects["ExampleSharedPerson"]
        tm.that(candidate.references_count, eq=2)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.test_references_count, eq=0)
        tm.that(candidate.example_references_count, eq=2)
        tm.that(candidate.script_references_count, eq=0)
        tm.that(
            {site.file_path for site in candidate.example_reference_sites},
            eq={str(facade_path)},
        )
        tm.that(
            sorted(site.line for site in candidate.example_reference_sites), eq=[3, 6]
        )

    def test_workspace_dsl_tracks_same_file_references(self, tmp_path: Path) -> None:
        """Same-file uses must block the unused fast-path shortcut."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        candidate = objects["ExampleService"]
        tm.that(candidate.references_count, eq=1)
        tm.that(candidate.runtime_references_count, eq=1)
        tm.that(candidate.test_references_count, eq=0)
        tm.that(candidate.example_references_count, eq=0)
        tm.that(candidate.script_references_count, eq=0)
        tm.that(
            {site.file_path for site in candidate.runtime_reference_sites},
            eq={str(module_path)},
        )
        tm.that([site.line for site in candidate.runtime_reference_sites], eq=[6])
