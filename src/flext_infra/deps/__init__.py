# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Dependency management services.

Provides the pyproject modernizer for workspace-wide dependency
synchronization and formatting.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps import (
        _phases as _phases,
        cli as cli,
        detection as detection,
        detector as detector,
        extra_paths as extra_paths,
        fix_pyrefly_config as fix_pyrefly_config,
        internal_sync as internal_sync,
        modernizer as modernizer,
        path_sync as path_sync,
    )
    from flext_infra.deps._phases import (
        consolidate_groups as consolidate_groups,
        ensure_coverage as ensure_coverage,
        ensure_extra_paths as ensure_extra_paths,
        ensure_formatting as ensure_formatting,
        ensure_mypy as ensure_mypy,
        ensure_namespace as ensure_namespace,
        ensure_pydantic_mypy as ensure_pydantic_mypy,
        ensure_pyrefly as ensure_pyrefly,
        ensure_pyright as ensure_pyright,
        ensure_pytest as ensure_pytest,
        ensure_ruff as ensure_ruff,
        inject_comments as inject_comments,
    )
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase as FlextInfraEnsureExtraPathsPhase,
    )
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps._phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps._phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps._phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
    from flext_infra.deps.cli import FlextInfraCliDeps as FlextInfraCliDeps
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionService as FlextInfraDependencyDetectionService,
    )
    from flext_infra.deps.detector import (
        FlextInfraRuntimeDevDependencyDetector as FlextInfraRuntimeDevDependencyDetector,
        main as main,
    )
    from flext_infra.deps.extra_paths import (
        FlextInfraExtraPathsManager as FlextInfraExtraPathsManager,
    )
    from flext_infra.deps.fix_pyrefly_config import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
    )
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService as FlextInfraInternalDependencySyncService,
    )
    from flext_infra.deps.modernizer import (
        FlextInfraPyprojectModernizer as FlextInfraPyprojectModernizer,
    )
    from flext_infra.deps.path_sync import (
        FlextInfraDependencyPathSync as FlextInfraDependencyPathSync,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliDeps": ["flext_infra.deps.cli", "FlextInfraCliDeps"],
    "FlextInfraConfigFixer": [
        "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraConfigFixer",
    ],
    "FlextInfraConsolidateGroupsPhase": [
        "flext_infra.deps._phases.consolidate_groups",
        "FlextInfraConsolidateGroupsPhase",
    ],
    "FlextInfraDependencyDetectionService": [
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionService",
    ],
    "FlextInfraDependencyPathSync": [
        "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSync",
    ],
    "FlextInfraEnsureCoverageConfigPhase": [
        "flext_infra.deps._phases.ensure_coverage",
        "FlextInfraEnsureCoverageConfigPhase",
    ],
    "FlextInfraEnsureExtraPathsPhase": [
        "flext_infra.deps._phases.ensure_extra_paths",
        "FlextInfraEnsureExtraPathsPhase",
    ],
    "FlextInfraEnsureFormattingToolingPhase": [
        "flext_infra.deps._phases.ensure_formatting",
        "FlextInfraEnsureFormattingToolingPhase",
    ],
    "FlextInfraEnsureMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_mypy",
        "FlextInfraEnsureMypyConfigPhase",
    ],
    "FlextInfraEnsureNamespaceToolingPhase": [
        "flext_infra.deps._phases.ensure_namespace",
        "FlextInfraEnsureNamespaceToolingPhase",
    ],
    "FlextInfraEnsurePydanticMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "FlextInfraEnsurePydanticMypyConfigPhase",
    ],
    "FlextInfraEnsurePyreflyConfigPhase": [
        "flext_infra.deps._phases.ensure_pyrefly",
        "FlextInfraEnsurePyreflyConfigPhase",
    ],
    "FlextInfraEnsurePyrightConfigPhase": [
        "flext_infra.deps._phases.ensure_pyright",
        "FlextInfraEnsurePyrightConfigPhase",
    ],
    "FlextInfraEnsurePytestConfigPhase": [
        "flext_infra.deps._phases.ensure_pytest",
        "FlextInfraEnsurePytestConfigPhase",
    ],
    "FlextInfraEnsureRuffConfigPhase": [
        "flext_infra.deps._phases.ensure_ruff",
        "FlextInfraEnsureRuffConfigPhase",
    ],
    "FlextInfraExtraPathsManager": [
        "flext_infra.deps.extra_paths",
        "FlextInfraExtraPathsManager",
    ],
    "FlextInfraInjectCommentsPhase": [
        "flext_infra.deps._phases.inject_comments",
        "FlextInfraInjectCommentsPhase",
    ],
    "FlextInfraInternalDependencySyncService": [
        "flext_infra.deps.internal_sync",
        "FlextInfraInternalDependencySyncService",
    ],
    "FlextInfraPyprojectModernizer": [
        "flext_infra.deps.modernizer",
        "FlextInfraPyprojectModernizer",
    ],
    "FlextInfraRuntimeDevDependencyDetector": [
        "flext_infra.deps.detector",
        "FlextInfraRuntimeDevDependencyDetector",
    ],
    "_phases": ["flext_infra.deps._phases", ""],
    "cli": ["flext_infra.deps.cli", ""],
    "consolidate_groups": ["flext_infra.deps._phases.consolidate_groups", ""],
    "detection": ["flext_infra.deps.detection", ""],
    "detector": ["flext_infra.deps.detector", ""],
    "ensure_coverage": ["flext_infra.deps._phases.ensure_coverage", ""],
    "ensure_extra_paths": ["flext_infra.deps._phases.ensure_extra_paths", ""],
    "ensure_formatting": ["flext_infra.deps._phases.ensure_formatting", ""],
    "ensure_mypy": ["flext_infra.deps._phases.ensure_mypy", ""],
    "ensure_namespace": ["flext_infra.deps._phases.ensure_namespace", ""],
    "ensure_pydantic_mypy": ["flext_infra.deps._phases.ensure_pydantic_mypy", ""],
    "ensure_pyrefly": ["flext_infra.deps._phases.ensure_pyrefly", ""],
    "ensure_pyright": ["flext_infra.deps._phases.ensure_pyright", ""],
    "ensure_pytest": ["flext_infra.deps._phases.ensure_pytest", ""],
    "ensure_ruff": ["flext_infra.deps._phases.ensure_ruff", ""],
    "extra_paths": ["flext_infra.deps.extra_paths", ""],
    "fix_pyrefly_config": ["flext_infra.deps.fix_pyrefly_config", ""],
    "inject_comments": ["flext_infra.deps._phases.inject_comments", ""],
    "internal_sync": ["flext_infra.deps.internal_sync", ""],
    "main": ["flext_infra.deps.detector", "main"],
    "modernizer": ["flext_infra.deps.modernizer", ""],
    "path_sync": ["flext_infra.deps.path_sync", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliDeps",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyPathSync",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
    "_phases",
    "cli",
    "consolidate_groups",
    "detection",
    "detector",
    "ensure_coverage",
    "ensure_extra_paths",
    "ensure_formatting",
    "ensure_mypy",
    "ensure_namespace",
    "ensure_pydantic_mypy",
    "ensure_pyrefly",
    "ensure_pyright",
    "ensure_pytest",
    "ensure_ruff",
    "extra_paths",
    "fix_pyrefly_config",
    "inject_comments",
    "internal_sync",
    "main",
    "modernizer",
    "path_sync",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
