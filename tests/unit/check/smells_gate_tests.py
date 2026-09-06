"""Fail-closed public behavior for the qlty smells gate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.gates.smells import FlextInfraSmellsGate
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _ctx(root: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(repository_root=root, reports_dir=root / "reports")


class TestSmellsGate:
    """Exercise observable gate behavior with the real setup-provisioned tool."""

    def test_registry_exposes_the_canonical_gate(self) -> None:
        gate = FlextInfraGateRegistry.default().get("smells")
        tm.that(gate is FlextInfraSmellsGate, eq=True)

    def test_missing_project_configuration_is_a_blocking_failure(
        self, tmp_path: Path
    ) -> None:
        project = u.Tests.mk_project(tmp_path, "smells-project", with_src=True)

        execution = FlextInfraSmellsGate(tmp_path).check(project, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(execution.issues[0].severity, eq=str(c.Infra.GateSeverity.ERROR.value))
