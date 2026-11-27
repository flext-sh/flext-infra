# AUTO-GENERATED FILE — Regenerate with: make check
"""Tests. Constants package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests._constants.scan import TestsFlextInfraConstantsScan
    from tests._constants.semantic_cutover import (
        TestsFlextInfraConstantsSemanticCutover,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraConstantsScan",
    "TestsFlextInfraConstantsSemanticCutover",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraConstantsScan": ".scan",
        "TestsFlextInfraConstantsSemanticCutover": ".semantic_cutover",
    },
    public_exports=__all__,
    deferred_members=(
        "TestsFlextInfraConstantsScan",
        "TestsFlextInfraConstantsSemanticCutover",
    ),
)
