"""Canonical FLEXT import-law enforcement engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacadeSyntax,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._import_law import (
    FlextInfraUtilitiesImportLawGraph,
    FlextInfraUtilitiesImportLawPlacement,
    FlextInfraUtilitiesImportLawRoutes,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesImportLawNormalization(
    FlextInfraUtilitiesImportLawRoutes,
    FlextInfraUtilitiesImportLawPlacement,
    FlextInfraUtilitiesImportLawGraph,
):
    """Rewrite one module's imports into the FLEXT import law.

    The law (operator-ruling-2026-10-08-import-law), applied to every module
    of a namespace (the source package or an internal tier such as
    ``tests``) except the generated package initializers:

    1. Every import lives at module level; ``try/except ImportError`` guards
       become plain imports.
    2. Imports follow the tooling layer order (settings, config, c, t, p, m,
       u, other, base, services, api, cli): a reverse import read only in
       annotations moves under ``if TYPE_CHECKING:``; a reverse import read
       at runtime keeps its place and its finding, for manual repair.
    3. A root alias (facade and operational letters, ``config``,
       ``settings``, names the namespace root re-exports) binds through the
       module's own namespace root; facade modules keep the letters they
       declare; family packages and runtime facade dependencies retain their
       external providers, and settings/config modules keep their own law.
    4. A concrete object binds through the nearest package ``__init__`` that
       publishes it lazily.
    5. A root alias the module reads but binds nowhere is imported from its
       namespace root; an alias imported from the module's own root that the
       module also defines is dropped.

    ``make mod`` runs it over every governed file; the ``make fix`` lint
    recipe ``normalize-imports`` runs it over each file Ruff reports for
    ``import-outside-top-level``, so both verbs converge on one fixed point.
    """

    @classmethod
    def plan_import_normalization(
        cls,
        project_root: Path,
        files: t.SequenceOf[Path],
        *,
        sources: t.MappingKV[Path, str],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan import rewrites against the working sources.

        Returns:
            One plan per rewritten file, or the first planning failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        root = project_root.resolve()
        with ExitStack() as stack:
            source_project = FlextInfraUtilitiesRopeRuntime.snapshot_project(
                snapshot.engine, sources, declared_files=declared_files
            )
            stack.callback(source_project.close)
            owned = set(
                FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                    snapshot, root, project=source_project
                )
            )
            selected = tuple(sorted(owned.intersection(files)))
            resources = cls._import_law_import_resources(
                source_project, tuple(sorted(owned))
            )
            import_graph, modules = cls.snapshot_import_graph(
                source_project, resources=resources
            )
            member_resolver = (
                FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                    source_project,
                    sources={
                        module: (path, sources[path])
                        for path, module in modules.items()
                        if path in sources
                    },
                )
            )
            plans = cls._import_law_plan_import_sources(
                location=(root, selected),
                sources=sources,
                snapshot=snapshot,
                native=(source_project, import_graph, member_resolver),
            )
            if plans.failure:
                return plans
            candidate = dict(sources)
            candidate.update(
                (
                    plan.path,
                    plan.desired_content.decode(c.DEFAULT_ENCODING),
                )
                for plan in plans.value
                if plan.desired_content is not None
            )
            verified = FlextInfraUtilitiesRopeRuntime.snapshot_project(
                snapshot.engine, candidate, declared_files=declared_files
            )
            stack.callback(verified.close)
            cycles = cls.project_import_cycles(
                cls.snapshot_import_graph(
                    verified,
                    resources=cls._import_law_import_resources(
                        verified, tuple(sorted(owned))
                    ),
                )[0]
            )
            if cycles:
                message = (
                    f"canonical imports retain runtime dependency cycles in {root}: "
                    f"{sorted({tuple(sorted(group)) for group in cycles.values()})}"
                )
                return result_type.fail(message)
            return plans

    @classmethod
    def _import_law_import_resources(
        cls, project: p.Infra.RopeProject, paths: t.SequenceOf[Path]
    ) -> t.VariadicTuple[t.Infra.RopeFile]:
        """Elect only owned sources through their candidate native resources.

        Returns:
            Native resources of the selected source cohort.

        Raises:
            ValueError: If a declared source is absent from its candidate view.

        """
        resources: list[t.Infra.RopeFile] = []
        for path in paths:
            resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                project, path
            )
            if resource is None:
                message = f"import source is absent from its candidate view: {path}"
                raise ValueError(message)
            resources.append(resource)
        return tuple(resources)

    @classmethod
    def _import_law_plan_import_sources(
        cls,
        *,
        location: t.Pair[Path, t.SequenceOf[Path]],
        sources: t.MappingKV[Path, str],
        snapshot: p.Infra.WorkspaceSnapshot,
        native: t.Triple[
            p.Infra.RopeProject,
            t.MappingKV[str, frozenset[str]],
            p.Infra.RopeSourceMemberResolver,
        ],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Normalize one elected cohort through its shared source resolver.

        Returns:
            Import plans retaining their original authenticated file states.

        """
        project_root, files = location
        source_project, import_graph, member_resolver = native
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        plans: list[m.Infra.CodegenFilePlan] = []
        for path in files:
            source = sources[path]
            if source.startswith(c.Infra.AUTOGEN_HEADER):
                continue
            normalized = cls._import_law_normalize_source(
                location=(project_root, path),
                source=source,
                inputs=(import_graph, sources, source_project),
                member_resolver=member_resolver,
            )
            if normalized is None or normalized == source:
                continue
            before = (
                r[m.Cli.AtomicFileState].ok(snapshot.sources[path].state)
                if path in snapshot.sources
                else FlextInfraUtilitiesCodegenFilePlan.codegen_target_snapshot(path)
            )
            if before.failure:
                return result_type.from_failure(before)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=project_root,
                    path=path,
                    before=before.value,
                    desired_content=normalized.encode(c.DEFAULT_ENCODING),
                    desired_mode=before.value.mode
                    if before.value.content is not None
                    else config.Infra.codegen.modes.file_default,
                    owner="import-normalization",
                )
            )
        return result_type.ok(tuple(plans))

    @classmethod
    def normalize_import_source(
        cls,
        *,
        project_root: Path,
        file_path: Path,
        source: str,
        import_graph: t.MappingKV[str, frozenset[str]] | None = None,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> str | None:
        """Return the canonical form of one module, or ``None`` when unchanged.

        Returns:
            The rewritten source, or ``None`` when the module is out of scope
            or already canonical.

        Raises:
            ValueError: If the canonical candidate retains runtime import cycles.

        """
        with ExitStack() as stack:
            origin = stack.enter_context(
                FlextInfraUtilitiesRopeCore.open_import_project(project_root)
            )
            candidate = dict(sources or {})
            candidate[file_path] = source
            project = FlextInfraUtilitiesRopeRuntime.snapshot_project(origin, candidate)
            stack.callback(project.close)
            observed_graph, modules = cls.snapshot_import_graph(project)
            members = FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                project,
                sources={
                    module: (path, project.source_text(path))
                    for path, module in modules.items()
                },
            )
            normalized = cls._import_law_normalize_source(
                location=(project_root, file_path),
                source=source,
                inputs=(
                    observed_graph if import_graph is None else import_graph,
                    candidate,
                    project,
                ),
                member_resolver=members,
            )
            if normalized is None:
                return None
            candidate[file_path] = normalized
            verified = FlextInfraUtilitiesRopeRuntime.snapshot_project(
                origin, candidate
            )
            stack.callback(verified.close)
            graph, _ = cls.snapshot_import_graph(verified)
            if cycles := cls.project_import_cycles(graph):
                message = (
                    f"canonical imports retain runtime dependency cycles in "
                    f"{project_root}: "
                    f"{sorted({tuple(sorted(group)) for group in cycles.values()})}"
                )
                raise ValueError(message)
            return normalized

    @classmethod
    def _import_law_normalize_source(
        cls,
        *,
        location: t.Pair[Path, Path],
        source: str,
        inputs: t.Triple[
            t.MappingKV[str, frozenset[str]] | None,
            t.MappingKV[Path, str] | None,
            p.Infra.RopeProject | None,
        ],
        member_resolver: p.Infra.RopeSourceMemberResolver | None = None,
    ) -> str | None:
        """Normalize against the caller's existing native inventory when supplied.

        Returns:
            The canonical source, or None at the fixed point.

        Raises:
            ValueError: If the namespace has no owned package initializer.

        """
        project_root, file_path = location
        import_graph, sources, project = inputs
        if file_path.name == c.Infra.INIT_PY:
            return None
        if (
            located := cls.import_namespace(
                project_root, file_path, sources=sources, source_project=project
            )
        ) is None:
            return None
        namespace_dir, module = located
        namespace = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            namespace_dir, project_root=project_root, source_project=project
        )
        root_exports = cls.import_lazy_exports(
            project_root, namespace, sources=sources, source_project=project
        )
        if root_exports is None:
            message = f"{namespace_dir} is a namespace without an owned package init"
            raise ValueError(message)
        if import_graph is None:
            message = "import normalization requires its captured runtime graph"
            raise ValueError(message)
        facade_dependencies = cls.import_facade_dependencies(
            module,
            root_exports,
            import_graph,
        )
        current = FlextInfraUtilitiesCodegenFacadeSyntax.unalias_own_package_imports(
            package=namespace, source=source
        )
        for _ in range(c.Infra.IMPORT_NORMALIZATION_MAX_PASSES):
            tree = ast.parse(current, filename=str(file_path))
            state = m.Infra.ImportLawPass(
                scope=m.Infra.ImportLawScope(
                    project_root=project_root.resolve(),
                    file_path=file_path,
                    namespace_dir=namespace_dir,
                    module=module,
                    layer=cls.module_import_layer(module, namespace=namespace),
                    own_exports=cls._import_law_declared_exports(tree),
                    facade_dependencies=facade_dependencies,
                    family_letter=cls.family_letter(namespace_dir, file_path),
                    direct_imports=cls.import_direct_module(
                        namespace_dir,
                        file_path,
                        namespace=namespace,
                    )
                    or cls.import_bootstrap_dependency(namespace, module, import_graph),
                    bootstrap_dependency=cls.import_bootstrap_dependency(
                        namespace, module, import_graph
                    ),
                ),
                tree=tree,
                parents=cls._import_law_parent_map(tree),
                bindings=cls._module_bindings(tree),
                root_exports=root_exports,
                sources=sources,
                source_project=project,
            )
            updated = cls._import_law_one_pass(
                state,
                current,
                sources=sources,
                rope_project=inputs[2],
                member_resolver=member_resolver,
            )
            if updated is None:
                break
            current = updated
        return current if current != source else None

    @classmethod
    def _import_law_one_pass(
        cls,
        state: m.Infra.ImportLawPass,
        source: str,
        *,
        sources: t.MappingKV[Path, str] | None = None,
        rope_project: p.Infra.RopeProject | None = None,
        member_resolver: p.Infra.RopeSourceMemberResolver | None = None,
    ) -> str | None:
        """Apply the first rewrite category that changes the module.

        Every category's edits are computed against the text they mutate, so
        categories never share a pass; the caller re-parses between passes.

        Returns:
            The rewritten source, or ``None`` when every category is a no-op.

        Raises:
            ValueError: If one category plans overlapping edits.

        """
        lines = source.splitlines()
        cls._import_law_validate_import_boundary(state)
        builders = (
            lambda: cls._import_law_relative_import_edits(state, lines),
            lambda: cls._import_law_guard_edits(state.tree, lines),
            lambda: cls._import_law_placement_edits(state, lines),
            lambda: cls._import_law_root_alias_binding_edits(state, lines),
            lambda: cls._import_law_route_edits(
                state,
                lines,
                sources=sources,
                rope_project=rope_project,
                member_resolver=member_resolver,
            ),
            lambda: cls._import_law_layer_order_edits(state, lines),
        )
        for build in builders:
            edits = build()
            if not edits:
                continue
            applied = cls._import_law_apply_edits(source, edits)
            if applied is None:
                msg = f"{state.scope.file_path}: overlapping import-law edits {edits}"
                raise ValueError(msg)
            if applied != source:
                return applied
        return None

    @classmethod
    def _import_law_validate_import_boundary(cls, state: m.Infra.ImportLawPass) -> None:
        """Reject forbidden dependencies before hoisting, deferral or routing.

        Raises:
            ValueError: If a layer-zero module imports its own namespace or a
                family binds its own facade, including TYPE_CHECKING imports.

        """
        scope = state.scope
        role = (
            "layer0"
            if scope.bootstrap_dependency
            else cls.import_module_role(scope.module, namespace=scope.namespace)
        )
        for node in cls._import_law_iter_imports(state.tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                continue  # The next pass validates the absolute rewrite.
            for alias in node.names:
                target = (
                    node.module or ""
                    if isinstance(node, ast.ImportFrom)
                    else alias.name
                )
                if target != scope.namespace and not target.startswith(
                    f"{scope.namespace}."
                ):
                    continue
                if role == "layer0":
                    msg = (
                        f"{scope.file_path}: layer-zero module imports its own "
                        f"namespace: {target}"
                    )
                    raise ValueError(msg)
                if role != "family" or scope.family_letter is None:
                    continue
                provider = (
                    state.root_exports.get(alias.name, "")
                    if isinstance(node, ast.ImportFrom) and target == scope.namespace
                    else target
                )
                family = FlextInfraUtilitiesCodegenNamespace.facade_families()[
                    scope.family_letter
                ]
                if provider not in {
                    f"{scope.namespace}.{family.module}",
                    f"{scope.namespace}.{scope.family_letter}",
                } and not (
                    target == scope.namespace and alias.name == scope.family_letter
                ):
                    continue
                if (
                    isinstance(node, ast.ImportFrom)
                    and target == scope.namespace
                    and cls._import_law_enclosing_scope(node, state.parents) is None
                    and any(
                        isinstance(statement, c.Infra.AST_ASSIGNMENT_TYPES)
                        and (alias.asname or alias.name)
                        in cls._module_bindings(
                            ast.Module(body=[statement], type_ignores=[]),
                        )
                        for statement in state.tree.body
                    )
                ):
                    # The existing binding repair removes this redundant import.
                    continue
                msg = (
                    f"{scope.file_path}: family imports its own facade: "
                    f"{target}.{alias.name}"
                )
                raise ValueError(msg)

    @staticmethod
    def _import_law_declared_exports(tree: ast.Module) -> frozenset[str]:
        """Return the names one module declares in its literal ``__all__``.

        Returns:
            The resulting ``frozenset[str]``.

        """
        for node in tree.body:
            target = (
                node.targets[0]
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                else node.target
                if isinstance(node, ast.AnnAssign)
                else None
            )
            value = (
                node.value if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES) else None
            )
            if (
                isinstance(target, ast.Name)
                and target.id == "__all__"
                and isinstance(value, c.Infra.AST_SEQUENCE_DISPLAY_TYPES)
            ):
                return frozenset(
                    element.value
                    for element in value.elts
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                )
        return frozenset()


__all__: list[str] = ["FlextInfraUtilitiesImportLawNormalization"]
