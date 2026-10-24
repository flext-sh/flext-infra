"""Payload dependency, import and orphaned-import resolution for relocation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities._semantic_cutover.declaration_relocation_exports import (
    FlextInfraUtilitiesSemanticDeclarationRelocationExports,
)


class FlextInfraUtilitiesSemanticDeclarationRelocationImports(
    FlextInfraUtilitiesSemanticDeclarationRelocationExports,
    FlextInfraUtilitiesDeclarationPayload,
):
    """Resolve the imports and nested dependencies a relocated payload needs."""

    _COMPOSED_REFERENCE_SEGMENTS = 2

    @classmethod
    def _remove_orphaned_imports(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        original: str,
        proposed: str,
    ) -> str:
        """Remove only native imports whose last proven use this cutover removed.

        Args:
            project: The Rope project owning the cutover sources.
            resource: Source resource of the rewritten module.
            original: Source text before this cutover's rewrites.
            proposed: Source text after this cutover's rewrites.

        Returns:
            The proposed text with newly orphaned imports removed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        before = runtime.build_string_module(project, original, resource=resource)
        after = runtime.build_string_module(project, proposed, resource=resource)
        orphaned = cls._used_import_names(project, before) - cls._used_import_names(
            project,
            after,
        )
        if not orphaned:
            return proposed
        rewrites: list[m.Infra.SourceRewrite] = []
        lines = cls._source_lines(proposed)
        for statement in runtime.module_imports_for_pymodule(project, after).imports:
            information = statement.import_info
            retained = tuple(
                (name, alias)
                for name, alias in information.names_and_aliases
                if (alias or name.partition(".")[0]) not in orphaned
            )
            if retained == tuple(information.names_and_aliases):
                continue
            replacement = (
                runtime.from_import(
                    information.module_name,
                    information.level,
                    retained,
                )
                if isinstance(information, p.Infra.RopeFromImport)
                else runtime.normal_import(retained)
            )
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=lines.get_line_start(statement.start_line),
                    end=min(lines.get_line_start(statement.end_line), len(proposed)),
                    text=replacement.get_import_statement() + "\n" if retained else "",
                ),
            )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            proposed,
            tuple(rewrites),
        ).new_contents

    @classmethod
    def _used_import_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> set[str]:
        imports = cls.native_import_infos(project, module)
        names = {
            alias or name.partition(".")[0]
            for information in imports
            for name, alias in information.names_and_aliases
        }
        used: set[str] = set()
        for name in names:
            binding = module.get_scope().get_names().get(name)
            if binding is None:
                continue
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                project,
                name,
                binding,
                imports=False,
                in_hierarchy=False,
            )
            if any(
                not occurrence.is_defined()
                for occurrence in finder.find_occurrences(pymodule=module)
            ):
                used.add(name)
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        for _begin, _end, literal, scope in types.quoted_type_regions(
            module.source_code,
            project,
            module,
        ):
            used.update(cls._quoted_dependency_names(project, scope, literal) & names)
        exported = tuple(
            statement
            for statement in FlextInfraUtilitiesRopeStructure.logical_statements(
                module.source_code
            )
            if FlextInfraUtilitiesRopeStructure.target_name(statement) == "__all__"
        )
        for (
            start,
            stop,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(
            module.source_code
        ):
            if module.source_code[start] == "#" or not any(
                statement.start_offset <= start < stop <= statement.end_offset
                for statement in exported
            ):
                continue
            literal = types.string_constant(module.source_code[start:stop])
            if literal in names:
                used.add(literal)
        return used
    @classmethod
    def _payload_imports(
        cls,
        project: p.Infra.RopeProject,
        origin: Path,
        target: Path,
        node: p.Infra.RopeScope,
    ) -> t.Pair[
        t.VariadicTuple[p.Infra.RopeImportInfo],
        t.MappingKV[t.Pair[int, int], str],
    ]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        source = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(origin.relative_to(root).as_posix()),
            origin,
        ).read()
        destination = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            project.get_resource(target.relative_to(root).as_posix()),
        ).get_scope()
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                project.get_resource(origin.relative_to(root).as_posix()), origin
            ),
        )
        scope = module.get_scope()
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo] = {}
        for information in cls.native_import_infos(project, module):
            for name, alias in information.names_and_aliases:
                imports[alias or name.split(".")[0]] = information
        dependencies, required = cls._payload_dependency_routes(
            (project, scope),
            destination,
            target,
            node,
        )
        for name in sorted(
            cls._payload_dependency_names(project, module, node, source, dependencies)
        ):
            if hasattr(builtins, name) and name not in scope.get_defined_names():
                continue
            statement = imports.get(name)
            if statement is None or (
                isinstance(statement, p.Infra.RopeFromImport) and statement.level
            ):
                msg = (
                    "declaration-relocation: unresolved/outer dependency "
                    f"{origin}:{node.pyobject.get_name()} -> {name}"
                )
                raise ValueError(msg)
            existing = destination.get_names().get(name)
            original = scope.get_names().get(name)
            if existing is not None and (
                original is None or not runtime.same_name(original, existing)
            ):
                msg = f"declaration-relocation: conflicting dependency {target}:{name}"
                raise ValueError(msg)
            if existing is None:
                aliases = tuple(
                    (imported_name, alias)
                    for imported_name, alias in statement.names_and_aliases
                    if (alias or imported_name.split(".")[0]) == name
                )
                imported = (
                    runtime.from_import(statement.module_name, statement.level, aliases)
                    if isinstance(statement, p.Infra.RopeFromImport)
                    else runtime.normal_import(aliases)
                )
                required.append(imported)
        return tuple(required), dependencies

    @classmethod
    def native_import_infos(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> t.VariadicTuple[p.Infra.RopeImportInfo]:
        """Read native import records, including native guarded source regions.

        Returns:
            Every native import record of the module, top-level and guarded.

        Raises:
            ValueError: If native import records differ from their lexical occurrences;
                or if native import token has no enclosing logical statement.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        records = FlextInfraUtilitiesRopeImports.source_import_statements(
            project,
            module.source_code,
        )
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
            project, "import"
        )
        tokens = tuple(
            occurrence.offset for occurrence in finder.find_occurrences(pymodule=module)
        )
        if len(tokens) != len(records):
            msg = "native import records differ from their lexical occurrences"
            raise ValueError(msg)
        guard = cls.identity_name(project, c.Infra.TYPING_GUARD_IDENTITY)
        facts = FlextInfraUtilitiesRopeStructure.logical_statements(module.source_code)
        selected: list[p.Infra.RopeImportInfo] = []
        conditions: list[t.Pair[int, bool]] = []
        position = 0
        for statement in facts:
            while conditions and statement.indent <= conditions[-1][0]:
                conditions.pop()
            words = statement.text.strip().split(maxsplit=1)
            head = words[0].rstrip(":") if words else ""
            if head in {
                "else",
                "elif",
                "except",
                "finally",
                "try",
                "with",
                "for",
                "while",
            }:
                # Module scope does not make a conditional import unconditional.
                # Only the explicitly proven typing guard may be promoted.
                conditions.append((statement.indent, False))
            if statement.category == c.Infra.StatementCategory.IF_GUARD:
                expression = (
                    statement.text.strip().removeprefix("if ").partition(":")[0]
                )
                expression = expression.removesuffix(" is True").strip()
                conditions.append((
                    statement.indent,
                    runtime.same_name(
                        guard,
                        runtime.expression_name(module.get_scope(), expression),
                    ),
                ))
            while position < len(tokens) and tokens[position] < statement.end_offset:
                offset = tokens[position]
                record = records[position]
                position += 1
                if offset < statement.start_offset:
                    msg = "native import token has no enclosing logical statement"
                    raise ValueError(msg)
                if runtime.scope_at(module, offset).get_kind() == "Module" and all(
                    condition for _indent, condition in conditions
                ):
                    selected.append(record.import_info)
        return tuple(selected)

    @staticmethod
    def _dependency_source(
        source: str,
        dependencies: t.MappingKV[t.Pair[int, int], str],
    ) -> str:
        """Rewrite only bound executable attributes, retaining ordinary strings.

        Returns:
            Source rebound to the resolved dependency owners.

        """
        rewrites = sorted(
            (start, stop - start, text) for (start, stop), text in dependencies.items()
        )
        end = -1
        selected: list[t.Triple[int, int, str]] = []
        for start, length, replacement in sorted(
            rewrites, key=lambda row: (row[0], -row[1])
        ):
            if start >= end:
                selected.append((start, length, replacement))
                end = start + length
        for start, length, replacement in reversed(selected):
            source = source[:start] + replacement + source[start + length :]
        return source

    @classmethod
    def _payload_dependency_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: p.Infra.RopeScope,
        source: str,
        dependencies: t.MappingKV[t.Pair[int, int], str],
    ) -> set[str]:
        """Keep original imports only when transferred code still loads them.

        Returns:
            The unreplaced original dependency roots.

        """
        lines = cls._source_lines(source)
        begin = lines.get_line_start(node.get_start())
        end = min(lines.get_line_end(node.get_end()) + 1, len(source))
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        changed = cls._dependency_source(source[begin:end], dependencies)
        remaining = {
            changed[start:stop].split(".")[0]
            for start, stop in types.reference_regions(changed)
        }
        original = cls._payload_loaded_names(project, module, node, source)
        replaced = {
            source[begin + first : begin + last].split(".", maxsplit=1)[0]
            for first, last in dependencies
            if source[begin + first : begin + last]
            .split(".", maxsplit=1)[0]
            .isidentifier()
        }
        for (first, last), text in dependencies.items():
            old = types.string_constant(source[begin + first : begin + last])
            new = types.string_constant(text)
            if old is not None and new is not None:
                replaced.update(
                    cls._quoted_dependency_names(project, module.get_scope(), old)
                    - cls._quoted_dependency_names(project, module.get_scope(), new),
                )
                remaining.update(
                    cls._quoted_dependency_names(project, module.get_scope(), new),
                )
        return original - (replaced - remaining)

    @classmethod
    def _payload_dependency_routes(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        destination: p.Infra.RopeScope,
        target: Path,
        node: p.Infra.RopeScope,
    ) -> t.Pair[
        t.MappingKV[t.Pair[int, int], str],
        list[p.Infra.RopeImportInfo],
    ]:
        """Resolve nested dependencies to their authored declaration identities.

        Conflicting owners surface as ``ValueError`` during owner resolution.

        Returns:
            Attribute replacements and required direct owner imports.

        Raises:
            TypeError: The dependency scope lacks its native source module.

        """
        dependencies: t.MutableMappingKV[t.Pair[int, int], str] = {}
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo] = {}
        module = context[1].pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = "payload dependency scope has no native source module"
            raise TypeError(message)
        source = module.source_code
        lines = cls._source_lines(source)
        first = lines.get_line_start(node.get_start())
        last = min(lines.get_line_end(node.get_end()) + 1, len(source))
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        annotations = types.annotation_regions(source, module)
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(
            source[first:last]
        ):
            item = source[first + begin : first + end]
            if "." not in item:
                continue
            line = next(
                (
                    declaration_line
                    for start, stop, declaration_line in annotations
                    if start <= first + begin < first + end <= stop
                ),
                None,
            )
            lexical = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                module,
                first + begin,
                declaration_line=line,
            )
            replacement = cls._dependency_replacement(
                (context[0], lexical),
                destination,
                target,
                item,
                imports,
            )
            if replacement is None:
                continue
            dependencies[begin, end] = replacement
        for begin, end, literal, lexical in types.quoted_type_regions(
            source,
            context[0],
            module,
        ):
            if not first <= begin < end <= last:
                continue
            changed = types.rewrite_type_source(
                literal,
                context[0],
                lexical,
                lambda scope, value: cls._dependency_replacement(
                    (context[0], scope),
                    destination,
                    target,
                    value,
                    imports,
                ),
            )
            if changed != literal:
                dependencies[begin - first, end - first] = repr(changed)
        return dependencies, list(imports.values())

    @classmethod
    def _dependency_replacement(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        destination: p.Infra.RopeScope,
        target: Path,
        expression: str,
        imports: t.MutableMappingKV[str, p.Infra.RopeImportInfo],
    ) -> str | None:
        owner = cls._payload_dependency_owner(context, expression, target)
        if owner is None:
            return None
        provider, outer, child = owner
        resource = provider.get_resource()
        if resource is not None and Path(resource.real_path).resolve() == target:
            return child
        existing = destination.get_names().get(outer)
        declared = provider.get_attribute(outer)
        if existing is not None and not FlextInfraUtilitiesRopeRuntimeModules.same_name(
            existing,
            declared,
        ):
            msg = f"declaration-relocation: conflicting dependency {target}:{outer}"
            raise ValueError(msg)
        if existing is None:
            imports[outer] = FlextInfraUtilitiesRopeRuntimeModules.from_import(
                provider.get_name(),
                0,
                ((outer, None),),
            )
        return f"{outer}.{child}"

    @classmethod
    def _payload_dependency_owner(
        cls,
        context: t.Pair[p.Infra.RopeProject, p.Infra.RopeScope],
        item: str,
        target: Path,
    ) -> t.Triple[p.Infra.RopePyModule, str, str] | None:
        """Find a unique same-package nested declaration, never a facade alias.

        Returns:
            The declaring module, outer class and nested declaration, if unique.

        Raises:
            TypeError: The nested declaration has no native source module.

        """
        project, scope = context
        segments = item.split(".")
        imported = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            scope,
            segments[0],
        )
        if (
            isinstance(imported, p.Infra.RopeImportedName)
            and imported.imported_module.module_name is not None
            and not imported.imported_module.level
        ):
            binding = cls._resolve_binding(
                project,
                imported.imported_module.module_name,
                imported.imported_name,
                Path(project.root.real_path),
                {},
            )
            if (
                binding is not None
                and len(segments) == cls._COMPOSED_REFERENCE_SEGMENTS
            ):
                owned = cls._composed_dependency_owner(
                    binding.get_object(), segments[1], target
                )
                if owned is not None:
                    return owned
            for segment in segments[1:]:
                if binding is None:
                    break
                binding = binding.get_object().get_attributes().get(segment)
        else:
            binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(scope, item)
        if binding is None:
            return None
        provider, line = binding.get_definition_location()
        if provider is None or line is None:
            return None
        provider = provider.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider):
            message = "nested declaration requires a native source module"
            raise TypeError(message)
        resource = provider.get_resource()
        if (
            resource is None
            or Path(resource.real_path).resolve().parent.parent != target.parent.parent
        ):
            return None
        owners = [
            (outer, child)
            for outer in provider.get_scope().get_scopes()
            if outer.get_kind() == "Class"
            for child in outer.get_scopes()
            if child.get_kind() == "Class" and child.get_start() == line
        ]
        return (
            (
                provider,
                owners[0][0].pyobject.get_name(),
                owners[0][1].pyobject.get_name(),
            )
            if len(owners) == 1
            else None
        )

    @classmethod
    def _composed_dependency_owner(
        cls,
        composed: p.Infra.RopePyObject,
        name: str,
        target: Path,
    ) -> t.Triple[p.Infra.RopePyModule, str, str] | None:
        """Bind preset and primitive exports to the class that declares them.

        Returns:
            The unique authored declaring owner, including assigned primitives.

        Raises:
            TypeError: An authored declaring owner has no native source module.
            ValueError: If multiple authored owners declare the dependency.

        """
        owners: list[t.Triple[p.Infra.RopePyModule, str, str]] = []
        for ancestor in cls.class_ancestry(composed):
            scope = ancestor.get_scope()
            provider = ancestor.get_module()
            resource = provider.get_resource() if provider is not None else None
            if scope is None or provider is None or resource is None:
                continue
            if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider):
                message = "declaration owner requires a native source module"
                raise TypeError(message)
            path = Path(resource.real_path).resolve()
            if (
                path.parent.parent == target.parent.parent
                and name in scope.get_defined_names()
            ):
                owners.append((provider, ancestor.get_name(), name))
        if len(owners) > 1:
            msg = f"declaration-relocation: ambiguous dependency owner {name}"
            raise ValueError(msg)
        return owners[0] if owners else None

    @classmethod
    def _payload_loaded_names(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: p.Infra.RopeScope,
        source: str,
    ) -> set[str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        first, last = node.get_region()
        resource = module.get_resource()
        loaded: set[str] = set()
        for name, binding in module.get_scope().get_names().items():
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                project,
                name,
                binding,
                imports=False,
                in_hierarchy=False,
            )
            if any(
                not occurrence.is_defined() and first <= occurrence.offset < last
                for occurrence in finder.find_occurrences(resource=resource)
            ):
                loaded.add(name)
        types = FlextInfraUtilitiesSemanticFamilyTypeReferences
        for begin, end, literal, lexical in types.quoted_type_regions(
            source, project, module
        ):
            if first <= begin < end <= last:
                for name in cls._quoted_dependency_names(project, lexical, literal):
                    binding = runtime.expression_name(lexical, name)
                    supplier, line = (
                        binding.get_definition_location()
                        if binding is not None
                        else (None, None)
                    )
                    if (
                        supplier is module
                        and line is not None
                        and (node.get_start() <= line <= node.get_end())
                    ):
                        continue
                    loaded.add(name)
        return loaded

    @classmethod
    def _quoted_dependency_names(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        source: str,
    ) -> set[str]:
        names: set[str] = set()

        def collect(_scope: p.Infra.RopeScope, expression: str) -> None:
            names.add(expression.partition(".")[0])

        FlextInfraUtilitiesSemanticFamilyTypeReferences.rewrite_type_source(
            source,
            project,
            scope,
            collect,
        )
        return names


__all__: list[str] = ["FlextInfraUtilitiesSemanticDeclarationRelocationImports"]
