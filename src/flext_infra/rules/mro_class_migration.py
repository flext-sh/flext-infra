"""Rule that migrates module-level constants into constants facade classes."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesRope,
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
    ) -> tuple[str, t.StrSequence]:
        """Migrate module-level Final constants into the facade class."""
        file_path = Path(rope_project.root.real_path) / resource.path
        if file_path.name != c.Infra.CONSTANTS_FILE_GLOB:
            return (FlextInfraUtilitiesRope.read_source(resource), [])
        source = FlextInfraUtilitiesRope.read_source(resource)
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
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                updated_source,
                description="MRO constants migration",
            )
        syms = ", ".join(migration.moved_symbols)
        return (updated_source, [f"migrated constants into facade class: {syms}"])


__all__ = ["FlextInfraRefactorMROClassMigrationRule"]
