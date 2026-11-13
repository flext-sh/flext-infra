# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests. Protocols package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests._protocols.base import TestsFlextInfraProtocolsBase
    from tests._protocols.semantic_cutover import (
        TestsFlextInfraProtocolsSemanticCutover,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraProtocolsBase",
    "TestsFlextInfraProtocolsSemanticCutover",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraProtocolsBase": ".base",
        "TestsFlextInfraProtocolsSemanticCutover": ".semantic_cutover",
    },
    public_exports=__all__,
    deferred_members={
        "TestsFlextInfraProtocolsBase": (
            "AstGrepFixtureSnapshots",
            "PytestDiagOptions",
        ),
        "TestsFlextInfraProtocolsSemanticCutover": ("SemanticCutoverScenario",),
    },
)
