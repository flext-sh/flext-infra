# AUTO-GENERATED FILE — Regenerate with: make gen
"""Release package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

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
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
    from flext_infra.release.release import FlextInfraReleaseRelease


__all__: tuple[str, ...] = (
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseRelease",
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
        "FlextInfraReleaseOrchestrator": ".orchestrator",
        "FlextInfraReleaseRelease": ".release",
        "FlextInfraReleaseReleaseArtifact": "._release.artifact",
        "FlextInfraReleaseReleaseBoundary": "._release.boundary",
        "FlextInfraReleaseReleaseBuild": "._release.build",
        "FlextInfraReleaseReleaseMetadata": "._release.metadata",
        "FlextInfraReleaseReleasePlan": "._release.plan",
        "FlextInfraReleaseReleaseProject": "._release.project",
        "FlextInfraReleaseReleasePublish": "._release.publish",
        "FlextInfraReleaseReleaseSource": "._release.source",
    }),
    public_exports=__all__,
)
