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
from flext_infra.codemod.discovery import discover_rules
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path


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
        rules = discover_rules()
        if not rules:
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=True,
                    errors=[],
                    duration=round(time.monotonic() - started, 3),
                ),
                raw_output="no codemod rules discovered",
            )

        issues: list[str] = []
        for rule_path in rules:
            scan = u.Cli.capture(
                [
                    c.Infra.AST_GREP,
                    "scan",
                    "--rule",
                    str(rule_path),
                    "--error",
                    str(project_dir),
                ],
                cwd=project_dir,
            )
            if scan.failure:
                issues.append(
                    f"{rule_path.stem}: scan failed — {scan.error or 'unknown'}"
                )
                continue
            issues.extend(
                f"{rule_path.stem}: {line.strip()}"
                for line in scan.value.splitlines()
                if line.strip()
            )

        passed = len(issues) == 0
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=issues,
                duration=round(time.monotonic() - started, 3),
            ),
            raw_output=f"{len(rules)} rules scanned, {len(issues)} violations",
        )
