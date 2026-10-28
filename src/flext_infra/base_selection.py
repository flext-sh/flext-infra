"""Project-selection service base for flext-infra command services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Annotated

from flext_infra import FlextInfraBaseProjects, FlextInfraServiceBase, m, t


class FlextInfraProjectSelectionServiceBase[
    TDomainResult: t.JsonValue | t.BaseModelType | Path | datetime,
](
    FlextInfraServiceBase[TDomainResult],
    FlextInfraBaseProjects,
):
    """Shared service foundation for commands that target workspace projects.

    The bound is JsonPayload's value union without its Pydantic serialization
    metadata, which Mypy's Pydantic plugin erases when used as an upper bound.
    """

    selected_projects: Annotated[
        Sequence[str] | None,
        m.BeforeValidator(lambda value: (value,) if isinstance(value, str) else value),
        m.Field(
            default=None,
            alias="projects",
            description="Projects to process",
        ),
    ] = None


__all__: list[str] = ["FlextInfraProjectSelectionServiceBase"]
