"""Domain models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import FlextInfraDepsModelsToolConfig, t


class FlextInfraDepsModels(FlextInfraDepsModelsToolConfig):
    """Models for dependency detection and modernization reporting."""

    class DependencyLimitsInfo(m.ArbitraryTypesModel):
        """Dependency limits configuration metadata."""

        python_version: str | None = None
        limits_path: Annotated[str, Field(default="")] = ""

    class PipCheckReport(m.ArbitraryTypesModel):
        """Pip check execution report with status and output lines."""

        ok: bool = True
        lines: t.StrSequence = Field(default_factory=list)

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

        missing: t.StrSequence = Field(default_factory=list)
        unused: t.StrSequence = Field(default_factory=list)
        transitive: t.StrSequence = Field(default_factory=list)
        dev_in_runtime: t.StrSequence = Field(default_factory=list)
        raw_count: Annotated[t.NonNegativeInt, Field(default=0)] = 0

    class ProjectDependencyReport(m.ArbitraryTypesModel):
        """Project-level dependency report combining deptry results."""

        project: Annotated[t.NonEmptyStr, Field()]
        deptry: FlextInfraDepsModels.DeptryReport

    class TypingsReport(m.ArbitraryTypesModel):
        """Typing stubs analysis report with required/current/delta packages."""

        required_packages: t.StrSequence = Field(default_factory=list)
        hinted: t.StrSequence = Field(default_factory=list)
        missing_modules: t.StrSequence = Field(default_factory=list)
        current: t.StrSequence = Field(default_factory=list)
        to_add: t.StrSequence = Field(default_factory=list)
        to_remove: t.StrSequence = Field(default_factory=list)
        limits_applied: bool = False
        python_version: str | None = None

    class ProjectRuntimeReport(m.ArbitraryTypesModel):
        """Project runtime dependency and typings report."""

        deptry: FlextInfraDepsModels.DeptryReport
        typings: FlextInfraDepsModels.TypingsReport | None = None

    class WorkspaceDependencyReport(m.ArbitraryTypesModel):
        """Workspace-level dependency analysis report aggregating all projects."""

        workspace: str
        projects: Annotated[
            Mapping[str, FlextInfraDepsModels.ProjectRuntimeReport],
            Field(description="Per-project reports"),
        ] = Field(default_factory=dict)
        pip_check: FlextInfraDepsModels.PipCheckReport | None = None
        dependency_limits: FlextInfraDepsModels.DependencyLimitsInfo | None = None


__all__ = ["FlextInfraDepsModels"]
