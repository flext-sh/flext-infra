# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for consolidator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen._consolidator.steps import (
        FlextInfraCodegenConsolidatorSteps,
    )

__all__: tuple[str, ...] = ("FlextInfraCodegenConsolidatorSteps",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenConsolidatorSteps": ".steps",
    }),
    public_exports=__all__,
)
