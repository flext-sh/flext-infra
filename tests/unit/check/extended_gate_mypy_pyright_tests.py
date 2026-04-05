"""Tests for workspace checker gate runners — mypy and pyright.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import create_checker_project, patch_gate_run, patch_python_dir_detection
from tests.unit.check._shared_fixtures import run_gate_check

from flext_infra import FlextInfraMypyGate, FlextInfraPyrightGate


class TestWorkspaceCheckerRunMypy:
    """Test FlextInfraWorkspaceChecker._run_mypy method."""

    def test_run_mypy_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=False,
        )
        result = run_gate_check(FlextInfraMypyGate, workspace_root, proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_mypy_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        json_line = (
            '{"file": "a.py", "line": 1, "column": 0,'
            ' "code": "E001", "message": "Error", "severity": "error"}'
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            stdout=json_line,
            returncode=1,
        )
        result = run_gate_check(FlextInfraMypyGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)


class TestWorkspaceCheckerRunPyright:
    """Test FlextInfraWorkspaceChecker._run_pyright method."""

    def test_run_pyright_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=False,
        )
        result = run_gate_check(FlextInfraPyrightGate, workspace_root, proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_pyright_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
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
        patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout=json_output,
            returncode=1,
        )
        result = run_gate_check(FlextInfraPyrightGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_pyright_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=True,
        )
        patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout="invalid json",
            returncode=1,
        )
        result = run_gate_check(FlextInfraPyrightGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
