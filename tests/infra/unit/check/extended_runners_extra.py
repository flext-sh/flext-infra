"""Tests for workspace checker runners — pyright, bandit, markdown, go, ruff.

Uses monkeypatch to inject controlled subprocess output.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.check.services import FlextInfraWorkspaceChecker
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.pyright import FlextInfraPyrightGate

from ...models import m

RunCallable = Callable[
    [object, list[str], Path, int, dict[str, str] | None],
    m.Infra.CommandOutput,
]

GateClass = (
    type[FlextInfraPyrightGate]
    | type[FlextInfraBanditGate]
    | type[FlextInfraMarkdownGate]
)


def _stub_run(result: m.Infra.CommandOutput) -> RunCallable:
    """Create a stub _run method returning a fixed result."""

    def _run(
        _self: object,
        cmd: list[str],
        cwd: Path,
        timeout: int = 120,
        env: dict[str, str] | None = None,
    ) -> m.Infra.CommandOutput:
        del _self, cmd, cwd, timeout, env
        return result

    return _run


def _create_checker_project(
    tmp_path: Path,
    *,
    project_name: str = "p1",
    with_src: bool = False,
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")
    if with_src:
        (project_dir / "src").mkdir(exist_ok=True)
    return checker, project_dir


def _patch_gate_run(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: GateClass,
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> None:
    stub_result = m.Infra.CommandOutput(
        stdout=stdout,
        stderr=stderr,
        exit_code=returncode,
    )
    monkeypatch.setattr(
        gate_class,
        "_run",
        _stub_run(stub_result),
    )


def _patch_pyright_python_dirs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    has_python_dirs: bool,
) -> None:
    monkeypatch.setattr(FlextInfraPyrightGate, "_existing_check_dirs", _existing_dirs)
    dirs_with_py = _src_dirs_with_py if has_python_dirs else _no_dirs_with_py
    monkeypatch.setattr(
        FlextInfraPyrightGate, "_dirs_with_py", staticmethod(dirs_with_py)
    )


def _existing_dirs(_self: FlextInfraPyrightGate, _project_dir: Path) -> list[str]:
    del _self, _project_dir
    return ["src"]


def _no_dirs_with_py(_project_dir: Path, _dirs: list[str]) -> list[str]:
    del _project_dir, _dirs
    return []


def _src_dirs_with_py(_project_dir: Path, _dirs: list[str]) -> list[str]:
    del _project_dir, _dirs
    return ["src"]


class TestRunPyright:
    """Test FlextInfraWorkspaceChecker._run_pyright method."""

    def test_run_pyright_no_python_dirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        _patch_pyright_python_dirs(monkeypatch, has_python_dirs=False)
        result = checker._run_pyright(proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_pyright_with_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code")
        json_output = '{"generalDiagnostics": [{"file": "a.py", "range": {"start": {"line": 0, "character": 0}}, "rule": "E001", "message": "Error", "severity": "error"}]}'
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout=json_output,
            returncode=1,
        )
        _patch_pyright_python_dirs(monkeypatch, has_python_dirs=True)
        result = checker._run_pyright(proj_dir)
        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)

    def test_run_pyright_with_invalid_json(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code")
        _patch_gate_run(
            monkeypatch,
            FlextInfraPyrightGate,
            stdout="invalid json",
            returncode=1,
        )
        _patch_pyright_python_dirs(monkeypatch, has_python_dirs=True)
        result = checker._run_pyright(proj_dir)
        tm.that(result.result.passed, eq=False)


class TestRunBandit:
    """Test FlextInfraWorkspaceChecker._run_bandit method."""

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
        json_output = '{"results": [{"filename": "a.py", "line_number": 1, "test_id": "B101", "issue_text": "Assert used", "issue_severity": "MEDIUM"}]}'
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
        _patch_gate_run(
            monkeypatch,
            FlextInfraBanditGate,
            stdout="invalid json",
            returncode=1,
        )
        result = checker._run_bandit(proj_dir)
        tm.that(result.result.passed, eq=False)


class TestRunMarkdown:
    """Test FlextInfraWorkspaceChecker._run_markdown method."""

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
        _patch_gate_run(
            monkeypatch,
            FlextInfraMarkdownGate,
            stdout="README.md:1:1 error MD001 Heading level",
            returncode=1,
        )
        result = checker._run_markdown(proj_dir)
        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)

    def test_run_markdown_fallback_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker, proj_dir = _create_checker_project(tmp_path)
        (proj_dir / "README.md").write_text("# Test")
        _patch_gate_run(
            monkeypatch,
            FlextInfraMarkdownGate,
            stderr="markdownlint failed",
            returncode=1,
        )
        result = checker._run_markdown(proj_dir)
        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
