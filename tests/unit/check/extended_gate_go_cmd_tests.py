"""Tests for workspace checker — go, command, collect, and run_command methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import (
    FlextInfraGate,
    FlextInfraGoGate,
    FlextInfraMarkdownGate,
    FlextInfraRuffLintGate,
    FlextInfraUtilitiesSubprocess,
    FlextInfraWorkspaceChecker,
    m,
)
from tests import t

from ...helpers import h

GateClass = type[FlextInfraGoGate] | type[FlextInfraRuffLintGate]


def _create_run_raw_result(
    result: r[SimpleNamespace] | str,
) -> Callable[[t.StrSequence], r[SimpleNamespace]]:
    def _fake_run_raw(_cmd: t.StrSequence, **_kw: t.Scalar) -> r[SimpleNamespace]:
        del _cmd, _kw
        if isinstance(result, str):
            return r[SimpleNamespace].fail(result)
        return result

    return _fake_run_raw


def _create_checker_project(
    tmp_path: Path,
    *,
    with_go_mod: bool = False,
    with_main_go: bool = False,
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = h.mk_project(tmp_path, "p1")
    if with_go_mod:
        (project_dir / "go.mod").write_text("module test")
    if with_main_go:
        (project_dir / "main.go").write_text("package main")
    return checker, project_dir


def _patch_go_gate_run_sequence(
    monkeypatch: pytest.MonkeyPatch,
    outputs: Sequence[SimpleNamespace],
) -> None:
    index = {"value": 0}

    def _fake_run(
        _self: FlextInfraGate,
        _cmd: t.StrSequence,
        _cwd: Path,
        timeout: int = 120,
        env: t.StrMapping | None = None,
    ) -> SimpleNamespace:
        del _self, _cmd, _cwd, timeout, env
        current = index["value"]
        index["value"] = current + 1
        if current < len(outputs):
            return outputs[current]
        return outputs[-1]

    monkeypatch.setattr(FlextInfraGate, "_run", _fake_run)


def run_command_failure_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    gate_class: GateClass,
) -> tuple[bool, str]:
    monkeypatch.setattr(
        FlextInfraUtilitiesSubprocess,
        "run_raw",
        _create_run_raw_result("execution failed"),
    )
    gate = gate_class(tmp_path)
    result = gate.check(
        tmp_path,
        m.Infra.GateContext(workspace_root=tmp_path, reports_dir=tmp_path),
    )
    return bool(result.result.passed), str(result.raw_output)


class TestWorkspaceCheckerRunGo:
    """Test FlextInfraWorkspaceChecker._run_go method."""

    def test_run_go_no_go_mod(self, tmp_path: Path) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        result = checker._run_go(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_go_with_vet_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_go_mod=True)
        _patch_go_gate_run_sequence(
            monkeypatch,
            outputs=[
                SimpleNamespace(
                    stdout="main.go:10:5: error message",
                    stderr="",
                    exit_code=1,
                ),
                SimpleNamespace(stdout="", stderr="", exit_code=0),
            ],
        )
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)

    def test_run_go_with_format_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(
            tmp_path,
            with_go_mod=True,
            with_main_go=True,
        )
        _patch_go_gate_run_sequence(
            monkeypatch,
            outputs=[
                SimpleNamespace(stdout="", stderr="", exit_code=0),
                SimpleNamespace(stdout="main.go", stderr="", exit_code=1),
            ],
        )
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_go_fallback_error_message(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_go_mod=True)
        _patch_go_gate_run_sequence(
            monkeypatch,
            outputs=[
                SimpleNamespace(
                    stdout="",
                    stderr="go vet failed",
                    exit_code=1,
                ),
                SimpleNamespace(stdout="", stderr="", exit_code=0),
            ],
        )
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)


class TestWorkspaceCheckerRunCommand:
    """Test FlextInfraWorkspaceChecker._run method."""

    def test_run_command_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "go.mod").write_text("module test")

        monkeypatch.setattr(
            FlextInfraUtilitiesSubprocess,
            "run_raw",
            _create_run_raw_result(
                r[SimpleNamespace].ok(
                    SimpleNamespace(stdout="", stderr="", exit_code=0),
                ),
            ),
        )
        gate = FlextInfraGoGate(tmp_path)
        result = gate.check(
            tmp_path,
            m.Infra.GateContext(workspace_root=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=True)

    def test_run_command_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "go.mod").write_text("module test")

        passed, raw_output = run_command_failure_check(
            monkeypatch,
            tmp_path,
            FlextInfraGoGate,
        )
        tm.that(not passed, eq=True)
        tm.that(raw_output, contains="execution failed")


class TestWorkspaceCheckerCollectMarkdownFiles:
    """Test FlextInfraWorkspaceChecker._collect_markdown_files method."""

    def test_collect_markdown_files_finds_files(self, tmp_path: Path) -> None:
        proj_dir = h.mk_project(tmp_path, "p1")
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / "docs").mkdir()
        (proj_dir / "docs" / "guide.md").write_text("# Guide")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=2)

    def test_collect_markdown_files_excludes_dirs(self, tmp_path: Path) -> None:
        proj_dir = h.mk_project(tmp_path, "p1", with_git=True)
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / ".git" / "README.md").write_text("# Git")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=1)
