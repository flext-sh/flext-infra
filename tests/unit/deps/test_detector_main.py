from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_tests import tm

from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraRuntimeDevDependencyDetector,
    main,
)
from tests import m, p, r, t


class _DepsStub(
    p.Infra.DepsService,
    p.Infra.TypingsDepsService,
    p.Infra.PipCheckDepsService,
):
    def __init__(self, project: Path, to_add: t.StrSequence) -> None:
        self._project = project
        self._to_add = to_add

    @override
    def discover_project_paths(
        self,
        workspace_root: Path,
        *,
        projects_filter: t.StrSequence | None = None,
    ) -> p.Result[Sequence[Path]]:
        del workspace_root, projects_filter
        return r[Sequence[Path]].ok([self._project])

    @override
    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> p.Result[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
        del project_path, venv_bin
        return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].ok(([], 0))

    @override
    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.Infra.ContainerDict],
    ) -> m.Infra.ProjectRuntimeReport:
        del project_name, deptry_issues
        return m.Infra.ProjectRuntimeReport(
            deptry=m.Infra.DeptryReport(
                missing=[],
                unused=[],
                transitive=[],
                dev_in_runtime=[],
                raw_count=0,
            ),
        )

    @override
    def get_required_typings(
        self,
        project_path: Path,
        venv_bin: Path,
        limits_path: Path | None = None,
        *,
        include_mypy: bool = True,
    ) -> p.Result[m.Infra.TypingsReport]:
        del project_path, venv_bin, limits_path
        del include_mypy
        return r[m.Infra.TypingsReport].ok(
            m.Infra.TypingsReport(to_add=list(self._to_add)),
        )

    @override
    def load_dependency_limits(
        self,
        limits_path: Path | None = None,
    ) -> t.StrMapping:
        del limits_path
        return {}

    @override
    def run_pip_check(
        self,
        workspace_root: Path,
        venv_bin: Path,
    ) -> p.Result[tuple[t.StrSequence, int]]:
        del workspace_root, venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], 0))


class _RunnerStub(p.Infra.RunnerService):
    def __init__(
        self,
        run_raw: Callable[..., p.Result[m.Cli.CommandOutput]],
    ) -> None:
        self._run_raw = run_raw

    @override
    def run_raw(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> p.Result[m.Cli.CommandOutput]:
        return self._run_raw(
            cmd,
            cwd=cwd or Path.cwd(),
            timeout=timeout or 0,
            env=env or {},
        )


class _ReportingStub(p.Infra.ReportingService):
    @override
    def get_report_dir(self, workspace_root: Path, scope: str, verb: str) -> Path:
        del scope
        return workspace_root / ".reports" / verb


def _setup_typings_detector(
    tmp_path: Path,
    to_add: t.StrSequence,
    run_raw_result: p.Result[m.Cli.CommandOutput],
) -> tuple[
    FlextInfraRuntimeDevDependencyDetector,
    Sequence[t.StrSequence],
]:
    project_path = tmp_path / "proj-a"
    (project_path / "src").mkdir(parents=True)
    deptry_path = tmp_path / ".venv" / "bin" / "deptry"
    deptry_path.parent.mkdir(parents=True)
    deptry_path.write_text("", encoding="utf-8")
    captured_commands: MutableSequence[t.StrSequence] = []

    def _run_raw(
        cmd: t.StrSequence,
        *,
        cwd: Path,
        timeout: int,
        env: t.StrMapping,
    ) -> p.Result[m.Cli.CommandOutput]:
        del cwd, timeout, env
        captured_commands.append(cmd)
        return run_raw_result

    detector = FlextInfraRuntimeDevDependencyDetector()
    detector.deps = _DepsStub(project_path, to_add)
    detector.runner = _RunnerStub(_run_raw)
    detector.reporting = _ReportingStub()
    return detector, captured_commands


class TestFlextInfraRuntimeDevDependencyDetectorRunTypings:
    def test_run_with_apply_typings_success(
        self,
        tmp_path: Path,
    ) -> None:
        run_result = r[m.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(stdout="", stderr="", exit_code=0)
        )
        detector, calls = _setup_typings_detector(
            tmp_path,
            ["types-requests"],
            run_result,
        )
        params = FlextInfraModelsDeps.DetectCommand(
            workspace=str(tmp_path),
            typings=True,
            apply_typings=True,
            apply=True,
            no_pip_check=True,
        )
        tm.ok(detector.run(params))
        tm.that(len(calls), eq=1)

    def test_run_with_apply_typings_multiple_packages(
        self,
        tmp_path: Path,
    ) -> None:
        run_result = r[m.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(stdout="", stderr="", exit_code=0)
        )
        detector, calls = _setup_typings_detector(
            tmp_path,
            ["types-requests", "types-python-dateutil", "types-pyyaml"],
            run_result,
        )
        params = FlextInfraModelsDeps.DetectCommand(
            workspace=str(tmp_path),
            typings=True,
            apply_typings=True,
            apply=True,
            no_pip_check=True,
        )
        tm.ok(detector.run(params))
        tm.that(len(calls), eq=3)

    def test_run_with_apply_typings_poetry_add_failure(
        self,
        tmp_path: Path,
    ) -> None:
        run_result = r[m.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(stdout="", stderr="", exit_code=1)
        )
        detector, _ = _setup_typings_detector(
            tmp_path,
            ["types-requests"],
            run_result,
        )
        params = FlextInfraModelsDeps.DetectCommand(
            workspace=str(tmp_path),
            typings=True,
            apply_typings=True,
            no_pip_check=True,
        )
        tm.ok(detector.run(params))

    def test_run_with_apply_typings_poetry_add_failure_result(
        self,
        tmp_path: Path,
    ) -> None:
        detector, _ = _setup_typings_detector(
            tmp_path,
            ["types-requests"],
            r[m.Cli.CommandOutput].fail("poetry add failed"),
        )
        params = FlextInfraModelsDeps.DetectCommand(
            workspace=str(tmp_path),
            typings=True,
            apply_typings=True,
            no_pip_check=True,
        )
        tm.ok(detector.run(params))


class TestMainFunction:
    def test_main_returns_failure_code_on_run_failure(
        self,
    ) -> None:
        tm.that(
            main([
                "deps",
                "detect",
                "--workspace",
                "/nonexistent/path",
                "--no-pip-check",
            ]),
            eq=1,
        )
