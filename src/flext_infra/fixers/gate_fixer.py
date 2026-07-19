"""Gate-based fix adapter for enforcement rules backed by quality gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, t, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr


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

    def _registry(self) -> FlextInfraGateRegistry:
        """Lazy import of the gate registry to avoid circular imports."""
        return FlextInfraGateRegistry.default()

    @override
    def can_fix(self, fix_action: p.EnforcementFixAction) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        if fix_action.kind != self.kind:
            return False
        gate_cls = self._registry().get(fix_action.target)
        return gate_cls is not None and gate_cls.can_fix

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[p.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: p.Infra.FixEnforcementCommand,
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
        reports_dir = project_dir / c.Infra.REPORTS_DIR_NAME / "fix-enforcement"
        if ctx.apply:
            reports_dir_result = u.Cli.ensure_dir(reports_dir)
            if reports_dir_result.failure:
                return fr.ProjectFixResult(
                    project=project_dir.name,
                    failed=(
                        fr.FailedFix(
                            rule_id=rule.id,
                            file_path=str(project_dir),
                            error=(
                                reports_dir_result.error
                                or "unable to create report dir"
                            ),
                        ),
                    ),
                )
            reports_dir = reports_dir_result.value
        gate_ctx = m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=reports_dir,
            apply_fixes=ctx.apply,
            check_only=not ctx.apply,
            fail_fast=ctx.fail_fast,
        )
        try:
            execution = (
                gate.fix(project_dir, gate_ctx)
                if ctx.apply
                else gate.check(project_dir, gate_ctx)
            )
        except c.EXC_BROAD_RUNTIME as exc:
            return fr.ProjectFixResult(
                project=project_dir.name,
                failed=(
                    fr.FailedFix(
                        rule_id=rule.id,
                        file_path=str(project_dir),
                        error=(
                            f"gate {fix_action.target} execution failed: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                    ),
                ),
            )
        if not ctx.apply:
            return self._preview_from_check(
                project_dir=project_dir,
                rule=rule,
                target=fix_action.target,
                execution=execution,
            )
        fixed: list[fr.FixedViolation] = []
        previewed: list[fr.PreviewedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        if execution.result.passed:
            message = f"gate {fix_action.target} fix applied"
            fixed_violation: fr.FixedViolation = fr.FixedViolation(
                rule_id=rule.id, file_path=str(project_dir), message=message
            )
            fixed = [fixed_violation]
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
            previewed=tuple(previewed),
            skipped=tuple(skipped),
            failed=tuple(failed),
        )

    def _preview_from_check(
        self,
        *,
        project_dir: Path,
        rule: p.EnforcementRuleSpec,
        target: str,
        execution: p.Infra.GateExecution,
    ) -> fr.ProjectFixResult:
        """Build a dry-run result from the non-mutating gate check output."""
        matching = self._matching_issues(rule, execution.issues)
        if matching:
            return fr.ProjectFixResult(
                project=project_dir.name,
                previewed=(
                    fr.PreviewedViolation(
                        rule_id=rule.id,
                        file_path=str(project_dir),
                        message=(
                            f"would run gate {target} fix for "
                            f"{len(matching)} matching issue(s)"
                        ),
                    ),
                ),
            )
        if execution.result.passed:
            return fr.ProjectFixResult(project=project_dir.name)
        details = execution.raw_output or "; ".join(
            issue.formatted for issue in execution.issues
        )
        return fr.ProjectFixResult(
            project=project_dir.name,
            failed=(
                fr.FailedFix(
                    rule_id=rule.id,
                    file_path=str(project_dir),
                    error=details or f"gate {target} check failed",
                ),
            ),
        )

    @staticmethod
    def _matching_issues(
        rule: p.EnforcementRuleSpec, issues: t.SequenceOf[p.Infra.Issue]
    ) -> tuple[p.Infra.Issue, ...]:
        """Return gate issues that correspond to the selected rule fix action."""
        fix_action = rule.fix_action
        if fix_action is None:
            return ()
        smell_tag = str(fix_action.params.get("smell_tag", ""))
        if not smell_tag:
            return tuple(issues)
        return tuple(
            issue
            for issue in issues
            if c.Infra.SMELLS_RULE_TAGS.get(issue.code, "") == smell_tag
        )


__all__: list[str] = ["FlextInfraGateFixerAdapter"]
