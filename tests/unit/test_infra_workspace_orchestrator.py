from __future__ import annotations

from pathlib import Path
from typing import override

import pytest
from flext_tests import r, tm

from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from tests.models import m
from tests.protocols import p
from tests.typings import t


@pytest.fixture
def orchestrator() -> FlextInfraOrchestratorService:
    return FlextInfraOrchestratorService(verb="check")


class TestsFlextInfraInfraWorkspaceOrchestrator:
    class ProjectRunner:
        """Callable project runner fixture for orchestration tests."""

        def __init__(
            self,
            exit_code_by_project: t.MappingKV[str, int],
            *,
            calls: t.MutableSequenceOf[str] | None = None,
            observed_make_args: t.MutableSequenceOf[t.StrSequence] | None = None,
        ) -> None:
            self._exit_code_by_project = exit_code_by_project
            self._calls = calls
            self._observed_make_args = observed_make_args

        def __call__(
            self,
            project: str,
            verb: str,
            _index: int,
            *,
            make_args: t.StrSequence,
        ) -> p.Result[m.Cli.CommandOutput]:
            _ = (verb, _index)
            if self._calls is not None:
                self._calls.append(project)
            if self._observed_make_args is not None:
                self._observed_make_args.append(make_args)
            exit_code = self._exit_code_by_project.get(project, 0)
            return r[m.Cli.CommandOutput].ok(
                TestsFlextInfraInfraWorkspaceOrchestrator._command_output(exit_code)
            )

    class RunnerOrchestrator(FlextInfraOrchestratorService):
        """Orchestrator test double with a typed project runner."""

        def __init__(
            self,
            runner: TestsFlextInfraInfraWorkspaceOrchestrator.ProjectRunner,
            *,
            verb: str = "check",
        ) -> None:
            super().__init__(verb=verb)
            self._runner = runner

        @override
        def _run_project(
            self,
            project: str,
            verb: str,
            _index: int,
            *,
            make_args: t.StrSequence,
        ) -> p.Result[m.Cli.CommandOutput]:
            return self._runner(project, verb, _index, make_args=make_args)

    class PreparedOrchestrator(RunnerOrchestrator):
        """Executable orchestrator test double with resolved projects."""

        def __init__(
            self,
            runner: TestsFlextInfraInfraWorkspaceOrchestrator.ProjectRunner,
            project: m.Infra.ProjectInfo,
        ) -> None:
            super().__init__(runner, verb="check")
            self._project = project

        @override
        def _resolved_projects(
            self,
        ) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
            return r[t.SequenceOf[m.Infra.ProjectInfo]].ok([self._project])

        @staticmethod
        @override
        def _prepare_projects(
            projects: t.SequenceOf[m.Infra.ProjectInfo],
            *,
            workspace_root: Path,
        ) -> p.Result[bool]:
            _ = (projects, workspace_root)
            return r[bool].ok(True)

    @staticmethod
    def _command_output(exit_code: int = 0) -> m.Cli.CommandOutput:
        return m.Cli.CommandOutput(
            stdout="",
            stderr="",
            exit_code=exit_code,
            duration=0.0,
        )

    def test_executes_verb_across_projects(
        self,
    ) -> None:
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"project-a": 0, "project-b": 0}),
        )

        tm.ok(orchestrator.orchestrate(["project-a", "project-b"], "check"), len=2)

    def test_fail_fast(self) -> None:
        calls: t.MutableSequenceOf[str] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 1, "p-b": 1, "p-c": 1}, calls=calls),
        )

        tm.fail(
            orchestrator.orchestrate(["p-a", "p-b", "p-c"], "test", fail_fast=True),
            has="orchestration completed with failures",
        )
        tm.that(calls, eq=["p-a"])

    def test_continues_without_fail_fast(
        self,
    ) -> None:
        calls: t.MutableSequenceOf[str] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 1, "p-b": 0}, calls=calls),
        )

        tm.fail(
            orchestrator.orchestrate(["p-a", "p-b"], "test", fail_fast=False),
            has="orchestration completed with failures",
        )
        tm.that(calls, eq=["p-a", "p-b"])

    def test_orchestrate_fail_fast_reaches_project_make_args(
        self,
    ) -> None:
        observed_make_args: t.MutableSequenceOf[t.StrSequence] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 0}, observed_make_args=observed_make_args),
        )

        tm.ok(orchestrator.orchestrate(["p-a"], "test", fail_fast=True), len=1)
        tm.that(observed_make_args, eq=[("FAIL_FAST=1",)])

    def test_execute_returns_success_for_supported_verb(self) -> None:
        project = m.Infra.ProjectInfo(
            name="flext-demo",
            path=Path.cwd(),
            stack="python",
        )
        orchestrator = self.PreparedOrchestrator(
            self.ProjectRunner({"flext-demo": 0}),
            project,
        )

        tm.ok(orchestrator.execute(), eq=True)

    def test_empty_project_list(
        self,
        orchestrator: FlextInfraOrchestratorService,
    ) -> None:
        tm.ok(orchestrator.orchestrate([], "check"), len=0)

    def test_rejects_unknown_verb(
        self,
        orchestrator: FlextInfraOrchestratorService,
    ) -> None:
        tm.fail(
            orchestrator.orchestrate(["project-a"], "legacy-check"),
            has="unsupported orchestrate verb",
        )
