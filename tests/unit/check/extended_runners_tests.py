"""Tests for workspace checker runner methods (pyrefly, mypy).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import patch_python_dir_detection
from tests.unit.check._shared_fixtures import (
    create_checker_project,
    patch_gate_run,
    run_gate_check,
)

from flext_infra import FlextInfraMypyGate, FlextInfraPyreflyGate


class TestRunPyrefly:
    """Test FlextInfraWorkspaceChecker._run_pyrefly method."""

    def test_run_pyrefly_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text('{"errors": []}')
        patch_gate_run(monkeypatch, FlextInfraPyreflyGate, returncode=0)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )
        tm.that(result.result.passed, eq=True)

    def test_run_pyrefly_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text(
            '{"errors": [{"path": "a.py", "line": 1, "column": 0, "name": "E001", "description": "Error", "severity": "error"}]}',
        )
        patch_gate_run(monkeypatch, FlextInfraPyreflyGate, returncode=1)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_pyrefly_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text("invalid json")
        patch_gate_run(monkeypatch, FlextInfraPyreflyGate, returncode=1)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )
        tm.that(not result.result.passed, eq=True)

    def test_run_pyrefly_with_list_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        json_file = reports_dir / "p1-pyrefly.json"
        json_file.write_text(
            '[{"path": "a.py", "line": 1, "column": 0, "name": "E001", "description": "Error", "severity": "error"}]',
        )
        patch_gate_run(monkeypatch, FlextInfraPyreflyGate, returncode=1)
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyreflyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )
        tm.that(len(result.issues), eq=1)


class TestRunMypy:
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
        (proj_dir / "src" / "main.py").write_text("# code")
        json_line = '{"file": "a.py", "line": 1, "column": 0, "code": "E001", "message": "Error", "severity": "error"}'
        patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            stdout=json_line,
            returncode=1,
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(FlextInfraMypyGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_mypy_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        (proj_dir / "src" / "main.py").write_text("# code")
        line1 = '{"file": "a.py", "line": 1, "column": 0, "code": "E001", "message": "Error", "severity": "error"}'
        line2 = '{"file": "b.py", "line": 2, "column": 0, "code": "E002", "message": "Error", "severity": "error"}'
        patch_gate_run(
            monkeypatch,
            FlextInfraMypyGate,
            stdout=f"{line1}\n\n{line2}\n",
            returncode=1,
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraMypyGate,
            has_python_dirs=True,
        )
        result = run_gate_check(FlextInfraMypyGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)
