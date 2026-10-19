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

import sys
from pathlib import Path
from typing import override
from uuid import uuid4

from flext_cli import cli

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codemod import FlextInfraModGateEngine, FlextInfraModTextGateEngine


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
        if not self.effective_dry_run:
            return self._execute_apply(
                self.repository_root,
                tuple(dict.fromkeys(rule.resource for rule in planned.value.rules)),
                rule_ids=rule_ids,
            )
        ast_report = FlextInfraModGateEngine.scan(
            self.repository_root,
            fix=False,
            selection=planned.value,
        ).unwrap()
        if rule_ids is not None:
            return self._selected_scan_outcome(planned.value, ast_report)
        return self._full_scan_outcome(self.repository_root, planned.value, ast_report)

    @staticmethod
    def _selected_scan_outcome(
        planned: m.Infra.CodemodRulePlan,
        ast_report: m.Infra.ModScanReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Render a selected-rules scan and refuse any remaining finding.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        for entry in ast_report.entries:
            cli.display_text(
                f"ast: {entry.rule_id} {entry.file.as_posix()} "
                f"[{entry.text!r}] "
                f"{'actionable' if entry.actionable else 'detection-only'}",
            )
        cli.display_text(
            f"ast: selected {len(planned.rules)} exact rule(s) from "
            f"{len(planned.rulesets)} provider(s); "
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

    @staticmethod
    def _full_scan_outcome(
        root: Path,
        planned: m.Infra.CodemodRulePlan,
        ast_report: m.Infra.ModScanReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Render both full-corpus cascades and refuse any remaining finding.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        text_report = FlextInfraModTextGateEngine.scan(
            root,
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
            f"ast: scanned {len({rule.resource for rule in planned.rules})} rule "
            f"file(s) from "
            f"{len(planned.rulesets)} provider(s); "
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

        Selected failures remain primary over later scan or publication failures.
        Post-apply observations never roll back accepted selected writes.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        cli.display_text("ast: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(root, rules).unwrap()
        before = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        catalog_before = u.Infra.codemod_rule_plan(root).unwrap()
        destination = c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        invocation = destination.parent / destination.stem / uuid4().hex
        if rule_ids is not None:
            receipt = u.Infra.publish_mod_scan_evidence(
                root,
                before,
                publication=m.Infra.ModScanPublication(
                    command=c.Infra.ModScanCommand.SCAN,
                    scope=u.Infra.ast_grep_scan_targets(root),
                    relative_path=invocation / "before.json",
                ),
            ).unwrap()
            cli.display_text(
                f"ast: whole-catalog before evidence={receipt.path} "
                f"sha256={receipt.sha256}",
            )
        current = (
            FlextInfraModGateEngine.scan(root, fix=False, selection=rule_ids).unwrap()
            if rule_ids is not None
            else before
        )
        published_plans: list[m.Infra.CodegenStagedFile] = []
        outcome = cls._converge(
            root, current, rule_ids=rule_ids, published_plans=published_plans
        )
        if rule_ids is None:
            return outcome
        observed = cls._observed_after_evidence(root, invocation, outcome)
        if observed.failure:
            return r[t.Cli.ResultValue].from_failure(observed)
        receipt, after = observed.value
        cli.display_text(
            f"ast: whole-catalog after evidence={receipt.path} sha256={receipt.sha256}",
        )
        try:
            catalog_after = u.Infra.codemod_rule_plan(root)
            cls._require_whole_catalog_correspondence(catalog_before, catalog_after)
            deltas = u.Infra.rule_deltas(
                before,
                after,
                options=m.Infra.RuleDeltaOptions(
                    publication_chain=tuple(published_plans)
                ),
            )
        except ValueError as exc:
            sys.stderr.write(
                f"ast: {'secondary ' if outcome.failure else ''}"
                f"whole-catalog correspondence failure: {exc}; "
                "accepted writes retained; no rollback performed\n"
            )
            return (
                outcome
                if outcome.failure
                else r[t.Cli.ResultValue].fail(str(exc), exception=exc)
            )
        cli.display_text(
            f"ast: whole-catalog before={before.findings} "
            f"after={after.findings}; "
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
                "ast: selected apply introduced whole-catalog finding occurrences; "
                "accepted writes retained; no rollback performed",
            )
        return outcome

    @classmethod
    def _observed_after_evidence(
        cls,
        root: Path,
        invocation: Path,
        outcome: p.Result[t.Cli.ResultValue],
    ) -> p.Result[t.Pair[m.Infra.ModScanEvidenceReceipt, m.Infra.ModScanReport]]:
        """Scan the whole catalog after a selected apply and publish evidence.

        A failed apply keeps its failure primary over any observation or
        publication failure; accepted writes are never rolled back.

        Args:
            root: Governed repository root of the apply.
            invocation: Evidence directory of this apply invocation.
            outcome: Already-converged selected apply outcome.

        Returns:
            The published after evidence with its whole-catalog report, or the
            observation or publication failure.

        """
        result_type = r[t.Pair[m.Infra.ModScanEvidenceReceipt, m.Infra.ModScanReport]]
        after = FlextInfraModGateEngine.scan(root, fix=False)
        if after.failure:
            sys.stderr.write(
                f"ast: {'secondary ' if outcome.failure else ''}"
                f"whole-catalog after scan failure: {after.error}; "
                "accepted writes retained; no rollback performed\n",
            )
            return result_type.from_failure(after)
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            after.value,
            publication=m.Infra.ModScanPublication(
                command=c.Infra.ModScanCommand.SCAN,
                scope=u.Infra.ast_grep_scan_targets(root),
                relative_path=invocation / "after.json",
            ),
        )
        if receipt.failure:
            sys.stderr.write(
                f"ast: {'secondary ' if outcome.failure else ''}"
                f"after evidence publication failure: {receipt.error}; "
                "accepted writes retained; no rollback performed\n",
            )
            return result_type.from_failure(receipt)
        return result_type.ok((receipt.value, after.value))

    @staticmethod
    def _require_whole_catalog_correspondence(
        catalog_before: m.Infra.CodemodRulePlan,
        catalog_after: p.Result[m.Infra.CodemodRulePlan],
    ) -> None:
        """Fail loud when the whole catalog breaks the applied selected identity.

        Raises:
            ValueError: If the whole-catalog observation failed or the rule
                plan changed during the selected apply.

        """
        if catalog_after.failure:
            msg = f"ast: whole-catalog observation failed: {catalog_after.error}"
            raise ValueError(msg)
        if catalog_before != catalog_after.value:
            msg = "ast: whole-catalog identity changed during selected apply"
            raise ValueError(msg)

    @staticmethod
    def _selected_fixed_point(
        current: m.Infra.ModScanReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Reject a selected-cascade fixed point that retains findings.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        if current.findings:
            return r[t.Cli.ResultValue].fail(
                f"ast: selected fixed point retains {current.findings} finding(s) "
                f"({current.detection_only} detection-only)",
            )
        cli.display_text("ast: selected AST fixed point verified")
        return r[t.Cli.ResultValue].ok(value=True)

    @classmethod
    def _converge(
        cls,
        root: Path,
        current: m.Infra.ModScanReport,
        *,
        rule_ids: t.StrSequence | None = None,
        published_plans: t.MutableSequenceOf[m.Infra.CodegenStagedFile] | None = None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Drive both mechanical cascades to a verified fixed point.

        Mechanical quiescence is not acceptance while any finding remains.

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
            applied = FlextInfraModGateEngine.apply_report(
                root,
                current,
                exact_replacements=rule_ids is not None,
                published_plans=published_plans,
            )
            if rule_ids is None:
                applied.unwrap()
            if applied.failure:
                return r[t.Cli.ResultValue].from_failure(applied)
            scanned = FlextInfraModGateEngine.scan(root, fix=False, selection=rule_ids)
            if rule_ids is None:
                scanned.unwrap()
            if scanned.failure:
                return r[t.Cli.ResultValue].from_failure(scanned)
            current = scanned.value
        if rule_ids is not None:
            return cls._selected_fixed_point(current)
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
        if remaining_ast.findings or text.findings:
            return r[t.Cli.ResultValue].fail(
                f"ast fixed point retains findings: {remaining_ast.findings} "
                f"ast-grep ({remaining_ast.actionable} actionable, "
                f"{remaining_ast.detection_only} detection-only), "
                f"{text.findings} sed-by-list; run make mod for the "
                "semantic phases",
            )
        cli.display_text("ast: mechanical fixed point verified")
        return r[t.Cli.ResultValue].ok(value=True)


__all__: list[str] = ["FlextInfraCodemodAstScan"]
