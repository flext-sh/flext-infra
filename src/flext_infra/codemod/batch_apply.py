"""Fix-forward ast-grep batch application for ``make mod``."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli

from flext_core import r

from .. import FlextInfraServiceBase, m, p, t, u
from . import (
    FlextInfraCodemodSemanticApply,
    FlextInfraModGateEngine,
    FlextInfraModTextGateEngine,
)
from .batch_replacements import FlextInfraModReplacements


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
            text_pending = FlextInfraModTextGateEngine.scan(
                self.repository_root, fix=False, validate_receipts=True
            ).unwrap()
            pending_count += text_pending.findings
            if pending_count:
                return r[t.Cli.ResultValue].fail(
                    f"{pending.findings} pending ast-grep finding(s), "
                    f"{pending.actionable} actionable and "
                    f"{pending.detection_only} detection-only and "
                    f"{pending.non_actionable_with_fix} non-actionable with fix, plus "
                    f"{text_pending.findings} pending sed-by-list finding(s) "
                    f"({text_pending.actionable} actionable), across "
                    f"{len(rules)} rule file(s)"
                )
            validated = FlextInfraModGateEngine.validate(self.repository_root)
            if validated.failure:
                return r[t.Cli.ResultValue].from_failure(validated)
            cli.display_text("mod: no pending ast-grep or sed-by-list fixes")
            return r[t.Cli.ResultValue].ok(True)
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
        seen: t.MutableMappingKV[
            t.VariadicTuple[t.Quad[str, str, str, str | None]], int
        ] = {}
        iteration = 0
        transaction_paths = FlextInfraCodemodSemanticApply.plan_transaction_paths(
            root, current
        )
        while current.findings or transaction_paths:
            iteration += 1
            fingerprint = tuple(
                sorted(
                    [
                        (
                            finding.rule_id,
                            finding.file.as_posix(),
                            finding.text,
                            finding.replacement,
                        )
                        for finding in current.entries
                    ]
                    + [
                        (
                            "transaction-path-capability",
                            edit.file_path.as_posix(),
                            u.Cli.sha256_bytes(edit.original_source.encode()),
                            u.Cli.sha256_bytes(edit.updated_source.encode()),
                        )
                        for edit in transaction_paths
                    ]
                )
            )
            if fingerprint in seen:
                prev_iter = seen[fingerprint]
                # No-progress cause attribution: identify which rules/phases stalled
                stalled_rules = {
                    finding.rule_id for finding in current.entries if finding.actionable
                }
                return r[t.Cli.ResultValue].fail(
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
            # Validated mechanical rewrites are independent of later semantic
            # ambiguity. Publish their complete batch before selecting that phase.
            if current.actionable:
                cli.display_text(f"mod: apply {len(rules)} ast-grep rule file(s)")
                FlextInfraModGateEngine.scan(root, fix=True).unwrap()
            after_ast = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            FlextInfraCodemodBatchApply.validate_fix_match(current, after_ast)
            transaction_paths = FlextInfraCodemodSemanticApply.plan_transaction_paths(
                root, after_ast
            )
            if transaction_paths:
                FlextInfraCodemodSemanticApply.apply_transaction_paths(
                    root, transaction_paths
                )
                current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
                transaction_paths = (
                    FlextInfraCodemodSemanticApply.plan_transaction_paths(root, current)
                )
                continue
            owned = FlextInfraModReplacements.require_authored(after_ast)
            if owned.failure:
                return r[t.Cli.ResultValue].from_failure(owned)
            FlextInfraCodemodSemanticApply.apply(root, after_ast)
            current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        current_text = FlextInfraModTextGateEngine.scan(
            root, fix=False, validate_receipts=True
        ).unwrap()
        seen_text: t.MutableMappingKV[
            t.VariadicTuple[tuple[str, str, int, str, str]], int
        ] = {}
        iteration = 0
        while current_text.findings:
            iteration += 1
            text_fingerprint = FlextInfraCodemodBatchApply._text_fingerprint(
                current_text.entries
            )
            if text_fingerprint in seen_text:
                prev_iter = seen_text[text_fingerprint]
                stalled = {
                    finding.rule_id
                    for finding in current_text.entries
                    if finding.text != finding.replacement
                }
                return r[t.Cli.ResultValue].fail(
                    f"mod text phase iteration {iteration} made no progress since "
                    f"iteration {prev_iter}; stalled sed-by-list rules: "
                    f"{', '.join(sorted(stalled)) or 'none'}; changes retained "
                    "for mandatory owner repair"
                )
            seen_text[text_fingerprint] = iteration
            cli.display_text(
                f"mod: text phase iteration {iteration} — "
                f"{current_text.findings} sed-by-list finding(s), "
                f"{current_text.actionable} actionable"
            )
            if current_text.actionable:
                cli.display_text("mod: apply sed-by-list rule cascade")
                FlextInfraModTextGateEngine.scan(root, fix=True).unwrap()
            current_text = FlextInfraModTextGateEngine.scan(root, fix=False).unwrap()
            if not current_text.actionable and current_text.findings:
                detection_only = {finding.rule_id for finding in current_text.entries}
                return r[t.Cli.ResultValue].fail(
                    "mod text phase retains detection-only findings without a "
                    f"rewrite: {', '.join(sorted(detection_only))}"
                )
        cli.display_text(
            "mod: require canonical formatting and zero Ruff, Pyrefly, and LSP diagnostics"
        )
        validated = FlextInfraModGateEngine.validate(root)
        if validated.failure:
            return r[t.Cli.ResultValue].from_failure(validated)
        cli.display_text("mod: AST fixed point verified with zero findings")
        return r[t.Cli.ResultValue].ok(True)

    @staticmethod
    def _text_fingerprint(
        entries: t.VariadicTuple[m.Infra.ModTextFinding],
    ) -> t.VariadicTuple[tuple[str, str, int, str, str]]:
        """Build a sorted fingerprint of all text findings."""
        result: list[tuple[str, str, int, str, str]] = []
        for entry in entries:
            rule_id: str = entry.rule_id
            file_path: str = entry.file.as_posix()
            line_no: int = entry.line
            text_val: str = entry.text
            replacement_val: str = entry.replacement
            result.append((rule_id, file_path, line_no, text_val, replacement_val))
        return tuple(sorted(result))

    @staticmethod
    def validate_fix_match(
        before: m.Infra.ModScanReport, after_apply: m.Infra.ModScanReport
    ) -> None:
        """Reject unresolved rewrites while preserving valid rule cascades."""
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
        # A completed rule may enable a later rule in the declared cascade.
        # Those later-rule findings are consumed by the next fixed-point iteration.
        new_actionable = after_apply_actionable - before_actionable
        prior_rule_ids = {rule_id for rule_id, _, _, _ in before_actionable}
        unexpected = {
            finding for finding in new_actionable if finding[0] in prior_rule_ids
        }
        if unexpected:
            rule_ids = {r for r, _, _, _ in unexpected}
            files = {p for _, p, _, _ in unexpected}
            msg = (
                f"fix!=match: ast-grep apply introduced {len(unexpected)} new actionable "
                f"findings in rules {sorted(rule_ids)} across files {sorted(files)}"
            )
            raise RuntimeError(msg)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
