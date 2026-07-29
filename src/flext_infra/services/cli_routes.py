"""Command-selected composition for every flext-infra CLI route."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.cli_catalog import CliCatalog
from flext_infra.services.cli_routes_codegen import CodegenRoutes

if TYPE_CHECKING:
    from flext_infra import m


class CliRouteService:
    """Resolve route implementations only after group and command selection."""

    codegen_groups = frozenset({"basemk", "check", "codegen", "deps"})

    @classmethod
    def route_names(cls, group: str) -> frozenset[str]:
        """Return public command names without loading unrelated implementations."""
        return frozenset(CliCatalog.command_descriptions[group])

    @staticmethod
    def _selected_route(
        group: str, command: str
    ) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Load the one route factory selected by group and command."""
        if group in {"docs", "github", "maintenance", "validate"}:
            from flext_infra.services.cli_routes_validate import ValidationRoutes

            return ValidationRoutes.routes_for(group, command)
        if group in {"refactor", "release", "workspace"}:
            from flext_infra.services.cli_routes_workspace import WorkspaceRoutes

            return WorkspaceRoutes.routes_for(group, command)
        return ()

    @classmethod
    def routes_for(
        cls, group: str, command: str | None = None
    ) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Return only the route selected by group and command when available."""
        if command is None:
            return ()
        if group in cls.codegen_groups:
            return CodegenRoutes.routes_for(group, command) if command is not None else ()
        return cls._selected_route(group, command)


__all__: list[str] = ["CliRouteService"]
