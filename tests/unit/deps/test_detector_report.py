from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import override

from flext_tests import tm

from flext_infra import FlextInfraRuntimeDevDependencyDetector
from tests import p, r, t, u


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
    ) -> r[Sequence[Path]]:
        _ = workspace_root
        _ = projects_filter
        return r[Sequence[Path]].ok([self._project])

    @override
    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> r[tuple[Sequence[t.StrMapping], int]]:
        _ = project_path
        _ = venv_bin
        return r[tuple[Sequence[t.StrMapping], int]].ok(([], 0))

    @override
    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.StrMapping],
    ) -> _ReportStub:
        _ = project_name
        _ = deptry_issues
        return _ReportStub(self._raw_count)

    @override
    def run_pip_check(
        self,
        workspace_root: Path,
        venv_bin: Path,
    ) -> r[tuple[t.StrSequence, int]]:
        _ = workspace_root
        _ = venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))


class _ReportingStub(p.Infra.ReportingService):
    def __init__(self, report_dir: Path) -> None:
        self._report_dir = report_dir

    @override
    def get_report_dir(self, workspace_root: Path, scope: str, verb: str) -> Path:
        del workspace_root
        del scope
        del verb
        return self._report_dir


def _setup(
    tmp_path: Path,
    deps: _DepsStub,
    *,
    reporting_service: p.Infra.ReportingService | None = None,
) -> FlextInfraRuntimeDevDependencyDetector:
    return u.Infra.Tests.setup_detector_runtime(
        tmp_path,
        deps,
        reporting=reporting_service,
    )


class TestFlextInfraRuntimeDevDependencyDetectorRunReport:
    def test_run_with_output_flag(
        self,
        tmp_path: Path,
    ) -> None:
        custom_output = tmp_path / "custom_report.json"
        detector = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        tm.that(
            tm.ok(
                detector.run(
                    u.Infra.Tests.detect_command(
                        tmp_path,
                        output=str(custom_output),
                        no_pip_check=True,
                        apply=True,
                    ),
                ),
            ),
            eq=True,
        )
        tm.that(custom_output.exists(), eq=True)
        payload = tm.ok(u.Cli.json_read(custom_output))
        tm.that("projects" in payload, eq=True)

    def test_run_with_report_directory_creation_failure(
        self,
        tmp_path: Path,
    ) -> None:
        blocked_dir = tmp_path / "readonly"
        blocked_dir.write_text("not-a-directory", encoding="utf-8")

        reporting = _ReportingStub(blocked_dir)

        detector = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
            reporting_service=reporting,
        )
        tm.that(
            tm.fail(
                detector.run(
                    u.Infra.Tests.detect_command(
                        tmp_path,
                        no_pip_check=True,
                        apply=True,
                    ),
                ),
            ),
            has="ensure_dir:",
        )

    def test_run_with_json_write_failure(
        self,
        tmp_path: Path,
    ) -> None:
        blocked_parent = tmp_path / "blocked-parent"
        blocked_parent.write_text("not-a-directory", encoding="utf-8")
        blocked_output = blocked_parent / "report.json"

        detector = _setup(
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
        )
        error = tm.fail(
            detector.run(
                u.Infra.Tests.detect_command(
                    tmp_path,
                    output=str(blocked_output),
                    no_pip_check=True,
                    apply=True,
                ),
            ),
        )
        tm.that("json_write:" in error or "failed to write report" in error, eq=True)
