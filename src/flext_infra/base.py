"""Shared service foundation for flext-infra command services."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Self, TypeVar, override

from pydantic import ConfigDict, Field, field_validator

from flext_cli import FlextCliSettings
from flext_core import (
    FlextModels,
    FlextProtocols,
    FlextSettings,
    r,
    s as core_service_base,
)
from flext_infra import FlextInfraConstantsBase, FlextInfraTypesBase

TDomainResult = TypeVar("TDomainResult", bound=FlextInfraTypesBase.DomainOutput)


class FlextInfraServiceBase(
    core_service_base[TDomainResult],
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
        return FlextSettings.get_global().get_namespace("cli", FlextCliSettings)

    @classmethod
    @override
    def _runtime_bootstrap_options(cls) -> FlextProtocols.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace."""
        return FlextModels.RuntimeBootstrapOptions(config_type=FlextCliSettings)

    workspace_root: Annotated[
        Path,
        Field(
            default_factory=Path.cwd,
            alias="workspace",
            description="Workspace root",
        ),
    ]
    apply_changes: Annotated[
        bool,
        Field(
            default=False,
            alias="apply",
            description="Apply changes",
            json_schema_extra={
                "typer_param_decls": list(
                    FlextInfraConstantsBase.CLI_APPLY_OPTION_DECLS
                )
            },
        ),
    ]
    check_only: Annotated[
        bool,
        Field(
            default=False,
            alias="check",
            description="Check mode",
        ),
    ]
    dry_run: Annotated[
        bool,
        Field(default=False, description="Dry-run mode"),
    ]
    fail_fast: Annotated[
        bool,
        Field(default=False, description="Stop on first failure"),
    ]
    output_format: Annotated[
        str,
        Field(default="text", description="Output format (json|text)"),
    ]
    project_filter: Annotated[
        str | None,
        Field(
            default=None, description="Project filter (comma-separated)", exclude=True
        ),
    ]
    report_path: Annotated[
        Path | None,
        Field(default=None, description="Report output path", exclude=True),
    ]
    output_dir: Annotated[
        Path | None,
        Field(default=None, description="Output directory", exclude=True),
    ]

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
        value: str | Sequence[str] | None,
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
    ) -> r[TDomainResult]:
        """Execute the validated CLI service instance directly."""
        _ = cls
        return params.execute()


s = FlextInfraServiceBase

__all__ = [
    "FlextInfraServiceBase",
    "s",
]
