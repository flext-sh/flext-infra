"""Canonical per-group lazy resolution for every flext-infra CLI route.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, services

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraCliRouteService:
    """Resolve one group's CLI route table on demand, never all of them."""

    @classmethod
    def route_table_for(cls, group: str) -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Return the routes for one command group, importing only its owner.

        Returns:
            The routes for one command group, importing only its owner.

        Raises:
            ValueError: If CLI group has no route owner.

        """
        if group in {
            c.Infra.CLI_GROUP_CHECK,
            c.Infra.CLI_GROUP_CODEGEN,
            c.Infra.CLI_GROUP_DEPS,
        }:
            return cls._codegen_family_routes(group)
        if group in {
            c.Infra.CLI_GROUP_DOCS,
            c.Infra.CLI_GROUP_MAINTENANCE,
            c.Infra.CLI_GROUP_VALIDATE,
        }:
            return services.FlextInfraValidationRoutes.validation_routes[group]
        if group == c.Infra.CLI_GROUP_REFACTOR:
            return services.FlextInfraRefactorRoutes.refactor_routes
        if group in {c.Infra.CLI_GROUP_RELEASE, c.Infra.CLI_GROUP_WORKSPACE}:
            return cls._workspace_family_routes(group)
        msg = f"CLI group has no route owner: {group}"
        raise ValueError(msg)

    @staticmethod
    def _codegen_family_routes(
        group: str,
    ) -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Return the check, codegen or deps routes from the codegen owner.

        Returns:
            The routes of the requested codegen-owned group.

        """
        if group == c.Infra.CLI_GROUP_CHECK:
            return services.FlextInfraCodegenRoutes.check_routes()
        if group == c.Infra.CLI_GROUP_CODEGEN:
            return services.FlextInfraCodegenRoutes.codegen_routes()
        return services.FlextInfraCodegenRoutes.deps_routes()

    @staticmethod
    def _workspace_family_routes(
        group: str,
    ) -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Return the release or workspace routes from the workspace owner.

        Returns:
            The routes of the requested workspace-owned group.

        """
        if group == c.Infra.CLI_GROUP_RELEASE:
            return services.FlextInfraWorkspaceRoutes.release_routes()
        return services.FlextInfraWorkspaceRoutes.workspace_routes()


__all__: list[str] = ["FlextInfraCliRouteService"]
