"""Source discovery specification models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigStatic:
    """Source discovery specification models."""

    class SourceScanSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Canonical production roots and recursively ignored directories."""

        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Ordered production source directory names"),
        ]

    class ConsolidationOutcome(FlextInfraModelsConfigContract.ConfigContract):
        """Per-file constants consolidation outcome."""

        found: Annotated[
            int, m.Field(description="Canonical matches found in the file")
        ]
        lines: Annotated[
            tuple[str, ...], m.Field(description="Report lines for the file")
        ]
        record: Annotated[
            t.JsonMapping | None,
            m.Field(description="Applied-change record; none outside application"),
        ]
        applied: Annotated[int, m.Field(description="Replacements applied to the file")]


__all__: list[str] = ["FlextInfraModelsConfigStatic"]
