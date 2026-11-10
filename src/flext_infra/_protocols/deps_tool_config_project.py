# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_project
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra._protocols import (
        FlextInfraProtocolsDepsToolConfigProjectMise,
        FlextInfraProtocolsProjectGitignore,
    )


class FlextInfraProtocolsDepsToolConfigProject:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectManagedArtifactsFragment(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def Mise(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigProjectMise.ProjectMiseConfig | None:
            """Mise section declared by this source."""
            ...

        @property
        def Gitignore(
            self,
        ) -> FlextInfraProtocolsProjectGitignore.ProjectGitignoreConfig | None:
            """Gitignore section declared by this source."""
            ...

    @runtime_checkable
    class ProjectConfigDocument(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def ManagedArtifacts(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigProject.ProjectManagedArtifactsFragment:
            """Project-local managed artifact configuration."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigProject",
]
