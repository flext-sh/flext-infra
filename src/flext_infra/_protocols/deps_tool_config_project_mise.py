# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_project_mise
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsDepsToolConfigProjectMise:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectMiseTool(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        version: t.NonEmptyStr

    @runtime_checkable
    class ProjectMiseConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tools(
            self,
        ) -> Mapping[
            t.NonEmptyStr, FlextInfraProtocolsDepsToolConfigProjectMise.ProjectMiseTool
        ]:
            """Project-local Mise tools added to generated config."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigProjectMise",
]
