# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests. Models package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests._models.base import TestsFlextInfraModelsBase


__all__: tuple[str, ...] = ("TestsFlextInfraModelsBase",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({"TestsFlextInfraModelsBase": ".base"}),
    public_exports=__all__,
)
