"""Shared service foundation for flext-infra command services."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Self, TypeVar, override

from pydantic import ConfigDict, field_validator

from flext_cli import FlextCliSettings
from flext_core import (
    FlextProtocols,
    FlextSettings,
    m,
    s,
    t,
)
from flext_infra import FlextInfraConstantsBase, FlextInfraTypesBase

if TYPE_CHECKING:
    from flext_infra import p

TDomainResult = TypeVar(
    "TDomainResult",
    bound=t.ValueOrModel | Sequence[t.ValueOrModel],
)


class FlextInfraServiceBase(
    s[TDomainResult],
    ABC,
):
    """Domain command context shared by all flext-infra CLI services.

    Provides settings/bootstrap and normalized fields for workspace location,
    apply/dry-run toggles, output formatting, and project filtering.
    """

    model_config = ConfigDict(populate_by_name=True)

    @property
    @override
    def settings(self) -> FlextCliSettings:
        """Return the typed CLI settings namespace."""
        return FlextSettings.fetch_global().fetch_namespace("cli", FlextCliSettings)

    @classmethod
    @override
    def _runtime_bootstrap_options(cls) -> FlextProtocols.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace."""
        return m.RuntimeBootstrapOptions(settings_type=FlextCliSettings)

    workspace_root: Annotated[
        Path,
        m.Field(
            default_factory=Path.cwd,
            alias="workspace",
            description="Workspace root",
        ),
    ]
    apply_changes: Annotated[
        bool,
        m.Field(
            alias="apply",
            description="Apply changes",
            json_schema_extra={
                "typer_param_decls": list(
                    FlextInfraConstantsBase.CLI_APPLY_OPTION_DECLS
                )
            },
        ),
    ] = False
    check_only: Annotated[
        bool,
        m.Field(
            alias="check",
            description="Check mode",
        ),
    ] = False
    dry_run: Annotated[bool, m.Field(description="Dry-run mode")] = False
    fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = False
    output_format: Annotated[str, m.Field(description="Output format (json|text)")] = (
        "text"
    )
    project_filter: Annotated[
        str | None,
        m.Field(description="Project filter (comma-separated)", exclude=True),
    ] = None
    report_path: Annotated[
        Path | None, m.Field(description="Report output path", exclude=True)
    ] = None
    output_dir: Annotated[
        Path | None, m.Field(description="Output directory", exclude=True)
    ] = None

    @field_validator("workspace_root", mode="before")
    @classmethod
    def _normalize_workspace_root(cls, value: str | Path) -> Path:
        """Normalize workspace roots eagerly through Pydantic validation."""
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @field_validator("output_format", mode="before")
    @classmethod
    def _normalize_output_format(cls, value: str) -> str:
        """Normalize CLI output format names once in the base layer."""
        return value.strip().lower()

    @field_validator("project_filter", mode="before")
    @classmethod
    def _normalize_project_filter(
        cls,
        value: str | t.StrSequence | None,
    ) -> str | None:
        """Normalize project filters into a compact comma-separated string."""
        if value is None:
            return None
        if isinstance(value, str):
            values = [item.strip() for item in value.split(",") if item.strip()]
            return ",".join(values) or None
        values = [item.strip() for item in value if item.strip()]
        return ",".join(values) or None

    @field_validator("report_path", "output_dir", mode="before")
    @classmethod
    def _normalize_optional_path(cls, value: str | Path | None) -> Path | None:
        """Resolve optional output paths in one place."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    def command_payload(self) -> FlextInfraTypesBase.ContainerOverrides:
        """Return the normalized shared command payload once."""
        return {
            "workspace_root": self.workspace_root,
            "apply_changes": self.apply_changes,
            "check_only": self.check_only,
            "dry_run": self.dry_run,
            "fail_fast": self.fail_fast,
            "output_format": self.output_format,
            "project_filter": self.project_filter,
            "report_path": self.report_path,
            "output_dir": self.output_dir,
        }

    @classmethod
    def execute_command(
        cls,
        params: Self,
    ) -> p.Result[TDomainResult]:
        """Execute the validated CLI service instance directly."""
        _ = cls
        return params.execute()


s = FlextInfraServiceBase

__all__: list[str] = [
    "FlextInfraServiceBase",
    "s",
]
