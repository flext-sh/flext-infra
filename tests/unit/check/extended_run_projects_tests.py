"""Tests for workspace checker run_projects and run methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import (
    FlextInfraTestHelpers as h,
    create_check_project_iter_stub,
    create_check_project_stub,
    create_gate_execution,
    m,
    t,
)

from flext_infra import FlextInfraWorkspaceChecker


class TestRunProjectsValidation:
    """Test run_projects input validation and edge cases."""

    def test_invalid_gates(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        result = checker.run_projects(
            ["p1"],
            ["invalid_gate"],
            reports_dir=tmp_path / "reports",
        )
        tm.fail(result)

    def test_skips_missing_projects(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        result = checker.run_projects(
            ["nonexistent"],
            ["lint"],
            reports_dir=tmp_path / "reports",
        )
        tm.ok(result)
        tm.that(len(result.value), eq=0)


class TestRunProjectsReports:
    """Test run_projects report generation."""

    def test_creates_markdown_report(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        project = m.Infra.ProjectResult(
            project="p1",
            gates={"lint": create_gate_execution(passed=False)},
        )
        monkeypatch.setattr(
            checker, "_check_project_with_ctx", create_check_project_stub(project)
        )
        _ = h.mk_project(tmp_path, "p1")
        result = checker.run_projects(["p1"], ["lint"], reports_dir=reports_dir)
        tm.ok(result)
        tm.that((reports_dir / "check-report.md").exists(), eq=True)

    def test_creates_sarif_report(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        project = m.Infra.ProjectResult(
            project="p1",
            gates={"lint": create_gate_execution(passed=True)},
        )
        monkeypatch.setattr(
            checker, "_check_project_with_ctx", create_check_project_stub(project)
        )
        _ = h.mk_project(tmp_path, "p1")
        result = checker.run_projects(["p1"], ["lint"], reports_dir=reports_dir)
        tm.ok(result)
        tm.that((reports_dir / "check-report.sarif").exists(), eq=True)

    def test_creates_project_scoped_reports_dir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / "reports"
        captured: t.MutableMappingKV[str, Path] = {}

        def _fake_check(
            _project_dir: Path,
            _gates: t.StrSequence,
            ctx: m.Infra.GateContext,
        ) -> m.Infra.ProjectResult:
            captured["reports_dir"] = ctx.reports_dir
            return m.Infra.ProjectResult(
                project="p1",
                gates={"lint": create_gate_execution(passed=True)},
            )

        monkeypatch.setattr(checker, "_check_project_with_ctx", _fake_check)
        _ = h.mk_project(tmp_path, "p1")

        result = checker.run_projects(["p1"], ["lint"], reports_dir=reports_dir)

        tm.ok(result)
        tm.that((reports_dir / "p1").is_dir(), eq=True)
        tm.that(captured["reports_dir"], eq=reports_dir / "p1")


class TestRunProjectsBehavior:
    """Test run_projects fail_fast and error reporting."""

    def test_fail_fast_stops_on_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        call_count = [0]

        def _fake_check(
            _project_dir: Path,
            _gates: t.StrSequence,
            _reports_dir: Path,
            **_kwargs: t.Infra.InfraValue,
        ) -> m.Infra.ProjectResult:
            del _project_dir, _gates, _reports_dir, _kwargs
            call_count[0] += 1
            return m.Infra.ProjectResult(
                project="p",
                gates={"lint": create_gate_execution(passed=False)},
            )

        monkeypatch.setattr(checker, "_check_project_with_ctx", _fake_check)
        for name in ["p1", "p2", "p3"]:
            _ = h.mk_project(tmp_path, name)
        result = checker.run_projects(
            ["p1", "p2", "p3"],
            ["lint"],
            reports_dir=tmp_path / "reports",
            fail_fast=True,
        )
        tm.ok(result)
        tm.that(call_count[0], eq=1)

    def test_reports_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        issue = m.Infra.Issue(
            file="test.py",
            line=1,
            column=1,
            code="E1",
            message="error",
            severity="error",
        )
        gate_exec = create_gate_execution(passed=True, issues=[issue])
        project = m.Infra.ProjectResult(project="p1", gates={"lint": gate_exec})
        monkeypatch.setattr(
            checker, "_check_project_with_ctx", create_check_project_stub(project)
        )
        _ = h.mk_project(tmp_path, "p1")
        result = checker.run_projects(
            ["p1"],
            ["lint"],
            reports_dir=tmp_path / "reports",
        )
        tm.ok(result)
        tm.that(len(result.value), eq=1)
        tm.that(result.value[0].total_errors, eq=1)

    def test_multiple_with_mixed_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        issue = m.Infra.Issue(
            file="test.py",
            line=1,
            column=1,
            code="E1",
            message="error",
            severity="error",
        )
        exec_with = create_gate_execution(passed=True, issues=[issue])
        exec_without = create_gate_execution(passed=True)
        project1 = m.Infra.ProjectResult(project="p1", gates={"lint": exec_with})
        project2 = m.Infra.ProjectResult(project="p2", gates={"lint": exec_without})
        monkeypatch.setattr(
            checker,
            "_check_project_with_ctx",
            create_check_project_iter_stub([project1, project2]),
        )
        for name in ["p1", "p2"]:
            _ = h.mk_project(tmp_path, name)
        result = checker.run_projects(
            ["p1", "p2"],
            ["lint"],
            reports_dir=tmp_path / "reports",
        )
        tm.ok(result)
        tm.that(len(result.value), eq=2)
        tm.that(result.value[0].total_errors, eq=1)
        tm.that(result.value[1].total_errors, eq=0)


class TestRunSingleProject:
    """Test FlextInfraWorkspaceChecker.run method."""

    def test_run_single_project_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        _ = h.mk_project(tmp_path, "p1")
        project = m.Infra.ProjectResult(
            project="p1",
            gates={"lint": create_gate_execution(passed=True)},
        )
        monkeypatch.setattr(
            checker, "_check_project_with_ctx", create_check_project_stub(project)
        )
        result = checker.run_project("p1", ["lint"])
        tm.ok(result)
        tm.that(len(result.value), eq=1)


class _FixableGate:
    can_fix = True
    gate_id: str = "lint"

    def __init__(self) -> None:
        self.calls: t.MutableSequenceOf[str] = []

    def fix(
        self,
        _project_dir: Path,
        _ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        self.calls.append("fix")
        return create_gate_execution()

    def check(
        self,
        _project_dir: Path,
        _ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        self.calls.append("check")
        return create_gate_execution()


def _create_fixable_gate(
    _gate_id: str,
    _workspace_root: Path,
    *,
    gate: _FixableGate,
) -> _FixableGate:
    return gate


class TestRunProjectFixMode:
    """Test supported gate fixes during project checking."""

    def test_check_project_runs_fix_before_check(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        gate = _FixableGate()

        def _fake_create(gate_id: str, workspace_root: Path) -> _FixableGate:
            return _create_fixable_gate(
                gate_id,
                workspace_root,
                gate=gate,
            )

        monkeypatch.setattr(checker._registry, "create", _fake_create)
        _ = h.mk_project(tmp_path, "p1")

        result = checker._check_project_with_ctx(
            tmp_path / "p1",
            ["lint"],
            m.Infra.GateContext(
                workspace=tmp_path,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
            ),
        )

        tm.that(result.passed, eq=True)
        tm.that(gate.calls, eq=["fix", "check"])

    def test_check_project_check_only_skips_fix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        gate = _FixableGate()

        def _fake_create(gate_id: str, workspace_root: Path) -> _FixableGate:
            return _create_fixable_gate(
                gate_id,
                workspace_root,
                gate=gate,
            )

        monkeypatch.setattr(checker._registry, "create", _fake_create)
        _ = h.mk_project(tmp_path, "p1")

        result = checker._check_project_with_ctx(
            tmp_path / "p1",
            ["lint"],
            m.Infra.GateContext(
                workspace=tmp_path,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
                check_only=True,
            ),
        )

        tm.that(result.passed, eq=True)
        tm.that(gate.calls, eq=["check"])
