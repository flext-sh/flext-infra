"""Tests for workspace checker ruff lint/format and command runner.

Uses monkeypatch to inject controlled subprocess output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import (
    FlextInfraMarkdownGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    FlextInfraUtilitiesSubprocess,
    FlextInfraWorkspaceChecker,
    t,
)
from tests import (
    FlextInfraTestHelpers,
    create_checker_project,
    m,
    patch_gate_run,
    run_command_failure_check,
)


def _create_run_raw_result(
    result: r[SimpleNamespace] | str,
) -> Callable[[t.StrSequence], r[SimpleNamespace]]:
    def _fake_run_raw(_cmd: t.StrSequence, **_kw: str) -> r[SimpleNamespace]:
        del _cmd, _kw
        if isinstance(result, str):
            return r[SimpleNamespace].fail(result)
        return result

    return _fake_run_raw


class TestRunRuffLint:
    """Test FlextInfraWorkspaceChecker._run_ruff_lint method."""

    def test_run_ruff_lint_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = create_checker_project(tmp_path)
        json_output = '[{"filename": "a.py", "location": {"row": 1, "column": 0}, "code": "E001", "message": "Error"}]'
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffLintGate,
            stdout=json_output,
            returncode=1,
        )
        result = checker._run_ruff_lint(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_lint_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffLintGate,
            stdout="invalid json",
            returncode=1,
        )
        result = checker._run_ruff_lint(proj_dir)
        tm.that(not result.result.passed, eq=True)


class TestRunRuffFormat:
    """Test FlextInfraWorkspaceChecker._run_ruff_format method."""

    def test_run_ruff_format_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="  --> a.py:1:1",
            returncode=1,
        )
        result = checker._run_ruff_format(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_format_with_simple_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="a.py",
            returncode=1,
        )
        result = checker._run_ruff_format(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_format_deduplicates_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="--> src/file.py:1:1\n--> src/file.py:1:1\n--> src/other.py:1:1\n",
            returncode=1,
        )
        result = checker._run_ruff_format(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)

    def test_run_ruff_format_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
        (tmp_path / "pyproject.toml").touch()
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="file1.py\n\nfile2.py\n",
            returncode=1,
        )
        result = checker._run_ruff_format(tmp_path)
        tm.that(len(result.issues), gte=1)


class TestRunCommand:
    """Test FlextInfraWorkspaceChecker._run method."""

    def test_run_command_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            FlextInfraUtilitiesSubprocess,
            "run_raw",
            _create_run_raw_result(
                r[SimpleNamespace].ok(
                    SimpleNamespace(stdout="[]", stderr="", exit_code=0),
                ),
            ),
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        result = gate.check(
            tmp_path,
            m.Infra.GateContext(workspace_root=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=True)
        tm.that(result.raw_output, eq="")

    def test_run_command_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        passed, raw_output = run_command_failure_check(
            monkeypatch,
            tmp_path,
            FlextInfraRuffLintGate,
        )
        tm.that(not passed, eq=True)
        tm.that(raw_output, contains="execution failed")


class TestCollectMarkdownFiles:
    """Test FlextInfraWorkspaceChecker._collect_markdown_files method."""

    def test_collect_markdown_files_finds_files(self, tmp_path: Path) -> None:
        proj_dir = FlextInfraTestHelpers.mk_project(tmp_path, "p1")
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / "docs").mkdir()
        (proj_dir / "docs" / "guide.md").write_text("# Guide")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=2)

    def test_collect_markdown_files_excludes_dirs(self, tmp_path: Path) -> None:
        proj_dir = FlextInfraTestHelpers.mk_project(tmp_path, "p1", with_git=True)
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / ".git" / "README.md").write_text("# Git")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=1)
