# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Dependency management services.

Provides the pyproject modernizer for workspace-wide dependency
synchronization and formatting.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.deps import _phases
    from flext_infra.deps._phases import (
        ConsolidateGroupsPhase,
        EnsureCoverageConfigPhase,
        EnsureExtraPathsPhase,
        EnsureFormattingToolingPhase,
        EnsureMypyConfigPhase,
        EnsureNamespaceToolingPhase,
        EnsurePydanticMypyConfigPhase,
        EnsurePyreflyConfigPhase,
        EnsurePyrightConfigPhase,
        EnsurePytestConfigPhase,
        EnsureRuffConfigPhase,
        InjectCommentsPhase,
    )
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionHelpers,
        FlextInfraDependencyDetectionService,
        dm,
    )
    from flext_infra.deps.detector import (
        FlextInfraRuntimeDevDependencyDetector,
        FlextInfraUtilitiesIo,
        FlextInfraUtilitiesPaths,
        FlextInfraUtilitiesReporting,
        FlextInfraUtilitiesSubprocess,
        main,
    )
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService,
        shutil,
    )
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer, u
    from flext_infra.deps.path_sync import FlextInfraDependencyPathSync
    from flext_infra.deps.tool_config import FlextInfraDependencyToolConfig

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ConsolidateGroupsPhase": ("flext_infra.deps._phases", "ConsolidateGroupsPhase"),
    "EnsureCoverageConfigPhase": (
        "flext_infra.deps._phases",
        "EnsureCoverageConfigPhase",
    ),
    "EnsureExtraPathsPhase": ("flext_infra.deps._phases", "EnsureExtraPathsPhase"),
    "EnsureFormattingToolingPhase": (
        "flext_infra.deps._phases",
        "EnsureFormattingToolingPhase",
    ),
    "EnsureMypyConfigPhase": ("flext_infra.deps._phases", "EnsureMypyConfigPhase"),
    "EnsureNamespaceToolingPhase": (
        "flext_infra.deps._phases",
        "EnsureNamespaceToolingPhase",
    ),
    "EnsurePydanticMypyConfigPhase": (
        "flext_infra.deps._phases",
        "EnsurePydanticMypyConfigPhase",
    ),
    "EnsurePyreflyConfigPhase": (
        "flext_infra.deps._phases",
        "EnsurePyreflyConfigPhase",
    ),
    "EnsurePyrightConfigPhase": (
        "flext_infra.deps._phases",
        "EnsurePyrightConfigPhase",
    ),
    "EnsurePytestConfigPhase": ("flext_infra.deps._phases", "EnsurePytestConfigPhase"),
    "EnsureRuffConfigPhase": ("flext_infra.deps._phases", "EnsureRuffConfigPhase"),
    "FlextInfraConfigFixer": (
        "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraConfigFixer",
    ),
    "FlextInfraDependencyDetectionHelpers": (
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionHelpers",
    ),
    "FlextInfraDependencyDetectionService": (
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionService",
    ),
    "FlextInfraDependencyPathSync": (
        "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSync",
    ),
    "FlextInfraDependencyToolConfig": (
        "flext_infra.deps.tool_config",
        "FlextInfraDependencyToolConfig",
    ),
    "FlextInfraExtraPathsManager": (
        "flext_infra.deps.extra_paths",
        "FlextInfraExtraPathsManager",
    ),
    "FlextInfraInternalDependencySyncService": (
        "flext_infra.deps.internal_sync",
        "FlextInfraInternalDependencySyncService",
    ),
    "FlextInfraPyprojectModernizer": (
        "flext_infra.deps.modernizer",
        "FlextInfraPyprojectModernizer",
    ),
    "FlextInfraRuntimeDevDependencyDetector": (
        "flext_infra.deps.detector",
        "FlextInfraRuntimeDevDependencyDetector",
    ),
    "FlextInfraUtilitiesIo": ("flext_infra.deps.detector", "FlextInfraUtilitiesIo"),
    "FlextInfraUtilitiesPaths": (
        "flext_infra.deps.detector",
        "FlextInfraUtilitiesPaths",
    ),
    "FlextInfraUtilitiesReporting": (
        "flext_infra.deps.detector",
        "FlextInfraUtilitiesReporting",
    ),
    "FlextInfraUtilitiesSubprocess": (
        "flext_infra.deps.detector",
        "FlextInfraUtilitiesSubprocess",
    ),
    "InjectCommentsPhase": ("flext_infra.deps._phases", "InjectCommentsPhase"),
    "_phases": ("flext_infra.deps._phases", ""),
    "dm": ("flext_infra.deps.detection", "dm"),
    "main": ("flext_infra.deps.detector", "main"),
    "shutil": ("flext_infra.deps.internal_sync", "shutil"),
    "u": ("flext_infra.deps.modernizer", "u"),
}

__all__ = [
    "ConsolidateGroupsPhase",
    "EnsureCoverageConfigPhase",
    "EnsureExtraPathsPhase",
    "EnsureFormattingToolingPhase",
    "EnsureMypyConfigPhase",
    "EnsureNamespaceToolingPhase",
    "EnsurePydanticMypyConfigPhase",
    "EnsurePyreflyConfigPhase",
    "EnsurePyrightConfigPhase",
    "EnsurePytestConfigPhase",
    "EnsureRuffConfigPhase",
    "FlextInfraConfigFixer",
    "FlextInfraDependencyDetectionHelpers",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyToolConfig",
    "FlextInfraExtraPathsManager",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesSubprocess",
    "InjectCommentsPhase",
    "_phases",
    "dm",
    "main",
    "shutil",
    "u",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
