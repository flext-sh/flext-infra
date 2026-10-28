# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.release package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.release._release import (
        FlextInfraReleaseReleaseArtifact,
        FlextInfraReleaseReleaseBoundary,
        FlextInfraReleaseReleaseBuild,
        FlextInfraReleaseReleaseMetadata,
        FlextInfraReleaseReleasePlan,
        FlextInfraReleaseReleaseProject,
        FlextInfraReleaseReleasePublish,
        FlextInfraReleaseReleaseSource,
    )
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator


__all__: tuple[str, ...] = (
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseReleaseArtifact",
    "FlextInfraReleaseReleaseBoundary",
    "FlextInfraReleaseReleaseBuild",
    "FlextInfraReleaseReleaseMetadata",
    "FlextInfraReleaseReleasePlan",
    "FlextInfraReleaseReleaseProject",
    "FlextInfraReleaseReleasePublish",
    "FlextInfraReleaseReleaseSource",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraReleaseReleaseArtifact": "._release_artifact",
        "FlextInfraReleaseReleaseBoundary": "._release_boundary",
        "FlextInfraReleaseReleaseBuild": "._release_build",
        "FlextInfraReleaseReleaseMetadata": "._release_metadata",
        "FlextInfraReleaseOrchestrator": ".orchestrator",
        "FlextInfraReleaseReleasePlan": "._release_plan",
        "FlextInfraReleaseReleaseProject": "._release_project",
        "FlextInfraReleaseReleasePublish": "._release_publish",
        "FlextInfraReleaseReleaseSource": "._release_source",
    }),
    public_exports=__all__,
)
