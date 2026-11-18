"""Extracted facade class for census.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import override

from flext_infra import m, p, r, t
from flext_infra.refactor._census import (
    FlextInfraRefactorCensusCollectHelpers,
    FlextInfraRefactorCensusRender,
)


class FlextInfraRefactorCensus(
    FlextInfraRefactorCensusCollectHelpers,
    FlextInfraRefactorCensusRender,
):
    """Facade for census."""

    workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl] = (
        m.Field(exclude=True, description="Injected candidate Rope workspace factory")
    )

    source_preview: t.Port[p.Infra.SourcePreview] = m.Field(
        exclude=True,
        description="Injected authenticated source preview capability",
    )

    @property
    def json_output_path(self) -> Path | None:
        """Structured census report destination declared by the options."""
        return (
            Path(self.options.json_output)
            if self.options.json_output is not None
            else None
        )

    @property
    def impact_map_output_path(self) -> Path | None:
        """Impact-map report destination declared by the options."""
        return (
            Path(self.options.impact_map_output)
            if self.options.impact_map_output is not None
            else None
        )

    def build_report(self) -> p.Infra.WorkspaceReport:
        """Inventory the selected modules and assemble the census report.

        Returns:
            The resulting ``m.Infra.WorkspaceReport``.

        """
        with self.workspace_factory(self.repository_root, None) as rope:
            return self._collect_report(rope, source_preview=self.source_preview)

    @override
    def execute(self) -> p.Result[p.Infra.WorkspaceReport]:
        """Run the census and return the report through the result boundary.

        Returns:
            The resulting ``p.Result[p.Infra.WorkspaceReport]``.

        """
        return r[p.Infra.WorkspaceReport].ok(self.build_report())


__all__: list[str] = ["FlextInfraRefactorCensus"]
