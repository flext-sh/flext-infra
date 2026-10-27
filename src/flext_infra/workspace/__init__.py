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
    from flext_infra.workspace._environment_provenance_editable import (
        FlextInfraWorkspaceEnvironmentProvenanceEditableMixin,
    )
    from flext_infra.workspace._environment_provenance_module_source import (
        FlextInfraWorkspaceEnvironmentProvenanceModuleSourceMixin,
    )
    from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin
    from flext_infra.workspace._rope_query import FlextInfraRopeQueryMixin
    from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
    from flext_infra.workspace.environment_contracts import (
        FlextInfraWorkspaceEnvironmentContracts,
    )
    from flext_infra.workspace.environment_provenance import (
        FlextInfraWorkspaceEnvironmentProvenance,
    )
    from flext_infra.workspace.fleet_gaps import FlextInfraWorkspaceFleetGaps
    from flext_infra.workspace.flext_binding import FlextInfraBindingService
    from flext_infra.workspace.flext_editable import FlextInfraWorkspaceFlextEditable
    from flext_infra.workspace.lock_completeness import (
        FlextInfraWorkspaceLockCompleteness,
    )
    from flext_infra.workspace.native_reference import (
        FlextInfraWorkspaceNativeReference,
    )
    from flext_infra.workspace.propagation import FlextInfraWorkspacePropagation
    from flext_infra.workspace.rope import FlextInfraRopeWorkspace
    from flext_infra.workspace.runtime_dependencies import (
        FlextInfraRuntimeDependencyCollector,
    )


__all__: tuple[str, ...] = (
    "FlextInfraBindingService",
    "FlextInfraRopeQueryMixin",
    "FlextInfraRopeWorkspace",
    "FlextInfraRuntimeDependencyCollector",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceEnvironmentContracts",
    "FlextInfraWorkspaceEnvironmentProvenance",
    "FlextInfraWorkspaceEnvironmentProvenanceEditableMixin",
    "FlextInfraWorkspaceEnvironmentProvenanceModuleSourceMixin",
    "FlextInfraWorkspaceFleetGaps",
    "FlextInfraWorkspaceFlextEditable",
    "FlextInfraWorkspaceGovernanceMixin",
    "FlextInfraWorkspaceLockCompleteness",
    "FlextInfraWorkspaceNativeReference",
    "FlextInfraWorkspacePropagation",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraBindingService": ".flext_binding",
        "FlextInfraRopeQueryMixin": "._rope_query",
        "FlextInfraRopeWorkspace": ".rope",
        "FlextInfraRuntimeDependencyCollector": ".runtime_dependencies",
        "FlextInfraWorkspaceDetector": ".detector",
        "FlextInfraWorkspaceEnvironmentContracts": ".environment_contracts",
        "FlextInfraWorkspaceEnvironmentProvenance": ".environment_provenance",
        "FlextInfraWorkspaceEnvironmentProvenanceEditableMixin": (
            "._environment_provenance_editable"
        ),
        "FlextInfraWorkspaceEnvironmentProvenanceModuleSourceMixin": (
            "._environment_provenance_module_source"
        ),
        "FlextInfraWorkspaceFleetGaps": ".fleet_gaps",
        "FlextInfraWorkspaceFlextEditable": ".flext_editable",
        "FlextInfraWorkspaceGovernanceMixin": "._governance",
        "FlextInfraWorkspaceLockCompleteness": ".lock_completeness",
        "FlextInfraWorkspaceNativeReference": ".native_reference",
        "FlextInfraWorkspacePropagation": ".propagation",
    }),
    public_exports=__all__,
)
