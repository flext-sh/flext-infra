# pyright: reportMissingTypeStubs=false
"""Rope-backed import and rename operations."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.contrib.findit import find_occurrences
from rope.refactor.importutils import ImportOrganizer
from rope.refactor.importutils.importinfo import FromImport
from rope.refactor.rename import Rename

from flext_infra import c, p, t
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesRopeImports(FlextInfraUtilitiesRopeCore):
    """Rope-backed import organization and rename helpers."""

    @staticmethod
    def rename_symbol_workspace(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        new_name: str,
        *,
        apply: bool,
    ) -> t.StrSequence:
        """Rename symbol at offset across the whole project."""
        changed_files: t.MutableIntMapping = {}
        try:
            changes = Rename(rope_project, resource, offset).get_changes(new_name)
        except RefactoringError:
            return []
        for change in changes.changes:
            changed_files[change.resource.path] = 1
        if apply:
            rope_project.do(changes)
        return list(changed_files)

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
                find_occurrences(
                    rope_project,
                    resource,
                    offset,
                    in_hierarchy=in_hierarchy,
                )
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return []

    @staticmethod
    def organize_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool,
    ) -> bool:
        """Organize imports for one rope resource using rope's import engine."""
        original_source = resource.read()
        try:
            organizer = ImportOrganizer(rope_project)
            changes = organizer.organize_imports(resource)
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return False
        if not isinstance(changes, p.Infra.RopeChangesLike):
            return False
        changed = any(
            change.new_contents is not None and change.new_contents != original_source
            for change in changes.changes
        )
        if changed and apply:
            rope_project.do(changes)
        return changed

    @staticmethod
    def get_plain_from_imported_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        module_name: str,
    ) -> t.Infra.StrSet:
        """Return unaliased names imported from one absolute `from x import ...`."""
        imported: t.Infra.StrSet = set()
        module_imports = FlextInfraUtilitiesRopeImports._get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return imported
        for import_stmt in module_imports.imports:
            from_import = FlextInfraUtilitiesRopeImports._absolute_from_import(
                import_stmt.import_info,
                module_name=module_name,
            )
            if from_import is None:
                continue
            for name, alias in from_import.names_and_aliases:
                if alias is None:
                    imported.add(name)
        return imported

    @staticmethod
    def get_absolute_from_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[p.Infra.RopeFromImportLike]:
        """Return all absolute ``from x import ...`` descriptors in a module."""
        module_imports = FlextInfraUtilitiesRopeImports._get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return ()
        return tuple(
            from_import
            for import_stmt in module_imports.imports
            if (
                from_import := FlextInfraUtilitiesRopeImports._absolute_from_import_any(
                    import_stmt.import_info
                )
            )
            is not None
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
        module_imports = FlextInfraUtilitiesRopeImports._get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        moved_aliases: t.Infra.StrSet = set()
        for import_stmt in module_imports.imports:
            from_import = FlextInfraUtilitiesRopeImports._absolute_from_import(
                import_stmt.import_info,
                module_name=source_module,
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
        module_imports.add_import(
            FromImport(
                target_module,
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
            FlextInfraUtilitiesRopeImports.apply_source_change(
                rope_project,
                resource,
                updated_source,
                description=f"relocate import aliases in <{resource.path}>",
            )
        return updated_source

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
        module_imports = cls._get_module_imports(rope_project, resource)
        if module_imports is None:
            return None
        moved_aliases: t.Infra.StrSet = set()
        package_prefix = f"{package_name}."
        for import_stmt in module_imports.imports:
            from_import = cls._absolute_from_import_any(import_stmt.import_info)
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
            FlextInfraUtilitiesRopeImports.apply_source_change(
                rope_project,
                resource,
                updated_source,
                description=f"collapse import aliases in <{resource.path}>",
            )
        return updated_source

    @classmethod
    def organize_imports_for_path(
        cls,
        workspace_root: Path,
        file_path: Path,
        *,
        apply: bool,
    ) -> bool:
        """Organize imports for one file path using a temporary rope project."""
        rope_project = cls.init_rope_project(workspace_root.resolve())
        try:
            resource = cls.get_resource_from_path(rope_project, file_path.resolve())
            if resource is None:
                return False
            return cls.organize_imports(rope_project, resource, apply=apply)
        finally:
            rope_project.close()

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
        module_imports = FlextInfraUtilitiesRopeImports._get_module_imports(
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
            FlextInfraUtilitiesRopeImports.apply_source_change(
                rope_project,
                resource,
                updated,
                description=f"add import from {from_module} in <{resource.path}>",
            )
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
        module_imports = FlextInfraUtilitiesRopeImports._get_module_imports(
            rope_project,
            resource,
        )
        if module_imports is None:
            return None
        changed = False
        for import_stmt in module_imports.imports:
            from_import = FlextInfraUtilitiesRopeImports._absolute_from_import(
                import_stmt.import_info,
                module_name=from_module,
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
            FlextInfraUtilitiesRopeImports.apply_source_change(
                rope_project,
                resource,
                updated,
                description=f"remove imports in <{resource.path}>",
            )
        return updated

    @staticmethod
    def ensure_future_annotations(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool = True,
    ) -> bool:
        """Ensure ``from __future__ import annotations`` is present."""
        source = resource.read()
        if c.Infra.SourceCode.FUTURE_ANNOTATIONS in source:
            return False
        lines = source.splitlines(keepends=True)
        insert_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("#", '"""', "'''")) or not stripped:
                insert_idx = i + 1
                continue
            if stripped.startswith(("from __future__", "import __future__")):
                return False
            break
        lines.insert(insert_idx, "from __future__ import annotations\n")
        new_source = "".join(lines)
        if apply:
            FlextInfraUtilitiesRopeImports.apply_source_change(
                rope_project,
                resource,
                new_source,
                description=f"add future annotations in <{resource.path}>",
            )
        return True


__all__ = ["FlextInfraUtilitiesRopeImports"]
