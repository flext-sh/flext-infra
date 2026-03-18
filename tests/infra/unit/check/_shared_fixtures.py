"""Shared fixtures and helpers for workspace checker tests.

Single Source of Truth for common test patterns and mocks.
Eliminates duplication across extended_project_runners and extended_runners_ruff.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_core import r, t

from flext_infra.check.services import FlextInfraWorkspaceChecker, GateExecution
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate

from ...helpers import h
from ...models import m

type RuffGateClass = type[FlextInfraRuffLintGate | FlextInfraRuffFormatGate]


def create_gate_execution(
    gate: str = "lint",
    project: str = "p",
    *,
    passed: bool = True,
    issues: list | None = None,
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
) -> tuple[FlextInfraWorkspaceChecker, Path]:
    """Factory for checker + project directory pair.

    Single Responsibility: Encapsulate shared project setup logic.
    Eliminates duplication of: FlextInfraWorkspaceChecker creation + project initialization.
    """
    checker = FlextInfraWorkspaceChecker(workspace_root=tmp_path)
    project_dir = h.mk_project(tmp_path, project_name)
    return checker, project_dir


def patch_gate_run(
    monkeypatch: pytest.MonkeyPatch,
    gate_class: RuffGateClass,
    *,
    stdout: str,
    returncode: int,
) -> None:
    """Patch gate._run() with controlled output.

    Single Responsibility: Encapsulate monkeypatch setup for gate mocking.
    Eliminates duplication of: gate._run stub creation + monkeypatch.setattr() call.
    """

    def _stub_run(
        result: m.Infra.CommandOutput,
    ) -> callable:
        """Create stub returning fixed result."""

        def _run(
            _self: object,
            _cmd: list[str],
            _cwd: Path,
            _timeout: int = 120,
            _env: dict[str, str] | None = None,
        ) -> m.Infra.CommandOutput:
            del _self, _cmd, _cwd, _timeout, _env
            return result

        return _run

    monkeypatch.setattr(
        gate_class,
        "_run",
        _stub_run(h.stub_run(stdout=stdout, returncode=returncode)),
    )


def create_fake_run_raw(
    result: r[m.Infra.CommandOutput] | str,
) -> callable:
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


__all__ = [
    "create_checker_project",
    "create_fake_run_raw",
    "create_gate_execution",
    "patch_gate_run",
]
