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
            f"census: resolve constant declaration qualifiers in {len(candidates)} modules"
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
            rewrites.extend(
                m.Infra.SourceRewrite(start=left, end=right, text="ClassVar")
                for left, right in refactors.semantic_regions(
                    module,
                    "${qualifier}",
                    arguments=qualifiers,
                    start=start,
                    end=end,
                )
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
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        convention = rope_workspace.convention(path)
        policy = convention.module_policy
        if policy.expected_alias == "c" or policy.expected_family == "Constants":
            return source, ()
        if (
            path.name in c.Infra.NAMESPACE_DEFAULT_OWNER_FILE_NAMES
            and (path.parent / c.Infra.CONSTANTS_PY).is_file()
        ):
            return source, ()
        if any(
            FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(parent.name)
            == "c"
            for parent in path.parents
            if parent.is_relative_to(rope_workspace.repository_root)
        ):
            return source, ()
        layout = convention.project_layout
        if layout is None:
            return source, ()
        resource = project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix()
        )
        module = project.get_pymodule(resource)
        imports = runtime.module_imports_for_pymodule(project, module)
        statements = tuple(
            statement
            for statement in imports.imports
            if isinstance(statement.import_info, p.Infra.RopeFromImport)
            and statement.import_info.module_name.startswith(
                c.Infra.PKG_PREFIX_UNDERSCORE
            )
            and not statement.import_info.level
        )
        if not any(
            name not in c.Infra.ALIAS_NAMES or (name == "c" and alias is not None)
            for statement in statements
            for name, alias in statement.import_info.names_and_aliases
        ):
            return source, ()
        package = cls._constant_facade_package(statements, layout.package_name, path)
        if package not in paths:
            paths[package] = cls._constant_public_paths(project, package)
        scope = runtime.scope_at(module, 0)
        bindings = scope.get_names()
        rewrites: list[m.Infra.SourceRewrite] = []
        removals: t.MutableMappingKV[int, set[str]] = {}
        descriptions: list[str] = []
        for statement in statements:
            info = statement.import_info
            for imported, alias in info.names_and_aliases:
                name = alias or imported
                binding = bindings.get(name)
                if binding is None or (imported == "c" and alias is None):
                    continue
                references = tuple(
                    reference
                    for reference, candidate in paths[package].items()
                    if cls._constant_owner_binding(candidate, binding)
                )
                if not references:
                    continue
                depth = min(reference.count(".") for reference in references)
                references = tuple(
                    reference
                    for reference in references
                    if reference.count(".") == depth
                )
                if len(references) != 1:
                    message = (
                        f"constant {name} has ambiguous public owners in {path}: "
                        f"{references}"
                    )
                    raise ValueError(message)
                finder = refactors.create_occurrence_finder(
                    project, name, binding, imports=False, in_hierarchy=False
                )
                occurrences = tuple(finder.find_occurrences(resource=resource))
                if any(item.is_defined() for item in occurrences):
                    continue
                if cls._constant_composition_base(module, binding):
                    continue
                if not occurrences:
                    continue
                for occurrence in occurrences:
                    local_scope = runtime.scope_at(module, occurrence.offset)
                    existing = local_scope.lookup("c")
                    if existing is not None and not runtime.same_name(
                        paths[package]["c"], existing
                    ):
                        message = f"constant facade c is shadowed in {path}"
                        raise ValueError(message)
                    start, end = occurrence.get_word_range()
                    rewrites.append(
                        m.Infra.SourceRewrite(start=start, end=end, text=references[0])
                    )
                removals.setdefault(statement.start_line, set()).add(name)
                descriptions.append(f"constant consumer {name} -> {references[0]}")
        if not rewrites:
            return source, ()
        changed = refactors.content_change(resource, source, rewrites)
        proposed = runtime.build_string_module(
            project, changed.new_contents, resource=resource
        )
        organized = runtime.module_imports_for_pymodule(project, proposed)
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
        organized.add_import(runtime.from_import(package, 0, [("c", None)]))
        organized.remove_duplicates()
        return organized.get_changed_source(), tuple(descriptions)

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
        pending = [("c", facade.get_object(), ())]
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
        """Prove a published value or a constants composition provider identity."""
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
        """Keep provider imports used in a class's composition header."""
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
