# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.release package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
    from flext_infra.release.release import FlextInfraReleaseRelease


__all__: tuple[str, ...] = ("FlextInfraReleaseOrchestrator", "FlextInfraReleaseRelease")

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraReleaseOrchestrator": ".orchestrator",
        "FlextInfraReleaseRelease": ".release",
    },
    public_exports=__all__,
)
