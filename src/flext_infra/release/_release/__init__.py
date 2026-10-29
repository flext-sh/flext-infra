# AUTO-GENERATED FILE — Regenerate with: make gen
"""release package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.release._release.artifact import FlextInfraReleaseReleaseArtifact
    from flext_infra.release._release.boundary import FlextInfraReleaseReleaseBoundary
    from flext_infra.release._release.build import FlextInfraReleaseReleaseBuild
    from flext_infra.release._release.metadata import FlextInfraReleaseReleaseMetadata
    from flext_infra.release._release.plan import FlextInfraReleaseReleasePlan
    from flext_infra.release._release.project import FlextInfraReleaseReleaseProject
    from flext_infra.release._release.publish import FlextInfraReleaseReleasePublish
    from flext_infra.release._release.source import FlextInfraReleaseReleaseSource


__all__: tuple[str, ...] = (
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
        "FlextInfraReleaseReleaseArtifact": ".artifact",
        "FlextInfraReleaseReleaseBoundary": ".boundary",
        "FlextInfraReleaseReleaseBuild": ".build",
        "FlextInfraReleaseReleaseMetadata": ".metadata",
        "FlextInfraReleaseReleasePlan": ".plan",
        "FlextInfraReleaseReleaseProject": ".project",
        "FlextInfraReleaseReleasePublish": ".publish",
        "FlextInfraReleaseReleaseSource": ".source",
    }),
    public_exports=__all__,
)
