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
    FlextInfraCodegenSnapshot,
    FlextInfraNamespaceValidator,
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
        pkg_dir = FlextInfraCodegenSnapshot.find_package_dir(project_path)
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
        stash_ref = checkpoint_result.value if checkpoint_result.is_success else ""
        self._apply_ns_rules(src_dir=src_dir, pkg_dir=pkg_dir, ctx=ctx)
        if self._dry_run or self._rules_only:
            return self._build_result(project_path.name, ctx)
        report = u.Infra.apply_project_mro_migrations(
            project_path=project_path, ctx=ctx
        )
        u.Infra.record_mro_migration_result(report=report, ctx=ctx)
        u.Infra.apply_refactor_engine_pass(project_path=project_path, ctx=ctx)
        u.Infra.apply_namespace_enforcement_pass(project_path=project_path, ctx=ctx)
        u.Infra.run_lazy_propagation(project_path=project_path, ctx=ctx)
        try:
            u.Infra.cleanup_stale_all_entries(ctx)
            u.Infra.normalize_rewritten_python_files(ctx)
        except (OSError, UnicodeDecodeError):
            _ = u.Infra.rollback_to_checkpoint(self._workspace_root, stash_ref)
            raise
        return self._build_result(project_path.name, ctx)

    def _apply_ns_rules(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Apply NS-001 through NS-005 rules."""
        excluded = {"constants.py", "typings.py", c.Infra.Files.INIT_PY}
        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name in excluded or py_file.name.startswith("_"):
                continue
            u.Infra.fix_rule1(
                source_file=py_file,
                pkg_dir=pkg_dir,
                ctx=ctx,
                dry_run=self._dry_run,
            )
            u.Infra.fix_rule2(
                source_file=py_file,
                pkg_dir=pkg_dir,
                ctx=ctx,
                dry_run=self._dry_run,
            )
        u.Infra.fix_rule3(pkg_dir=pkg_dir, ctx=ctx)
        u.Infra.fix_rule4(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            ctx=ctx,
            workspace_root=self._workspace_root,
        )
        u.Infra.fix_rule5(src_dir=src_dir, pkg_dir=pkg_dir, ctx=ctx)

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
