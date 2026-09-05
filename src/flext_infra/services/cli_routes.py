"""Canonical per-group lazy resolution for every flext-infra CLI route."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from flext_infra import m

# Why (ai-hub-xkux, fleet-wide fix): the previous CliRouteService composed
# CodegenRoutes + ValidationRoutes + WorkspaceRoutes via multi-inheritance and
# built every group's ClassVar route table (docs/refactor/release/check/...)
# at CLASS-DEFINITION time, so importing this module -- which cli_dispatch.py
# does unconditionally on every CLI invocation -- eagerly imported all three
# owning modules and their entire transitive dependency graph (~5.9s measured
# via python -X importtime), even though exactly one command group is ever
# dispatched per invocation. Only the owning module for the RESOLVED group is
# imported now, cutting startup to that one module's cost.


class CliRouteService:
    """Resolve one group's CLI route table on demand, never all of them."""

    @classmethod
    @functools.cache
    def route_table_for(cls, group: str) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Return the routes for one command group, importing only its owner."""
        if group in {
            c.Infra.CLI_GROUP_CHECK,
            c.Infra.CLI_GROUP_CODEGEN,
            c.Infra.CLI_GROUP_DEPS,
        }:
            from flext_infra.services.cli_routes_codegen import CodegenRoutes

            return CodegenRoutes.codegen_routes[group]
        if group in {
            c.Infra.CLI_GROUP_DOCS,
            c.Infra.CLI_GROUP_GITHUB,
            c.Infra.CLI_GROUP_MAINTENANCE,
            c.Infra.CLI_GROUP_VALIDATE,
        }:
            from flext_infra.services.cli_routes_validate import ValidationRoutes

            return ValidationRoutes.validation_routes[group]
        if group in {
            c.Infra.CLI_GROUP_REFACTOR,
            c.Infra.CLI_GROUP_RELEASE,
            c.Infra.CLI_GROUP_WORKSPACE,
        }:
            from flext_infra.services.cli_routes_workspace import WorkspaceRoutes

            return WorkspaceRoutes.workspace_routes[group]
        msg = f"CLI group has no route owner: {group}"
        raise ValueError(msg)


__all__: list[str] = ["CliRouteService"]
