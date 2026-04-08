# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
