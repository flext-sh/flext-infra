# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextInfraProtocolsBase
    from .check import FlextInfraProtocolsCheck
    from .deps import FlextInfraProtocolsDeps
    from .docs import FlextInfraProtocolsDocs
    from .rope import FlextInfraProtocolsRope
    from .rope_runtime import FlextInfraProtocolsRopeRuntime

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextInfraProtocolsBase",),
    ".check": ("FlextInfraProtocolsCheck",),
    ".deps": ("FlextInfraProtocolsDeps",),
    ".docs": ("FlextInfraProtocolsDocs",),
    ".rope": ("FlextInfraProtocolsRope",),
    ".rope_runtime": ("FlextInfraProtocolsRopeRuntime",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCheck",
    "FlextInfraProtocolsDeps",
    "FlextInfraProtocolsDocs",
    "FlextInfraProtocolsRope",
    "FlextInfraProtocolsRopeRuntime",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
