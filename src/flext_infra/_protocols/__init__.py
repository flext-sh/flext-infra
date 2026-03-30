# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols import base as base, cst as cst, rope as rope
    from flext_infra._protocols.base import (
        FlextInfraProtocolsBase as FlextInfraProtocolsBase,
    )
    from flext_infra._protocols.cst import (
        FlextInfraProtocolsCst as FlextInfraProtocolsCst,
    )
    from flext_infra._protocols.rope import (
        FlextInfraProtocolsRope as FlextInfraProtocolsRope,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraProtocolsBase": [
        "flext_infra._protocols.base",
        "FlextInfraProtocolsBase",
    ],
    "FlextInfraProtocolsCst": ["flext_infra._protocols.cst", "FlextInfraProtocolsCst"],
    "FlextInfraProtocolsRope": [
        "flext_infra._protocols.rope",
        "FlextInfraProtocolsRope",
    ],
    "base": ["flext_infra._protocols.base", ""],
    "cst": ["flext_infra._protocols.cst", ""],
    "rope": ["flext_infra._protocols.rope", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraProtocolsBase",
    "FlextInfraProtocolsCst",
    "FlextInfraProtocolsRope",
    "base",
    "cst",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
