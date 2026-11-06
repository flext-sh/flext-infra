# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps. Detection package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps._detection.runners import FlextInfraDepsDetectionRunners


__all__: tuple[str, ...] = ("FlextInfraDepsDetectionRunners",)

install_lazy_exports(
    __name__,
    globals(),
    {"FlextInfraDepsDetectionRunners": ".runners"},
    public_exports=__all__,
)
