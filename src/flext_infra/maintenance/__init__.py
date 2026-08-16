# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.maintenance package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .clean import FlextInfraCleanService
    from .python_version import FlextInfraPythonVersionEnforcer
__all__: tuple[str, ...] = ("FlextInfraCleanService", "FlextInfraPythonVersionEnforcer")

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".clean": ("FlextInfraCleanService",),
                ".python_version": ("FlextInfraPythonVersionEnforcer",),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
