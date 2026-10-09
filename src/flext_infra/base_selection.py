"""Project-selection service base for flext-infra command services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import FlextInfraServiceBase, m, t
from flext_infra._base_projects import FlextInfraProjectSelectionMixin


class FlextInfraProjectSelectionServiceBase[TDomainResult](
    FlextInfraServiceBase[TDomainResult],
    FlextInfraProjectSelectionMixin,
):
    """Shared service foundation for commands that target workspace projects."""

    selected_projects: t.StrSequence | None = m.Field(
        default=None,
        alias="projects",
        description="Projects to process",
    )

    @m.field_validator("selected_projects", mode="before")
    @classmethod
    def _wrap_single_project(cls, value: object) -> object:
        """Coerce one bare project name (a CLI ``--projects .``) to a sequence.

        Returns:
            The canonical sequence value for the field.

        """
        return (value,) if isinstance(value, str) else value


__all__: list[str] = ["FlextInfraProjectSelectionServiceBase"]
