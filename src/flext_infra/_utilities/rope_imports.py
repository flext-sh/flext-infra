"""Rope-backed import and rename operations."""

from __future__ import annotations

import re
from collections.abc import Sequence

import rope.contrib.findit as rope_findit
import rope.refactor.importutils as rope_importutils
from rope.base.change import ChangeSet
from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.refactor.importutils.importinfo import FromImport

from flext_infra import (
    FlextInfraUtilitiesRopeCore,
    c,
    t,
)


class FlextInfraUtilitiesRopeImports:
    """Rope-backed import organization and rename helpers."""

    @staticmethod
    def find_occurrences(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        *,
        in_hierarchy: bool = False,
    ) -> Sequence[t.Infra.RopeLocation]:
        """Find all occurrences of the symbol at offset across the project."""
        try:
            return list(
                rope_findit.find_occurrences(
                    rope_project,
                    resource,
                    offset,
                    in_hierarchy=in_hierarchy,
                )
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError, TypeError):
            return ()

    @staticmethod
    def organize_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool,
    ) -> bool:
        """Organize imports for one rope resource using rope's import engine."""
        try:
            original_source = resource.read()
            organizer = rope_importutils.ImportOrganizer(rope_project)
            changes = organizer.organize_imports(resource)
        except (RefactoringError, ResourceNotFoundError, AttributeError, TypeError):
            return False
        if not isinstance(changes, ChangeSet):
            return False
        change_list = tuple(changes.changes)
        if not change_list:
            return False
        changed = any(
            change.new_contents is not None and change.new_contents != original_source
            for change in change_list
        )
        if changed and apply:
            rope_project.do(changes)
        return changed

    def get_absolute_from_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[t.Infra.RopeFromImport]:
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

    @staticmethod
    def relocate_from_import_aliases(
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
        original_source = resource.read()
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        moved_aliases: t.Infra.StrSet = set()
        target_import_stmt: t.Infra.RopeImportStatement | None = None
        merged_target_pairs: Sequence[tuple[str, str | None]] = ()
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return None
        for import_stmt in import_statements:
            import_info = import_stmt.import_info
            target_from_import = (
                import_info
                if isinstance(import_info, FromImport)
                and import_info.level == 0
                and import_info.module_name == target_module
                else None
            )
            if target_from_import is not None:
                target_import_stmt = import_stmt
            from_import = (
                import_info
                if isinstance(import_info, FromImport)
                and import_info.level == 0
                and import_info.module_name == source_module
                else None
            )
            if from_import is None:
                continue
            kept_pairs: list[tuple[str, str | None]] = []
            for name, alias in from_import.names_and_aliases:
                if alias is None and name in aliases_to_move:
                    moved_aliases.add(name)
                    continue
                kept_pairs.append((name, alias))
            if len(kept_pairs) == len(from_import.names_and_aliases):
                continue
            import_stmt.import_info = FromImport(source_module, 0, kept_pairs)
        if not moved_aliases:
            return None
        if target_import_stmt is not None:
            import_info = target_import_stmt.import_info
            if (
                isinstance(import_info, FromImport)
                and import_info.level == 0
                and import_info.module_name == target_module
            ):
                merged_pairs = list(import_info.names_and_aliases)
                existing_plain_names = {
                    name for name, alias in merged_pairs if alias is None
                }
                merged_pairs.extend(
                    (name, None)
                    for name in sorted(moved_aliases)
                    if name not in existing_plain_names
                )
                merged_target_pairs = tuple(merged_pairs)
                target_import_stmt.import_info = FromImport(
                    target_module,
                    0,
                    list(merged_target_pairs),
                )
        else:
            module_imports.add_import(
                FromImport(
                    target_module,
                    0,
                    [(name, None) for name in sorted(moved_aliases)],
                )
            )
            module_imports.sort_imports()
            merged_target_pairs = tuple((name, None) for name in sorted(moved_aliases))
        updated_source = module_imports.get_changed_source()
        if (
            merged_target_pairs
            and FlextInfraUtilitiesRopeImports._uses_parenthesized_from_import(
                source=original_source,
                module_name=target_module,
            )
        ):
            updated_source = (
                FlextInfraUtilitiesRopeImports._format_parenthesized_from_import(
                    source=updated_source,
                    module_name=target_module,
                    names_and_aliases=merged_target_pairs,
                )
            )
        if updated_source == original_source:
            return None
        if apply:
            resource.write(updated_source)
        return updated_source

    @staticmethod
    def _uses_parenthesized_from_import(*, source: str, module_name: str) -> bool:
        pattern = re.compile(rf"^from\s+{re.escape(module_name)}\s+import\s+\(")
        return any(pattern.match(line) for line in source.splitlines())

    @staticmethod
    def _format_parenthesized_from_import(
        *,
        source: str,
        module_name: str,
        names_and_aliases: Sequence[tuple[str, str | None]],
    ) -> str:
        entries = [
            (f"{name} as {alias}" if alias else name)
            for name, alias in names_and_aliases
        ]
        replacement = "\n".join([
            f"from {module_name} import (",
            *[f"    {entry}," for entry in entries],
            ")",
        ])
        pattern = re.compile(
            rf"^from\s+{re.escape(module_name)}\s+import\s+.+$",
            re.MULTILINE,
        )
        return pattern.sub(replacement, source, count=1)

    @classmethod
    def collapse_submodule_alias_imports(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        package_name: str,
        aliases: t.StrSequence = tuple(c.Infra.RUNTIME_ALIAS_NAMES),
        apply: bool,
    ) -> str | None:
        """Hoist ``from package.sub import alias`` into ``from package import alias``."""
        requested_aliases = frozenset(
            alias for alias in aliases if len(alias) == 1 and alias.islower()
        )
        if not requested_aliases:
            return None
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        moved_aliases: t.Infra.StrSet = set()
        package_prefix = f"{package_name}."
        import_statements = module_imports.imports
        if not isinstance(import_statements, list):
            return None
        for import_stmt in import_statements:
            import_info = import_stmt.import_info
            from_import = (
                import_info
                if isinstance(import_info, FromImport) and import_info.level == 0
                else None
            )
            if from_import is None or not from_import.module_name.startswith(
                package_prefix
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
        if not moved_aliases:
            return None
        module_imports.add_import(
            FromImport(
                package_name,
                0,
                [(name, None) for name in sorted(moved_aliases)],
            )
        )
        module_imports.remove_duplicates()
        module_imports.sort_imports()
        updated_source = module_imports.get_changed_source()
        if updated_source == resource.read():
            return None
        if apply:
            resource.write(updated_source)
        return updated_source

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
        updated = module_imports.get_changed_source()
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
        updated = module_imports.get_changed_source()
        if updated == resource.read():
            return None
        if apply:
            resource.write(updated)
        return updated


__all__: list[str] = ["FlextInfraUtilitiesRopeImports"]
