"""Canonical FLEXT import-law enforcement engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import ClassVar

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
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
    FlextInfraUtilitiesRopeModulePatch,
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
    2. Imports follow the tooling layer order (settings, config, c, p, t, p, m,
       u, other, base, services, api, cli). An enclosing facade that depends on
       its fragment is also a reverse edge, even at the same layer. A reverse
       import read only in annotations moves under ``if TYPE_CHECKING:``; a
       runtime read keeps its place and its finding for repair.
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

    # Shared totals for one pass. Deferred classes keep one diagnostic row;
    # the pass owner emits the aggregate without repeating every class.
    _annotation_classified: ClassVar[t.Infra.MutableSetOf[tuple[str, str, int]]] = set()
    _annotation_deferred: ClassVar[t.Infra.MutableSetOf[tuple[str, str, int]]] = set()

    @classmethod
    def _import_law_annotation_summary(cls) -> None:
        """Emit one aggregate annotation-classification row and reset totals."""
        if not cls._annotation_classified:
            return
        u.Cli.info(
            "annotation classification summary "
            f"modules={len({module for module, _, _ in cls._annotation_classified})} "
            f"classes={len(cls._annotation_classified)} "
            f"deferred={len(cls._annotation_deferred)}"
        )
        cls._annotation_classified.clear()
        cls._annotation_deferred.clear()

    @classmethod
    def plan_import_normalization(
        cls,
        project_root: Path,
        files: Sequence[Path],
        *,
        sources: Mapping[Path, str],
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan import rewrites at this phase's declared result boundary.

        A typed failure of ``u.Infra.MOD_MODULE_FAILURE_TYPES`` born for
        one module (its context names ``c.Infra.MOD_FAILURE_MODULE_KEY``)
        becomes the phase's failed result, so its ``error_data`` attributes
        the module. Every engine exception escapes unchanged.

        Returns:
            One plan per rewritten file, or the first planning failure.

        """
        attempt = r.safe(
            cls._plan_import_normalization_phase,
            exceptions=FlextInfraUtilitiesWorkspaceSnapshot.MOD_MODULE_FAILURE_TYPES,
        )(
            project_root,
            files,
            sources=sources,
            declared_files=declared_files,
            snapshot=snapshot,
        )
        if attempt.failure:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(attempt)
        return attempt.value

    @classmethod
    def _plan_import_normalization_phase(
        cls,
        project_root: Path,
        files: Sequence[Path],
        *,
        sources: Mapping[Path, str],
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan import rewrites against the working sources.

        Returns:
            One plan per rewritten file, or the first planning failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
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
        paths: Sequence[Path],
        runtime_diagnostics: Mapping[str, t.StrTuple],
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
        cls, project: p.Infra.RopeProject, paths: Sequence[Path]
    ) -> tuple[t.Infra.RopeFile, ...]:
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
        location: tuple[Path, Sequence[Path]],
        sources: Mapping[Path, str],
        snapshot: p.Infra.WorkspaceSnapshot,
        native: tuple[
            p.Infra.RopeProject,
            Mapping[str, frozenset[str]],
            p.Infra.RopeSourceMemberResolver,
        ],
        runtime_diagnostics: MutableMapping[str, t.StrTuple] | None = None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
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
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        plans: list[p.Infra.CodegenFilePlan] = []
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
            if normalized.failure:
                return result_type.from_failure(normalized)
            if normalized.value == source:
                continue
            normalized_source = normalized.value
            before = (
                r[p.Cli.AtomicFileState].ok(snapshot.sources[path].state)
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
                    desired_content=normalized_source.encode(c.DEFAULT_ENCODING),
                    desired_mode=before.value.mode
                    if before.value.content is not None
                    else config.Infra.codegen.modes.file_default,
                    owner="import-normalization",
                )
            )
        cls._import_law_annotation_summary()
        cls._publication_scan_summary()
        return result_type.ok(tuple(plans))

    @classmethod
    def normalize_import_source(
        cls,
        *,
        project_root: Path,
        file_path: Path,
        source: str,
        import_graph: Mapping[str, frozenset[str]] | None = None,
        sources: Mapping[Path, str] | None = None,
    ) -> p.Result[str]:
        """Return the canonical form of one module.

        Returns:
            The rewritten source, the unchanged source when the module is out
            of scope or already canonical, or the typed failure of the
            attempted pass.

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
            cls._import_law_annotation_summary()
            cls._publication_scan_summary()
            if normalized.failure:
                return normalized
            candidate[file_path] = normalized.value
            verified = FlextInfraUtilitiesRopeRuntime.snapshot_project(
                origin, candidate
            )
            stack.callback(verified.close)
            graph, _ = cls.snapshot_import_graph(verified)
            if cycles := cls.project_import_cycles(graph):
                return r[str].fail(
                    f"canonical imports retain runtime dependency cycles in "
                    f"{project_root}: "
                    f"{sorted({tuple(sorted(group)) for group in cycles.values()})}",
                )
            return r[str].ok(value=normalized.value)

    @classmethod
    def _import_law_normalize_source(
        cls,
        *,
        location: tuple[Path, Path],
        source: str,
        inputs: tuple[
            Mapping[str, frozenset[str]] | None,
            Mapping[Path, str] | None,
            p.Infra.RopeProject | None,
        ],
        member_resolver: p.Infra.RopeSourceMemberResolver | None = None,
        runtime_diagnostics: MutableMapping[str, t.StrTuple] | None = None,
    ) -> p.Result[str]:
        """Normalize against the caller's existing native inventory when supplied.

        Returns:
            The canonical source, the unchanged source at the fixed point, or
            the first typed classification failure of the normalization pass.

        """
        prepared = cls._import_law_initial_pass_state(
            location, source, inputs, member_resolver=member_resolver
        )
        if prepared.failure:
            return r[str].from_failure(prepared)
        state, current = prepared.value
        if state is None:
            return r[str].ok(value=source)
        for _ in range(c.Infra.IMPORT_NORMALIZATION_MAX_PASSES):
            updated = cls._import_law_one_pass(
                state,
                current,
                sources=inputs[1],
                rope_project=inputs[2],
                member_resolver=member_resolver,
            )
            if updated.failure:
                return updated
            if updated.value == current:
                break
            current = updated.value
            state = cls._import_law_refreshed_tree(
                state,
                current,
                member_resolver=member_resolver,
            )
        else:
            return r[str].fail(
                f"{state.scope.file_path}: import normalization has no "
                "validated fixed point",
            )
        if runtime_diagnostics is not None:
            runtime_diagnostics[state.scope.module] = (
                cls._import_law_runtime_diagnostics(state)
            )
        return r[str].ok(value=current)

    @classmethod
    def _import_law_initial_pass_state(
        cls,
        location: tuple[Path, Path],
        source: str,
        inputs: tuple[
            Mapping[str, frozenset[str]] | None,
            Mapping[Path, str] | None,
            p.Infra.RopeProject | None,
        ],
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> p.Result[tuple[p.Infra.ImportLawPass | None, str]]:
        """Elect the namespace, authenticate the candidate and build one pass.

        Returns:
            The initial pass state with its cleaned current text, an empty
            state for an out-of-scope source, or the typed failure of an
            unauthenticated or unroutable candidate.

        """
        project_root, file_path = location
        import_graph = inputs[0]
        sources = inputs[1]
        located = (
            None
            if file_path.name == c.Infra.INIT_PY
            else cls.import_namespace(
                project_root, file_path, sources=sources, source_project=inputs[2]
            )
        )
        if located is None:
            return r[tuple[p.Infra.ImportLawPass | None, str]].ok(
                value=(None, source),
            )
        namespace_dir, module = located
        namespace = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            namespace_dir, project_root=project_root, source_project=inputs[2]
        )
        root_exports = cls.import_lazy_exports(
            project_root, namespace, sources=sources, source_project=inputs[2]
        )
        if root_exports is None:
            return r[tuple[p.Infra.ImportLawPass | None, str]].fail(
                f"{namespace_dir} is a namespace without an owned package init",
            )
        if import_graph is None:
            return r[tuple[p.Infra.ImportLawPass | None, str]].fail(
                "import normalization requires its captured runtime graph",
            )
        project = inputs[2]
        if project is None:
            return r[tuple[p.Infra.ImportLawPass | None, str]].fail(
                "Import normalization requires its bound native source project",
            )
        candidate = cls._import_law_candidate_module(
            project, file_path, source, namespace
        )
        if candidate.failure:
            return r[tuple[p.Infra.ImportLawPass | None, str]].from_failure(candidate)
        current = candidate.value
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
                facade_dependencies=cls.import_facade_dependencies(
                    module,
                    root_exports,
                    import_graph,
                ),
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
            source_project=project,
            deferred_class_lines=cls._import_law_deferred_class_lines(
                tree, parents, module, member_resolver
            ),
        )
        return r[tuple[p.Infra.ImportLawPass | None, str]].ok(value=(state, current))

    @classmethod
    def _import_law_refreshed_tree(
        cls,
        state: p.Infra.ImportLawPass,
        current: str,
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> p.Infra.ImportLawPass:
        """Re-parse the evolved candidate so the next pass owns its live lines.

        The pass state's tree, parent map and bindings describe the source
        this normalization started from; every accepted rewrite invalidates
        the line numbers the next pass plans against. The loop therefore
        refreshes exactly the tree-derived fields between passes, keeping
        namespace-level facts (scope identity, root exports) as elected.

        Returns:
            The pass state bound to the refreshed module.

        """
        tree = ast.parse(current, filename=str(state.scope.file_path))
        parents = FlextInfraUtilitiesRopeAnalysis.ast_parent_map(tree)
        return state.model_copy(
            update={
                "tree": tree,
                "parents": parents,
                "bindings": cls._module_bindings(tree),
                "scope": state.scope.model_copy(
                    update={"own_exports": cls._import_law_declared_exports(tree)},
                ),
                "deferred_class_lines": cls._import_law_deferred_class_lines(
                    tree, parents, state.scope.module, member_resolver
                ),
            },
        )

    @staticmethod
    def _import_law_candidate_module(
        project: p.Infra.RopeProject,
        file_path: Path,
        source: str,
        namespace: str,
    ) -> p.Result[str]:
        """Authenticate the candidate against its native module and clean it.

        Returns:
            The candidate text with its own-package imports unaliased and its
            TYPE_CHECKING scaffold stripped, or the typed authentication
            failure.

        """
        resource = FlextInfraUtilitiesRopeRuntime.file_resource_at(project, file_path)
        native = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        if native.source_code != source:
            return r[str].fail(
                f"Import normalization source differs from its candidate: {file_path}",
            )
        unaliased = FlextInfraUtilitiesRopeModulePatch.unalias_own_package_imports(
            native, package=namespace
        )
        if unaliased.failure:
            return unaliased
        declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path),
            (),
            {file_path: unaliased.value},
            source_project=project,
        )
        with project.source_view(
            declared_files=declared, additional_source_folders=None
        ):
            return FlextInfraUtilitiesRopeModulePatch.strip_type_checking_scaffold(
                FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            )

    @classmethod
    def _import_law_deferred_class_lines(
        cls,
        tree: ast.Module,
        parents: Mapping[int, ast.AST],
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
            classification = (
                module,
                ".".join(qualified.attributes),
                node.lineno,
            )
            cls._annotation_classified.add(classification)
            if deferred:
                cls._annotation_deferred.add(classification)
                u.Cli.info(
                    f"annotation classification deferred module={module} "
                    f"class={'.'.join(qualified.attributes)} line={node.lineno}"
                )
                lines.add(node.lineno)
        return frozenset(lines)

    @classmethod
    def _import_law_runtime_diagnostics(
        cls, state: p.Infra.ImportLawPass
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
        state: p.Infra.ImportLawPass,
        source: str,
        *,
        sources: Mapping[Path, str] | None = None,
        rope_project: p.Infra.RopeProject | None = None,
        member_resolver: p.Infra.RopeSourceMemberResolver | None = None,
    ) -> p.Result[str]:
        """Apply the first rewrite category that changes the module.

        Every category's edits are computed against the text they mutate, so
        categories never share a pass; the caller re-parses between passes.

        Returns:
            The rewritten source, the unchanged source at the pass's fixed
            point, or the first typed classification failure of the attempted
            categories. An overlapping-edit ``ValueError`` raised by the
            first rewrite propagates unchanged.

        """
        repaired = cls._import_law_own_family_candidate(
            state, source, member_resolver=member_resolver
        )
        if repaired.failure or repaired.value != source:
            return repaired
        boundary = cls._import_law_validate_import_boundary(state)
        if boundary.failure:
            return r[str].from_failure(boundary)
        return cls._import_law_first_rewrite(
            state,
            source,
            sources=sources,
            rope_project=rope_project,
            member_resolver=member_resolver,
        )

    @classmethod
    def _import_law_first_rewrite(
        cls,
        state: p.Infra.ImportLawPass,
        source: str,
        *,
        sources: Mapping[Path, str] | None,
        rope_project: p.Infra.RopeProject | None,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> p.Result[str]:
        """Apply the first rewrite category that plans a change.

        Every category's edits are computed against the text they mutate, so
        categories never share a pass; the caller re-parses between passes.

        Returns:
            The rewritten source, the unchanged source at the pass's fixed
            point, or the first typed classification failure of the attempted
            categories.

        Raises:
            ValueError: If one category plans overlapping edits.

        """
        lines = source.splitlines()
        builders: tuple[
            Callable[[], p.Result[tuple[tuple[int, int, Sequence[str]], ...]]], ...
        ] = (
            lambda: r[tuple[tuple[int, int, Sequence[str]], ...]].ok(
                value=tuple(cls._import_law_relative_import_edits(state, lines)),
            ),
            lambda: r[tuple[tuple[int, int, Sequence[str]], ...]].ok(
                value=tuple(cls._import_law_guard_edits(state.tree, lines)),
            ),
            lambda: cls._import_law_placement_edits(state, lines).map(tuple),
            lambda: r[tuple[tuple[int, int, Sequence[str]], ...]].ok(
                value=tuple(cls._import_law_root_alias_binding_edits(state, lines)),
            ),
            lambda: r[tuple[tuple[int, int, Sequence[str]], ...]].ok(
                value=tuple(
                    cls._import_law_route_edits(
                        state,
                        lines,
                        sources=sources,
                        rope_project=rope_project,
                        member_resolver=member_resolver,
                    ),
                ),
            ),
            lambda: r[tuple[tuple[int, int, Sequence[str]], ...]].ok(
                value=tuple(cls._import_law_layer_order_edits(state, lines)),
            ),
        )
        for build in builders:
            edits = build()
            if edits.failure:
                return r[str].from_failure(edits)
            planned = edits.value
            if not planned:
                continue
            applied = cls._import_law_apply_edits(source, planned)
            if applied is None:
                msg = f"{state.scope.file_path}: overlapping import-law edits {planned}"
                raise ValueError(msg)
            if applied != source:
                transition = cls._import_law_validate_transition(
                    state, applied, planned
                )
                if transition.failure:
                    return r[str].from_failure(transition)
                return r[str].ok(value=applied)
        return r[str].ok(value=source)

    @staticmethod
    def _import_law_validate_transition(
        state: p.Infra.ImportLawPass,
        candidate: str,
        edits: Sequence[tuple[int, int, Sequence[str]]],
    ) -> p.Result[bool]:
        """Preserve the first syntax failure with its exact line-edit transition.

        Returns:
            Whether the candidate parses, or its typed syntax failure.

        """
        try:
            ast.parse(candidate, filename=str(state.scope.file_path))
        except SyntaxError as exc:
            line = exc.lineno or 1
            context = candidate.splitlines()[max(0, line - 4) : line + 1]
            return r[bool].fail(
                f"{state.scope.file_path}: rewrite produced an invalid candidate "
                f"at line {line}: {exc.msg}; edits={edits}; "
                f"candidate_lines={context}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _import_law_own_family_candidate(
        cls,
        state: p.Infra.ImportLawPass,
        source: str,
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver | None,
    ) -> p.Result[str]:
        """Elect only native identity-preserving own-family member replacements.

        Returns:
            A corrective candidate for the next validated pass, the unchanged
            source when nothing is elected, or the typed failure of an
            unroutable elected reference.

        """
        scope = state.scope
        if scope.family_letter is None:
            return r[str].ok(value=source)
        elected = cls._import_law_own_family_imports(state)
        if not elected:
            return r[str].ok(value=source)
        if member_resolver is None or state.source_project is None:
            return r[str].fail(
                "Own-family repair requires native source identity; use make mod",
            )
        routes: dict[t.StrTuple, tuple[str, str, str]] = {}
        upstream: dict[str, str] = {}
        for bound, (module, name) in elected.items():
            providers = cls._import_law_own_family_binding_providers(
                state,
                (bound, module, name),
                routes,
                member_resolver=member_resolver,
            )
            if providers.failure:
                return r[str].from_failure(providers)
            if providers.value and not cls._import_law_binds_from(
                state, bound, next(iter(providers.value))
            ):
                upstream[bound] = next(iter(providers.value))
        cls._import_law_own_family_annotations(state.tree, scope.file_path)
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            Path(state.source_project.root.real_path),
            planned_sources={scope.file_path: source},
            source_project=state.source_project,
        ) as (project, _sources):
            return r[str].ok(
                value=FlextInfraUtilitiesSemanticCutoverOwnMro.rewrite_own_family_members(
                    (project, scope.file_path, source),
                    routes,
                    {bound: route[0] for bound, route in elected.items()},
                    local_module=scope.module,
                    upstream=upstream,
                ),
            )

    @classmethod
    def _import_law_own_family_binding_providers(
        cls,
        state: p.Infra.ImportLawPass,
        binding: tuple[str, str, str],
        routes: MutableMapping[t.StrTuple, tuple[str, str, str]],
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver,
    ) -> p.Result[frozenset[str]]:
        """Route every consumed facade path of one elected own-family binding.

        Declaring routes are recorded in ``routes``; paths declared upstream
        contribute the upstream package that publishes the letter.

        Returns:
            The upstream providers of the binding (at most one), or the typed
            failure of an unroutable or ambiguous reference.

        """
        scope = state.scope
        bound, module, name = binding
        paths = cls._import_law_consumed_facade_paths(state, bound)
        if not paths:
            return r[frozenset[str]].fail(
                "Own-family facade-value reads have no declaring route: "
                f"path={scope.file_path} binding={bound} "
                f"provider={module}.{name} "
                f"published_by={state.root_exports.get(name)}",
            )
        providers: set[str] = set()
        for path in paths:
            qualified = f"{module}.{name}.{'.'.join(path)}"
            route = cls._import_law_own_family_route(
                state,
                qualified,
                path[-1],
                member_resolver=member_resolver,
            )
            if route is None:
                # Declared upstream: the route keeps the letter, bound to
                # the upstream package that publishes it (ADR-028 D10).
                providers.add(
                    cls._import_law_upstream_letter_provider(
                        state, member_resolver(qualified), name
                    )
                )
                continue
            if any(
                owner == route[1] and provider != route[0]
                for provider, owner, _ in routes.values()
            ):
                return r[frozenset[str]].fail(
                    "Own-family exports have competing declaring owners: "
                    f"path={scope.file_path} owner={route[1]}",
                )
            routes[bound, *path] = route
        if len(providers) > 1:
            return r[frozenset[str]].fail(
                "Own-family upstream routes need more than one provider: "
                f"path={scope.file_path} binding={bound} "
                f"providers={sorted(providers)}",
            )
        return r[frozenset[str]].ok(value=frozenset(providers))

    @classmethod
    def _import_law_own_family_imports(
        cls, state: p.Infra.ImportLawPass
    ) -> Mapping[str, tuple[str, str]]:
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
        imports: dict[str, tuple[str, str]] = {}
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
                if provider not in {
                    f"{scope.namespace}.{family.module}",
                    f"{scope.namespace}.{scope.family_letter}",
                }:
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
        state: p.Infra.ImportLawPass,
        qualified: str,
        member: str,
        *,
        member_resolver: p.Infra.RopeSourceMemberResolver,
    ) -> tuple[str, str, str] | None:
        """Prove a member and its declaring owner share native identities.

        A member declared in the module itself is spelled through its local
        class; one declared in another module of the own package through that
        module's family package; one declared upstream keeps the letter route.

        Returns:
            Import target (the module itself for a local owner), declaring
            owner and relative member path; ``None`` for an upstream member.

        Raises:
            ValueError: The native member or exported owner changes identity.

        """
        project = state.source_project
        if project is None:
            message = "Own-family repair requires a native project"
            raise ValueError(message)
        before = member_resolver(qualified)
        holder, owners = cls._import_law_own_family_owner(before)
        declaring = holder.get_name()
        namespace = state.scope.namespace
        if declaring != namespace and not declaring.startswith(f"{namespace}."):
            return None
        suffix = ".".join((*owners[1:], member))
        if declaring == state.scope.module:
            after = member_resolver(f"{declaring}.{owners[0]}.{suffix}")
            if not FlextInfraUtilitiesRopeRuntime.same_name(before, after):
                message = "Own-family local spelling changes native identity"
                raise ValueError(message)
            return declaring, owners[0], suffix
        module = declaring.rpartition(".")[0]
        cls._import_law_own_family_publication(state, project, module, owners[0])
        exported = member_resolver(
            m.Infra.SourceClassReference(target=module, attributes=(owners[0],))
        )
        declared = holder.get_scope().get_defined_names().get(owners[0])
        after = member_resolver(f"{module}.{owners[0]}.{suffix}")
        if (
            declared is None
            or not FlextInfraUtilitiesRopeRuntime.same_name(exported, declared)
            or not FlextInfraUtilitiesRopeRuntime.same_name(before, after)
        ):
            message = (
                "Own-family replacement changes native identity: "
                f"path={state.scope.file_path} original={qualified} "
                f"replacement={module}.{owners[0]}.{suffix} "
                f"declared_owner={declared is not None}"
            )
            raise ValueError(message)
        return module, owners[0], suffix

    @classmethod
    def _import_law_upstream_letter_provider(
        cls,
        state: p.Infra.ImportLawPass,
        binding: p.Infra.RopePyName,
        letter: str,
    ) -> str:
        """Elect the upstream package that publishes the letter for a member.

        The provider is the deepest enclosing package of the member's declaring
        module whose native publication binds the letter.

        Returns:
            The upstream package name.

        Raises:
            ValueError: No enclosing package publishes the letter.

        """
        project = state.source_project
        holder, _owners = cls._import_law_own_family_owner(binding)
        parts = holder.get_name().split(".")
        for size in range(len(parts) - 1, 0, -1):
            package = ".".join(parts[:size])
            if project is not None and cls.resolve_declared_binding(
                project,
                (package, letter),
                state.scope.project_root,
                state.sources or {},
            ):
                return package
        message = (
            f"No upstream package publishes letter {letter} for "
            f"{holder.get_name()}: {state.scope.file_path}"
        )
        raise ValueError(message)

    @classmethod
    def _import_law_binds_from(
        cls, state: p.Infra.ImportLawPass, bound: str, provider: str
    ) -> bool:
        """Return whether the module already binds a name from one provider.

        Returns:
            Whether an absolute ``from provider import`` binds ``bound``.

        """
        return any(
            isinstance(node, ast.ImportFrom)
            and not node.level
            and node.module == provider
            and any((alias.asname or alias.name) == bound for alias in node.names)
            for node in cls._import_law_iter_imports(state.tree)
        )

    @staticmethod
    def _import_law_own_family_owner(
        binding: p.Infra.RopePyName,
    ) -> tuple[p.Infra.RopeParsedModule, t.StrTuple]:
        """Read enclosing native class scopes at the exact declaration location.

        Returns:
            Declaring native module and nonempty outer-to-inner class path.

        Raises:
            ValueError: The declaration is unresolved or not in a class.

        """
        holder, line = binding.get_definition_location()
        if holder is None or line is None:
            message = "Own-family member declaration is unresolved"
            raise ValueError(message)
        scope = holder.get_scope().get_inner_scope_for_line(line)
        if scope.get_start() == line:
            scope = scope.parent
        owners: list[str] = []
        while scope is not None and scope.get_kind() == "Class":
            owners.append(scope.pyobject.get_name())
            scope = scope.parent
        if not owners:
            message = "Own-family member has no declaring class"
            raise ValueError(message)
        return holder, tuple(reversed(owners))

    @staticmethod
    def _import_law_own_family_publication(
        state: p.Infra.ImportLawPass,
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
            message = (
                "Own-family owner has no non-self lazy export; use make mod: "
                f"{state.scope.file_path} owner={owner} module={module}"
            )
            raise ValueError(message)

    @classmethod
    def _import_law_own_family_annotations(
        cls, tree: ast.Module, file_path: Path
    ) -> None:
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
                for part in cls._type_expression_nodes(annotation)
            ):
                message = (
                    "Own-family quoted annotations require make mod: "
                    f"{file_path}:{annotation.lineno}"
                )
                raise ValueError(message)

    @staticmethod
    def _type_expression_nodes(annotation: ast.expr) -> Sequence[ast.AST]:
        """Return the nodes of an annotation that are type expressions.

        Call arguments (``Field(description="...")``) and ``Literal[...]``
        members are values, never quoted forward references.

        Returns:
            The annotation's type-expression nodes.

        """
        nodes: list[ast.AST] = []
        pending: list[ast.AST] = [annotation]
        while pending:
            node = pending.pop()
            nodes.append(node)
            if isinstance(node, ast.Call):
                continue
            if isinstance(node, ast.Subscript) and (
                (isinstance(node.value, ast.Name) and node.value.id == "Literal")
                or (
                    isinstance(node.value, ast.Attribute)
                    and node.value.attr == "Literal"
                )
            ):
                continue
            pending.extend(ast.iter_child_nodes(node))
        return nodes

    @classmethod
    def _import_law_outside_boundary(
        cls,
        state: p.Infra.ImportLawPass,
        node: ast.Import | ast.ImportFrom,
        *,
        runtime_only: bool,
    ) -> bool:
        """Return whether one import is outside the dependency boundary check.

        A relative import is validated by the next pass after its absolute
        rewrite; a type-checking import never executes, so it is outside a
        runtime-only layer-zero boundary.

        Returns:
            Whether the boundary validator skips the import.

        """
        if isinstance(node, ast.ImportFrom) and node.level:
            return True
        return runtime_only and cls._import_law_inside_type_checking(
            node, state.parents
        )

    @classmethod
    def _import_law_validate_import_boundary(
        cls, state: p.Infra.ImportLawPass
    ) -> p.Result[bool]:
        """Reject forbidden dependencies before hoisting, deferral or routing.

        Returns:
            Whether the module passes the dependency boundary, or its first
            typed dependency failure.

        """
        scope = state.scope
        role = (
            "layer0"
            if scope.bootstrap_dependency
            else cls.import_module_role(scope.module, namespace=scope.namespace)
        )
        runtime_only = role == "layer0" and cls.import_law_runtime_only_layer_zero(
            scope.module, namespace=scope.namespace
        )
        for node in cls._import_law_iter_imports(state.tree):
            if cls._import_law_outside_boundary(state, node, runtime_only=runtime_only):
                continue
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
                    return r[bool].fail(
                        f"{scope.file_path}: layer-zero module imports its own "
                        f"namespace: {target}",
                    )
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
                }:
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
                return r[bool].fail(
                    f"{scope.file_path}: family imports its own facade: "
                    f"{target}.{alias.name}",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def import_law_runtime_only_layer_zero(module: str, *, namespace: str) -> bool:
        """Return whether a layer-zero module is constrained at runtime only.

        The lazy loader, bootstrap dependencies and pytest plugins are layer
        zero because they execute before the facades exist; a type-checking
        import never executes, so it cannot create that cycle. The config and
        settings roots keep ADR-005's law, which bans own facades even under
        ``TYPE_CHECKING``.

        Returns:
            Whether type-checking imports are outside the module's boundary.

        """
        parts = module.split(".")[len(namespace.split(".")) :]
        stem = parts[0].lstrip("_") if parts else ""
        return not any(
            stem == root or stem.startswith(f"{root}_")
            for root in c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        )

    @classmethod
    def import_law_layer_zero_helper(
        cls, state: p.Infra.ImportLawPass, target: str
    ) -> bool:
        """Prove an own helper against the complete native candidate dependency graph.

        Returns:
            Whether the helper has authenticated, acyclic foundation dependencies.

        Raises:
            ValueError: If the native candidate inventory is missing, cyclic,
                or a module is absent from the candidate.

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
            edges = cls._layer_zero_module_edges(state, module)
            if edges is None:
                return False
            graph[module] = edges
            pending.extend(edges - graph.keys())
        if cls.project_import_cycles(graph):
            message = f"layer-zero helper retains candidate dependency cycles: {target}"
            raise ValueError(message)
        return True

    @classmethod
    def _layer_zero_module_edges(
        cls, state: p.Infra.ImportLawPass, module: str
    ) -> frozenset[str] | None:
        """Resolve one module's authenticated foundation dependencies.

        Returns:
            The module's edges, or ``None`` when the module rejects the
            layer-zero contract.

        Raises:
            ValueError: If the module is absent or has a self dependency.

        """
        if module == state.scope.namespace or state.source_project is None:
            return None
        parsed = FlextInfraUtilitiesRopeRuntime.require_parsed_module(
            state.source_project.get_module(module)
        )
        resource = parsed.get_resource()
        if isinstance(resource, p.Infra.RopeRoot) and resource.has_child(
            c.Infra.INIT_PY
        ):
            # A package's source is its initializer, read through Rope's
            # public resource and module API.
            resource = resource.get_child(c.Infra.INIT_PY)
            parsed = FlextInfraUtilitiesRopeRuntime.require_parsed_module(
                state.source_project.get_pymodule(resource)
            )
        sources = state.sources
        if (
            resource is None
            or sources is None
            or Path(resource.real_path).resolve() not in sources
        ):
            message = f"layer-zero helper is absent from the candidate: {module}"
            raise ValueError(message)
        native_tree = state.tree if module == state.scope.module else parsed.get_ast()
        tree = native_tree
        family_base = (
            cls.import_module_role(module, namespace=state.scope.namespace) == "family"
        )
        if family_base and not cls.import_direct_module(
            state.scope.namespace_dir,
            Path(resource.real_path),
            namespace=state.scope.namespace,
        ):
            return None
        edges = cls._import_law_layer_zero_edges(state, module, tree)
        if edges is None or (family_base and edges):
            return None
        if module in edges:
            message = f"layer-zero helper has a self dependency: {module}"
            raise ValueError(message)
        return edges

    @classmethod
    def _import_law_layer_zero_edges(
        cls, state: p.Infra.ImportLawPass, module: str, tree: ast.Module
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
        runtime_only = cls.import_law_runtime_only_layer_zero(
            state.scope.module, namespace=state.scope.namespace
        )
        parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in cls._import_law_iter_imports(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue  # Compiler features do not load a schema dependency.
            if runtime_only and cls._import_law_inside_type_checking(node, parents):
                continue
            if isinstance(node, ast.ImportFrom) and node.level:
                provider = ".".join(module.split(".")[: -node.level])
                provider = f"{provider}.{node.module}" if node.module else provider
            else:
                provider = node.module or "" if isinstance(node, ast.ImportFrom) else ""
            for alias in node.names:
                dependency = (
                    provider if isinstance(node, ast.ImportFrom) else alias.name
                )
                if dependency != state.scope.namespace and not dependency.startswith(
                    f"{state.scope.namespace}."
                ):
                    # External providers (stdlib, foundation libraries, compiled
                    # extensions) carry no own candidate edge; Rope reports no
                    # module for their variables, so they are never resolved.
                    continue
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
                if native is None:
                    return None
                identity = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    native, source_project=state.source_project
                )
                if (
                    identity == state.scope.namespace
                    or identity.startswith(f"{state.scope.namespace}.")
                ) and cls.import_module_role(identity) == "family":
                    return None
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
