# AUTO-GENERATED FILE — Regenerate with: make gen
"""pyproject package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._pyproject.base import FlextInfraUtilitiesPyprojectConformBase
    from flext_infra._pyproject.conform import FlextInfraUtilitiesPyprojectConform
    from flext_infra._pyproject.document import FlextInfraUtilitiesPyprojectDocument
    from flext_infra._pyproject.overlay import FlextInfraUtilitiesPyprojectOverlay
    from flext_infra._pyproject.requirements import (
        FlextInfraUtilitiesPyprojectRequirements,
    )
    from flext_infra._pyproject.toml_phases import (
        FlextInfraUtilitiesPyprojectTomlPhases,
    )
    from flext_infra._pyproject.uv_sources import FlextInfraUtilitiesPyprojectUvSources


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesPyprojectConform",
    "FlextInfraUtilitiesPyprojectConformBase",
    "FlextInfraUtilitiesPyprojectDocument",
    "FlextInfraUtilitiesPyprojectOverlay",
    "FlextInfraUtilitiesPyprojectRequirements",
    "FlextInfraUtilitiesPyprojectTomlPhases",
    "FlextInfraUtilitiesPyprojectUvSources",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesPyprojectConform": ".conform",
        "FlextInfraUtilitiesPyprojectConformBase": ".base",
        "FlextInfraUtilitiesPyprojectDocument": ".document",
        "FlextInfraUtilitiesPyprojectOverlay": ".overlay",
        "FlextInfraUtilitiesPyprojectRequirements": ".requirements",
        "FlextInfraUtilitiesPyprojectTomlPhases": ".toml_phases",
        "FlextInfraUtilitiesPyprojectUvSources": ".uv_sources",
    }),
    public_exports=__all__,
)
