"""Tests for workspace checker project runner execution and public methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, t, u

from flext_core import r
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker

from ._shared_fixtures import create_gate_execution


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
                called[self._gate_name] = True
                return create_gate_execution(gate=self._gate_name)

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


class TestJsonWriteFailure:
    def test_run_projects_with_json_write_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        proj_dir = tmp_path / "test-project"
        proj_dir.mkdir()
        (proj_dir / "pyproject.toml").write_text("[tool.poetry]\n")

        def _fake_write_json(*_a: t.Scalar, **_kw: t.Scalar) -> r[bool]:
            del _a, _kw
            return r[bool].fail("write error")

        monkeypatch.setattr(u.Cli, "json_write", _fake_write_json)

        class _FakeLintGate:
            def check(
                self,
                _project_dir: Path,
                _ctx: m.Infra.GateContext,
            ) -> m.Infra.GateExecution:
                del _project_dir, _ctx
                return create_gate_execution("lint", "p", passed=True)

        def _fake_create(_gate_name: str, _workspace_root: Path) -> _FakeLintGate:
            del _gate_name, _workspace_root
            return _FakeLintGate()

        monkeypatch.setattr(checker._registry, "create", _fake_create)
        result = checker.run_projects(["test-project"], ["lint"])
        tm.fail(result, has="write error")


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
            return create_gate_execution(requested_gate_name, "p", passed=True)

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
