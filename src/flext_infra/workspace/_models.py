"""Domain models for the workspace subpackage."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from flext_core import FlextModels
from pydantic import Field

from flext_infra import t


class FlextInfraWorkspaceModels:
    """Models for workspace discovery, sync, and migration.

    Canonical base policy:
    - ``ArbitraryTypesModel`` for mutable discovery and migration payloads.
    - ``FrozenStrictModel`` reserved for immutable workspace config contracts.
    """

    class ProjectInfo(FlextModels.ArbitraryTypesModel):
        """Discovered project metadata for workspace operations."""

        name: Annotated[t.NonEmptyStr, Field(description="Project name")]
        path: Annotated[Path, Field(description="Absolute or relative project path")]
        stack: Annotated[
            t.NonEmptyStr,
            Field(description="Primary technology stack"),
        ]
        has_tests: Annotated[
            bool,
            Field(default=False, description="Project has test suite"),
        ] = False
        has_src: Annotated[
            bool,
            Field(default=True, description="Project has source directory"),
        ] = True

    class SyncResult(FlextModels.ArbitraryTypesModel):
        """Result payload for sync operations."""

        files_changed: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total changed files"),
        ] = 0
        source: Annotated[Path, Field(description="Sync source path")]
        target: Annotated[Path, Field(description="Sync target path")]
        timestamp: Annotated[
            datetime,
            Field(
                default_factory=lambda: datetime.now(UTC),
                description="Execution timestamp in UTC",
            ),
        ] = Field(default_factory=lambda: datetime.now(UTC))

    class MigrationResult(FlextModels.ArbitraryTypesModel):
        """Migration operation outcome with applied changes and errors."""

        project: Annotated[t.NonEmptyStr, Field(description="Project identifier")]
        changes: Annotated[
            Sequence[str],
            Field(default_factory=list, description="Applied changes"),
        ] = Field(default_factory=list)
        errors: Annotated[
            Sequence[str],
            Field(default_factory=list, description="Migration errors"),
        ] = Field(default_factory=list)


__all__ = ["FlextInfraWorkspaceModels"]
