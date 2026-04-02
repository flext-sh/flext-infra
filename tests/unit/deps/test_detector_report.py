from __future__ import annotations

import types
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

import flext_infra.deps as detector_module
from tests import t


class _ReportStub:
    def __init__(self, raw_count: int) -> None:
        self._raw_count = raw_count

    def model_dump(self) -> Mapping[str, Mapping[str, int]]:
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
        _ = root
        _ = projects_filter
        return r[Sequence[Path]].ok([self._project])

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> r[tuple[Sequence[t.StrMapping], int]]:
        _ = project_path
        _ = venv_bin
        return r[tuple[Sequence[t.StrMapping], int]].ok(([], 0))

    def build_project_report(
        self,
        project_name: str,
        issues: Sequence[t.StrMapping],
    ) -> _ReportStub:
        _ = project_name
        _ = issues
        return _ReportStub(self._raw_count)

    def run_pip_check(self, root: Path, venv_bin: Path) -> r[tuple[t.StrSequence, int]]:
        _ = root
        _ = venv_bin
        return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    deps: _DepsStub,
    *,
    json_service: types.SimpleNamespace | None = None,
    reporting_service: types.SimpleNamespace | None = None,
) -> detector_module.FlextInfraRuntimeDevDependencyDetector:
    def _exists(path: Path) -> bool:
        del path
        return True

    monkeypatch.setattr(Path, "exists", _exists)

    detector = detector_module.FlextInfraRuntimeDevDependencyDetector()
    monkeypatch.setattr(detector, "deps", deps)
    if json_service is not None:
        monkeypatch.setattr(detector, "json", json_service)
    if reporting_service is not None:
        monkeypatch.setattr(detector, "reporting", reporting_service)
    return detector


class TestFlextInfraRuntimeDevDependencyDetectorRunReport:
    def test_run_with_output_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        call_paths: MutableSequence[str] = []

        def _write_json(
            path: Path,
            payload: Mapping[str, Mapping[str, Mapping[str, int]]],
        ) -> r[bool]:
            _ = payload
            call_paths.append(str(path))
            return r[bool].ok(True)

        custom_output = tmp_path / "custom_report.json"
        detector = _setup(
            monkeypatch,
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
            json_service=types.SimpleNamespace(write_json=_write_json),
        )
        tm.ok(
            detector.run([
                "--output",
                str(custom_output),
                "--no-pip-check",
                "--apply",
                "--workspace",
                str(tmp_path),
            ]),
        )
        tm.that(len(call_paths), eq=1)
        tm.that(call_paths[0], eq=str(custom_output))

    def test_run_with_report_directory_creation_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        def _report_dir(root: Path, category: str, name: str) -> Path:
            del root
            del category
            del name
            return tmp_path / "readonly"

        reporting = types.SimpleNamespace(get_report_dir=_report_dir)

        def _mkdir_fail(
            path: Path,
            *,
            parents: bool = False,
            exist_ok: bool = False,
        ) -> None:
            del path
            del parents
            del exist_ok
            msg = "Permission denied"
            raise OSError(msg)

        monkeypatch.setattr(Path, "mkdir", _mkdir_fail)
        detector = _setup(
            monkeypatch,
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
            reporting_service=reporting,
        )
        tm.that(
            tm.fail(
                detector.run([
                    "--no-pip-check",
                    "--apply",
                    "--workspace",
                    str(tmp_path),
                ]),
            ),
            has="failed to create report directory",
        )

    def test_run_with_json_write_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        def _write_json_fail(
            path: Path,
            payload: Mapping[str, Mapping[str, Mapping[str, int]]],
        ) -> r[bool]:
            del path
            del payload
            return r[bool].fail("write failed")

        def _report_dir(root: Path, category: str, name: str) -> Path:
            del root
            del category
            del name
            return tmp_path / "reports"

        def _mkdir_ok(
            path: Path,
            *,
            parents: bool = False,
            exist_ok: bool = False,
        ) -> None:
            del path
            del parents
            del exist_ok

        json_service = types.SimpleNamespace(write_json=_write_json_fail)
        reporting = types.SimpleNamespace(get_report_dir=_report_dir)
        monkeypatch.setattr(Path, "mkdir", _mkdir_ok)
        detector = _setup(
            monkeypatch,
            tmp_path,
            _DepsStub(tmp_path / "proj-a", 0, 0),
            json_service=json_service,
            reporting_service=reporting,
        )
        error = tm.fail(
            detector.run(["--no-pip-check", "--apply", "--workspace", str(tmp_path)]),
        )
        tm.that("write failed" in error or "failed to write report" in error, eq=True)
