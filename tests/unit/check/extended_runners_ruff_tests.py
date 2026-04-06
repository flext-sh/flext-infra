"""Tests for workspace checker ruff lint/format and command runner.

Uses monkeypatch to inject controlled subprocess output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import FlextInfraTestHelpers, m, r, t, u
from tests.unit.check._shared_fixtures import (
    create_checker_project,
    create_fake_run_raw,
    patch_gate_run,
    run_gate_check,
)

from flext_infra import (
    FlextInfraMarkdownGate,
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
)


class TestRunRuffLint:
    """Test FlextInfraWorkspaceChecker._run_ruff_lint method."""

    def test_run_ruff_lint_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        json_output = '[{"filename": "a.py", "location": {"row": 1, "column": 0}, "code": "E001", "message": "Error"}]'
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffLintGate,
            stdout=json_output,
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffLintGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_lint_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffLintGate,
            stdout="invalid json",
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffLintGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)

    def test_run_ruff_lint_forwards_ctx_ruff_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_cmd: list[str] = []

        def _fake_run(
            _self: FlextInfraRuffLintGate,
            cmd: t.StrSequence,
            cwd: Path,
            timeout: int = 0,
            env: t.StrMapping | None = None,
        ) -> m.Cli.CommandOutput:
            _ = cwd, timeout, env
            captured_cmd.extend(cmd)
            return m.Cli.CommandOutput(stdout="[]", stderr="", exit_code=0)

        monkeypatch.setattr(FlextInfraRuffLintGate, "_run", _fake_run)
        gate = FlextInfraRuffLintGate(tmp_path)
        proj_dir = create_checker_project(tmp_path)[1]
        _ = gate.check(
            proj_dir,
            m.Infra.GateContext(
                workspace=tmp_path,
                reports_dir=tmp_path,
                ruff_args=("--select", "E501"),
            ),
        )
        tm.that(captured_cmd, has=["--select", "E501", "--output-format", "json"])


class TestRunRuffFormat:
    """Test FlextInfraWorkspaceChecker._run_ruff_format method."""

    def test_run_ruff_format_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="  --> a.py:1:1",
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffFormatGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_format_with_simple_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="a.py",
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffFormatGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_ruff_format_deduplicates_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = create_checker_project(tmp_path)
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="--> src/file.py:1:1\n--> src/file.py:1:1\n--> src/other.py:1:1\n",
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffFormatGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)

    def test_run_ruff_format_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").touch()
        patch_gate_run(
            monkeypatch,
            FlextInfraRuffFormatGate,
            stdout="file1.py\n\nfile2.py\n",
            returncode=1,
        )
        result = run_gate_check(FlextInfraRuffFormatGate, tmp_path, tmp_path)
        tm.that(len(result.issues), gte=1)


class TestRunPyrightArgs:
    """Test Pyright gate extra argument forwarding."""

    def test_run_pyright_forwards_ctx_args(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_cmd: list[str] = []

        def _fake_run(
            _self: FlextInfraPyrightGate,
            cmd: t.StrSequence,
            cwd: Path,
            timeout: int = 0,
            env: t.StrMapping | None = None,
        ) -> m.Cli.CommandOutput:
            _ = cwd, timeout, env
            captured_cmd.extend(cmd)
            return m.Cli.CommandOutput(
                stdout='{"generalDiagnostics":[]}',
                stderr="",
                exit_code=0,
            )

        monkeypatch.setattr(FlextInfraPyrightGate, "_run", _fake_run)
        gate = FlextInfraPyrightGate(tmp_path)
        proj_dir = create_checker_project(tmp_path, with_src=True)[1]
        (proj_dir / "src" / "demo.py").write_text("value = 1\n", encoding="utf-8")
        _ = gate.check(
            proj_dir,
            m.Infra.GateContext(
                workspace=tmp_path,
                reports_dir=tmp_path,
                pyright_args=("--level", "basic"),
            ),
        )
        tm.that(captured_cmd, has=["--level", "basic", "--outputjson"])


class TestRunCommand:
    """Test FlextInfraWorkspaceChecker._run method."""

    def test_run_command_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            u.Cli,
            "run_raw",
            create_fake_run_raw(
                r[m.Cli.CommandOutput].ok(
                    m.Cli.CommandOutput(stdout="[]", stderr="", exit_code=0),
                ),
            ),
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        result = gate.check(
            tmp_path,
            m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=True)
        tm.that(result.raw_output, eq="")

    def test_run_command_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(u.Cli, "run_raw", create_fake_run_raw("execution failed"))
        gate = FlextInfraRuffLintGate(tmp_path)
        result = gate._run(["echo"], tmp_path)
        tm.that(result.exit_code, eq=1)
        tm.that(result.stderr, contains="execution failed")


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
