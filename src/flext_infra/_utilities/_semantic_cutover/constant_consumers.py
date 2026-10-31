"""Census-derived constant consumer cutover across declared workspace members.

Declaration owners are not constant consumers. Equal literal bytes do not prove
shared domain identity: enum vocabularies, builtin names and prose retain their
declaring contracts. Consumer rewrites exclude constant-definition sources and
must not introduce a reference to the facade being assembled. Explicit upstream
bindings and their genuine consumer defaults remain valid.
Literal rewrites replace complete native literal regions, never a prefix inside
another word or quoted payload; grammatical validity does not prove domain ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_cli import cli

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._rope.core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope.structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticConstantSources,
    FlextInfraUtilitiesSemanticContracts,
    FlextInfraUtilitiesSemanticCutoverEdits,
)


class FlextInfraUtilitiesSemanticConstantConsumers(
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticConstantSources,
):
    """Derive constant paths from declarations and rewrite proven bindings."""

    @classmethod
    def _plan_constant_consumers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.ResultView[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Compose constant effects under their original source authority.

        Returns:
            The complete edits against the original immutable source inventory.

        """
        working = dict(sources)
        originals = dict(cls._editable_sources(sources))
        changes: MutableMapping[Path, list[str]] = {}
        retired: set[Path] = set()
        source_project = rope_workspace.rope_project
        with (
            rope_workspace.open_workspace(
                rope_workspace.repository_root,
                rope_repository_root=rope_workspace.rope_repository_root,
                source_project=source_project,
            ) as workspace,
        ):
            for phase in (
                cls._constant_declarations,
                cls._retire_flat_constant_declarations,
                cls._plan_constant_imports,
            ):
                result = phase(workspace, working)
                if result.failure:
                    return result
                for edit in result.value:
                    originals.setdefault(edit.file_path, sources[edit.file_path])
                    working[edit.file_path] = edit.updated_source
                    changes.setdefault(edit.file_path, []).extend(edit.changes)
                    if edit.retire_file:
                        retired.add(edit.file_path)
        return r[tuple[m.Infra.SemanticMigrationEdit, ...]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    retire_file=path in retired,
                    changes=tuple(changes.get(path, ())),
                )
                for path, source in sorted(originals.items())
                if working[path] != source or path in retired
            )
        )

    @classmethod
    def _retire_flat_constant_declarations(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Retire flat facts only at equivalent explicit authored class owners.

        Returns:
            Authenticated declaration retirements for the shared candidate.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        project = runtime.snapshot_project(workspace.rope_project, sources)
        try:

            def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
                convention = workspace.convention(path)
                if convention.module_policy.expected_alias != "c":
                    return source, ()
                public = cls._constant_public_paths(project, convention.package_name)
                facade = public.get("c")
                if (
                    facade is None
                    or (owner_module := facade.get_object().get_module()) is None
                ):
                    return source, ()
                edits: list[m.Infra.SourceRewrite] = []
                for flat, destinations in cls._constant_destinations(
                    public, owner_module
                ).items():
                    binding = public.get(flat)
                    if binding is None:
                        continue
                    module, line = runtime.definition_location(binding)
                    if module is None or line is None:
                        continue
                    resource = module.get_module().get_resource()
                    if resource is None or resource.real_path != str(path):
                        continue
                    if len(destinations) != 1:
                        msg = (
                            f"constant has ambiguous explicit owners: "
                            f"{path}:{flat}: {destinations}"
                        )
                        raise ValueError(msg)
                    if not cls._equivalent_constant_declarations(
                        project, sources, binding, public[destinations[0]]
                    ):
                        continue
                    edits.extend(
                        m.Infra.SourceRewrite(
                            start=statement.start_offset,
                            end=statement.end_offset,
                            text="",
                        )
                        for statement in (
                            FlextInfraUtilitiesRopeStructure.logical_statements(source)
                        )
                        if cls._binding_statement_matches(
                            module,
                            statement,
                            binding,
                            line,
                        )
                    )
                resource = project.get_resource(
                    path.relative_to(Path(project.root.real_path)).as_posix()
                )
                return (
                    FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                        resource, source, edits
                    ).new_contents,
                    ("retired equivalent flat constants into explicit class owners",)
                    if edits
                    else (),
                )

            return cls._semantic_edits(cls._editable_sources(sources), rewrite)
        finally:
            project.close()

    @staticmethod
    def _equivalent_constant_declarations(
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        original: p.Infra.RopePyName,
        target: p.Infra.RopePyName,
    ) -> bool:
        """Compare complete native inert values and ClassVar type identities.

        Returns:
            Whether both declarations preserve the complete value and type.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        signatures: list[tuple[str, p.Infra.RopePyName]] = []
        for binding in (original, target):
            if (
                not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
                or len(binding.assignments) != 1
            ):
                return False
            assignment = binding.assignments[0]
            module, line = runtime.definition_location(binding)
            if (
                module is None
                or line is None
                or not isinstance(assignment.ast_node, ast.Constant)
                or not isinstance(assignment.type_hint, ast.Subscript)
            ):
                return False
            resource = module.get_resource()
            if resource is None or Path(resource.real_path) not in sources:
                return False
            scope = runtime.scope_at(
                module,
                runtime.source_offset(
                    sources[Path(resource.real_path)], assignment.ast_node
                ),
            )
            if not runtime.same_name(
                runtime.qualified_name(project, "ClassVar", module_name="typing"),
                runtime.annotation_origin(project, assignment.type_hint, scope),
            ):
                return False
            contract = runtime.annotation_origin(
                project, assignment.type_hint.slice, scope
            )
            if contract is None:
                return False
            signatures.append((ast.dump(assignment.ast_node), contract))
        return signatures[0][0] == signatures[1][0] and runtime.same_name(
            signatures[0][1], signatures[1][1]
        )

    @classmethod
    def _constant_declarations(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.ResultView[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Delegate constants declaration policy to the shared native contract loop.

        Returns:
            Declaration edits produced by the existing Rope ChangeSet owner.

        """
        contracts = FlextInfraUtilitiesSemanticContracts
        return contracts.plan_contract_rules(
            workspace,
            sources,
            tuple(
                rule
                for rule in contracts.declared_contract_rules(workspace.repository_root)
                if rule.phase == c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
            ),
        )

    @classmethod
    def _plan_constant_imports(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Resolve imported constants in one closed Rope graph.

        Returns:
            The complete identity-bound consumer edits.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        cli.display_text(f"census: resolve constants imports in {len(sources)} modules")
        project = runtime.snapshot_project(rope_workspace.rope_project, sources)
        paths: MutableMapping[str, Mapping[str, p.Infra.RopePyName]] = {}
        try:

            def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
                updated, changes = cls._rewrite_constant_consumer(
                    path, source, rope_workspace, project, paths
                )
                reused, literal_changes = cls._reuse_literal_constants(
                    path, updated, rope_workspace, project, paths
                )
                return reused, (*changes, *literal_changes)

            with FlextInfraUtilitiesRopeRuntimeRefactors.semantic_matching_context():
                return cls._semantic_edits(cls._editable_sources(sources), rewrite)
        finally:
            project.close()

    @classmethod
    def _reuse_literal_constants(
        cls,
        path: Path,
        source: str,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: MutableMapping[str, Mapping[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Admit scalar returns, singleton Literal fields and frozen predicates.

        Returns:
            Proposed source with only identity-proven literal consumer edits.

        """
        convention = workspace.convention(path)
        layout = convention.project_layout
        if cls._constant_definition_source(workspace, convention) or layout is None:
            return source, ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = runtime.build_string_module(project, source, resource=resource)
        returns_by_type = {
            literal_type: refactors.semantic_regions(
                module,
                "return ${literal}",
                arguments={"literal": f"type={literal_type}"},
            )
            for literal_type in ("__builtin__.str", "__builtin__.int")
        }
        enum_fields = any(
            refactors.semantic_regions(
                module, pattern, arguments={"literal": "name=typing.Literal"}
            )
            for pattern in (
                "${name}: ${literal}[${value}]",
                "${name}: ${literal}[${value}] = ${default}",
            )
        )
        frozen_arguments = {"frozen": "name=__builtin__.frozenset"}
        frozen_predicates = any(
            refactors.semantic_regions(module, pattern, arguments=frozen_arguments)
            for pattern in (
                "${subject} in ${frozen}(${value})",
                "${subject} not in ${frozen}(${value})",
            )
        )
        if not (any(returns_by_type.values()) or enum_fields or frozen_predicates):
            return source, ()
        package = cls._constant_facade_package(
            cls._constant_imports(project, module), layout.package_name, path
        )
        if project.find_module(f"{package}.constants") is None:
            return source, ()
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        public = paths[package]
        if not public:
            return source, ()
        contexts = (
            (
                "literal returns",
                cls._literal_return_matches(
                    project, module, public, returns_by_type, path
                )
                if any(returns_by_type.values())
                else None,
            ),
            (
                "singleton Literal fields",
                cls._enum_annotation_matches(project, module, public, source, path)
                if enum_fields
                else None,
            ),
            (
                "singleton frozenset predicates",
                cls._frozenset_membership_matches(
                    project, module, public, frozen_arguments, path
                )
                if frozen_predicates
                else None,
            ),
        )
        rewrites = tuple(
            m.Infra.SourceRewrite(start=start, end=end, text=reference)
            for _description, matches in contexts
            if matches is not None
            for (start, end), reference in matches.items()
        )
        if not rewrites:
            return source, ()
        module = runtime.build_string_module(
            project,
            refactors.content_change(resource, source, rewrites).new_contents,
            resource=resource,
        )
        imports = runtime.module_imports_for_pymodule(project, module)
        imports.add_import(runtime.from_import(package, 0, [("c", None)]))
        imports.remove_duplicates()
        return imports.get_changed_source(), tuple(
            f"{description} -> {package}.c: {len(matches)} references"
            for description, matches in contexts
            if matches
        )

    @classmethod
    def _literal_return_matches(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        public: Mapping[str, p.Infra.RopePyName],
        returns_by_type: Mapping[str, tuple[tuple[int, int], ...]],
        path: Path,
    ) -> Mapping[tuple[int, int], str]:
        """Match native scalar returns, refusing competing public owners.

        Returns:
            Native source regions mapped to unique constant publications.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"literal return has ambiguous public constant owners in {path}"
        matched: MutableMapping[tuple[int, int], str] = {}
        for literal_type, returns in returns_by_type.items():
            for literal, reference in cls._literal_constant_patterns(
                project, public, literal_type=literal_type
            ):
                if cls._constant_derives_from(project, public[reference], "enum.Enum"):
                    continue
                for start, end in refactors.semantic_regions(
                    module, f"return {literal}", arguments={}
                ):
                    if (start, end) not in returns:
                        continue
                    if (
                        runtime.scope_at(module, start).get_kind()
                        != c.Infra.RopeScopeKind.FUNCTION
                    ):
                        continue
                    cls._admit_literal_facade(project, module, public["c"], start, path)
                    for region in refactors.semantic_regions(
                        module, literal, arguments={}, start=start, end=end
                    ):
                        cls._record_matched_region(matched, region, reference, scope)
        return matched

    @staticmethod
    def _admit_literal_facade(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        facade: p.Infra.RopePyName,
        offset: int,
        path: Path,
    ) -> None:
        """Reject shadowing or a missing preceding unconditional facade import.

        Raises:
            ValueError: The source does not admit the requested facade binding.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        existing = runtime.scope_at(module, offset).lookup("c")
        if existing is not None and not runtime.same_name(facade, existing):
            message = f"literal constant facade c is shadowed in {path}"
            raise ValueError(message)
        if isinstance(
            existing, (p.Infra.RopeImportedName, p.Infra.RopeImportedModule)
        ) and not runtime.imported_binding_precedes(project, module, "c", offset):
            message = (
                f"literal constant facade c has no preceding "
                f"unconditional import in {path}"
            )
            raise ValueError(message)

    @staticmethod
    def _record_matched_region(
        matched: MutableMapping[tuple[int, int], str],
        region: tuple[int, int],
        reference: str,
        scope: str,
    ) -> None:
        """Record one matched region, refusing ambiguous public owners.

        Raises:
            ValueError: The same region has competing native owners.

        """
        previous = matched.get(region)
        if previous is not None and previous != reference:
            message = f"{scope}: {previous}, {reference}"
            raise ValueError(message)
        matched[region] = reference

    @classmethod
    def _frozenset_membership_matches(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        public: Mapping[str, p.Infra.RopePyName],
        arguments: Mapping[str, str],
        path: Path,
    ) -> Mapping[tuple[int, int], str]:
        """Match native frozen predicates, refusing competing public owners.

        Returns:
            Frozen-predicate regions mapped to unique constant publications.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"frozenset predicate has ambiguous public owners in {path}"
        matched: MutableMapping[tuple[int, int], str] = {}
        for literal_type in ("__builtin__.str", "__builtin__.int"):
            for expression, reference in cls._literal_constant_patterns(
                project, public, literal_type=literal_type, frozen=True
            ):
                if cls._constant_derives_from(project, public[reference], "enum.Enum"):
                    continue
                candidates = (
                    (start, end)
                    for pattern in (
                        f"${{subject}} in {expression}",
                        f"${{subject}} not in {expression}",
                    )
                    for start, end in refactors.semantic_regions(
                        module, pattern, arguments=arguments
                    )
                )
                for start, end in candidates:
                    cls._admit_literal_facade(project, module, public["c"], start, path)
                    constructors = refactors.semantic_regions(
                        module,
                        expression,
                        arguments=arguments,
                        start=start,
                        end=end,
                    )
                    if not constructors:
                        continue
                    region = max(constructors, key=operator.itemgetter(0))
                    cls._record_matched_region(matched, region, reference, scope)
        return matched

    @classmethod
    def _enum_annotation_matches(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        public: Mapping[str, p.Infra.RopePyName],
        source: str,
        path: Path,
    ) -> Mapping[tuple[int, int], str]:
        """Match StrEnum members to singleton Literal annotations by identity.

        Returns:
            Annotation regions mapped to their native enum members.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"literal annotation has ambiguous enum owners in {path}"
        matched: MutableMapping[tuple[int, int], str] = {}
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        for literal, reference in cls._literal_constant_patterns(project, public):
            if not cls._constant_derives_from(
                project, public[reference], "enum.StrEnum"
            ):
                continue
            annotation = f"${{name}}: ${{literal}}[{literal}]"
            for pattern in (annotation, f"{annotation} = ${{default}}"):
                for start, end in refactors.semantic_regions(
                    module,
                    pattern,
                    arguments={"literal": "name=typing.Literal"},
                ):
                    if not any(
                        statement.start_offset <= start < statement.end_offset
                        and FlextInfraUtilitiesRopeStructure.target_name(statement)
                        for statement in statements
                    ):
                        continue
                    cls._admit_literal_facade(project, module, public["c"], start, path)
                    annotations = refactors.semantic_regions(
                        module,
                        f"${{literal}}[{literal}]",
                        arguments={"literal": "name=typing.Literal"},
                        start=start,
                        end=end,
                    )
                    if annotations:
                        begin, finish = min(annotations, key=operator.itemgetter(0))
                        for region in refactors.semantic_regions(
                            module, literal, arguments={}, start=begin, end=finish
                        ):
                            cls._record_matched_region(
                                matched, region, reference, scope
                            )
        return matched

    @classmethod
    def _rewrite_constant_consumer(
        cls,
        path: Path,
        source: str,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: MutableMapping[str, Mapping[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Rebind one consumer using its complete native import plan.

        Returns:
            Proposed source and descriptions of its native reference edits.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        convention = rope_workspace.convention(path)
        if cls._constant_definition_source(rope_workspace, convention):
            return source, ()
        layout = convention.project_layout
        if layout is None:
            return source, ()
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(resource, path),
        )
        statements = cls._constant_imports(project, module)
        if not cls._has_constant_imports(rope_workspace, project, module, statements):
            return source, ()
        package = cls._constant_facade_package(statements, layout.package_name, path)
        facade_module = Path(c.Infra.CONSTANTS_PY).stem
        if project.find_module(f"{layout.package_name}.{facade_module}") is not None:
            package = layout.package_name
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        plan = cls._constant_import_plan(
            project, module, statements, paths[package], path
        )
        if plan[0]:
            source = cls._apply_constant_imports(
                project, resource, source, package, plan
            )
            module = runtime.build_string_module(project, source, resource=resource)
        qualified = cls._constant_qualified_edits(module, paths[package], path)
        if qualified:
            source = refactors.content_change(resource, source, qualified).new_contents
        count = len(plan[0]) + len(qualified)
        changes = (
            (f"constant consumers -> {package}.c: {count} references",) if count else ()
        )
        return source, changes

    @classmethod
    def _apply_constant_imports(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        package: str,
        plan: tuple[tuple[m.Infra.SourceRewrite, ...], Mapping[int, set[str]]],
    ) -> str:
        """Apply correlated reference/removal edits through native import owners.

        Returns:
            Proposed source with one canonical facade import binding.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        changed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, plan[0]
        )
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        cleaned = cls._remove_constant_imports(project, proposed, plan[1])
        proposed = runtime.build_string_module(project, cleaned, resource=resource)
        organized = runtime.module_imports_for_pymodule(project, proposed)
        organized.add_import(runtime.from_import(package, 0, [("c", None)]))
        organized.remove_duplicates()
        return organized.get_changed_source()

    @staticmethod
    def _constant_qualified_edits(
        module: p.Infra.RopePyModule,
        public: Mapping[str, p.Infra.RopePyName],
        path: Path,
    ) -> tuple[m.Infra.SourceRewrite, ...]:
        """Qualify missing flat members beneath their proven published namespace.

        A missing terminal has no identity to compare. Only its resolved namespace
        prefix and a unique member published by that namespace's owners admit it.

        Returns:
            Native expression edits retaining aliases and unrelated lexical names.

        Raises:
            ValueError: A referenced flat member has competing public destinations.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        facade = public.get("c")
        if facade is None:
            return ()
        owner_module = facade.get_object().get_module()
        if owner_module is None:
            return ()
        destinations = (
            FlextInfraUtilitiesSemanticConstantConsumers._constant_destinations(
                public, owner_module
            )
        )
        edits: list[m.Infra.SourceRewrite] = []
        qualified_facade = f"{owner_module.get_name()}.c"
        for flat, references in destinations.items():
            if flat in public:
                continue
            _root, namespace, member = flat.split(".")
            regions = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
                module,
                f"${{facade}}.{namespace}.{member}",
                arguments={"facade": f"name={qualified_facade}"},
            )
            if not regions:
                continue
            if len(references) != 1:
                message = (
                    f"constant has ambiguous public owners in {path}: "
                    f"{tuple(references)}"
                )
                raise ValueError(message)
            reference = references[0]
            if not runtime.same_name(
                public[reference],
                public[reference.rpartition(".")[0]]
                .get_object()
                .get_attributes()
                .get(member),
            ):
                message = f"constant destination lost its publication: {reference}"
                raise ValueError(message)
            for start, end in regions:
                prefix = module.source_code[start:end].rpartition(".")[0]
                edits.append(
                    m.Infra.SourceRewrite(
                        start=start,
                        end=end,
                        text=f"{prefix}.{reference.split('.')[2]}.{member}",
                    )
                )
        return tuple(edits)

    @staticmethod
    def _constant_destinations(
        public: Mapping[str, p.Infra.RopePyName],
        owner_module: p.Infra.RopeSemanticModule,
    ) -> MutableMapping[str, list[str]]:
        """Elect component destinations beneath natively published namespaces.

        Returns:
            Candidate class-owned references for each namespace member.

        """
        namespaces = {
            reference
            for reference, binding in public.items()
            if reference.count(".") == 1
            and FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(binding.get_object())
            and binding.get_object().get_module() is owner_module
        }
        destinations: MutableMapping[str, list[str]] = {}
        for reference in public:
            match reference.split("."):
                case [facade, namespace, _, member]:
                    prefix = f"{facade}.{namespace}"
                    flat = f"{prefix}.{member}"
                    if prefix in namespaces:
                        destinations.setdefault(flat, []).append(reference)
                case _:
                    pass
        return destinations

    @classmethod
    def _has_constant_imports(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        statements: Sequence[tuple[p.Infra.RopeFromImport, m.Infra.LogicalStatement]],
    ) -> bool:
        """Elect imported constants through their native declaration's role.

        Returns:
            Whether a resolved import declares the constants family.

        """
        bindings = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, 0).get_names()
        for info, _statement in statements:
            for name, alias in info.names_and_aliases:
                binding = bindings.get(alias or name)
                if binding is None:
                    continue
                terminal = cls._constant_terminal(
                    project, binding, f"{info.module_name}.{name}"
                )
                declaration, _line = terminal.get_definition_location()
                if declaration is None:
                    continue
                resource = declaration.get_module().get_resource()
                if resource is not None and cls._constant_definition_source(
                    workspace, workspace.convention(Path(resource.real_path))
                ):
                    return True
        return False

    @staticmethod
    def _constant_definition_source(
        workspace: p.Infra.RopeWorkspaceDsl,
        convention: m.Infra.RopeModuleConvention,
    ) -> bool:
        """Exclude constants and configured layer-zero owners from consumer edits.

        Returns:
            Whether this module owns declarations rather than consuming them.

        """
        path = convention.file_path
        policy = convention.module_policy
        layout = convention.project_layout
        runtime_owner = (
            layout is not None
            and path.parent == layout.package_dir
            and path.stem
            in FlextInfraUtilitiesCodegenNamespace.runtime_module_names(
                project_name=layout.project_name,
                codegen=FlextInfraUtilitiesProjectManagedArtifacts
                .load_codegen_inputs(
                    layout.project_root, source_project=workspace.rope_project
                )
                .unwrap()
                .spec,
            ).values()
        )
        return (
            policy.expected_alias == "c"
            or policy.expected_family == "Constants"
            or runtime_owner
            or any(
                FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                    parent.name
                )
                == "c"
                for parent in path.parents
                if parent.is_relative_to(workspace.repository_root)
            )
        )

    @staticmethod
    def _constant_imports(
        project: p.Infra.RopeProject, module: p.Infra.RopePyModule
    ) -> tuple[tuple[p.Infra.RopeFromImport, m.Infra.LogicalStatement], ...]:
        """Elect declared constants imports before resolving native suppliers.

        Returns:
            Native from-import declarations participating in constant ownership.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        found: list[tuple[p.Infra.RopeFromImport, m.Infra.LogicalStatement]] = []
        for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
            module.source_code
        ):
            if (
                statement.category != c.Infra.StatementCategory.FROM_IMPORT
                or statement.enclosing_kind != c.Infra.RopeScopeKind.MODULE
            ):
                continue
            parsed = runtime.build_string_module(
                project, statement.text.lstrip(), resource=module.get_resource()
            )
            for imported in runtime.module_imports_for_pymodule(
                project, parsed
            ).imports:
                info = imported.import_info
                if not isinstance(info, p.Infra.RopeFromImport):
                    continue
                if info.level:
                    continue
                parts = info.module_name.split(".")
                constants_module = (
                    FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
                        f"{parts[-1]}.py"
                    )
                    == "c"
                    or any(
                        FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                            part
                        )
                        == "c"
                        for part in parts
                    )
                )
                names = [
                    (name, alias)
                    for name, alias in info.names_and_aliases
                    if constants_module or name == "c"
                ]
                if not names:
                    continue
                found.append((
                    runtime.from_import(info.module_name, 0, names),
                    statement,
                ))
        return tuple(found)

    @classmethod
    def _constant_import_plan(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        statements: Sequence[tuple[p.Infra.RopeFromImport, m.Infra.LogicalStatement]],
        paths: Mapping[str, p.Infra.RopePyName],
        path: Path,
    ) -> tuple[tuple[m.Infra.SourceRewrite, ...], Mapping[int, set[str]]]:
        """Plan every native reference before removing its import binding.

        Returns:
            Source edits and the imported bindings they retire.

        """
        bindings = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, 0).get_names()
        rewrites: list[m.Infra.SourceRewrite] = []
        removals: MutableMapping[int, set[str]] = {}
        for info, statement in statements:
            for imported, alias in info.names_and_aliases:
                name = alias or imported
                binding = bindings.get(name)
                if binding is None:
                    continue
                binding = cls._constant_terminal(
                    project, binding, f"{info.module_name}.{imported}"
                )
                if imported == "c" and FlextInfraUtilitiesRopeRuntimeModules.same_name(
                    paths["c"], binding
                ):
                    continue
                reference = cls._constant_reference(paths, binding, path)
                if reference is None:
                    continue
                changes = cls._constant_binding_edits(
                    project, module, (name, binding), reference, paths["c"]
                )
                if not changes:
                    continue
                rewrites.extend(changes)
                removals.setdefault(statement.line, set()).add(name)
        return tuple(rewrites), removals

    @classmethod
    def _constant_binding_edits(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        imported: tuple[str, p.Infra.RopePyName],
        reference: str,
        facade: p.Infra.RopePyName,
    ) -> tuple[m.Infra.SourceRewrite, ...]:
        """Rewrite native imported occurrences without crossing local rebindings.

        Returns:
            Proven occurrence edits, or no admissible binding retirement.

        Raises:
            ValueError: The resource or canonical facade binding is unavailable.

        """
        name, binding = imported
        if cls._constant_composition_base(module, binding):
            return ()
        resource = module.get_resource()
        if resource is None:
            message = "constant consumer module has no source resource"
            raise ValueError(message)
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project, name, binding, imports=False, in_hierarchy=False
        )
        occurrences = tuple(finder.find_occurrences(resource=resource))
        if any(item.is_defined() for item in occurrences):
            return ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        rewrites: list[m.Infra.SourceRewrite] = []
        for occurrence in occurrences:
            scope = runtime.scope_at(module, occurrence.offset)
            existing = scope.lookup("c")
            if existing is not None and not cls._constant_owner_binding(
                facade, existing
            ):
                message = f"constant facade c is shadowed in {resource.real_path}"
                raise ValueError(message)
            start, end = occurrence.get_word_range()
            rewrites.append(m.Infra.SourceRewrite(start=start, end=end, text=reference))
        return tuple(rewrites)

    @classmethod
    def _remove_constant_imports(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        removals: Mapping[int, set[str]],
    ) -> str:
        """Remove proven imports and empty suites, preserving unrelated comments.

        Returns:
            Source preserving unrelated import bindings and comments.

        Raises:
            ValueError: The consumer has no native source resource.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = module.get_resource()
        if resource is None:
            message = "constant imports have no source resource"
            raise ValueError(message)
        edits: list[m.Infra.SourceRewrite] = []
        emptied: set[int] = set()
        for _native_info, statement in cls._constant_imports(project, module):
            removed = removals.get(statement.line)
            if not removed:
                continue
            parsed = runtime.build_string_module(
                project, statement.text.lstrip(), resource=resource
            )
            imports = runtime.module_imports_for_pymodule(project, parsed)
            for imported in imports.imports:
                info = imported.import_info
                if isinstance(info, p.Infra.RopeFromImport):
                    imported.import_info = runtime.from_import(
                        info.module_name,
                        info.level,
                        [
                            (name, alias)
                            for name, alias in info.names_and_aliases
                            if (alias or name) not in removed
                        ],
                    )
            changed = imports.get_changed_source().rstrip()
            if not changed:
                emptied.add(statement.line)
            indent = statement.text[: statement.indent]
            edits.append(
                m.Infra.SourceRewrite(
                    start=statement.start_offset,
                    end=statement.end_offset,
                    text=indent + changed if changed else "",
                )
            )
        edits = cls._empty_type_checking_suites(module.source_code, edits, emptied)
        changed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, module.source_code, edits
        ).new_contents
        return cls._unused_type_checking_import(project, resource, changed)

    @staticmethod
    def _empty_type_checking_suites(
        source: str,
        edits: Sequence[m.Infra.SourceRewrite],
        emptied: frozenset[int] | set[int],
    ) -> list[m.Infra.SourceRewrite]:
        """Remove empty TYPE_CHECKING suites without stubs or comment loss.

        Returns:
            Source edits retaining the empty suites' documentation comments.

        """
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        result = list(edits)
        for index, guard in enumerate(statements):
            if guard.category != c.Infra.StatementCategory.IF_GUARD:
                continue
            body: list[m.Infra.LogicalStatement] = []
            for statement in statements[index + 1 :]:
                if statement.indent <= guard.indent:
                    break
                body.append(statement)
            if not body or not all(
                item.type_checking_guarded and item.line in emptied for item in body
            ):
                continue
            end = body[-1].end_offset
            result = [
                edit for edit in result if not guard.start_offset <= edit.start < end
            ]
            comment = guard.text.partition("#")[2]
            result.append(
                m.Infra.SourceRewrite(
                    start=guard.start_offset,
                    end=end,
                    text="#" + comment if comment else "",
                )
            )
        return result

    @staticmethod
    def _unused_type_checking_import(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
    ) -> str:
        """Remove annotation-guard imports natively after their last reference.

        Returns:
            Proposed source without unused TYPE_CHECKING imports.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = runtime.build_string_module(project, source, resource=resource)
        imports = runtime.module_imports_for_pymodule(project, module)
        for statement in imports.imports:
            info = statement.import_info
            if (
                not isinstance(info, p.Infra.RopeFromImport)
                or info.module_name != "typing"
            ):
                continue
            kept: list[tuple[str, str | None]] = []
            for name, alias in info.names_and_aliases:
                if name != "TYPE_CHECKING":
                    kept.append((name, alias))
                    continue
                if FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
                    module,
                    "${guard}",
                    arguments={"guard": "name=typing.TYPE_CHECKING"},
                ):
                    kept.append((name, alias))
            statement.import_info = runtime.from_import(
                info.module_name, info.level, kept
            )
        return imports.get_changed_source()

    @staticmethod
    def _constant_composition_base(
        module: p.Infra.RopePyModule,
        binding: p.Infra.RopePyName,
    ) -> bool:
        """Keep native provider imports used in class composition headers.

        Returns:
            Whether the reference belongs to a class's composition header.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for scope in runtime.scope_at(module, 0).get_scopes():
            if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
                continue
            if (
                binding.get_object()
                in FlextInfraUtilitiesRopeRuntimeTypes.require_class_object(
                    scope.pyobject, "constant facade composition"
                ).get_superclasses()
            ):
                return True
        return False

    @staticmethod
    def _constant_facade_package(
        statements: Sequence[tuple[p.Infra.RopeFromImport, m.Infra.LogicalStatement]],
        declared_package: str,
        path: Path,
    ) -> str:
        """Elect one declared facade package, rejecting competing c bindings.

        Returns:
            The package owning the consumer's canonical constants facade.

        Raises:
            ValueError: Several constants facades are bound as c.

        """
        public_packages = {
            info.module_name
            for info, _source in statements
            if any(
                name == "c" and alias is None for name, alias in info.names_and_aliases
            )
        }
        if len(public_packages) > 1:
            msg = f"multiple constants facades bound as c in {path}"
            raise ValueError(msg)
        return next(iter(public_packages), declared_package)


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantConsumers"]
