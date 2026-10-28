# AUTO-GENERATED FILE — Regenerate with: make gen
"""promoted package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._promoted.commands import FlextInfraUtilitiesPromotedCommands
    from flext_infra._promoted.execution import FlextInfraUtilitiesPromotedExecution
    from flext_infra._promoted.invocation import FlextInfraUtilitiesPromotedInvocation
    from flext_infra._promoted.rendering import FlextInfraUtilitiesPromotedRendering
    from flext_infra._promoted.workspace import FlextInfraUtilitiesPromotedWorkspace


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesPromotedCommands",
    "FlextInfraUtilitiesPromotedExecution",
    "FlextInfraUtilitiesPromotedInvocation",
    "FlextInfraUtilitiesPromotedRendering",
    "FlextInfraUtilitiesPromotedWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesPromotedCommands": ".commands",
        "FlextInfraUtilitiesPromotedExecution": ".execution",
        "FlextInfraUtilitiesPromotedInvocation": ".invocation",
        "FlextInfraUtilitiesPromotedRendering": ".rendering",
        "FlextInfraUtilitiesPromotedWorkspace": ".workspace",
    }),
    public_exports=__all__,
)
