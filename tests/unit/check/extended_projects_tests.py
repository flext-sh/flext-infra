"""Tests for workspace checker public methods and runner execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, t

from flext_infra import FlextInfraWorkspaceChecker

from ._shared_fixtures import create_gate_execution


class TestLintAndFormatPublicMethods:
    @staticmethod
    def _assert_gate_public_method(
        *,
        checker: FlextInfraWorkspaceChecker,
        target_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        gate_name: str,
    ) -> None:
        def _fake_run_gate(
            requested_gate_name: str,
            _project_dir: Path,
        ) -> m.Infra.GateExecution:
            del _project_dir
            return create_gate_execution(gate=requested_gate_name, passed=True)

        monkeypatch.setattr(checker, "_run_gate", _fake_run_gate)
        run_public = checker.lint if gate_name == "lint" else checker.format
        result = run_public(target_dir)
        tm.ok(result)
        tm.that(result.value.gate, eq=gate_name)

    def test_lint_public_method(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        (tmp_path / "pyproject.toml").touch()
        self._assert_gate_public_method(
            checker=checker,
            target_dir=tmp_path,
            monkeypatch=monkeypatch,
            gate_name="lint",
        )

    def test_format_public_method(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        (tmp_path / "pyproject.toml").touch()
        self._assert_gate_public_method(
            checker=checker,
            target_dir=tmp_path,
            monkeypatch=monkeypatch,
            gate_name="format",
        )


class TestCheckProjectRunners:
    def test_check_project_runner_execution(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "test.py").touch()
        called: t.MutableBoolMapping = {
            "lint": False,
            "format": False,
            "pyrefly": False,
        }

        class _FakeGate:
            def __init__(self, gate_name: str) -> None:
                self._gate_name = gate_name

            def check(
                self,
                _project_dir: Path,
                _ctx: t.Scalar,
            ) -> m.Infra.GateExecution:
                del _project_dir, _ctx
                called[self._gate_name] = True
                return create_gate_execution(gate=self._gate_name, passed=True)

        def _fake_create(gate_name: str, _workspace_root: Path) -> _FakeGate:
            del _workspace_root
            return _FakeGate(gate_name)

        monkeypatch.setattr(checker._registry, "create", _fake_create)
        result = checker._check_project_with_ctx(
            tmp_path,
            ["lint", "format", "pyrefly"],
            m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path),
        )
        tm.that(called["lint"], eq=True)
        tm.that(called["format"], eq=True)
        tm.that(called["pyrefly"], eq=True)
        tm.that(result.gates, has="lint")
        tm.that(result.gates, has="format")
        tm.that(result.gates, has="pyrefly")
