# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._codemod.scan_cache import FlextInfraCodemodScanCache


__all__: tuple[str, ...] = ("FlextInfraCodemodScanCache",)

install_lazy_exports(
    __name__,
    globals(),
    {"FlextInfraCodemodScanCache": ".scan_cache"},
    public_exports=__all__,
)
