"""Shared fixtures and helpers for workspace checker tests.

Single Source of Truth for common test patterns and mocks.
Eliminates duplication across extended_project_runners and extended_runners_ruff.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from flext_core import r, t
from flext_infra import m as infra_models
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
from tests.infra import m, t

from ...helpers import h
from ...models import m

type GateClass = type[
    FlextInfraRuffLintGate
    | FlextInfraRuffFormatGate
    | FlextInfraBanditGate
    | FlextInfraMarkdownGate
]


def create_gate_execution(
    gate: str = "lint",
    project: str = "p",
    *,
    passed: bool = True,
    issues: list[m.Infra.Issue] | None = None,
) -> GateExecution:
    """Factory for GateExecution with standard defaults.

    Single Responsibility: Create consistent test execution results.
    """
    return GateExecution(
        result=m.Infra.GateResult(
            gate=gate,
            project=project,
            passed=passed,
            errors=[],
            duration=0.0,
        ),
        issues=issues or [],
        raw_output="",
    )


def create_checker_project(
    tmp_path: Path,
    *,
    project_name: str = "p1",
    with_src: bool = False,
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    """Factory for checker + project directory pair.

    Single Responsibility: Encapsulate shared project setup logic.
    Eliminates duplication of: FlextInfraWorkspaceChecker creation + project initialization.
    """
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = h.mk_project(tmp_path, project_name)
    if with_src:
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
    return checker, project_dir


def patch_gate_run(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: GateClass,
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int,
) -> None:
    """Patch gate._run() with controlled output.

    Single Responsibility: Encapsulate monkeypatch setup for gate mocking.
    Eliminates duplication of: gate._run stub creation + monkeypatch.setattr() call.
    """

    def _as_command_output(
        output: m.Infra.CommandOutput | SimpleNamespace,
    ) -> m.Infra.CommandOutput:
        """Convert SimpleNamespace or CommandOutput to CommandOutput."""
        if isinstance(output, m.Infra.CommandOutput):
            return output
        # Handle SimpleNamespace from h.stub_run
        return m.Infra.CommandOutput(
            stdout=getattr(output, "stdout", ""),
            stderr=getattr(output, "stderr", ""),
            exit_code=getattr(output, "exit_code", getattr(output, "returncode", 0)),
        )

    def _stub_run(
        result: m.Infra.CommandOutput | SimpleNamespace,
    ) -> Callable[
        [object, list[str], Path, int, dict[str, str] | None],
        m.Infra.CommandOutput,
    ]:
        """Create stub returning fixed result or SimpleNamespace."""

        def _run(
            _self: object,
            _cmd: list[str],
            _cwd: Path,
            _timeout: int = 120,
            _env: dict[str, str] | None = None,
        ) -> m.Infra.CommandOutput:
            del _self, _cmd, _cwd, _timeout, _env
            return _as_command_output(result)

        return _run

    monkeypatch.setattr(
        gate_class,
        "_run",
        _stub_run(h.stub_run(stdout=stdout, stderr=stderr, returncode=returncode)),
    )


def create_fake_run_raw(
    result: r[m.Infra.CommandOutput] | str,
) -> Callable[[list[str]], r[m.Infra.CommandOutput]]:
    """Factory for _fake_run_raw that handles both success and failure.

    Single Responsibility: Encapsulate subprocess.run_raw mock creation.
    Eliminates duplication of: identical _fake_run_raw definitions in tests.

    Args:
        result: r[CommandOutput] for success, or str for failure message

    """

    def _fake_run_raw(
        _cmd: list[str],
        **_kw: t.Scalar,
    ) -> r[m.Infra.CommandOutput]:
        if isinstance(result, str):
            return r[m.Infra.CommandOutput].fail(result)
        return result

    return _fake_run_raw


class RunProjectsMock:
    """Stateful mock for run_projects with captured arguments.

    Single Responsibility: Encapsulate captured state for CLI test assertions.
    """

    def __init__(
        self,
        passed: bool | None = None,
        error_msg: str | None = None,
    ) -> None:
        self.passed = True if passed is None else passed
        self.error_msg = error_msg
        self.captured_projects: list[str] = []
        self.captured_fail_fast: bool = False

    def __call__(
        self,
        projects: list[str],
        gates: list[str],
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
    ) -> r[list[m.Infra.ProjectResult]]:
        """Mock run_projects method with captured argument state."""
        del gates, reports_dir  # Not used in mock, but required by signature
        self.captured_projects = projects
        self.captured_fail_fast = fail_fast
        if self.error_msg:
            return r[list[m.Infra.ProjectResult]].fail(self.error_msg)
        result = infra_models.Infra.ProjectResult(project="test-project")
        if not self.passed:
            # Add failing gate to make passed=False (computed from gates dict)
            fail_gate = infra_models.Infra.GateExecution(
                result=infra_models.Infra.GateResult(
                    gate="test",
                    project="test-project",
                    passed=False,
                    errors=[],
                    duration=0.0,
                ),
                issues=[],
                raw_output="",
            )
            result.gates["test"] = fail_gate
        return r[list[m.Infra.ProjectResult]].ok([result])


def create_fake_run_projects(
    passed: bool | None = None,
    error_msg: str | None = None,
) -> RunProjectsMock:
    """Factory for run_projects monkeypatch with state capture.

    Single Responsibility: Create consistent workspace checker CLI test mocks.
    Eliminates duplication: Identical monkeypatch setup across 5+ tests.

    Args:
        passed: True/False for success/failure result. Defaults to True if None and
                error_msg is None.
        error_msg: Error message - if set, overrides passed and returns fail()

    Returns:
        RunProjectsMock with captured_projects and captured_fail_fast attributes.

    """
    return RunProjectsMock(passed=passed, error_msg=error_msg)


def create_check_project_stub() -> Callable[
    [Path, list[str], Path], m.Infra.ProjectResult
]:
    """Factory for _check_project stub that returns fixed project result.

    Single Responsibility: Create consistent project checking mocks.
    Eliminates duplication: Identical _fake_check definitions.
    """

    def _fake_check(
        _project_dir: Path,
        _gates: list[str],
        _reports_dir: Path,
    ) -> m.Infra.ProjectResult:
        del _project_dir, _gates, _reports_dir
        return project

    return _fake_check


def create_check_project_iter_stub(
    projects: list[m.Infra.ProjectResult],
) -> Callable[[Path, list[str], Path], m.Infra.ProjectResult]:
    """Factory for _check_project stub that iterates through project results.

    Single Responsibility: Create consistent project checking mocks with state.
    Eliminates duplication: Multiple _iter_check_project_stub definitions.
    """
    project_iter = iter(projects)

    def _fake_check(
        _project_dir: Path,
        _gates: list[str],
        _reports_dir: Path,
    ) -> m.Infra.ProjectResult:
        del _project_dir, _gates, _reports_dir
        return next(project_iter)

    return _fake_check


def patch_python_dir_detection(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: type,
    *,
    has_python_dirs: bool,
) -> None:
    """Patch gate python directory detection methods.

    Single Responsibility: Mock python directory discovery for gate tests.
    """

    def _existing_dirs(_self: object, _project_dir: Path) -> list[str]:
        del _self, _project_dir
        return ["src"]

    def _no_python_dirs(_project_dir: Path, _dirs: list[str]) -> list[str]:
        del _project_dir, _dirs
        return []

    def _src_python_dirs(_project_dir: Path, _dirs: list[str]) -> list[str]:
        del _project_dir, _dirs
        return ["src"]

    monkeypatch.setattr(gate_class, "_existing_check_dirs", _existing_dirs)
    dirs_with_py = _src_python_dirs if has_python_dirs else _no_python_dirs
    monkeypatch.setattr(gate_class, "_dirs_with_py", staticmethod(dirs_with_py))


__all__ = [
    "RunProjectsMock",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_execution",
    "patch_gate_run",
    "patch_python_dir_detection",
]
