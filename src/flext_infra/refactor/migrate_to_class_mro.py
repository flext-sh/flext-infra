"""Automated migration of loose constants/typings into MRO facade classes."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from time import perf_counter
from typing import ClassVar

from flext_cli import cli

from flext_infra import (
    FlextInfraRefactorMROImportRewriter,
    FlextInfraRefactorMROMigrationValidator,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraRefactorMigrateToClassMRO:
    """Orchestrate scan, migration, rewrite, and validation phases."""

    _DEFAULT_TARGET: ClassVar[str] = "all"

    def __init__(self, *, workspace_root: Path) -> None:
        """Create migration service bound to a workspace root."""
        self._workspace_root = workspace_root.resolve()

    def run(
        self,
        *,
        target: str,
        apply: bool,
        project_names: t.StrSequence | None = None,
    ) -> m.Infra.MROMigrationReport:
        """Run scan, transform, rewrite, and validation phases."""
        start_time = perf_counter()
        normalized_target = self._normalize_target(target=target)
        selected_projects = tuple(sorted(set(project_names or ())))
        scan_start = perf_counter()
        scan_results, files_scanned = u.Infra.scan_workspace(
            workspace_root=self._workspace_root,
            target=normalized_target,
            project_names=project_names,
        )
        scan_duration = perf_counter() - scan_start
        warnings: list[str] = []
        stash_ref = ""
        rewrite_start = perf_counter()
        migrations, rewrites, errors = (
            FlextInfraRefactorMROImportRewriter.migrate_workspace(
                workspace_root=self._workspace_root,
                scan_results=scan_results,
                apply=apply,
                project_names=project_names,
            )
        )
        rewrite_duration = perf_counter() - rewrite_start
        validation_start = perf_counter()
        if apply:
            remaining_violations, mro_failures = (
                FlextInfraRefactorMROMigrationValidator.validate(
                    workspace_root=self._workspace_root,
                    target=normalized_target,
                    project_names=project_names,
                )
            )
            validation_mode = "post-apply-rescan"
        else:
            remaining_violations = sum(
                len(scan_result.candidates) for scan_result in scan_results
            )
            mro_failures = 0
            validation_mode = "dry-run-estimate"
            warnings.append(
                "Dry-run skips post-apply rescan; remaining violations reflect the current candidate snapshot.",
            )
        validation_duration = perf_counter() - validation_start
        total_duration = perf_counter() - start_time
        return m.Infra.MROMigrationReport(
            workspace=str(self._workspace_root),
            target=normalized_target,
            selected_projects=selected_projects,
            dry_run=not apply,
            validation_mode=validation_mode,
            files_scanned=files_scanned,
            files_with_candidates=len(scan_results),
            migrations=tuple(migrations),
            rewrites=tuple(rewrites),
            remaining_violations=remaining_violations,
            mro_failures=mro_failures,
            stash_ref=stash_ref,
            scan_duration_seconds=scan_duration,
            rewrite_duration_seconds=rewrite_duration,
            validation_duration_seconds=validation_duration,
            total_duration_seconds=total_duration,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    @classmethod
    def execute_command(
        cls,
        params: m.Infra.RefactorMigrateMroInput,
    ) -> p.Result[m.Infra.MROMigrationReport]:
        """Execute MRO migration directly from the canonical refactor payload."""
        report = cls(workspace_root=params.workspace_path).run(
            target=params.target or cls._DEFAULT_TARGET,
            apply=params.apply,
            project_names=params.project_names,
        )
        cli.display_text(cls.render_text(report))
        if report.errors:
            return r[m.Infra.MROMigrationReport].fail("MRO migration had errors")
        return r[m.Infra.MROMigrationReport].ok(report)

    @staticmethod
    def render_text(report: m.Infra.MROMigrationReport) -> str:
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
            *u.Infra.SYNTAX_ERRORS,
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
        value = u.norm_str(target, case="lower")
        if value in c.Infra.MRO_TARGETS:
            return value
        msg = f"unsupported target: {target}"
        raise ValueError(msg)


__all__: list[str] = ["FlextInfraRefactorMigrateToClassMRO"]

u.Infra.register_rope_post_hook(
    FlextInfraRefactorMigrateToClassMRO.run_as_hook,
)
