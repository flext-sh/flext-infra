# AUTO-GENERATED FILE — Regenerate with: make gen
"""Typings package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.rope import FlextInfraTypesRope
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".adapters": ("FlextInfraTypesAdapters",),
        ".base": ("FlextInfraTypesBase",),
        ".rope": ("FlextInfraTypesRope",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
