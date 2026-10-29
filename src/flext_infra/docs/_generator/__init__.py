# AUTO-GENERATED FILE — Regenerate with: make gen
"""generator package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._generator.bundle import FlextInfraDocsGeneratorBundle


__all__: tuple[str, ...] = ("FlextInfraDocsGeneratorBundle",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraDocsGeneratorBundle": ".bundle",
    }),
    public_exports=__all__,
)
