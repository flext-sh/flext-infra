# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps. Detector package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps._detector.runtime_steps import (
        FlextInfraDepsDetectorRuntimeSteps,
    )


__all__: tuple[str, ...] = ("FlextInfraDepsDetectorRuntimeSteps",)

install_lazy_exports(
    __name__,
    globals(),
    {"FlextInfraDepsDetectorRuntimeSteps": ".runtime_steps"},
    public_exports=__all__,
)
