"""Census-derived constant consumer cutover across declared workspace members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import cli

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
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
        working = dict(sources)
        working.update({edit.file_path: edit.updated_source for edit in declarations})
        consumers = cls._plan_constant_imports(rope_workspace, working)
        if consumers.failure:
            return consumers
        working.update({
            edit.file_path: edit.updated_source for edit in consumers.value
        })
        changes = {
            edit.file_path: edit.changes for edit in (*declarations, *consumers.value)
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
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Repair typing.Final in constants class suites by Rope identity.

        A module Final retains its contract. A class constant must be a
        ClassVar so a composed Pydantic namespace never turns it into a field.
        Aliased typing imports resolve through the lexical Rope scope; a
        same-spelled user type is not a typing qualifier.

        Returns:
            Syntax-preserving declaration edits within the constants family.
        """
        candidates = tuple(
            (path, source)
            for path, source in cls._editable_sources(sources)
            if any(
                FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                    parent.name
                )
                == "c"
                for parent in path.parents
                if parent.is_relative_to(workspace.repository_root)
            )
        )
        if not candidates:
            return ()
        cli.display_text(
            "census: resolve constant declaration qualifiers "
            f"in {len(candidates)} modules"
        )
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        project = runtime.snapshot_project(workspace.rope_project, sources)
        try:
            return tuple(
                edit
                for path, source in candidates
                if (edit := cls._constant_annotation_edit(project, path, source))
                is not None
            )
        finally:
            project.close()

    @classmethod
    def _constant_annotation_edit(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
    ) -> m.Infra.SemanticMigrationEdit | None:
        """Plan one module's identity-proven Final-to-ClassVar repair.

        Returns:
            The source edit, or None when no class declaration needs repair.

        Raises:
            ValueError: If ClassVar would capture an existing annotation binding.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix(),
        )
        module = project.get_pymodule(resource)
        classvar = project.get_module("typing").get_attribute("ClassVar")
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        qualifiers = {"qualifier": "name=typing.Final"}
        statements = refactors.semantic_regions(
            module,
            "${target}: ${qualifier}[${payload}] = ${value}",
            arguments=qualifiers,
        )
        cli.display_text(
            f"census: {path.name}: identity-proven Final declarations={len(statements)}"
        )
        rewrites: list[m.Infra.SourceRewrite] = []
        for start, end in statements:
            scope = runtime.scope_at(module, start)
            if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
                continue
            existing = scope.lookup("ClassVar")
            if existing is not None and not runtime.same_name(classvar, existing):
                message = f"constant ClassVar binding is shadowed in {path}"
                raise ValueError(message)
            qualifiers_in_statement = refactors.semantic_regions(
                module,
                "${qualifier}",
                arguments=qualifiers,
                start=start,
                end=end,
            )
            rewrites.extend(
                m.Infra.SourceRewrite(start=left, end=right, text="ClassVar")
                for left, right in qualifiers_in_statement[:1]
            )
        if not rewrites:
            return None
        changed = refactors.content_change(resource, source, rewrites)
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        imports = runtime.module_imports_for_pymodule(project, proposed)
        imports.add_import(runtime.from_import("typing", 0, [("ClassVar", None)]))
        imports.remove_duplicates()
        return m.Infra.SemanticMigrationEdit(
            file_path=path,
            original_source=source,
            updated_source=imports.get_changed_source(),
            changes=(f"typing.Final class constants -> ClassVar: {len(rewrites)}",),
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
                return cls._rewrite_constant_consumer(
                    path, source, rope_workspace, project, paths
                )

            return cls._semantic_edits(cls._editable_sources(sources), rewrite)
        finally:
            project.close()

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
        organized = runtime.module_imports_for_pymodule(project, proposed)
        cls._remove_constant_imports(organized, removals)
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
    ) -> t.VariadicTuple[p.Infra.RopeImportStatement]:
        """Read first-party absolute imports from Rope's module owner.

        Returns:
            From-imports participating in constants ownership resolution.
        """
        return tuple(
            statement
            for statement in (
                FlextInfraUtilitiesRopeRuntimeModules.module_imports_for_pymodule(
                    project, module
                ).imports
            )
            if isinstance(statement.import_info, p.Infra.RopeFromImport)
            and statement.import_info.module_name.startswith(
                c.Infra.PKG_PREFIX_UNDERSCORE
            )
            and not statement.import_info.level
        )

    @classmethod
    def _constant_import_plan(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        statements: t.SequenceOf[p.Infra.RopeImportStatement],
        paths: t.MappingKV[str, p.Infra.RopePyName],
        path: Path,
    ) -> t.Pair[t.VariadicTuple[m.Infra.SourceRewrite], t.MappingKV[int, set[str]]]:
        """Plan every reference before removing any imported binding.

        Returns:
            Proven edits and obsolete bindings by their import declaration line.

        Raises:
            TypeError: If an import plan contains an unsupported declaration.
        """
        bindings = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, 0).get_names()
        rewrites: list[m.Infra.SourceRewrite] = []
        removals: t.MutableMappingKV[int, set[str]] = {}
        for statement in statements:
            info = statement.import_info
            if not isinstance(info, p.Infra.RopeFromImport):
                message = "constant import plan requires a from-import declaration"
                raise TypeError(message)
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

    @staticmethod
    def _constant_terminal(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        qualified: str,
    ) -> p.Infra.RopePyName:
        """Prove each reaching import declaration before evaluating its terminal.

        Returns:
            The unique terminal binding at the end of the import chain.

        Raises:
            ValueError: If the chain is cyclic, ambiguous or lacks its target.
            TypeError: If an imported Python module has no inspectable Rope source.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        visited: set[t.Pair[Path, str]] = set()
        while isinstance(binding, p.Infra.RopeImportedName):
            path = runtime.imported_module_path(project, binding)
            key = path, binding.imported_name
            if key in visited:
                message = f"cyclic constant import chain: {qualified}"
                raise ValueError(message)
            visited.add(key)
            module = binding.imported_module.get_object()
            if not isinstance(module, p.Infra.RopePyModule):
                message = f"constant import has no Python module source: {qualified}"
                raise TypeError(message)
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
            terminal = module.get_attributes().get(binding.imported_name)
            if terminal is None:
                message = f"unresolved constant import chain: {qualified}"
                raise ValueError(message)
            binding = terminal
        return binding

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

    @staticmethod
    def _remove_constant_imports(
        organized: p.Infra.RopeModuleImports,
        removals: t.MappingKV[int, set[str]],
    ) -> None:
        """Remove only bindings whose occurrence cutover was completely planned."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for statement in organized.imports:
            info = statement.import_info
            removed = removals.get(statement.start_line, set())
            if not removed or not isinstance(info, p.Infra.RopeFromImport):
                continue
            statement.import_info = runtime.from_import(
                info.module_name,
                info.level,
                [
                    (name, alias)
                    for name, alias in info.names_and_aliases
                    if (alias or name) not in removed
                ],
            )

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
        statements: t.SequenceOf[p.Infra.RopeImportStatement],
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
            for statement in statements
            if isinstance((info := statement.import_info), p.Infra.RopeFromImport)
            and any(
                name == "c" and alias is None for name, alias in info.names_and_aliases
            )
        }
        if len(public_packages) > 1:
            msg = f"multiple constants facades bound as c in {path}"
            raise ValueError(msg)
        return next(iter(public_packages), declared_package)


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantConsumers"]
