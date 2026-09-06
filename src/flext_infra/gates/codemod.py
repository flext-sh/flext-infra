"""Codemod enforcement quality gate.

Runs ``ast-grep scan`` with the codemod rules discovered via
``importlib.resources`` cascade (ADR-014). Rules with ``severity: error``
block the build; violations are not warnings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u

from .base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodemodGate(FlextInfraGate):
    """Enforce codemod rules as error gates across every project."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run ast-grep scan with cascaded codemod rules."""
        started = time.monotonic()
        planned = u.Infra.codemod_rule_plan(project_dir)
        if planned.failure:
            failure = planned.error
            if not failure:
                msg = "codemod rule planning failed without a diagnostic"
                raise RuntimeError(msg)
            return self._build_check_gate_execution(
                project_dir,
                passed=False,
                issues=(
                    m.Infra.Issue(
                        file=c.Infra.PYPROJECT_FILENAME,
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=failure,
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    ),
                ),
                raw_output=failure,
                started=started,
            )

        issues: list[m.Infra.Issue] = []
        raw_outputs: list[str] = []
        for ruleset in planned.value.rulesets:
            scan = self._run(
                u.Infra.ast_grep_scan_command(
                    ruleset.config, rule_ids=ruleset.rule_ids
                ),
                project_dir,
                timeout=self._check_timeout(project_dir, ctx),
            )
            issues.extend(self._issues_from_scan(scan, ruleset.provider))
            raw_outputs.extend(
                output
                for output in (scan.stdout.strip(), scan.stderr.strip())
                if output
            )

        summary = (
            f"{len(planned.value.rules)} rules from "
            f"{len(planned.value.rulesets)} providers scanned, "
            f"{len(issues)} violations"
        )
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="\n".join((*raw_outputs, summary)),
            started=started,
        )

    def _issues_from_scan(
        self, scan: p.Cli.CommandOutput, provider: str
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Turn one rule scan into issues; a scanner crash is never a silent pass."""
        if not scan.stdout.strip() and (
            not u.Cli.process_succeeded(scan.outcome) or scan.stderr.strip()
        ):
            failure = (
                "execution failed"
                if not u.Cli.process_succeeded(scan.outcome)
                else "emitted stderr"
            )
            detail = scan.stderr.strip()
            if not detail:
                detail = (
                    "ast-grep returned exit code "
                    f"{scan.outcome.raw_return_code} without diagnostics"
                )
            return (
                m.Infra.Issue(
                    file=c.Infra.PYPROJECT_FILENAME,
                    line=1,
                    column=0,
                    code=self.gate_id,
                    message=f"{provider}: ast-grep {failure} — {detail}",
                    severity=str(c.Infra.GateSeverity.ERROR.value),
                ),
            )
        return tuple(
            m.Infra.Issue(
                file=provider,
                line=1,
                column=0,
                code=self.gate_id,
                message=line.strip(),
                severity=str(c.Infra.GateSeverity.ERROR.value),
            )
            for line in scan.stdout.splitlines()
            if line.strip()
        )

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Per-rule scans are issued by check(); expose the first rule command."""
        _ = ctx, check_dirs
        planned = u.Infra.codemod_rule_plan(project_dir).unwrap()
        ruleset = planned.rulesets[0]
        return u.Infra.ast_grep_scan_command(ruleset.config, rule_ids=ruleset.rule_ids)

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse a single ast-grep scan result into issues."""
        _ = ctx
        planned = u.Infra.codemod_rule_plan(project_dir).unwrap()
        issues = self._issues_from_scan(result, planned.rulesets[0].provider)
        return not issues, issues
