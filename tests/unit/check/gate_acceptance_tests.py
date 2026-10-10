"""Native gate acceptance preserves failures, scope and execution evidence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import (
    FlextInfraGateRegistry,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    FlextInfraWorkspaceChecker,
    c,
    m,
    p,
)
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraGateAcceptance:
    """Observe acceptance through real checker and Ruff public boundaries."""

    @staticmethod
    @pytest.mark.parametrize("verdict", [False, True])
    def test_execution_params_round_trip_preserves_independent_verdict(
        tmp_path: Path,
        *,
        verdict: bool,
    ) -> None:
        """The facade model validates and implements the structural boundary."""
        params = m.Infra.GateExecutionParams(
            project_dir=tmp_path,
            verdict=verdict,
            outcome=c.Infra.ToolOutcome.FINDINGS,
            issues=(),
            raw_output="native diagnostic\n",
            started=1.0,
        )
        restored = m.Infra.GateExecutionParams.model_validate_json(
            params.model_dump_json(),
        )
        boundary: p.Infra.GateExecutionParams = restored
        tm.that(isinstance(restored, p.Infra.GateExecutionParams), eq=True)
        tm.that(boundary.verdict, eq=verdict)
        tm.that(boundary.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(boundary.raw_output, eq=params.raw_output)
        tm.that(boundary.project_dir, eq=tmp_path)
        tm.that(boundary.started, eq=params.started)
        tm.that(tuple(boundary.issues), eq=params.issues)

    @staticmethod
    def test_execution_params_rejects_invalid_native_outcome(tmp_path: Path) -> None:
        """An unknown native outcome cannot cross the validated model boundary."""
        with pytest.raises(ValueError, match="outcome"):
            m.Infra.GateExecutionParams.model_validate({
                "project_dir": tmp_path,
                "verdict": True,
                "outcome": "not-a-native-outcome",
                "issues": (),
                "raw_output": "",
                "started": 1.0,
            })

    @staticmethod
    @pytest.mark.parametrize("broken", [False, True])
    def test_generic_fix_preserves_native_clean_or_error(
        tmp_path: Path,
        *,
        broken: bool,
    ) -> None:
        """Real Ruff formatting exercises the shared assembly contract."""
        project = u.Tests.mk_project(tmp_path, "format-contract", with_src=True)
        source = project / "src" / "sample.py"
        source.write_text(
            "def broken(:\n" if broken else "value=1\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project)
        execution = FlextInfraRuffFormatGate(tmp_path).fix(
            project,
            m.Infra.GateContext(
                repository_root=tmp_path,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
            ),
        )
        tm.that(execution.result.passed, eq=not broken)
        tm.that(
            execution.outcome,
            eq=c.Infra.ToolOutcome.ERROR if broken else c.Infra.ToolOutcome.CLEAN,
        )
        tm.that(bool(execution.issues), eq=broken)
        tm.that(execution.raw_output.strip() != "", eq=True)
        tm.that(
            source.read_text(encoding="utf-8"),
            eq="def broken(:\n" if broken else "value = 1\n",
        )

    @staticmethod
    @pytest.mark.parametrize("fail_fast", [False, True])
    def test_failed_gate_preserves_only_executed_native_verdicts(
        tmp_path: Path,
        *,
        fail_fast: bool,
    ) -> None:
        """Real Ruff failures remain red without inventing dependent executions."""
        project: Path = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project / "src" / "broken.py").write_text(
            "missing_name( 1 )\n",
            encoding="utf-8",
        )
        requested = (c.Infra.LINT, c.Infra.FORMAT)
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                requested,
                fail_fast=fail_fast,
            ),
        )
        tm.that(len(results), eq=1)
        verdict = results[0]
        tm.that(verdict.passed, eq=False)
        tm.that(
            tuple(verdict.gates),
            eq=requested[:1] if fail_fast else requested,
        )
        for execution in verdict.gates.values():
            tm.that(execution.result.passed, eq=False)
            tm.that(execution.finding_count > 0, eq=True)
            receipt = execution.raw_receipt
            tm.that(receipt is not None, eq=True)
            if receipt is None:
                pytest.fail("Every executed gate must retain its native receipt")
            tm.that(receipt.read_text(encoding="utf-8").strip() != "", eq=True)

    @staticmethod
    def test_native_fix_with_residual_findings_remains_red(tmp_path: Path) -> None:
        """A completed Ruff repair cannot accept an unresolved native finding."""
        project: Path = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project / "src" / "broken.py").write_text(
            "missing_name()\n",
            encoding="utf-8",
        )
        execution = FlextInfraRuffLintGate(tmp_path).fix(
            project,
            m.Infra.GateContext(
                repository_root=tmp_path,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
            ),
        )
        tm.that(execution.result.passed, eq=False)
        tm.that(execution.finding_count > 0, eq=True)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(execution.raw_output.strip() != "", eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        "gate_id",
        sorted(
            gate_id
            for gate_id in c.Infra.TYPE_CHECKER_GATES
            for gate_type in (FlextInfraGateRegistry().get(gate_id),)
            if gate_type is not None and gate_type.requires_python_targets
        ),
    )
    def test_project_without_an_executed_gate_is_not_accepted(
        tmp_path: Path,
        gate_id: str,
    ) -> None:
        """Content-selected checkers have no execution without Python sources."""
        project: Path = u.Tests.mk_project(tmp_path, "p1")
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                (gate_id,),
            ),
        )
        tm.that(len(results), eq=1)
        tm.that(results[0].gates, empty=True)
        tm.that(results[0].passed, eq=False)
