"""Auto-fix engine for namespace violations.

Orchestrates NS rule fixes, MRO migration, refactor engine passes,
namespace enforcement, and lazy init propagation for each project.

Rule implementations live in ``_utilities_codegen_fixer_rules``.
Pipeline passes live in ``_utilities_codegen_fixer_passes``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from pydantic import Field

from flext_core import r
from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraNamespaceEnforcer,
    FlextInfraNamespaceValidator,
    FlextInfraRefactorEngine,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    p,
    s,
    u,
)

_log = u.fetch_logger(__name__)


class FlextInfraCodegenFixer(s[str]):
    """Rope-oriented auto-fixer for namespace violations (Rules 1-5)."""

    dry_run: bool = Field(
        default=False, description="Preview changes without modifying files"
    )
    rules_only: bool = Field(
        default=False, description="Only apply rule-based fixes, skip heuristic ones"
    )

    @override
    def execute(self) -> r[str]:
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
        package_name = project.package_name
        prefix = FlextInfraNamespaceValidator.derive_prefix(project_path)
        if not prefix:
            return self._empty_result(project_path.name)
        if not package_name:
            return self._empty_result(project_path.name)
        pkg_dir = (
            project_path
            / c.Infra.DEFAULT_SRC_DIR
            / Path(
                *package_name.split("."),
            )
        )
        if not (pkg_dir / c.Infra.INIT_PY).is_file():
            return self._empty_result(project_path.name)
        ctx = m.Infra.FixContext()
        src_dir = pkg_dir.parent
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        initial_violations_result = u.Infra.parse_namespace_validation(
            FlextInfraNamespaceValidator().validate(project_path),
        )
        initial_violations = initial_violations_result.unwrap_or(())
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
        py_files = tuple(project_path.rglob(c.Infra.EXT_PYTHON_GLOB))
        bak_paths = u.Infra.backup_files(py_files)
        if self.dry_run or self.rules_only:
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        u.Infra.normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=project_path,
        ).run(target="all", apply=True)
        _log.info(
            "mro_migration_complete",
            project=project_path.name,
            migrations=len(report.migrations),
        )
        for migration in report.migrations:
            ctx.files_modified.add(migration.file)
            symbols = ", ".join(migration.moved_symbols) or "symbols"
            ctx.fix(
                module=migration.module,
                rule="MRO",
                line=1,
                message=f"migrated {symbols} into facade MRO",
            )
        for rewrite in report.rewrites:
            ctx.files_modified.add(rewrite.file)
            ctx.fix(
                module=rewrite.file,
                rule="MRO-REWRITE",
                line=1,
                message=f"rewrote {rewrite.replacements} consumer references",
            )
        for error in report.errors:
            ctx.skip(
                module=project_path.name,
                rule="MRO",
                line=0,
                message=error,
            )
        engine = FlextInfraRefactorEngine()
        config_result = engine.load_config()
        rules_result = engine.load_rules() if config_result.success else None
        if config_result.failure:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=config_result.error or "refactor settings load failed",
            )
        elif rules_result is not None and rules_result.failure:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=rules_result.error or "refactor rule load failed",
            )
        else:
            for result in engine.refactor_project(
                project_path,
                dry_run=False,
                apply_safety=False,
            ):
                if result.success:
                    ctx.files_modified.add(str(result.file_path))
                if result.modified:
                    changes = tuple(result.changes) or ("refactor applied",)
                    for change in changes:
                        ctx.fix(
                            module=str(result.file_path),
                            rule="REFACTOR",
                            line=1,
                            message=change,
                        )
                elif not result.success:
                    ctx.skip(
                        module=str(result.file_path),
                        rule="REFACTOR",
                        line=1,
                        message=result.error or "refactor failed",
                    )
        enforcement = FlextInfraNamespaceEnforcer(
            workspace_root=project_path,
        ).enforce(apply=True)
        for project_report in enforcement.projects:
            if project_report.has_violations:
                _log.warning(
                    "namespace_enforcement_failed",
                    project=project_path.name,
                    error="violations remain after namespace enforcement",
                )
                ctx.skip(
                    module=project_report.project,
                    rule="NAMESPACE",
                    line=0,
                    message="violations remain after namespace enforcement",
                )
        lazy_generator = FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": project_path},
        )
        lazy_errors = lazy_generator.generate_inits(check_only=False)
        for f in lazy_generator.modified_files:
            ctx.files_modified.add(f)
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
                remaining_violations=remaining_violations_result.unwrap_or(()),
            )
            ctx.violations_fixed.extend(fixed)
            ctx.violations_skipped.extend(skipped)
        return self._build_result(project_path.name, ctx)

    def fix_workspace(
        self,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on all projects in workspace.

        Args:
            projects: Pre-discovered projects to skip redundant discovery.

        """
        projects_result = u.Infra.discover_codegen_projects(
            self.workspace_root,
            projects=projects,
        )
        if not projects_result.success:
            msg = projects_result.error or "project discovery failed"
            raise RuntimeError(msg)
        return [self._fix_project(project) for project in projects_result.unwrap()]


__all__: list[str] = ["FlextInfraCodegenFixer"]
