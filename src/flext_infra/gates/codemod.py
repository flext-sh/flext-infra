"""Codemod enforcement quality gate.

Runs ``ast-grep scan`` with the codemod rules discovered via
``importlib.resources`` cascade (ADR-014). Rules with ``severity: error``
block the build; violations are not warnings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.codemod.discovery import discover_rules
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodemodGate(FlextInfraGate):
    """Enforce codemod rules as error gates across every project."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run ast-grep scan with cascaded codemod rules."""
        started = time.monotonic()
        discovered = discover_rules()
        if discovered.failure:
            return self._build_single_issue_result(
                project_dir,
                Path(c.Infra.PYPROJECT_FILENAME),
                discovered.error or "ast-grep rule discovery failed",
                passed=False,
                started=started,
                ctx=ctx,
            )
        rules = discovered.value
        if not rules:
            return self._build_check_gate_execution(
                project_dir,
                passed=True,
                issues=(),
                raw_output="no codemod rules discovered",
                started=started,
            )

        issues: list[m.Infra.Issue] = []
        for rule_path in rules:
            scan = self._run(
                self._scan_command(rule_path, project_dir),
                project_dir,
                timeout=self._check_timeout(project_dir, ctx),
            )
            issues.extend(self._issues_from_scan(scan, rule_path))

        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output=f"{len(rules)} rules scanned, {len(issues)} violations",
            started=started,
        )

    @staticmethod
    def _scan_command(rule_path: Path, project_dir: Path) -> t.StrSequence:
        """Canonical ast-grep invocation for a single packaged rule."""
        return (c.Infra.SG, c.Infra.SCAN, "--rule", str(rule_path), str(project_dir))

    def _issues_from_scan(
        self, scan: p.Cli.CommandOutput, rule_path: Path
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
                        f"{rule_path.stem}: ast-grep execution failed — "
                        f"{scan.stderr or 'unknown error'}"
                    ),
                    severity=str(c.Infra.GateSeverity.ERROR.value),
                ),
            )
        return tuple(
            m.Infra.Issue(
                file=rule_path.stem,
                line=1,
                column=0,
                code=self.gate_id,
                message=line.strip(),
                severity=str(c.Infra.GateSeverity.ERROR.value),
            )
            for line in scan.stdout.splitlines()
            if line.strip()
        )
