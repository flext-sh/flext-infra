# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope. Analysis package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._rope._analysis.asthelpers import (
        FlextInfraUtilitiesRopeAnalysisAstHelpers,
    )
    from flext_infra._utilities._rope._analysis.base import (
        FlextInfraUtilitiesRopeAnalysisBase,
    )
    from flext_infra._utilities._rope._analysis.exports import (
        FlextInfraUtilitiesRopeAnalysisExports,
    )
    from flext_infra._utilities._rope._analysis.importstate import (
        FlextInfraUtilitiesRopeAnalysisImportState,
    )
    from flext_infra._utilities._rope._analysis.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities._rope._analysis.sourcescan import (
        FlextInfraUtilitiesRopeAnalysisSourceScan,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesRopeAnalysisAstHelpers",
    "FlextInfraUtilitiesRopeAnalysisBase",
    "FlextInfraUtilitiesRopeAnalysisExports",
    "FlextInfraUtilitiesRopeAnalysisImportState",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeAnalysisSourceScan",
    "FlextInfraUtilitiesRopeAnalysisWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesRopeAnalysisAstHelpers": ".asthelpers",
        "FlextInfraUtilitiesRopeAnalysisBase": ".base",
        "FlextInfraUtilitiesRopeAnalysisExports": ".exports",
        "FlextInfraUtilitiesRopeAnalysisImportState": ".importstate",
        "FlextInfraUtilitiesRopeAnalysisIntrospection": ".rope_analysis_introspection",
        "FlextInfraUtilitiesRopeAnalysisSourceScan": ".sourcescan",
        "FlextInfraUtilitiesRopeAnalysisWorkspace": ".rope_analysis_workspace",
    }),
    public_exports=__all__,
)
