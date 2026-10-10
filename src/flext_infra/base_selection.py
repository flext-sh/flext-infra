"""Project-selection service base for flext-infra command services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_infra import m, t
from flext_infra._base_projects import FlextInfraProjectSelectionMixin
from flext_infra.base import FlextInfraServiceBase


class FlextInfraProjectSelectionServiceBase[TDomainResult](
    FlextInfraServiceBase[TDomainResult],
    FlextInfraProjectSelectionMixin,
):
    """Shared service foundation for commands that target workspace projects."""

    selected_projects: Annotated[
        t.StrSequence | None,
        m.BeforeValidator(
            lambda value: (value,) if isinstance(value, str) else value
        ),
        m.Field(
            default=None,
            alias="projects",
            description="Projects to process",
        ),
    ] = None


__all__: list[str] = ["FlextInfraProjectSelectionServiceBase"]
