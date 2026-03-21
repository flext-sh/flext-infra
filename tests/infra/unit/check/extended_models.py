"""Tests for check model types — _m.Infra.Issue and _ProjectResult.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from ...models import m


class TestCheckIssueFormatted:
    """Test _m.Infra.Issue.formatted property."""

    def test_formatted_with_code(self) -> None:
        issue = m.Infra.Issue(
            file="test.py",
            line=10,
            column=5,
            code="E001",
            message="Error",
            severity="error",
        )
        tm.that(issue.formatted, contains="[E001]")
        tm.that(issue.formatted, contains="test.py:10:5")

    def test_formatted_without_code(self) -> None:
        issue = m.Infra.Issue(
            file="test.py",
            line=10,
            column=5,
            code="",
            message="Error",
            severity="error",
        )
        tm.that(issue.formatted, contains="test.py:10:5")


class TestProjectResultProperties:
    """Test _ProjectResult computed properties."""

    def test_total_errors_multiple_gates(self) -> None:
        gate1 = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        gate2 = m.Infra.GateResult(
            gate="format",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        issue1 = m.Infra.Issue(
            file="a.py",
            line=1,
            column=1,
            code="E1",
            message="m1",
            severity="error",
        )
        issue2 = m.Infra.Issue(
            file="b.py",
            line=2,
            column=1,
            code="E2",
            message="m2",
            severity="error",
        )
        issue3 = m.Infra.Issue(
            file="c.py",
            line=3,
            column=1,
            code="E3",
            message="m3",
            severity="error",
        )
        exec1 = GateExecution(result=gate1, issues=[issue1, issue2], raw_output="")
        exec2 = GateExecution(result=gate2, issues=[issue3], raw_output="")
        project = ProjectResult(project="p", gates={"lint": exec1, "format": exec2})
        tm.that(project.total_errors, eq=3)

    def test_passed_all_gates_pass(self) -> None:
        gate1 = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        gate2 = m.Infra.GateResult(
            gate="format",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        exec1 = GateExecution(result=gate1, issues=[], raw_output="")
        exec2 = GateExecution(result=gate2, issues=[], raw_output="")
        project = ProjectResult(project="p", gates={"lint": exec1, "format": exec2})
        tm.that(project.passed, eq=True)

    def test_passed_one_gate_fails(self) -> None:
        gate1 = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        gate2 = m.Infra.GateResult(
            gate="format",
            project="p",
            passed=False,
            errors=[],
            duration=0.0,
        )
        exec1 = GateExecution(result=gate1, issues=[], raw_output="")
        exec2 = GateExecution(result=gate2, issues=[], raw_output="")
        project = ProjectResult(project="p", gates={"lint": exec1, "format": exec2})
        tm.that(project.passed, eq=False)


class TestWorkspaceCheckerErrorSummary:
    """Test error summary reporting."""

    def test_error_summary_with_multiple_projects_and_gates(self) -> None:
        issue1 = m.Infra.Issue(
            file="a.py",
            line=1,
            column=1,
            code="E1",
            message="m1",
            severity="error",
        )
        issue2 = m.Infra.Issue(
            file="b.py",
            line=2,
            column=1,
            code="E2",
            message="m2",
            severity="error",
        )
        issue3 = m.Infra.Issue(
            file="c.py",
            line=3,
            column=1,
            code="E3",
            message="m3",
            severity="error",
        )
        gate1 = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        gate2 = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        exec1 = GateExecution(result=gate1, issues=[issue1, issue2], raw_output="")
        exec2 = GateExecution(result=gate2, issues=[issue3], raw_output="")
        proj1 = ProjectResult(project="proj1", gates={"lint": exec1})
        proj2 = ProjectResult(project="proj2", gates={"format": exec2})
        tm.that(proj1.total_errors, eq=2)
        tm.that(proj2.total_errors, eq=1)
