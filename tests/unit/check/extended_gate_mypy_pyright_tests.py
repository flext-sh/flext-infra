"""Tests for workspace checker gate runners — mypy and pyright.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, patch_python_dir_detection

from flext_infra import (
    FlextInfraGate,
    FlextInfraMypyGate,
    FlextInfraPyrightGate,
    FlextInfraWorkspaceChecker,
    t,
)

type GateClass = type[FlextInfraMypyGate | FlextInfraPyrightGate]


def _create_checker_project(
    tmp_path: Path,
    *,
    project_name: str = "p1",
    with_src: bool = False,
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    """Create checker and minimal project structure for gate tests."""
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")
    if with_src:
        src_dir = project_dir / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# code")
    return checker, project_dir


def _patch_gate_run(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: GateClass,
    *,
    stdout: str,
    returncode: int,
) -> None:
    """Patch gate._run() to return fixed CommandOutput."""

    def _stub_run(
        _self: FlextInfraGate,
        _cmd: t.StrSequence,
        _cwd: Path,
        timeout: int = 120,
        env: t.StrMapping | None = None,
    ) -> m.Infra.CommandOutput:
        del _self, _cmd, _cwd, timeout, env
        return m.Infra.CommandOutput(stdout=stdout, stderr="", exit_code=returncode)

    monkeypatch.setattr(gate_class, "_run", _stub_run)


class TestWorkspaceCheckerRunMypy:
    """Test FlextInfraWorkspaceChecker._run_mypy method."""

    def test_run_mypy_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        patch_python_dir_detection(
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
        json_line = (
            '{"file": "a.py", "line": 1, "column": 0,'
            ' "code": "E001", "message": "Error", "severity": "error"}'
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            stdout=json_line,
            returncode=1,
        )
        result = checker._run_mypy(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)


class TestWorkspaceCheckerRunPyright:
    """Test FlextInfraWorkspaceChecker._run_pyright method."""

    def test_run_pyright_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=False,
        )
        result = checker._run_pyright(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_pyright_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        json_output = (
            '{"generalDiagnostics": [{"file": "a.py",'
            ' "range": {"start": {"line": 0, "character": 0}},'
            ' "rule": "E001", "message": "Error", "severity": "error"}]}'
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=True,
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout=json_output,
            returncode=1,
        )
        result = checker._run_pyright(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_pyright_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=True,
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout="invalid json",
            returncode=1,
        )
        result = checker._run_pyright(proj_dir)
        tm.that(not result.result.passed, eq=True)
