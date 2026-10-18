# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Typings package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import CliResultValue, FlextInfraTypesBase
    from flext_infra._typings.collections import FlextInfraTypesCollections
    from flext_infra._typings.rope import FlextInfraTypesRope
    from flext_infra._typings.rope_native import FlextInfraTypesRopeNative


__all__: tuple[str, ...] = (
    "CliResultValue",
    "FlextInfraTypesAdapters",
    "FlextInfraTypesBase",
    "FlextInfraTypesCollections",
    "FlextInfraTypesRope",
    "FlextInfraTypesRopeNative",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "CliResultValue": ".base",
        "FlextInfraTypesAdapters": ".adapters",
        "FlextInfraTypesBase": ".base",
        "FlextInfraTypesCollections": ".collections",
        "FlextInfraTypesRope": ".rope",
        "FlextInfraTypesRopeNative": ".rope_native",
    }),
    public_exports=__all__,
)
