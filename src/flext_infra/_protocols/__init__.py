# AUTO-GENERATED FILE — Regenerate with: make gen
"""Protocols package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols.base import (
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
    )
    from flext_infra._protocols.check import (
        FlextInfraProtocolsCheck as FlextInfraProtocolsCheck,
    )
    from flext_infra._protocols.rope import (
        FlextInfraProtocolsRope as FlextInfraProtocolsRope,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraProtocolsBase",),
        ".check": ("FlextInfraProtocolsCheck",),
        ".rope": ("FlextInfraProtocolsRope",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
