"""Public behavior tests for the Rope workspace DSL service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import flext_infra
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraInfraRopeService:
    """Validate the public Rope workspace DSL through public methods only."""

    @staticmethod
    def test_query_refresh_preserves_native_project_and_resource_contract(
        tmp_path: Path,
    ) -> None:
        """Read queries keep native identities, ordering, and eager missing errors."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source_path = package / "query_owner.py"
        source = "class QueryOwner:\n    pass\n"
        source_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with flext_infra.infra.rope_workspace(root) as workspace:
            project = workspace.rope_project
            resource = tm.not_none(workspace.resource(source_path))
            tm.ok(resource is workspace.resource(source_path))
            tm.that(workspace.source(source_path), eq=source)
            modules = workspace.modules()
            tm.that(
                tuple(entry.file_path for entry in modules),
                eq=tuple(sorted(entry.file_path for entry in modules)),
            )
            names = workspace.name_index()
            tm.ok(names is workspace.name_index())
            tm.that(names, has="QueryOwner")
            workspace.refresh(preserve_indexes=True)
            tm.ok(project is workspace.rope_project)
            tm.that(workspace.source(source_path), eq=source)
            with pytest.raises(FileNotFoundError):
                workspace.source(package / "missing_query_owner.py")

    @staticmethod
    @pytest.mark.parametrize("same_root", [False, True])
    def test_sibling_scopes_keep_their_root_and_independent_lifetime(
        rope_sibling_scopes: tuple[tuple[Path, Path], tuple[Path, Path]],
        *,
        same_root: bool,
    ) -> None:
        """Closing one consumer never changes another consumer's logical scope."""
        (producer_root, producer), (consumer_root, consumer) = rope_sibling_scopes
        if same_root:
            consumer_root, consumer = producer_root, producer
        source = producer / "owned.py"
        source.write_text("class Owner:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        with flext_infra.infra.rope_workspace(
            producer_root, producer_root.parent
        ) as outer:
            before = tuple(item.name for item in outer.objects(source))
            tm.that(before, has="Owner")
            with flext_infra.infra.rope_workspace(
                consumer_root, producer_root.parent
            ) as inner:
                tm.that(inner.repository_root, eq=consumer_root)
                tm.that(outer.repository_root, eq=producer_root)
                tm.not_none(inner.resource(consumer / "__init__.py"))
            tm.that(
                tuple(item.name for item in outer.objects(source)),
                eq=before,
            )

    @staticmethod
    @pytest.mark.parametrize("include_local_scopes", [False, True])
    def test_workspace_dsl_keeps_nested_declarations_without_function_locals(
        tmp_path: Path,
        *,
        include_local_scopes: bool,
    ) -> None:
        """Class families remain visible when function-local inventory is disabled."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "declarations.py"
        source = (
            "from pydantic import BaseModel\n"
            "from typing import Protocol\n"
            "class Namespace:\n"
            "    class Payload(BaseModel):\n"
            "        value: str\n"
            "        def normalize(self, value: str) -> str:\n"
            "            local = value.strip()\n"
            "            return local\n"
            "    class Reader(Protocol):\n"
            "        value: str\n"
            "def create():\n"
            "    class FunctionLocal:\n"
            "        value: str\n"
            "    return FunctionLocal\n"
        )
        path.write_text(source, encoding="utf-8")
        with flext_infra.infra.rope_workspace(root) as workspace:
            objects = workspace.objects(
                path,
                include_local_scopes=include_local_scopes,
                include_references=False,
            )
        paths = {item.scope_path for item in objects}
        tm.that(
            {
                "Namespace",
                "Namespace.Payload",
                "Namespace.Payload.value",
                "Namespace.Payload.normalize",
                "Namespace.Reader",
                "Namespace.Reader.value",
                "create",
            }.issubset(paths),
            eq=True,
        )
        tm.that(
            "Namespace.Payload.normalize.local" in paths,
            eq=include_local_scopes,
        )
        tm.that("create.FunctionLocal" in paths, eq=include_local_scopes)
        tm.that(
            any(item.reference_evidence_collected for item in objects),
            eq=False,
        )
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def _paired_namespace_projects(
        root: Path,
    ) -> tuple[Path, Path, Path, Path, Path]:
        """Declare two sibling namespace projects and return their roots and modules.

        Returns:
            The resulting ``tuple[Path, Path, Path, Path, Path]``.

        """
        project_root, package_root = u.Tests.create_lazy_init_workspace(
            root,
            project_name="flext-infra",
            package_name="flext_infra",
        )
        sibling_root, sibling_package_root = u.Tests.create_lazy_init_workspace(
            root,
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
        sibling_module_path = sibling_package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            sibling_module_path,
            class_name="FlextModelsDemo",
            alias="m",
            docstring="Models.",
        )
        return (
            project_root,
            package_root,
            module_path,
            sibling_root,
            sibling_module_path,
        )

    @staticmethod
    def _module_exports(
        repository_root: Path,
        module_path: Path,
        options: t.JsonMapping,
    ) -> tuple[str, ...]:
        """Read one module's public export contract through the Rope workspace.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        with flext_infra.infra.rope_workspace(repository_root) as rope:
            return tuple(
                rope.exports(
                    module_path,
                    export_options=m.Infra.ExportOptions.model_validate(options),
                ),
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "symbol", "documented"),
        [
            ("from .sibling import Public\n", "Public", False),
            ('class Public:\n    """Public contract."""\n', "Public", True),
            ("class Public:\n    pass\n", "Public", False),
        ],
    )
    def test_source_docstrings_only_resolve_local_definitions(
        tmp_path: Path,
        source: str,
        symbol: str,
        *,
        documented: bool,
    ) -> None:
        """Documented local definitions satisfy the real public docs consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "provider.py"
        path.write_text(source, encoding="utf-8")
        with u.Infra.facade_source_project(root) as (project, _sources):
            issues = u.Infra.docstring_issues(
                root,
                {
                    "package_name": package.name,
                    "modules": [],
                    "target_map": {symbol: f"{package.name}.{path.stem}"},
                },
                rope_project=project,
            )
        missing = f"exported symbol `{symbol}` is missing a docstring"
        tm.that(not any(issue.message == missing for issue in issues), eq=documented)

    @staticmethod
    def test_public_workspace_materializes_index(tmp_path: Path) -> None:
        """The public workspace exposes its typed repository index directly."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            tm.that(rope.repository_root, eq=repository_root.resolve())
            tm.that(rope.workspace_index.package_dirs, has=package_root)
            tm.that(rope.module(module_path), none=False)
            tm.that(rope.package(package_root), none=False)
            exports = rope.exports(
                module_path,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_assignments": True,
                }),
            )
            tm.that(exports, has="FlextTestsModels")
            tm.that(exports, has="m")

    @staticmethod
    def test_script_guard_bindings_are_not_exports(tmp_path: Path) -> None:
        """A name bound under ``if __name__ == "__main__":`` is not a module export.

        flext-core's examples bound ``result`` and ``msg`` in their script
        blocks; the regenerated package facade re-exported them and every
        importer failed with a missing module attribute.
        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "demo.py"
        module_path.write_text(
            '"""Demo."""\n\n'
            "LIMIT = 3\n\n\n"
            "def run() -> int:\n"
            '    """Run."""\n'
            "    return LIMIT\n\n\n"
            'if __name__ == "__main__":\n'
            "    result = run()\n"
            "    if result != LIMIT:\n"
            '        msg = "unexpected"\n'
            "        raise RuntimeError(msg)\n",
            encoding=c.DEFAULT_ENCODING,
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            exports = rope.exports(
                module_path,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_assignments": True,
                    "allow_functions": True,
                }),
            )

        tm.that(exports, has=["LIMIT", "run"], lacks=["result", "msg"])

    def test_source_exports_preserve_explicit_public_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Explicit ``__all__`` remains authoritative over implicit symbols."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "public.py"
        module_path.write_text(
            '"""Public contract."""\n\n'
            "from elsewhere import Imported\n\n"
            'PUBLIC = "public"\n'
            'PRIVATE = "private"\n'
            '__all__ = ("PUBLIC",)\n',
            encoding=c.DEFAULT_ENCODING,
        )

        exports = self._module_exports(
            repository_root,
            module_path,
            {"allow_assignments": True, "allow_functions": True},
        )

        tm.that(exports, eq=("PUBLIC",))

    def test_source_exports_include_conditional_module_assignments(
        self,
        tmp_path: Path,
    ) -> None:
        """Module-control-flow assignments remain visible outside script guards."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "conditional.py"
        module_path.write_text(
            '"""Conditional contract."""\n\n'
            "if TYPE_CHECKING:\n"
            '    MODE = "typing"\n'
            "else:\n"
            '    MODE = "runtime"\n',
            encoding=c.DEFAULT_ENCODING,
        )

        exports = self._module_exports(
            repository_root,
            module_path,
            {"allow_assignments": True},
        )

        tm.that(exports, eq=("MODE",))

    @staticmethod
    def test_open_workspace_indexes_declared_wrapper_packages(
        tmp_path: Path,
    ) -> None:
        """Expose examples modules for explicitly targeted semantic codegen."""
        repository_root, _package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        examples_root = repository_root / c.Infra.DIR_EXAMPLES
        examples_root.mkdir()
        examples_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        module_path = examples_root / "demo.py"
        module_path.write_text(
            'class ExamplesDemo:\n    """Example boundary."""\n\n'
            '__all__ = ["ExamplesDemo"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            tm.that(rope.workspace_index.package_dirs, has=examples_root)
            module = rope.module(module_path)
            tm.that(module, none=False)
            tm.that(
                module.module_name if module is not None else "",
                eq="examples.demo",
            )

    @staticmethod
    def test_public_facade_opens_rope_workspace(tmp_path: Path) -> None:
        """Public facade returns the same ergonomic Rope workspace DSL."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        module_path = package_root / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            state = rope.semantic(module_path)
            tm.that(
                any(
                    class_info.name == "FlextTestsModels"
                    for class_info in state.class_infos
                ),
                eq=True,
            )

    @staticmethod
    @pytest.mark.parametrize("family_alias", sorted(u.Infra.facade_families()))
    def test_class_nesting_cutover_uses_declared_family_owner(
        tmp_path: Path,
        family_alias: str,
    ) -> None:
        """Plan every facade family from semantic objects and its declared owner."""
        module_name = u.Tests.family_public_module(family_alias)
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        owner_name = (
            f"{u.derive_class_stem(repository_root.name)}"
            f"{u.Infra.facade_families()[family_alias].suffix}"
        )
        extra_class_name = f"{owner_name}Member"
        module_path = package_root / f"{module_name}.py"
        u.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name=owner_name,
            alias=family_alias,
            extra_class_names=(extra_class_name,),
        )

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            owner = rope.convention(module_path).module_policy.expected_family
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module_path: module_path.read_text(encoding="utf-8")},
            )

        tm.ok(planned)
        tm.that(len(planned.value), eq=1)
        tm.that(planned.value[0].file_path, eq=module_path.resolve())
        tm.that(
            planned.value[0].changes,
            eq=(f"nested {extra_class_name} under {owner}",),
        )

    def test_workspace_indexes_only_each_repositorys_own_sources(
        self,
        tmp_path: Path,
    ) -> None:
        """Planning targets stay local while member repositories remain importable."""
        monorepo_root, owned_package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="repo", package_name="workspace_root"
        )
        u.Tests.declare_workspace_projects(monorepo_root, ("flext-infra", "flext-demo"))
        owned_module_path = owned_package_root / "owned.py"
        owned_module_path.write_text(
            "class WorkspaceOwned:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        (
            repository_root,
            package_root,
            module_path,
            _sibling_root,
            sibling_module_path,
        ) = self._paired_namespace_projects(monorepo_root)

        for call_root in (monorepo_root, repository_root, package_root):
            workspace_scope = call_root == monorepo_root
            expected_root = monorepo_root if workspace_scope else repository_root
            expected_projects = {expected_root.resolve()}
            with flext_infra.infra.rope_workspace(call_root) as rope:
                tm.that(rope.rope_repository_root, eq=expected_root.resolve())
                tm.that(
                    {entry.project_root for entry in rope.modules()},
                    eq=expected_projects,
                )
                tm.that(rope.module(module_path), none=workspace_scope)
                tm.that(rope.module(sibling_module_path), none=True)
                tm.that(rope.module(owned_module_path), none=not workspace_scope)
                if workspace_scope:
                    dependency = u.Infra.resolve_pymodule(
                        rope.rope_project,
                        tm.not_none(rope.resource(sibling_module_path)),
                    )
                    tm.not_none(dependency.get_attribute("FlextModelsDemo"))

    def test_open_standalone_keeps_local_project_scope(self, tmp_path: Path) -> None:
        """Without a workspace context, sibling projects remain outside Rope."""
        projects_root = tmp_path / "projects"
        projects_root.mkdir()
        project_root, package_root, module_path, sibling_root, sibling_module_path = (
            self._paired_namespace_projects(projects_root)
        )

        with flext_infra.infra.rope_workspace(package_root) as rope:
            tm.that(rope.rope_repository_root, eq=project_root.resolve())
            tm.that(
                {entry.project_root for entry in rope.modules()},
                eq={project_root.resolve()},
            )
            tm.that(rope.module(module_path), none=False)
            tm.that(rope.module(sibling_module_path), none=True)
            tm.fail(sibling_root in rope.rope_repository_root.parents)

    @staticmethod
    def test_unrelated_ancestor_workspace_does_not_capture_project(
        tmp_path: Path,
    ) -> None:
        """An ancestor workspace owns only the projects it declares."""
        ancestor = tmp_path / "ancestor"
        ancestor.mkdir()
        declared_root, _ = u.Tests.create_lazy_init_workspace(
            ancestor,
            project_name="declared",
            package_name="declared",
        )
        project_root, package_root = u.Tests.create_lazy_init_workspace(
            ancestor / "scratch",
            project_name="standalone",
            package_name="standalone",
        )
        u.Tests.declare_workspace_projects(ancestor, (declared_root.name,))

        with flext_infra.infra.rope_workspace(package_root) as rope:
            tm.that(rope.rope_repository_root, eq=project_root.resolve())

    @staticmethod
    def test_unowned_ancestor_src_does_not_expand_rope_scope(
        tmp_path: Path,
    ) -> None:
        """Ignore an ancestor source directory that owns no repository."""
        unowned_parent = tmp_path / "unowned"
        scratch = unowned_parent / "scratch"
        (unowned_parent / c.Infra.DEFAULT_SRC_DIR).mkdir(parents=True)
        scratch.mkdir()

        with flext_infra.infra.rope_workspace(scratch) as rope:
            tm.that(rope.rope_repository_root, eq=scratch.resolve())
            tm.that(rope.modules(), eq=())

    @staticmethod
    def test_workspace_exports_fixture_functions_when_requested(
        tmp_path: Path,
    ) -> None:
        """Fixture modules can publish pytest fixtures through the Rope DSL."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
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

        with flext_infra.infra.rope_workspace(repository_root) as rope:
            exports = rope.exports(
                fixture_module,
                export_options=m.Infra.ExportOptions.model_validate({
                    "allow_functions": True,
                }),
            )

        tm.that(exports, has="reset_settings")
        tm.that(exports, has="settings_factory")
