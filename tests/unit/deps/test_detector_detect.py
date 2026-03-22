from __future__ import annotations

import types
from pathlib import Path
from typing import cast

import pytest
from flext_tests import tm

import flext_infra.deps as detector_module
from flext_core import r
from flext_infra import p
from flext_infra.deps import detector as _det_mod


class _ReportStub:
    def __init__(self, raw_count: int) -> None:
        self._raw_count = raw_count

    def model_dump(self) -> dict[str, dict[str, int]]:
        return {"deptry": {"raw_count": self._raw_count}}


class _DepsStub:
    def __init__(self, project_paths: list[Path]) -> None:
        self.project_paths = project_paths
        self.discovery_failure: str | None = None
        self.deptry_failure: str | None = None
        self.typings_failure: str | None = None

    def discover_project_paths(
        self,
        root: Path,
        *,
        projects_filter: list[str] | None = None,
    ) -> r[list[Path]]:
        _ = root
        _ = projects_filter
        if self.discovery_failure is not None:
            return r[list[Path]].fail(self.discovery_failure)
        return r[list[Path]].ok(self.project_paths)

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> r[tuple[list[dict[str, str]], int]]:
        _ = project_path
        _ = venv_bin
        if self.deptry_failure is not None:
            return r[tuple[list[dict[str, str]], int]].fail(self.deptry_failure)
        return r[tuple[list[dict[str, str]], int]].ok(([], 0))

    def build_project_report(
        self,
        project_name: str,
        issues: list[dict[str, str]],
    ) -> _ReportStub:
        _ = project_name
        _ = issues
        return _ReportStub(0)

    def get_required_typings(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        limits_path: Path,
    ) -> r[types.SimpleNamespace]:
        _ = project_path
        _ = venv_bin
        _ = limits_path
        if self.typings_failure is not None:
            return r[types.SimpleNamespace].fail(self.typings_failure)
        typings = types.SimpleNamespace(to_add=[])

        def _model_dump() -> dict[str, list[str]]:
            return {"to_add": []}

        setattr(typings, "model_dump", _model_dump)
        return r[types.SimpleNamespace].ok(typings)

    def load_dependency_limits(self, limits_path: Path | None = None) -> dict[str, str]:
        _ = limits_path
        return {}


def _patch_deptry_exists(monkeypatch: pytest.MonkeyPatch, exists: bool) -> None:
    def _exists(_: Path) -> bool:
        return exists

    monkeypatch.setattr(Path, "exists", _exists)


def _setup_detector(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    deps: _DepsStub,
    *,
    deptry_exists: bool = True,
) -> detector_module.FlextInfraRuntimeDevDependencyDetector:
    monkeypatch.setattr(
        _det_mod,
        "FlextInfraDependencyDetectionService",
        lambda: deps,
    )
    _patch_deptry_exists(monkeypatch, deptry_exists)
    det = detector_module.FlextInfraRuntimeDevDependencyDetector()
    det.deps = cast("p.Infra.DepsService", deps)
    return det


class TestFlextInfraRuntimeDevDependencyDetectorRunDetect:
    def test_run_with_no_projects(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = _setup_detector(monkeypatch, tmp_path, _DepsStub([])).run([
            "--no-pip-check",
        ])
        tm.that(tm.ok(result), eq=2)

    def test_run_with_deptry_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = _setup_detector(
            monkeypatch,
            tmp_path,
            _DepsStub([tmp_path / "proj-a"]),
            deptry_exists=False,
        ).run(["--no-pip-check"])
        tm.that(tm.ok(result), eq=3)

    def test_run_with_projects_and_deptry(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = _setup_detector(
            monkeypatch,
            tmp_path,
            _DepsStub([tmp_path / "proj-a"]),
        ).run(
            ["--no-pip-check", "--dry-run"],
        )
        tm.that(tm.ok(result), eq=0)
