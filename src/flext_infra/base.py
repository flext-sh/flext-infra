"""Shared service foundation for flext-infra command services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import (
    Callable,
    Sequence,
)
from pathlib import Path
from typing import Annotated, Self, override

from flext_cli import FlextCliSettings
from flext_core import FlextSettings, s

from flext_infra import (
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraServiceBase[TDomainResult: t.Cli.ResultValue](
    s[TDomainResult],
    ABC,
):
    """Domain command context shared by all flext-infra CLI services.

    Provides settings/bootstrap and normalized fields for workspace location,
    apply/dry-run toggles, output formatting, and project filtering.
    """

    model_config = m.ConfigDict(populate_by_name=True)

    @property
    @override
    def settings(self) -> FlextCliSettings:
        """Return the typed CLI settings namespace."""
        return FlextSettings.fetch_global().fetch_namespace("cli", FlextCliSettings)

    @classmethod
    def _runtime_bootstrap_options(cls) -> p.RuntimeBootstrapOptions:
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

    @u.field_validator("workspace_root", mode="before")
    @classmethod
    def _normalize_workspace_root(cls, value: str | Path) -> Path:
        """Normalize workspace roots eagerly through Pydantic validation."""
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @u.field_validator("output_format", mode="before")
    @classmethod
    def _normalize_output_format(cls, value: str) -> str:
        """Normalize CLI output format names once in the base layer."""
        return value.strip().lower()

    @u.field_validator("project_filter", mode="before")
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

    @u.field_validator("report_path", mode="before")
    @classmethod
    def _normalize_report_path(cls, value: str | Path | None) -> Path | None:
        """Resolve report file paths eagerly so report writes are absolute."""
        return u.Infra.normalize_optional_path(value)

    @u.field_validator("output_dir", mode="before")
    @classmethod
    def _normalize_output_dir(cls, value: str | Path | None) -> Path | None:
        """Preserve relative output dirs so callers can scope them under workspace roots."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve() if path.is_absolute() else path

    @property
    def root(self) -> Path:
        """Return the canonical normalized workspace root."""
        return self.workspace_root

    @property
    def effective_dry_run(self) -> bool:
        """Return the normalized write-mode decision for CLI services."""
        return bool(self.dry_run or self.check_only or (not self.apply_changes))

    @staticmethod
    def normalize_selected_projects(
        selected_projects: t.StrSequence | None,
    ) -> t.StrSequence | None:
        """Normalize repeated project selectors into a compact sequence."""
        return u.Infra.normalize_sequence_values(selected_projects)

    def selected_project_dirs(
        self,
        selected_projects: t.StrSequence | None,
    ) -> Sequence[Path] | None:
        """Resolve selected project directories relative to the workspace root."""
        names = self.normalize_selected_projects(selected_projects)
        if names is None:
            return None
        return [self.root / name for name in names]

    def command_payload(self) -> t.JsonMapping:
        """Return the normalized shared command payload once."""
        payload: t.MutableJsonMapping = {
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
            "check_only": self.check_only,
            "dry_run": self.dry_run,
            "fail_fast": self.fail_fast,
            "output_format": self.output_format,
        }
        if self.project_filter is not None:
            payload["project_filter"] = self.project_filter
        if self.report_path is not None:
            payload["report_path"] = str(self.report_path)
        if self.output_dir is not None:
            payload["output_dir"] = str(self.output_dir)
        return payload

    @abstractmethod
    def execute(self) -> p.Result[TDomainResult]:
        """Execute the service contract and return a typed result."""
        raise NotImplementedError

    @classmethod
    def execute_command(
        cls,
        params: Self,
    ) -> p.Result[TDomainResult]:
        """Execute the validated CLI service instance directly."""
        _ = cls
        return params.execute()


class FlextInfraProjectSelectionServiceBase[TDomainResult: t.Cli.ResultValue](
    FlextInfraServiceBase[TDomainResult],
    ABC,
):
    """Shared service foundation for commands that target workspace projects."""

    selected_projects: Annotated[
        t.StrSequence | None,
        m.Field(alias="projects", description="Projects to process"),
    ] = None

    @property
    def project_names(self) -> t.StrSequence | None:
        """Return normalized selected project names."""
        return self.normalize_selected_projects(self.selected_projects)

    @property
    def project_dirs(self) -> Sequence[Path] | None:
        """Resolve selected project directories relative to the workspace root."""
        return self.selected_project_dirs(self.selected_projects)

    def run_scoped_docs(
        self,
        workspace_root: Path,
        *,
        output_dir: Path | str,
        handler: Callable[
            [m.Infra.DocScope],
            m.Infra.DocsPhaseReport,
        ],
        projects: t.StrSequence | None = None,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Run one docs phase across the resolved governed scopes."""
        return u.Infra.run_scoped(
            workspace_root,
            projects=self.selected_projects if projects is None else projects,
            output_dir=output_dir,
            handler=handler,
        )


s = FlextInfraServiceBase

__all__: list[str] = [
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraServiceBase",
    "s",
]
