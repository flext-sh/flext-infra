# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports
from flext_infra._protocols.base import FlextInfraProtocolsBase
from flext_infra._protocols.rope import FlextInfraProtocolsRope

if _t.TYPE_CHECKING:
    import flext_infra._protocols.base as _flext_infra__protocols_base

    base = _flext_infra__protocols_base
    import flext_infra._protocols.rope as _flext_infra__protocols_rope

    rope = _flext_infra__protocols_rope

    _ = (
        FlextInfraProtocolsBase,
        FlextInfraProtocolsRope,
        base,
        rope,
    )
_LAZY_IMPORTS = {
    "FlextInfraProtocolsBase": "flext_infra._protocols.base",
    "FlextInfraProtocolsRope": "flext_infra._protocols.rope",
    "base": "flext_infra._protocols.base",
    "rope": "flext_infra._protocols.rope",
}

__all__ = [
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsRope",
    "base",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
