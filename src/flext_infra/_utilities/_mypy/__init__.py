# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Mypy package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._mypy.profile import FlextInfraUtilitiesMypyProfile
    from flext_infra._utilities._mypy.supervisor import (
        FlextInfraUtilitiesMypySupervisor,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesMypyProfile",
    "FlextInfraUtilitiesMypySupervisor",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesMypyProfile": ".profile",
        "FlextInfraUtilitiesMypySupervisor": ".supervisor",
    }),
    public_exports=__all__,
)
