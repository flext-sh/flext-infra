# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Protocols package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .enforcement import (
        FlextTestsEnforcementProtocolsMixin as FlextTestsEnforcementProtocolsMixin,
    )
    from .valuefactory import (
        FlextTestsValueFactoryProtocolsMixin as FlextTestsValueFactoryProtocolsMixin,
    )
    from .workspace_cleanup import (
        FlextTestsWorkspaceCleanupProtocolsMixin as FlextTestsWorkspaceCleanupProtocolsMixin,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".enforcement": ("FlextTestsEnforcementProtocolsMixin",),
    ".valuefactory": ("FlextTestsValueFactoryProtocolsMixin",),
    ".workspace_cleanup": ("FlextTestsWorkspaceCleanupProtocolsMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsEnforcementProtocolsMixin",
    "FlextTestsValueFactoryProtocolsMixin",
    "FlextTestsWorkspaceCleanupProtocolsMixin",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
