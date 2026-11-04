"""Canonical owner of the Rope utilities domain, composed from its parts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeAstBindings,
    FlextInfraUtilitiesRopeClassMove,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeInventory,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesInventory,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesRopeSourceBindingCollector,
    FlextInfraUtilitiesRopeStructure,
)


class FlextInfraUtilitiesRope(
    FlextInfraUtilitiesRopeSourceBasesAliases,
    FlextInfraUtilitiesRopeSourceBasesInventory,
    FlextInfraUtilitiesRopeSourceBindingCollector,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesRopeClassMove,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeInventory,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSource,
    FlextInfraUtilitiesRopeAstBindings,
    FlextInfraUtilitiesRopeStructure,
):
    """Rope utilities domain owner composing every declared Rope part by MRO."""


__all__: list[str] = ["FlextInfraUtilitiesRope"]
