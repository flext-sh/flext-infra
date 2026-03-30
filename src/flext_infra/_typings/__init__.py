# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Typings package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._typings import base as base, cst as cst, rope as rope
    from flext_infra._typings.base import FlextInfraTypesBase as FlextInfraTypesBase
    from flext_infra._typings.cst import FlextInfraTypesCst as FlextInfraTypesCst
    from flext_infra._typings.rope import FlextInfraTypesRope as FlextInfraTypesRope

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraTypesBase": ["flext_infra._typings.base", "FlextInfraTypesBase"],
    "FlextInfraTypesCst": ["flext_infra._typings.cst", "FlextInfraTypesCst"],
    "FlextInfraTypesRope": ["flext_infra._typings.rope", "FlextInfraTypesRope"],
    "base": ["flext_infra._typings.base", ""],
    "cst": ["flext_infra._typings.cst", ""],
    "rope": ["flext_infra._typings.rope", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraTypesBase",
    "FlextInfraTypesCst",
    "FlextInfraTypesRope",
    "base",
    "cst",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
