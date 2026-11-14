# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests. Models package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests._models.base import TestsFlextInfraModelsBase
    from tests._models.semantic_cutover import TestsFlextInfraModelsSemanticCutover


__all__: tuple[str, ...] = (
    "TestsFlextInfraModelsBase",
    "TestsFlextInfraModelsSemanticCutover",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraModelsBase": ".base",
        "TestsFlextInfraModelsSemanticCutover": ".semantic_cutover",
    },
    public_exports=__all__,
    deferred_members={
        "TestsFlextInfraModelsBase": (
            "AstGrepFixtureSnapshots",
            "PytestDiagOptions",
        ),
        "TestsFlextInfraModelsSemanticCutover": ("SemanticCutoverScenario",),
    },
)
