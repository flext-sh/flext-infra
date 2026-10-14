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
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
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
                    changes=changes[path],
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
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
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
                for rule in contracts.declared_contract_rules()
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
                reused, literal_changes = cls._reuse_literal_returns(
                    path, updated, rope_workspace, project, paths
                )
                enums, enum_changes = cls._reuse_literal_enums(
                    path, reused, rope_workspace, project, paths
                )
                immutable, immutable_changes = cls._reuse_frozenset_membership(
                    path, enums, rope_workspace, project, paths
                )
                return immutable, (
                    *changes,
                    *literal_changes,
                    *enum_changes,
                    *immutable_changes,
                )

            return cls._semantic_edits(cls._editable_sources(sources), rewrite)
        finally:
            project.close()

    @classmethod
    def _reuse_literal_returns(
        cls,
        path: Path,
        source: str,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Reuse public string and decimal integer constants in complete returns.

        Only native literal regions belonging to a single constants assignment
        are candidates. Native return matching leaves annotations, metadata,
        docstrings, defaults and computed expressions outside this slice.

        Returns:
            Source edits preserving the literal's exact scalar type and value.

        Raises:
            ValueError: If a return has competing owners or a shadowed facade.
        """
        convention = workspace.convention(path)
        if (
            cls._constant_definition_source(workspace, convention)
            or path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
            or convention.module_policy.expected_alias in {"config", "settings"}
            or convention.project_layout is None
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
            for literal_type in ("builtins.str", "builtins.int")
        }
        if not any(returns_by_type.values()):
            return source, ()
        package = cls._constant_facade_package(
            cls._constant_imports(project, module),
            convention.project_layout.package_name,
            path,
        )
        if project.find_module(f"{package}.constants") is None:
            return source, ()
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        public = paths[package]
        if not public:
            return source, ()
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
                    previous = matched.get((start, end))
                    if previous is not None and previous != reference:
                        message = (
                            f"literal return has ambiguous public constant owners "
                            f"in {path}: {previous}, {reference}"
                        )
                        raise ValueError(message)
                    matched[start, end] = reference
        if not matched:
            return source, ()
        changed = refactors.content_change(
            resource,
            source,
            tuple(
                m.Infra.SourceRewrite(start=start, end=end, text=f"return {reference}")
                for (start, end), reference in matched.items()
            ),
        )
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        imports = runtime.module_imports_for_pymodule(project, proposed)
        imports.add_import(runtime.from_import(package, 0, [("c", None)]))
        imports.remove_duplicates()
        return imports.get_changed_source(), (
            f"literal returns -> {package}.c: {len(matched)} references",
        )

    @classmethod
    def _constant_derives_from(
        cls,
        project: p.Infra.RopeProject,
        candidate: p.Infra.RopePyName,
        qualified: str,
    ) -> bool:
        """Resolve a member's declaring ancestry through native class identity."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = cls._constant_terminal(project, candidate, "enum member")
        module, line = binding.get_definition_location()
        if module is None or line is None:
            return False
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
        """Reject a competing or conditionally imported constants binding."""
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

    @classmethod
    def _reuse_frozenset_membership(
        cls,
        path: Path,
        source: str,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Reuse static singleton frozensets only inside membership predicates.

        Construction and return contexts retain their observable object identity.

        Returns:
            Edits to identity-proven builtin calls in ``in``/``not in`` predicates.

        Raises:
            ValueError: If a membership predicate has competing constants owners.
        """
        convention = workspace.convention(path)
        if (
            cls._constant_definition_source(workspace, convention)
            or path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
            or convention.module_policy.expected_alias in {"config", "settings"}
            or convention.project_layout is None
        ):
            return source, ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = runtime.build_string_module(project, source, resource=resource)
        arguments = {"frozen": "name=builtins.frozenset"}
        if not refactors.semantic_regions(
            module, "${frozen}(${value})", arguments=arguments
        ):
            return source, ()
        package = cls._constant_facade_package(
            cls._constant_imports(project, module),
            convention.project_layout.package_name,
            path,
        )
        if project.find_module(f"{package}.constants") is None:
            return source, ()
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        public = paths[package]
        if not public:
            return source, ()
        matched: t.MutableMappingKV[t.Pair[int, int], str] = {}
        for literal_type in ("builtins.str", "builtins.int"):
            for expression, reference in cls._literal_constant_patterns(
                project, public, literal_type=literal_type, frozen=True
            ):
                if cls._constant_derives_from(project, public[reference], "enum.Enum"):
                    continue
                for pattern in (
                    f"${{subject}} in {expression}",
                    f"${{subject}} not in {expression}",
                ):
                    for start, end in refactors.semantic_regions(
                        module, pattern, arguments=arguments
                    ):
                        cls._admit_literal_facade(
                            project, module, public["c"], start, path
                        )
                        constructors = refactors.semantic_regions(
                            module,
                            expression,
                            arguments=arguments,
                            start=start,
                            end=end,
                        )
                        if constructors:
                            region = max(constructors, key=operator.itemgetter(0))
                            previous = matched.get(region)
                            if previous is not None and previous != reference:
                                message = (
                                    f"frozenset predicate has ambiguous public owners "
                                    f"in {path}: {previous}, {reference}"
                                )
                                raise ValueError(message)
                            matched[region] = reference
        if not matched:
            return source, ()
        changed = refactors.content_change(
            resource,
            source,
            tuple(
                m.Infra.SourceRewrite(start=start, end=end, text=reference)
                for (start, end), reference in matched.items()
            ),
        )
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        imports = runtime.module_imports_for_pymodule(project, proposed)
        imports.add_import(runtime.from_import(package, 0, [("c", None)]))
        imports.remove_duplicates()
        return imports.get_changed_source(), (
            f"singleton frozenset predicates -> {package}.c: {len(matched)} references",
        )

    @classmethod
    def _reuse_literal_enums(
        cls,
        path: Path,
        source: str,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        paths: t.MutableMappingKV[str, t.MappingKV[str, p.Infra.RopePyName]],
    ) -> t.Infra.TransformResult:
        """Reuse declared StrEnum members in singleton Literal field annotations.

        Returns:
            Native source-region edits retaining the annotation's Literal owner.

        Raises:
            ValueError: If an enum owner or the consumer facade is ambiguous.
        """
        convention = workspace.convention(path)
        if (
            cls._constant_definition_source(workspace, convention)
            or path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
            or convention.module_policy.expected_alias in {"config", "settings"}
            or convention.project_layout is None
        ):
            return source, ()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = runtime.build_string_module(project, source, resource=resource)
        if not refactors.semantic_regions(
            module,
            "${literal}[${value}]",
            arguments={"literal": "name=typing.Literal"},
        ):
            return source, ()
        package = cls._constant_facade_package(
            cls._constant_imports(project, module),
            convention.project_layout.package_name,
            path,
        )
        if project.find_module(f"{package}.constants") is None:
            return source, ()
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        public = paths[package]
        if not public:
            return source, ()
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
                    if annotations:
                        begin, finish = min(annotations, key=operator.itemgetter(0))
                        regions = refactors.semantic_regions(
                            module, literal, arguments={}, start=begin, end=finish
                        )
                        for region in regions:
                            previous = matched.get(region)
                            if previous is not None and previous != reference:
                                message = (
                                    f"literal annotation has ambiguous enum owners "
                                    f"in {path}: {previous}, {reference}"
                                )
                                raise ValueError(message)
                            matched[region] = reference
        if not matched:
            return source, ()
        changed = refactors.content_change(
            resource,
            source,
            tuple(
                m.Infra.SourceRewrite(start=start, end=end, text=reference)
                for (start, end), reference in matched.items()
            ),
        )
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        imports = runtime.module_imports_for_pymodule(project, proposed)
        imports.add_import(runtime.from_import(package, 0, [("c", None)]))
        imports.remove_duplicates()
        return imports.get_changed_source(), (
            f"singleton Literal fields -> {package}.c: {len(matched)} references",
        )

    @classmethod
    def _literal_constant_patterns(
        cls,
        project: p.Infra.RopeProject,
        public: t.MappingKV[str, p.Infra.RopePyName],
        *,
        literal_type: str = "builtins.str",
        frozen: bool = False,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Read proven literals at uniquely assigned public c bindings.

        Strings require exact native literal boundaries. Integer declarations
        admit decimal tokens only. Frozen candidates additionally require the
        native builtin constructor around one such literal in a singleton set.

        Returns:
            Raw source patterns and their identity-proven public references.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        structure = FlextInfraUtilitiesRopeStructure
        found: list[t.Pair[str, str]] = []
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
            resource = module.get_resource()
            if resource is None:
                continue
            declarations.setdefault(Path(resource.real_path), (module, []))[1].append((
                binding,
                line,
            ))
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
                    if (
                        statement.line != line
                        or statement.enclosing_kind != c.Infra.RopeScopeKind.CLASS
                        or statement.category
                        not in {
                            c.Infra.StatementCategory.ASSIGN,
                            c.Infra.StatementCategory.ANN_ASSIGN,
                        }
                    ):
                        continue
                    target = structure.target_name(statement)
                    if not target or not runtime.same_name(
                        binding,
                        runtime.expression_name(
                            runtime.scope_at(module, statement.start_offset), target
                        ),
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
                            literal_type == "builtins.str"
                            and (start, end) not in literal_regions
                        ):
                            continue
                        if literal_type == "builtins.int" and not literal.isdecimal():
                            continue
                        expression = (
                            f"${{frozen}}({{{literal}}})" if frozen else literal
                        )
                        arguments = (
                            {"frozen": "name=builtins.frozenset"} if frozen else {}
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
        module = project.get_pymodule(resource)
        statements = cls._constant_imports(project, module)
        if not any(
            name not in c.Infra.ALIAS_NAMES or (name == "c" and alias is not None)
            for statement in statements
            for name, alias in statement.import_info.names_and_aliases
        ):
            return source, ()
        package = cls._constant_facade_package(statements, layout.package_name, path)
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        rewrites, removals = cls._constant_import_plan(
            project, module, statements, paths[package], path
        )
        if not rewrites:
            return source, ()
        changed = refactors.content_change(resource, source, rewrites)
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        cleaned = cls._remove_constant_imports(project, proposed, removals)
        proposed = runtime.build_string_module(project, cleaned, resource=resource)
        organized = runtime.module_imports_for_pymodule(project, proposed)
        organized.add_import(runtime.from_import(package, 0, [("c", None)]))
        organized.remove_duplicates()
        return organized.get_changed_source(), (
            f"constant consumers -> {package}.c: {len(rewrites)} references",
        )

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
    ) -> t.VariadicTuple[m.Infra.RopeSourceImport]:
        """Read first-party absolute imports from Rope's module owner.

        Returns:
            From-imports participating in constants ownership resolution.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        found: list[m.Infra.RopeSourceImport] = []
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
                if info.level or not info.module_name.startswith(
                    c.Infra.PKG_PREFIX_UNDERSCORE
                ):
                    continue
                found.append(
                    m.Infra.RopeSourceImport(
                        import_info=info,
                        start_line=statement.line,
                        start_offset=statement.start_offset,
                        end_offset=statement.end_offset,
                        source=statement.text,
                        type_checking_guarded=statement.type_checking_guarded,
                    )
                )
        return tuple(found)

    @classmethod
    def _constant_import_plan(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        statements: t.SequenceOf[m.Infra.RopeSourceImport],
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
        for statement in statements:
            info = statement.import_info
            for imported, alias in info.names_and_aliases:
                name = alias or imported
                binding = bindings.get(name)
                if binding is None or (imported == "c" and alias is None):
                    continue
                binding = cls._constant_terminal(
                    project, binding, f"{info.module_name}.{imported}"
                )
                reference = cls._constant_reference(paths, binding, path)
                if reference is None:
                    continue
                changes = cls._constant_binding_edits(
                    project, module, (name, binding), reference, paths["c"]
                )
                if not changes:
                    continue
                rewrites.extend(changes)
                removals.setdefault(statement.start_line, set()).add(name)
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
                module = project.get_pymodule(declaration)
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
        return project.get_pymodule(resource)

    @classmethod
    def _constant_reference(
        cls,
        paths: t.MappingKV[str, p.Infra.RopePyName],
        binding: p.Infra.RopePyName,
        path: Path,
    ) -> str | None:
        """Choose the unique closest public owner in the constants ancestry.

        Returns:
            The canonical public reference, or None for a nonconstant binding.

        Raises:
            ValueError: If multiple equally close public owners exist.
        """
        references = tuple(
            reference
            for reference, candidate in paths.items()
            if cls._constant_owner_binding(candidate, binding)
        )
        if not references:
            return None
        depth = min(reference.count(".") for reference in references)
        closest = tuple(
            reference for reference in references if reference.count(".") == depth
        )
        if len(closest) != 1:
            message = f"constant has ambiguous public owners in {path}: {closest}"
            raise ValueError(message)
        return closest[0]

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
            if existing is not None and not runtime.same_name(facade, existing):
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
        for statement in cls._constant_imports(project, module):
            removed = removals.get(statement.start_line)
            if not removed:
                continue
            parsed = runtime.build_string_module(
                project, statement.source.lstrip(), resource=resource
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
                emptied.add(statement.start_line)
            indentation = len(statement.source) - len(statement.source.lstrip())
            indent = statement.source[:indentation]
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
        facade = (
            project
            .get_module(f"{package}.{Path(c.Infra.CONSTANTS_PY).stem}")
            .get_attributes()
            .get("c")
        )
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
        statements: t.SequenceOf[m.Infra.RopeSourceImport],
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
            statement.import_info.module_name
            for statement in statements
            if any(
                name == "c" and alias is None
                for name, alias in statement.import_info.names_and_aliases
            )
        }
        if len(public_packages) > 1:
            msg = f"multiple constants facades bound as c in {path}"
            raise ValueError(msg)
        return next(iter(public_packages), declared_package)


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantConsumers"]
