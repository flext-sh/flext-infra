"""Tests for check model types — _m.Infra.Issue and _ProjectResult.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import m


class TestCheckIssueFormatted:
    """Test _m.Infra.Issue.formatted property."""

    def test_formatted_with_code(self) -> None:
        """Include an available issue code in the formatted location."""
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
        """Format an issue location when no issue code is available."""
        issue = m.Infra.Issue(
            file="test.py",
            line=10,
            column=5,
            code="",
            message="Error",
            severity="error",
        )
        tm.that(issue.formatted, contains="test.py:10:5")


class TestRunCommandGateParsing:
    """Test run-command gate parsing for check workflows."""

    def test_run_command_splits_csv_gate_in_sequence_payload(self) -> None:
        """Normalize a comma-delimited gate payload into ordered gate names."""
        command = m.Infra.RunCommand.model_validate({
            "projects": ["flext-core"],
            "gates": ["lint,format,pyrefly,mypy,pyright,security,markdown"],
        })

        tm.that(
            command.gates,
            eq=("lint", "format", "pyrefly", "mypy", "pyright", "security", "markdown"),
        )

    def test_run_command_resolves_shell_style_file_scope(self) -> None:
        """Resolve each shell-style file selector against the invocation path."""
        command = m.Infra.RunCommand.model_validate({
            "projects": ["flext-infra"],
            "gates": ["mypy"],
            "files": ["src/a.py tests/b.py"],
        })

        tm.that(command.files, eq=("src/a.py", "tests/b.py"))
        tm.that(
            command.file_paths,
            eq=(
                (Path.cwd() / "src/a.py").resolve(),
                (Path.cwd() / "tests/b.py").resolve(),
            ),
        )


class TestProjectResultProperties:
    """Test _ProjectResult computed properties."""

    def test_total_errors_multiple_gates(self) -> None:
        """Count errors contributed by every executed project gate."""
        gate1 = m.Infra.GateResult(
            gate="lint", project="p", passed=True, errors=[], duration=0.0
        )
        gate2 = m.Infra.GateResult(
            gate="format", project="p", passed=True, errors=[], duration=0.0
        )
        issue1 = m.Infra.Issue(
            file="a.py", line=1, column=1, code="E1", message="m1", severity="error"
        )
        issue2 = m.Infra.Issue(
            file="b.py", line=2, column=1, code="E2", message="m2", severity="error"
        )
        issue3 = m.Infra.Issue(
            file="c.py", line=3, column=1, code="E3", message="m3", severity="error"
        )
        exec1 = m.Infra.GateExecution(
            result=gate1, issues=(issue1, issue2), raw_output=""
        )
        exec2 = m.Infra.GateExecution(result=gate2, issues=(issue3,), raw_output="")
        project = m.Infra.ProjectResult(
            project="p", gates={"lint": exec1, "format": exec2}
        )
        tm.that(project.total_errors, eq=3)

    def test_total_errors_ignores_warning_issues(self) -> None:
        """Exclude warning-severity issues from the project error total."""
        gate = m.Infra.GateResult(
            gate="pyright", project="p", passed=True, errors=[], duration=0.0
        )
        warning = m.Infra.Issue(
            file="a.py",
            line=1,
            column=1,
            code="reportPrivateUsage",
            message="warning",
            severity="warning",
        )
        execution = m.Infra.GateExecution(result=gate, issues=(warning,), raw_output="")
        project = m.Infra.ProjectResult(project="p", gates={"pyright": execution})

        tm.that(execution.error_count, eq=0)
        tm.that(project.total_errors, eq=0)

    def test_passed_all_gates_pass(self) -> None:
        """Report a project as passed when every gate passes."""
        gate1 = m.Infra.GateResult(
            gate="lint", project="p", passed=True, errors=[], duration=0.0
        )
        gate2 = m.Infra.GateResult(
            gate="format", project="p", passed=True, errors=[], duration=0.0
        )
        exec1 = m.Infra.GateExecution(result=gate1, issues=(), raw_output="")
        exec2 = m.Infra.GateExecution(result=gate2, issues=(), raw_output="")
        project = m.Infra.ProjectResult(
            project="p", gates={"lint": exec1, "format": exec2}
        )
        tm.that(project.passed, eq=True)

    def test_passed_one_gate_fails(self) -> None:
        """Report a project as failed when any gate fails."""
        gate1 = m.Infra.GateResult(
            gate="lint", project="p", passed=True, errors=[], duration=0.0
        )
        gate2 = m.Infra.GateResult(
            gate="format", project="p", passed=False, errors=[], duration=0.0
        )
        exec1 = m.Infra.GateExecution(result=gate1, issues=(), raw_output="")
        exec2 = m.Infra.GateExecution(result=gate2, issues=(), raw_output="")
        project = m.Infra.ProjectResult(
            project="p", gates={"lint": exec1, "format": exec2}
        )
        tm.that(not project.passed, eq=True)


class TestWorkspaceCheckerErrorSummary:
    """Test error summary reporting."""

    def test_error_summary_with_multiple_projects_and_gates(self) -> None:
        """Summarize issues across multiple projects and gates."""
        issue1 = m.Infra.Issue(
            file="a.py", line=1, column=1, code="E1", message="m1", severity="error"
        )
        issue2 = m.Infra.Issue(
            file="b.py", line=2, column=1, code="E2", message="m2", severity="error"
        )
        issue3 = m.Infra.Issue(
            file="c.py", line=3, column=1, code="E3", message="m3", severity="error"
        )
        gate1 = m.Infra.GateResult(
            gate="lint", project="p", passed=True, errors=[], duration=0.0
        )
        gate2 = m.Infra.GateResult(
            gate="lint", project="p", passed=True, errors=[], duration=0.0
        )
        exec1 = m.Infra.GateExecution(
            result=gate1, issues=(issue1, issue2), raw_output=""
        )
        exec2 = m.Infra.GateExecution(result=gate2, issues=(issue3,), raw_output="")
        proj1 = m.Infra.ProjectResult(project="proj1", gates={"lint": exec1})
        proj2 = m.Infra.ProjectResult(project="proj2", gates={"format": exec2})
        tm.that(proj1.total_errors, eq=2)
        tm.that(proj2.total_errors, eq=1)
