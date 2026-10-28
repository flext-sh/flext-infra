# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.workspace package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.workspace import (
        FlextInfraBindingService,
        FlextInfraRopeWorkspace,
        FlextInfraRuntimeDependencyCollector,
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceEnvironmentContracts,
        FlextInfraWorkspaceEnvironmentProvenance,
        FlextInfraWorkspaceEnvironmentProvenanceEditable,
        FlextInfraWorkspaceEnvironmentProvenanceModuleSource,
        FlextInfraWorkspaceFleetGaps,
        FlextInfraWorkspaceFlextEditable,
        FlextInfraWorkspaceGovernance,
        FlextInfraWorkspaceLockCompleteness,
        FlextInfraWorkspaceNativeReference,
        FlextInfraWorkspacePropagation,
    )
    from flext_infra.workspace._rope import FlextInfraWorkspaceRopeQuery


__all__: tuple[str, ...] = (
    "FlextInfraBindingService",
    "FlextInfraRopeWorkspace",
    "FlextInfraRuntimeDependencyCollector",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceEnvironmentContracts",
    "FlextInfraWorkspaceEnvironmentProvenance",
    "FlextInfraWorkspaceEnvironmentProvenanceEditable",
    "FlextInfraWorkspaceEnvironmentProvenanceModuleSource",
    "FlextInfraWorkspaceFleetGaps",
    "FlextInfraWorkspaceFlextEditable",
    "FlextInfraWorkspaceGovernance",
    "FlextInfraWorkspaceLockCompleteness",
    "FlextInfraWorkspaceNativeReference",
    "FlextInfraWorkspacePropagation",
    "FlextInfraWorkspaceRopeQuery",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraBindingService": ".flext_binding",
        "FlextInfraWorkspaceRopeQuery": "._rope_query",
        "FlextInfraRopeWorkspace": ".rope",
        "FlextInfraRuntimeDependencyCollector": ".runtime_dependencies",
        "FlextInfraWorkspaceDetector": ".detector",
        "FlextInfraWorkspaceEnvironmentContracts": ".environment_contracts",
        "FlextInfraWorkspaceEnvironmentProvenance": ".environment_provenance",
        "FlextInfraWorkspaceEnvironmentProvenanceEditable": (
            "._environment_provenance_editable"
        ),
        "FlextInfraWorkspaceEnvironmentProvenanceModuleSource": (
            "._environment_provenance_module_source"
        ),
        "FlextInfraWorkspaceFleetGaps": ".fleet_gaps",
        "FlextInfraWorkspaceFlextEditable": ".flext_editable",
        "FlextInfraWorkspaceGovernance": "._governance",
        "FlextInfraWorkspaceLockCompleteness": ".lock_completeness",
        "FlextInfraWorkspaceNativeReference": ".native_reference",
        "FlextInfraWorkspacePropagation": ".propagation",
    }),
    public_exports=__all__,
)
