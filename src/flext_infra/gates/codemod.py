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
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run ast-grep scan with cascaded codemod rules."""
        _ = ctx
        started = time.monotonic()
        rules = self._rules(project_dir)
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
                u.Infra.ast_grep_scan_command(rule_path),
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
    def _rules(project_dir: Path) -> t.SequenceOf[Path]:
        """Resolve inherited rules through the public dependency utility."""
        return u.Infra.project_dependency_resource_files(
            project_dir,
            resource_parts=(c.Infra.CODEMOD_RESOURCE_DIRNAME, c.Cli.RULES_DIR_NAME),
            distribution_prefix=c.Infra.PKG_PREFIX_HYPHEN,
            suffix=c.Infra.CODEMOD_RULE_SUFFIX,
        )

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

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Per-rule scans are issued by check(); expose the first rule command."""
        _ = ctx, check_dirs
        rules = self._rules(project_dir)
        if not rules:
            return (c.Infra.SG, c.Infra.SCAN, ".")
        return u.Infra.ast_grep_scan_command(rules[0])

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse a single ast-grep scan result into issues."""
        _ = ctx
        rules = self._rules(project_dir)
        rule_path = rules[0] if rules else project_dir
        issues = self._issues_from_scan(result, rule_path)
        return not issues, issues
