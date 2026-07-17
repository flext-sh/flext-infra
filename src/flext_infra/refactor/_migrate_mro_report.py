"""MRO-migration reporting — extracted concern of FlextInfraRefactorMigrateToClassMRO.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

from flext_infra import m, p, t


class FlextInfraRefactorMigrateMroReportMixin:
    """Render + convert the MRO migration report into text / rope Results.

    Composed into FlextInfraRefactorMigrateToClassMRO via inheritance; both
    methods are pure (operate only on the passed report), so the facade keeps
    just the scan/transform/rewrite/validate orchestration.
    """

    @staticmethod
    def render_text(report: p.Infra.MROMigrationReport) -> str:
        """Render migration report in CLI-friendly plain text."""
        lines = [
            f"Workspace: {report.workspace}",
            f"Target: {report.target}",
            (
                "Projects: " + ", ".join(report.selected_projects)
                if report.selected_projects
                else "Projects: all"
            ),
            f"Mode: {('dry-run' if report.dry_run else 'apply')}",
            f"Validation mode: {report.validation_mode}",
            f"Files scanned: {report.files_scanned}",
            f"Files with candidates: {report.files_with_candidates}",
            f"Migrations: {len(report.migrations)}",
            f"Rewrites: {len(report.rewrites)}",
            f"Remaining violations: {report.remaining_violations}",
            f"MRO failures: {report.mro_failures}",
            f"Scan time: {report.scan_duration_seconds:.3f}s",
            f"Rewrite time: {report.rewrite_duration_seconds:.3f}s",
            f"Validation time: {report.validation_duration_seconds:.3f}s",
            f"Total time: {report.total_duration_seconds:.3f}s",
        ]
        if report.checkpoint_ref:
            lines.append(f"Rollback checkpoint: {report.checkpoint_ref}")
        if report.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in report.warnings)
        if report.errors:
            lines.append("Errors:")
            lines.extend(f"- {error}" for error in report.errors)
        return "\n".join(lines) + "\n"

    @staticmethod
    def _report_to_results(
        *, report: p.Infra.MROMigrationReport, dry_run: bool
    ) -> t.SequenceOf[p.Infra.Result]:
        """Convert MRO migration report into rope-compatible Result sequence."""
        per_file_changes: MutableMapping[Path, t.MutableSequenceOf[str]] = {}
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
                f"{action} {rewrite.replacements} consumer references after MRO migration"
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
                per_file_changes.items(), key=lambda item: str(item[0])
            )
        ]


__all__: list[str] = ["FlextInfraRefactorMigrateMroReportMixin"]
