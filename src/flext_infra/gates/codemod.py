"""Codemod enforcement quality gate.

Reports the findings of the same native scan route ``make mod`` rewrites
from (ADR-028 Decision 18), including its per-source scan cache. Policy
findings block the final check; a scanner that stops early remains a blocking
native failure while its published records are still measured.

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
            project_dir, planned.value, targets, runner=self._runner
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
        # A scanner that stopped early stays a blocking native failure; the
        # complete records it published are still measured as findings.
        failures = tuple(
            m.Infra.Issue(
                file=c.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=failure.split("\n", 1)[0],
                severity="ERROR",
            )
            for failure in scanned.value.native_failures
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
                "verdict": not (failures or findings),
                "issues": (*failures, *findings),
                "started": started,
                "outcome": (
                    c.Infra.ToolOutcome.ERROR
                    if failures
                    else c.Infra.ToolOutcome.FINDINGS
                    if findings
                    else c.Infra.ToolOutcome.CLEAN
                ),
                "raw_output": "\n".join((
                    f"{len(findings)} policy findings; {len(failures)} native failures",
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

    def _scan_projects(
        self,
        scope: tuple[Path, p.Infra.GateContext, Path, frozenset[str]],
        plan: p.Infra.CodemodRulePlan,
        targets: Sequence[str],
        sinks: tuple[list[p.Infra.AstGrepDiagnostic], list[p.Infra.Issue], list[str]],
    ) -> None:
        """Stage and scan each governed project's ruleset until one fails natively.

        Staging runs ast-grep over the projected ruleset; its refusal is a
        native failure of this gate, recorded like a failed scan, not a crash.

        """
        _found, failures, raw_output = sinks
        with tempfile.TemporaryDirectory(prefix="check-codemod-") as directory:
            for index, (project, project_targets) in enumerate(
                u.Infra.project_targets(plan, targets)
            ):
                stage = Path(directory) / str(index)
                try:
                    ruleset = u.Infra.codemod_stage_scan_ruleset(
                        u.Infra.project_plan(plan, project), stage
                    )
                except ValueError as exc:
                    failures.append(
                        m.Infra.Issue(
                            file=str(stage / c.Infra.CODEMOD_CONFIG_FILENAME),
                            line=1,
                            column=1,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=str(exc),
                            severity="ERROR",
                        )
                    )
                    raw_output.append(str(exc))
                    return
                if not self._scan_ruleset(scope, ruleset, project_targets, sinks):
                    return

    def _scan_ruleset(
        self,
        scope: tuple[Path, p.Infra.GateContext, Path, frozenset[str]],
        ruleset: p.Infra.CodemodRuleset,
        targets: Sequence[str],
        sinks: tuple[list[p.Infra.AstGrepDiagnostic], list[p.Infra.Issue], list[str]],
    ) -> bool:
        """Scan one project's staged ruleset and collect its native report.

        Returns:
            Whether the scan completed; a native failure stops the gate.

        """
        project_dir, ctx, binary, nonparticipants = scope
        found, failures, raw_output = sinks
        scan = self._run(
            self._scan_command(ruleset, targets, binary, nonparticipants),
            project_dir,
            ctx,
        )
        outcome = scan.outcome
        raw_output.extend((
            (
                f"{ruleset.provider}: exit={outcome.raw_return_code}, "
                f"timed_out={outcome.timed_out}, signal={outcome.forwarded_signal}"
            ),
            self._raw_output(scan),
        ))
        failure = self._command_error_issue(scan, c.Infra.SG, str(ruleset.config))
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code not in {0, 1}
            or (outcome.raw_return_code == 0 and bool(scan.stderr.strip()))
        ):
            # A scanner that stops early still publishes the matches it emitted
            # to stdout. Measure that payload so the gate reports the true
            # finding total and each rule/file instead of collapsing the whole
            # native report into this one failure.
            found.extend(self._published_scan_findings(scan, ruleset))
            failures.append(failure)
            return False
        # DiagnosticError (exit 1) requires a valid RuleMatch array,
        # matching error count and the exact terminal diagnostic below.
        # Additional native diagnostics make that scan incomplete.
        report, expected_stderr = self._validated_scan_report(scan, ruleset)
        if scan.stderr.strip() != expected_stderr:
            # ast-grep can continue after a traversal error and still return
            # DiagnosticError because another file has an error match.
            # Only the complete terminal diagnostic proves a clean walk.
            failures.append(failure)
            return False
        found.extend(report.root)
        return True

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
