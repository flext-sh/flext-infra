"""Scope-resolution domain models for refactor selectors (Task 0.4).

``ScopeResolution`` is the typed Pydantic v2 envelope returned by
``FlextInfraUtilitiesScopeSelector.scope_resolve`` — it carries the chosen
``c.Infra.ScopeLevel``, the workspace root, and the deterministic file
universe a verb must operate on. The model is frozen so consumers can pass
it down call chains without defensive copies.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import c


class FlextInfraModelsScope:
    """Scope-resolution result models exposed via ``m.Infra.*``."""

    class ScopeResolution(m.BaseModel):
        """Concrete file universe produced by a single scope-resolution call.

        ``files`` is sorted + deduplicated and every entry is contained
        inside ``workspace_root`` — invariant enforced by the producer
        (``FlextInfraUtilitiesScopeSelector.scope_resolve``).
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        level: Annotated[
            c.Infra.ScopeLevel,
            m.Field(description="Granularity of this resolution."),
        ]
        workspace_root: Annotated[
            Path,
            m.Field(description="Resolved workspace root every file lives under."),
        ]
        files: Annotated[
            tuple[Path, ...],
            m.Field(
                default_factory=tuple,
                description=(
                    "Sorted + deduplicated absolute file paths the verb "
                    "should operate on."
                ),
            ),
        ]
