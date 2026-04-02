# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Constants package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra._constants import base, census, rope
    from flext_infra._constants.base import FlextInfraConstantsBase
    from flext_infra._constants.census import FlextInfraConstantsCensus
    from flext_infra._constants.rope import FlextInfraConstantsRope

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraConstantsBase": "flext_infra._constants.base",
    "FlextInfraConstantsCensus": "flext_infra._constants.census",
    "FlextInfraConstantsRope": "flext_infra._constants.rope",
    "base": "flext_infra._constants.base",
    "census": "flext_infra._constants.census",
    "rope": "flext_infra._constants.rope",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
