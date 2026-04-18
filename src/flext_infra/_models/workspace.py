"""Domain models for the workspace subpackage."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar

from flext_core import m
from flext_infra import FlextInfraModelsMixins, c, t


class FlextInfraModelsWorkspace:
    """Models for workspace discovery, sync, and migration.

    Canonical base policy:
    - ``ArbitraryTypesModel`` for mutable discovery and migration payloads.
    - ``ContractModel`` reserved for immutable workspace settings contracts.
    """

    class ProjectInfo(
        FlextInfraModelsMixins.ProjectEntryNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Discovered project metadata for workspace operations."""

        model_config = m.ConfigDict(frozen=True, validate_default=False)

        path: Annotated[Path, m.Field(description="Absolute or relative project path")]
        stack: Annotated[
            t.NonEmptyStr,
            m.Field(description="Primary technology stack"),
        ]
        has_tests: Annotated[bool, m.Field(description="Project has test suite")] = (
            False
        )
        has_src: Annotated[
            bool, m.Field(description="Project has source directory")
        ] = True
        project_class: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Docs/governance project classification",
            ),
        ] = "platform"
        package_name: Annotated[
            str, m.Field(description="Primary Python package name")
        ] = ""
        workspace_role: Annotated[
            c.Infra.WorkspaceProjectRole,
            m.Field(
                description="Operational role relative to the uv workspace root",
            ),
        ] = c.Infra.WorkspaceProjectRole.ATTACHED

    class ProjectPyprojectState(m.ArbitraryTypesModel):
        """Centralized parsed pyproject state reused across discovery services.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        model_config = m.ConfigDict(frozen=True, validate_default=False)

        project_root: Annotated[Path, m.Field(description="Project root path")]
        pyproject_path: Annotated[Path, m.Field(description="Resolved pyproject path")]
        payload: Annotated[
            t.Infra.ContainerDict,
            m.Field(description="Parsed pyproject payload"),
        ] = m.Field(default_factory=dict)
        docs_meta: Annotated[
            t.Infra.ContainerDict,
            m.Field(description="Parsed tool.flext.docs payload"),
        ] = m.Field(default_factory=dict)
        project_name: Annotated[str, m.Field(description="Declared project name")] = ""
        package_name: Annotated[str, m.Field(description="Primary package name")] = ""
        dependency_names: Annotated[
            t.StrSequence,
            m.Field(description="Declared dependency names"),
        ] = m.Field(default_factory=tuple)

    class SyncResult(m.ArbitraryTypesModel):
        """Result payload for sync operations."""

        files_changed: Annotated[
            t.NonNegativeInt, m.Field(description="Total changed files")
        ] = 0
        source: Annotated[Path, m.Field(description="Sync source path")]
        target: Annotated[Path, m.Field(description="Sync target path")]
        timestamp: Annotated[
            datetime,
            m.Field(
                description="Execution timestamp in UTC",
            ),
        ] = m.Field(default_factory=lambda: datetime.now(UTC))

    class MigrationResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Migration operation outcome with applied changes and errors."""

        changes: Annotated[
            t.StrSequence,
            m.Field(description="Applied changes"),
        ] = m.Field(default_factory=tuple)
        errors: Annotated[
            t.StrSequence,
            m.Field(description="Migration errors"),
        ] = m.Field(default_factory=tuple)


__all__: list[str] = ["FlextInfraModelsWorkspace"]
