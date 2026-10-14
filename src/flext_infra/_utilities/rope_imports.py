"""Rope-backed import and rename operations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from collections.abc import Callable, MutableMapping
from pathlib import Path

import libcst as cst
from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesQualifiedNames,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities.rope_structure import FlextInfraUtilitiesRopeStructure


class FlextInfraUtilitiesRopeImports:
    """Rope-backed import organization and rename helpers."""

    @classmethod
    def source_import_statements(
        cls,
        project: p.Infra.RopeProject,
        source: str,
    ) -> t.VariadicTuple[p.Infra.RopeImportStatement]:
        """Collect imports in every lexical scope through native Rope owners.

        Native token occurrences exclude strings and comments. Native logical
        regions bound each fragment, and Rope's import tables parse the actual
        declaration, including inline suites and multiple imports on one line.

        Args:
            project: The Rope project instance.
            source: The source code to analyze.

        Returns:
            A tuple of Rope import statements found in the source.

        """
        module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            project,
            source,
        )
        imports = tuple(
            occurrence.offset
            for occurrence in (
                FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                    project, "import"
                ).find_occurrences(pymodule=module)
            )
        )
        if not imports:
            return ()
        froms = tuple(
            occurrence.offset
            for occurrence in (
                FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                    project, "from"
                ).find_occurrences(pymodule=module)
            )
        )
        statements: list[p.Infra.RopeImportStatement] = []
        position = 0
        from_position = 0
        preceding: int | None = None
        for region in FlextInfraUtilitiesRopeStructure.logical_statements(source):
            while position < len(imports) and imports[position] < region.start_offset:
                position += 1
            if position == len(imports):
                break
            offset = imports[position]
            if offset >= region.end_offset:
                continue
            start = offset
            while from_position < len(froms) and froms[from_position] < offset:
                preceding = froms[from_position]
                from_position += 1
            if preceding is not None and preceding >= region.start_offset:
                # Only a dotted import module may stand between `from` and
                # `import`; `yield from` and exception chaining are not imports.
                target = "".join(
                    source[preceding + len("from") : offset]
                    .replace("\\\n", "")
                    .split(),
                )
                if target and all(
                    not component or component.isidentifier()
                    for component in target.split(".")
                ):
                    start = preceding
            fragment = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project,
                source[start : region.end_offset],
            )
            table = FlextInfraUtilitiesRopeRuntimeModules.module_imports_for_pymodule(
                project,
                fragment,
            )
            line_offset = module.lines.get_line_number(start) - 1
            for statement in cls.import_statements(table):
                # Every table owns its fragment records. Preserve the native
                # import-info object and project the record's coordinates back
                # to the complete immutable source before returning it.
                statement.start_line += line_offset
                statement.end_line += line_offset
                statements.append(statement)
            while position < len(imports) and imports[position] < region.end_offset:
                position += 1
        return tuple(statements)

    @staticmethod
    def import_statements(
        module_imports: t.Infra.RopeModuleImports,
    ) -> t.SequenceOf[t.Infra.RopeImportStatement]:
        """Return validated Rope import statements from one module import collection.

        Returns:
            Validated Rope import statements from one module import collection.

        """
        return tuple(module_imports.imports)

    @staticmethod
    def import_statement_module_name(
        import_statement: t.Infra.RopeImportStatement,
    ) -> str | None:
        """Return the declared module name, preserving relative import depth.

        Returns:
            The declared module name, preserving relative import depth.

        """
        import_info = import_statement.import_info
        if not FlextInfraUtilitiesRopeRuntime.from_import_info(import_info):
            return None
        module_name = f"{'.' * import_info.level}{import_info.module_name}"
        return module_name or None

    @staticmethod
    def import_statement_names_and_aliases(
        import_statement: t.Infra.RopeImportStatement,
    ) -> t.SequenceOf[t.Pair[str, str | None]]:
        """Return validated imported-name pairs from one Rope import statement.

        Returns:
            Validated imported-name pairs from one Rope import statement.

        """
        import_info = import_statement.import_info
        if not (
            FlextInfraUtilitiesRopeRuntime.from_import_info(import_info)
            or FlextInfraUtilitiesRopeRuntime.normal_import_info(import_info)
        ):
            return ()
        return tuple(import_info.names_and_aliases)

    @classmethod
    def imported_module_paths(
        cls,
        module_imports: t.Infra.RopeModuleImports,
        *,
        current_package: str = "",
    ) -> t.StrSequence:
        """Return runtime import targets represented by a Rope module import set.

        Returns:
            Runtime import targets represented by a Rope module import set.

        """
        imported_paths: list[str] = []
        for import_statement in cls.import_statements(module_imports):
            declared_name = (
                getattr(import_statement.import_info, "module_name", "") or ""
            )
            level = getattr(import_statement.import_info, "level", 0) or 0
            module_name = cls.import_statement_module_name(import_statement)
            names_and_aliases = cls.import_statement_names_and_aliases(import_statement)
            if current_package and level > 0:
                resolved = FlextInfraUtilitiesRopeAnalysis.resolve_import_module(
                    current_package=current_package,
                    module_name=declared_name,
                    level=level,
                )
                if not resolved:
                    resolved = current_package
                if resolved != declared_name:
                    module_name = resolved
            if module_name is not None:
                imported_paths.append(module_name)
                imported_paths.extend(
                    f"{module_name}.{name}" for name, _alias in names_and_aliases
                )
                continue
            imported_paths.extend(name for name, _alias in names_and_aliases)
        return tuple(imported_paths)

    @staticmethod
    def find_occurrences(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        resources: t.SequenceOf[t.Infra.RopeResource] | None = None,
        in_hierarchy: bool = False,
    ) -> t.SequenceOf[t.Infra.RopeLocation]:
        """Find all occurrences of the symbol at offset across the project.

        Returns:
            The resulting ``t.SequenceOf[t.Infra.RopeLocation]``.

        Raises:
            RuntimeError: If rope find_occurrences failed for.

        """
        runtime_errors: t.VariadicTuple[type[BaseException]] = (
            *FlextInfraUtilitiesRopeRuntime.rope_runtime_errors(),
            TypeError,
            RecursionError,
        )
        try:
            return FlextInfraUtilitiesRopeRuntime.runtime_find_occurrences(
                rope_project,
                resource,
                offset,
                resources=resources,
                in_hierarchy=in_hierarchy,
            )
        except runtime_errors as exc:
            msg = (
                "rope find_occurrences failed for "
                f"{resource.path}@{offset}: {type(exc).__name__}: {exc!s}"
            )
            raise RuntimeError(msg) from exc

    @staticmethod
    def location_file_path(location: t.Infra.RopeLocation) -> Path | None:
        """Resolve one Rope occurrence back to an absolute file path.

        Returns:
            The resulting ``Path | None``.

        """
        resource = getattr(location, "resource", None)
        real_path = getattr(resource, "real_path", None)
        if isinstance(real_path, str) and real_path:
            return Path(real_path).resolve()
        path = getattr(resource, "path", None)
        if isinstance(path, str) and path:
            return Path(path)
        return None

    @staticmethod
    def indexed_search_resources(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        resource: t.Infra.RopeResource,
        name: str,
        definition_path: Path,
        dependent_import_targets: t.StrSequence = (),
    ) -> t.VariadicTuple[t.Infra.RopeResource]:
        """Build the reachability resource set for semantic occurrence searches.

        The workspace name index already narrows the candidate module set to
        files that contain ``name`` textually. This helper converts that cheap
        index into concrete Rope resources so callers can still rely on Rope's
        semantic identity checks without scanning the full project, keeping the
        removal-planning resource set: package reexports stay excluded and the
        candidates narrow to the import dependents when targets are given.

        Returns:
            The resulting ``t.VariadicTuple[t.Infra.RopeResource]``.

        """
        resolved_definition = definition_path.resolve()
        dependent_paths: frozenset[str] | None = None
        if dependent_import_targets:
            dependent_candidates: set[Path] = {resolved_definition}
            for import_target in dependent_import_targets:
                dependent_candidates.update(
                    path.resolve()
                    for path in rope_workspace.import_dependents(import_target)
                )
            dependent_paths = frozenset(str(path) for path in dependent_candidates)

        def admitted(resolved_path: Path) -> bool:
            return (
                resolved_path != resolved_definition
                and resolved_path.name != c.Infra.INIT_PY
                and (dependent_paths is None or str(resolved_path) in dependent_paths)
            )

        return FlextInfraUtilitiesRopeImports._indexed_search_resources(
            rope_workspace,
            resource=resource,
            name=name,
            definition_path=resolved_definition,
            occurrence_admitted=admitted,
        )

    @staticmethod
    def indexed_surface_search_resources(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        resource: t.Infra.RopeResource,
        name: str,
        definition_path: Path,
    ) -> t.VariadicTuple[t.Infra.RopeResource]:
        """Build the report-only resource set that spans package reexports.

        Report-only callers index every surface, so ``__init__`` reexports stay
        admissible and the candidate set is not narrowed to import dependents.

        Returns:
            The resulting ``t.VariadicTuple[t.Infra.RopeResource]``.

        """
        resolved_definition = definition_path.resolve()

        def admitted(resolved_path: Path) -> bool:
            return resolved_path != resolved_definition

        return FlextInfraUtilitiesRopeImports._indexed_search_resources(
            rope_workspace,
            resource=resource,
            name=name,
            definition_path=resolved_definition,
            occurrence_admitted=admitted,
        )

    @staticmethod
    def _indexed_search_resources(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        resource: t.Infra.RopeResource,
        name: str,
        definition_path: Path,
        occurrence_admitted: Callable[[Path], bool],
    ) -> t.VariadicTuple[t.Infra.RopeResource]:
        """Collect deduplicated Rope resources from the workspace name index.

        Returns:
            The resulting ``t.VariadicTuple[t.Infra.RopeResource]``.

        Raises:
            RuntimeError: If rope search resource unavailable for indexed path.

        """
        occurrences = rope_workspace.name_index().get(name, ())
        seen_paths = {str(definition_path)}
        resources: list[t.Infra.RopeResource] = [resource]
        for path, _surface, _lines in occurrences:
            resolved_path = path.resolve()
            if not occurrence_admitted(resolved_path):
                continue
            cache_key = str(resolved_path)
            if cache_key in seen_paths:
                continue
            candidate_resource = rope_workspace.resource(resolved_path)
            if candidate_resource is None:
                msg = (
                    "rope search resource unavailable for indexed path "
                    f"{resolved_path} while resolving '{name}'"
                )
                raise RuntimeError(msg)
            seen_paths.add(cache_key)
            resources.append(candidate_resource)
        return tuple(resources)

    @staticmethod
    def organize_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        *,
        apply: bool,
    ) -> p.Result[bool]:
        """Organize imports for one rope resource using rope's import tools.

        ``r.ok(True)`` when rope produced a non-empty change set; the
        change is applied when ``apply`` is set. ``r.ok(False)`` when
        rope produced no changes (already organised). ``r.fail(reason)``
        when rope raised a refactoring/resource/type error.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        runtime_errors: t.VariadicTuple[type[BaseException]] = (
            *FlextInfraUtilitiesRopeRuntime.rope_syntax_errors(),
            *FlextInfraUtilitiesRopeRuntime.rope_runtime_errors(),
            TypeError,
        )
        try:
            original_source = resource.read()
            organizer = FlextInfraUtilitiesRopeRuntime.import_organizer(rope_project)
            changes = organizer.organize_imports(resource)
        except runtime_errors as exc:
            return r[bool].fail(f"rope organize_imports raised: {exc!s}", exception=exc)
        if changes is None:
            return r[bool].ok(value=False)
        members = FlextInfraUtilitiesRopeRuntime.change_set_members(
            changes.changes,
            f"unexpected rope organize_imports result type: {type(changes).__name__}",
        )
        if members.failure:
            return r[bool].from_failure(members)
        change_list = members.unwrap()
        if not change_list:
            return r[bool].ok(value=False)
        changed = any(change.new_contents != original_source for change in change_list)
        if changed and apply:
            rope_project.do(changes)
        return r[bool].ok(changed)

    @classmethod
    def normalize_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        *,
        file_paths: t.SequenceOf[Path],
        preserve_canonical_aliases: bool = False,
    ) -> p.Result[bool]:
        """Normalize imports with Ruff and preserve semantic facade references.

        Ruff owns removal and ordering because it understands quoted typing
        expressions, including cast arguments. Rope's unused-import pass drops
        imports used only in those expressions before Ruff can inspect them.
        Rope still resolves canonical aliases when their preservation is requested.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        existing_paths = tuple(path.resolve() for path in file_paths if path.is_file())
        if not existing_paths:
            return r[bool].ok(value=False)
        canonical_imports: MutableMapping[
            Path,
            list[t.Pair[str, t.VariadicTuple[str]]],
        ] = {}
        if preserve_canonical_aliases:
            try:
                canonical_imports = cls._collect_canonical_alias_imports(
                    rope_project,
                    existing_paths,
                )
            except ValueError as exc:
                return r[bool].fail(str(exc), exception=exc)
        before = {path: path.read_bytes() for path in existing_paths}
        normalized_paths = tuple(str(path) for path in existing_paths)
        check_result = u.Cli.run_checked(
            ["ruff", "check", "--fix", "--select", "I,F401", *normalized_paths],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if check_result.failure:
            return r[bool].from_failure(check_result)
        if preserve_canonical_aliases:
            restore_result = cls._ensure_canonical_alias_imports(
                rope_project,
                canonical_imports,
            )
            if restore_result.failure:
                return r[bool].from_failure(restore_result)
        format_result = u.Cli.run_checked(
            ["ruff", "format", *normalized_paths],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if format_result.failure:
            return r[bool].from_failure(format_result)
        return r[bool].ok(
            any(path.read_bytes() != before[path] for path in existing_paths),
        )

    @classmethod
    def _collect_canonical_alias_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        file_paths: t.SequenceOf[Path],
    ) -> MutableMapping[Path, list[t.Pair[str, t.VariadicTuple[str]]]]:
        """Collect canonical runtime-alias imports eligible for semantic restore.

        Returns:
            The resulting ``MutableMapping[Path, list[t.Pair[str,
                t.VariadicTuple[str]]]]``.

        Raises:
            ValueError: If ``referenced_result.failure``.

        """
        runtime_aliases = u.runtime_alias_names(c.Infra.PKG_INFRA_UNDERSCORE)
        canonical_modules = frozenset({
            c.Infra.PKG_CORE_UNDERSCORE,
            c.Infra.PKG_INFRA_UNDERSCORE,
        })
        collected: MutableMapping[Path, list[t.Pair[str, t.VariadicTuple[str]]]] = {}
        for file_path in file_paths:
            resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                rope_project,
                file_path,
            )
            if resource is None:
                continue
            module_imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
                rope_project,
                resource,
            )
            entries: list[t.Pair[str, t.VariadicTuple[str]]] = []
            for import_stmt in cls.import_statements(module_imports):
                import_info = import_stmt.import_info
                if (
                    not FlextInfraUtilitiesRopeRuntime.from_import_info(import_info)
                    or import_info.level != 0
                ):
                    continue
                if import_info.module_name not in canonical_modules:
                    continue
                plain_names = [
                    (name, alias)
                    for name, alias in import_info.names_and_aliases
                    if alias is None
                ]
                if not plain_names or not all(
                    name in runtime_aliases for name, _alias in plain_names
                ):
                    continue
                referenced_result = cls._referenced_runtime_aliases(
                    resource.read(),
                    tuple(name for name, _alias in plain_names),
                )
                if referenced_result.failure:
                    msg = referenced_result.error or "alias reference scan failed"
                    raise ValueError(msg)
                referenced_aliases = referenced_result.unwrap()
                alias_names = tuple(
                    name for name, _alias in plain_names if name in referenced_aliases
                )
                if not alias_names:
                    continue
                entries.append((import_info.module_name, alias_names))
            if entries:
                collected[file_path] = entries
        return collected

    @staticmethod
    def _referenced_runtime_aliases(
        source: str,
        aliases: t.SequenceOf[str],
    ) -> p.Result[frozenset[str]]:
        """Return runtime aliases referenced after Ruff cleanup.

        Returns:
            Runtime aliases referenced after Ruff cleanup.

        """
        alias_set = frozenset(aliases)
        referenced: set[str] = set()
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return r[frozenset[str]].fail(
                f"source is not parseable after import cleanup: {exc!s}",
                exception=exc,
            )
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in alias_set:
                referenced.add(node.id)
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literal = node.value
                referenced.update(
                    alias for alias in alias_set if f"{alias}." in literal
                )
        return r[frozenset[str]].ok(frozenset(referenced))

    @classmethod
    def _ensure_canonical_alias_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        collected: MutableMapping[Path, list[t.Pair[str, t.VariadicTuple[str]]]],
    ) -> p.Result[bool]:
        """Re-add canonical runtime-alias imports removed by Ruff F401 cleanup.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        changed_any = False
        for file_path, entries in collected.items():
            restore_result = cls._restore_alias_imports(
                rope_project,
                file_path,
                entries,
            )
            if restore_result.failure:
                return r[bool].from_failure(restore_result)
            changed_any = changed_any or restore_result.unwrap()
        return r[bool].ok(changed_any)

    @classmethod
    def _restore_alias_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        file_path: Path,
        entries: t.SequenceOf[t.Pair[str, t.VariadicTuple[str]]],
    ) -> p.Result[bool]:
        """Restore one file's referenced canonical aliases Rope removed.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
            rope_project,
            file_path,
        )
        if resource is None:
            return r[bool].ok(value=False)
        module_imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
            rope_project,
            resource,
        )
        referenced_aliases_result = cls._referenced_runtime_aliases(
            resource.read(),
            tuple(alias for _module_name, aliases in entries for alias in aliases),
        )
        if referenced_aliases_result.failure:
            return r[bool].from_failure(referenced_aliases_result)
        referenced_aliases = referenced_aliases_result.unwrap()
        current = cls._current_plain_aliases(module_imports)
        changed = False
        for module_name, alias_names in entries:
            missing = sorted(
                (frozenset(alias_names) & referenced_aliases)
                - current.get(module_name, set()),
            )
            if not missing:
                continue
            existing = current.get(module_name, set())
            if existing:
                # Merge into the existing from-import via rope mutation.
                changed = (
                    cls._merge_missing_into_statement(
                        module_imports,
                        module_name,
                        missing,
                    )
                    or changed
                )
            else:
                module_imports.add_import(
                    FlextInfraUtilitiesRopeRuntime.from_import(
                        module_name,
                        0,
                        [(name, None) for name in missing],
                    ),
                )
                changed = True
        if not changed:
            return r[bool].ok(value=False)
        module_imports.remove_duplicates()
        module_imports.sort_imports()
        updated_source = module_imports.get_changed_source()
        if updated_source == resource.read():
            return r[bool].ok(value=False)
        resource.write(updated_source)
        return r[bool].ok(value=True)

    @staticmethod
    def _current_plain_aliases(
        module_imports: t.Infra.RopeModuleImports,
    ) -> MutableMapping[str, set[str]]:
        """Map each absolute from-import's module to its unaliased names.

        Returns:
            The module name to unaliased imported names.

        """
        current: MutableMapping[str, set[str]] = defaultdict(set)
        for import_stmt in FlextInfraUtilitiesRopeImports.import_statements(
            module_imports,
        ):
            import_info = import_stmt.import_info
            if (
                not FlextInfraUtilitiesRopeRuntime.from_import_info(import_info)
                or import_info.level != 0
            ):
                continue
            current[import_info.module_name].update(
                name for name, alias in import_info.names_and_aliases if alias is None
            )
        return current

    @staticmethod
    def _merge_missing_into_statement(
        module_imports: t.Infra.RopeModuleImports,
        module_name: str,
        missing: t.StrSequence,
    ) -> bool:
        """Merge missing names into the module's existing absolute from-import.

        Returns:
            True when a matching statement was found and mutated.

        """
        for import_stmt in FlextInfraUtilitiesRopeImports.import_statements(
            module_imports,
        ):
            import_info = import_stmt.import_info
            if (
                not FlextInfraUtilitiesRopeRuntime.from_import_info(import_info)
                or import_info.level != 0
                or import_info.module_name != module_name
            ):
                continue
            merged = list(import_info.names_and_aliases)
            present = {name for name, alias in merged if alias is None}
            merged.extend(
                (name, None) for name in sorted(missing) if name not in present
            )
            import_stmt.import_info = FlextInfraUtilitiesRopeRuntime.from_import(
                module_name,
                0,
                merged,
            )
            return True
        return False

    @classmethod
    def relocate_from_import_aliases(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        *,
        source_module: str,
        target_module: str,
        aliases: t.StrSequence,
    ) -> str | None:
        """Move names and their bindings between absolute imports using Rope.

        The relocated source is written to ``resource`` and returned; ``None``
        means no import changed.

        Returns:
            The resulting ``str | None``.

        """
        updated = cls.plan_from_import_aliases(
            rope_project,
            resource,
            source_module=source_module,
            target_module=target_module,
            aliases=aliases,
        )
        if updated is not None:
            resource.write(updated)
        return updated

    @classmethod
    def package_root_import_owner(
        cls, project_root: Path, source_module: str
    ) -> str | None:
        """Resolve an own-package target; foreign-package findings stay residue.

        Returns:
            The declared project package or no owned relocation target.
        """
        own = FlextInfraUtilitiesPyproject.project_package_name(project_root)
        return own if source_module.split(".", maxsplit=1)[0] == own else None

    @classmethod
    def plan_package_root_import(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        source_module: str,
        aliases: t.StrSequence,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan an own-package import without publishing or rebinding foreign names.

        The project declaration owns the target. Rope owns import bindings and
        aliases; foreign-package findings remain unmodified residue.

        Returns:
            A typed source edit, no-op, or an explicit resource/ownership failure.
        """
        entry = rope_workspace.module(file_path)
        root = entry.project_root if entry is not None else None
        if root is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
                f"import owner has no declared project: {file_path}",
            )
        own = cls.package_root_import_owner(root, source_module)
        if own is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        resource = rope_workspace.resource(file_path)
        if resource is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
                f"import owner is not a Rope resource: {file_path}",
            )
        original = resource.read()
        updated = cls.plan_from_import_aliases(
            rope_workspace.rope_project,
            resource,
            source_module=source_module,
            target_module=own,
            aliases=aliases,
        )
        if updated is None:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok((
            m.Infra.SemanticMigrationEdit(
                file_path=file_path.resolve(),
                original_source=original,
                updated_source=updated,
                changes=(f"bound import to declared package {own}",),
            ),
        ))

    @classmethod
    def plan_from_import_aliases(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        *,
        source_module: str,
        target_module: str,
        aliases: t.StrSequence,
    ) -> str | None:
        """Prepare scoped imports in place without changing reference text.

        Invalid Rope or CST representations propagate their native type errors.

        Returns:
            The prepared source, or None when no selected import exists.

        Raises:
            RuntimeError: If an import identity is unresolved, unsupported, or
                conflicts with a target binding in the same lexical scope.
        """
        aliases_to_move = frozenset(aliases)
        if not aliases_to_move:
            return None
        original_source: str = resource.read()
        tree = ast.parse(original_source)
        owners = (
            (source_module, rope_project.find_module(source_module)),
            (target_module, rope_project.find_module(target_module)),
        )
        # Only physical Python newlines contribute to AST line numbers.
        lines = re.split(r"(?<=\n)|(?<=\r)(?!\n)", original_source)
        imports = cls._scoped_from_imports(
            rope_project,
            resource,
            tree,
            owners,
            cls._reject_module_alias_consumers(
                rope_project,
                resource,
                lines,
                owners[0][1],
                aliases_to_move,
            ),
        )
        if owners[0][1] is None:
            for statement, module_name, _scope in imports:
                if module_name != source_module or not any(
                    name.name in aliases_to_move for name in statement.names
                ):
                    continue
                # Repeated bindings fail before unresolved source identities.
                if len({name.asname or name.name for name in statement.names}) != len(
                    statement.names,
                ):
                    msg = (
                        "conflicting Rope imported binding: "
                        f"{resource.path}:{statement.lineno}"
                    )
                    raise RuntimeError(msg)
                msg = f"unresolved Rope source module: {source_module}"
                raise RuntimeError(msg)
        changes = [
            cls._render_import_alias_statement(
                resource,
                statement,
                lines,
                target_module,
                aliases_to_move,
            )
            for statement, module_name, _scope in imports
            if module_name == source_module
            and cls._validate_import_alias_bindings(
                resource,
                statement,
                imports,
                target_module,
                aliases_to_move,
            )
        ]
        if not changes:
            return None
        return FlextInfraUtilitiesRopeSource.rewrite_source_at_offsets(
            rope_project,
            resource,
            changes,
            apply=False,
        )

    @staticmethod
    def _ast_character_offset(
        lines: t.StrSequence,
        line: int,
        column: int | None,
    ) -> int:
        """Convert a physical AST UTF-8 byte position into a Rope character offset.

        Returns:
            The character offset in the original source snapshot.
        """
        return sum(map(len, lines[: line - 1])) + len(
            lines[line - 1].encode("utf-8")[:column].decode("utf-8"),
        )

    @classmethod
    def _reject_module_alias_consumers(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        lines: t.StrSequence,
        source_resource: t.Infra.RopeResource | None,
        aliases: frozenset[str],
    ) -> t.VariadicTuple[t.Infra.RopePyName]:
        """Reject selected exports in runtime or scoped quoted type attributes.

        Returns:
            The selected export identities for subsequent star-import validation.

        Raises:
            RuntimeError: If an attribute consumes a selected source export.
        """
        selected_names = (
            tuple(
                binding
                for name, binding in FlextInfraUtilitiesRopeCore
                .resolve_pymodule(
                    rope_project,
                    source_resource,
                )
                .get_attributes()
                .items()
                if name in aliases
            )
            if source_resource is not None
            else ()
        )
        pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(rope_project, resource)
        protected = FlextInfraUtilitiesSemanticFamilyTypeReferences.type_payload_ranges(
            "".join(lines),
            rope_project,
            pymodule,
        )
        source = "".join(lines)
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(source):
            expression = source[begin:end]
            if "." not in expression or any(
                start <= begin < end <= stop for start, stop in protected
            ):
                continue
            binding = FlextInfraUtilitiesRopeRuntime.expression_name(
                FlextInfraUtilitiesRopeRuntime.scope_at(pymodule, begin),
                expression,
            )
            if any(
                FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
                for expected in selected_names
            ):
                msg = f"unsupported Rope module consumer: {resource.path}:{pymodule.lines.get_line_number(begin)}"
                raise RuntimeError(msg)
        for (
            expression,
            scope,
            line,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.scoped_quoted_type_references(
            "".join(lines),
            rope_project,
            pymodule,
        ):
            if "." not in expression:
                continue
            binding = FlextInfraUtilitiesRopeRuntime.expression_name(scope, expression)
            if any(
                FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
                for expected in selected_names
            ):
                msg = f"unsupported Rope module consumer: {resource.path}:{line}"
                raise RuntimeError(msg)
        return selected_names

    @classmethod
    def _scoped_from_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        tree: ast.Module,
        owners: t.SequenceOf[t.Pair[str, t.Infra.RopeResource | None]],
        selected_names: t.SequenceOf[t.Infra.RopePyName],
    ) -> list[t.Triple[ast.ImportFrom, str, ast.AST]]:
        """Resolve import identities and lexical scopes before planning any edit.

        Returns:
            Resolved imports and their innermost lexical scopes.
        """
        imports: list[t.Triple[ast.ImportFrom, str, ast.AST]] = []
        scopes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        ]
        for statement in ast.walk(tree):
            if not isinstance(statement, ast.ImportFrom):
                continue
            module_name = cls._relocated_from_import_module(
                rope_project,
                resource,
                statement,
                owners,
            )
            if module_name is None:
                continue
            if any(name.name == "*" for name in statement.names):
                cls._reject_star_alias_consumer(
                    rope_project,
                    resource,
                    statement,
                    module_name,
                    selected_names,
                )
            scope = max(
                (
                    candidate
                    for candidate in scopes
                    if (candidate.lineno, candidate.col_offset)
                    < (statement.lineno, statement.col_offset)
                    and statement.lineno <= (candidate.end_lineno or candidate.lineno)
                ),
                key=lambda candidate: (candidate.lineno, candidate.col_offset),
                default=tree,
            )
            imports.append((statement, module_name, scope))
        return imports

    @staticmethod
    def _relocated_from_import_module(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        owners: t.SequenceOf[t.Pair[str, t.Infra.RopeResource | None]],
    ) -> str | None:
        """Resolve relative imports by physical Rope identity, in owner order.

        Returns:
            The absolute module name, or None for an unresolved relative import.
        """
        if not statement.level:
            return statement.module or ""
        imported_resource = rope_project.find_relative_module(
            statement.module or "",
            resource.parent,
            statement.level,
        )
        if imported_resource is None:
            return None
        module_name = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project,
            imported_resource,
        ).get_name()
        return next(
            (
                name
                for name, owner in owners
                if owner is not None and imported_resource.real_path == owner.real_path
            ),
            module_name,
        )

    @staticmethod
    def _reject_star_alias_consumer(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        module_name: str,
        selected_names: t.SequenceOf[t.Infra.RopePyName],
    ) -> None:
        """Reject star imports exposing a selected Rope identity.

        Raises:
            TypeError: If the imported module has no valid module AST.
            RuntimeError: If the star import exposes a selected source export.
        """
        imported_resource = (
            rope_project.find_relative_module(
                statement.module or "",
                resource.parent,
                statement.level,
            )
            if statement.level
            else rope_project.find_module(module_name)
        )
        if imported_resource is None:
            return
        imported = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project,
            imported_resource,
        )
        imported_tree = imported.get_ast()
        if not isinstance(imported_tree, ast.Module):
            msg = f"invalid Rope module AST: {module_name}"
            raise TypeError(msg)
        exports: t.StrSequence | None = None
        for declaration in imported_tree.body:
            if not isinstance(declaration, ast.Assign | ast.AnnAssign):
                continue
            if "__all__" in (
                FlextInfraUtilitiesRopeAnalysis.assignment_target_names(declaration)
            ):
                exports = (
                    FlextInfraUtilitiesRopeAnalysis.literal_string_sequence(
                        declaration.value,
                    )
                    if isinstance(declaration.value, ast.List | ast.Tuple | ast.Set)
                    and all(
                        isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                        for element in declaration.value.elts
                    )
                    else None
                )
        # Only a sole, unescaped literal binding proves exclusion. Any extra
        # access can mutate or publish the list through an unknown writer.
        if sum(
            isinstance(node, ast.Name) and node.id == "__all__"
            for node in ast.walk(imported_tree)
        ) != 1 or any(
            (isinstance(node, ast.Constant) and node.value == "__all__")
            or (isinstance(node, ast.Attribute) and node.attr == "__all__")
            or (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"exec", "eval", "globals", "locals", "vars"}
            )
            for node in ast.walk(imported_tree)
        ):
            exports = None
        exported_names = (
            exports
            if exports is not None
            else tuple(
                name for name in imported.get_attributes() if not name.startswith("_")
            )
        )
        if any(
            FlextInfraUtilitiesRopeRuntime.same_name(expected, binding)
            for name, binding in imported.get_attributes().items()
            if name in exported_names
            for expected in selected_names
        ):
            msg = (
                "unsupported Rope module/star consumer: "
                f"{resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)

    @staticmethod
    def _validate_import_alias_bindings(
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        imports: t.SequenceOf[t.Triple[ast.ImportFrom, str, ast.AST]],
        target_module: str,
        aliases: frozenset[str],
    ) -> bool:
        """Reject repeated or conflicting selected bindings before rendering.

        Returns:
            Whether this statement contains any selected import.

        Raises:
            RuntimeError: If source bindings repeat or conflict.
        """
        moved = [name for name in statement.names if name.name in aliases]
        if not moved:
            return False
        if len({name.asname or name.name for name in statement.names}) != len(
            statement.names,
        ):
            msg = (
                f"conflicting Rope imported binding: {resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)
        scope = next(
            scope for imported, _module_name, scope in imports if imported is statement
        )
        for target_statement, imported_module, target_scope in imports:
            if imported_module != target_module or target_scope is not scope:
                continue
            if any(
                existing.name == "*"
                or any(
                    (existing.asname or existing.name) == (name.asname or name.name)
                    and existing.name != name.name
                    for name in moved
                )
                for existing in target_statement.names
            ):
                msg = f"ambiguous Rope target binding: {target_module}"
                raise RuntimeError(msg)
        return True

    @classmethod
    def _render_import_alias_statement(
        cls,
        resource: t.Infra.RopeFile,
        statement: ast.ImportFrom,
        lines: t.StrSequence,
        target_module: str,
        aliases: frozenset[str],
    ) -> t.Triple[int, int, str]:
        """Render a source range with its contiguous relocated CST alias groups.

        Returns:
            The original character range and its replacement source.

        Raises:
            RuntimeError: If a mixed import occurs in an inline suite.
        """
        start = cls._ast_character_offset(lines, statement.lineno, statement.col_offset)
        end = cls._ast_character_offset(
            lines,
            statement.end_lineno or statement.lineno,
            statement.end_col_offset,
        )
        indentation = (
            lines[statement.lineno - 1]
            .encode("utf-8")[: statement.col_offset]
            .decode("utf-8")
        )
        parsed = cst.parse_module("".join(lines)[start:end] + "\n")
        replacements = cls._relocated_import_groups(
            parsed,
            target_module,
            aliases,
            f"{resource.path}:{statement.lineno}",
        )
        if len(replacements) > 1 and indentation.strip():
            msg = (
                "unsupported Rope inline mixed import: "
                f"{resource.path}:{statement.lineno}"
            )
            raise RuntimeError(msg)
        return (
            start,
            end,
            ("\n" + indentation).join(
                parsed.code_for_node(replacement) for replacement in replacements
            ),
        )

    @staticmethod
    def _relocated_import_groups(
        parsed: cst.Module,
        target_module: str,
        aliases: frozenset[str],
        location: str,
    ) -> list[cst.ImportFrom]:
        """Preserve alias ordering and trivia while splitting selected CST groups.

        Returns:
            The contiguous selected and unselected import groups.

        Raises:
            TypeError: If CST returns an invalid import representation.
        """
        line = parsed.body[0]
        if not isinstance(line, cst.SimpleStatementLine):
            msg = f"unsupported Rope import statement: {location}"
            raise TypeError(msg)
        imported_statement = line.body[0]
        if not isinstance(imported_statement, cst.ImportFrom) or isinstance(
            imported_statement.names,
            cst.ImportStar,
        ):
            msg = f"unsupported Rope import statement: {location}"
            raise TypeError(msg)
        groups: list[t.Pair[bool, list[cst.ImportAlias]]] = []
        for alias in imported_statement.names:
            selected = parsed.code_for_node(alias.name) in aliases
            if groups and groups[-1][0] == selected:
                groups[-1][1].append(alias)
            else:
                groups.append((selected, [alias]))
        return [
            imported_statement.with_changes(
                module=cst.parse_expression(target_module)
                if selected
                else imported_statement.module,
                relative=() if selected else imported_statement.relative,
                names=FlextInfraUtilitiesQualifiedNames.normalized_import_aliases(
                    names,
                    parenthesized=imported_statement.lpar is not None,
                ),
            )
            for selected, names in groups
        ]

    @staticmethod
    def _persisted_import_block(
        module_imports: t.Infra.RopeModuleImports,
        resource: t.Infra.RopeFile,
        *,
        apply: bool,
    ) -> str | None:
        """Normalize, render, and optionally write one module's import block.

        ``None`` when the rendered block already matches the file on disk.

        Returns:
            The resulting ``str | None``.

        """
        module_imports.remove_duplicates()
        module_imports.sort_imports()
        updated: str = module_imports.get_changed_source()
        if updated == resource.read():
            return None
        if apply:
            resource.write(updated)
        return updated

    @staticmethod
    def add_import(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        from_module: str,
        names: t.StrSequence,
        *,
        apply: bool = True,
    ) -> str | None:
        """Add ``from <module> import <names>`` using rope's ImportOrganizer.

        Returns:
            The resulting ``str | None``.

        """
        module_imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
            rope_project,
            resource,
        )
        module_imports.add_import(
            FlextInfraUtilitiesRopeRuntime.from_import(
                from_module,
                0,
                [(name, None) for name in sorted(names)],
            ),
        )
        return FlextInfraUtilitiesRopeImports._persisted_import_block(
            module_imports,
            resource,
            apply=apply,
        )

    @staticmethod
    def remove_import_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        from_module: str,
        names: t.StrSequence,
        *,
        apply: bool = True,
    ) -> str | None:
        """Remove specific names from ``from <module> import ...``.

        Returns:
            The resulting ``str | None``.

        """
        names_to_remove = frozenset(names)
        module_imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
            rope_project,
            resource,
        )
        changed = False
        import_statements = FlextInfraUtilitiesRopeImports.import_statements(
            module_imports,
        )
        for import_stmt in import_statements:
            import_info = import_stmt.import_info
            from_import = (
                import_info
                if FlextInfraUtilitiesRopeRuntime.from_import_info(import_info)
                and import_info.level == 0
                and import_info.module_name == from_module
                else None
            )
            if from_import is None:
                continue
            kept = [
                (name, alias)
                for name, alias in from_import.names_and_aliases
                if name not in names_to_remove
            ]
            if len(kept) < len(from_import.names_and_aliases):
                import_stmt.import_info = FlextInfraUtilitiesRopeRuntime.from_import(
                    from_module,
                    0,
                    kept,
                )
                changed = True
        if not changed:
            return None
        return FlextInfraUtilitiesRopeImports._persisted_import_block(
            module_imports,
            resource,
            apply=apply,
        )

    # ------------------------------------------------------------------
    # Import alignment: every relative from-import takes its absolute form
    # ------------------------------------------------------------------

    @staticmethod
    def _absolute_from_import(source_module: str, module_name: str, level: int) -> str:
        """Resolve one relative from-import target to its absolute module name.

        Python resolves ``level`` dots from the module's own package, so a
        module ``a.b.c`` with ``level=1`` imports from ``a.b``.

        Returns:
            The resulting ``str``.

        """
        parts = source_module.split(".")
        base = parts[: max(len(parts) - level, 0)]
        return ".".join(part for part in (*base, module_name) if part)

    @classmethod
    def align_module_imports(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        repository_root: Path,
        index: m.Infra.RopeWorkspaceIndex,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan absolute-form rewrites for every relative from-import.

        Package initializers are generated and render their own imports, so
        only authored modules are planned.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        file_plans: list[m.Infra.CodegenFilePlan] = []
        for entry in sorted(
            index.modules_by_path.values(),
            key=lambda item: str(item.file_path),
        ):
            if entry.is_package_init or not entry.module_name:
                continue
            plan_result = cls._align_entry_imports(
                rope_project,
                repository_root,
                entry,
            )
            if plan_result.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(
                    plan_result,
                )
            plan_value, plan_present = plan_result.value
            if plan_present and plan_value is not None:
                file_plans.append(plan_value)
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(file_plans))

    @classmethod
    def _align_entry_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        repository_root: Path,
        entry: m.Infra.RopeModuleIndexEntry,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Plan the absolute-form rewrite of one indexed module's imports.

        Returns:
            One file plan when the module's imports change; otherwise None.

        """
        file_path = entry.file_path
        resource = (
            FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                rope_project,
                file_path,
            )
            if file_path.is_file()
            else None
        )
        if resource is None:
            return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok((None, False))
        module_imports = FlextInfraUtilitiesRopeCore.resolve_module_imports(
            rope_project,
            resource,
        )
        changed = cls._rewrite_relative_from_imports(
            module_imports,
            entry.module_name,
        )
        if not changed:
            return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok((None, False))
        updated_source = module_imports.get_changed_source()
        original_source = resource.read()
        if updated_source == original_source:
            return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok((None, False))
        before = u.Cli.atomic_read_binary_file_state(file_path, required=False)
        if before.failure:
            return r[t.Pair[m.Infra.CodegenFilePlan | None, bool]].from_failure(before)
        snapshot = before.unwrap()
        if snapshot.mode is None:
            return r[t.Pair[m.Infra.CodegenFilePlan | None, bool]].fail(
                f"import source has no permission snapshot: {file_path}",
            )
        return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok(
            (
                m.Infra.CodegenFilePlan(
                    project=repository_root,
                    path=file_path.resolve(),
                    before=snapshot,
                    desired_content=updated_source.encode("utf-8"),
                    desired_mode=snapshot.mode,
                ),
                True,
            ),
        )

    @classmethod
    def _rewrite_relative_from_imports(
        cls,
        module_imports: t.Infra.RopeModuleImports,
        source_module: str,
    ) -> bool:
        """Rewrite every relative from-import of one module to absolute form.

        Returns:
            True when any import statement changed.

        Raises:
            ValueError: If a relative import level escapes the package.

        """
        changed = False
        for import_stmt in cls.import_statements(module_imports):
            import_info = import_stmt.import_info
            if not FlextInfraUtilitiesRopeRuntime.from_import_info(import_info):
                continue
            level = import_info.level or 0
            if level == 0:
                continue
            absolute = cls._absolute_from_import(
                source_module,
                import_info.module_name or "",
                level,
            )
            if not absolute:
                msg = (
                    f"relative import level {level} escapes the package of "
                    f"{source_module}"
                )
                raise ValueError(msg)
            import_stmt.import_info = FlextInfraUtilitiesRopeRuntime.from_import(
                absolute,
                0,
                list(import_info.names_and_aliases),
            )
            changed = True
        return changed


__all__: list[str] = ["FlextInfraUtilitiesRopeImports"]
