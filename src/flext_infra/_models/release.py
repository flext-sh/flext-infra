"""Domain models for the release subpackage."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import t


class FlextInfraReleaseModels:
    """Models for release management."""

    class BuildRecord(FlextModels.ArbitraryTypesModel):
        """Base model for build result data."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        path: Annotated[t.NonEmptyStr, Field(description="Project absolute path")]
        exit_code: Annotated[
            t.NonNegativeInt,
            Field(description="Exit code returned by make build"),
        ]
        log: Annotated[t.NonEmptyStr, Field(description="Build log file path")]

    class ReleaseSpec(FlextModels.ArbitraryTypesModel):
        """Release descriptor with version, tag, and bump metadata."""

        version: Annotated[
            t.NonEmptyStr,
            Field(description="Semantic version string"),
        ]
        tag: Annotated[t.NonEmptyStr, Field(description="Git tag for release")]
        bump_type: Annotated[t.NonEmptyStr, Field(description="Release bump type")]

    class BuildReport(FlextModels.ArbitraryTypesModel):
        """Aggregated build report payload written to JSON."""

        version: Annotated[t.NonEmptyStr, Field(description="Release version")]
        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total projects attempted"),
        ]
        failures: Annotated[
            t.NonNegativeInt,
            Field(description="Total projects with non-zero exit"),
        ]
        records: Sequence[FlextInfraReleaseModels.BuildRecord] = Field(
            default_factory=list, description="Per-project build records"
        )

    class ReleaseOrchestratorConfig(FlextModels.ArbitraryTypesModel):
        """Configuration for release workflow execution."""

        workspace_root: Annotated[Path, Field(description="Workspace root")]
        version: Annotated[t.NonEmptyStr, Field(description="Release version")]
        tag: Annotated[t.NonEmptyStr, Field(description="Release tag")]
        phases: Annotated[t.StrSequence, Field(description="Ordered list of phases")]
        project_names: Annotated[
            t.StrSequence | None, Field(default=None, description="Project names")
        ]
        dry_run: Annotated[bool, Field(default=False, description="Dry run flag")]
        push: Annotated[bool, Field(default=False, description="Push flag")]
        dev_suffix: Annotated[bool, Field(default=False, description="Dev suffix flag")]
        create_branches: Annotated[
            bool, Field(default=True, description="Create branches flag")
        ]
        next_dev: Annotated[bool, Field(default=False, description="Next dev flag")]
        next_bump: Annotated[str, Field(default="minor", description="Next bump")]

    class ReleasePhaseDispatchConfig(FlextModels.ArbitraryTypesModel):
        """Configuration for single release phase dispatch."""

        phase: Annotated[t.NonEmptyStr, Field(description="Release phase")]
        workspace_root: Annotated[Path, Field(description="Workspace root")]
        version: Annotated[t.NonEmptyStr, Field(description="Release version")]
        tag: Annotated[t.NonEmptyStr, Field(description="Git tag")]
        project_names: Annotated[
            t.StrSequence, Field(default_factory=list, description="Project names")
        ]
        dry_run: Annotated[bool, Field(default=False, description="Dry run flag")]
        push: Annotated[bool, Field(default=False, description="Push flag")]
        dev_suffix: Annotated[bool, Field(default=False, description="Dev suffix flag")]


__all__ = ["FlextInfraReleaseModels"]
