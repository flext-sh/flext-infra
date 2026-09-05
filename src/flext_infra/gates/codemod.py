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
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodemodGate(FlextInfraGate):
    """Enforce codemod rules as error gates across every project."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = "ast-grep"
    tool_url: ClassVar[str] = "https://ast-grep.github.io/"

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run ast-grep scan with cascaded codemod rules."""
        _ = ctx
        started = time.monotonic()
        planned = u.Infra.codemod_rule_plan(project_dir)
        if planned.failure:
            return self._build_check_gate_execution(
                project_dir,
                passed=False,
                issues=(
                    m.Infra.Issue(
                        file=c.Infra.PYPROJECT_FILENAME,
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=planned.error or "ast-grep rule discovery failed",
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    ),
                ),
                raw_output=planned.error or "ast-grep rule discovery failed",
                started=started,
            )

        issues: list[m.Infra.Issue] = []
        for ruleset in planned.value.rulesets:
            scan = self._run(
                self._scan_command(ruleset, project_dir),
                project_dir,
                timeout=self._check_timeout(project_dir, ctx),
            )
            issues.extend(self._issues_from_scan(scan, ruleset.provider))

        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output=(
                f"{len(planned.value.rules)} rules from "
                f"{len(planned.value.rulesets)} providers scanned, "
                f"{len(issues)} violations"
            ),
            started=started,
        )

    @staticmethod
    def _scan_command(
        ruleset: m.Infra.CodemodRuleset, project_dir: Path
    ) -> t.StrSequence:
        """Canonical ast-grep invocation for one composed provider ruleset."""
        return (
            c.Infra.SG,
            c.Infra.SCAN,
            "--config",
            str(ruleset.config),
            "--filter",
            u.Infra.codemod_rule_filter(ruleset.rule_ids),
            str(project_dir),
        )

    def _issues_from_scan(
        self, scan: p.Cli.CommandOutput, provider: str
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Turn one rule scan into issues; a scanner crash is never a silent pass."""
        if scan.exit_code != 0 and not scan.stdout.strip():
            return (
                m.Infra.Issue(
                    file=c.Infra.PYPROJECT_FILENAME,
                    line=1,
                    column=0,
                    code=self.gate_id,
                    message=(
                        f"{provider}: ast-grep execution failed — "
                        f"{scan.stderr or 'unknown error'}"
                    ),
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
        planned = u.Infra.codemod_rule_plan(project_dir)
        if planned.failure:
            raise ValueError(planned.error or "ast-grep rule discovery failed")
        return self._scan_command(planned.value.rulesets[0], project_dir)

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse a single ast-grep scan result into issues."""
        _ = ctx
        planned = u.Infra.codemod_rule_plan(project_dir)
        if planned.failure:
            raise ValueError(planned.error or "ast-grep rule discovery failed")
        issues = self._issues_from_scan(result, planned.value.rulesets[0].provider)
        return not issues, issues
