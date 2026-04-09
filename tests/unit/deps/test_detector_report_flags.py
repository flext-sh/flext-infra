from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as detector_module
from flext_core import r
from tests import t


class _ReportStub:
    def __init__(self, raw_count: int) -> None:
        self._raw_count = raw_count

    def model_dump(self) -> Mapping[str, t.IntMapping]:
        return {"deptry": {"raw_count": self._raw_count}}


class _DepsStub:
    def __init__(self, project: Path, raw_count: int, pip_exit: int) -> None:
        self._project = project
        self._raw_count = raw_count
        self._pip_exit = pip_exit

    def discover_project_paths(
        self,
        root: Path,
        *,
        projects_filter: t.StrSequence | None = None,
    ) -> r[Sequence[Path]]:
        del root
        del projects_filter
        return r[Sequence[Path]].ok([self._project])

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> r[tuple[Sequence[t.StrMapping], int]]:
        del project_path
        del venv_bin
        return r[tuple[Sequence[t.StrMapping], int]].ok(([], 0))

    def build_project_report(
        self,
        project_name: str,
        issues: Sequence[t.StrMapping],
    ) -> _ReportStub:
        del project_name
        del issues
        return _ReportStub(self._raw_count)

    def run_pip_check(self, root: Path, venv_bin: Path) -> r[tuple[t.StrSequence, int]]:
        del root
        del venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    deps: _DepsStub,
) -> detector_module.FlextInfraRuntimeDevDependencyDetector:
    def _exists(path: Path) -> bool:
        del path
        return True

    return detector_module.FlextInfraRuntimeDevDependencyDetector()


class TestDetectorReportFlags:
    def test_run_with_issues_and_pip_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        detector = _setup(monkeypatch, tmp_path, _DepsStub(tmp_path / "proj-a", 5, 1))
        tm.that(tm.ok(detector.run(["--dry-run", "--workspace", str(tmp_path)])), eq=1)

    def test_run_with_no_fail_flag_with_issues(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        detector = _setup(monkeypatch, tmp_path, _DepsStub(tmp_path / "proj-a", 5, 1))
        tm.that(
            tm.ok(
                detector.run(["--no-fail", "--dry-run", "--workspace", str(tmp_path)]),
            ),
            eq=0,
        )

    def test_run_with_json_stdout_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        detector = _setup(monkeypatch, tmp_path, _DepsStub(tmp_path / "proj-a", 0, 0))
        tm.that(
            tm.ok(
                detector.run([
                    "--format",
                    "json",
                    "--no-pip-check",
                    "--workspace",
                    str(tmp_path),
                ]),
            ),
            eq=0,
        )
