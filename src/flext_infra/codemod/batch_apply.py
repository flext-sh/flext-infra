"""Fix-forward ast-grep batch application for ``make mod APPLY=Y``."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import cli
from flext_infra import c, p, r, t, u
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply every discovered AST rewrite without destructive rollback."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Inspect or apply the complete rule cascade with visible phases."""
        rules = u.Infra.project_dependency_resource_files(
            self.repository_root,
            resource_parts=(c.Infra.CODEMOD_RESOURCE_DIRNAME, c.Cli.RULES_DIR_NAME),
            distribution_prefix=c.Infra.PKG_PREFIX_HYPHEN,
            suffix=c.Infra.CODEMOD_RULE_SUFFIX,
        )
        if not rules:
            return r.fail(f"no ast-grep rules discovered for {self.repository_root}")
        if self.effective_dry_run:
            cli.display_text(f"mod: scan {len(rules)} discovered rule file(s)")
            pending = FlextInfraModGateEngine.scan(
                self.repository_root, rules, fix=False
            ).unwrap()
            if pending.findings:
                return r.fail(
                    f"{pending.findings} pending ast-grep finding(s), "
                    f"{pending.nodes} actionable, across {len(rules)} rule file(s)"
                )
            FlextInfraModGateEngine.validate(self.repository_root, ()).unwrap()
            cli.display_text("mod: no pending ast-grep fixes")
            return r.ok(True)
        return self._execute_apply(self.repository_root, rules)

    @staticmethod
    def _execute_apply(
        root: Path, rules: t.SequenceOf[Path]
    ) -> p.Result[t.Cli.ResultValue]:
        """Apply rules in place and retain failures for mandatory fix-forward."""
        cli.display_text("mod: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(rules).unwrap()
        cli.display_text(f"mod: apply {len(rules)} ast-grep rule file(s)")
        applied = FlextInfraModGateEngine.scan(root, rules, fix=True).unwrap()
        cli.display_text("mod: verify AST fixed point")
        remaining = FlextInfraModGateEngine.scan(root, rules, fix=False).unwrap()
        if remaining.findings:
            return r.fail(
                f"{remaining.findings} finding(s) remained after apply; "
                "changes retained for mandatory fix-forward repair"
            )
        cli.display_text("mod: require zero Ruff, Pyrefly, LSP, and CRG diagnostics")
        FlextInfraModGateEngine.validate(root, tuple(applied.files)).unwrap()
        cli.display_text(
            f"mod: applied {applied.nodes} node(s) across {len(applied.files)} file(s)"
        )
        return r.ok(True)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
