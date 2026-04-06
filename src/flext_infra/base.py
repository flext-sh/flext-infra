"""Shared service base for flext-infra command services.

Two-class design mirroring flext-cli's base.py pattern:

- ``FlextInfraServiceBase`` (~40 LOC) -- thin foundation with settings
  access and bootstrap options only.  Suitable for services that need
  no shared command-context fields (e.g. the API facade).

- ``FlextInfraCommandContext`` (~90 LOC) -- mixin inheriting the thin
  base and carrying domain fields used by every CLI command service
  (workspace_root, apply_changes, dry_run, etc.).

The module-level ``s`` alias points to ``FlextInfraCommandContext`` so
that existing ``s[T]`` consumers keep working without import changes.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Self, TypeVar, override

from pydantic import ConfigDict, Field, field_validator
from pydantic.config import JsonDict

from flext_cli.settings import FlextCliSettings
from flext_core.models import FlextModels
from flext_core.protocols import FlextProtocols
from flext_core.result import FlextResult as r
from flext_core.service import FlextService as core_service_base
from flext_core.settings import FlextSettings
from flext_infra._constants.base import FlextInfraConstantsBase
from flext_infra._typings.base import FlextInfraTypesBase

TDomainResult = TypeVar("TDomainResult", bound=FlextInfraTypesBase.DomainOutput)


def _apply_option_json_schema_extra(schema: JsonDict) -> None:
    """Inject Typer dual-flag metadata without importing the facade root."""
    schema["typer_param_decls"] = list(FlextInfraConstantsBase.Cli.APPLY_OPTION_DECLS)


# ---------------------------------------------------------------------------
# Thin service base (~40 LOC) -- mirrors FlextCliServiceBase
# ---------------------------------------------------------------------------


class FlextInfraServiceBase(
    core_service_base[TDomainResult],
    ABC,
):
    """Thin base class for flext-infra services.

    Provides settings access and runtime bootstrap only.
    Domain command fields live in :class:`FlextInfraCommandContext`.
    """

    @property
    @override
    def settings(self) -> FlextProtocols.Settings:
        """Return the typed CLI settings namespace."""
        return FlextSettings.get_global().get_namespace("cli", FlextCliSettings)

    @classmethod
    @override
    def _runtime_bootstrap_options(cls) -> FlextProtocols.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace."""
        return FlextModels.RuntimeBootstrapOptions(config_type=FlextCliSettings)


# ---------------------------------------------------------------------------
# Command context mixin (~90 LOC) -- carries all domain fields
# ---------------------------------------------------------------------------


class FlextInfraCommandContext(
    FlextInfraServiceBase[TDomainResult],
):
    """Domain command context shared by all flext-infra CLI services.

    Inherits settings + bootstrap from :class:`FlextInfraServiceBase`
    and adds fields for workspace location, apply/dry-run toggles,
    output formatting, and project filtering.
    """

    model_config = ConfigDict(populate_by_name=True)

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
            json_schema_extra=_apply_option_json_schema_extra,
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

    @classmethod
    def execute_command(
        cls,
        params: Self,
    ) -> r[TDomainResult]:
        """Execute the validated CLI service instance directly."""
        _ = cls
        return params.execute()


# ---------------------------------------------------------------------------
# Aliases & exports
# ---------------------------------------------------------------------------

# ``s`` points to FlextInfraCommandContext for backward compatibility.
# All existing ``s[T]`` consumers access domain fields and need them.
s = FlextInfraCommandContext

__all__ = [
    "FlextInfraCommandContext",
    "FlextInfraServiceBase",
    "s",
]
