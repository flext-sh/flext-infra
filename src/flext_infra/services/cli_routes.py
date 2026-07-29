"""Canonical MRO composition for every flext-infra CLI route."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import m
from flext_infra.services.cli_routes_codegen import CodegenRoutes
from flext_infra.services.cli_routes_validate import ValidationRoutes
from flext_infra.services.cli_routes_workspace import WorkspaceRoutes


class CliRouteService(CodegenRoutes, ValidationRoutes, WorkspaceRoutes):
    """Compose all CLI route families into one typed service surface."""

    group_commands: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        **CodegenRoutes.codegen_routes,
        **ValidationRoutes.validation_routes,
        **WorkspaceRoutes.workspace_routes,
    }


__all__: list[str] = ["CliRouteService"]
