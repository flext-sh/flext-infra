"""Tests for workspace checker gate runners — bandit and markdown.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_tests import tm

from flext_infra import (
    FlextInfraBanditGate,
    FlextInfraMarkdownGate,
    FlextInfraWorkspaceChecker,
)
from tests import m

from ._shared_fixtures import create_checker_project, patch_gate_run

GateClass = type[FlextInfraBanditGate] | type[FlextInfraMarkdownGate]

# Local aliases for backward compatibility
_create_checker_project = create_checker_project
_patch_gate_run = patch_gate_run


def _run_stub(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> SimpleNamespace:
    """Create SimpleNamespace mimicking subprocess output."""
    return SimpleNamespace(
        stdout=stdout,
        stderr=stderr,
        exit_code=returncode,
    )


def _run_failed_gate_check(
    checker: FlextInfraWorkspaceChecker,
    project_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    gate_class: GateClass,
    gate_runner: Callable[[FlextInfraWorkspaceChecker, Path], m.Infra.GateExecution],
    stdout: str = "",
    stderr: str = "",
) -> m.Infra.GateExecution:
    """Helper to run gate check with failure setup."""
    patch_gate_run(
        monkeypatch,
        gate_class,
        stdout=stdout,
        stderr=stderr,
        returncode=1,
    )
    return gate_runner(checker, project_dir)


def _assert_failed_single_issue(result: m.Infra.GateExecution) -> None:
    tm.that(result.result.passed, eq=False)
    tm.that(len(result.issues), eq=1)


class TestWorkspaceCheckerRunBandit:
    def test_run_bandit_no_src_dir(self, tmp_path: Path) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        result = checker._run_bandit(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_bandit_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        json_output = (
            '{"results": [{"filename": "a.py", "line_number": 1,'
            ' "test_id": "B101", "issue_text": "Assert used",'
            ' "issue_severity": "MEDIUM"}]}'
        )
        _patch_gate_run(
            monkeypatch,
            FlextInfraBanditGate,
            stdout=json_output,
            returncode=1,
        )
        result = checker._run_bandit(proj_dir)
        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)

    def test_run_bandit_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        result = _run_failed_gate_check(
            checker,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraBanditGate,
            gate_runner=FlextInfraWorkspaceChecker._run_bandit,
            stdout="invalid json",
        )
        tm.that(result.result.passed, eq=False)


class TestWorkspaceCheckerRunMarkdown:
    def test_run_markdown_no_files(self, tmp_path: Path) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        result = checker._run_markdown(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_markdown_with_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        result = _run_failed_gate_check(
            checker,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraMarkdownGate,
            gate_runner=FlextInfraWorkspaceChecker._run_markdown,
            stdout="README.md:1:1 error MD001 Heading level",
        )
        _assert_failed_single_issue(result)

    def test_run_markdown_with_config(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / ".markdownlint.json").write_text("{}")
        captured_args: list[list[str]] = []

        def _fake_run(
            _self: FlextInfraMarkdownGate,
            cmd: list[str],
            cwd: Path,
            timeout: int = 120,
            env: dict[str, str] | None = None,
        ) -> SimpleNamespace:
            del _self, cwd, timeout, env
            captured_args.append(cmd)
            return _run_stub()

        monkeypatch.setattr(FlextInfraMarkdownGate, "_run", _fake_run)
        checker._run_markdown(proj_dir)
        tm.that("--config" in captured_args[0], eq=True)

    def test_run_markdown_fallback_error_message(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        result = _run_failed_gate_check(
            checker,
            proj_dir,
            monkeypatch,
            gate_class=FlextInfraMarkdownGate,
            gate_runner=FlextInfraWorkspaceChecker._run_markdown,
            stderr="markdownlint failed",
        )
        _assert_failed_single_issue(result)
