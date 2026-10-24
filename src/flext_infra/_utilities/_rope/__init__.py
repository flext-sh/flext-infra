# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._rope._sdk import Restructure
    from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
    from flext_infra._utilities._rope.project import FlextInfraRopeProject
    from flext_infra._utilities._rope.restructure import FlextInfraRopeRestructure


__all__: tuple[str, ...] = (
    "FlextInfraRopeNativeProject",
    "FlextInfraRopeProject",
    "FlextInfraRopeRestructure",
    "Restructure",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRopeNativeProject": ".native_project",
        "FlextInfraRopeProject": ".project",
        "FlextInfraRopeRestructure": ".restructure",
        "Restructure": "._sdk",
    }),
    public_exports=__all__,
)
