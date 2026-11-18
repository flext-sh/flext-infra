"""Project-owned managed-artifact configuration models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import (
    FlextInfraModelsDepsToolConfigProjectMise,
    FlextInfraModelsProjectGitignore,
)


class FlextInfraModelsProjectArtifacts(
    FlextInfraModelsProjectGitignore,
):
    """Managed-artifact models composed from project-owned slices."""

    class ProjectManagedArtifactsConfig(m.ArbitraryTypesModel):
        """Project-owned configuration for generated artifacts."""

        Mise: Annotated[
            FlextInfraModelsDepsToolConfigProjectMise.ProjectMiseConfig,
            m.Field(description="Mise additions owned by the current project."),
        ]
        Gitignore: Annotated[
            FlextInfraModelsProjectGitignore.ProjectGitignoreConfig,
            m.Field(description="Ignore patterns owned by the current project."),
        ]

    class ProjectManagedArtifactsResolution(m.ArbitraryTypesModel):
        """Composed project configuration plus selector provenance."""

        artifacts: Annotated[
            (FlextInfraModelsProjectArtifacts.ProjectManagedArtifactsConfig),
            m.Field(description="Composed managed-artifact configuration."),
        ]
        mise_tool_sources: Annotated[
            Mapping[t.NonEmptyStr, Path],
            m.Field(description="Source YAML path for every local Mise selector."),
        ]

    class ProjectManagedArtifactsSnapshot(m.ArbitraryTypesModel):
        """One immutable YAML snapshot and its single parsed resolution."""

        sources: Annotated[
            tuple[t.Port[p.Cli.AtomicFileState], ...],
            m.Field(description="Ordered exact project configuration sources."),
        ]
        resolution: Annotated[
            (FlextInfraModelsProjectArtifacts.ProjectManagedArtifactsResolution),
            m.Field(description="Managed artifacts parsed from those exact sources."),
        ]


__all__: list[str] = ["FlextInfraModelsProjectArtifacts"]
