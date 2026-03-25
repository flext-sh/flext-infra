"""Domain models for the shared utilities subpackage.

Scan violation and result models used by infrastructure scanning utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from flext_core import FlextModels
from pydantic import Field


class FlextInfraModelsScan:
    """Shared utility domain models for scanning and analysis."""

    class ScanViolation(FlextModels.FrozenStrictModel):
        """A single violation found during file scanning."""

        line: Annotated[int, Field(description="Line number of the violation")]
        message: Annotated[
            str,
            Field(description="Human-readable violation description"),
        ]
        severity: Annotated[str, Field(description="Violation severity level")]
        rule_id: Annotated[
            str | None,
            Field(default=None, description="Optional rule identifier"),
        ]

    class ScanResult(FlextModels.ArbitraryTypesModel):
        """Result of scanning a single file."""

        file_path: Annotated[Path, Field(description="Path to the scanned file")]
        violations: Annotated[
            Sequence[FlextInfraModelsScan.ScanViolation],
            Field(
                description="Violations found in the file",
            ),
        ] = Field(default_factory=list)
        detector_name: Annotated[
            str,
            Field(description="Name of the detector that produced this result"),
        ]


__all__ = ["FlextInfraModelsScan"]
