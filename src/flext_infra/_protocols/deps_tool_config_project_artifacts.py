# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_project_artifacts
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToolConfigProjectArtifacts:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectManagedArtifactsConfig(Protocol):
        """Structural data contract projected from the owning model."""

        Mise: p.Infra.ProjectMiseConfig
        Gitignore: p.Infra.ProjectGitignoreConfig

    @runtime_checkable
    class ProjectManagedArtifactsResolution(Protocol):
        """Structural data contract projected from the owning model."""

        artifacts: p.Infra.ProjectManagedArtifactsConfig
        mise_tool_sources: Mapping[t.NonEmptyStr, Path]

    @runtime_checkable
    class ProjectManagedArtifactsSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        sources: tuple[p.Cli.AtomicFileState, ...]
        resolution: p.Infra.ProjectManagedArtifactsResolution


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigProjectArtifacts",
]
