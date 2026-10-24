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
    from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin
    from flext_infra.workspace._native_reference_bindings import (
        FlextInfraWorkspaceNativeReferenceBindingsMixin,
    )
    from flext_infra.workspace._native_reference_functions import (
        FlextInfraWorkspaceNativeReferenceFunctionsMixin,
    )
    from flext_infra.workspace._native_reference_primitives import (
        FlextInfraWorkspaceNativeReferencePrimitivesMixin,
    )
    from flext_infra.workspace._native_reference_symbols import (
        FlextInfraWorkspaceNativeReferenceSymbolsMixin,
    )
    from flext_infra.workspace._native_reference_values import (
        FlextInfraWorkspaceNativeReferenceValuesMixin,
    )
    from flext_infra.workspace._rope_query import FlextInfraRopeQueryMixin
    from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
    from flext_infra.workspace.environment import FlextInfraWorkspaceEnvironmentMixin
    from flext_infra.workspace.environment_contracts import (
        FlextInfraWorkspaceEnvironmentContracts,
    )
    from flext_infra.workspace.environment_provenance import (
        FlextInfraWorkspaceEnvironmentProvenance,
    )
    from flext_infra.workspace.fleet_gaps import FlextInfraWorkspaceFleetGaps
    from flext_infra.workspace.fleet_verbs import FlextInfraWorkspaceFleetVerbs
    from flext_infra.workspace.flext_binding import FlextInfraBindingService
    from flext_infra.workspace.lifecycle import FlextInfraWorkspaceLifecycle
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
    "FlextInfraWorkspaceEnvironmentMixin",
    "FlextInfraWorkspaceEnvironmentProvenance",
    "FlextInfraWorkspaceFleetGaps",
    "FlextInfraWorkspaceFleetVerbs",
    "FlextInfraWorkspaceGovernanceMixin",
    "FlextInfraWorkspaceLifecycle",
    "FlextInfraWorkspaceLockCompleteness",
    "FlextInfraWorkspaceNativeReference",
    "FlextInfraWorkspaceNativeReferenceBindingsMixin",
    "FlextInfraWorkspaceNativeReferenceFunctionsMixin",
    "FlextInfraWorkspaceNativeReferencePrimitivesMixin",
    "FlextInfraWorkspaceNativeReferenceSymbolsMixin",
    "FlextInfraWorkspaceNativeReferenceValuesMixin",
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
        "FlextInfraWorkspaceEnvironmentMixin": ".environment",
        "FlextInfraWorkspaceEnvironmentProvenance": ".environment_provenance",
        "FlextInfraWorkspaceFleetGaps": ".fleet_gaps",
        "FlextInfraWorkspaceFleetVerbs": ".fleet_verbs",
        "FlextInfraWorkspaceGovernanceMixin": "._governance",
        "FlextInfraWorkspaceLifecycle": ".lifecycle",
        "FlextInfraWorkspaceLockCompleteness": ".lock_completeness",
        "FlextInfraWorkspaceNativeReference": ".native_reference",
        "FlextInfraWorkspaceNativeReferenceBindingsMixin": (
            "._native_reference_bindings"
        ),
        "FlextInfraWorkspaceNativeReferenceFunctionsMixin": (
            "._native_reference_functions"
        ),
        "FlextInfraWorkspaceNativeReferencePrimitivesMixin": (
            "._native_reference_primitives"
        ),
        "FlextInfraWorkspaceNativeReferenceSymbolsMixin": "._native_reference_symbols",
        "FlextInfraWorkspaceNativeReferenceValuesMixin": "._native_reference_values",
        "FlextInfraWorkspacePropagation": ".propagation",
    }),
    public_exports=__all__,
)
