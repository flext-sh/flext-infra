"""Public behavior tests for Rope workspace objects, conventions, and refresh.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

import pytest

import flext_infra
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraInfraRopeServiceObjects:
    """Validate Rope workspace objects, conventions, and refresh via public methods."""

    @staticmethod
    def _demo_module(
        tmp_path: Path,
        module_name: str,
        source: str,
    ) -> tuple[Path, Path]:
        """Create one flext-demo workspace and write ``source`` into its module.

        Returns:
            The resulting ``tuple[Path, Path]``.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / module_name
        module_path.write_text(source, encoding="utf-8")
        return repository_root, module_path

    @staticmethod
    def _module_objects_by_name(
        repository_root: Path,
        module_path: Path,
    ) -> MutableMapping[str, m.Infra.Object]:
        """Index one module's non-local objects by their declared name.

        Returns:
            The resulting ``MutableMapping[str, m.Infra.Object]``.

        """
        with flext_infra.infra.rope_workspace(repository_root) as rope:
            return {
                item.name: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

    @staticmethod
    def test_workspace_dsl_centralizes_project_and_module_conventions(
        tmp_path: Path,
    ) -> None:
        """Public Rope DSL centralizes project discovery and module naming rules."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextModelsDemo",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            projects = rope.projects()
            tm.that(len(projects), eq=1)
            tm.that(projects[0].name, eq="flext-demo")

            layout = rope.layout(repository_root)
            layout = tm.not_none(layout)
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
            project_layout = tm.not_none(convention.project_layout)
            tm.that(project_layout.class_stem, eq="FlextDemo")

    def test_api_module_alias_comes_only_from_declared_exports(
        self,
        tmp_path: Path,
    ) -> None:
        """A root ``api.py`` without a declared alias never gets a synthesized one."""
        repository_root, api_path = self._demo_module(
            tmp_path,
            c.Infra.API_PY,
            '"""Api."""\n\n__all__: list[str] = ["FlextDemo"]\n\n'
            "class FlextDemo:\n    pass\n",
        )
        with flext_infra.infra.rope_workspace(repository_root) as rope:
            layout = tm.not_none(rope.layout(repository_root))
            policy = rope.convention(api_path).module_policy
        tm.that(policy.expected_alias, none=True)
        tm.that(layout.package_alias, ne=policy.expected_alias)

    @staticmethod
    def test_workspace_dsl_exposes_direct_modules_source_and_objects(
        tmp_path: Path,
    ) -> None:
        """Public Rope DSL returns direct module inventory through census objects."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "VALUE = 1\n\n"
                "class FlextModelsDemo:\n"
                "    FLAG = VALUE\n\n"
                "    def build(self, payload: int) -> int:\n"
                "        local = payload + VALUE\n\n"
                "        def nested(extra: int) -> int:\n"
                "            return local + extra\n\n"
                "        return nested(1)\n\n"
                "m = FlextModelsDemo\n"
            ),
            encoding="utf-8",
        )
        with flext_infra.infra.rope_workspace(repository_root) as rope:
            tm.that(
                any(entry.file_path == module_path for entry in rope.modules()),
                eq=True,
            )
            tm.that(rope.source(module_path), has="class FlextModelsDemo")
            objects = {
                (item.scope_path, item.kind): item for item in rope.objects(module_path)
            }
            tm.that(objects.get(("VALUE", "constant")), none=False)
            tm.that(objects.get(("FlextModelsDemo", "class")), none=False)
            tm.that(objects.get(("FlextModelsDemo.build", "method")), none=False)
            tm.that(
                objects.get(("FlextModelsDemo.build.payload", "parameter")),
                none=False,
            )
            tm.that(objects.get(("FlextModelsDemo.build.local", "local")), none=False)
            tm.that(
                objects.get(("FlextModelsDemo.build.nested", "function")),
                none=False,
            )

    @staticmethod
    def test_workspace_dsl_reload_refreshes_cached_objects(
        tmp_path: Path,
    ) -> None:
        """Reload drops Rope caches and reflects updated module objects."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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
        with flext_infra.infra.rope_workspace(repository_root) as rope:
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

    @staticmethod
    def test_workspace_refresh_invalidates_source_and_semantic_snapshots(
        tmp_path: Path,
    ) -> None:
        """Refresh exposes file changes after preserving stable session snapshots."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        original_source = "class Original:\n    pass\n"
        changed_source = "class Changed:\n    pass\n"
        module_path.write_text(original_source, encoding=c.DEFAULT_ENCODING)

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            original_semantic = rope.semantic(module_path)
            tm.that(rope.source(module_path), eq=original_source)
            tm.that(
                tuple(item.name for item in original_semantic.class_infos),
                eq=("Original",),
            )

            module_path.write_text(changed_source, encoding=c.DEFAULT_ENCODING)
            tm.that(rope.source(module_path), eq=changed_source)
            tm.that(
                tuple(item.name for item in rope.semantic(module_path).class_infos),
                eq=("Original",),
            )
            tm.that(
                tuple(item.name for item in rope.objects(module_path)),
                eq=("Original",),
            )

            rope.refresh()
            tm.that(
                tuple(item.name for item in rope.objects(module_path)),
                eq=("Changed",),
            )

    @staticmethod
    @pytest.mark.parametrize("move_existing", [False, True])
    def test_workspace_refresh_exposes_created_and_moved_modules(
        tmp_path: Path,
        *,
        move_existing: bool,
    ) -> None:
        """Refresh rebuilds module and package inventories on the same project."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        original_path = package_root / "service.py"
        source = "class PublicService:\n    pass\n"
        original_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        destination_dir = package_root / "services"
        destination_path = destination_dir / "service.py"

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            project = rope.rope_project
            tm.that(rope.module(original_path), none=False)
            tm.that(rope.module(destination_path), none=True)
            tm.that(rope.package(destination_dir), none=True)
            tm.that(rope.name_index(), has="PublicService")
            destination_dir.mkdir()
            (destination_dir / c.Infra.INIT_PY).write_text(
                "",
                encoding=c.DEFAULT_ENCODING,
            )
            if move_existing:
                original_path.rename(destination_path)
            else:
                destination_path.write_text(source, encoding=c.DEFAULT_ENCODING)

            snapshot = rope.refresh()

            tm.ok(rope.rope_project is project)
            tm.that(snapshot.workspace_index.package_dirs, has=destination_dir)
            module = tm.not_none(rope.module(destination_path))
            tm.that(module.module_name, eq="flext_demo.services.service")
            package = tm.not_none(rope.package(destination_dir))
            tm.that(package.package_name, eq="flext_demo.services")
            tm.that(rope.module(original_path), none=move_existing)
            tm.that(
                {entry.file_path for entry in rope.modules()},
                has=destination_path,
            )
            tm.that(
                {path for path, _surface, _lines in rope.name_index()["PublicService"]},
                eq={destination_path}
                if move_existing
                else {original_path, destination_path},
            )
            tm.that(
                {item.name for item in rope.objects(destination_path)},
                eq={"PublicService"},
            )

    @staticmethod
    def test_workspace_refresh_discovers_new_import_dependents(tmp_path: Path) -> None:
        """New consumers participate in rebuilt semantic import queries."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        service_path = package_root / "service.py"
        service_path.write_text(
            "class PublicService:\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer_path = package_root / "consumer.py"
        import_target = "flext_demo.service.PublicService"

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            tm.that(rope.import_dependents(import_target), eq=())
            consumer_path.write_text(
                "from flext_demo.service import PublicService\n",
                encoding=c.DEFAULT_ENCODING,
            )
            rope.refresh()
            tm.that(rope.import_dependents(import_target), eq=(consumer_path,))

    @staticmethod
    def test_workspace_refresh_updates_project_metadata_and_layout(
        tmp_path: Path,
    ) -> None:
        """Changed metadata and facade declarations refresh discovery and layout."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        pyproject_path = repository_root / c.PYPROJECT_FILENAME

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            tm.that(rope.projects()[0].name, eq=repository_root.name)
            original_layout = tm.not_none(rope.layout(repository_root))
            tm.that(original_layout.runtime_aliases, eq=())
            changed_name = "flext-renamed-demo"
            pyproject_path.write_text(
                pyproject_path.read_text(encoding=c.DEFAULT_ENCODING).replace(
                    f'name = "{repository_root.name}"',
                    f'name = "{changed_name}"',
                ),
                encoding=c.DEFAULT_ENCODING,
            )
            u.Tests.write_lazy_init_namespace_module(
                package_root / "models.py",
                class_name="FlextModelsDemo",
                alias="m",
                docstring="Models.",
            )
            rope.refresh()

            tm.that(rope.projects()[0].name, eq=changed_name)
            layout = tm.not_none(rope.layout(repository_root))
            tm.that(layout.project_name, eq=changed_name)
            tm.that(layout.package_dir, eq=package_root)
            tm.that(layout.runtime_aliases, eq=("m",))

    @staticmethod
    @pytest.mark.parametrize("validate_project", [False, True])
    def test_workspace_refresh_can_preserve_reverted_name_indexes(
        tmp_path: Path,
        *,
        validate_project: bool,
    ) -> None:
        """Refresh can retain the text index after preview-style reverted writes."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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
        consumer_path = package_root / "consumer.py"
        consumer_path.write_text(
            "from flext_demo.service import first\n",
            encoding=c.DEFAULT_ENCODING,
        )
        import_target = "flext_demo.service.first"

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            original_workspace_index = rope.workspace_index
            original_projects = rope.projects()
            original_layout = rope.layout(repository_root)
            original_dependents = rope.import_dependents(import_target)
            tm.that(original_dependents, eq=(consumer_path,))
            original_index = rope.name_index()
            tm.that(original_index, has="first")
            tm.that(original_index, lacks="second")

            module_path.write_text(changed_source, encoding="utf-8")
            module_path.write_text(original_source, encoding="utf-8")
            snapshot = rope.refresh(
                preserve_indexes=True,
                validate_project=validate_project,
            )

            preserved_index = rope.name_index()
            tm.ok(snapshot.workspace_index is original_workspace_index)
            tm.ok(rope.projects() is original_projects)
            tm.ok(rope.layout(repository_root) is original_layout)
            tm.that(
                rope.import_dependents(import_target) is original_dependents,
                eq=True,
            )
            tm.ok(preserved_index is original_index)
            tm.that(preserved_index, lacks="second")

            module_path.write_text(changed_source, encoding="utf-8")
            rope.refresh()

            rebuilt_index = rope.name_index()
            tm.ok(rebuilt_index is not original_index)
            tm.that(rebuilt_index, has="second")

    @staticmethod
    def test_workspace_objects_raise_on_unparseable_module(
        tmp_path: Path,
    ) -> None:
        """Unparseable module sources surface instead of an empty module."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text("def first(:\n", encoding=c.DEFAULT_ENCODING)

        with (
            flext_infra.infra.rope_workspace(repository_root) as rope,
            pytest.raises(SyntaxError) as parse_error,
        ):
            rope.objects(module_path)

        tm.that(parse_error.value.filename, eq=str(module_path.resolve()))

    @staticmethod
    def test_workspace_name_index_raises_on_module_read_error(
        tmp_path: Path,
    ) -> None:
        """Name index failures surface instead of dropping unreadable modules."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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
            encoding=c.DEFAULT_ENCODING,
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            _ = rope.workspace_index
            module_path.unlink()
            with pytest.raises(FileNotFoundError, match=r"service\.py"):
                rope.name_index()

    @staticmethod
    def test_workspace_objects_raise_on_indexed_resource_lookup_error(
        tmp_path: Path,
    ) -> None:
        """Indexed reference lookup fails when a module resource vanishes."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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
            encoding=c.DEFAULT_ENCODING,
        )
        consumer_path = package_root / "consumer.py"
        consumer_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from flext_demo.service import public\n\n"
                "def consume() -> int:\n"
                "    return public()\n"
            ),
            encoding=c.DEFAULT_ENCODING,
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            _ = rope.name_index()
            consumer_path.unlink()
            with pytest.raises(FileNotFoundError, match=r"consumer\.py"):
                rope.objects(service_path, include_local_scopes=False)

    @staticmethod
    def test_workspace_dsl_ignores_test_references(tmp_path: Path) -> None:
        """Tests remain outside production reachability."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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
        test_path = repository_root / "tests" / "test_service.py"
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

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        candidate = objects["only_for_tests"]
        tm.that(candidate.references_count, eq=0)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.script_references_count, eq=0)

    def test_workspace_dsl_does_not_classify_legacy_root_facade(
        self,
        tmp_path: Path,
    ) -> None:
        """Legacy root facade declarations are ordinary objects."""
        repository_root, module_path = self._demo_module(
            tmp_path,
            "models.py",
            "from __future__ import annotations\n\n"
            "class FlextModelsDemo:\n"
            "    pass\n\n"
            "m = FlextModelsDemo\n",
        )

        objects = self._module_objects_by_name(repository_root, module_path)

        tm.fail(objects["FlextModelsDemo"].is_facade_member)
        tm.fail(objects["m"].is_facade_member)

    def test_workspace_dsl_skips_reference_scan_for_private_names(
        self,
        tmp_path: Path,
    ) -> None:
        """Private and dunder names expose zero production references."""
        repository_root, module_path = self._demo_module(
            tmp_path,
            "service.py",
            "from __future__ import annotations\n\n"
            '__all__: list[str] = ["public"]\n\n'
            "def public() -> int:\n"
            "    return 1\n",
        )

        objects = self._module_objects_by_name(repository_root, module_path)

        tm.that(objects, has="__all__")
        tm.that(objects["__all__"].references_count, eq=0)
        tm.that(objects, has="public")

    @staticmethod
    def test_workspace_dsl_ignores_example_importers_for_generic_names(
        tmp_path: Path,
    ) -> None:
        """Examples remain outside production reachability."""
        repository_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        examples_dir = repository_root / c.Infra.DIR_EXAMPLES
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

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(producer_path, include_local_scopes=False)
            }

        candidate = objects["run"]
        tm.that(candidate.references_count, eq=0)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.script_references_count, eq=0)

    @staticmethod
    def test_workspace_dsl_ignores_example_base_class_references(
        tmp_path: Path,
    ) -> None:
        """Example inheritance remains outside production reachability."""
        repository_root, _package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        examples_dir = repository_root / c.Infra.DIR_EXAMPLES
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

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(shared_path, include_local_scopes=False)
            }

        candidate = objects["ExampleSharedPerson"]
        tm.that(candidate.references_count, eq=0)
        tm.that(candidate.runtime_references_count, eq=0)
        tm.that(candidate.script_references_count, eq=0)

    @staticmethod
    def test_workspace_dsl_tracks_same_file_references(tmp_path: Path) -> None:
        """Same-file uses must block the unused fast-path shortcut."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            objects = {
                item.scope_path: item
                for item in rope.objects(module_path, include_local_scopes=False)
            }

        candidate = objects["ExampleService"]
        tm.that(candidate.references_count, eq=1)
        tm.that(candidate.runtime_references_count, eq=1)
        tm.that(candidate.script_references_count, eq=0)
        tm.that(
            {site.file_path for site in candidate.runtime_reference_sites},
            eq={str(module_path)},
        )
        tm.that([site.line for site in candidate.runtime_reference_sites], eq=[6])
