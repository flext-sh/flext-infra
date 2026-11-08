"""Quality-gate and enforcement fixture test utilities for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import infra
from flext_infra.deps import FlextInfraConfigFixer
from tests import c, m, p, tm
from tests.utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixture

if TYPE_CHECKING:
    from flext_infra.gates.base_gate import FlextInfraGates


class TestsFlextInfraUtilitiesGates:
    """Typed quality-gate execution and enforcement fixture helpers."""

    @staticmethod
    def reject_inaccessible_config_project(tmp_path: Path) -> None:
        """Run the config fixer on an inaccessible project, proving the failure."""
        fixer = FlextInfraConfigFixer(repository_root=tmp_path)
        result = fixer.run(["nonexistent"])

        tm.fail(result)
        tm.that(result.error, has="explicit project path is not accessible")

    @staticmethod
    def gate_context(
        root: Path,
        reports_dir: Path | None = None,
        *,
        fail_fast: bool = c.Infra.CHECK_FAIL_FAST_DEFAULT,
    ) -> p.Infra.GateContext:
        """Build the standard check-mode gate context for one root.

        ``reports_dir`` defaults to the root; a checker run publishes its
        invocation report leaf under it.

        Returns:
            The resulting ``m.Infra.GateContext``.

        """
        return m.Infra.GateContext(
            repository_root=root,
            reports_dir=root if reports_dir is None else reports_dir,
            fail_fast=fail_fast,
        )

    @staticmethod
    def check_gate_asserting(
        gate_class: type[FlextInfraGates],
        tmp_path: Path,
        project_dir: Path,
        *,
        passed: bool,
        issues_len: int,
    ) -> p.Infra.GateExecution:
        """Check one gate once, asserting its pass state and issue count.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        gate = gate_class(tmp_path)
        result = gate.check(
            project_dir,
            TestsFlextInfraUtilitiesGates.gate_context(tmp_path),
        )
        tm.that(result.result.passed, eq=passed)
        tm.that(len(result.issues), eq=issues_len)
        return result

    @staticmethod
    def create_gate_execution(
        gate: str = "lint",
        project: str = "p",
        *,
        passed: bool = True,
        issues: Sequence[p.Infra.Issue] | None = None,
    ) -> p.Infra.GateExecution:
        """Create a typed quality-gate execution fixture.

        The native outcome follows the findings, as a completed tool run
        reports it: findings when issues exist, clean otherwise. A failed
        gate lists every finding in its errors.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        findings = tuple(issues or ())
        return m.Infra.GateExecution.model_validate({
            "result": m.Infra.GateResult(
                gate=gate,
                project=project,
                passed=passed,
                errors=() if passed else tuple(item.formatted for item in findings),
                duration=0.0,
            ),
            "issues": findings,
            "raw_output": "",
            "outcome": (
                c.Infra.ToolOutcome.FINDINGS if findings else c.Infra.ToolOutcome.CLEAN
            ),
        })

    @staticmethod
    def make_issue(
        *,
        file: str = "a.py",
        line: int = 1,
        column: int = 1,
        code: str = "E1",
        message: str = "Error",
    ) -> p.Infra.Issue:
        """Create a typed quality issue fixture.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=file,
            line=line,
            column=column,
            code=code,
            message=message,
            severity="error",
        )

    @staticmethod
    def make_project(
        name: str = "p",
        gates: Mapping[str, p.Infra.GateExecution] | None = None,
    ) -> p.Infra.ProjectResult:
        """Create a typed project-result fixture.

        Returns:
            The resulting ``m.Infra.ProjectResult``.

        """
        resolved_gates: Mapping[str, p.Infra.GateExecution] = (
            gates
            if gates is not None
            else {"lint": TestsFlextInfraUtilitiesGates.create_gate_execution()}
        )
        result: p.Infra.ProjectResult = m.Infra.ProjectResult.model_validate({
            "project": name,
            "gates": resolved_gates,
        })
        return result

    @staticmethod
    def create_gate_context(
        repository_root: Path,
        *,
        reports_dir: Path | None = None,
    ) -> p.Infra.GateContext:
        """Provide the typed test helper `create_gate_context`.

        Returns:
            The resulting ``m.Infra.GateContext``.

        """
        return m.Infra.GateContext(
            repository_root=repository_root,
            reports_dir=reports_dir or repository_root,
        )

    @staticmethod
    def run_gate_check(
        gate_class: type[FlextInfraGates],
        repository_root: Path,
        project_dir: Path,
        *,
        ctx: p.Infra.GateContext | None = None,
        reports_dir: Path | None = None,
    ) -> p.Infra.GateExecution:
        """Provide the typed test helper `run_gate_check`.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        gate = gate_class(repository_root)
        return gate.check(
            project_dir,
            ctx
            or TestsFlextInfraUtilitiesGates.create_gate_context(
                repository_root,
                reports_dir=reports_dir,
            ),
        )

    @staticmethod
    def census_report(
        workspace: Path,
        *,
        rules: Sequence[str],
        kinds: Sequence[str] | None = None,
        options: p.Infra.CensusInput | None = None,
    ) -> p.Infra.WorkspaceReport:
        """Execute one refactor census and unwrap its successful report.

        Returns:
            The resulting ``m.Infra.WorkspaceReport``.

        """
        resolved = m.Infra.CensusInput() if options is None else options
        values = resolved.model_dump(round_trip=True)
        values.update(repository_root=workspace, rules=rules)
        if kinds is not None:
            values["kinds"] = kinds
        TestsFlextInfraUtilitiesToolingFixture.provision_checkout(workspace)
        return tm.ok(infra.census(m.Infra.CensusInput.model_validate(values)))

    @staticmethod
    def census_violations(report: p.Infra.WorkspaceReport) -> list[p.Infra.Violation]:
        """Flatten every per-project violation of one census report.

        Returns:
            The resulting ``list[p.Infra.Violation]``.

        """
        return [
            violation for project in report.projects for violation in project.violations
        ]


__all__: list[str] = ["TestsFlextInfraUtilitiesGates"]
