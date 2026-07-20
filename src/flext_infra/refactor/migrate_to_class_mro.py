"""Automated migration of loose constants/typings into MRO facade classes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli
from flext_core import r, u
from flext_infra import c, m, p, t
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._utilities.mro_scan import FlextInfraUtilitiesRefactorMroScan
from flext_infra.refactor._migrate_mro_report import (
    FlextInfraRefactorMigrateMroReportMixin,
)
from flext_infra.refactor.mro_import_rewriter import FlextInfraRefactorMROImportRewriter
from flext_infra.refactor.mro_migration_validator import (
    FlextInfraRefactorMROMigrationValidator,
)
from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraRefactorMigrateToClassMRO(FlextInfraRefactorMigrateMroReportMixin):
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
        gates: t.StrSequence | None = None,
    ) -> m.Infra.MROMigrationReport:
        """Run scan, transform, rewrite, and validation phases."""
        start_time = perf_counter()
        normalized_target = self._normalize_target(target=target)
        selected_projects = tuple(sorted(set(project_names or ())))
        scan_start = perf_counter()
        scan_results, files_scanned = FlextInfraUtilitiesRefactorMroScan.scan_workspace(
            workspace_root=self._workspace_root,
            target=normalized_target,
            project_names=project_names,
        )
        scan_duration = perf_counter() - scan_start
        warnings: list[str] = []
        checkpoint_ref = ""
        safety_manager: FlextInfraRefactorSafetyManager | None = None
        if apply:
            safety_manager = FlextInfraRefactorSafetyManager()
            checkpoint_outcome = safety_manager.create_pre_transformation_checkpoint(
                self._workspace_root, label="flext-infra-refactor-migrate-to-class-mro"
            )
            if checkpoint_outcome.failure:
                warnings.append(
                    f"Pre-transformation checkpoint failed: {checkpoint_outcome.error}"
                )
            else:
                checkpoint_ref = checkpoint_outcome.value
        rewrite_start = perf_counter()
        migrations, rewrites, errors = (
            FlextInfraRefactorMROImportRewriter.migrate_workspace(
                workspace_root=self._workspace_root,
                scan_results=scan_results,
                apply=apply,
                project_names=project_names,
                gates=gates,
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
            # Never roll back the whole workspace on a partial failure: each
            # file write is already lint-gated per file (green files committed,
            # failing files skipped). A global rollback would discard every
            # converged file whenever a single unrelated file failed lint,
            # leaving the census unchanged and the run non-idempotent. Keep the
            # green writes and only surface the failures as warnings/errors.
            if safety_manager is not None:
                if errors or mro_failures:
                    warnings.append(
                        "Partial failures left in place (fix-forward): "
                        f"{len(errors)} error(s), {mro_failures} mro failure(s); "
                        "converged files were kept, not rolled back."
                    )
                clear_outcome = safety_manager.clear_checkpoint()
                if clear_outcome.failure:
                    warnings.append(f"Checkpoint cleanup failed: {clear_outcome.error}")
        else:
            remaining_violations = sum(
                len(scan_result.candidates) for scan_result in scan_results
            )
            mro_failures = 0
            validation_mode = "dry-run-estimate"
            warnings.append(
                "Dry-run skips post-apply rescan; remaining violations reflect the current candidate snapshot."
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
            checkpoint_ref=checkpoint_ref,
            scan_duration_seconds=scan_duration,
            rewrite_duration_seconds=rewrite_duration,
            validation_duration_seconds=validation_duration,
            total_duration_seconds=total_duration,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    @classmethod
    def execute_command(
        cls, params: m.Infra.RefactorMigrateMroInput
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

    @classmethod
    def run_as_hook(cls, path: Path, *, dry_run: bool) -> t.SequenceOf[p.Infra.Result]:
        """Execute MRO migration as a rope post-hook (implements p.Infra.RopePostHook)."""
        try:
            report = cls(workspace_root=path).run(target="all", apply=not dry_run)
        except (
            *FlextInfraConstantsRope.SYNTAX_ERRORS,
            OSError,
            ValueError,
            KeyError,
            AttributeError,
        ):
            return []
        return cls._report_to_results(report=report, dry_run=dry_run)

    @staticmethod
    def _normalize_target(*, target: str) -> str:
        """Normalize target."""
        value: str = u.norm_str(target, case="lower")
        if value in c.Infra.MRO_TARGETS:
            return value
        msg = f"unsupported target: {target}"
        raise ValueError(msg)


__all__: list[str] = ["FlextInfraRefactorMigrateToClassMRO"]
