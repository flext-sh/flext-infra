"""Verify workspace orchestration through its public service interface."""

from __future__ import annotations

from pathlib import Path
from typing import override

import pytest
from flext_tests import r, tm

from flext_infra import c, u
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from tests import m, p, t


@pytest.fixture
def orchestrator() -> FlextInfraOrchestratorService:
    """Provide the canonical workspace orchestrator service."""
    return FlextInfraOrchestratorService(verb="check")


class TestsFlextInfraInfraWorkspaceOrchestrator:
    """Exercise the public workspace orchestration contract."""

    class ProjectRunner:
        """Callable project runner fixture for orchestration tests."""

        def __init__(
            self,
            exit_code_by_project: t.MappingKV[str, int],
            *,
            calls: t.MutableSequenceOf[str] | None = None,
            observed_make_args: t.MutableSequenceOf[t.StrSequence] | None = None,
        ) -> None:
            """Initialize deterministic project outcomes and observations."""
            self._exit_code_by_project = exit_code_by_project
            self._calls = calls
            self._observed_make_args = observed_make_args

        def __call__(
            self, project: str, verb: str, _index: int, *, make_args: t.StrSequence
        ) -> p.Result[p.Cli.CommandOutput]:
            """Return the configured command outcome for one project."""
            _ = (verb, _index)
            if self._calls is not None:
                self._calls.append(project)
            if self._observed_make_args is not None:
                self._observed_make_args.append(make_args)
            exit_code = self._exit_code_by_project.get(project, 0)
            return r[p.Cli.CommandOutput].ok(
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
            """Initialize the orchestrator with a typed project runner."""
            super().__init__(verb=verb)
            self._runner = runner

        @override
        def _run_project(
            self, project: str, verb: str, _index: int, *, make_args: t.StrSequence
        ) -> p.Result[p.Cli.CommandOutput]:
            return self._runner(project, verb, _index, make_args=make_args)

    class PreparedOrchestrator(RunnerOrchestrator):
        """Executable orchestrator test double with resolved projects."""

        def __init__(
            self,
            runner: TestsFlextInfraInfraWorkspaceOrchestrator.ProjectRunner,
            project: p.Infra.ProjectInfo,
        ) -> None:
            """Initialize an executable orchestrator for one resolved project."""
            super().__init__(runner, verb="check")
            self._project = project

        @override
        def _resolved_projects(self) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].ok([self._project])

        @staticmethod
        @override
        def _prepare_projects(
            projects: t.SequenceOf[p.Infra.ProjectInfo], *, workspace_root: Path
        ) -> p.Result[bool]:
            _ = (projects, workspace_root)
            return r[bool].ok(True)

    @staticmethod
    def _command_output(exit_code: int = 0) -> m.Cli.CommandOutput:
        return m.Cli.CommandOutput(
            stdout="", stderr="", exit_code=exit_code, duration=0.0
        )

    def test_executes_verb_across_projects(self) -> None:
        """Execute the requested verb for every supplied project."""
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"project-a": 0, "project-b": 0})
        )

        tm.ok(orchestrator.orchestrate(["project-a", "project-b"], "check"), len=2)

    def test_fail_fast(self) -> None:
        """Stop orchestration after the first failing project when requested."""
        calls: t.MutableSequenceOf[str] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 1, "p-b": 1, "p-c": 1}, calls=calls)
        )

        tm.fail(
            orchestrator.orchestrate(["p-a", "p-b", "p-c"], "test", fail_fast=True),
            has="orchestration completed with failures",
        )
        tm.that(calls, eq=["p-a"])

    def test_continues_without_fail_fast(self) -> None:
        """Continue orchestration after failures when fail-fast is disabled."""
        calls: t.MutableSequenceOf[str] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 1, "p-b": 0}, calls=calls)
        )

        tm.fail(
            orchestrator.orchestrate(["p-a", "p-b"], "test", fail_fast=False),
            has="orchestration completed with failures",
        )
        tm.that(calls, eq=["p-a", "p-b"])

    def test_orchestrate_fail_fast_reaches_project_make_args(self) -> None:
        """Propagate fail-fast intent through public orchestration arguments."""
        observed_make_args: t.MutableSequenceOf[t.StrSequence] = []
        orchestrator = self.RunnerOrchestrator(
            self.ProjectRunner({"p-a": 0}, observed_make_args=observed_make_args)
        )

        tm.ok(orchestrator.orchestrate(["p-a"], "test", fail_fast=True), len=1)
        tm.that(observed_make_args, eq=[("FAIL_FAST=1",)])

    def test_run_project_sanitizes_parent_make_environment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Sanitize inherited make state at the external command boundary."""
        observed_remove_keys: t.MutableSequenceOf[t.StrSequence] = []
        observed_envs: t.MutableSequenceOf[t.StrMapping] = []
        bin_path = tmp_path / "bin"
        mise_shims = tmp_path / "mise-shims"
        system_bin = tmp_path / "system-bin"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv(c.Infra.ORCHESTRATOR_ENV_MISE_SHIMS, str(mise_shims))
        monkeypatch.setenv(
            c.Infra.ORCHESTRATOR_ENV_PATH,
            c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join((
                str(bin_path),
                str(mise_shims),
                str(system_bin),
            )),
        )

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
        ) -> p.Result[int]:
            _ = cmd, cwd, timeout, env
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text("", encoding="utf-8")
            observed_remove_keys.append(tuple(remove_env_keys))
            observed_envs.append(dict(env or {}))
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))
        orchestrator = FlextInfraOrchestratorService(verb="test")

        result = orchestrator.orchestrate(["flext-demo"], "test")

        tm.ok(result, len=1)
        tm.that(observed_remove_keys, eq=[c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS])
        tm.that(observed_envs[0][c.Infra.ORCHESTRATOR_ENV_NO_COLOR], eq="1")
        tm.that(
            observed_envs[0][c.Infra.ORCHESTRATOR_ENV_PATH],
            eq=c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join((
                str(bin_path),
                str(system_bin),
            )),
        )

    def test_execute_returns_success_for_supported_verb(self) -> None:
        """Return success when execute resolves and runs a supported verb."""
        project = m.Infra.ProjectInfo(
            name="flext-demo", path=Path.cwd(), stack="python"
        )
        orchestrator = self.PreparedOrchestrator(
            self.ProjectRunner({"flext-demo": 0}), project
        )

        tm.ok(orchestrator.execute(), eq=True)

    def test_empty_project_list(
        self, orchestrator: FlextInfraOrchestratorService
    ) -> None:
        """Accept an empty project selection as a successful no-op."""
        tm.ok(orchestrator.orchestrate([], "check"), len=0)

    def test_rejects_unknown_verb(
        self, orchestrator: FlextInfraOrchestratorService
    ) -> None:
        """Reject verbs outside the canonical orchestration allowlist."""
        tm.fail(
            orchestrator.orchestrate(["project-a"], "legacy-check"),
            has="unsupported orchestrate verb",
        )
