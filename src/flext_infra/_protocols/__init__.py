# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra._protocols import base, rope
    from flext_infra._protocols.base import FlextInfraProtocolsBase
    from flext_infra._protocols.rope import FlextInfraProtocolsRope

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraProtocolsBase": "flext_infra._protocols.base",
    "FlextInfraProtocolsRope": "flext_infra._protocols.rope",
    "base": "flext_infra._protocols.base",
    "rope": "flext_infra._protocols.rope",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
