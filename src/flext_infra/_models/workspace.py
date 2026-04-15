"""Domain models for the workspace subpackage."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from pydantic import ConfigDict, Field

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

        model_config = ConfigDict(frozen=True, validate_default=False)

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
        project_class: Annotated[
            t.NonEmptyStr,
            Field(
                default="platform",
                description="Docs/governance project classification",
            ),
        ] = "platform"
        package_name: Annotated[
            str,
            Field(default="", description="Primary Python package name"),
        ] = ""
        workspace_role: Annotated[
            c.Infra.WorkspaceProjectRole,
            Field(
                default=c.Infra.WorkspaceProjectRole.ATTACHED,
                description="Operational role relative to the uv workspace root",
            ),
        ] = c.Infra.WorkspaceProjectRole.ATTACHED

    class ProjectMeta(
        FlextInfraModelsMixins.ProjectEntryNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Extracted project metadata for makefile generation."""

        python_version: Annotated[t.NonEmptyStr, Field(description="Python version")]
        description: Annotated[t.NonEmptyStr, Field(description="Project description")]

    class ProjectPyprojectState(m.ArbitraryTypesModel):
        """Centralized parsed pyproject state reused across discovery services."""

        model_config = ConfigDict(frozen=True, validate_default=False)

        project_root: Annotated[Path, Field(description="Project root path")]
        pyproject_path: Annotated[Path, Field(description="Resolved pyproject path")]
        payload: Annotated[
            t.Infra.ContainerDict,
            Field(description="Parsed pyproject payload"),
        ] = Field(default_factory=dict)
        docs_meta: Annotated[
            t.Infra.ContainerDict,
            Field(description="Parsed tool.flext.docs payload"),
        ] = Field(default_factory=dict)
        project_name: Annotated[
            str,
            Field(default="", description="Declared project name"),
        ] = ""
        package_name: Annotated[
            str,
            Field(default="", description="Primary package name"),
        ] = ""
        dependency_names: Annotated[
            t.StrSequence,
            Field(description="Declared dependency names"),
        ] = Field(default_factory=tuple)

    class SyncResult(m.ArbitraryTypesModel):
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
                description="Execution timestamp in UTC",
            ),
        ] = Field(default_factory=lambda: datetime.now(UTC))

    class MigrationResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Migration operation outcome with applied changes and errors."""

        changes: Annotated[
            t.StrSequence,
            Field(description="Applied changes"),
        ] = Field(default_factory=list)
        errors: Annotated[
            t.StrSequence,
            Field(description="Migration errors"),
        ] = Field(default_factory=list)


__all__: list[str] = ["FlextInfraModelsWorkspace"]
