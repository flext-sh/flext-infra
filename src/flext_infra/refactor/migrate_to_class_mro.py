"""Automated migration of loose constants/typings into MRO facade classes."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraRefactorMROImportRewriter,
    FlextInfraRefactorMROMigrationValidator,
    c,
    m,
    t,
    u,
)

_ROPE_MODULE_SYNTAX_ERROR = u.Infra.module_syntax_error_type()


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
        scan_results, files_scanned = u.Infra.scan_workspace(
            workspace_root=self._workspace_root,
            target=normalized_target,
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

    @classmethod
    def run_as_hook(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Execute MRO migration as a rope post-hook (implements p.Infra.RopePostHook)."""
        try:
            report = cls(workspace_root=path).run(target="all", apply=not dry_run)
        except (
            SyntaxError,
            _ROPE_MODULE_SYNTAX_ERROR,
            OSError,
            ValueError,
            KeyError,
            AttributeError,
        ):
            return []
        return cls._report_to_results(report=report, dry_run=dry_run)

    @staticmethod
    def _report_to_results(
        *,
        report: m.Infra.MROMigrationReport,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Convert MRO migration report into rope-compatible Result sequence."""
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

    @staticmethod
    def _normalize_target(*, target: str) -> str:
        value = FlextUtilities.norm_str(target, case="lower")
        if value in c.Infra.MRO_TARGETS:
            return value
        msg = f"unsupported target: {target}"
        raise ValueError(msg)


__all__ = ["FlextInfraRefactorMigrateToClassMRO"]
