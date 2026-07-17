"""Canonical CLI route table aggregator for flext-infra."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import m

    CODEGEN_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]]
    VALIDATE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]]
    WORKSPACE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]]


def __getattr__(name: str) -> dict[str, tuple[m.Cli.ResultCommandRoute, ...]]:
    """Lazy-load one route table on first access.

    Importing every route table at module load pulls in heavy subgraphs
    (docs, release, workspace orchestrators) even for commands that only
    need codegen routes. Each route table is cached by Python's module
    object after the first attribute access.
    """
    if name == "CODEGEN_ROUTES":
        from flext_infra._constants.cli_routes_codegen import CODEGEN_ROUTES

        return CODEGEN_ROUTES
    if name == "VALIDATE_ROUTES":
        from flext_infra._constants.cli_routes_validate import VALIDATE_ROUTES

        return VALIDATE_ROUTES
    if name == "WORKSPACE_ROUTES":
        from flext_infra._constants.cli_routes_workspace import WORKSPACE_ROUTES

        return WORKSPACE_ROUTES
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__: list[str] = ["CODEGEN_ROUTES", "VALIDATE_ROUTES", "WORKSPACE_ROUTES"]
