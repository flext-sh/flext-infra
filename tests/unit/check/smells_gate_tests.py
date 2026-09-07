"""Fail-closed public behavior for the qlty smells gate."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.check import FlextInfraGateRegistry
from flext_infra.gates.smells import FlextInfraSmellsGate
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _ctx(root: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(workspace=root, reports_dir=root / "reports")


class TestSmellsGate:
    """Exercise observable gate behavior with the real setup-provisioned tool."""

    def test_registry_exposes_the_canonical_gate(self) -> None:
        gate = FlextInfraGateRegistry.default().get(FlextInfraSmellsGate.gate_id)
        tm.that(gate is FlextInfraSmellsGate, eq=True)

    def test_missing_project_configuration_is_a_blocking_failure(
        self, tmp_path: Path
    ) -> None:
        """A missing generated prerequisite escapes; it is not a code finding.

        The qlty config is owned by the generator, so its absence is an
        operational gap the operator has to close with `make gen APPLY=Y`.
        Reporting it as one more issue inside the scan would bury an
        unrunnable gate among the findings it never produced.
        """
        project = u.Tests.mk_project(tmp_path, "smells-project", with_src=True)

        with pytest.raises(FileNotFoundError, match="run make gen APPLY=Y"):
            _ = FlextInfraSmellsGate(tmp_path).check(project, _ctx(tmp_path))
