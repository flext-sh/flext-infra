"""Codemod enforcement quality gate.

Reports the findings of the same native scan route ``make mod`` rewrites
from (ADR-028 Decision 18), including its per-source scan cache. Policy
findings block the final check; native machinery failures remain distinct.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.gates import FlextInfraGates


class FlextInfraGatesCodemod(FlextInfraGates):
    """Report codemod rule findings for the selected repository."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Run ast-grep only on this repository's first-class source roots.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            FileNotFoundError: If ``not targets``.

        """
        targets = u.Infra.ast_grep_scan_targets(project_dir)
        if not targets:
            raise FileNotFoundError(project_dir)
        return self._execute_check_command(
            project_dir,
            ctx,
            targets,
            time.monotonic(),
        )

    @override
    def check_files(
        self,
        files: Sequence[Path],
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Scan every requested file against every elected provider ruleset.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            FileNotFoundError: If ``not path.is_file()``.

        """
        if not files:
            return self.check(project_dir, ctx)
        for path in files:
            if not path.is_file():
                raise FileNotFoundError(path)
        return self._execute_check_command(
            project_dir,
            ctx,
            u.Infra.ast_grep_scan_targets(project_dir, source_files=files),
            time.monotonic(),
        )

    @override
    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
        started: float,
    ) -> p.Infra.GateExecution:
        """Report the findings of the scan route ``make mod`` rewrites from.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            RuntimeError: If codemod rule planning or the native scan failed
                without a diagnostic.

        """
        with u.Infra.codemod_workspace_snapshot(project_dir) as snapshot:
            planned = u.Infra.codemod_rule_plan(snapshot)
        if planned.failure:
            failure = planned.error
            if not failure:
                failure = "codemod rule planning failed without a diagnostic"
                raise RuntimeError(failure)
            return self._failure_gate_execution(project_dir, ctx, failure, started)
        scanned = FlextInfraModGateEngine.native_findings(
            project_dir, planned.value, targets
        )
        if scanned.failure:
            failure = scanned.error
            if not failure:
                failure = "codemod native scan failed without a diagnostic"
                raise RuntimeError(failure)
            return self._failure_gate_execution(project_dir, ctx, failure, started)
        findings = (
            *self._policy_issues(scanned.value.entries),
            *u.Infra.codemod_import_cycle_issues(project_dir),
        )

        # Each finding counts under its declared catalog rule: a partitioned
        # rule's documents fold into the rule they were partitioned from.
        origins = {
            c.Infra.CODEMOD_IMPORT_CYCLE_CODE: c.Infra.CODEMOD_IMPORT_CYCLE_CODE,
            **{rule.id: rule.partition_of or rule.id for rule in planned.value.rules},
        }
        counts = Counter(origins[issue.code] for issue in findings)
        return self._build_gate_execution(
            m.Infra.GateExecutionParams.model_validate({
                "project_dir": project_dir,
                "verdict": not findings,
                "issues": findings,
                "started": started,
                "outcome": (
                    c.Infra.ToolOutcome.FINDINGS
                    if findings
                    else c.Infra.ToolOutcome.CLEAN
                ),
                "raw_output": "\n".join((
                    f"{len(findings)} policy findings",
                    *(
                        f"  {rule_id}: {count}"
                        for rule_id, count in sorted(
                            counts.items(), key=lambda item: (-item[1], item[0])
                        )
                    ),
                )),
            }),
            ctx=ctx,
        )

    def _failure_gate_execution(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        failure: str,
        started: float,
    ) -> p.Infra.GateExecution:
        """Record one native codemod failure as a failed gate execution.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=False,
                issues=(
                    m.Infra.Issue(
                        file=c.PYPROJECT_FILENAME,
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=failure,
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    ),
                ),
                raw_output=failure,
                started=started,
            ),
            ctx,
        )

    @staticmethod
    def _policy_issues(
        found: Sequence[p.Infra.ModScanFinding],
    ) -> Sequence[p.Infra.Issue]:
        """Report every native finding: ast-grep alone decides the match.

        Returns:
            One policy issue per native finding, one-based coordinates.

        """
        return [
            m.Infra.Issue(
                file=str(finding.file),
                line=(start := u.Infra.codemod_finding_start(finding))[0] + 1,
                column=start[1] + 1,
                code=finding.rule_id,
                message=finding.message or "",
                severity=finding.severity,
            )
            for finding in found
        ]


__all__: list[str] = ["FlextInfraGatesCodemod"]
