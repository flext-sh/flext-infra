# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .workspace_check import FlextInfraWorkspaceChecker
    from .workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )
__all__: tuple[str, ...] = (
    "FlextInfraGateRegistry",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceChecker",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".workspace_check": ("FlextInfraWorkspaceChecker",),
                ".workspace_check_gates": (
                    "FlextInfraGateRegistry",
                    "FlextInfraWorkspaceCheckGatesMixin",
                ),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
