"""Tests for workspace checker runners — pyright, bandit, markdown, go, ruff.

Uses monkeypatch to inject controlled subprocess output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import create_checker_project, patch_gate_run

from flext_infra import (
    FlextInfraBanditGate,
    FlextInfraMarkdownGate,
    FlextInfraPyrightGate,
)

from ._shared_fixtures import patch_python_dir_detection, run_gate_check


class TestRunPyright:
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
        (proj_dir / "src" / "main.py").write_text("# code")
        json_output = '{"generalDiagnostics": [{"file": "a.py", "range": {"start": {"line": 0, "character": 0}}, "rule": "E001", "message": "Error", "severity": "error"}]}'
        patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout=json_output,
            returncode=1,
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=True,
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
        (proj_dir / "src" / "main.py").write_text("# code")
        patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout="invalid json",
            returncode=1,
        )
        patch_python_dir_detection(
            monkeypatch,
            FlextInfraPyrightGate,
            has_python_dirs=True,
        )
        result = run_gate_check(FlextInfraPyrightGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)


class TestRunBandit:
    """Test FlextInfraWorkspaceChecker._run_bandit method."""

    def test_run_bandit_no_src_dir(self, tmp_path: Path) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        result = run_gate_check(FlextInfraBanditGate, workspace_root, proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_bandit_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        json_output = '{"results": [{"filename": "a.py", "line_number": 1, "test_id": "B101", "issue_text": "Assert used", "issue_severity": "MEDIUM"}]}'
        patch_gate_run(
            monkeypatch,
            FlextInfraBanditGate,
            stdout=json_output,
            returncode=1,
        )
        result = run_gate_check(FlextInfraBanditGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_bandit_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path, with_src=True)
        workspace_root = tmp_path
        patch_gate_run(
            monkeypatch,
            FlextInfraBanditGate,
            stdout="invalid json",
            returncode=1,
        )
        result = run_gate_check(FlextInfraBanditGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)


class TestRunMarkdown:
    """Test FlextInfraWorkspaceChecker._run_markdown method."""

    def test_run_markdown_no_files(self, tmp_path: Path) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        result = run_gate_check(FlextInfraMarkdownGate, workspace_root, proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_markdown_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        workspace_root = tmp_path
        (proj_dir / "README.md").write_text("# Test")
        patch_gate_run(
            monkeypatch,
            FlextInfraMarkdownGate,
            stdout="README.md:1:1 error MD001 Heading level",
            returncode=1,
        )
        result = run_gate_check(FlextInfraMarkdownGate, workspace_root, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)
