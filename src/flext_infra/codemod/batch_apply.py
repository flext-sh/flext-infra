"""Batch ast-grep rule application guarded by the operator safety circuit.

Circuit contract (``make mod APPLY=Y``): measure ruff + pyrefly error counts
before the batch apply, apply every rule discovered through the package cascade
(``flext_infra.codemod.discovery``) plus the project's own hand-written
``ast-grep-rules/``, then re-measure. Any count increase fails loud with the
changed files retained for the required fix-forward repair; the codemod never
commits, resets, restores, checks out, or otherwise rewrites unrelated work.
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli
from flext_infra import config, m, p, r, t
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.discovery import discover_rules


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply the discovered ast-grep rule batch under the fix-forward circuit."""

    def _rules(self) -> p.Result[t.SequenceOf[Path]]:
        """Resolve the batch: packaged cascade plus project-local own rules.

        Project-local ``ast-grep-rules/`` files are applied last so a
        hand-written rule overrides a packaged rule with the same rule ID.
        """
        rules = {rule.stem: rule for rule in discover_rules()}
        for rule_dir_name in config.Infra.codegen.sgconfig.rule_dirs:
            rule_dir = self.repository_root / rule_dir_name
            if not rule_dir.is_dir():
                continue
            for rule_file in sorted(rule_dir.rglob("*.yml")):
                rules[rule_file.stem] = rule_file
        if not rules:
            return r[t.SequenceOf[Path]].fail(
                f"no ast-grep rules discovered for {self.repository_root}"
            )
        return r[t.SequenceOf[Path]].ok(tuple(sorted(rules.values())))

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Run check mode (report pending fixes) or the guarded apply circuit."""
        root = self.repository_root
        rules_result = self._rules()
        if rules_result.failure:
            return r[t.Cli.ResultValue].fail(
                rules_result.error or "ast-grep rule discovery failed"
            )
        rules = rules_result.value
        prepared_rules = FlextInfraModGateEngine.prepare_rules(rules)
        if prepared_rules.failure:
            return r[t.Cli.ResultValue].fail(
                prepared_rules.error or "ast-grep rule preparation failed"
            )
        compiled_rules = prepared_rules.value
        effective_dry_run: bool = self.effective_dry_run
        if effective_dry_run:
            pending = FlextInfraModGateEngine.scan_prepared(
                root, compiled_rules, fix=False
            )
            if pending.failure:
                return r[t.Cli.ResultValue].fail(
                    pending.error or "ast-grep scan failed"
                )
            if pending.value.nodes:
                return r[t.Cli.ResultValue].fail(
                    f"{pending.value.nodes} pending ast-grep finding(s) "
                    f"across {compiled_rules.rule_count} discovered rule file(s)"
                )
            cli.display_text("mod: no pending ast-grep fixes")
            return r[t.Cli.ResultValue].ok(True)
        return self._execute_apply(root, compiled_rules)

    def _execute_apply(
        self, root: Path, compiled_rules: m.Infra.ModRuleBatch
    ) -> p.Result[t.Cli.ResultValue]:
        """Measure, batch-apply, and retain every result for fix-forward repair."""
        cli.display_text("mod: phase=measure-baseline")
        baseline = FlextInfraModGateEngine.measure(root)
        if baseline.failure:
            return r[t.Cli.ResultValue].fail(
                baseline.error or "baseline measure failed"
            )
        cli.display_text(f"mod: phase=scan-before rules={compiled_rules.rule_count}")
        pending = FlextInfraModGateEngine.scan_prepared(root, compiled_rules, fix=False)
        if pending.failure:
            return r[t.Cli.ResultValue].fail(pending.error or "ast-grep scan failed")
        cli.display_text(f"mod: phase=apply rules={compiled_rules.rule_count}")
        applied = FlextInfraModGateEngine.scan_prepared(root, compiled_rules, fix=True)
        if applied.failure:
            return r[t.Cli.ResultValue].fail(
                applied.error or "ast-grep fix pass failed"
            )
        cli.display_text(f"mod: phase=scan-after rules={compiled_rules.rule_count}")
        remaining = FlextInfraModGateEngine.scan_prepared(
            root, compiled_rules, fix=False
        )
        if remaining.failure:
            return r[t.Cli.ResultValue].fail(
                remaining.error or "ast-grep verification scan failed"
            )
        if remaining.value.nodes:
            findings = "\n".join(remaining.value.findings)
            return r[t.Cli.ResultValue].fail(
                f"{remaining.value.nodes} ast-grep finding(s) remained after apply "
                f"across {len(remaining.value.files)} file(s):\n{findings}"
            )
        verified_nodes = pending.value.nodes - remaining.value.nodes
        changed_files = len(applied.value.files)
        cli.display_text("mod: phase=measure-final")
        final = FlextInfraModGateEngine.measure(root)
        if final.failure:
            return r[t.Cli.ResultValue].fail(final.error or "final measure failed")
        if FlextInfraModGateEngine.fixed_point_broken(final.value):
            diagnostics = "\n".join(
                output.strip()
                for output in (final.value.ruff_output, final.value.pyrefly_output)
                if output.strip()
            )
            return r[t.Cli.ResultValue].fail(
                f"mod circuit: gates are not at zero-findings fixed point "
                f"(ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
                f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors}); "
                f"changes retained for fix-forward repair\n{diagnostics}"
            )
        cli.display_text(
            f"mod: applied {verified_nodes} node(s) across {changed_files} file(s); "
            f"ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
            f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors}"
        )
        return r[t.Cli.ResultValue].ok(True)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
