# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Typings package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._typings.adapters as _flext_infra__typings_adapters

    adapters = _flext_infra__typings_adapters
    import flext_infra._typings.base as _flext_infra__typings_base
    from flext_infra._typings.adapters import FlextInfraTypesAdapters

    base = _flext_infra__typings_base
    import flext_infra._typings.rope as _flext_infra__typings_rope
    from flext_infra._typings.base import FlextInfraTypesBase

    rope = _flext_infra__typings_rope
    from flext_infra._typings.rope import FlextInfraTypesRope
_LAZY_IMPORTS = {
    "FlextInfraTypesAdapters": (
        "flext_infra._typings.adapters",
        "FlextInfraTypesAdapters",
    ),
    "FlextInfraTypesBase": ("flext_infra._typings.base", "FlextInfraTypesBase"),
    "FlextInfraTypesRope": ("flext_infra._typings.rope", "FlextInfraTypesRope"),
    "adapters": "flext_infra._typings.adapters",
    "base": "flext_infra._typings.base",
    "rope": "flext_infra._typings.rope",
}

__all__ = [
    "FlextInfraTypesAdapters",
    "FlextInfraTypesBase",
    "FlextInfraTypesRope",
    "adapters",
    "base",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
