"""Domain models for the release subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsMixins, t


class FlextInfraReleaseModels:
    """Models for release management."""

    class BuildRecord(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Base model for build result data."""

        path: Annotated[t.NonEmptyStr, Field(description="Project absolute path")]
        exit_code: Annotated[
            t.NonNegativeInt,
            Field(description="Exit code returned by make build"),
        ]
        log: Annotated[t.NonEmptyStr, Field(description="Build log file path")]

    class ReleaseSpec(
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Release descriptor with version, tag, and bump metadata."""

        bump_type: Annotated[t.NonEmptyStr, Field(description="Release bump type")]

    class BuildReport(FlextModels.ArbitraryTypesModel):
        """Aggregated build report payload written to JSON."""

        @staticmethod
        def _records_default() -> list[FlextInfraReleaseModels.BuildRecord]:
            return []

        version: Annotated[t.NonEmptyStr, Field(description="Release version")]
        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total projects attempted"),
        ]
        failures: Annotated[
            t.NonNegativeInt,
            Field(description="Total projects with non-zero exit"),
        ]
        records: Annotated[
            list[FlextInfraReleaseModels.BuildRecord],
            Field(
                default_factory=_records_default,
                description="Per-project build records",
            ),
        ]

    class ReleaseOrchestratorConfig(
        FlextInfraModelsMixins.DryRunFalseMixin,
        FlextInfraModelsMixins.ProjectNamesOptionalMixin,
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextInfraModelsMixins.ReleaseAutomationMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Configuration for release workflow execution."""

        phases: Annotated[t.StrSequence, Field(description="Ordered list of phases")]
        create_branches: Annotated[
            bool, Field(default=True, description="Create branches flag")
        ]
        next_dev: Annotated[bool, Field(default=False, description="Next dev flag")]
        next_bump: Annotated[str, Field(default="minor", description="Next bump")]

    class ReleasePhaseDispatchConfig(
        FlextInfraModelsMixins.DryRunFalseMixin,
        FlextInfraModelsMixins.ProjectNamesListMixin,
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextInfraModelsMixins.ReleaseAutomationMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Configuration for single release phase dispatch."""

        phase: Annotated[t.NonEmptyStr, Field(description="Release phase")]


__all__ = ["FlextInfraReleaseModels"]
