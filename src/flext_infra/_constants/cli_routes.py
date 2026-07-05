"""Canonical CLI route table aggregator for flext-infra."""

from __future__ import annotations

from flext_infra._constants.cli_routes_codegen import CODEGEN_ROUTES
from flext_infra._constants.cli_routes_validate import VALIDATE_ROUTES
from flext_infra._constants.cli_routes_workspace import WORKSPACE_ROUTES

__all__: list[str] = ["CODEGEN_ROUTES", "VALIDATE_ROUTES", "WORKSPACE_ROUTES"]
