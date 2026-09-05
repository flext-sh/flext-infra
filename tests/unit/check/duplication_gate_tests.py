"""Fail-closed public behavior for the jscpd duplication gate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.gates.duplication import FlextInfraDuplicationGate
from flext_infra.gates.registry import FlextInfraGateRegistry
from flext_tests import tm
from tests import m

if TYPE_CHECKING:
    from pathlib import Path


def _ctx(root: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(workspace=root, reports_dir=root / "reports")


class TestDuplicationGate:
    """Exercise observable gate behavior with the real setup-provisioned tool."""

    def test_registry_exposes_the_canonical_gate(self) -> None:
        gate = FlextInfraGateRegistry.default().get(c.Infra.DUPLICATION)
        tm.that(gate is FlextInfraDuplicationGate, eq=True)

    def test_empty_workspace_scope_is_a_blocking_failure(self, tmp_path: Path) -> None:
        project = tmp_path / "missing-project"
        project.mkdir()

        execution = FlextInfraDuplicationGate(tmp_path).check(
            project, _ctx(tmp_path)
        )

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(execution.issues[0].message, has="project")
        tm.that(
            execution.issues[0].severity,
            eq=str(c.Infra.GateSeverity.ERROR.value),
        )
