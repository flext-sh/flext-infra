"""Tests for workspace checker runner methods (pyrefly, mypy).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence, Callable, Mapping
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_tests import tm

from flext_infra import (
    FlextInfraGate,
    FlextInfraMypyGate,
    FlextInfraPyreflyGate,
    FlextInfraPyrightGate,
    FlextInfraWorkspaceChecker,
)
from tests import patch_python_dir_detection
from tests.helpers import FlextInfraTestHelpers as h

# Local alias for backward compatibility
_patch_python_dir_detection = patch_python_dir_detection

type GateClass = type[
    FlextInfraPyreflyGate | FlextInfraMypyGate | FlextInfraPyrightGate
]


def _as_command_output(result: SimpleNamespace) -> SimpleNamespace:
    if hasattr(result, "exit_code"):
        return result
    return SimpleNamespace(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )


def _stub_run(
    result: SimpleNamespace,
) -> Callable[..., SimpleNamespace]:
    def _run(
        _self: FlextInfraGate,
        cmd: t.StrSequence,
        cwd: Path,
        timeout: int = 120,
        env: t.StrMapping | None = None,
    ) -> SimpleNamespace:
        del _self, cmd, cwd, timeout, env
        return _as_command_output(result)

    return _run


def _create_checker_project(
    tmp_path: Path,
    *,
    project_name: str = "p1",
    with_src: bool = False,
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")
    if with_src:
        src_dir = project_dir / "src"
        src_dir.mkdir(exist_ok=True)
    return checker, project_dir


def _patch_gate_run(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: GateClass,
    result: SimpleNamespace,
) -> None:
    monkeypatch.setattr(gate_class, "_run", _stub_run(result))


class TestRunPyrefly:
    """Test FlextInfraWorkspaceChecker._run_pyrefly method."""

    def test_run_pyrefly_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text('{"errors": []}')
        _patch_gate_run(monkeypatch, FlextInfraPyreflyGate, h.stub_run())
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = checker._run_pyrefly(proj_dir, reports_dir)
        tm.that(result.result.passed, eq=True)

    def test_run_pyrefly_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text(
            '{"errors": [{"path": "a.py", "line": 1, "column": 0, "name": "E001", "description": "Error", "severity": "error"}]}',
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyreflyGate,
            h.stub_run(returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = checker._run_pyrefly(proj_dir, reports_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_pyrefly_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text("invalid json")
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyreflyGate,
            h.stub_run(returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = checker._run_pyrefly(proj_dir, reports_dir)
        tm.that(not result.result.passed, eq=True)

    def test_run_pyrefly_with_error_count_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyreflyGate,
            h.stub_run(stderr="Found 3 errors", returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = checker._run_pyrefly(proj_dir, reports_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=3)

    def test_run_pyrefly_with_list_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text(
            '[{"path": "a.py", "line": 1, "column": 0, "name": "E001", "description": "Error", "severity": "error"}]',
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyreflyGate,
            h.stub_run(returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = checker._run_pyrefly(proj_dir, reports_dir)
        tm.that(len(result.issues), eq=1)


class TestRunMypy:
    """Test FlextInfraWorkspaceChecker._run_mypy method."""

    def test_run_mypy_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=False,
        )
        result = checker._run_mypy(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_mypy_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code")
        json_line = '{"file": "a.py", "line": 1, "column": 0, "code": "E001", "message": "Error", "severity": "error"}'
        _patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            h.stub_run(stdout=json_line, returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        result = checker._run_mypy(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_mypy_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code")
        line1 = '{"file": "a.py", "line": 1, "column": 0, "code": "E001", "message": "Error", "severity": "error"}'
        line2 = '{"file": "b.py", "line": 2, "column": 0, "code": "E002", "message": "Error", "severity": "error"}'
        _patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            h.stub_run(stdout=f"{line1}\n\n{line2}\n", returncode=1),
        )
        _patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        result = checker._run_mypy(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)
