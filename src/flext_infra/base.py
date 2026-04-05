"""Shared service base for flext-infra command services."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Annotated, Self, override

from pydantic import ConfigDict, Field, field_validator
from pydantic.config import JsonDict

from flext_cli import FlextCliSettings
from flext_core import FlextModels, FlextSettings, p, r, s as core_service_base
from flext_infra import t

APPLY_OPTION_DECLS: list[str] = ["--apply/--dry-run"]


def apply_option_json_schema_extra(schema: JsonDict) -> None:
    """Inject Typer dual-flag metadata using a Pydantic-supported hook."""
    schema["typer_param_decls"] = list(APPLY_OPTION_DECLS)


class FlextInfraServiceBase[TDomainResult: t.Infra.DomainOutput](
    core_service_base[TDomainResult],
    ABC,
):
    """Base class for flext-infra services with normalized command context."""

    model_config = ConfigDict(populate_by_name=True)

    config_type: Annotated[
        type | None,
        Field(default=None, description="Configuration type constraint", exclude=True),
    ] = None
    config_overrides: Annotated[
        t.Infra.ContainerOverrides | None,
        Field(
            default=None, description="Configuration overrides context", exclude=True
        ),
    ] = None
    initial_context: Annotated[
        p.Context | None,
        Field(default=None, description="Initial service context", exclude=True),
    ] = None
    subproject: Annotated[
        str | None,
        Field(default=None, description="Target subproject identifier", exclude=True),
    ] = None
    container_overrides: Annotated[
        t.Infra.RuntimeScalarOverrides | None,
        Field(
            default=None,
            description="Context dependency container overrides",
            exclude=True,
        ),
    ] = None
    wire_modules: Annotated[
        Sequence[ModuleType] | None,
        Field(
            default=None, description="Modules to wire dependencies into", exclude=True
        ),
    ] = None
    wire_packages: Annotated[
        Sequence[str] | None,
        Field(
            default=None, description="Packages to wire dependencies into", exclude=True
        ),
    ] = None
    wire_classes: Annotated[
        Sequence[type] | None,
        Field(
            default=None, description="Classes to wire dependencies into", exclude=True
        ),
    ] = None

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
            json_schema_extra=apply_option_json_schema_extra,
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

    @property
    @override
    def settings(self) -> FlextCliSettings:
        """Return the typed CLI settings namespace."""
        return FlextSettings.get_global().get_namespace("cli", FlextCliSettings)

    @classmethod
    @override
    def _runtime_bootstrap_options(cls) -> p.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace."""
        return FlextModels.RuntimeBootstrapOptions(config_type=FlextCliSettings)

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
    "APPLY_OPTION_DECLS",
    "FlextInfraServiceBase",
    "apply_option_json_schema_extra",
    "s",
]
