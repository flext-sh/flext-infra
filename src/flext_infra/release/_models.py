"""Domain models for the release subpackage."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels


class FlextInfraReleaseModels:
    """Models for release management."""

    class BuildRecord(FlextModels.ArbitraryTypesModel):
        """Base model for build result data."""

        project: Annotated[str, Field(min_length=1, description="Project name")]
        path: Annotated[str, Field(min_length=1, description="Project absolute path")]
        exit_code: Annotated[
            int,
            Field(ge=0, description="Exit code returned by make build"),
        ]
        log: Annotated[str, Field(min_length=1, description="Build log file path")]

    class ReleaseSpec(FlextModels.ArbitraryTypesModel):
        """Release descriptor with version, tag, and bump metadata."""

        version: Annotated[
            str,
            Field(min_length=1, description="Semantic version string"),
        ]
        tag: Annotated[str, Field(min_length=1, description="Git tag for release")]
        bump_type: Annotated[str, Field(min_length=1, description="Release bump type")]

    class BuildReport(FlextModels.ArbitraryTypesModel):
        """Aggregated build report payload written to JSON."""

        version: Annotated[str, Field(min_length=1, description="Release version")]
        total: Annotated[int, Field(ge=0, description="Total projects attempted")]
        failures: Annotated[
            int,
            Field(ge=0, description="Total projects with non-zero exit"),
        ]
        records: Annotated[
            Sequence[FlextInfraReleaseModels.BuildRecord],
            Field(
                default_factory=list,
                description="Per-project build records",
            ),
        ]

    class ReleaseOrchestratorConfig(FlextModels.ArbitraryTypesModel):
        """Configuration for release workflow execution."""

        workspace_root: Annotated[Path, Field(description="Workspace root")]
        version: Annotated[str, Field(min_length=1)]
        tag: Annotated[str, Field(min_length=1)]
        phases: Annotated[list[str], Field(description="Ordered list of phases")]
        project_names: Annotated[list[str] | None, Field(default=None)]
        dry_run: Annotated[bool, Field(default=False)]
        push: Annotated[bool, Field(default=False)]
        dev_suffix: Annotated[bool, Field(default=False)]
        create_branches: Annotated[bool, Field(default=True)]
        next_dev: Annotated[bool, Field(default=False)]
        next_bump: Annotated[str, Field(default="minor")]

    class ReleasePhaseDispatchConfig(FlextModels.ArbitraryTypesModel):
        """Configuration for single release phase dispatch."""

        phase: Annotated[str, Field(min_length=1)]
        workspace_root: Annotated[Path, Field(description="Workspace root")]
        version: Annotated[str, Field(min_length=1)]
        tag: Annotated[str, Field(min_length=1)]
        project_names: Annotated[list[str], Field(default_factory=list)]
        dry_run: Annotated[bool, Field(default=False)]
        push: Annotated[bool, Field(default=False)]
        dev_suffix: Annotated[bool, Field(default=False)]


__all__ = ["FlextInfraReleaseModels"]
