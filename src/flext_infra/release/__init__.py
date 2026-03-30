# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release management services.

Provides services for versioning, release notes generation, and release
orchestration through composable phases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.release import cli as cli, orchestrator as orchestrator
    from flext_infra.release.cli import FlextInfraCliRelease as FlextInfraCliRelease
    from flext_infra.release.orchestrator import (
        FlextInfraReleaseOrchestrator as FlextInfraReleaseOrchestrator,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliRelease": ["flext_infra.release.cli", "FlextInfraCliRelease"],
    "FlextInfraReleaseOrchestrator": [
        "flext_infra.release.orchestrator",
        "FlextInfraReleaseOrchestrator",
    ],
    "cli": ["flext_infra.release.cli", ""],
    "orchestrator": ["flext_infra.release.orchestrator", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliRelease",
    "FlextInfraReleaseOrchestrator",
    "cli",
    "orchestrator",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
