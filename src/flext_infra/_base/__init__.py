# AUTO-GENERATED FILE — Regenerate with: make gen
"""base package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._base.payload import FlextInfraBasePayload
    from flext_infra._base.projects import FlextInfraBaseProjects


__all__: tuple[str, ...] = (
    "FlextInfraBasePayload",
    "FlextInfraBaseProjects",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraBasePayload": ".payload",
        "FlextInfraBaseProjects": ".projects",
    }),
    public_exports=__all__,
)
