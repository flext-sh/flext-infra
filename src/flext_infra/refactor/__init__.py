# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._accessor.expression import (
        FlextInfraRefactorAccessorExpression,
    )
    from flext_infra.refactor._accessor.origin import FlextInfraRefactorAccessorOrigin
    from flext_infra.refactor._accessor.report import FlextInfraRefactorAccessorReport
    from flext_infra.refactor._accessor.rewrite import FlextInfraRefactorAccessorRewrite
    from flext_infra.refactor._accessor.warnings import (
        FlextInfraRefactorAccessorWarnings,
    )
    from flext_infra.refactor._census.collect import FlextInfraRefactorCensusCollect
    from flext_infra.refactor._census.collect_helpers import (
        FlextInfraRefactorCensusCollectHelpers,
    )
    from flext_infra.refactor._census.filters import FlextInfraRefactorCensusFilters
    from flext_infra.refactor._census.objects import FlextInfraRefactorCensusObjects
    from flext_infra.refactor._census.project import FlextInfraRefactorCensusProject
    from flext_infra.refactor._census.removal import FlextInfraRefactorCensusRemoval
    from flext_infra.refactor._census.render import FlextInfraRefactorCensusRender
    from flext_infra.refactor._namespace.enforcer_project import (
        FlextInfraRefactorNamespaceEnforcerProject,
    )
    from flext_infra.refactor._project.classifier_deps import (
        FlextInfraRefactorProjectClassifierDeps,
    )
    from flext_infra.refactor._project.classifier_family import (
        FlextInfraRefactorProjectClassifierFamily,
    )
    from flext_infra.refactor._wrapper.rewrite import FlextInfraRefactorWrapperRewrite
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
    "FlextInfraRefactorNamespace",
    "FlextInfraRefactorNamespaceEnforcerProject",
    "FlextInfraRefactorProject",
    "FlextInfraRefactorProjectClassifierDeps",
    "FlextInfraRefactorProjectClassifierFamily",
    "FlextInfraRefactorViolationsSweep",
    "FlextInfraRefactorWrapper",
    "FlextInfraRefactorWrapperRewrite",
    "FlextInfraWrapperRootNamespaceRefactor",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraAccessorMigrationOrchestrator": ".accessor_migration",
        "FlextInfraNamespaceEnforcer": ".namespace_enforcer",
        "FlextInfraNamespaceRelocationCascade": ".namespace_relocations",
        "FlextInfraProjectClassifier": ".project_classifier",
        "FlextInfraRefactorAccessor": ".accessor",
        "FlextInfraRefactorAccessorExpression": "._accessor.expression",
        "FlextInfraRefactorAccessorOrigin": "._accessor.origin",
        "FlextInfraRefactorAccessorReport": "._accessor.report",
        "FlextInfraRefactorAccessorRewrite": "._accessor.rewrite",
        "FlextInfraRefactorAccessorWarnings": "._accessor.warnings",
        "FlextInfraRefactorCensus": ".census",
        "FlextInfraRefactorCensusCollect": "._census.collect",
        "FlextInfraRefactorCensusCollectHelpers": "._census.collect_helpers",
        "FlextInfraRefactorCensusFilters": "._census.filters",
        "FlextInfraRefactorCensusObjects": "._census.objects",
        "FlextInfraRefactorCensusProject": "._census.project",
        "FlextInfraRefactorCensusRemoval": "._census.removal",
        "FlextInfraRefactorCensusRender": "._census.render",
        "FlextInfraRefactorNamespace": ".namespace",
        "FlextInfraRefactorNamespaceEnforcerProject": "._namespace.enforcer_project",
        "FlextInfraRefactorProject": ".project",
        "FlextInfraRefactorProjectClassifierDeps": "._project.classifier_deps",
        "FlextInfraRefactorProjectClassifierFamily": "._project.classifier_family",
        "FlextInfraRefactorViolationsSweep": ".violations_sweep",
        "FlextInfraRefactorWrapper": ".wrapper",
        "FlextInfraRefactorWrapperRewrite": "._wrapper.rewrite",
        "FlextInfraWrapperRootNamespaceRefactor": ".wrapper_root_namespace",
    }),
    public_exports=__all__,
)
