"""Harness scope of the public pytest runner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import config
from tests import c, infra, m, tm, u

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraPytestRunnerHarness:
    """The harness scope runs exactly the gates every other scope deselects."""

    @staticmethod
    def _marker_expression(command: Sequence[str]) -> str:
        return command[command.index("-m", 3) + 1]

    @staticmethod
    @c.Tests.MARK.parametrize("ci_context", [False, True])
    def test_harness_scope_selects_only_the_harness_gates(
        cached_runner_project: Path,
        *,
        ci_context: bool,
    ) -> None:
        """Selection, inventory and suite argv share one harness expression."""
        policy = config.Infra.tooling.tools.pytest
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, ci_context=ci_context
        )
        report = cached_runner_project / runner.reports
        mode = c.Infra.PytestExecutionMode.HARNESS
        others = tuple(
            marker
            for marker in policy.external_gate_markers
            if marker not in policy.harness_gate_markers
        )
        tm.that(runner.harness_markers(), eq=policy.harness_gate_markers)
        tm.that(runner.not_executed_external_gates(execution_mode=mode), eq=others)
        expressions = {
            TestsFlextInfraPytestRunnerHarness._marker_expression(command)
            for command in (
                runner.build_selection_command(
                    report_log=report / "selection.jsonl",
                    manifest_path=report / "selection.json",
                    execution_mode=mode,
                ),
                runner.build_command(report, execution_mode=mode),
            )
        }
        tm.that(expressions, length=1)
        selection, _, deselection = next(iter(expressions)).partition(" and not ")
        tm.that(
            selection.removeprefix("(").removesuffix(")").split(" or "),
            eq=list(policy.harness_gate_markers),
        )
        tm.that(
            deselection.removeprefix("(").removesuffix(")").split(" or ")
            if deselection
            else [],
            eq=list(others),
        )

    @staticmethod
    def test_harness_marker_narrows_to_one_declared_harness_gate(
        cached_runner_project: Path,
    ) -> None:
        """A declared harness marker narrows the scope; any other one fails."""
        policy = config.Infra.tooling.tools.pytest
        narrowed = policy.harness_gate_markers[-1]
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        tm.that(
            runner.model_copy(update={"harness_marker": narrowed}).harness_markers(),
            eq=(narrowed,),
        )
        for marker in (
            policy.slow_marker,
            *(
                marker
                for marker in policy.external_gate_markers
                if marker not in policy.harness_gate_markers
            ),
        ):
            with u.Tests.raises(ValueError, match="harness-gate-marker"):
                runner.model_copy(update={"harness_marker": marker}).harness_markers()

    @staticmethod
    @c.Tests.MARK.parametrize("ci_context", [False, True])
    def test_other_scopes_still_deselect_the_harness_gates(
        cached_runner_project: Path,
        *,
        ci_context: bool,
    ) -> None:
        """Incremental, global and full scopes keep deselecting harness gates."""
        policy = config.Infra.tooling.tools.pytest
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, ci_context=ci_context
        )
        for mode in (
            c.Infra.PytestExecutionMode.INCREMENTAL,
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL,
            c.Infra.PytestExecutionMode.FULL,
        ):
            tm.that(
                runner.not_executed_external_gates(execution_mode=mode),
                has=list(policy.harness_gate_markers),
            )

    @staticmethod
    def test_harness_scope_owns_its_testmon_environment(
        cached_runner_project: Path,
    ) -> None:
        """The harness records never share another marker scope's environment."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        harness = runner.testmon_environment(c.Infra.PytestExecutionMode.HARNESS)
        tm.that(
            harness,
            ne=runner.testmon_environment(c.Infra.PytestExecutionMode.INCREMENTAL),
        )
        tm.that(
            harness,
            ne=runner.testmon_environment(
                c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
            ),
        )

    @staticmethod
    def test_marker_outside_the_harness_scope_fails_at_the_boundary(
        cached_runner_project: Path,
    ) -> None:
        """A marker given to another test scope is refused, never ignored."""
        request = m.Infra.WorkspaceTestsRequest(
            repository_root=cached_runner_project,
            marker=config.Infra.tooling.tools.pytest.harness_gate_markers[0],
        )
        for mode in (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL,
            c.Infra.PytestExecutionMode.FULL,
        ):
            tm.fail(
                infra.workspace_tests(request, execution_mode=mode),
                has="harness scope",
            )

    @staticmethod
    @c.Tests.MARK.slow
    def test_harness_scope_executes_only_the_harness_gates(
        cached_runner_project: Path,
    ) -> None:
        """A real harness run executes its gates and accounts for the rest."""
        policy = config.Infra.tooling.tools.pytest
        others = tuple(
            marker
            for marker in policy.external_gate_markers
            if marker not in policy.harness_gate_markers
        )
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        source = "import pytest\n\n\ndef test_unmarked() -> None:\n    pass\n\n"
        for index, marker in enumerate((*policy.harness_gate_markers, *others)):
            source += (
                f"\n@pytest.mark.{marker}\n"
                f"def test_gate_{index}() -> None:\n    pass\n\n"
            )
        (cached_runner_project / runner.target / "test_gates.py").write_text(
            source,
            encoding="utf-8",
        )

        exit_code = tm.ok(
            runner.execute_global(execution_mode=c.Infra.PytestExecutionMode.HARNESS)
        )

        tm.that(exit_code, eq=0)
        reports_root = cached_runner_project / runner.reports
        tm.that(
            u.Tests.PytestRunner.summary(reports_root),
            has=[
                f"executed={len(policy.harness_gate_markers)}",
                f"not_executed_external_gates={','.join(others)}",
                "failed=0",
                "exit=0",
            ],
        )

    @staticmethod
    def test_project_document_owns_the_gate_markers(
        cached_runner_project: Path,
    ) -> None:
        """A project's harness-gate-markers change its global marker scope.

        The suite clock is elected from the project's tooling document, so
        the marker policy is read from that same document, never from the
        packaged settings of the installed runner.
        """
        policy = config.Infra.tooling.tools.pytest
        declared = policy.external_gate_markers
        tm.that(set(declared) != set(policy.harness_gate_markers), truth=True)
        overlay = cached_runner_project / "config" / "tooling.yaml"
        overlay.parent.mkdir()
        overlay.write_text(
            "Infra:\n  tooling:\n    tools:\n      pytest:\n"
            f"        harness-gate-markers: [ {', '.join(declared)} ]\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        report = cached_runner_project / runner.reports
        mode = c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        tm.that(
            runner.not_executed_external_gates(execution_mode=mode),
            eq=declared,
        )
        expression = TestsFlextInfraPytestRunnerHarness._marker_expression(
            runner.build_command(report, execution_mode=mode)
        )
        tm.that(expression, has=[f"not ({' or '.join(declared)})"])
        tm.that(runner.harness_markers(), eq=declared)

    @staticmethod
    def test_runner_elects_its_tooling_document_once(
        cached_runner_project: Path,
    ) -> None:
        """A run keeps the document elected at its boundary; no mid-run re-read."""
        policy = config.Infra.tooling.tools.pytest
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        elected = runner.tooling
        overlay = cached_runner_project / "config" / "tooling.yaml"
        overlay.parent.mkdir()
        declared = ", ".join(policy.external_gate_markers)
        overlay.write_text(
            "Infra:\n  tooling:\n    tools:\n      pytest:\n"
            f"        harness-gate-markers: [ {declared} ]\n",
            encoding="utf-8",
        )
        mode = c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        tm.that(
            runner.not_executed_external_gates(execution_mode=mode),
            eq=policy.harness_gate_markers,
        )
        tm.that(runner.pytest_policy(), eq=elected.tools.pytest)
        tm.that(runner.tooling is elected, truth=True)

    @staticmethod
    @c.Tests.MARK.slow
    def test_empty_harness_scope_reports_no_tests_collected(
        cached_runner_project: Path,
    ) -> None:
        """A project owning no harness gate is an empty scope, typed, not a crash."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)

        exit_code = tm.ok(
            runner.execute_global(execution_mode=c.Infra.PytestExecutionMode.HARNESS)
        )

        tm.that(exit_code, eq=c.Infra.PytestExitCode.NO_TESTS_COLLECTED)
        tm.that(
            u.Tests.PytestRunner.summary(cached_runner_project / runner.reports),
            has=["executed=0", "failed=0"],
        )
