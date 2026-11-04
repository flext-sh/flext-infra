# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.refactor package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor.accessor import FlextInfraRefactorAccessor
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.namespace import FlextInfraRefactorNamespace
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.namespace_relocations import (
        FlextInfraNamespaceRelocationCascade,
    )
    from flext_infra.refactor.project import FlextInfraRefactorProject
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
    from flext_infra.refactor.violations_sweep import FlextInfraRefactorViolationsSweep
    from flext_infra.refactor.wrapper import FlextInfraRefactorWrapper
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor,
    )


__all__: tuple[str, ...] = (
    "FlextInfraAccessorMigrationOrchestrator",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceRelocationCascade",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorAccessor",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorNamespace",
    "FlextInfraRefactorProject",
    "FlextInfraRefactorViolationsSweep",
    "FlextInfraRefactorWrapper",
    "FlextInfraWrapperRootNamespaceRefactor",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraAccessorMigrationOrchestrator": ".accessor_migration",
        "FlextInfraNamespaceEnforcer": ".namespace_enforcer",
        "FlextInfraNamespaceRelocationCascade": ".namespace_relocations",
        "FlextInfraProjectClassifier": ".project_classifier",
        "FlextInfraRefactorAccessor": ".accessor",
        "FlextInfraRefactorCensus": ".census",
        "FlextInfraRefactorNamespace": ".namespace",
        "FlextInfraRefactorProject": ".project",
        "FlextInfraRefactorViolationsSweep": ".violations_sweep",
        "FlextInfraRefactorWrapper": ".wrapper",
        "FlextInfraWrapperRootNamespaceRefactor": ".wrapper_root_namespace",
    },
    public_exports=__all__,
)
