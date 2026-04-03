"""Tests for workspace checker runner — go vet and go fmt.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_tests import tm
from tests import m, t
from tests.helpers import FlextInfraTestHelpers as h

from flext_infra import FlextInfraGate, FlextInfraWorkspaceChecker

RunCallable = Callable[
    [t.StrSequence, Path, int, t.StrMapping | None],
    m.Infra.CommandOutput,
]


def _as_command_output(
    result: m.Infra.CommandOutput | SimpleNamespace,
) -> m.Infra.CommandOutput:
    if isinstance(result, m.Infra.CommandOutput):
        return result
    return m.Infra.CommandOutput(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )


def _stub_run_seq(
    results: Sequence[m.Infra.CommandOutput | SimpleNamespace],
) -> Callable[..., m.Infra.CommandOutput]:
    idx = [0]

    def _run(
        _self: FlextInfraGate,
        _cmd: t.StrSequence,
        _cwd: Path,
        timeout: int = 120,
        env: t.StrMapping | None = None,
    ) -> m.Infra.CommandOutput:
        del _self, _cmd, _cwd, timeout, env
        i = idx[0]
        idx[0] += 1
        result = results[i] if i < len(results) else results[-1]
        return _as_command_output(result)

    return _run


class TestRunGo:
    def test_run_go_no_go_mod(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
        proj_dir = h.mk_project(tmp_path, "p1")
        result = checker._run_go(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_go_with_vet_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
        proj_dir = h.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test")
        vet = h.stub_run(stdout="main.go:10:5: error message", returncode=1)
        fmt = h.stub_run()
        monkeypatch.setattr(FlextInfraGate, "_run", _stub_run_seq([vet, fmt]))
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)

    def test_run_go_with_format_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
        proj_dir = h.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test")
        (proj_dir / "main.go").write_text("package main")
        vet = h.stub_run()
        fmt = h.stub_run(stdout="main.go", returncode=1)
        monkeypatch.setattr(FlextInfraGate, "_run", _stub_run_seq([vet, fmt]))
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_go_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
        proj_dir = h.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test\n")
        (proj_dir / "main.go").write_text("package main\n")
        vet = h.stub_run()
        fmt = h.stub_run(stdout="src/file.go\n\nsrc/other.go\n", returncode=1)
        monkeypatch.setattr(FlextInfraGate, "_run", _stub_run_seq([vet, fmt]))
        result = checker._run_go(proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)
