"""Canonical FLEXT import-law enforcement engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from contextlib import ExitStack
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
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
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover.own_mro import (
    FlextInfraUtilitiesSemanticCutoverOwnMro,
)


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
            sources = {path: source_project.source_text(path) for path in owned}
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
            runtime_diagnostics: dict[str, t.StrTuple] = {}
            plans = cls._import_law_plan_import_sources(
                location=(root, selected),
                sources=sources,
                snapshot=snapshot,
                native=(source_project, import_graph, member_resolver),
                runtime_diagnostics=runtime_diagnostics,
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
            if message := cls._import_law_cycle_message(
                root, verified, tuple(sorted(owned)), runtime_diagnostics
            ):
                return result_type.fail(message)
            return plans

    @classmethod
    def _import_law_cycle_message(
        cls,
        root: Path,
        project: p.Infra.RopeProject,
        paths: t.SequenceOf[Path],
        runtime_diagnostics: t.MappingKV[str, t.StrTuple],
    ) -> str | None:
        """Describe retained cycles using the verified candidate's native graph.

        Returns:
            The cycle diagnostic, or None when the candidate has no cycles.

        """
        graph, modules = cls.snapshot_import_graph(
            project, resources=cls._import_law_import_resources(project, paths)
        )
        cycles = cls.project_import_cycles(graph)
        if not cycles:
            return None
        statements = cls.import_cycle_statements(project, cycles, modules)
        reads = tuple(
            (module, runtime_diagnostics.get(module, ())) for module in sorted(cycles)
        )
        edges = tuple(
            (module, tuple(sorted(graph[module] & cycles[module])))
            for module in sorted(cycles)
        )
        return (
            f"canonical imports retain runtime dependency cycles in {root}: "
            f"{sorted({tuple(sorted(group)) for group in cycles.values()})}"
            f"; candidate_cycle_edges={edges}"
            f"; candidate_top_level_imports={statements}"
            f"; normalizer_runtime_reads={reads}"
        )

    @classmethod
    def _import_law_import_resources(
        cls, project: p.Infra.RopeProject, paths: t.SequenceOf[Path]
    ) -> t.VariadicTuple[t.Infra.RopeFile]:
        """Elect only owned sources through their candidate native resources.

        Args:
            project: The native project providing the candidate resources.
            paths: The sequence of file paths to resolve into native resources.

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
        runtime_diagnostics: t.MutableMappingKV[str, t.StrTuple] | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Normalize one elected cohort through its shared source resolver.

        Args:
            location: A pair of the project root and the sequence of file paths to
              normalize.
            sources: A mapping from file paths to their source content.
            snapshot: The workspace snapshot capturing the current state of the files.
            native: A triple containing the source project, the import graph, and the
              member resolver.
            runtime_diagnostics: Optional evidence sink for rejected candidates.

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
                runtime_diagnostics=runtime_diagnostics,
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
            working_sources = {path: project.source_text(path) for path in modules}
            members = FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                project,
                sources={
                    module: (path, working_sources[path])
                    for path, module in modules.items()
                },
            )
            normalized = cls._import_law_normalize_source(
                location=(project_root, file_path),
                source=source,
                inputs=(
                    observed_graph if import_graph is None else import_graph,
                    working_sources,
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
        runtime_diagnostics: t.MutableMappingKV[str, t.StrTuple] | None = None,
    ) -> str | None:
        """Normalize against the caller's existing native inventory when supplied.

        Returns:
            The canonical source, or None at the fixed point.

        Raises:
            ValueError: If the namespace has no owned package initializer.

        """
        project_root, file_path = location
        import_graph = inputs[0]
        sources = inputs[1]
        if file_path.name == c.Infra.INIT_PY:
            return None
        if (
            located := cls.import_namespace(
                project_root, file_path, sources=sources, source_project=inputs[2]
            )
        ) is None:
            return None
        namespace_dir, module = located
        namespace = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            namespace_dir, project_root=project_root, source_project=inputs[2]
        )
        root_exports = cls.import_lazy_exports(
            project_root, namespace, sources=sources, source_project=inputs[2]
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
        state: m.Infra.ImportLawPass | None = None
        for _ in range(c.Infra.IMPORT_NORMALIZATION_MAX_PASSES):
            tree = ast.parse(current, filename=str(file_path))
            parents = FlextInfraUtilitiesRopeAnalysis.ast_parent_map(tree)
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
                parents=parents,
                bindings=cls._module_bindings(tree),
                root_exports=root_exports,
                sources=sources,
                source_project=inputs[2],
                deferred_class_lines=cls._import_law_deferred_class_lines(
                    tree, parents, module, member_resolver
                ),
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
        else:
            message = f"{file_path}: import normalization has no validated fixed point"
            raise ValueError(message)
        if runtime_diagnostics is not None and state is not None:
            runtime_diagnostics[module] = cls._import_law_runtime_diagnostics(state)
        return current if current != source else None

    @classmethod
    def _import_law_deferred_class_lines(
        cls,
        tree: ast.Module,
        parents: t.MappingKV[int, ast.AST],
        module: str,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> frozenset[int]:
        """Collect class lines whose native ancestry defers their annotations.

        Returns:
            Lines of positively proven deferred class declarations.

        """
        if member_resolver is None or not cls._import_law_defers_annotations(tree):
            return frozenset()
        lines: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not any(
                isinstance(statement, ast.AnnAssign) for statement in node.body
            ):
                continue
            attributes = [node.name]
            parent = parents.get(id(node))
            while isinstance(parent, ast.ClassDef):
                attributes.append(parent.name)
                parent = parents.get(id(parent))
            qualified = m.Infra.SourceClassReference(
                target=module, attributes=tuple(reversed(attributes))
            )
            deferred = parent is tree and member_resolver.class_defers_annotations(
                qualified
            )
            u.Cli.info(
                f"annotation classification module={module} "
                f"class={'.'.join(qualified.attributes)} line={node.lineno} "
                f"module_parent={parent is tree} deferred={deferred} "
                f"owner={__file__}"
            )
            if deferred:
                lines.add(node.lineno)
        return frozenset(lines)

    @classmethod
    def _import_law_runtime_diagnostics(
        cls, state: m.Infra.ImportLawPass
    ) -> t.StrTuple:
        """Describe the existing classifier's reads without changing placement.

        Returns:
            Binding positions and their existing lexical classification context.

        """
        evidence: list[str] = []
        for node in cls._import_law_iter_imports(state.tree):
            for alias in node.names:
                bound = alias.asname or alias.name.partition(".")[0]
                for read in cls._import_law_runtime_reads(state, bound):
                    context: list[str] = []
                    child: ast.AST = read
                    parent = state.parents.get(id(read))
                    while parent is not None:
                        if isinstance(parent, ast.ClassDef):
                            context.append(
                                f"class={parent.name}:{parent.lineno},"
                                "deferred="
                                f"{parent.lineno in state.deferred_class_lines}"
                            )
                        elif isinstance(parent, ast.AnnAssign):
                            context.append(
                                f"annotation={parent.lineno}"
                                if child is parent.annotation
                                else f"assignment-value={parent.lineno}"
                            )
                        elif isinstance(parent, c.Infra.AST_FUNCTION_TYPES):
                            context.append(f"function={parent.name}:{parent.lineno}")
                        child, parent = parent, state.parents.get(id(parent))
                    evidence.append(
                        f"{bound}@{read.lineno}:{read.col_offset + 1} "
                        f"parent={type(state.parents[id(read)]).__name__} "
                        f"context={tuple(context)}"
                    )
        return tuple(evidence)

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
        repaired = cls._import_law_own_family_candidate(
            state, source, member_resolver=member_resolver
        )
        if repaired is not None:
            return repaired
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
                cls._import_law_validate_transition(state, applied, edits)
                return applied
        return None

    @staticmethod
    def _import_law_validate_transition(
        state: m.Infra.ImportLawPass,
        candidate: str,
        edits: t.SequenceOf[tuple[int, int, t.StrSequence]],
    ) -> None:
        """Preserve the first syntax failure with its exact line-edit transition.

        Raises:
            SyntaxError: A rewrite produced an invalid candidate.

        """
        try:
            ast.parse(candidate, filename=str(state.scope.file_path))
        except SyntaxError as exc:
            line = exc.lineno or 1
            context = candidate.splitlines()[max(0, line - 4) : line + 1]
            exc.add_note(
                f"import normalization transition: module={state.scope.module}; "
                f"edits={edits}; candidate_lines={context}"
            )
            raise

    @classmethod
    def _import_law_own_family_candidate(
        cls,
        state: m.Infra.ImportLawPass,
        source: str,
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> str | None:
        """Elect only native identity-preserving own-family member replacements.

        Returns:
            A corrective candidate for the next validated pass, or no correction.

        Raises:
            ValueError: An elected reference has no safe published non-self owner.

        """
        scope = state.scope
        if scope.family_letter is None or scope.direct_imports:
            return None
        elected = cls._import_law_own_family_imports(state)
        if not elected:
            return None
        if member_resolver is None or state.source_project is None:
            message = "Own-family repair requires native source identity; use make mod"
            raise ValueError(message)
        routes: dict[t.StrTuple, t.Triple[str, str, str]] = {}
        for bound, (module, name) in elected.items():
            paths = cls._import_law_consumed_facade_paths(state, bound)
            if not paths:
                message = "Own-family facade-value reads require make mod"
                raise ValueError(message)
            for path in paths:
                route = cls._import_law_own_family_route(
                    state,
                    f"{module}.{name}.{'.'.join(path)}",
                    path[-1],
                    member_resolver=member_resolver,
                )
                if any(
                    owner == route[1] and provider != route[0]
                    for provider, owner, _ in routes.values()
                ):
                    message = "Own-family exports have competing bindings; use make mod"
                    raise ValueError(message)
                routes[bound, *path] = route
        cls._import_law_own_family_annotations(state.tree)
        return FlextInfraUtilitiesSemanticCutoverOwnMro.rewrite_own_family_members(
            source, routes, {bound: route[0] for bound, route in elected.items()}
        )

    @classmethod
    def _import_law_own_family_imports(
        cls, state: m.Infra.ImportLawPass
    ) -> t.MappingKV[str, t.Pair[str, str]]:
        """Elect root imports that the existing own-family boundary rejects.

        Returns:
            Native lookup module and original imported name per lexical binding.

        Raises:
            ValueError: More than one elected import binds the same name.

        """
        scope = state.scope
        if scope.family_letter is None:
            return {}
        family = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            scope.family_letter
        ]
        imports: dict[str, t.Pair[str, str]] = {}
        for node in cls._import_law_iter_imports(state.tree):
            if (
                not isinstance(node, ast.ImportFrom)
                or node.level
                or node.module is None
                or node.module != scope.namespace
            ):
                continue
            for alias in node.names:
                provider = state.root_exports.get(alias.name, "")
                if not (
                    alias.name == scope.family_letter
                    or provider == f"{scope.namespace}.{family.module}"
                ):
                    continue
                bound = alias.asname or alias.name
                if bound in imports:
                    message = "Own-family repair has competing imports; use make mod"
                    raise ValueError(message)
                imports[bound] = node.module, alias.name
        return imports

    @classmethod
    def _import_law_own_family_route(
        cls,
        state: m.Infra.ImportLawPass,
        qualified: str,
        member: str,
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver,
    ) -> t.Triple[str, str, str]:
        """Prove a member and its exported declaring owner share native identities.

        Returns:
            Published module, declaring owner and relative member path.

        Raises:
            ValueError: The native member or exported owner changes identity.

        """
        project = state.source_project
        if project is None:
            message = "Own-family repair requires a native project; use make mod"
            raise ValueError(message)
        before = member_resolver(qualified)
        holder, owners = cls._import_law_own_family_owner(before, state.scope.module)
        module = holder.get_name().rpartition(".")[0]
        cls._import_law_own_family_publication(state, project, module, owners[0])
        exported = cls.resolve_declared_binding(
            project, module, owners[0], state.scope.project_root, state.sources or {}
        )
        declared = holder.get_scope().get_defined_names().get(owners[0])
        suffix = ".".join((*owners[1:], member))
        after = member_resolver(f"{module}.{owners[0]}.{suffix}")
        if (
            exported is None
            or declared is None
            or not FlextInfraUtilitiesRopeRuntime.same_name(exported, declared)
            or not FlextInfraUtilitiesRopeRuntime.same_name(before, after)
        ):
            message = "Own-family replacement changes native identity; use make mod"
            raise ValueError(message)
        return module, owners[0], suffix

    @staticmethod
    def _import_law_own_family_owner(
        binding: p.Infra.RopePyName, current_module: str
    ) -> t.Pair[p.Infra.RopeParsedModule, t.StrTuple]:
        """Read enclosing native class scopes at the exact declaration location.

        Returns:
            Declaring native module and nonempty outer-to-inner class path.

        Raises:
            ValueError: The declaration is unresolved, self-owned or not in a facade.

        """
        holder, line = binding.get_definition_location()
        if holder is None or line is None or holder.get_name() == current_module:
            message = "Own-family repair has an unresolved or self owner; use make mod"
            raise ValueError(message)
        scope = holder.get_scope().get_inner_scope_for_line(line)
        if scope.get_start() == line:
            scope = scope.parent
        owners: list[str] = []
        while scope is not None and scope.get_kind() == "Class":
            owners.append(scope.pyobject.get_name())
            scope = scope.parent
        if not owners:
            message = "Own-family member has no declaring facade; use make mod"
            raise ValueError(message)
        return holder, tuple(reversed(owners))

    @staticmethod
    def _import_law_own_family_publication(
        state: m.Infra.ImportLawPass,
        project: p.Infra.RopeProject,
        module: str,
        owner: str,
    ) -> None:
        """Authenticate the nearest native package's lazy publication.

        Raises:
            TypeError: The native publisher is not a package resource.
            ValueError: No non-self lazy export publishes the declaring owner.

        """
        published = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
            project.get_module(module)
        )
        resource = published.get_resource()
        if not isinstance(resource, p.Infra.RopeRoot):
            message = "Own-family owner has no native publishing package; use make mod"
            raise TypeError(message)
        init = resource.get_child(c.Infra.INIT_PY)
        path = Path(init.real_path).resolve()
        source = (
            state.sources[path]
            if state.sources is not None and path in state.sources
            else FlextInfraUtilitiesRopeRuntime.require_file_resource(init, path).read()
        )
        routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
            module, path, source, project=project, pymodule=published
        )
        if owner not in routes or module == state.scope.module:
            message = "Own-family owner has no non-self lazy export; use make mod"
            raise ValueError(message)

    @staticmethod
    def _import_law_own_family_annotations(tree: ast.Module) -> None:
        """Reject quoted annotations outside this bounded corrective category.

        Raises:
            ValueError: An annotation requires canonical structural rewriting.

        """
        for node in ast.walk(tree):
            annotation = (
                node.annotation
                if isinstance(node, (ast.AnnAssign, ast.arg))
                else node.returns
                if isinstance(node, c.Infra.AST_FUNCTION_TYPES)
                else node.value
                if isinstance(node, ast.TypeAlias)
                else None
            )
            if annotation is not None and any(
                isinstance(part, ast.Constant) and isinstance(part.value, str)
                for part in ast.walk(annotation)
            ):
                message = "Own-family quoted annotations require make mod"
                raise ValueError(message)

    @classmethod
    def _import_law_validate_import_boundary(cls, state: m.Infra.ImportLawPass) -> None:
        """Reject forbidden dependencies before hoisting, deferral or routing.

        Raises:
            ValueError: If a layer-zero module imports a non-foundation dependency or a
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
                    if cls.import_law_layer_zero_helper(state, target):
                        continue
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

    @classmethod
    def import_law_layer_zero_helper(
        cls, state: m.Infra.ImportLawPass, target: str
    ) -> bool:
        """Prove an own helper against the complete native candidate dependency graph.

        Returns:
            Whether the helper has authenticated, acyclic foundation dependencies.

        Raises:
            ValueError: If the native candidate inventory is missing or cyclic.
            TypeError: If a helper does not expose a native module declaration.

        """
        if state.source_project is None or state.sources is None:
            message = (
                "layer-zero helper admission requires the complete native candidate"
            )
            raise ValueError(message)
        graph: dict[str, frozenset[str]] = {}
        pending = [target]
        while pending:
            module = pending.pop()
            if module in graph:
                continue
            if (
                module == state.scope.namespace
                or cls.import_module_role(module, namespace=state.scope.namespace)
                == "family"
            ):
                return False
            parsed = FlextInfraUtilitiesRopeRuntime.require_parsed_module(
                state.source_project.get_module(module)
            )
            resource = parsed.get_resource()
            if (
                resource is None
                or Path(resource.real_path).resolve() not in state.sources
            ):
                message = f"layer-zero helper is absent from the candidate: {module}"
                raise ValueError(message)
            tree = state.tree if module == state.scope.module else parsed.get_ast()
            if not isinstance(tree, ast.Module):
                message = f"layer-zero helper has no native module tree: {module}"
                raise TypeError(message)
            edges = cls._import_law_layer_zero_edges(state, module, tree)
            if edges is None:
                return False
            if module in edges:
                message = f"layer-zero helper has a self dependency: {module}"
                raise ValueError(message)
            graph[module] = edges
            pending.extend(edges - graph.keys())
        if cls.project_import_cycles(graph):
            message = f"layer-zero helper retains candidate dependency cycles: {target}"
            raise ValueError(message)
        return True

    @classmethod
    def _import_law_layer_zero_edges(
        cls, state: m.Infra.ImportLawPass, module: str, tree: ast.Module
    ) -> frozenset[str] | None:
        """Read native helper dependencies, including type-checking-only imports.

        Returns:
            Own candidate edges, or None for a facade dependency.

        Raises:
            ValueError: If native identity cannot be established.

        """
        if state.source_project is None:
            message = "layer-zero helper edges require a native source project"
            raise ValueError(message)
        edges: set[str] = set()
        for node in cls._import_law_iter_imports(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue  # Compiler features do not load a schema dependency.
            if isinstance(node, ast.ImportFrom) and node.level:
                provider = ".".join(module.split(".")[: -node.level])
                provider = f"{provider}.{node.module}" if node.module else provider
            else:
                provider = node.module or "" if isinstance(node, ast.ImportFrom) else ""
            for alias in node.names:
                dependency = (
                    provider if isinstance(node, ast.ImportFrom) else alias.name
                )
                native = (
                    FlextInfraUtilitiesRopeRuntime
                    .qualified_name(
                        state.source_project, alias.name, module_name=dependency
                    )
                    .get_object()
                    .get_module()
                    if isinstance(node, ast.ImportFrom)
                    else FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                        state.source_project.get_module(dependency)
                    )
                )
                if (
                    native is None
                    or cls.import_module_role(native.get_name()) == "family"
                ):
                    return None
                if dependency == state.scope.namespace or dependency.startswith(
                    f"{state.scope.namespace}."
                ):
                    edges.add(dependency)
        return frozenset(edges)

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
