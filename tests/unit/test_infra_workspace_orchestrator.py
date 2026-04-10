from __future__ import annotations

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfraOrchestratorService
from tests import c, m, t


def _cmd_out(exit_code: int = 0) -> m.Cli.CommandOutput:
    return m.Cli.CommandOutput(
        stdout="",
        stderr="",
        exit_code=exit_code,
        duration=0.0,
    )


@pytest.fixture
def orchestrator() -> FlextInfraOrchestratorService:
    return FlextInfraOrchestratorService(verb="check")


class TestOrchestratorBasic:
    def test_executes_verb_across_projects(
        self,
        orchestrator: FlextInfraOrchestratorService,
    ) -> None:
        tm.ok(orchestrator.orchestrate(["project-a", "project-b"], "check"), len=2)

    def test_fail_fast(self, orchestrator: FlextInfraOrchestratorService) -> None:
        tm.ok(orchestrator.orchestrate(["p-a", "p-b", "p-c"], "test", fail_fast=True))

    def test_continues_without_fail_fast(
        self,
        orchestrator: FlextInfraOrchestratorService,
    ) -> None:
        tm.ok(orchestrator.orchestrate(["p-a", "p-b"], "test", fail_fast=False), len=2)

    def test_execute_returns_success_for_supported_verb(self) -> None:
        tm.ok(FlextInfraOrchestratorService(verb="check").execute(), eq=True)

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


class TestOrchestratorFailures:
    def test_fail_fast_skips_remaining(
        self,
        orchestrator: FlextInfraOrchestratorService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _run_project_fail(
            self: FlextInfraOrchestratorService,
            project: str,
            verb: str,
            idx: int,
            make_args: t.StrSequence,
        ) -> r[m.Cli.CommandOutput]:
            del self, project, verb, idx, make_args
            return r[m.Cli.CommandOutput].fail("Failed")

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "_run_project",
            _run_project_fail,
        )
        tm.ok(
            orchestrator.orchestrate(["p-a", "p-b", "p-c"], "test", fail_fast=True),
            len=3,
        )

    def test_runner_exception(
        self,
        orchestrator: FlextInfraOrchestratorService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _run_project_raise(
            self: FlextInfraOrchestratorService,
            project: str,
            verb: str,
            idx: int,
            make_args: t.StrSequence,
        ) -> r[m.Cli.CommandOutput]:
            del self, project, verb, idx, make_args
            msg = "Runner failed"
            raise OSError(msg)

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "_run_project",
            _run_project_raise,
        )
        tm.fail(orchestrator.orchestrate(["p-a"], "test"), has="Orchestration failed")

    def test_run_project_failure_with_fail_fast(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        orchestrator = FlextInfraOrchestratorService(verb="test")
        call_count = [0]

        def _run_project(
            self: FlextInfraOrchestratorService,
            project: str,
            verb: str,
            idx: int,
            make_args: t.StrSequence,
        ) -> r[m.Cli.CommandOutput]:
            del self, project, verb, idx, make_args
            call_count[0] += 1
            if call_count[0] == 1:
                return r[m.Cli.CommandOutput].fail("project execution failed")
            return r[m.Cli.CommandOutput].ok(_cmd_out(0))

        tm.ok(
            orchestrator.orchestrate(["p1", "p2", "p3"], "test", fail_fast=True),
            len=3,
        )


class TestOrchestratorGateNormalization:
    def test_maps_python_type_gates_to_go_type_alias(
        self,
        tmp_path_factory: pytest.TempPathFactory,
    ) -> None:
        orchestrator = FlextInfraOrchestratorService(verb="check")
        go_project = tmp_path_factory.mktemp("go-project")
        (go_project / "go.mod").write_text("module example.org/go-project\n")

        normalized = orchestrator._normalize_make_args_for_project(
            project=str(go_project),
            verb=c.Infra.Verbs.CHECK,
            make_args=["CHECK_GATES=lint,pyrefly,mypy,pyright,security"],
        )

        tm.that(
            normalized,
            eq=["CHECK_GATES=lint,type,security"],
        )

    def test_leaves_python_project_gates_unchanged(
        self,
        tmp_path_factory: pytest.TempPathFactory,
    ) -> None:
        orchestrator = FlextInfraOrchestratorService(verb="check")
        python_project = tmp_path_factory.mktemp("python-project")
        (python_project / "pyproject.toml").write_text(
            "[project]\nname='python-project'\n",
        )

        make_args = ["CHECK_GATES=pyrefly"]
        normalized = orchestrator._normalize_make_args_for_project(
            project=str(python_project),
            verb=c.Infra.Verbs.CHECK,
            make_args=make_args,
        )

        tm.that(normalized, eq=make_args)
