"""Promote shared test behavior using its original Rope declaration identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path

from flext_infra import c, m, p
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
from flext_infra._utilities._rope.pymodule import FlextInfraUtilitiesRopeCorePyModule
from flext_infra._utilities._rope.rope_module_patch import (
    FlextInfraUtilitiesRopeModulePatch,
)
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticHelperReferences,
)


class FlextInfraUtilitiesSemanticTestHelpers(
    FlextInfraUtilitiesSemanticHelperReferences,
):
    """Discover shared test helpers and move them to their tier utilities owner."""

    @classmethod
    def _test_helper_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        editable = {
            path.resolve(): source
            for path, source in sources.items()
            if not source.startswith(c.Infra.AUTOGEN_HEADER)
        }
        candidates = tuple(
            path
            for path in sorted(editable)
            if path.is_relative_to(workspace.repository_root)
            and c.Infra.DIR_TESTS in path.parts
            and (
                workspace.convention(path).module_policy.is_fixture_module
                or (path.stem.startswith("_") and path.stem != "__init__")
            )
        )
        if not candidates:
            return ()
        working = dict(sources)
        changes: MutableMapping[Path, list[str]] = {}
        for path in candidates:
            while True:
                project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    workspace.rope_project,
                    working,
                )
                try:
                    move = cls._shared_helper_move(
                        workspace,
                        project,
                        path,
                        working,
                        frozenset(editable),
                    )
                    if move is None:
                        break
                    planned = cls._helper_move_plan(
                        move,
                        sources={path: working[path] for path in editable},
                    )
                    if not any(edit.file_path == path for edit in planned):
                        msg = (
                            f"shared test helper move did not remove "
                            f"its declaration: {path}"
                        )
                        raise ValueError(msg)
                    for edit in planned:
                        working[edit.file_path] = edit.updated_source
                        changes.setdefault(edit.file_path, []).extend(edit.changes)
                    with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
                        workspace.repository_root,
                        planned_sources=working,
                        source_project=project,
                    ) as (native, _captured):
                        module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                            native,
                            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
                                native, path
                            ),
                        )
                        working[path] = (
                            FlextInfraUtilitiesRopeModulePatch.remove_runtime_alias_export(
                                module, alias=move.class_name
                            )
                        )
                finally:
                    project.close()
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=sources[path],
                updated_source=working[path],
                changes=tuple(operations),
            )
            for path, operations in sorted(changes.items())
            if sources[path] != working[path]
        )

    @classmethod
    def _shared_helper_move(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        path: Path,
        sources: Mapping[Path, str],
        editable: frozenset[Path],
    ) -> m.Infra.ClassMoveRequest | None:
        """Elect the shared helper declaration one file moves under.

        Returns:
            The elected class-move request, or none when nothing moves.

        """
        root = Path(project.root.real_path)
        resource = project.get_resource(path.relative_to(root).as_posix())
        resources = tuple(
            project.get_resource(item.relative_to(root).as_posix())
            for item in sorted(editable)
        )
        module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(project, resource)
        fixture = cls._fixture_move(project, path, module, sources)
        if fixture is not None:
            return fixture
        return cls._shared_declaration_move(
            project, path, sources, resources, (workspace, sources, module)
        )

    @classmethod
    def _shared_declaration_move(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        sources: Mapping[Path, str],
        resources: tuple[object, ...],
        owner_context: tuple[
            p.Infra.RopeWorkspaceDsl, Mapping[Path, str], p.Infra.RopePyModule
        ],
    ) -> m.Infra.ClassMoveRequest | None:
        """Elect one shared class or function declaration for the utilities move.

        Returns:
            The elected class-move request, or none when nothing is shared.

        Raises:
            ValueError: If a shared declaration lost its identifier or target.

        """
        module = owner_context[2]
        for declaration in (
            scope
            for scope in module.get_scope().get_scopes()
            if scope.get_kind() in {"Class", "Function"}
        ):
            name = declaration.pyobject.get_name()
            members = (declaration, *cls._helper_callable_scopes(declaration))
            behavior = any(member.get_kind() == "Function" for member in members)
            if any(
                member.pyobject.get_name().startswith(
                    c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX
                )
                for member in members
                if member.get_kind() == "Function"
            ):
                continue
            offset = (
                FlextInfraUtilitiesRopeCorePyModule.find_identifier_offset_in_lines
            )(
                sources[path].splitlines(keepends=True),
                line=declaration.get_start(),
                symbol=name,
            )
            if offset is None:
                msg = f"shared helper declaration has no identifier: {path}:{name}"
                raise ValueError(msg)
            references = FlextInfraUtilitiesRopeRuntimeModules.runtime_find_occurrences(
                project,
                project.get_resource(
                    path.relative_to(Path(project.root.real_path)).as_posix()
                ),
                offset,
                resources=resources,
                in_hierarchy=False,
            )
            if not any(
                reference.resource is not None
                and Path(reference.resource.real_path).resolve() != path
                for reference in references
            ):
                continue
            return cls._destination_class_move(
                owner_context, project, path, declaration, "u" if behavior else "m"
            )
        return None

    @classmethod
    def _destination_class_move(
        cls,
        owner_context: tuple[
            p.Infra.RopeWorkspaceDsl, Mapping[Path, str], p.Infra.RopePyModule
        ],
        project: p.Infra.RopeProject,
        path: Path,
        declaration: p.Infra.RopeScope,
        letter: str,
    ) -> m.Infra.ClassMoveRequest:
        """Bind one shared declaration's move into the tests utilities owner.

        Returns:
            The class-move request into the elected owner surface.

        Raises:
            ValueError: If the destination already binds the name without moving.

        """
        workspace, sources, _module = owner_context
        root = Path(project.root.real_path)
        name = declaration.pyobject.get_name()
        resource = project.get_resource(path.relative_to(root).as_posix())
        target = cls._test_utilities_owner(workspace, path, sources, letter=letter)
        target_resource = project.get_resource(target.relative_to(root).as_posix())
        target_module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            project, target_resource
        )
        if name in target_module.get_attributes() and not (
            cls._destination_imports_moving_declaration(
                project, resource, name, target_module.get_attribute(name)
            )
        ):
            msg = f"shared helper destination already binds {name}: {target}"
            raise ValueError(msg)
        return m.Infra.ClassMoveRequest(
            rope_project=project,
            source_file=path,
            target_file=target,
            class_name=name,
            line=declaration.get_start(),
            apply=False,
        )

    @classmethod
    def _fixture_move(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        module: p.Infra.RopePyModule,
        sources: Mapping[Path, str],
    ) -> m.Infra.ClassMoveRequest | None:
        """Elect pytest fixture declarations by native decorator binding identity.

        Returns:
            The elected class-move request, or none when no fixture declares.

        Raises:
            ValueError: If a fixture decorator has no declaration owner.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        declarations = tuple(module.get_scope().get_scopes())
        functions = tuple(
            scope for scope in declarations if scope.get_kind() == "Function"
        )
        if not functions:
            return None
        fixture_binding = project.get_module("pytest").get_attribute("fixture")
        fragments = module.get_source_binding_index().fragments
        for fragment in fragments:
            if (
                fragment.context.role != "decorator"
                or fragment.context.structural_scope is not module.get_scope()
            ):
                continue
            binding = runtime.expression_name(
                fragment.context.environment,
                module.source_code[fragment.start : fragment.end],
            )
            if binding is None or not runtime.same_name(binding, fixture_binding):
                continue
            line = module.lines.get_line_number(fragment.start)
            owners = tuple(
                scope
                for scope in declarations
                if scope.get_start() > line
                and scope.parent is fragment.context.structural_scope
            )
            if not owners:
                msg = (
                    f"fixture decorator has no native declaration owner: {path}:{line}"
                )
                raise ValueError(msg)
            owner = min(owners, key=lambda scope: scope.get_start())
            if owner.get_kind() != "Function":
                msg = f"fixture decorator owner is not a function: {path}:{line}"
                raise ValueError(msg)
            target = next(
                (
                    parent / "conftest.py"
                    for parent in path.parents
                    if parent / "conftest.py" in sources
                ),
                None,
            )
            if target is None:
                msg = f"fixture declaration has no existing conftest owner: {path}"
                raise ValueError(msg)
            name = owner.pyobject.get_name()
            target_resource = project.get_resource(
                target.relative_to(Path(project.root.real_path)).as_posix()
            )
            destination = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                project, target_resource
            )
            if name in destination.get_attributes():
                msg = f"fixture destination already binds {name}: {target}"
                raise ValueError(msg)
            return m.Infra.ClassMoveRequest(
                rope_project=project,
                source_file=path,
                target_file=target,
                class_name=name,
                line=owner.get_start(),
                apply=False,
            )
        return None

    @classmethod
    def _helper_callable_scopes(
        cls, scope: p.Infra.RopeScope
    ) -> tuple[p.Infra.RopeScope, ...]:
        """Traverse source-owned scopes without exposing syntax nodes.

        Returns:
            Every descendant scope, depth-first, including each child itself.

        """
        return tuple(
            descendant
            for child in scope.get_scopes()
            for descendant in (child, *cls._helper_callable_scopes(child))
        )

    @staticmethod
    def _destination_imports_moving_declaration(
        project: p.Infra.RopeProject,
        source: p.Infra.RopeResource,
        name: str,
        bound: p.Infra.RopePyName,
    ) -> bool:
        """Return whether this binding imports the declaration being moved.

        Returns:
            The resulting ``bool``.

        """
        if (
            not isinstance(bound, p.Infra.RopeImportedName)
            or bound.imported_name != name
        ):
            return False
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        expected = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            project, source
        ).get_attribute(name)
        return runtime.same_name(expected, bound) and (
            runtime.imported_module_path(project, bound)
            == Path(source.real_path).resolve()
        )

    @staticmethod
    def _test_utilities_owner(
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        sources: Mapping[Path, str],
        *,
        letter: str = "u",
    ) -> Path:
        """Elect the unique declared behavior or payload facade in this tier.

        Returns:
            The resulting ``Path``.

        Raises:
            ValueError: If shared test helper requires one utilities facade.

        """
        prefix = workspace.convention(path).module_policy.project_prefix
        owners = tuple(
            candidate
            for candidate, source in sources.items()
            if candidate.parent in path.parents
            and not source.startswith(c.Infra.AUTOGEN_HEADER)
            and (policy := workspace.convention(candidate).module_policy).expected_alias
            == letter
            and policy.project_prefix == prefix
            and policy.is_internal_namespace
        )
        if len(owners) != 1:
            msg = (
                f"shared test helper requires one {letter} facade: {path}; "
                f"owners={owners}"
            )
            raise ValueError(msg)
        return owners[0]


__all__: list[str] = ["FlextInfraUtilitiesSemanticTestHelpers"]
