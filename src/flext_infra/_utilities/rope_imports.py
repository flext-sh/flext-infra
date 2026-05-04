"""Rope-backed import and rename operations."""

from __future__ import annotations

from pathlib import Path

import rope.contrib.findit as rope_findit
import rope.refactor.importutils as rope_importutils
from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.refactor.importutils.importinfo import (
    FromImport,
    ImportStatement,
    NormalImport,
)

from flext_cli import u
from flext_infra import (
    c,
    p,
    r,
    t,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesRopeImports:
    """Rope-backed import organization and rename helpers."""

    @staticmethod
    def import_statements(
        module_imports: t.Infra.RopeModuleImports,
    ) -> t.SequenceOf[t.Infra.RopeImportStatement]:
        """Return validated Rope import statements from one module import collection."""
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return ()
        return tuple(
            import_stmt
            for import_stmt in import_statements
            if isinstance(import_stmt, ImportStatement)
        )

    @staticmethod
    def import_statement_module_name(
        import_statement: t.Infra.RopeImportStatement,
    ) -> str | None:
        """Return the absolute module name represented by one Rope import statement."""
        import_info = import_statement.import_info
        if not isinstance(import_info, FromImport):
            return None
        module_name = import_info.module_name
        return module_name or None

    @staticmethod
    def import_statement_names_and_aliases(
        import_statement: t.Infra.RopeImportStatement,
    ) -> t.SequenceOf[tuple[str, str | None]]:
        """Return validated imported-name pairs from one Rope import statement."""
        import_info = import_statement.import_info
        if not isinstance(import_info, FromImport | NormalImport):
            return ()
        return tuple(import_info.names_and_aliases)

    @classmethod
    def imported_module_paths(
        cls,
        module_imports: t.Infra.RopeModuleImports,
    ) -> t.StrSequence:
        """Return runtime import targets represented by a Rope module import set."""
        imported_paths: list[str] = []
        for import_statement in cls.import_statements(module_imports):
            module_name = cls.import_statement_module_name(import_statement)
            names_and_aliases = cls.import_statement_names_and_aliases(import_statement)
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
        """Find all occurrences of the symbol at offset across the project."""
        try:
            return list(
                rope_findit.find_occurrences(
                    rope_project,
                    resource,
                    offset,
                    resources=resources,
                    in_hierarchy=in_hierarchy,
                )
            )
        except (
            RefactoringError,
            ResourceNotFoundError,
            AttributeError,
            TypeError,
            RecursionError,
        ) as exc:
            msg = (
                "rope find_occurrences failed for "
                f"{resource.path}@{offset}: {type(exc).__name__}: {exc!s}"
            )
            raise RuntimeError(msg) from exc

    @staticmethod
    def location_file_path(location: t.Infra.RopeLocation) -> Path | None:
        """Resolve one Rope occurrence back to an absolute file path."""
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
        rope_workspace: p.AttributeProbe,
        *,
        resource: t.Infra.RopeResource,
        name: str,
        definition_path: Path,
        dependent_import_targets: t.StrSequence = (),
    ) -> tuple[t.Infra.RopeResource, ...] | None:
        """Build the minimal Rope resource set for semantic occurrence searches.

        The workspace name index already narrows the candidate module set to
        files that contain ``name`` textually. This helper converts that cheap
        index into concrete Rope resources so callers can still rely on Rope's
        semantic identity checks without scanning the full project.
        """
        name_index_getter = getattr(rope_workspace, "name_index", None)
        resource_getter = getattr(rope_workspace, "resource", None)
        if name_index_getter is None or resource_getter is None:
            return None
        occurrences = name_index_getter().get(name, ())
        resolved_definition = definition_path.resolve()
        dependent_paths: frozenset[str] | None = None
        import_dependents_getter = getattr(rope_workspace, "import_dependents", None)
        if dependent_import_targets and callable(import_dependents_getter):
            dependent_candidates: set[Path] = {resolved_definition}
            for import_target in dependent_import_targets:
                dependent_paths_raw = import_dependents_getter(import_target)
                if not isinstance(dependent_paths_raw, tuple):
                    msg = (
                        "rope import_dependents returned non-tuple for "
                        f"{import_target}: {type(dependent_paths_raw).__name__}"
                    )
                    raise TypeError(msg)
                for path in dependent_paths_raw:
                    if not isinstance(path, Path):
                        msg = (
                            "rope import_dependents returned invalid path for "
                            f"{import_target}: {type(path).__name__}"
                        )
                        raise TypeError(msg)
                    dependent_candidates.add(path.resolve())
            dependent_paths = frozenset(str(path) for path in dependent_candidates)
        seen_paths = {str(resolved_definition)}
        resources: list[t.Infra.RopeResource] = [resource]
        for path, _surface, _lines in occurrences:
            resolved_path = path.resolve()
            if resolved_path == resolved_definition or path.name == c.Infra.INIT_PY:
                continue
            cache_key = str(resolved_path)
            if dependent_paths is not None and cache_key not in dependent_paths:
                continue
            if cache_key in seen_paths:
                continue
            candidate_resource = resource_getter(resolved_path)
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
        resource: t.Infra.RopeResource,
        *,
        apply: bool,
    ) -> p.Result[bool]:
        """Organize imports for one rope resource using rope's import engine.

        ``r.ok(True)`` when rope produced a non-empty change set; the
        change is applied when ``apply`` is set. ``r.ok(False)`` when
        rope produced no changes (already organised). ``r.fail(reason)``
        when rope raised a refactoring/resource/type error.
        """
        try:
            original_source = resource.read()
            organizer = rope_importutils.ImportOrganizer(rope_project)
            changes = organizer.organize_imports(resource)
        except (
            ModuleSyntaxError,
            SyntaxError,
            RefactoringError,
            ResourceNotFoundError,
            AttributeError,
            TypeError,
        ) as exc:
            return r[bool].fail(f"rope organize_imports raised: {exc!s}")
        if changes is None:
            return r[bool].ok(False)
        change_list_raw = getattr(changes, "changes", None)
        if not isinstance(change_list_raw, list):
            return r[bool].fail(
                "unexpected rope organize_imports result type: "
                f"{type(changes).__name__}"
            )
        change_list = tuple(change_list_raw)
        if not change_list:
            return r[bool].ok(False)
        changed = any(
            getattr(change, "new_contents", None) is not None
            and getattr(change, "new_contents", None) != original_source
            for change in change_list
        )
        if changed and apply:
            rope_project.do(changes)
        return r[bool].ok(changed)

    @classmethod
    def normalize_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        *,
        file_paths: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Apply one centralized Rope+Ruff import cleanup for touched files.

        Runs Rope's import organizer per file first, then lets Ruff remove
        orphaned imports and normalize import ordering/formatting once across the
        touched path set. Returns whether Rope reported any import rewrite.
        """
        existing_paths = tuple(path.resolve() for path in file_paths if path.is_file())
        if not existing_paths:
            return r[bool].ok(False)
        rope_changed = False
        for file_path in existing_paths:
            resource = FlextInfraUtilitiesRopeCore.get_resource_from_path(
                rope_project,
                file_path,
            )
            if resource is None:
                continue
            organize_result = cls.organize_imports(
                rope_project,
                resource,
                apply=True,
            )
            if organize_result.failure:
                return r[bool].fail(
                    organize_result.error or "rope organize_imports failed"
                )
            rope_changed = rope_changed or organize_result.unwrap_or(False)
        normalized_paths = tuple(str(path) for path in existing_paths)
        check_result = u.Cli.run_raw(
            ["ruff", "check", "--fix", "--select", "I,F401", *normalized_paths],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if check_result.failure:
            return r[bool].fail(check_result.error or "ruff check --fix failed")
        format_result = u.Cli.run_raw(
            ["ruff", "format", *normalized_paths],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if format_result.failure:
            return r[bool].fail(format_result.error or "ruff format failed")
        return r[bool].ok(rope_changed)

    @staticmethod
    def get_absolute_from_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.SequenceOf[t.Infra.RopeFromImport]:
        """Return all absolute ``from x import ...`` descriptors in a module."""
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return ()
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return ()
        return tuple(
            import_stmt.import_info
            for import_stmt in import_statements
            if isinstance(import_stmt.import_info, FromImport)
            and import_stmt.import_info.level == 0
        )

    @classmethod
    def relocate_from_import_aliases(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        source_module: str,
        target_module: str,
        aliases: t.StrSequence,
        apply: bool,
    ) -> str | None:
        """Move unaliased names from one absolute import to another using Rope."""
        aliases_to_move = frozenset(aliases)
        if not aliases_to_move:
            return None
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        original_source: str = resource.read()
        target_import_stmt, moved_aliases = cls._strip_aliases_from_source_imports(
            module_imports,
            source_module=source_module,
            target_module=target_module,
            aliases_to_move=aliases_to_move,
        )
        if not moved_aliases:
            return None
        merged_target_pairs = cls._merge_aliases_into_target(
            module_imports,
            target_import_stmt=target_import_stmt,
            target_module=target_module,
            moved_aliases=moved_aliases,
        )
        updated_source: str = module_imports.get_changed_source()
        if merged_target_pairs and cls._uses_parenthesized_from_import(
            source=original_source,
            module_name=target_module,
        ):
            updated_source = cls._format_parenthesized_from_import(
                source=updated_source,
                module_name=target_module,
                names_and_aliases=merged_target_pairs,
            )
        if updated_source == original_source:
            return None
        if apply:
            resource.write(updated_source)
        return updated_source

    @staticmethod
    def _strip_aliases_from_source_imports(
        module_imports: t.Infra.RopeModuleImports,
        *,
        source_module: str,
        target_module: str,
        aliases_to_move: frozenset[str],
    ) -> tuple[t.Infra.RopeImportStatement | None, t.Infra.StrSet]:
        """Remove ``aliases_to_move`` from each ``from source_module`` statement.

        Returns ``(target_import_stmt_or_None, moved_aliases_set)``. Mutates
        the source-module statements in place via ``import_info`` reassignment;
        the caller still owns the merge into the target.
        """
        target_import_stmt: t.Infra.RopeImportStatement | None = None
        moved_aliases: t.Infra.StrSet = set()
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return target_import_stmt, moved_aliases
        for import_stmt in import_statements:
            import_info = import_stmt.import_info
            if not (isinstance(import_info, FromImport) and import_info.level == 0):
                continue
            if import_info.module_name == target_module:
                target_import_stmt = import_stmt
            if import_info.module_name != source_module:
                continue
            kept_pairs: list[tuple[str, str | None]] = []
            for name, alias in import_info.names_and_aliases:
                if alias is None and name in aliases_to_move:
                    moved_aliases.add(name)
                    continue
                kept_pairs.append((name, alias))
            if len(kept_pairs) == len(import_info.names_and_aliases):
                continue
            import_stmt.import_info = FromImport(source_module, 0, kept_pairs)
        return target_import_stmt, moved_aliases

    @staticmethod
    def _merge_aliases_into_target(
        module_imports: t.Infra.RopeModuleImports,
        *,
        target_import_stmt: t.Infra.RopeImportStatement | None,
        target_module: str,
        moved_aliases: t.Infra.StrSet,
    ) -> t.SequenceOf[tuple[str, str | None]]:
        """Merge ``moved_aliases`` into the target import; create one if missing."""
        sorted_moved = sorted(moved_aliases)
        if target_import_stmt is None:
            module_imports.add_import(
                FromImport(target_module, 0, [(name, None) for name in sorted_moved]),
            )
            module_imports.sort_imports()
            return tuple((name, None) for name in sorted_moved)
        import_info = target_import_stmt.import_info
        if not (
            isinstance(import_info, FromImport)
            and import_info.level == 0
            and import_info.module_name == target_module
        ):
            msg = (
                "rope target import mismatch for "
                f"{target_module}: {type(import_info).__name__}"
            )
            raise RuntimeError(msg)
        merged_pairs = list(import_info.names_and_aliases)
        existing_plain_names = {name for name, alias in merged_pairs if alias is None}
        merged_pairs.extend(
            (name, None) for name in sorted_moved if name not in existing_plain_names
        )
        target_import_stmt.import_info = FromImport(
            target_module,
            0,
            list(merged_pairs),
        )
        return tuple(merged_pairs)

    @staticmethod
    def _uses_parenthesized_from_import(*, source: str, module_name: str) -> bool:
        """Uses parenthesized from import."""
        pattern = c.Infra.compile_from_module_paren_open(module_name)
        return any(pattern.match(line) for line in source.splitlines())

    @staticmethod
    def _format_parenthesized_from_import(
        *,
        source: str,
        module_name: str,
        names_and_aliases: t.SequenceOf[tuple[str, str | None]],
    ) -> str:
        """Format parenthesized from import."""
        entries = [
            (f"{name} as {alias}" if alias else name)
            for name, alias in names_and_aliases
        ]
        replacement = "\n".join([
            f"from {module_name} import (",
            *[f"    {entry}," for entry in entries],
            ")",
        ])
        pattern = c.Infra.compile_from_module_import_line(module_name)
        rewritten_source: str = pattern.sub(replacement, source, count=1)
        if rewritten_source == source:
            return source
        return rewritten_source

    @classmethod
    def collapse_submodule_alias_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        package_name: str,
        aliases: t.StrSequence | None = None,
        apply: bool,
    ) -> str | None:
        """Hoist ``from package.sub import alias`` into ``from package import alias``."""
        effective_aliases = aliases or tuple(
            u.read_project_constants("flext-infra").RUNTIME_ALIAS_NAMES
        )
        requested_aliases = frozenset(
            alias for alias in effective_aliases if len(alias) == 1 and alias.islower()
        )
        result: str | None = None
        if requested_aliases:
            module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
                rope_project,
                resource,
            )
            if module_imports is not None:
                moved_aliases: t.Infra.StrSet = set()
                package_prefix = f"{package_name}."
                import_statements = module_imports.imports
                if isinstance(import_statements, list):
                    for import_stmt in import_statements:
                        import_info = import_stmt.import_info
                        from_import = (
                            import_info
                            if isinstance(import_info, FromImport)
                            and import_info.level == 0
                            else None
                        )
                        if (
                            from_import is None
                            or not from_import.module_name.startswith(package_prefix)
                        ):
                            continue
                        kept_pairs: list[tuple[str, str | None]] = []
                        for name, alias in from_import.names_and_aliases:
                            if alias is None and name in requested_aliases:
                                moved_aliases.add(name)
                                continue
                            kept_pairs.append((name, alias))
                        if len(kept_pairs) == len(from_import.names_and_aliases):
                            continue
                        import_stmt.import_info = FromImport(
                            from_import.module_name,
                            0,
                            kept_pairs,
                        )
                    if moved_aliases:
                        module_imports.add_import(
                            FromImport(
                                package_name,
                                0,
                                [(name, None) for name in sorted(moved_aliases)],
                            )
                        )
                        module_imports.remove_duplicates()
                        module_imports.sort_imports()
                        updated_source: str = module_imports.get_changed_source()
                        if updated_source != resource.read():
                            if apply:
                                resource.write(updated_source)
                            result = updated_source
        return result

    @staticmethod
    def add_import(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        from_module: str,
        names: t.StrSequence,
        *,
        apply: bool = True,
    ) -> str | None:
        """Add ``from <module> import <names>`` using rope's ImportOrganizer."""
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        module_imports.add_import(
            FromImport(from_module, 0, [(name, None) for name in sorted(names)])
        )
        module_imports.remove_duplicates()
        module_imports.sort_imports()
        updated: str = module_imports.get_changed_source()
        if updated == resource.read():
            return None
        if apply:
            resource.write(updated)
        return updated

    @staticmethod
    def remove_import_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        from_module: str,
        names: t.StrSequence,
        *,
        apply: bool = True,
    ) -> str | None:
        """Remove specific names from ``from <module> import ...``."""
        names_to_remove = frozenset(names)
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        changed = False
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return None
        for import_stmt in import_statements:
            import_info = import_stmt.import_info
            from_import = (
                import_info
                if isinstance(import_info, FromImport)
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
                import_stmt.import_info = FromImport(from_module, 0, kept)
                changed = True
        if not changed:
            return None
        module_imports.remove_duplicates()
        module_imports.sort_imports()
        updated: str = module_imports.get_changed_source()
        if updated == resource.read():
            return None
        if apply:
            resource.write(updated)
        return updated


__all__: list[str] = ["FlextInfraUtilitiesRopeImports"]
