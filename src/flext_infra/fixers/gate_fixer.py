"""Gate-based fix adapter for enforcement rules backed by quality gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.constants import c
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraGateFixerAdapter(FlextInfraFixerAdapter):
    """Apply fixes by delegating to a registered ``FlextInfraGate``.

    This adapter handles ``fix_action.kind == "gate"`` by routing the rule
    to the gate registered under ``fix_action.target``. The gate must have
    ``can_fix=True`` and implement ``_build_fix_command``.
    """

    kind: ClassVar[str] = "gate"

    def __init__(self, workspace_root: Path) -> None:
        """Bind the workspace root used to instantiate gates."""
        super().__init__(workspace_root)

    def _registry(self) -> object:
        """Lazy import of the gate registry to avoid circular imports."""
        import importlib

        mod = importlib.import_module("flext_infra.check.workspace_check_gates")
        return mod.FlextInfraGateRegistry.default()

    @override
    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        return fix_action.kind == self.kind

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, t.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Apply gate fixes for the first violation group (all share target)."""
        if not violations:
            return fr.ProjectFixResult(project=project_dir.name)
        rule, _probe = violations[0]
        fix_action = rule.fix_action
        if fix_action is None:
            return fr.ProjectFixResult(project=project_dir.name)
        gate_cls = self._registry().get(fix_action.target)
        if gate_cls is None:
            return fr.ProjectFixResult(
                project=project_dir.name,
                failed=(
                    fr.FailedFix(
                        rule_id=rule.id,
                        file_path=str(project_dir),
                        error=f"gate {fix_action.target} not registered",
                    ),
                ),
            )
        gate = gate_cls(self._workspace_root)
        if not gate.can_fix:
            return fr.ProjectFixResult(
                project=project_dir.name,
                skipped=(
                    fr.SkippedViolation(
                        rule_id=rule.id,
                        file_path=str(project_dir),
                        reason=f"gate {fix_action.target} does not support fix",
                    ),
                ),
            )
        gate_ctx = m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=u.Cli.ensure_dir(
                project_dir / c.Infra.REPORTS_DIR_NAME / "fix-enforcement",
            ),
            apply_fixes=ctx.apply,
            check_only=ctx.dry_run,
            fail_fast=ctx.fail_fast,
        )
        execution = gate.fix(project_dir, gate_ctx)
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        if execution.result.passed:
            fixed = [
                fr.FixedViolation(
                    rule_id=rule.id,
                    file_path=str(project_dir),
                    message=f"gate {fix_action.target} fix applied",
                )
            ]
        else:
            failed = [
                fr.FailedFix(
                    rule_id=rule.id,
                    file_path=str(project_dir),
                    error=execution.raw_output or "gate fix failed",
                )
            ]
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
        )


__all__: list[str] = ["FlextInfraGateFixerAdapter"]
