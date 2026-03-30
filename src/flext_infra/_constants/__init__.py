# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Constants package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._constants import (
        base as base,
        census as census,
        cst as cst,
        rope as rope,
    )
    from flext_infra._constants.base import (
        FlextInfraConstantsBase as FlextInfraConstantsBase,
    )
    from flext_infra._constants.census import (
        FlextInfraConstantsCensus as FlextInfraConstantsCensus,
    )
    from flext_infra._constants.cst import (
        FlextInfraConstantsCst as FlextInfraConstantsCst,
    )
    from flext_infra._constants.rope import (
        FlextInfraConstantsRope as FlextInfraConstantsRope,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraConstantsBase": [
        "flext_infra._constants.base",
        "FlextInfraConstantsBase",
    ],
    "FlextInfraConstantsCensus": [
        "flext_infra._constants.census",
        "FlextInfraConstantsCensus",
    ],
    "FlextInfraConstantsCst": ["flext_infra._constants.cst", "FlextInfraConstantsCst"],
    "FlextInfraConstantsRope": [
        "flext_infra._constants.rope",
        "FlextInfraConstantsRope",
    ],
    "base": ["flext_infra._constants.base", ""],
    "census": ["flext_infra._constants.census", ""],
    "cst": ["flext_infra._constants.cst", ""],
    "rope": ["flext_infra._constants.rope", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraConstantsBase",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCst",
    "FlextInfraConstantsRope",
    "base",
    "census",
    "cst",
    "rope",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
