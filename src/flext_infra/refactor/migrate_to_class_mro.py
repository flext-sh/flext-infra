"""Automated migration of loose constants/typings into MRO facade classes."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, t
from flext_infra.refactor._utilities_mro_scan import FlextInfraUtilitiesRefactorMroScan
from flext_infra.refactor.mro_import_rewriter import FlextInfraRefactorMROImportRewriter
from flext_infra.refactor.mro_migration_validator import (
    FlextInfraRefactorMROMigrationValidator,
)


class FlextInfraRefactorMigrateToClassMRO:
    """Orchestrate scan, migration, rewrite, and validation phases."""

    def __init__(self, *, workspace_root: Path) -> None:
        """Create migration service bound to a workspace root."""
        self._workspace_root = workspace_root.resolve()

    def run(
        self,
        *,
        target: str,
        apply: bool,
    ) -> m.Infra.MROMigrationReport:
        """Run scan, transform, rewrite, and validation phases."""
        normalized_target = self._normalize_target(target=target)
        scan_results, files_scanned = (
            FlextInfraUtilitiesRefactorMroScan.mro_scan_workspace(
                workspace_root=self._workspace_root,
                target=normalized_target,
            )
        )
        warnings: t.StrSequence = []
        stash_ref = ""
        migrations, rewrites, errors = (
            FlextInfraRefactorMROImportRewriter.migrate_workspace(
                workspace_root=self._workspace_root,
                scan_results=scan_results,
                apply=apply,
            )
        )
        remaining_violations, mro_failures = (
            FlextInfraRefactorMROMigrationValidator.validate(
                workspace_root=self._workspace_root,
                target=normalized_target,
            )
        )
        return m.Infra.MROMigrationReport(
            workspace=str(self._workspace_root),
            target=normalized_target,
            dry_run=not apply,
            files_scanned=files_scanned,
            files_with_candidates=len(scan_results),
            migrations=tuple(migrations),
            rewrites=tuple(rewrites),
            remaining_violations=remaining_violations,
            mro_failures=mro_failures,
            stash_ref=stash_ref,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    @staticmethod
    def render_text(report: m.Infra.MROMigrationReport) -> str:
        """Render migration report in CLI-friendly plain text."""
        lines = [
            f"Workspace: {report.workspace}",
            f"Target: {report.target}",
            f"Mode: {('dry-run' if report.dry_run else 'apply')}",
            f"Files scanned: {report.files_scanned}",
            f"Files with candidates: {report.files_with_candidates}",
            f"Migrations: {len(report.migrations)}",
            f"Rewrites: {len(report.rewrites)}",
            f"Remaining violations: {report.remaining_violations}",
            f"MRO failures: {report.mro_failures}",
        ]
        if report.stash_ref:
            lines.append(f"Rollback stash: {report.stash_ref}")
        if report.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in report.warnings)
        if report.errors:
            lines.append("Errors:")
            lines.extend(f"- {error}" for error in report.errors)
        return "\n".join(lines) + "\n"

    @staticmethod
    def _normalize_target(*, target: str) -> str:
        value = target.strip().lower()
        if value in c.Infra.MRO_TARGETS:
            return value
        msg = f"unsupported target: {target}"
        raise ValueError(msg)


__all__ = ["FlextInfraRefactorMigrateToClassMRO"]
