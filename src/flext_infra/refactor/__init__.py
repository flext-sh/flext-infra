# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.refactor package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._accessor import (
        FlextInfraRefactorAccessorExpression,
        FlextInfraRefactorAccessorOrigin,
        FlextInfraRefactorAccessorReport,
        FlextInfraRefactorAccessorRewrite,
        FlextInfraRefactorAccessorWarnings,
    )
    from flext_infra.refactor._census import (
        FlextInfraRefactorCensusCollect,
        FlextInfraRefactorCensusCollectHelpers,
        FlextInfraRefactorCensusFilters,
        FlextInfraRefactorCensusObjects,
        FlextInfraRefactorCensusProject,
        FlextInfraRefactorCensusRemoval,
        FlextInfraRefactorCensusRender,
    )
    from flext_infra.refactor._namespace import (
        FlextInfraRefactorNamespaceEnforcerProject,
    )
    from flext_infra.refactor._project import (
        FlextInfraRefactorProjectClassifierDeps,
        FlextInfraRefactorProjectClassifierFamily,
    )
    from flext_infra.refactor._wrapper import FlextInfraRefactorWrapperRewrite
    from flext_infra.refactor.accessor_migration import (
        FlextInfraAccessorMigrationOrchestrator,
    )
    from flext_infra.refactor.census import FlextInfraRefactorCensus
    from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
    from flext_infra.refactor.namespace_relocations import (
        FlextInfraNamespaceRelocationCascade,
    )
    from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
    from flext_infra.refactor.violations_sweep import FlextInfraRefactorViolationsSweep
    from flext_infra.refactor.wrapper_root_namespace import (
        FlextInfraWrapperRootNamespaceRefactor,
    )


__all__: tuple[str, ...] = (
    "FlextInfraAccessorMigrationOrchestrator",
    "FlextInfraNamespaceEnforcer",
    "FlextInfraNamespaceRelocationCascade",
    "FlextInfraProjectClassifier",
    "FlextInfraRefactorAccessorExpression",
    "FlextInfraRefactorAccessorOrigin",
    "FlextInfraRefactorAccessorReport",
    "FlextInfraRefactorAccessorRewrite",
    "FlextInfraRefactorAccessorWarnings",
    "FlextInfraRefactorCensus",
    "FlextInfraRefactorCensusCollect",
    "FlextInfraRefactorCensusCollectHelpers",
    "FlextInfraRefactorCensusFilters",
    "FlextInfraRefactorCensusObjects",
    "FlextInfraRefactorCensusProject",
    "FlextInfraRefactorCensusRemoval",
    "FlextInfraRefactorCensusRender",
    "FlextInfraRefactorNamespaceEnforcerProject",
    "FlextInfraRefactorProjectClassifierDeps",
    "FlextInfraRefactorProjectClassifierFamily",
    "FlextInfraRefactorViolationsSweep",
    "FlextInfraRefactorWrapperRewrite",
    "FlextInfraWrapperRootNamespaceRefactor",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRefactorAccessorExpression": "._accessor_expression",
        "FlextInfraAccessorMigrationOrchestrator": ".accessor_migration",
        "FlextInfraRefactorAccessorReport": "._accessor_report",
        "FlextInfraRefactorAccessorRewrite": "._accessor_rewrite",
        "FlextInfraRefactorAccessorWarnings": "._accessor_warnings",
        "FlextInfraRefactorAccessorOrigin": "._accessor_origin",
        "FlextInfraNamespaceEnforcer": ".namespace_enforcer",
        "FlextInfraRefactorNamespaceEnforcerProject": "._namespace_enforcer_project",
        "FlextInfraNamespaceRelocationCascade": ".namespace_relocations",
        "FlextInfraProjectClassifier": ".project_classifier",
        "FlextInfraRefactorProjectClassifierDeps": "._project_classifier_deps",
        "FlextInfraRefactorProjectClassifierFamily": "._project_classifier_family",
        "FlextInfraRefactorCensus": ".census",
        "FlextInfraRefactorCensusCollectHelpers": "._census_collect_helpers",
        "FlextInfraRefactorCensusCollect": "._census_collect",
        "FlextInfraRefactorCensusFilters": "._census_filters",
        "FlextInfraRefactorCensusObjects": "._census_objects",
        "FlextInfraRefactorCensusProject": "._census_project",
        "FlextInfraRefactorCensusRemoval": "._census_removal",
        "FlextInfraRefactorCensusRender": "._census_render",
        "FlextInfraRefactorViolationsSweep": ".violations_sweep",
        "FlextInfraWrapperRootNamespaceRefactor": ".wrapper_root_namespace",
        "FlextInfraRefactorWrapperRewrite": "._wrapper_rewrite",
    }),
    public_exports=__all__,
)
