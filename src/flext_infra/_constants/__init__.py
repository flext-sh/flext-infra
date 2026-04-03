# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Constants package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports
from flext_infra._constants.base import FlextInfraConstantsBase
from flext_infra._constants.census import FlextInfraConstantsCensus
from flext_infra._constants.make import FlextInfraConstantsMake
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._constants.source_code import FlextInfraConstantsSourceCode

if _t.TYPE_CHECKING:
    import flext_infra._constants.base as _flext_infra__constants_base

    base = _flext_infra__constants_base
    import flext_infra._constants.census as _flext_infra__constants_census

    census = _flext_infra__constants_census
    import flext_infra._constants.make as _flext_infra__constants_make

    make = _flext_infra__constants_make
    import flext_infra._constants.rope as _flext_infra__constants_rope

    rope = _flext_infra__constants_rope
    import flext_infra._constants.source_code as _flext_infra__constants_source_code

    source_code = _flext_infra__constants_source_code

    _ = (
        FlextInfraConstantsBase,
        FlextInfraConstantsCensus,
        FlextInfraConstantsMake,
        FlextInfraConstantsRope,
        FlextInfraConstantsSourceCode,
        base,
        census,
        make,
        rope,
        source_code,
    )
_LAZY_IMPORTS = {
    "FlextInfraConstantsBase": "flext_infra._constants.base",
    "FlextInfraConstantsCensus": "flext_infra._constants.census",
    "FlextInfraConstantsMake": "flext_infra._constants.make",
    "FlextInfraConstantsRope": "flext_infra._constants.rope",
    "FlextInfraConstantsSourceCode": "flext_infra._constants.source_code",
    "base": "flext_infra._constants.base",
    "census": "flext_infra._constants.census",
    "make": "flext_infra._constants.make",
    "rope": "flext_infra._constants.rope",
    "source_code": "flext_infra._constants.source_code",
}

__all__ = [
    "FlextInfraConstantsBase",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSourceCode",
    "base",
    "census",
    "make",
    "rope",
    "source_code",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
