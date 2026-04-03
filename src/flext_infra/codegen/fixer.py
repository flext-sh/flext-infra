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

from flext_core import r, s
from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraNamespaceEnforcer,
    FlextInfraNamespaceValidator,
    FlextInfraRefactorEngine,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    t,
    u,
)


def _violation(
    *,
    module: str,
    rule: str,
    line: int,
    message: str,
    fixable: bool,
) -> m.Infra.CensusViolation:
    """Create a CensusViolation with standard fields."""
    return m.Infra.CensusViolation(
        module=module,
        rule=rule,
        line=line,
        message=message,
        fixable=fixable,
    )


class FlextInfraCodegenFixer(s[bool]):
    """AST-based auto-fixer for namespace violations (Rules 1-5)."""

    class _FixContext(m.ArbitraryTypesModel):
        """Mutable accumulation context for fix operations."""

        violations_fixed: MutableSequence[m.Infra.CensusViolation] = Field(
            default_factory=list,
        )
        violations_skipped: MutableSequence[m.Infra.CensusViolation] = Field(
            default_factory=list,
        )
        files_modified: t.Infra.StrSet = Field(default_factory=set)

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_skipped.append(
                _violation(
                    module=module, rule=rule, line=line, message=message, fixable=False
                ),
            )

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_fixed.append(
                _violation(
                    module=module, rule=rule, line=line, message=message, fixable=True
                ),
            )

    _workspace_root: Path
    _dry_run: bool
    _rules_only: bool

    def __init__(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        rules_only: bool = False,
    ) -> None:
        """Initialize codegen fixer with workspace root."""
        super().__init__()
        self._workspace_root = workspace_root
        self._dry_run = dry_run
        self._rules_only = rules_only

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() directly")

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
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=ctx.violations_fixed,
            violations_skipped=ctx.violations_skipped,
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
        ctx = self._FixContext()
        src_dir = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        checkpoint_result = u.Infra.create_checkpoint(
            self._workspace_root,
            label=f"codegen-fix:{project_path.name}",
        )
        stash_ref = checkpoint_result.unwrap_or("")
        self._apply_ns_rules(project_path=project_path, ctx=ctx)
        if self._dry_run or self._rules_only:
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
        lazy_generator = FlextInfraCodegenLazyInit(project_path)
        lazy_errors = lazy_generator.run(check_only=False)
        ctx.files_modified.update(lazy_generator.modified_files)
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
            _ = u.Infra.rollback_to_checkpoint(self._workspace_root, stash_ref)
            raise
        return self._build_result(project_path.name, ctx)

    def _apply_ns_rules(
        self,
        *,
        project_path: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Collect current namespace-rule violations for reporting/dry-run output."""
        validation = FlextInfraNamespaceValidator().validate(project_path)
        if validation.is_failure:
            ctx.skip(
                module=project_path.name,
                rule="NAMESPACE",
                line=0,
                message=validation.error or "namespace validation failed",
            )
            return
        for violation_str in validation.value.violations:
            match = c.Infra.VIOLATION_PATTERN.match(violation_str)
            if match is None:
                ctx.skip(
                    module=project_path.name,
                    rule="NAMESPACE",
                    line=0,
                    message=violation_str,
                )
                continue
            ctx.skip(
                module=match.group("module"),
                rule=match.group("rule"),
                line=int(match.group("line")),
                message=match.group("message"),
            )

    def run(self) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on all projects in workspace."""
        projects_result = u.Infra.discover_projects(self._workspace_root)
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
