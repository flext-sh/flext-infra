# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Typings package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports
from flext_infra._typings.adapters import FlextInfraTypesAdapters
from flext_infra._typings.base import FlextInfraTypesBase
from flext_infra._typings.rope import FlextInfraTypesRope

if _t.TYPE_CHECKING:
    import flext_infra._typings.adapters as _flext_infra__typings_adapters

    adapters = _flext_infra__typings_adapters
    import flext_infra._typings.base as _flext_infra__typings_base

    base = _flext_infra__typings_base
    import flext_infra._typings.rope as _flext_infra__typings_rope

    rope = _flext_infra__typings_rope

    _ = (
        FlextInfraTypesAdapters,
        FlextInfraTypesBase,
        FlextInfraTypesRope,
        adapters,
        base,
        rope,
    )
_LAZY_IMPORTS = {
    "FlextInfraTypesAdapters": "flext_infra._typings.adapters",
    "FlextInfraTypesBase": "flext_infra._typings.base",
    "FlextInfraTypesRope": "flext_infra._typings.rope",
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
