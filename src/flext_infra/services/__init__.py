# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.services package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _codegen
    from ._codegen.vscode import FlextInfraCodegenVscodeMixin
    from .cli_dispatch import CliDispatchService
    from .cli_route_base import CliRouteBase
    from .cli_routes import CliRouteService
    from .cli_routes_codegen import CodegenRoutes
    from .cli_routes_refactor import RefactorRoutes
    from .cli_routes_validate import ValidationRoutes
    from .cli_routes_validate_commands import ValidationCommandRoutes
    from .cli_routes_workspace import WorkspaceRoutes
    from .codegen import FlextInfraCodegen
__all__: tuple[str, ...] = (
    "CliDispatchService", "CliRouteBase", "CliRouteService", "CodegenRoutes",
    "FlextInfraCodegen", "FlextInfraCodegenVscodeMixin", "RefactorRoutes", "ValidationCommandRoutes",
    "ValidationRoutes", "WorkspaceRoutes", "_codegen",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._codegen": ("_codegen",),
            "._codegen.vscode": ("FlextInfraCodegenVscodeMixin",),
            ".cli_dispatch": ("CliDispatchService",),
            ".cli_route_base": ("CliRouteBase",),
            ".cli_routes": ("CliRouteService",),
            ".cli_routes_codegen": ("CodegenRoutes",),
            ".cli_routes_refactor": ("RefactorRoutes",),
            ".cli_routes_validate": ("ValidationRoutes",),
            ".cli_routes_validate_commands": ("ValidationCommandRoutes",),
            ".cli_routes_workspace": ("WorkspaceRoutes",),
            ".codegen": ("FlextInfraCodegen",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
