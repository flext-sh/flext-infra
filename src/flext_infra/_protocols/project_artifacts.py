# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/project_artifacts
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t
    from flext_infra._protocols import (
        FlextInfraProtocolsDepsToolConfigProjectMise,
        FlextInfraProtocolsProjectGitignore,
    )


class FlextInfraProtocolsProjectArtifacts:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectManagedArtifactsConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def Mise(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigProjectMise.ProjectMiseConfig:
            """Mise additions owned by the current project."""
            ...

        @property
        def Gitignore(
            self,
        ) -> FlextInfraProtocolsProjectGitignore.ProjectGitignoreConfig:
            """Ignore patterns owned by the current project."""
            ...

    @runtime_checkable
    class ProjectManagedArtifactsResolution(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def artifacts(
            self,
        ) -> FlextInfraProtocolsProjectArtifacts.ProjectManagedArtifactsConfig:
            """Composed managed-artifact configuration."""
            ...

        mise_tool_sources: Mapping[t.NonEmptyStr, Path]

    @runtime_checkable
    class ProjectManagedArtifactsSnapshot(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        sources: tuple[p.Cli.AtomicFileState, ...]

        @property
        def resolution(
            self,
        ) -> FlextInfraProtocolsProjectArtifacts.ProjectManagedArtifactsResolution:
            """Managed artifacts parsed from those exact sources."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsProjectArtifacts",
]
