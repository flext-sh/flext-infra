"""Standalone ast engine verb (``refactor ast`` / ``make ast``).

Runs the two mechanical cascades of ``make mod`` (ADR-017): the ast-grep rule
cascade and the sed-by-list cascade from the rules tree (``config/rules/ast``
patterns plus ``config/rules/mod/sed.yaml``). Scan-only by default; ``--apply``
drives both cascades to a verified fixed point with exact receipts. Rope
phases, the enforcement component, and the lint gates belong to ``mod``.
``--rules`` selects exact CSV AST IDs only, retaining the full governed corpus;
text and semantic callbacks are not executed in that mode.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override
from uuid import uuid4

from flext_cli import cli

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.text_gates import FlextInfraModTextGateEngine
from flext_infra.refactor import FlextInfraRefactorViolationsSweep


class FlextInfraCodemodAstScan(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Run the ast-grep cascade and the sed-by-list cascade of the rules tree."""

    rules: str | None = m.Field(
        default=None,
        description="Exact comma-separated AST rule IDs; excludes text and callbacks",
    )

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Report or apply both mechanical cascades of the ast engine.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        # The engines currently own full-corpus inventories and count receipts.
        # Refuse narrower requests before either engine can scan or publish.
        if any(
            selector is not None
            for selector in (
                self.target_module,
                self.target_namespace,
                self.project_filter,
            )
        ):
            return r[t.Cli.ResultValue].fail(
                "ast: selected scope is not supported by both mechanical "
                "inventories and their count receipts; no scan or rewrite executed",
            )
        if self.output_format != c.Cli.OutputFormats.TEXT:
            return r[t.Cli.ResultValue].fail(
                f"ast: output format {self.output_format!r} is not supported; "
                "no scan or rewrite executed",
            )
        rule_ids = (
            tuple(rule_id.strip() for rule_id in self.rules.split(","))
            if self.rules is not None
            else None
        )
        planned = u.Infra.codemod_rule_plan(self.repository_root, rule_ids=rule_ids)
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        rules = tuple(dict.fromkeys(rule.resource for rule in planned.value.rules))
        if not self.effective_dry_run:
            return self._execute_apply(self.repository_root, rules, rule_ids=rule_ids)
        ast_report = FlextInfraModGateEngine.scan(
            self.repository_root,
            fix=False,
            rule_ids=rule_ids,
        ).unwrap()
        if rule_ids is not None:
            for entry in ast_report.entries:
                cli.display_text(
                    f"ast: {entry.rule_id} {entry.file.as_posix()} "
                    f"[{entry.text!r}] "
                    f"{'actionable' if entry.actionable else 'detection-only'}",
                )
            cli.display_text(
                f"ast: selected {len(planned.value.rules)} exact rule(s) from "
                f"{len(planned.value.rulesets)} provider(s); "
                f"{ast_report.findings} finding(s) "
                f"({ast_report.actionable} actionable); "
                "text phases=0 semantic callbacks=0; corpus=full",
            )
            if ast_report.findings:
                return r[t.Cli.ResultValue].fail(
                    f"{ast_report.findings} selected ast-grep finding(s) "
                    f"({ast_report.actionable} actionable, "
                    f"{ast_report.detection_only} detection-only)",
                )
            return r[t.Cli.ResultValue].ok(value=True)
        text_report = FlextInfraModTextGateEngine.scan(
            self.repository_root,
            fix=False,
            validate_receipts=True,
        ).unwrap()
        for entry in ast_report.entries:
            cli.display_text(
                f"ast: {entry.rule_id} {entry.file.as_posix()} "
                f"[{entry.text!r}] "
                f"{'actionable' if entry.actionable else 'detection-only'}",
            )
        for entry in text_report.entries:
            cli.display_text(
                f"sed: {entry.rule_id} {entry.file.as_posix()}:{entry.line} "
                f"[{entry.text!r}]",
            )
        cli.display_text(
            f"ast: scanned {len(rules)} rule file(s) from "
            f"{len(planned.value.rulesets)} provider(s); "
            f"{ast_report.findings} ast-grep finding(s) "
            f"({ast_report.actionable} actionable), "
            f"{text_report.findings} sed-by-list finding(s) "
            f"({text_report.actionable} actionable)",
        )
        if ast_report.findings or text_report.findings:
            return r[t.Cli.ResultValue].fail(
                f"{ast_report.findings} ast-grep finding(s) "
                f"({ast_report.actionable} actionable, "
                f"{ast_report.detection_only} detection-only) plus "
                f"{text_report.findings} sed-by-list finding(s) "
                f"({text_report.actionable} actionable)",
            )
        cli.display_text("ast: zero findings in both cascades")
        return r[t.Cli.ResultValue].ok(value=True)

    @classmethod
    def _execute_apply(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
        *,
        rule_ids: t.StrSequence | None = None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Drive both mechanical cascades while retaining accepted progress.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        cli.display_text("ast: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(root, rules).unwrap()
        before = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        destination = c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        invocation = destination.parent / destination.stem / uuid4().hex
        if rule_ids is not None:
            receipt = u.Infra.publish_mod_scan_evidence(
                root, before, command=c.Infra.ModScanCommand.SCAN,
                scope=u.Infra.ast_grep_scan_targets(root),
                relative_path=invocation / "before.json",
            ).unwrap()
            cli.display_text(
                f"ast: whole-catalog before evidence={receipt.path} sha256={receipt.sha256}",
            )
        current = (
            FlextInfraModGateEngine.scan(root, fix=False, rule_ids=rule_ids).unwrap()
            if rule_ids is not None
            else before
        )
        outcome = cls._converge(root, current, rule_ids=rule_ids)
        if rule_ids is None:
            return outcome
        after = FlextInfraModGateEngine.scan(root, fix=False)
        if after.failure:
            return r[t.Cli.ResultValue].fail(
                f"ast: whole-catalog after scan failed: {after.error}; "
                f"selected apply: {outcome.error if outcome.failure else 'fixed point'}",
            )
        receipt = u.Infra.publish_mod_scan_evidence(
            root, after.value, command=c.Infra.ModScanCommand.SCAN,
            scope=u.Infra.ast_grep_scan_targets(root),
            relative_path=invocation / "after.json",
        ).unwrap()
        cli.display_text(
            f"ast: whole-catalog after evidence={receipt.path} sha256={receipt.sha256}",
        )
        deltas = FlextInfraRefactorViolationsSweep.rule_deltas(before, after.value)
        cli.display_text(
            f"ast: whole-catalog before={before.findings} "
            f"after={after.value.findings}; "
            "text phases=0 semantic callbacks=0; corpus=full",
        )
        for delta in deltas:
            cli.display_text(
                f"ast: whole-catalog {delta.repository} {delta.rule_id} "
                f"before={delta.before} after={delta.after} "
                f"introduced={delta.introduced}",
            )
        if outcome.failure:
            return outcome
        if any(delta.introduced for delta in deltas):
            return r[t.Cli.ResultValue].fail(
                "ast: selected apply introduced whole-catalog finding occurrences",
            )
        return outcome

    @staticmethod
    def _converge(
        root: Path,
        current: m.Infra.ModScanReport,
        *,
        rule_ids: t.StrSequence | None = None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Drive both mechanical cascades to a verified fixed point.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        seen: set[t.VariadicTuple[t.Quad[str, str, str, str | None]]] = set()
        iteration = 0
        while current.actionable:
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
                    if finding.actionable
                ),
            )
            if fingerprint in seen:
                return r[t.Cli.ResultValue].fail(
                    f"ast apply iteration {iteration} made no progress",
                )
            seen.add(fingerprint)
            cli.display_text(f"ast: apply iteration {iteration}")
            applied = FlextInfraModGateEngine.scan(root, fix=True, rule_ids=rule_ids)
            if rule_ids is None:
                applied.unwrap()
            if applied.failure:
                return r[t.Cli.ResultValue].from_failure(applied)
            scanned = FlextInfraModGateEngine.scan(root, fix=False, rule_ids=rule_ids)
            if rule_ids is None:
                scanned.unwrap()
            if scanned.failure:
                return r[t.Cli.ResultValue].from_failure(scanned)
            current = scanned.value
        if rule_ids is not None:
            if current.findings:
                return r[t.Cli.ResultValue].fail(
                    f"ast: selected fixed point retains {current.findings} finding(s) "
                    f"({current.detection_only} detection-only)",
                )
            cli.display_text("ast: selected AST fixed point verified")
            return r[t.Cli.ResultValue].ok(value=True)
        text = FlextInfraModTextGateEngine.scan(
            root,
            fix=False,
            validate_receipts=True,
        ).unwrap()
        while text.actionable:
            cli.display_text("ast: apply sed-by-list cascade")
            FlextInfraModTextGateEngine.scan(root, fix=True).unwrap()
            text = FlextInfraModTextGateEngine.scan(
                root,
                fix=False,
                validate_receipts=True,
            ).unwrap()
        remaining_ast = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        if remaining_ast.actionable or text.findings:
            return r[t.Cli.ResultValue].fail(
                f"ast fixed point retains findings: {remaining_ast.findings} "
                f"ast-grep ({remaining_ast.actionable} actionable), "
                f"{text.findings} sed-by-list; run make mod for the "
                "semantic phases",
            )
        cli.display_text("ast: mechanical fixed point verified")
        return r[t.Cli.ResultValue].ok(value=True)


__all__: list[str] = ["FlextInfraCodemodAstScan"]
