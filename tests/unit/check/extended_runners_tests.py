"""Tests for workspace checker runner methods (pyrefly, mypy).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import (
    create_checker_project,
    m,
    patch_gate_run,
    patch_python_dir_detection,
    run_gate_check,
    t,
)

import flext_infra.gates.pyrefly as pyrefly_gate_module
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

    def test_run_pyrefly_limits_check_to_local_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "tests").mkdir()
        (reports_dir / "p1-pyrefly.json").write_text('{"errors": []}')
        captured: t.MutableMappingKV[str, t.MutableSequenceOf[str]] = {}

        def _run(
            _self: FlextInfraPyreflyGate,
            _cmd: t.StrSequence,
            _cwd: Path,
            timeout: int = 120,
            env: t.StrMapping | None = None,
        ) -> m.Cli.CommandOutput:
            del _self, _cwd, timeout, env
            captured["cmd"] = list(_cmd)
            return m.Cli.CommandOutput(stdout="", stderr="", exit_code=0)

        monkeypatch.setattr(FlextInfraPyreflyGate, "_run", _run)
        monkeypatch.setattr(
            pyrefly_gate_module.u.Infra,
            "discover_python_dirs",
            staticmethod(lambda *_args, **_kwargs: ["src", "tests"]),
        )

        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )

        tm.that(result.result.passed, eq=True)
        assert captured["cmd"][0:4] == ["pyrefly", "check", "src", "tests"]

    def test_run_pyrefly_reports_command_failures_without_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        patch_gate_run(
            monkeypatch,
            FlextInfraPyreflyGate,
            stderr="pyrefly crashed",
            returncode=1,
        )
        monkeypatch.setattr(
            pyrefly_gate_module.u.Infra,
            "discover_python_dirs",
            staticmethod(lambda *_args, **_kwargs: ["src"]),
        )

        result = run_gate_check(
            FlextInfraPyreflyGate,
            workspace_root,
            proj_dir,
            reports_dir=reports_dir,
        )

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].code, eq="pyrefly-exec")
        tm.that(result.issues[0].message, contains="pyrefly crashed")


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
