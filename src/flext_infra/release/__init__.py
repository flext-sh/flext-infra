# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.release package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from ._orchestrator_dispatch import FlextInfraReleaseOrchestratorDispatchMixin
    from ._orchestrator_publish import FlextInfraReleaseOrchestratorPublishMixin
    from ._release_artifact_archive import FlextInfraReleaseArtifactArchiveMixin
    from ._release_artifact_build import FlextInfraReleaseArtifactBuildMixin
    from ._release_artifact_execution import FlextInfraReleaseArtifactExecutionMixin
    from ._release_artifact_metadata import FlextInfraReleaseArtifactMetadataMixin
    from ._release_artifact_persistence import FlextInfraReleaseArtifactPersistenceMixin
    from ._release_artifact_source import FlextInfraReleaseArtifactSourceMixin
    from .orchestrator import FlextInfraReleaseOrchestrator
    from .orchestrator_phases import FlextInfraReleaseOrchestratorPhases
    from .policy_render import FlextInfraReleasePolicyRender
__all__: tuple[str, ...] = (
    "FlextInfraReleaseArtifactArchiveMixin",
    "FlextInfraReleaseArtifactBuildMixin",
    "FlextInfraReleaseArtifactExecutionMixin",
    "FlextInfraReleaseArtifactMetadataMixin",
    "FlextInfraReleaseArtifactPersistenceMixin",
    "FlextInfraReleaseArtifactSourceMixin",
    "FlextInfraReleaseOrchestrator",
    "FlextInfraReleaseOrchestratorDispatchMixin",
    "FlextInfraReleaseOrchestratorPhases",
    "FlextInfraReleaseOrchestratorPublishMixin",
    "FlextInfraReleasePolicyRender",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._orchestrator_dispatch": ("FlextInfraReleaseOrchestratorDispatchMixin",),
            "._orchestrator_publish": ("FlextInfraReleaseOrchestratorPublishMixin",),
            "._release_artifact_archive": ("FlextInfraReleaseArtifactArchiveMixin",),
            "._release_artifact_build": ("FlextInfraReleaseArtifactBuildMixin",),
            "._release_artifact_execution": (
                "FlextInfraReleaseArtifactExecutionMixin",
            ),
            "._release_artifact_metadata": ("FlextInfraReleaseArtifactMetadataMixin",),
            "._release_artifact_persistence": (
                "FlextInfraReleaseArtifactPersistenceMixin",
            ),
            "._release_artifact_source": ("FlextInfraReleaseArtifactSourceMixin",),
            ".orchestrator": ("FlextInfraReleaseOrchestrator",),
            ".orchestrator_phases": ("FlextInfraReleaseOrchestratorPhases",),
            ".policy_render": ("FlextInfraReleasePolicyRender",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
