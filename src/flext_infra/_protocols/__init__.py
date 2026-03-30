# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Protocols package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols import base, rope
    from flext_infra._protocols.base import *
    from flext_infra._protocols.rope import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraProtocolsBase": "flext_infra._protocols.base",
    "FlextInfraProtocolsRope": "flext_infra._protocols.rope",
    "base": "flext_infra._protocols.base",
    "rope": "flext_infra._protocols.rope",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
