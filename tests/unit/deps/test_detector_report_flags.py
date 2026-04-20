from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_tests import tm

import flext_infra as detector_module
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
    ) -> p.Result[Sequence[Path]]:
        del workspace_root
        del projects_filter
        return r[Sequence[Path]].ok([self._project])

    @override
    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> p.Result[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
        del project_path
        del venv_bin
        return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].ok(([], 0))

    @override
    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.Infra.ContainerDict],
    ) -> _ReportStub:
        del project_name
        del deptry_issues
        return _ReportStub(self._raw_count)

    @override
    def run_pip_check(
        self,
        workspace_root: Path,
        venv_bin: Path,
    ) -> p.Result[tuple[t.StrSequence, int]]:
        del workspace_root
        del venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))


def _setup(
    tmp_path: Path,
    deps: _DepsStub,
) -> detector_module.FlextInfraRuntimeDevDependencyDetector:
    return u.Infra.Tests.setup_detector_runtime(
        tmp_path,
        deps,
    )


class TestDetectorReportFlags:
    def test_run_with_issues_and_pip_failure(
        self,
        tmp_path: Path,
    ) -> None:
        detector = _setup(tmp_path, _DepsStub(tmp_path / "proj-a", 5, 1))
        tm.fail(
            detector.run(u.Infra.Tests.detect_command(tmp_path)),
            has="dependency issues detected",
        )

    def test_run_with_no_fail_flag_with_issues(
        self,
        tmp_path: Path,
    ) -> None:
        detector = _setup(tmp_path, _DepsStub(tmp_path / "proj-a", 5, 1))
        tm.that(
            tm.ok(detector.run(u.Infra.Tests.detect_command(tmp_path, no_fail=True))),
            eq=True,
        )

    def test_run_with_json_stdout_flag(
        self,
        tmp_path: Path,
    ) -> None:
        detector = _setup(tmp_path, _DepsStub(tmp_path / "proj-a", 0, 0))
        tm.that(
            tm.ok(
                detector.run(
                    u.Infra.Tests.detect_command(
                        tmp_path,
                        output_format="json",
                        no_pip_check=True,
                    ),
                ),
            ),
            eq=True,
        )
