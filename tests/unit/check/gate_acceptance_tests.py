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
    FlextInfraRuffLintGate,
    FlextInfraWorkspaceChecker,
    c,
    m,
)
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraGateAcceptance:
    """Observe acceptance through real checker and Ruff public boundaries."""

    @staticmethod
    @pytest.mark.parametrize("fail_fast", [False, True])
    def test_failed_gate_preserves_only_executed_native_verdicts(
        tmp_path: Path,
        *,
        fail_fast: bool,
    ) -> None:
        """Real Ruff failures remain red without inventing dependent executions."""
        project = u.Tests.mk_project(tmp_path, "p1", with_src=True)
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
        project = u.Tests.mk_project(tmp_path, "p1", with_src=True)
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
            if gate_type is not None
            and gate_type.requires_python_targets
        ),
    )
    def test_project_without_an_executed_gate_is_not_accepted(
        tmp_path: Path,
        gate_id: str,
    ) -> None:
        """Content-selected checkers have no execution without Python sources."""
        project = u.Tests.mk_project(tmp_path, "p1")
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                (gate_id,),
            ),
        )
        tm.that(len(results), eq=1)
        tm.that(results[0].gates, empty=True)
        tm.that(results[0].passed, eq=False)
