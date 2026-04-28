from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectorRuntime, r
from tests.models import m
from tests.protocols import p
from tests.typings import t
from tests.utilities import TestsFlextInfraUtilities as u


class _ReportStub:
    def __init__(self, raw_count: int) -> None:
        self._raw_count = raw_count

    def model_dump(self) -> Mapping[str, t.IntMapping]:
        return {"deptry": {"raw_count": self._raw_count}}


class _DepsStub(p.Infra.DepsService, p.Infra.PipCheckDepsService):
    def __init__(self, project: Path, raw_count: int, pip_exit: int) -> None:
        self._project = project
        self._raw_count = raw_count
        self._pip_exit = pip_exit

    @override
    def discover_project_paths(
        self,
        workspace_root: Path,
        *,
        projects_filter: t.StrSequence | None = None,
    ) -> p.Result[Sequence[Path]]:
        _ = workspace_root
        _ = projects_filter
        return r[Sequence[Path]].ok([self._project])

    @override
    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> p.Result[t.Pair[Sequence[t.Infra.ContainerDict], int]]:
        _ = project_path
        _ = venv_bin
        return r[t.Pair[Sequence[t.Infra.ContainerDict], int]].ok(([], 0))

    @override
    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.Infra.ContainerDict],
    ) -> _ReportStub:
        _ = project_name
        _ = deptry_issues
        return _ReportStub(self._raw_count)

    @override
    def run_pip_check(
        self,
        workspace_root: Path,
        venv_bin: Path,
    ) -> p.Result[tuple[t.StrSequence, int]]:
        _ = workspace_root
        _ = venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))


class _DetectorStub:
    """Minimal stub satisfying p.Infra.DetectorRuntime for report tests."""

    def __init__(self, deps: _DepsStub) -> None:
        self.deps: p.Infra.DepsService = deps
        self.runner: p.Infra.RunnerService = u.Cli
        self.log: p.Logger = u.fetch_logger(__name__)


def _setup(
    tmp_path: Path,
    deps: _DepsStub,
) -> FlextInfraDependencyDetectorRuntime:
    deptry_path = tmp_path / ".venv" / "bin" / "deptry"
    deptry_path.parent.mkdir(parents=True, exist_ok=True)
    deptry_path.write_text("", encoding="utf-8")
    return FlextInfraDependencyDetectorRuntime(
        detector=_DetectorStub(deps),
        workspace_report_factory=m.Infra.WorkspaceDependencyReport,
        dependency_limits_factory=m.Infra.DependencyLimitsInfo,
        pip_check_factory=m.Infra.PipCheckReport,
    )


class TestsFlextInfraDepsDetectorReport:
    def test_run_without_output_flag_writes_default_report(
        self,
        tmp_path: Path,
    ) -> None:
        default_output = (
            tmp_path
            / ".reports"
            / "dependencies"
            / "detect-runtime-dev-latest.json"
        )
        runtime = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        tm.that(
            tm.ok(
                runtime.run(
                    u.Tests.detect_command(
                        tmp_path,
                        no_pip_check=True,
                    ),
                ),
            ),
            eq=True,
        )
        tm.that(default_output.exists(), eq=True)
        payload = tm.ok(u.Cli.json_read(default_output))
        tm.that(u.Cli.json_as_mapping(payload.get("projects")), keys=["proj-a"])

    def test_run_with_output_flag(
        self,
        tmp_path: Path,
    ) -> None:
        custom_output = tmp_path / "custom_report.json"
        runtime = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        tm.that(
            tm.ok(
                runtime.run(
                    u.Tests.detect_command(
                        tmp_path,
                        output=str(custom_output),
                        no_pip_check=True,
                    ),
                ),
            ),
            eq=True,
        )
        tm.that(custom_output.exists(), eq=True)
        payload = tm.ok(u.Cli.json_read(custom_output))
        tm.that(u.Cli.json_as_mapping(payload.get("projects")), keys=["proj-a"])

    def test_run_with_output_to_blocked_path_fails(
        self,
        tmp_path: Path,
    ) -> None:
        blocked_parent = tmp_path / "blocked-output"
        blocked_parent.write_text("not-a-directory", encoding="utf-8")
        blocked_output = blocked_parent / "report.json"

        runtime = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        error = tm.fail(
            runtime.run(
                u.Tests.detect_command(
                    tmp_path,
                    output=str(blocked_output),
                    no_pip_check=True,
                ),
            ),
        )
        tm.that("json_write:" in error or "failed to write report" in error, eq=True)

    def test_run_with_json_write_failure(
        self,
        tmp_path: Path,
    ) -> None:
        blocked_parent = tmp_path / "blocked-parent"
        blocked_parent.write_text("not-a-directory", encoding="utf-8")
        blocked_output = blocked_parent / "report.json"

        runtime = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        error = tm.fail(
            runtime.run(
                u.Tests.detect_command(
                    tmp_path,
                    output=str(blocked_output),
                    no_pip_check=True,
                ),
            ),
        )
        tm.that("json_write:" in error or "failed to write report" in error, eq=True)
