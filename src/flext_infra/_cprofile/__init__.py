# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Cprofile package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._cprofile.entry import FlextInfraCprofileEntry


__all__: tuple[str, ...] = ("FlextInfraCprofileEntry",)

install_lazy_exports(
    __name__,
    globals(),
    {"FlextInfraCprofileEntry": ".entry"},
    public_exports=__all__,
)
