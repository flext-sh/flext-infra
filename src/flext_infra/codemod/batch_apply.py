"""Fix-forward ast-grep batch application for ``make mod``."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli

from .. import FlextInfraServiceBase, m, p, r, t, u
from . import FlextInfraCodemodSemanticApply, FlextInfraModGateEngine


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply every discovered AST rewrite without destructive rollback."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Inspect or apply the complete rule cascade with visible phases."""
        planned = u.Infra.codemod_rule_plan(self.repository_root)
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        rules = tuple(dict.fromkeys(rule.resource for rule in planned.value.rules))
        if self.effective_dry_run:
            cli.display_text(f"mod: scan {len(rules)} discovered rule file(s)")
            pending = FlextInfraModGateEngine.scan(
                self.repository_root, fix=False
            ).unwrap()
            pending_count = pending.findings
            if pending_count:
                return r.fail(
                    f"{pending_count} pending ast-grep finding(s), "
                    f"{pending.actionable} actionable and "
                    f"{pending.detection_only} detection-only and "
                    f"{pending.non_actionable_with_fix} non-actionable with fix, across "
                    f"{len(rules)} rule file(s)"
                )
            FlextInfraModGateEngine.validate(self.repository_root).unwrap()
            cli.display_text("mod: no pending ast-grep fixes")
            return r.ok(True)
        return self._execute_apply(self.repository_root, rules)

    @staticmethod
    def _execute_apply(
        root: Path, rules: t.SequenceOf[Path]
    ) -> p.Result[t.Cli.ResultValue]:
        """Apply rules in place and retain failures for mandatory fix-forward."""
        cli.display_text("mod: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(root, rules).unwrap()
        cli.display_text("mod: preflight complete AST inventory")
        current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        seen: dict[t.VariadicTuple[t.Quad[str, str, str, str | None]], int] = {}
        iteration = 0
        while current.findings:
            iteration += 1
            fingerprint = tuple(
                sorted(
                    (
                        finding.rule_id,
                        finding.file.as_posix(),
                        finding.text,
                        finding.replacement,
                    )
                    for finding in current.entries
                )
            )
            if fingerprint in seen:
                prev_iter = seen[fingerprint]
                # No-progress cause attribution: identify which rules/phases stalled
                stalled_rules = {
                    finding.rule_id for finding in current.entries if finding.actionable
                }
                return r.fail(
                    f"mod iteration {iteration} made no progress since iteration {prev_iter}; "
                    f"stalled actionable rules: {', '.join(sorted(stalled_rules)) or 'none'}; "
                    f"{current.actionable} actionable, {current.detection_only} detection-only, "
                    f"{current.non_actionable_with_fix} non-actionable with fix; "
                    "changes retained for mandatory owner repair"
                )
            seen[fingerprint] = iteration
            cli.display_text(
                f"mod: iteration {iteration} — "
                f"{current.actionable} actionable, {current.detection_only} detection-only, "
                f"{current.non_actionable_with_fix} non-actionable with fix"
            )
            FlextInfraCodemodSemanticApply.apply(root, current)
            # Fix!=match validation: verify semantic phase actually reduced findings
            after_semantic = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            if after_semantic.actionable:
                cli.display_text(f"mod: apply {len(rules)} ast-grep rule file(s)")
                FlextInfraModGateEngine.scan(root, fix=True).unwrap()
            # Fix!=match validation: check that ast-grep apply actually changed what was expected
            after_apply = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            FlextInfraCodemodBatchApply._validate_fix_match(
                current, after_semantic, after_apply
            )
            current = after_apply
        cli.display_text(
            "mod: require canonical formatting and zero Ruff, Pyrefly, and LSP diagnostics"
        )
        FlextInfraModGateEngine.validate(root).unwrap()
        cli.display_text("mod: AST fixed point verified with zero findings")
        return r.ok(True)

    @staticmethod
    def _validate_fix_match(
        before: m.Infra.ModScanReport,
        after_semantic: m.Infra.ModScanReport,
        after_apply: m.Infra.ModScanReport,
    ) -> None:
        """Validate that applied fixes match expected changes (fix!=match)."""
        # Check that actionable findings were actually resolved
        before_actionable = {
            (f.rule_id, f.file.as_posix(), f.text, f.replacement)
            for f in before.entries
            if f.actionable
        }
        after_apply_actionable = {
            (f.rule_id, f.file.as_posix(), f.text, f.replacement)
            for f in after_apply.entries
            if f.actionable
        }
        after_semantic_actionable = {
            (f.rule_id, f.file.as_posix(), f.text, f.replacement)
            for f in after_semantic.entries
            if f.actionable
        }
        # The semantic phase may only reduce the actionable set, never grow it
        semantic_new = after_semantic_actionable - before_actionable
        if semantic_new:
            rule_ids = {r for r, _, _, _ in semantic_new}
            files = {p for _, p, _, _ in semantic_new}
            msg = (
                f"fix!=match: semantic phase introduced {len(semantic_new)} new "
                f"actionable findings in rules {sorted(rule_ids)} across files "
                f"{sorted(files)}"
            )
            raise RuntimeError(msg)
        # Actionable findings should be resolved
        unresolved = before_actionable & after_apply_actionable
        if unresolved:
            rule_ids = {r for r, _, _, _ in unresolved}
            files = {p for _, p, _, _ in unresolved}
            msg = (
                f"fix!=match: ast-grep apply did not resolve {len(unresolved)} expected actionable "
                f"findings in rules {sorted(rule_ids)} across files {sorted(files)}"
            )
            raise RuntimeError(msg)
        # Check that new actionable findings weren't introduced
        new_actionable = after_apply_actionable - before_actionable
        if new_actionable:
            rule_ids = {r for r, _, _, _ in new_actionable}
            files = {p for _, p, _, _ in new_actionable}
            msg = (
                f"fix!=match: ast-grep apply introduced {len(new_actionable)} new actionable "
                f"findings in rules {sorted(rule_ids)} across files {sorted(files)}"
            )
            raise RuntimeError(msg)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
