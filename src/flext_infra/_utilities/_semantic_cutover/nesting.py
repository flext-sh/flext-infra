"""Automatic class-nesting plans derived from the public Rope workspace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import traceback
from collections.abc import MutableMapping
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

import libcst as cst

from flext_infra import m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverClassScope,
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
    FlextInfraUtilitiesSemanticFamilyFlatten,
)
from flext_infra._utilities._semantic_cutover.test_helpers import (
    FlextInfraUtilitiesSemanticTestHelpers,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverNesting(
    FlextInfraUtilitiesSemanticTestHelpers,
    FlextInfraUtilitiesSemanticFamilyFlatten,
    FlextInfraUtilitiesSemanticCutoverNestingCst,
    FlextInfraUtilitiesSemanticCutoverNestingOwner,
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverClassScope,
):
    """Plan class nesting from semantic module ownership instead of record lists."""

    @staticmethod
    def _inheritance_bound_to_owner(
        classes: t.MappingKV[str, ast.ClassDef],
        owner_name: str,
    ) -> frozenset[str]:
        """Return top-level classes an owner cannot contain.

        Nesting is a definition-time move, so it fails in both directions of an
        inheritance edge. A class that inherits from the owner cannot live in
        the owner's body, because a class body cannot reference the class being
        defined around it. An owner that inherits from the class cannot contain
        it either, because the owner's base list is evaluated before its body
        exists. Either move produces a NameError at import, so both are excluded
        from the plan and stay at module level.

        Returns:
            Top-level classes an owner cannot contain.

        """

        def ancestors(name: str) -> frozenset[str]:
            found: set[str] = set()
            pending = [name]
            while pending:
                for base in classes[pending.pop()].bases:
                    current: ast.expr = base
                    while isinstance(current, ast.Attribute):
                        current = current.value
                    if (
                        isinstance(current, ast.Name)
                        and current.id in classes
                        and current.id not in found
                    ):
                        found.add(current.id)
                        pending.append(current.id)
            return frozenset(found)

        return ancestors(owner_name) | {
            name for name in classes if owner_name in ancestors(name)
        }

    @classmethod
    def _suite_reference_pins(
        cls,
        tree: ast.Module,
        classes: t.MappingKV[str, ast.ClassDef],
        movable: frozenset[str],
        owner: str,
    ) -> frozenset[str]:
        """Return classes that must stay at module level to keep suite lookups.

        A nested class suite looks names up in the module globals. The owner
        name is not bound until its class statement finishes, so neither the
        bare sibling nor ``Owner.Sibling`` resolves during that suite. A base
        in the class header does see the enclosing scope. An immediate load
        from a class that is moving, or from a class already nested in the
        owner, keeps its target at module level. A class that stays outside
        also keeps the bases it names there: qualifying those bases through
        the owner fails when the owner statement has not run yet.

        Returns:
            The movable classes pinned by an immediate suite reference.

        """
        pinned = cls._pins_from_suite_loads(tree, movable, owner)
        return cls._pins_from_outside_bases(classes, movable, pinned)

    @classmethod
    def _pins_from_suite_loads(
        cls,
        tree: ast.Module,
        movable: frozenset[str],
        owner: str,
    ) -> set[str]:
        """Return classes pinned because a suite loads them immediately.

        Returns:
            The movable classes named by an immediate suite load.

        """
        pinned: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name == owner:
                continue
            for statement in node.body:
                referenced = set(cls._immediate_suite_loads(statement) & movable)
                referenced.discard(node.name)
                if not referenced:
                    continue
                if node.name in movable:
                    pinned.add(node.name)
                pinned.update(referenced)
        return pinned

    @staticmethod
    def _pins_from_outside_bases(
        classes: t.MappingKV[str, ast.ClassDef],
        movable: frozenset[str],
        pinned: set[str],
    ) -> frozenset[str]:
        """Pin bases of classes that stay at module level.

        Returns:
            ``pinned`` plus every movable base those classes name.

        """
        changed = True
        while changed:
            changed = False
            for name, node in classes.items():
                if name in movable and name not in pinned:
                    continue
                for base in node.bases:
                    current: ast.expr = base
                    while isinstance(current, ast.Attribute):
                        current = current.value
                    if (
                        isinstance(current, ast.Name)
                        and current.id in movable
                        and current.id not in pinned
                    ):
                        pinned.add(current.id)
                        changed = True
        return frozenset(pinned)

    @classmethod
    def _class_value_aliases(
        cls,
        project: p.Infra.RopeProject,
        file_path: Path,
        tree: ast.Module,
    ) -> frozenset[str]:
        """Pin nested class identities instead of treating them as loose values.

        Returns:
            Bindings holding a nested class or its instance in the same snapshot.

        Loose top-level helper and sentinel classes can move together with their
        construction sites. A class already inside an owner is not such a helper.

        """
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                file_path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            file_path,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        root_scope = module.get_scope()
        pending: list[tuple[t.Infra.RopeScope, int]] = [(root_scope, 0)]
        identities: list[t.Infra.RopePyObject] = []
        while pending:
            scope, class_depth = pending.pop()
            if scope.get_kind() == "Class":
                class_depth += 1
                if class_depth > 1:
                    identities.append(scope.pyobject)
            pending.extend((child, class_depth) for child in scope.get_scopes())
        aliases: set[str] = set()
        for statement in tree.body:
            if not isinstance(statement, ast.Assign | ast.AnnAssign):
                continue
            name = cls._loose_value_name(statement)
            value = statement.value
            if isinstance(value, ast.Call):
                value = value.func
            if name is None or not isinstance(value, ast.Name | ast.Attribute):
                continue
            resolved = FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(
                root_scope,
                value,
            )
            if resolved is not None and any(
                resolved.get_object() is identity for identity in identities
            ):
                aliases.add(name)
        return frozenset(aliases)

    @classmethod
    def _class_nesting_definitions(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject,
        pytest_patterns: t.Triple[t.StrTuple, t.StrTuple, t.StrTuple],
    ) -> p.Result[t.StrMapping]:
        """Map each loose top-level class to the owner Rope's module policy elects.

        Returns:
            The resulting ``p.Result[t.StrMapping]``.

        """
        planned = r[t.StrMapping]
        if file_path.name == "__init__.py":
            return planned.ok({})
        tree = ast.parse(source, filename=str(file_path))
        classes = {
            node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
        }
        convention = rope_workspace.convention(file_path)
        test_module = any(
            fnmatch(file_path.name, pattern) for pattern in pytest_patterns[0]
        )
        loose = cls._loose_members(
            tree,
            values=not convention.module_policy.allow_type_alias,
        )
        class_aliases = cls._class_value_aliases(project, file_path, tree)
        loose = tuple(
            name
            for name in loose
            if name not in class_aliases
            and name not in {"pytestmark", "pytest_plugins"}
        )
        if len(classes) <= 1 and not loose:
            return planned.ok({})
        registered_decorators = {"fixture", "hookimpl"} | {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "pytest"
            for alias in node.names
            if alias.name in {"fixture", "hookimpl"}
        }
        registered = tuple(
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and (
                file_path.name == "conftest.py"
                or node.name.startswith("pytest_")
                or (
                    test_module
                    and node.name
                    in {
                        "setup_module",
                        "teardown_module",
                        "setup_function",
                        "teardown_function",
                    }
                )
                or (
                    node.name.startswith("test_")
                    and not (
                        test_module
                        and cls._pytest_name_matches(node.name, pytest_patterns[2])
                    )
                )
                or any(
                    cls._tail_name(
                        decorator.func
                        if isinstance(decorator, ast.Call)
                        else decorator,
                    )
                    in registered_decorators
                    for decorator in node.decorator_list
                )
                or (
                    test_module
                    and cls._pytest_name_matches(node.name, pytest_patterns[2])
                    and any(
                        not cls._pytest_mark_decorator(decorator, tree)
                        for decorator in node.decorator_list
                    )
                )
            )
        )
        if registered:
            return planned.fail(
                f"class-nesting cannot move framework-registered functions in "
                f"{convention.module_name}: {', '.join(registered)}; "
                "the framework registration contract must move with their owner",
            )
        owned = (
            cls._test_module_owner(convention, file_path, classes, pytest_patterns[1])
            if test_module
            else cls._module_owner(
                convention,
                file_path,
                classes,
                cls._declared_names(tree),
            )
        )
        if owned.failure:
            return planned.from_failure(owned)
        owner = owned.value
        suite = classes.get(owner)
        if (
            test_module
            and suite is not None
            and any(
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and cls._pytest_name_matches(node.name, pytest_patterns[2])
                for node in tree.body
            )
            and (
                suite.bases
                or suite.keywords
                or suite.decorator_list
                or any(
                    any(
                        name in {"__test__", "pytestmark"}
                        for name in cls._scope_bindings(node)
                    )
                    or (
                        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                        and (
                            node.name
                            in {
                                "__init__",
                                "__new__",
                                "setup_class",
                                "teardown_class",
                                "setup_method",
                                "teardown_method",
                            }
                            or any(
                                cls._tail_name(
                                    decorator.func
                                    if isinstance(decorator, ast.Call)
                                    else decorator
                                )
                                in registered_decorators
                                for decorator in node.decorator_list
                            )
                        )
                    )
                    for node in suite.body
                )
            )
        ):
            return planned.fail(
                f"class-nesting cannot add free tests to {convention.module_name}.{owner}: "
                "existing suite registration or lifecycle would change",
            )
        if owner not in classes and any(
            owner in cls._scope_bindings(node) for node in tree.body
        ):
            return planned.fail(
                f"class-nesting owner {owner} collides with a module binding in "
                f"{convention.module_name}",
            )
        movable = cls._movable_members(
            tree,
            loose,
            owner=owner,
            module_name=convention.module_name,
        )
        if movable.failure:
            return planned.from_failure(movable)
        bound: frozenset[str] = (
            cls._inheritance_bound_to_owner(classes, owner)
            if owner in classes
            else frozenset()
        )
        definitions = {
            name: owner for name in classes if name != owner and name not in bound
        }
        definitions.update((name, owner) for name in movable.value)
        metadata_dependencies = (
            frozenset(
                name
                for node in tree.body
                if any(
                    binding in {"pytestmark", "pytest_plugins"}
                    for binding in cls._scope_bindings(node)
                )
                for name in cls._definition_time_names(node)
            )
            & definitions.keys()
        )
        if metadata_dependencies:
            return planned.fail(
                f"class-nesting cannot move pytest metadata dependencies in "
                f"{convention.module_name}: {', '.join(sorted(metadata_dependencies))}",
            )
        pinned = cls._suite_reference_pins(
            tree,
            classes,
            frozenset(definitions),
            owner,
        )
        family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
            file_path.name,
        ) or FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
            file_path.parent.name,
        )
        blocked = bound | pinned | (frozenset(loose) - frozenset(movable.value))
        if family is None and blocked:
            return planned.fail(
                f"class-nesting cannot safely nest {convention.module_name} under "
                f"{owner}: definition-time dependencies pin "
                f"{', '.join(sorted(blocked))}",
            )
        owner_node = classes.get(owner)
        occupied = (
            frozenset(
                name for node in owner_node.body for name in cls._scope_bindings(node)
            )
            if owner_node is not None
            else frozenset()
        )
        collisions = occupied & definitions.keys()
        if collisions:
            return planned.fail(
                f"class-nesting owner {owner} already defines "
                f"{', '.join(sorted(collisions))} in {convention.module_name}",
            )
        return planned.ok({
            name: owner for name, owner in definitions.items() if name not in pinned
        })

    @classmethod
    def _plan_class_nesting(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose helper promotion, family flattening, and orphan nesting.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        planned = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        # The planner contract keeps every failure in the Result (see
        # plan_semantic_cutover); helper promotion raises per rejected move.
        # A promotion ValueError IS the rejected move's loud contract (one
        # utilities facade, unshadowed destination, unchanged bindings), so it
        # propagates instead of demoting to a Result the caller would retry.
        promotion = planned.create_from_callable(
            lambda: cls._test_helper_edits(rope_workspace, sources),
        )
        if promotion.failure:
            error = promotion.exception
            if isinstance(error, ValueError):
                raise error
            return promotion
        promoted = promotion.value
        proposed = dict(sources)
        merged = {edit.file_path: edit for edit in promoted}
        for edit in promoted:
            proposed[edit.file_path] = edit.updated_source
        consolidated = cls._facade_namespace_edits(rope_workspace, proposed)
        for edit in consolidated:
            proposed[edit.file_path] = edit.updated_source
        flattened = cls._family_flatten_edits(rope_workspace, proposed)
        for edit in flattened:
            proposed[edit.file_path] = edit.updated_source
        nested = cls._plan_orphan_nesting(rope_workspace, proposed)
        if nested.failure:
            return planned.from_failure(nested)
        for edit in (*consolidated, *flattened, *nested.value):
            previous = merged.get(edit.file_path)
            merged[edit.file_path] = m.Infra.SemanticMigrationEdit(
                file_path=edit.file_path,
                original_source=(
                    previous.original_source if previous else edit.original_source
                ),
                updated_source=edit.updated_source,
                changes=(*previous.changes, *edit.changes)
                if previous
                else edit.changes,
            )
        return planned.ok(tuple(merged[path] for path in sorted(merged)))

    @classmethod
    def _facade_namespace_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Move duplicate facade namespaces to their declared inherited owners.

        The canonical namespace's base identities elect destinations. No symbol
        catalog participates; an occupied declaration owner is never overwritten.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SemanticMigrationEdit]``.

        """
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            workspace.rope_project,
            sources,
        )
        cutover = m.Infra.FacadeNamespaceCutover(
            project=project,
            root=Path(project.root.real_path),
            sources=sources,
            working=dict(sources),
        )
        try:
            for path, source in cls._editable_sources(sources):
                site = cls._facade_namespace_site(workspace, path, source)
                if site is not None:
                    cls._apply_facade_namespace_site(cutover, site)
            return cls._facade_namespace_result(cutover)
        finally:
            project.close()

    @classmethod
    def _facade_namespace_site(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
    ) -> m.Infra.FacadeNamespaceSite | None:
        """Resolve one source's duplicate facade site, or ``None`` to skip it.

        Returns:
            The resolved site, or ``None`` when the source declares no single
            internal composed namespace facade.

        """
        policy = workspace.convention(path).module_policy
        if not policy.is_internal_namespace or policy.expected_alias is None:
            return None
        tree = ast.parse(source)
        facade = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == policy.expected_family
            ),
            None,
        )
        if facade is None:
            return None
        children = [node for node in facade.body if isinstance(node, ast.ClassDef)]
        composed = [node for node in children if node.bases]
        if len(composed) != 1:
            return None
        namespace = composed[0]
        return m.Infra.FacadeNamespaceSite(
            path=path,
            source=source,
            facade=facade,
            namespace=namespace,
            children=tuple(children),
            tree=tree,
        )

    @classmethod
    def _apply_facade_namespace_site(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
    ) -> None:
        """Plan child moves and consumer rewrites for one resolved facade site."""
        rewrites: MutableMapping[Path, list[m.Infra.SourceRewrite]] = {}
        for child in site.children:
            if child is site.namespace or child.bases or child.decorator_list:
                continue
            cls._apply_facade_namespace_child(cutover, site, child, rewrites)
        for consumer, changes in rewrites.items():
            consumer_resource = cutover.project.get_resource(
                consumer.relative_to(cutover.root).as_posix()
            )
            cutover.working[consumer] = (
                FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                    consumer_resource,
                    cutover.sources[consumer],
                    changes,
                ).new_contents
            )

    @classmethod
    def _apply_facade_namespace_child(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
        rewrites: MutableMapping[Path, list[m.Infra.SourceRewrite]],
    ) -> None:
        """Move one duplicate child declaration and record its consumer rewrites."""
        resource = cutover.project.get_resource(
            site.path.relative_to(cutover.root).as_posix()
        )
        owner = (
            FlextInfraUtilitiesRopeCore
            .resolve_pymodule(cutover.project, resource)
            .get_attribute(site.facade.name)
            .get_object()
        )
        target = owner.get_attribute(site.namespace.name).get_object()
        destinations = [
            base for base in target.get_superclasses() if base.get_name() == child.name
        ]
        if len(destinations) != 1:
            return
        destination_path = cls._facade_namespace_destination(
            cutover,
            site,
            child,
            destinations[0],
        )
        binding = owner.get_attribute(child.name)
        for consumer, rewrite in cls._collect_namespace_occurrence_rewrites(
            cutover,
            binding,
            child.name,
            site.namespace.name,
        ):
            rewrites.setdefault(consumer, []).append(rewrite)
        child_cst = cls._facade_namespace_child_cst(site, child)
        cutover.working[destination_path] = cls._facade_namespace_child_module(
            site.tree,
            child,
            child_cst,
        )
        rewrites.setdefault(site.path, []).append(
            cls._facade_namespace_removal(site.source, child)
        )

    @classmethod
    def _facade_namespace_destination(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
        destination: t.Infra.RopePyObject,
    ) -> Path:
        """Resolve one child's inherited declaration-owner destination.

        Returns:
            The editable path that carries the child's declaration owner.

        Raises:
            ValueError: If the owner has no scope, no module resource, lies
                outside the editable inventory, or is already occupied.

        """
        if destination.get_scope() is None:
            msg = "namespace declaration owner has no source scope"
            raise ValueError(msg)
        module = destination.get_module()
        if module is None or (destination_resource := module.get_resource()) is None:
            msg = "namespace declaration owner has no module resource"
            raise ValueError(msg)
        destination_path = Path(destination_resource.real_path).resolve()
        if destination_path not in cutover.sources or destination_path == site.path:
            msg = "namespace declaration owner is outside the editable inventory"
            raise ValueError(msg)
        declaration = next(
            node
            for node in ast.parse(cutover.sources[destination_path]).body
            if isinstance(node, ast.ClassDef) and node.name == child.name
        )
        if declaration.bases or any(
            not isinstance(node, ast.Pass)
            and not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            for node in declaration.body
        ):
            msg = "namespace declaration owner is already occupied"
            raise ValueError(msg)
        return destination_path

    @staticmethod
    def _facade_namespace_child_cst(
        site: m.Infra.FacadeNamespaceSite,
        child: ast.ClassDef,
    ) -> cst.ClassDef:
        """Extract one facade child's concrete-syntax node.

        Returns:
            The child's CST class definition.

        Raises:
            TypeError: If the facade body is not an indented declaration.

        """
        parsed = cst.parse_module(site.source)
        facade_cst = next(
            node
            for node in parsed.body
            if isinstance(node, cst.ClassDef) and node.name.value == site.facade.name
        )
        if not isinstance(facade_cst.body, cst.IndentedBlock):
            msg = "namespace facade requires an indented declaration"
            raise TypeError(msg)
        return next(
            node
            for node in facade_cst.body.body
            if isinstance(node, cst.ClassDef) and node.name.value == child.name
        )

    @staticmethod
    def _facade_namespace_child_module(
        tree: ast.Module,
        child: ast.ClassDef,
        child_cst: cst.ClassDef,
    ) -> str:
        """Render one relocated child module with the imports it still uses.

        Returns:
            The relocated child's module source text.

        """
        used = {node.id for node in ast.walk(child) if isinstance(node, ast.Name)}
        imports = [
            node
            for node in tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
            and any(
                (alias.asname or alias.name.partition(".")[0]) in used
                for alias in node.names
            )
        ]
        return (
            "from __future__ import annotations\n\n"
            + "\n".join(ast.unparse(node) for node in imports)
            + "\n\n"
            + cst.Module(body=(child_cst,)).code
            + f"\n__all__ = [{child.name!r}]\n"
        )

    @staticmethod
    def _facade_namespace_removal(
        source: str,
        child: ast.ClassDef,
    ) -> m.Infra.SourceRewrite:
        """Compute the byte range removing a relocated child from its facade.

        Returns:
            The deletion rewrite for the child's source span.

        Raises:
            ValueError: If the child has no complete source range.

        """
        if child.end_lineno is None:
            msg = "namespace declaration has no complete source range"
            raise ValueError(msg)
        lines = source.splitlines(keepends=True)
        start = sum(map(len, lines[: child.lineno - 1]))
        end = sum(map(len, lines[: child.end_lineno]))
        return m.Infra.SourceRewrite(start=start, end=end, text="")

    @classmethod
    def _collect_namespace_occurrence_rewrites(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
        binding: t.Infra.RopePyName,
        child_name: str,
        namespace_name: str,
    ) -> t.VariadicTuple[t.Pair[Path, m.Infra.SourceRewrite]]:
        """Collect consumer rewrites for one duplicate namespace declaration.

        Every non-defining occurrence of the duplicate child name across the
        editable sources is rewritten to the canonical namespace name.

        Returns:
            Each consumer path paired with the canonical-name rewrite it needs.

        """
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            cutover.project,
            child_name,
            binding,
            imports=True,
            in_hierarchy=False,
        )
        collected: list[t.Pair[Path, m.Infra.SourceRewrite]] = []
        for consumer, _consumer_source in cls._editable_sources(cutover.sources):
            consumer_resource = cutover.project.get_resource(
                consumer.relative_to(cutover.root).as_posix()
            )
            for occurrence in finder.find_occurrences(resource=consumer_resource):
                if occurrence.is_defined():
                    continue
                start, end = occurrence.get_word_range()
                collected.append((
                    consumer,
                    m.Infra.SourceRewrite(
                        start=start,
                        end=end,
                        text=namespace_name,
                    ),
                ))
        return tuple(collected)

    @classmethod
    def _facade_namespace_result(
        cls,
        cutover: m.Infra.FacadeNamespaceCutover,
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Assemble the edits for every path whose prospective bytes changed.

        Returns:
            The edits for every source whose prospective bytes changed.

        """
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=source,
                updated_source=cutover.working[path],
                changes=(
                    (
                        "consolidated facade namespace through declaration-owner "
                        "inheritance"
                    ),
                ),
            )
            for path, source in cutover.sources.items()
            if cutover.working[path] != source
        )

    @classmethod
    def _plan_orphan_nesting(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan all structural nesting and consumer rewrites without effects.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        planned_edits = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        modules = {
            entry.file_path.resolve(): entry for entry in rope_workspace.modules()
        }
        editable = cls._editable_sources(sources)
        owned = tuple(item for item in editable if item[0] in modules)
        # Parse native collection policy without importing consumer conftests or
        # installed plugins. Planning must not execute their registration hooks.
        pytest_patterns = cls._pytest_collection_patterns(
            Path(rope_workspace.rope_project.root.real_path),
        )
        project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            rope_workspace.rope_project,
            sources,
        )

        def definitions_for(item: t.Pair[Path, str]) -> p.Result[t.StrMapping]:
            try:
                return cls._class_nesting_definitions(
                    rope_workspace,
                    *item,
                    project=project,
                    pytest_patterns=pytest_patterns,
                )
            except Exception:
                traceback.print_exc()
                raise

        planned = r[t.StrMapping].traverse(owned, definitions_for, fail_fast=False)
        if planned.failure:
            project.close()
            return planned_edits.from_failure(planned)
        definitions_by_file = {
            path: definitions
            for (path, _source), definitions in zip(owned, planned.value, strict=True)
            if definitions
        }
        module_names = {
            path: modules[path].module_name
            or FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
                project.get_resource(modules[path].resource_path),
            ).get_name()
            for path, _source in owned
        }
        bindings_by_module: MutableMapping[str, MutableMapping[str, str]] = {}
        for path, definitions in definitions_by_file.items():
            module_name = module_names[path]
            bindings = bindings_by_module.setdefault(module_name, {})
            for name, owner in definitions.items():
                if bindings.setdefault(name, owner) != owner:
                    project.close()
                    return planned_edits.fail(
                        f"ambiguous class-nesting owner for {module_name}.{name}: "
                        f"{bindings[name]}, {owner}",
                    )
        nested_names = frozenset(
            name for bindings in bindings_by_module.values() for name in bindings
        )
        if not nested_names:
            project.close()
            return planned_edits.ok(())
        try:
            quoted = cls._nesting_quoted_sources(
                project,
                dict(editable),
                definitions_by_file,
            )

            def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
                module = modules.get(path)
                definitions = definitions_by_file.get(path, {})
                updated = cls._rewrite_class_nesting_source(
                    quoted[path],
                    native=(
                        project,
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix(),
                        ),
                    ),
                    scope=(
                        module_names.get(path, ""),
                        module.is_package_init if module is not None else False,
                    ),
                    bindings_by_module=bindings_by_module,
                    definitions=definitions,
                )
                if definitions and updated == source:
                    msg = "class-nesting owner produced no structural edit"
                    raise ValueError(msg)
                return updated, tuple(
                    f"nested {name} under {owner}"
                    for name, owner in definitions.items()
                ) or ("rewired nested-class consumer",)

            return cls._semantic_edits(
                tuple(
                    (path, source)
                    for path, source in editable
                    if path in definitions_by_file
                    or quoted[path] != source
                    or any(name in source for name in nested_names)
                ),
                rewrite,
            )
        finally:
            project.close()


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNesting"]
