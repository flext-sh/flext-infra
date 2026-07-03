"""Shared service foundation for flext-infra command services."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Self, override

from flext_cli import cli, p as cli_p, u as cli_u
from flext_core import s
from flext_infra import c, m, p, t
from flext_infra._base_payload import FlextInfraCommandPayloadMixin
from flext_infra._utilities.base import FlextInfraUtilitiesBase as ub


class FlextInfraServiceBase[TDomainResult: t.Cli.ResultValue](
    s[TDomainResult],
    FlextInfraCommandPayloadMixin,
):
    """Domain command context shared by all flext-infra CLI services.

    Provides settings/bootstrap and normalized fields for workspace location,
    apply/dry-run toggles, output formatting, and project filtering.
    """

    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(populate_by_name=True)

    settings_type: Annotated[
        type | None,
        m.Field(
            exclude=True,
            description="Internal settings type for runtime bootstrap",
        ),
    ] = None
    runtime_settings: Annotated[
        p.Settings | None,
        m.Field(
            exclude=True,
            description="Internal runtime settings instance for service execution",
        ),
    ] = None
    settings_overrides: Annotated[
        t.JsonMapping | None,
        m.Field(
            exclude=True,
            description="Internal settings override mapping for service bootstrap",
        ),
    ] = None
    initial_context: Annotated[
        p.Context | None,
        m.Field(
            exclude=True,
            description="Internal execution context overrides for service bootstrap",
        ),
    ] = None

    @property
    @override
    def settings(self) -> cli_p.Cli.Settings:
        """Return the typed CLI settings via the canonical cli facade."""
        return cli.settings

    @classmethod
    def _runtime_bootstrap_options(cls) -> p.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace."""
        return m.RuntimeBootstrapOptions(settings_type=type(cli.settings))

    workspace_root: Annotated[
        Path,
        m.Field(
            default_factory=Path.cwd,
            alias="workspace",
            description="Workspace root",
        ),
        m.BeforeValidator(
            lambda v: (v if isinstance(v, Path) else Path(v)).resolve(),
        ),
    ]
    apply_changes: Annotated[
        bool,
        m.Field(
            alias="apply",
            description="Apply changes",
            json_schema_extra={
                "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS)
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
    output_format: Annotated[
        str,
        m.Field(description="Output format (json|text)"),
        m.BeforeValidator(lambda v: v.strip().lower()),
    ] = "text"
    project_filter: Annotated[
        str | None,
        m.Field(description="Project filter (comma-separated)", exclude=True),
    ] = None
    target_module: Annotated[
        str | None,
        m.Field(
            alias="module",
            description=(
                "Dotted module path to scope the verb to a single module "
                "(e.g. flext_core.result). Composes with --workspace/--projects."
            ),
        ),
    ] = None
    target_namespace: Annotated[
        str | None,
        m.Field(
            alias="namespace",
            description=(
                "Alias namespace (c|m|p|t|u|r|e|h|s|x[.<Domain>]) to scope the "
                "verb to a single facade slot."
            ),
        ),
    ] = None
    report_path: Annotated[
        Path | None,
        m.Field(description="Report output path", exclude=True),
        m.BeforeValidator(ub.normalize_optional_path),
    ] = None
    output_dir: Annotated[
        Path | None, m.Field(description="Output directory", exclude=True)
    ] = None

    @m.field_validator("project_filter", mode="before")
    @classmethod
    def _normalize_project_filter(
        cls,
        value: str | t.StrSequence | None,
    ) -> str | None:
        """Normalize project filters into a compact comma-separated string."""
        if value is None:
            return None
        normalized_values = (
            ub.normalize_cli_values(value)
            if isinstance(value, str)
            else ub.normalize_cli_values(*value)
        )
        return ",".join(normalized_values) or None

    @m.field_validator("output_dir", mode="before")
    @classmethod
    def _normalize_output_dir(cls, value: str | Path | None) -> Path | None:
        """Preserve relative output dirs so callers can scope them under workspace roots."""
        if value is None:
            return None
        path: Path = cli_u.Cli.resolve_optional_path(value, default=Path())
        return path.resolve() if path.is_absolute() else path

    @m.computed_field()
    @property
    def root(self) -> Path:
        """Return the canonical normalized workspace root."""
        return self.workspace_root

    @m.computed_field()
    @property
    def effective_dry_run(self) -> bool:
        """Return the normalized write-mode decision for CLI services."""
        return self.dry_run or self.check_only or (not self.apply_changes)

    @override
    def execute(self) -> p.Result[TDomainResult]:
        """Execute the service contract and return a typed result."""
        raise NotImplementedError

    @property
    def log(self) -> p.Logger:
        """Return the service logger through the canonical FlextService kernel."""
        return self.logger

    @classmethod
    def execute_command(cls, params: Self) -> p.Result[TDomainResult]:
        """Execute the validated CLI service instance directly."""
        return params.execute()


s = FlextInfraServiceBase

__all__: list[str] = [
    "FlextInfraServiceBase",
    "s",
]
