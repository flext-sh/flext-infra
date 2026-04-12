"""Domain models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence
from pathlib import Path
from typing import Annotated

from pydantic import ConfigDict, Field, computed_field

from flext_core import m
from flext_infra import FlextInfraModelsDepsToolSettings, c, t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsDeps(FlextInfraModelsDepsToolSettings):
    """Models for dependency detection and modernization reporting."""

    class DetectCommand(FlextInfraModelsMixins.ProjectMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps detect``."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply follow-up typing dependency installs",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False
        output_format: Annotated[
            str,
            Field(
                default="text",
                alias="format",
                description="Output format for dependency report",
            ),
        ] = "text"
        output: Annotated[
            str | None,
            Field(default=None, description="Optional output report path"),
        ] = None
        quiet: Annotated[
            bool,
            Field(default=False, description="Reduce command output"),
        ] = False
        no_fail: Annotated[
            bool,
            Field(
                default=False,
                alias="no-fail",
                description="Exit successfully even when issues are found",
            ),
        ] = False
        typings: Annotated[
            bool,
            Field(default=False, description="Detect required typing packages"),
        ] = False
        apply_typings: Annotated[
            bool,
            Field(
                default=False,
                alias="apply-typings",
                description="Install missing typing packages into the typings group",
            ),
        ] = False
        no_pip_check: Annotated[
            bool,
            Field(
                default=False,
                alias="no-pip-check",
                description="Skip workspace pip check",
            ),
        ] = False
        limits: Annotated[
            str | None,
            Field(default=None, description="Path to dependency limits TOML"),
        ] = None

        @computed_field  # type: ignore[prop-decorator]
        @property
        def dry_run(self) -> bool:
            """Whether follow-up dependency installation is disabled."""
            return not self.apply

        @property
        def output_path(self) -> Path | None:
            """Return the resolved explicit output path when provided."""
            if self.output is None:
                return None
            return Path(self.output).expanduser().resolve()

        @property
        def limits_path(self) -> Path | None:
            """Return the resolved dependency limits path when provided."""
            if self.limits is None:
                return None
            return Path(self.limits).expanduser().resolve()

    class ExtraPathsCommand(FlextInfraModelsMixins.ProjectMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps extra-paths``."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply synchronized path changes",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False

        @computed_field  # type: ignore[prop-decorator]
        @property
        def dry_run(self) -> bool:
            """Whether path synchronization should avoid writing."""
            return not self.apply

    class InternalSyncCommand(FlextInfraModelsMixins.BaseMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps internal-sync``."""

    class ModernizeCommand(FlextInfraModelsMixins.ProjectMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps modernize``."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply pyproject modernization changes",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False
        check: Annotated[
            bool,
            Field(default=False, description="Run in check mode"),
        ] = False
        audit: Annotated[
            bool,
            Field(default=False, description="Audit pyproject changes without writing"),
        ] = False
        skip_check: Annotated[
            bool,
            Field(
                default=False,
                alias="skip-check",
                description="Skip post-write validation step",
            ),
        ] = False
        skip_comments: Annotated[
            bool,
            Field(
                default=False,
                alias="skip-comments",
                description="Skip modernization of explanatory comments",
            ),
        ] = False

        @computed_field  # type: ignore[prop-decorator]
        @property
        def dry_run(self) -> bool:
            """Whether modernization should avoid writing changes."""
            return not self.apply

    class PathSyncCommand(FlextInfraModelsMixins.ProjectMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra deps path-sync``."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply dependency path rewrites",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False
        mode: Annotated[
            t.Infra.PathSyncMode,
            Field(default="auto", description="Dependency path rewrite mode"),
        ] = "auto"

        @computed_field  # type: ignore[prop-decorator]
        @property
        def dry_run(self) -> bool:
            """Whether dependency path rewrites should avoid writing."""
            return not self.apply

    class PyprojectDocumentState(m.ArbitraryTypesModel):
        """Centralized normalized TOML state reused across deps workflows."""

        model_config = ConfigDict(validate_default=False)

        pyproject_path: Annotated[
            Path,
            Field(description="Resolved pyproject path"),
        ]
        original_rendered: Annotated[
            str,
            Field(description="Original TOML source text"),
        ] = ""
        payload: Annotated[
            MutableMapping[str, t.Cli.JsonValue],
            Field(description="Validated plain TOML payload"),
        ] = Field(default_factory=dict)

    class PathSyncDocumentState(m.ArbitraryTypesModel):
        """Centralized path-sync payload reused across dependency rewrite passes."""

        model_config = ConfigDict(validate_default=False)

        pyproject_path: Annotated[
            Path,
            Field(description="Resolved pyproject path"),
        ]
        original_rendered: Annotated[
            str,
            Field(description="Original TOML source text"),
        ] = ""
        payload: Annotated[
            MutableMapping[str, t.Cli.JsonValue],
            Field(description="Validated plain TOML payload"),
        ] = Field(default_factory=dict)

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

        deptry: FlextInfraModelsDeps.DeptryReport = Field(description="Deptry report")

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

        deptry: FlextInfraModelsDeps.DeptryReport = Field(description="Deptry report")
        typings: FlextInfraModelsDeps.TypingsReport | None = Field(
            default=None, description="Typings report"
        )

    class WorkspaceDependencyReport(m.ArbitraryTypesModel):
        """Workspace-level dependency analysis report aggregating all projects."""

        workspace: Annotated[str, Field(description="Workspace name")]
        projects: Mapping[str, FlextInfraModelsDeps.ProjectRuntimeReport] = Field(
            default_factory=dict, description="Per-project reports"
        )
        pip_check: FlextInfraModelsDeps.PipCheckReport | None = Field(
            default=None, description="Pip check report"
        )
        dependency_limits: FlextInfraModelsDeps.DependencyLimitsInfo | None = Field(
            default=None, description="Dependency limits"
        )


__all__ = ["FlextInfraModelsDeps"]
