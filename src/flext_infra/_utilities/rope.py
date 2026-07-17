"""Thin MRO facade for all infrastructure Rope behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities.rope_module_patch import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities.rope_mro_transform import (
    FlextInfraUtilitiesRopeMroTransform,
)
from flext_infra._utilities.rope_patch.pep695_patch import (
    FlextInfraUtilitiesRopePep695Patch,
)
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities.rope_structure import FlextInfraUtilitiesRopeStructure


# mro-wkii.17.26 (codex): one facade owns every Rope implementation part.
class FlextInfraUtilitiesRope(
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeAnalysisIntrospection,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeInventory,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesRopeStructure,
    FlextInfraUtilitiesRopePep695Patch,
    FlextInfraUtilitiesRopeMroTransform,
):
    """Compose the canonical Rope utility domain without adding behavior."""


__all__: list[str] = ["FlextInfraUtilitiesRope"]
