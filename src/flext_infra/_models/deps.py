"""Domain models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import FlextInfraDepsModelsToolConfig, FlextInfraModelsMixins, t


class FlextInfraDepsModels(FlextInfraDepsModelsToolConfig):
    """Models for dependency detection and modernization reporting."""

    class DependencyLimitsInfo(m.ArbitraryTypesModel):
        """Dependency limits configuration metadata."""

        python_version: Annotated[
            str | None, Field(default=None, description="Python version")
        ] = None
        limits_path: Annotated[
            str, Field(default="", description="Path to limits file")
        ] = ""

    class PipCheckReport(m.ArbitraryTypesModel):
        """Pip check execution report with status and output lines."""

        ok: Annotated[
            bool, Field(default=True, description="Whether pip check passed")
        ] = True
        lines: Annotated[t.StrSequence, Field(description="Pip check output lines")] = (
            Field(default_factory=list)
        )

    class DeptryIssueGroups(m.ArbitraryTypesModel):
        """Deptry issue grouping model by error code (DEP001-DEP004)."""

        dep001: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(description="DEP001 issues"),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep002: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(description="DEP002 issues"),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep003: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(description="DEP003 issues"),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep004: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(description="DEP004 issues"),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())

    class DeptryReport(m.ArbitraryTypesModel):
        """Deptry analysis report with categorized issue modules."""

        missing: Annotated[t.StrSequence, Field(description="Missing dependencies")] = (
            Field(default_factory=list)
        )
        unused: Annotated[t.StrSequence, Field(description="Unused dependencies")] = (
            Field(default_factory=list)
        )
        transitive: Annotated[
            t.StrSequence, Field(description="Transitive dependencies")
        ] = Field(default_factory=list)
        dev_in_runtime: Annotated[
            t.StrSequence, Field(description="Dev dependencies in runtime")
        ] = Field(default_factory=list)
        raw_count: Annotated[
            t.NonNegativeInt, Field(default=0, description="Raw issue count")
        ] = 0

    class ProjectDependencyReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Project-level dependency report combining deptry results."""

        deptry: FlextInfraDepsModels.DeptryReport = Field(description="Deptry report")

    class TypingsReport(m.ArbitraryTypesModel):
        """Typing stubs analysis report with required/current/delta packages."""

        required_packages: Annotated[
            t.StrSequence, Field(description="Required packages")
        ] = Field(default_factory=list)
        hinted: Annotated[t.StrSequence, Field(description="Hinted packages")] = Field(
            default_factory=list
        )
        missing_modules: Annotated[
            t.StrSequence, Field(description="Missing modules")
        ] = Field(default_factory=list)
        current: Annotated[t.StrSequence, Field(description="Current typings")] = Field(
            default_factory=list
        )
        to_add: Annotated[t.StrSequence, Field(description="Typings to add")] = Field(
            default_factory=list
        )
        to_remove: Annotated[t.StrSequence, Field(description="Typings to remove")] = (
            Field(default_factory=list)
        )
        limits_applied: Annotated[
            bool, Field(default=False, description="Whether limits were applied")
        ] = False
        python_version: Annotated[
            str | None, Field(default=None, description="Python version")
        ] = None

    class ProjectRuntimeReport(m.ArbitraryTypesModel):
        """Project runtime dependency and typings report."""

        deptry: FlextInfraDepsModels.DeptryReport = Field(description="Deptry report")
        typings: FlextInfraDepsModels.TypingsReport | None = Field(
            default=None, description="Typings report"
        )

    class WorkspaceDependencyReport(m.ArbitraryTypesModel):
        """Workspace-level dependency analysis report aggregating all projects."""

        workspace: Annotated[str, Field(description="Workspace name")]
        projects: Mapping[str, FlextInfraDepsModels.ProjectRuntimeReport] = Field(
            default_factory=dict, description="Per-project reports"
        )
        pip_check: FlextInfraDepsModels.PipCheckReport | None = Field(
            default=None, description="Pip check report"
        )
        dependency_limits: FlextInfraDepsModels.DependencyLimitsInfo | None = Field(
            default=None, description="Dependency limits"
        )


__all__ = ["FlextInfraDepsModels"]
