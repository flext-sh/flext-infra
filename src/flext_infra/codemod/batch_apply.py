"""Batch ast-grep application with preflight, fixed point, and fix-forward gates."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli
from flext_infra import m, p, r, t, u
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply discovered ast-grep rules and expose every regression for fix-forward."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Run check mode (report pending fixes) or the guarded apply circuit."""
        root = self.repository_root
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return r[t.Cli.ResultValue].fail(
                planned.error or "ast-grep rule discovery failed"
            )
        plan = planned.value
        effective_dry_run: bool = self.effective_dry_run
        if effective_dry_run:
            pending = FlextInfraModGateEngine.scan(root, plan, fix=False)
            if pending.failure:
                return r[t.Cli.ResultValue].fail(
                    pending.error or "ast-grep scan failed"
                )
            if pending.value.nodes:
                return r[t.Cli.ResultValue].fail(
                    f"{pending.value.nodes} pending actionable ast-grep fix(es) "
                    f"across {len(plan.rulesets)} inherited ruleset(s)"
                )
            cli.display_text("mod: no pending ast-grep fixes")
            return r[t.Cli.ResultValue].ok(True)
        return self._execute_apply(root, plan)

    def _execute_apply(
        self, root: Path, plan: m.Infra.CodemodRulePlan
    ) -> p.Result[t.Cli.ResultValue]:
        """Measure, batch-apply, prove a fixed point, and fail on every gate error."""
        baseline = FlextInfraModGateEngine.measure(root)
        if baseline.failure:
            return r[t.Cli.ResultValue].fail(
                baseline.error or "baseline measure failed"
            )
        pending = FlextInfraModGateEngine.scan(root, plan, fix=False)
        if pending.failure:
            return r[t.Cli.ResultValue].fail(pending.error or "ast-grep scan failed")
        normalized = FlextInfraModGateEngine.normalize_imports(
            root, baseline.value.ruff_files
        )
        if normalized.failure:
            return r[t.Cli.ResultValue].fail(
                normalized.error or "Rope import normalization failed"
            )
        if baseline.value.ruff_files:
            pending = FlextInfraModGateEngine.scan(root, plan, fix=False)
            if pending.failure:
                return r[t.Cli.ResultValue].fail(
                    pending.error or "ast-grep scan after import normalization failed"
                )
        remaining = pending
        applied_nodes = 0
        changed_paths: set[Path] = set()
        max_passes = len(plan.rules) + 1
        for _pass_index in range(max_passes):
            if not remaining.value.nodes:
                break
            applied = FlextInfraModGateEngine.scan(root, plan, fix=True)
            if applied.failure:
                return r[t.Cli.ResultValue].fail(
                    applied.error or "ast-grep fix pass failed"
                )
            applied_nodes += applied.value.nodes
            changed_paths.update(applied.value.files)
            normalized = FlextInfraModGateEngine.normalize_imports(
                root, applied.value.files
            )
            if normalized.failure:
                return r[t.Cli.ResultValue].fail(
                    normalized.error or "Rope import normalization failed"
                )
            remaining = FlextInfraModGateEngine.scan(root, plan, fix=False)
            if remaining.failure:
                return r[t.Cli.ResultValue].fail(
                    remaining.error or "ast-grep verification scan failed"
                )
        if remaining.value.nodes:
            return r[t.Cli.ResultValue].fail(
                f"{remaining.value.nodes} actionable finding(s) remained after "
                f"{max_passes} fixed-point pass(es)"
            )
        changed_files = len(changed_paths)
        final = FlextInfraModGateEngine.measure(root)
        if final.failure:
            return r[t.Cli.ResultValue].fail(final.error or "final measure failed")
        if FlextInfraModGateEngine.circuit_broken(baseline.value, final.value):
            return r[t.Cli.ResultValue].fail(
                f"mod circuit: gates regressed "
                f"(ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
                f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors})"
            )
        if final.value.ruff_errors or final.value.pyrefly_errors:
            diagnostics = "\n".join(final.value.diagnostics)
            return r[t.Cli.ResultValue].fail(
                "mod circuit: final gates are not clean "
                f"(ruff={final.value.ruff_errors}, "
                f"pyrefly={final.value.pyrefly_errors})\n{diagnostics}"
            )
        providers = " -> ".join(plan.provider_order)
        cli.display_text(
            f"mod: providers {providers}; "
            f"applied {applied_nodes} node(s) across {changed_files} file(s); "
            f"ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
            f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors}"
        )
        return r[t.Cli.ResultValue].ok(True)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
