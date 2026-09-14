"""Composed project-owned managed-artifact configuration document."""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from .deps_tool_config_project_artifacts import (
    FlextInfraModelsDepsToolConfigProjectArtifacts,
)


class FlextInfraModelsDepsToolConfigProject(
    FlextInfraModelsDepsToolConfigProjectArtifacts
):
    """Document layer composing every project-owned managed-artifact model."""

    class ProjectConfigDocument(m.ArbitraryTypesModel):
        """Relevant managed-artifact slice loaded from project config files."""

        ManagedArtifacts: Annotated[
            FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsConfig,
            m.Field(description="Project-local managed artifact configuration."),
        ] = m.Field(
            default_factory=(
                FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsConfig
            )
        )


__all__: list[str] = ["FlextInfraModelsDepsToolConfigProject"]
