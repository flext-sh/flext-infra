# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.check package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.check.codemod_gate_native_route_tests import (
        TestsFlextInfraCodemodGateNativeRoute,
    )
    from tests.unit.check.test_mutation_leases import TestsFlextInfraMutationLeases


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodemodGateNativeRoute",
    "TestsFlextInfraMutationLeases",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraCodemodGateNativeRoute": ".codemod_gate_native_route_tests",
        "TestsFlextInfraMutationLeases": ".test_mutation_leases",
    },
    public_exports=__all__,
)
