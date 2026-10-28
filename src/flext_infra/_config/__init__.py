# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for config.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._config.make_contract import FlextInfraConfigMakeContract

__all__: tuple[str, ...] = ("FlextInfraConfigMakeContract",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraConfigMakeContract": ".make_contract",
    }),
    public_exports=__all__,
)
