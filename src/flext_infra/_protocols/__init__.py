# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._protocols.base as _flext_infra__protocols_base

    base = _flext_infra__protocols_base
    import flext_infra._protocols.check as _flext_infra__protocols_check
    from flext_infra._protocols.base import FlextInfraProtocolsBase

    check = _flext_infra__protocols_check
    import flext_infra._protocols.refactor as _flext_infra__protocols_refactor
    from flext_infra._protocols.check import (
        FlextInfraProtocolsCheck,
        WorkspaceLoopOutcome,
    )

    refactor = _flext_infra__protocols_refactor
    import flext_infra._protocols.rope as _flext_infra__protocols_rope
    from flext_infra._protocols.refactor import (
        FlextInfraChangeTracker,
        FlextInfraProtocolsRefactor,
    )

    rope = _flext_infra__protocols_rope
    from flext_infra._protocols.rope import FlextInfraProtocolsRope
_LAZY_IMPORTS = {
    "FlextInfraChangeTracker": (
        "flext_infra._protocols.refactor",
        "FlextInfraChangeTracker",
    ),
    "FlextInfraProtocolsBase": (
        "flext_infra._protocols.base",
        "FlextInfraProtocolsBase",
    ),
    "FlextInfraProtocolsCheck": (
        "flext_infra._protocols.check",
        "FlextInfraProtocolsCheck",
    ),
    "FlextInfraProtocolsRefactor": (
        "flext_infra._protocols.refactor",
        "FlextInfraProtocolsRefactor",
    ),
    "FlextInfraProtocolsRope": (
        "flext_infra._protocols.rope",
        "FlextInfraProtocolsRope",
    ),
    "WorkspaceLoopOutcome": ("flext_infra._protocols.check", "WorkspaceLoopOutcome"),
    "base": "flext_infra._protocols.base",
    "check": "flext_infra._protocols.check",
    "refactor": "flext_infra._protocols.refactor",
    "rope": "flext_infra._protocols.rope",
}

__all__ = [
    "FlextInfraChangeTracker",
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCheck",
    "FlextInfraProtocolsRefactor",
    "FlextInfraProtocolsRope",
    "WorkspaceLoopOutcome",
    "base",
    "check",
    "refactor",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
