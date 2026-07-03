"""Tests for gate registration of the new durissimas gates.

`loc-cap` and `boundary` must be in the SSOT-derived ALLOWED_GATES and resolve
through the registry.
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.tests.typings import t


class TestGateRegistry:
    def test_new_gates_in_allowed(self) -> None:
        tm.that("loc-cap" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("boundary" in c.Infra.ALLOWED_GATES, eq=True)

    def test_registry_resolves_loc_cap(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("loc-cap") is not None, eq=True)

    def test_registry_resolves_boundary(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("boundary") is not None, eq=True)


__all__: t.StrSequence = []
