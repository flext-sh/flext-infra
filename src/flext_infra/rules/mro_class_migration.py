"""Rule that migrates module-level constants into constants facade classes."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    c,
    m,
    t,
    u,
)


class FlextInfraRefactorMROClassMigrationRule:
    """Apply MRO constants-class migration to a single module."""

    def apply(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> t.Infra.TransformResult:
        """Migrate module-level Final constants into the facade class."""
        root_real_path = getattr(
            getattr(rope_project, "root", None),
            "real_path",
            None,
        )
        project_root = Path(root_real_path) if isinstance(root_real_path, str) else None
        file_path = (
            project_root / resource.path
            if project_root is not None
            else Path(resource.real_path)
        )
        if file_path.name != c.Infra.Files.CONSTANTS_PY:
            return (resource.read(), [])
        source = resource.read()
        candidates = u.Infra.find_final_candidates(source)
        if not candidates:
            return (source, [])
        constants_class = u.Infra.first_constants_class_name(source)
        scan_result = m.Infra.MROScanReport(
            file=str(file_path),
            module="",
            constants_class=constants_class,
            candidates=tuple(candidates),
        )
        updated_source, migration, _ = u.Infra.migrate_file(
            scan_result=scan_result,
        )
        if not migration.moved_symbols or updated_source == source:
            return (source, [])
        if not dry_run:
            resource.write(updated_source)
        syms = ", ".join(migration.moved_symbols)
        return (updated_source, [f"migrated constants into facade class: {syms}"])


__all__ = ["FlextInfraRefactorMROClassMigrationRule"]
