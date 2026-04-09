"""Tests for gate runners — bandit and markdown.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import (
    FlextInfraBanditGate,
    FlextInfraMarkdownGate,
)
from tests import (
    m,
    t,
    u,
)


def _run_failed_gate_check(
    workspace_root: Path,
    project_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    gate_class: t.Infra.Tests.GateClass,
    stdout: str = "",
    stderr: str = "",
) -> m.Infra.GateExecution:
    """Helper to run gate check with failure setup."""
    u.Infra.Tests.patch_gate_run(
        monkeypatch,
        gate_class,
        stdout=stdout,
        stderr=stderr,
        returncode=1,
    )
    return u.Infra.Tests.run_gate_check(gate_class, workspace_root, project_dir)


def _assert_failed_single_issue(result: m.Infra.GateExecution) -> None:
    tm.that(not result.result.passed, eq=True)
    tm.that(len(result.issues), eq=1)


class TestWorkspaceCheckerRunBandit:
    def test_run_bandit_no_src_dir(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        result = u.Infra.Tests.run_gate_check(
            FlextInfraBanditGate,
            tmp_path,
            proj_dir,
        )
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_bandit_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        json_output = (
            '{"results": [{"filename": "a.py", "line_number": 1,'
            ' "test_id": "B101", "issue_text": "Assert used",'
            ' "issue_severity": "MEDIUM"}]}'
        )
        u.Infra.Tests.patch_gate_run(
            monkeypatch,
            FlextInfraBanditGate,
            stdout=json_output,
            returncode=1,
        )
        result = u.Infra.Tests.run_gate_check(
            FlextInfraBanditGate,
            tmp_path,
            proj_dir,
        )
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_bandit_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        result = _run_failed_gate_check(
            tmp_path,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraBanditGate,
            stdout="invalid json",
        )
        tm.that(not result.result.passed, eq=True)


class TestWorkspaceCheckerRunMarkdown:
    def test_run_markdown_no_files(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        result = u.Infra.Tests.run_gate_check(
            FlextInfraMarkdownGate,
            tmp_path,
            proj_dir,
        )
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_markdown_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        result = _run_failed_gate_check(
            tmp_path,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraMarkdownGate,
            stdout="README.md:1:1 error MD001 Heading level",
        )
        _assert_failed_single_issue(result)

    def test_run_markdown_with_config(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / ".markdownlint.json").write_text("{}")
        captured_args: MutableSequence[t.StrSequence] = []

        def _fake_run(
            _self: FlextInfraMarkdownGate,
            cmd: t.StrSequence,
            cwd: Path,
            timeout: int = 120,
            env: t.StrMapping | None = None,
        ) -> m.Cli.CommandOutput:
            del _self, cwd, timeout, env
            captured_args.append(cmd)
            return m.Cli.CommandOutput(stdout="", stderr="", exit_code=0)

        monkeypatch.setattr(FlextInfraMarkdownGate, "_run", _fake_run)
        _ = u.Infra.Tests.run_gate_check(FlextInfraMarkdownGate, tmp_path, proj_dir)
        tm.that(captured_args[0], has="--config")

    def test_run_markdown_without_parseable_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        result = _run_failed_gate_check(
            tmp_path,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraMarkdownGate,
            stderr="markdownlint failed",
        )
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)
        tm.that(result.raw_output, contains="markdownlint failed")
