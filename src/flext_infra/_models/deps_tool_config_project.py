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


# The composed document layer is the module's single declared owner. The
# layers below it are the mechanism of that composition -- each exists so a
# sibling model resolves as a base-class attribute at definition time -- and
# are reached through it, never imported on their own. Declaring them here
# made the module look like four competing owners, which left the class-nesting
# planner unable to name one and failed `make mod` for the whole fleet.
__all__: list[str] = ["FlextInfraModelsDepsToolConfigProject"]
