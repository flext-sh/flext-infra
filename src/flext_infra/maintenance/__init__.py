# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.maintenance package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .clean import FlextInfraCleanService
    from .python_version import FlextInfraPythonVersionEnforcer

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".clean": ("FlextInfraCleanService",),
    ".python_version": ("FlextInfraPythonVersionEnforcer",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ("FlextInfraCleanService", "FlextInfraPythonVersionEnforcer")

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
