# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_project
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToolConfigProject:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectManagedArtifactsFragment(Protocol):
        """Structural data contract projected from the owning model."""

        Mise: p.Infra.ProjectMiseConfig | None
        Gitignore: p.Infra.ProjectGitignoreConfig | None

    @runtime_checkable
    class ProjectConfigDocument(Protocol):
        """Structural data contract projected from the owning model."""

        ManagedArtifacts: p.Infra.ProjectManagedArtifactsFragment


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigProject",
]
