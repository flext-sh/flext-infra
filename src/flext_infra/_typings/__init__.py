# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Typings package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_infra._typings.base import *
    from flext_infra._typings.cst import *
    from flext_infra._typings.rope import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraTypesBase": "flext_infra._typings.base",
    "FlextInfraTypesCst": "flext_infra._typings.cst",
    "FlextInfraTypesRope": "flext_infra._typings.rope",
    "base": "flext_infra._typings.base",
    "cst": "flext_infra._typings.cst",
    "rope": "flext_infra._typings.rope",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
