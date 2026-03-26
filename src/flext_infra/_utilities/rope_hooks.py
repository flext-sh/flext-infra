"""Rope post-processing hooks — isolated to break circular imports.

This module exists because ``rope.py`` → ``migrate_to_class_mro`` → ``flext_infra``
→ ``utilities.py`` → ``FlextInfraUtilitiesRope`` (rope.py) creates a cycle.
By placing the MRO migration hook here, ``rope.py`` can reference it without
importing the cycle-inducing dependency at its own module scope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import m


def run_mro_migration_hook(
    path: Path,
    *,
    dry_run: bool,
) -> Sequence[m.Infra.Result]:
    """Run the centralized MRO migration service as a semantic post-pass."""
    from flext_infra.refactor.migrate_to_class_mro import (
        FlextInfraRefactorMigrateToClassMRO,
    )

    report = FlextInfraRefactorMigrateToClassMRO(workspace_root=path).run(
        target="all",
        apply=not dry_run,
    )
    return _mro_report_to_results(path=path, report=report, dry_run=dry_run)


def _mro_report_to_results(
    *,
    path: Path,
    report: m.Infra.MROMigrationReport,
    dry_run: bool,
) -> Sequence[m.Infra.Result]:
    """Convert MRO migration report into rope-compatible Result sequence."""
    _ = path  # used for context only; results carry per-file paths
    per_file_changes: MutableMapping[Path, MutableSequence[str]] = {}
    for migration in report.migrations:
        file_path = Path(migration.file)
        changes = per_file_changes.setdefault(file_path, [])
        changes.extend([
            ("planned MRO migration" if dry_run else "applied MRO migration")
            + f": {symbol}"
            for symbol in migration.moved_symbols
        ])
    for rewrite in report.rewrites:
        file_path = Path(rewrite.file)
        changes = per_file_changes.setdefault(file_path, [])
        action = "planned" if dry_run else "rewrote"
        changes.append(
            f"{action} {rewrite.replacements} consumer references after MRO migration",
        )
    return [
        m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=(not dry_run),
            error=None,
            changes=list(changes),
            refactored_code=None,
        )
        for file_path, changes in sorted(
            per_file_changes.items(),
            key=lambda item: str(item[0]),
        )
    ]


__all__: list[str] = ["run_mro_migration_hook"]
