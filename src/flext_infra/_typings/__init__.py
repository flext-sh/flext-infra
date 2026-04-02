# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Typings package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra._typings import adapters, base, cst, rope
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.cst import FlextInfraTypesCst
    from flext_infra._typings.rope import FlextInfraTypesRope

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraTypesAdapters": "flext_infra._typings.adapters",
    "FlextInfraTypesBase": "flext_infra._typings.base",
    "FlextInfraTypesCst": "flext_infra._typings.cst",
    "FlextInfraTypesRope": "flext_infra._typings.rope",
    "adapters": "flext_infra._typings.adapters",
    "base": "flext_infra._typings.base",
    "cst": "flext_infra._typings.cst",
    "rope": "flext_infra._typings.rope",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
