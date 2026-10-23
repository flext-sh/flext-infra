"""Census-derived constant consumer cutover across declared workspace members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from pathlib import Path

from flext_cli import cli

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.contracts import (
    FlextInfraUtilitiesSemanticContracts,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesSemanticConstantConsumers(
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Derive constant paths from declarations and rewrite proven bindings."""

    @classmethod
    def _plan_constant_consumers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Compose constant declaration repairs with their consumer cutover.

        Returns:
            The complete edits against the original immutable source inventory.

        """
        declarations = cls._constant_declarations(rope_workspace, sources)
        if declarations.failure:
            return declarations
        working = dict(sources)
        working.update({
            edit.file_path: edit.updated_source for edit in declarations.value
        })
        consumers = cls._plan_constant_imports(rope_workspace, working)
        if consumers.failure:
            return consumers
        working.update({
            edit.file_path: edit.updated_source for edit in consumers.value
        })
        changes = {
            edit.file_path: edit.changes
            for edit in (*declarations.value, *consumers.value)
        }
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=tuple(changes[path]),
                )
                for path, source in sources.items()
                if source != working[path]
            )
        )

    @classmethod
    def _constant_declarations(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
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
                for rule in contracts.declared_contract_rules(
                    Path(workspace.rope_project.root.real_path)
                )
                if rule.phase == c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
            ),
        )

    @classmethod
    def _plan_constant_imports(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve imported constants in one closed Rope graph.

        Returns:
            The complete identity-bound consumer edits.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        cli.display_text(f"census: resolve constants imports in {len(sources)} modules")
        project = runtime.snapshot_project(rope_workspace.rope_project, sources)
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]] = {}
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
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Plan contextual constant reuse against one immutable consumer module.

        Returns:
            Source with one shared import/publication result for admitted scalar
            returns, singleton Literal annotations and frozenset predicates.

        """
        convention = workspace.convention(path)
        layout = convention.project_layout
        if (
            cls._constant_definition_source(workspace, convention)
            or path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
            or convention.module_policy.expected_alias in {"config", "settings"}
            or layout is None
        ):
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
        public: t.MappingKV[str, p.Infra.RopePyName],
        returns_by_type: t.MappingKV[str, t.VariadicTuple[t.Pair[int, int]]],
        path: Path,
    ) -> t.MappingKV[t.Pair[int, int], str]:
        """Match admitted public constants onto native return regions.

        Returns:
            The return regions and their admitted public references. Regions
            with competing public owners fail through the admission guard
            with ``ValueError``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"literal return has ambiguous public constant owners in {path}"
        matched: t.MutableMappingKV[t.Pair[int, int], str] = {}
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

    @classmethod
    def _constant_derives_from(
        cls,
        project: p.Infra.RopeProject,
        candidate: p.Infra.RopePyName,
        qualified: str,
    ) -> bool:
        """Resolve a member's declaring ancestry through native class identity.

        Returns:
            Whether the member's owner declares the qualified enum ancestry.

        Raises:
            TypeError: The constant declaration has no native source module.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = cls._constant_terminal(project, candidate, "enum member")
        module, line = binding.get_definition_location()
        if module is None or line is None:
            return False
        module = module.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = "Constant declarations require a native source module"
            raise TypeError(message)
        enum = runtime.qualified_name(project, qualified).get_object()
        for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
            module.source_code
        ):
            if statement.line == line:
                owner = runtime.scope_at(module, statement.start_offset).pyobject
                return enum in FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                    owner
                )
        return False

    @staticmethod
    def _admit_literal_facade(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        facade: p.Infra.RopePyName,
        offset: int,
        path: Path,
    ) -> None:
        """Reject a competing or conditionally imported constants binding.

        Raises:
            ValueError: If the facade is shadowed or lacks a preceding
                unconditional import at the occurrence offset.

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
        matched: t.MutableMappingKV[t.Pair[int, int], str],
        region: t.Pair[int, int],
        reference: str,
        scope: str,
    ) -> None:
        """Record one matched region, refusing ambiguous public owners.

        Raises:
            ValueError: If the region already maps to a different reference.

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
        public: t.MappingKV[str, p.Infra.RopePyName],
        arguments: t.StrMapping,
        path: Path,
    ) -> t.MappingKV[t.Pair[int, int], str]:
        """Match identity-proven frozenset literals in membership predicates.

        Returns:
            The predicate regions and their admitted public references.
            Regions with competing public owners fail through the admission
            guard with ``ValueError``.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"frozenset predicate has ambiguous public owners in {path}"
        matched: t.MutableMappingKV[t.Pair[int, int], str] = {}
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
        public: t.MappingKV[str, p.Infra.RopePyName],
        source: str,
        path: Path,
    ) -> t.MappingKV[t.Pair[int, int], str]:
        """Match declared StrEnum members onto singleton Literal annotations.

        Returns:
            The annotation literal regions and their admitted enum references.
            Regions with competing enum owners fail through the admission
            guard with ``ValueError``.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        scope = f"literal annotation has ambiguous enum owners in {path}"
        matched: t.MutableMappingKV[t.Pair[int, int], str] = {}
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
                    for region in cls._enum_annotation_regions(
                        module, literal, annotations
                    ):
                        cls._record_matched_region(matched, region, reference, scope)
        return matched

    @staticmethod
    def _enum_annotation_regions(
        module: p.Infra.RopePyModule,
        literal: str,
        annotations: t.VariadicTuple[t.Pair[int, int]],
    ) -> t.VariadicTuple[t.Pair[int, int]]:
        """Read the literal regions inside one matched annotation.

        Returns:
            The literal source regions recorded for the annotation's enum
            owner, or an empty tuple when the annotation region is absent.

        """
        if not annotations:
            return ()
        begin, finish = min(annotations, key=operator.itemgetter(0))
        return FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
            module, literal, arguments={}, start=begin, end=finish
        )

    @classmethod
    def _constant_declaration_bindings(
        cls,
        project: p.Infra.RopeProject,
        public: t.MappingKV[str, p.Infra.RopePyName],
    ) -> t.MappingKV[
        Path,
        t.Pair[p.Infra.RopePyModule, list[t.Pair[p.Infra.RopePyName, int]]],
    ]:
        """Group uniquely assigned public constants by their defining module.

        Returns:
            Each defining module with its uniquely assigned constant bindings
            and definition lines.

        Raises:
            TypeError: A constant binding has no native source module.

        """
        declarations: t.MutableMappingKV[
            Path,
            t.Pair[
                p.Infra.RopePyModule,
                list[t.Pair[p.Infra.RopePyName, int]],
            ],
        ] = {}
        for reference, candidate in public.items():
            binding = cls._constant_terminal(project, candidate, reference)
            if (
                not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
                or len(binding.assignments) != 1
            ):
                continue
            module, line = binding.get_definition_location()
            if module is None or line is None:
                continue
            module = module.get_module()
            if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
                message = "Constant bindings require a native source module"
                raise TypeError(message)
            resource = module.get_resource()
            if resource is None:
                continue
            declarations.setdefault(Path(resource.real_path), (module, []))[1].append((
                binding,
                line,
            ))
        return declarations

    @classmethod
    def _binding_statement_matches(
        cls,
        module: p.Infra.RopePyModule,
        statement: m.Infra.LogicalStatement,
        binding: p.Infra.RopePyName,
        line: int,
    ) -> bool:
        """Report whether one class-level assignment declares the binding.

        Returns:
            Whether the statement's target resolves to the chased binding at
            its definition line.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        structure = FlextInfraUtilitiesRopeStructure
        if (
            statement.line != line
            or statement.enclosing_kind != c.Infra.RopeScopeKind.CLASS
            or statement.category
            not in {
                c.Infra.StatementCategory.ASSIGN,
                c.Infra.StatementCategory.ANN_ASSIGN,
            }
        ):
            return False
        target = structure.target_name(statement)
        return bool(target) and runtime.same_name(
            binding,
            runtime.expression_name(
                runtime.scope_at(module, statement.start_offset), target
            ),
        )

    @classmethod
    def _literal_constant_patterns(
        cls,
        project: p.Infra.RopeProject,
        public: t.MappingKV[str, p.Infra.RopePyName],
        *,
        literal_type: str = "__builtin__.str",
        frozen: bool = False,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Read proven literals at uniquely assigned public c bindings.

        Strings require exact native literal boundaries. Integer declarations
        admit decimal tokens only. Frozen candidates additionally require the
        native builtin constructor around one such literal in a singleton set.

        Returns:
            Raw source patterns and their identity-proven public references.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        structure = FlextInfraUtilitiesRopeStructure
        found: list[t.Pair[str, str]] = []
        arguments = dict[str, str]()
        if frozen:
            arguments["frozen"] = "name=__builtin__.frozenset"
        declarations = cls._constant_declaration_bindings(project, public)
        for path, (module, bindings) in declarations.items():
            source = module.source_code
            literal_regions = {
                (start, end)
                for start, end, metadata in refactors.ignored_regions(source)
                for prefix in (metadata.get("prefix"),)
                if prefix is None or "f" not in prefix.casefold()
            }
            statements = structure.logical_statements(source)
            for binding, line in bindings:
                for statement in statements:
                    if not cls._binding_statement_matches(
                        module, statement, binding, line
                    ):
                        continue
                    for start, end in refactors.semantic_regions(
                        module,
                        "${literal}",
                        arguments={"literal": f"type={literal_type}"},
                        start=statement.start_offset,
                        end=statement.end_offset,
                    ):
                        literal = source[start:end]
                        if (
                            literal_type == "__builtin__.str"
                            and (start, end) not in literal_regions
                        ) or (
                            literal_type == "__builtin__.int"
                            and not literal.isdecimal()
                        ):
                            continue
                        expression = (
                            f"${{frozen}}({{{literal}}})" if frozen else literal
                        )
                        pattern = (
                            f"${{target}}: ${{annotation}} = {expression}"
                            if statement.category
                            == c.Infra.StatementCategory.ANN_ASSIGN
                            else f"${{target}} = {expression}"
                        )
                        if not refactors.semantic_regions(
                            module,
                            pattern,
                            arguments=arguments,
                            start=statement.start_offset,
                            end=statement.end_offset,
                        ):
                            continue
                        canonical = cls._constant_reference(public, binding, path)
                        if canonical is not None:
                            found.append((expression, canonical))
        return tuple(found)

    @classmethod
    def _rewrite_constant_consumer(
        cls,
        path: Path,
        source: str,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Rebind one consumer using its complete Rope import plan.

        Returns:
            Proposed source and descriptions of its identity-proven edits.

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
        rewrites, removals = cls._constant_import_plan(
            project, module, statements, paths[package], path
        )
        if rewrites:
            changed = refactors.content_change(resource, source, rewrites)
            proposed = runtime.build_string_module(
                project, changed.new_contents, resource=resource
            )
            cleaned = cls._remove_constant_imports(project, proposed, removals)
            proposed = runtime.build_string_module(project, cleaned, resource=resource)
            organized = runtime.module_imports_for_pymodule(project, proposed)
            organized.add_import(runtime.from_import(package, 0, [("c", None)]))
            organized.remove_duplicates()
            source = organized.get_changed_source()
            module = runtime.build_string_module(project, source, resource=resource)
        qualified = cls._constant_qualified_edits(module, paths[package], path)
        if qualified:
            source = refactors.content_change(resource, source, qualified).new_contents
        count = len(rewrites) + len(qualified)
        changes = (
            (f"constant consumers -> {package}.c: {count} references",)
            if count
            else ()
        )
        return source, changes

    @staticmethod
    def _constant_qualified_edits(
        module: p.Infra.RopePyModule,
        public: t.MappingKV[str, p.Infra.RopePyName],
        path: Path,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
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
        namespaces = {
            reference
            for reference, binding in public.items()
            if reference.count(".") == 1
            and FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(
                binding.get_object()
            )
            and binding.get_object().get_module() is owner_module
        }
        destinations: t.MutableMappingKV[str, list[str]] = {}
        for reference in public:
            parts = reference.split(".")
            if len(parts) != 4:
                continue
            namespace = ".".join(parts[:2])
            if namespace not in namespaces:
                continue
            flat = f"{namespace}.{parts[-1]}"
            if flat not in public:
                destinations.setdefault(flat, []).append(reference)
        edits: list[m.Infra.SourceRewrite] = []
        qualified_facade = f"{owner_module.get_name()}.c"
        for flat, references in destinations.items():
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
            published_owner = public[reference.rpartition(".")[0]]
            published = published_owner.get_object().get_attributes().get(member)
            if not runtime.same_name(public[reference], published):
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

    @classmethod
    def _has_constant_imports(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        statements: t.SequenceOf[
            t.Pair[p.Infra.RopeFromImport, m.Infra.LogicalStatement]
        ],
    ) -> bool:
        """Elect imports by their native declaration's constants role.

        Returns:
            Whether a resolved import belongs to the constants family.

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
        """Keep constants composition and layer-zero bootstrap imports at their owner.

        Returns:
            Whether the module declares or bootstraps the constants family.

        """
        path = convention.file_path
        policy = convention.module_policy
        return (
            policy.expected_alias == "c"
            or policy.expected_family == "Constants"
            or (
                path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
                and (path.parent / c.Infra.CONSTANTS_PY).is_file()
            )
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
    ) -> t.VariadicTuple[t.Pair[p.Infra.RopeFromImport, m.Infra.LogicalStatement]]:
        """Elect declared constants imports before resolving their native sources.

        Returns:
            From-imports participating in constants ownership resolution.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        found: list[t.Pair[p.Infra.RopeFromImport, m.Infra.LogicalStatement]] = []
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
                    ) == "c"
                    or any(
                        FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                            part
                        ) == "c"
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
        statements: t.SequenceOf[
            t.Pair[p.Infra.RopeFromImport, m.Infra.LogicalStatement]
        ],
        paths: t.MappingKV[str, p.Infra.RopePyName],
        path: Path,
    ) -> t.Pair[t.VariadicTuple[m.Infra.SourceRewrite], t.MappingKV[int, set[str]]]:
        """Plan every reference before removing any imported binding.

        Returns:
            Proven edits and obsolete bindings by their import declaration line.

        """
        bindings = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, 0).get_names()
        rewrites: list[m.Infra.SourceRewrite] = []
        removals: t.MutableMappingKV[int, set[str]] = {}
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
    def _constant_terminal(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        qualified: str,
    ) -> p.Infra.RopePyName:
        """Prove each reaching import declaration before evaluating its terminal.

        Returns:
            The unique terminal binding at the end of the import chain.

        Raises:
            ValueError: If the chain is cyclic, ambiguous or lacks its target.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        visited: set[t.Pair[Path, str]] = set()
        while isinstance(binding, p.Infra.RopeImportedName):
            resource = runtime.imported_module_resource(project, binding)
            path = Path(resource.real_path).resolve()
            key = path, binding.imported_name
            if key in visited:
                message = f"cyclic constant import chain: {qualified}"
                raise ValueError(message)
            visited.add(key)
            module = cls._constant_import_module(project, resource, qualified)
            imports = runtime.module_imports_for_pymodule(project, module)
            declarations = sum(
                alias == binding.imported_name
                or (alias is None and name == binding.imported_name)
                for statement in imports.imports
                for name, alias in statement.import_info.names_and_aliases
            )
            if declarations > 1:
                message = f"ambiguous constant import chain: {qualified}"
                raise ValueError(message)
            if binding.imported_name == "c" and module.source_code.startswith(
                c.Infra.AUTOGEN_HEADERS
            ):
                owner = module.get_resource()
                if owner is None:
                    message = f"generated constants package has no source: {qualified}"
                    raise ValueError(message)
                declaration = owner.parent.get_child(c.Infra.CONSTANTS_PY)
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        declaration, declaration.path
                    ),
                )
            terminal = module.get_attributes().get(binding.imported_name)
            if terminal is None:
                message = f"unresolved constant import chain: {qualified}"
                raise ValueError(message)
            binding = terminal
        return binding

    @staticmethod
    def _constant_import_module(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        qualified: str,
    ) -> p.Infra.RopePyModule:
        """Inspect package initialization as a file without evaluating import targets.

        Returns:
            The Rope module containing the declared source bindings.

        Raises:
            TypeError: If a package does not expose Rope's folder contract.
            ValueError: If the import is a namespace package without declarations.

        """
        if resource.is_folder():
            if not isinstance(resource, p.Infra.RopeRoot):
                message = f"constant import has no package resource: {qualified}"
                raise TypeError(message)
            if not resource.has_child(c.Infra.INIT_PY):
                message = f"constant import has no package declarations: {qualified}"
                raise ValueError(message)
            resource = resource.get_child(c.Infra.INIT_PY)
        return FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource, qualified
            ),
        )

    @classmethod
    def _constant_reference(
        cls,
        paths: t.MappingKV[str, p.Infra.RopePyName],
        binding: p.Infra.RopePyName,
        path: Path,
    ) -> str | None:
        """Require one published identity or one proven constants ancestry owner.

        Returns:
            The canonical public reference, or None for a nonconstant binding.

        Raises:
            ValueError: If multiple public destinations exist.

        """
        references = tuple(
            reference
            for reference, candidate in paths.items()
            if cls._constant_owner_binding(candidate, binding)
        )
        if not references:
            return None
        if len(references) != 1:
            message = f"constant has ambiguous public owners in {path}: {references}"
            raise ValueError(message)
        return references[0]

    @classmethod
    def _constant_binding_edits(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        imported: t.Pair[str, p.Infra.RopePyName],
        reference: str,
        facade: p.Infra.RopePyName,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        """Rewrite one imported identity while preserving local rebinding.

        Returns:
            Character edits proven by Rope's occurrence finder.

        Raises:
            ValueError: If the source resource is absent or c has another identity.

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
            if existing is not None and not cls._constant_owner_binding(facade, existing):
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
        removals: t.MappingKV[int, set[str]],
    ) -> str:
        """Remove complete proven imports, including annotation-only suites.

        Returns:
            Source preserving unrelated imports and comments.

        Raises:
            ValueError: If the consumer has no source resource.

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
        edits: t.SequenceOf[m.Infra.SourceRewrite],
        emptied: frozenset[int] | set[int],
    ) -> list[m.Infra.SourceRewrite]:
        """Remove an empty TYPE_CHECKING suite without emitting a stub.

        Returns:
            Disjoint edits retaining the suite's documentation comments.

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
        """Let Rope remove annotation-guard imports after their last reference.

        Returns:
            The source with unused TYPE_CHECKING imports removed.

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
            kept: list[t.Pair[str, str | None]] = []
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

    @classmethod
    def _constant_public_paths(
        cls,
        project: p.Infra.RopeProject,
        package: str,
    ) -> t.MappingKV[str, p.Infra.RopePyName]:
        """Discover actual facade members and inherited identities once per package.

        Returns:
            Public reference paths bound by the constants facade's Rope graph.

        """
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_semantic_module(
            project.get_module(f"{package}.{Path(c.Infra.CONSTANTS_PY).stem}")
        )
        facade = module.get_attributes().get("c")
        if facade is None:
            return {}
        found: t.MutableMappingKV[str, p.Infra.RopePyName] = {"c": facade}
        pending: t.MutableSequenceOf[
            t.Triple[str, p.Infra.RopePyObject, t.VariadicTuple[p.Infra.RopePyObject]]
        ] = [("c", facade.get_object(), ())]
        while pending:
            prefix, owner, ancestors = pending.pop()
            if owner in ancestors:
                continue
            if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(owner):
                continue
            for name, binding in owner.get_attributes().items():
                if name.startswith("_"):
                    continue
                reference = f"{prefix}.{name}"
                found[reference] = binding
                value = binding.get_object()
                if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value):
                    pending.append((reference, value, (*ancestors, owner)))
        return found

    @staticmethod
    def _constant_owner_binding(
        candidate: p.Infra.RopePyName, binding: p.Infra.RopePyName
    ) -> bool:
        """Prove a published value or a constants composition provider identity.

        Returns:
            Whether the binding is published directly or through class ancestry.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if runtime.same_name(candidate, binding):
            return True
        types = FlextInfraUtilitiesRopeRuntimeTypes
        wanted = binding.get_object()
        if not types.abstract_class(wanted):
            return False
        pending = [candidate.get_object()]
        visited: list[p.Infra.RopePyObject] = []
        while pending:
            owner = pending.pop()
            if owner in visited or not types.abstract_class(owner):
                continue
            if owner is wanted:
                return True
            visited.append(owner)
            pending.extend(owner.get_superclasses())
        return False

    @staticmethod
    def _constant_composition_base(
        module: p.Infra.RopePyModule,
        binding: p.Infra.RopePyName,
    ) -> bool:
        """Keep provider imports used in a class's composition header.

        Returns:
            Whether the imported identity is a composing superclass.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for scope in runtime.scope_at(module, 0).get_scopes():
            if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
                continue
            if binding.get_object() in scope.pyobject.get_superclasses():
                return True
        return False

    @staticmethod
    def _constant_facade_package(
        statements: t.SequenceOf[
            t.Pair[p.Infra.RopeFromImport, m.Infra.LogicalStatement]
        ],
        declared_package: str,
        path: Path,
    ) -> str:
        """Select the existing c binding, or the module's declared facade.

        Returns:
            The resolved constants facade package name.

        Raises:
            ValueError: If multiple constants facades are bound as ``c``.

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
