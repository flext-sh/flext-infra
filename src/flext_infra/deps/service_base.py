"""Shared MRO bases for thin dependency services."""

from __future__ import annotations

from abc import ABC
from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import Annotated

from flext_infra import FlextInfraServiceBase, m, t


class FlextInfraDepsServiceBase(FlextInfraServiceBase[bool], ABC):
    """Shared deps base extending the canonical infra service foundation."""


class FlextInfraDepsProjectServiceBase(FlextInfraDepsServiceBase, ABC):
    """Shared project-selection helpers for dependency services."""

    selected_projects: Annotated[
        t.StrSequence | None,
        m.Field(alias="projects", description="Projects to process"),
    ] = None

    @property
    def project_names(self) -> t.StrSequence | None:
        """Return normalized project selectors."""
        return self.normalize_selected_projects(self.selected_projects)

    @property
    def project_dirs(self) -> Sequence[Path] | None:
        """Resolve selected project directories relative to the workspace root."""
        return self.selected_project_dirs(self.selected_projects)


__all__: list[str] = [
    "FlextInfraDepsProjectServiceBase",
    "FlextInfraDepsServiceBase",
]
