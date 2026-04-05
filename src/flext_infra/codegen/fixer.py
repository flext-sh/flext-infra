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
    s,
    u,
)


class FlextInfraCodegenFixer(s[str]):
    """AST-based auto-fixer for namespace violations (Rules 1-5)."""

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
        results = self.fix_workspace()
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

    def fix_project(self, project_path: Path) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project."""
        prefix = FlextInfraNamespaceValidator.derive_prefix(project_path)
        if not prefix:
            return self._empty_result(project_path.name)
        src_dir_for_pkg = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        pkg_dir: Path | None = None
        if src_dir_for_pkg.is_dir():
            for child in sorted(src_dir_for_pkg.iterdir()):
                if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                    pkg_dir = child
                    break
        if pkg_dir is None:
            return self._empty_result(project_path.name)
        ctx = m.Infra.FixContext()
        src_dir = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        initial_violations_result = self._namespace_violations(project_path)
        initial_violations = initial_violations_result.unwrap_or(())
        if initial_violations_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=initial_violations_result.error
                or "namespace validation failed",
            )
        checkpoint_result = u.Infra.create_checkpoint(
            self.workspace_root,
            label=f"codegen-fix:{project_path.name}",
        )
        stash_ref = checkpoint_result.unwrap_or("")
        if self.dry_run or self.rules_only:
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=project_path,
        ).run(target="all", apply=True)
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
        rules_result = engine.load_rules() if config_result.is_success else None
        if config_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="REFACTOR",
                line=0,
                message=config_result.error or "refactor config load failed",
            )
        elif rules_result is not None and rules_result.is_failure:
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
            _ = u.Infra.rollback_to_checkpoint(self.workspace_root, stash_ref)
            raise
        self._reconcile_namespace_violations(
            project_path=project_path,
            ctx=ctx,
            initial_violations=initial_violations,
        )
        return self._build_result(project_path.name, ctx)

    @staticmethod
    def _namespace_violations(
        project_path: Path,
    ) -> r[tuple[m.Infra.CensusViolation, ...]]:
        """Return parsed namespace violations for one project."""
        validation = FlextInfraNamespaceValidator().validate(project_path)
        if validation.is_failure:
            return r[tuple[m.Infra.CensusViolation, ...]].fail(
                validation.error or "namespace validation failed",
            )
        violations: MutableSequence[m.Infra.CensusViolation] = []
        for violation_str in validation.value.violations:
            violation = FlextInfraCodegenFixer._parse_violation(violation_str)
            if violation is not None:
                violations.append(violation)
        return r[tuple[m.Infra.CensusViolation, ...]].ok(tuple(violations))

    @staticmethod
    def _parse_violation(violation_str: str) -> m.Infra.CensusViolation | None:
        """Parse a namespace violation string into a typed model."""
        match = c.Infra.VIOLATION_PATTERN.match(violation_str)
        if match is None:
            return None
        rule = match.group("rule")
        module = match.group("module")
        message = match.group("message")
        return m.Infra.CensusViolation(
            module=module,
            rule=rule,
            line=int(match.group("line")),
            message=message,
            fixable=u.Infra.is_rule_fixable(rule, module),
        )

    @staticmethod
    def _violation_key(
        violation: m.Infra.CensusViolation,
    ) -> tuple[str, str, int, str]:
        return (
            violation.module,
            violation.rule,
            violation.line,
            violation.message,
        )

    @classmethod
    def _reconcile_namespace_violations(
        cls,
        *,
        project_path: Path,
        ctx: m.Infra.FixContext,
        initial_violations: Sequence[m.Infra.CensusViolation],
    ) -> None:
        """Classify initial namespace violations as fixed or still skipped."""
        if not initial_violations:
            return
        remaining_result = cls._namespace_violations(project_path)
        if remaining_result.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=remaining_result.error or "namespace validation failed",
            )
            return
        remaining_keys = {
            cls._violation_key(violation)
            for violation in remaining_result.unwrap_or(())
        }
        for violation in initial_violations:
            if (
                violation.fixable
                and cls._violation_key(violation) not in remaining_keys
            ):
                ctx.violations_fixed.append(violation)
                continue
            ctx.violations_skipped.append(violation)

    def fix_workspace(self) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on all projects in workspace."""
        projects_result = u.Infra.discover_projects(self.workspace_root)
        if not projects_result.is_success:
            return []
        results: MutableSequence[m.Infra.AutoFixResult] = []
        discovered: Sequence[m.Infra.ProjectInfo] = projects_result.unwrap()
        for project in discovered:
            if project.name in c.Infra.EXCLUDED_PROJECTS:
                continue
            if (project.path / c.Infra.Files.GO_MOD).exists():
                continue
            results.append(self.fix_project(project.path))
        return results


__all__ = ["FlextInfraCodegenFixer"]
