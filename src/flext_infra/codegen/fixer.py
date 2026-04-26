"""Auto-fix engine for namespace violations.

Orchestrates NS rule fixes, MRO migration, refactor engine passes,
namespace enforcement, and lazy init propagation for each project.

Rule implementations live in ``_utilities_codegen_fixer_rules``.
Pipeline passes live in ``_utilities_codegen_fixer_passes``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraNamespaceEnforcer,
    FlextInfraNamespaceValidator,
    FlextInfraProjectSelectionServiceBase,
    FlextInfraRefactorEngine,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    p,
    r,
    u,
)

_log = u.fetch_logger(__name__)


class FlextInfraCodegenFixer(FlextInfraProjectSelectionServiceBase[str]):
    """Rope-oriented auto-fixer for namespace violations (Rules 1-5)."""

    dry_run: Annotated[
        bool, m.Field(description="Preview changes without modifying files")
    ] = False
    rules_only: Annotated[
        bool, m.Field(description="Only apply rule-based fixes, skip heuristic ones")
    ] = False

    @override
    def execute(self) -> p.Result[str]:
        """Execute auto-fix directly from the validated CLI service model."""
        dry_run = self.dry_run or not self.apply_changes
        try:
            results = self.fix_workspace()
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return r[str].fail(f"auto-fix failed: {exc}", exception=exc)
        total_fixed = sum(len(result.violations_fixed) for result in results)
        total_skipped = sum(len(result.violations_skipped) for result in results)
        lines: MutableSequence[str] = []
        if dry_run:
            lines.append("Dry-run mode: no files will be modified")
        lines.extend(
            (f"  {result.project}: fixed {len(result.violations_fixed)} violations")
            for result in results
            if result.violations_fixed
        )
        lines.append(
            (
                f"Auto-fix: {total_fixed} fixed, {total_skipped} skipped"
                f" across {len(results)} projects"
            ),
        )
        return r[str].ok("\n".join(lines))

    @staticmethod
    def _empty_result(project_name: str) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=[],
            violations_skipped=[],
            files_modified=[],
        )

    @staticmethod
    def _build_result(
        project_name: str,
        ctx: m.Infra.FixContext,
    ) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=list(ctx.violations_fixed),
            violations_skipped=list(ctx.violations_skipped),
            files_modified=sorted(ctx.files_modified),
        )

    def _fix_project(
        self,
        project: p.Infra.ProjectInfo,
    ) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project."""
        project_path = project.path
        project_layout = u.Infra.layout(project_path)
        if project_layout is None or not project_layout.class_stem:
            return self._empty_result(project_path.name)
        pkg_dir = project_layout.package_dir
        if not (pkg_dir / c.Infra.INIT_PY).is_file():
            return self._empty_result(project_path.name)
        ctx = m.Infra.FixContext()
        src_dir = pkg_dir.parent
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        initial_violations_result = u.Infra.parse_namespace_validation(
            FlextInfraNamespaceValidator().validate(project_path),
        )
        initial_violations = (
            initial_violations_result.unwrap()
            if initial_violations_result.success
            else ()
        )
        if initial_violations_result.failure:
            _log.warning(
                "namespace_validation_failed",
                project=project_path.name,
                error=str(initial_violations_result.error),
            )
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=initial_violations_result.error
                or "namespace validation failed",
            )
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
        )
        if self.dry_run or self.rules_only:
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        py_files = tuple(py_files_result.value) if py_files_result.success else ()
        bak_paths = u.Infra.backup_files(py_files)
        u.Infra.normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=project_path,
        ).run(target="all", apply=True)
        _log.info(
            "mro_migration_complete",
            project=project_path.name,
            migrations=len(report.migrations),
        )
        ctx.files_modified = {
            *ctx.files_modified,
            *(migration.file for migration in report.migrations),
        }
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=migration.module,
                rule="MRO",
                line=1,
                message=(
                    f"migrated {', '.join(migration.moved_symbols) or 'symbols'}"
                    " into facade MRO"
                ),
                fixable=True,
            )
            for migration in report.migrations
        )
        ctx.files_modified = {
            *ctx.files_modified,
            *(rewrite.file for rewrite in report.rewrites),
        }
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=rewrite.file,
                rule="MRO-REWRITE",
                line=1,
                message=f"rewrote {rewrite.replacements} consumer references",
                fixable=True,
            )
            for rewrite in report.rewrites
        )
        ctx.violations_skipped.extend(
            m.Infra.CensusViolation(
                module=project_path.name,
                rule="MRO",
                line=0,
                message=error,
                fixable=False,
            )
            for error in report.errors
        )
        engine = FlextInfraRefactorEngine()
        config_result = engine.load_config()
        rules_result = engine.load_rules() if config_result.success else None
        refactor_load_error = next(
            (
                message
                for failed, message in (
                    (
                        config_result.failure,
                        config_result.error or "refactor settings load failed",
                    ),
                    (
                        rules_result is not None and rules_result.failure,
                        (
                            rules_result.error
                            if rules_result is not None
                            else "refactor rule load failed"
                        )
                        or "refactor rule load failed",
                    ),
                )
                if failed
            ),
            None,
        )
        if refactor_load_error is not None:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=refactor_load_error,
            )
        else:
            refactor_results = tuple(
                engine.refactor_project(
                project_path,
                dry_run=False,
                apply_safety=False,
                ),
            )
            ctx.files_modified = {
                *ctx.files_modified,
                *(
                    str(result.file_path)
                    for result in refactor_results
                    if result.success
                ),
            }
            ctx.violations_fixed.extend(
                m.Infra.CensusViolation(
                    module=str(result.file_path),
                    rule="REFACTOR",
                    line=1,
                    message=change,
                    fixable=True,
                )
                for result in refactor_results
                if result.modified
                for change in (tuple(result.changes) or ("refactor applied",))
            )
            ctx.violations_skipped.extend(
                m.Infra.CensusViolation(
                    module=str(result.file_path),
                    rule="REFACTOR",
                    line=1,
                    message=result.error or "refactor failed",
                    fixable=False,
                )
                for result in refactor_results
                if (not result.modified) and (not result.success)
            )
        enforcement = FlextInfraNamespaceEnforcer(
            workspace_root=project_path,
        ).enforce(apply=True)
        violating_projects = tuple(
            project_report
            for project_report in enforcement.projects
            if project_report.has_violations
        )
        if violating_projects:
            _log.warning(
                "namespace_enforcement_failed",
                project=project_path.name,
                error="violations remain after namespace enforcement",
            )
            ctx.violations_skipped.extend(
                m.Infra.CensusViolation(
                    module=project_report.project,
                    rule="NAMESPACE",
                    line=0,
                    message="violations remain after namespace enforcement",
                    fixable=False,
                )
                for project_report in violating_projects
            )
        lazy_generator = FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": project_path},
        )
        lazy_errors = lazy_generator.generate_inits(check_only=False)
        ctx.files_modified = {
            *ctx.files_modified,
            *lazy_generator.modified_files,
        }
        if lazy_errors > 0:
            ctx.skip(
                module=project_path.name,
                rule="LAZY-INIT",
                line=0,
                message=f"lazy propagation finished with {lazy_errors} errors",
            )
        try:
            for modified_file in sorted(ctx.files_modified):
                path = Path(modified_file)
                if path.is_file():
                    u.Infra.run_ruff_fix(path, quiet=True)
        except (OSError, UnicodeDecodeError):
            u.Infra.restore_files(bak_paths)
            raise
        remaining_violations_result = u.Infra.parse_namespace_validation(
            FlextInfraNamespaceValidator().validate(project_path),
        )
        if remaining_violations_result.failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=remaining_violations_result.error
                or "namespace validation failed",
            )
        else:
            fixed, skipped = u.Infra.classify_violation_outcomes(
                project_path=project_path,
                initial_violations=initial_violations,
                remaining_violations=(
                    remaining_violations_result.unwrap()
                    if remaining_violations_result.success
                    else ()
                ),
            )
            ctx.violations_fixed.extend(fixed)
            ctx.violations_skipped.extend(skipped)
        return self._build_result(project_path.name, ctx)

    def fix_workspace(
        self,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on selected projects (defaults to ``--projects`` scope or full workspace).

        Args:
            projects: Pre-discovered projects to skip redundant discovery.

        """
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            projects_result = u.Infra.projects(self.workspace_root)
            discovered = (
                tuple(projects_result.unwrap()) if projects_result.success else ()
            )
            scope = frozenset(self.project_names or ())
            selected_projects = (
                tuple(p for p in discovered if p.path.name in scope)
                if scope
                else discovered
            )
        return [self._fix_project(project) for project in selected_projects]


__all__: list[str] = ["FlextInfraCodegenFixer"]
