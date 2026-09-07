"""Fix-forward ast-grep batch application for ``make mod APPLY=Y``."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli
from flext_infra import p, r, t, u
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply


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
        seen: set[t.VariadicTuple[t.Quad[str, str, str, str | None]]] = set()
        while current.findings:
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
                return r.fail(
                    f"{current.actionable} actionable and "
                    f"{current.detection_only} detection-only and "
                    f"{current.non_actionable_with_fix} non-actionable with fix "
                    "finding(s) made no progress; changes retained for mandatory "
                    "owner repair"
                )
            seen.add(fingerprint)
            FlextInfraCodemodSemanticApply.apply(root, current)
            after_semantic = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            if after_semantic.actionable:
                cli.display_text(f"mod: apply {len(rules)} ast-grep rule file(s)")
                FlextInfraModGateEngine.scan(root, fix=True).unwrap()
            current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        cli.display_text(
            "mod: require canonical formatting and zero Ruff, Pyrefly, and LSP diagnostics"
        )
        FlextInfraModGateEngine.validate(root).unwrap()
        cli.display_text("mod: AST fixed point verified with zero findings")
        return r.ok(True)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
