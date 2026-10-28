# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Project package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._project.discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidates,
    )
    from flext_infra._utilities._project.discovery_shape import (
        FlextInfraUtilitiesProjectDiscoveryShape,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesProjectDiscoveryCandidates",
    "FlextInfraUtilitiesProjectDiscoveryShape",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesProjectDiscoveryCandidates": ".discovery_candidates",
        "FlextInfraUtilitiesProjectDiscoveryShape": ".discovery_shape",
    }),
    public_exports=__all__,
)
