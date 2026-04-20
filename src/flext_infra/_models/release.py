"""Domain models for the release subpackage."""

from __future__ import annotations

from typing import Annotated

from flext_core import m

from flext_infra import FlextInfraModelsMixins, t


class FlextInfraModelsRelease:
    """Models for release management."""

    class BuildRecord(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Base model for build result data."""

        path: t.NonEmptyStr = m.Field(description="Project absolute path")
        exit_code: t.NonNegativeInt = m.Field(
            description="Exit code returned by make build"
        )
        log: t.NonEmptyStr = m.Field(description="Build log file path")

    class ReleaseSpec(
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        m.ArbitraryTypesModel,
    ):
        """Release descriptor with version, tag, and bump metadata."""

        bump_type: Annotated[t.NonEmptyStr, m.Field(description="Release bump type")]

    class BuildReport(m.ArbitraryTypesModel):
        """Aggregated build report payload written to JSON."""

        @staticmethod
        def _records_default() -> list[FlextInfraModelsRelease.BuildRecord]:
            return []

        version: Annotated[t.NonEmptyStr, m.Field(description="Release version")]
        total: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total projects attempted"),
        ]
        failures: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total projects with non-zero exit"),
        ]
        records: Annotated[
            list[FlextInfraModelsRelease.BuildRecord],
            m.Field(
                default_factory=_records_default,
                description="Per-project build records",
            ),
        ]

    class ReleaseOrchestratorConfig(
        FlextInfraModelsMixins.ProjectNamesOptionalMixin,
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextInfraModelsMixins.ReleaseAutomationMixin,
        m.ArbitraryTypesModel,
    ):
        """Configuration for release workflow execution."""

        dry_run: Annotated[bool, m.Field(description="Dry run flag")] = False
        phases: Annotated[t.StrSequence, m.Field(description="Ordered list of phases")]
        create_branches: Annotated[
            bool, m.Field(description="Create branches flag")
        ] = True
        next_dev: Annotated[bool, m.Field(description="Next dev flag")] = False
        next_bump: Annotated[str, m.Field(description="Next bump")] = "minor"

    class ReleasePhaseDispatchConfig(
        FlextInfraModelsMixins.ProjectNamesListMixin,
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextInfraModelsMixins.ReleaseAutomationMixin,
        m.ArbitraryTypesModel,
    ):
        """Configuration for single release phase dispatch."""

        dry_run: Annotated[bool, m.Field(description="Dry run flag")] = False
        phase: Annotated[t.NonEmptyStr, m.Field(description="Release phase")]


__all__: list[str] = ["FlextInfraModelsRelease"]
