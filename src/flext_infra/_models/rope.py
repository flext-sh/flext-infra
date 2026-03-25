"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_core import FlextModels
from pydantic import Field


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class Location(FlextModels.FrozenStrictModel):
        """A symbol occurrence location found by rope's find_occurrences."""

        file: Annotated[str, Field(description="Relative file path within project")]
        line: Annotated[int, Field(description="Line number (1-based)")]
        start: Annotated[int, Field(description="Start character offset")]
        end: Annotated[int, Field(description="End character offset")]
        unsure: Annotated[
            bool, Field(default=False, description="Whether match is uncertain")
        ]

    class MoveResult(FlextModels.FrozenStrictModel):
        """Result of a MoveGlobal operation."""

        symbol: Annotated[str, Field(description="Name of the moved symbol")]
        source: Annotated[str, Field(description="Source module path")]
        destination: Annotated[str, Field(description="Destination module path")]
        changed_files: Annotated[int, Field(description="Number of files updated")]

    class RefactorSummary(FlextModels.FrozenStrictModel):
        """Summary of a rope refactoring operation."""

        operation: Annotated[
            str,
            Field(
                description="Operation name (rename/move/extract/inline/restructure)"
            ),
        ]
        files_changed: Annotated[int, Field(description="Number of files modified")]
        applied: Annotated[
            bool, Field(description="Whether changes were applied to disk")
        ]


__all__ = ["FlextInfraModelsRope"]
