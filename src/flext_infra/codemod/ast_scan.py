"""Standalone ast engine verb (``refactor ast`` / ``make ast``).

Runs the two mechanical cascades of ``make mod`` (ADR-017): the ast-grep rule
cascade and the sed-by-list cascade from the rules tree (``config/rules/ast``
patterns plus ``config/rules/mod/sed.yaml``) over the full governed corpus.
The verb owns no rule selector (operator ruling D11, 2026-10-31): every run
covers the whole catalog. Rope phases, the enforcement component, and the
lint gates belong to ``mod``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_cli import cli

from flext_infra import c, m, p, r, s, t, u
from flext_infra.codemod import FlextInfraModGateEngine, FlextInfraModTextGateEngine


class FlextInfraCodemodAstScan(s[t.Cli.ResultValue]):
    """Run the ast-grep cascade and the sed-by-list cascade of the rules tree."""

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Report or apply both mechanical cascades of the ast engine.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        # The engines currently own full-corpus inventories and count receipts.
        # Refuse project filters before either engine can scan or publish.
        if self.project_filter is not None:
            return r[t.Cli.ResultValue].fail(
                "ast: selected scope is not supported by both mechanical "
                "inventories and their count receipts; no scan or rewrite executed",
            )
        if self.output_format != c.Cli.OutputFormats.TEXT:
            return r[t.Cli.ResultValue].fail(
                f"ast: output format {self.output_format!r} is not supported; "
                "no scan or rewrite executed",
            )
        with u.Infra.codemod_workspace_snapshot(self.repository_root) as snapshot:
            planned = u.Infra.codemod_rule_plan(snapshot)
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        if not self.effective_dry_run:
            return self._execute_apply(
                self.repository_root,
                u.Infra.codemod_fixture_resources(planned.value),
            )
        ast_report = FlextInfraModGateEngine.scan(
            self.repository_root,
            fix=False,
            selection=planned.value,
        ).unwrap()
        return self._full_scan_outcome(self.repository_root, planned.value, ast_report)

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
        rules: Sequence[Path],
    ) -> p.Result[t.Cli.ResultValue]:
        """Drive both mechanical cascades to a verified fixed point.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        cli.display_text("ast: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(root, rules).unwrap()
        before = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        return cls._converge(root, before)

    @classmethod
    def _converge(
        cls,
        root: Path,
        current: m.Infra.ModScanReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Drive both mechanical cascades to a verified fixed point.

        Mechanical quiescence is not acceptance while any finding remains.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        seen: set[tuple[tuple[str, str, str, str | None], ...]] = set()
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
            FlextInfraModGateEngine.apply_report(root, current).unwrap()
            current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
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
