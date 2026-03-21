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
    from flext_infra.deps._phases.consolidate_groups import ConsolidateGroupsPhase
    from flext_infra.deps._phases.ensure_coverage import EnsureCoverageConfigPhase
    from flext_infra.deps._phases.ensure_extra_paths import EnsureExtraPathsPhase
    from flext_infra.deps._phases.ensure_formatting import EnsureFormattingToolingPhase
    from flext_infra.deps._phases.ensure_mypy import EnsureMypyConfigPhase
    from flext_infra.deps._phases.ensure_namespace import EnsureNamespaceToolingPhase
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        EnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import EnsurePyreflyConfigPhase
    from flext_infra.deps._phases.ensure_pyright import EnsurePyrightConfigPhase
    from flext_infra.deps._phases.ensure_pytest import EnsurePytestConfigPhase
    from flext_infra.deps._phases.ensure_ruff import EnsureRuffConfigPhase
    from flext_infra.deps._phases.inject_comments import InjectCommentsPhase
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector, main
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService,
        shutil,
    )
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer, u
    from flext_infra.deps.path_sync import FlextInfraDependencyPathSync

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ConsolidateGroupsPhase": (
        "flext_infra.deps._phases.consolidate_groups",
        "ConsolidateGroupsPhase",
    ),
    "EnsureCoverageConfigPhase": (
        "flext_infra.deps._phases.ensure_coverage",
        "EnsureCoverageConfigPhase",
    ),
    "EnsureExtraPathsPhase": (
        "flext_infra.deps._phases.ensure_extra_paths",
        "EnsureExtraPathsPhase",
    ),
    "EnsureFormattingToolingPhase": (
        "flext_infra.deps._phases.ensure_formatting",
        "EnsureFormattingToolingPhase",
    ),
    "EnsureMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_mypy",
        "EnsureMypyConfigPhase",
    ),
    "EnsureNamespaceToolingPhase": (
        "flext_infra.deps._phases.ensure_namespace",
        "EnsureNamespaceToolingPhase",
    ),
    "EnsurePydanticMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "EnsurePydanticMypyConfigPhase",
    ),
    "EnsurePyreflyConfigPhase": (
        "flext_infra.deps._phases.ensure_pyrefly",
        "EnsurePyreflyConfigPhase",
    ),
    "EnsurePyrightConfigPhase": (
        "flext_infra.deps._phases.ensure_pyright",
        "EnsurePyrightConfigPhase",
    ),
    "EnsurePytestConfigPhase": (
        "flext_infra.deps._phases.ensure_pytest",
        "EnsurePytestConfigPhase",
    ),
    "EnsureRuffConfigPhase": (
        "flext_infra.deps._phases.ensure_ruff",
        "EnsureRuffConfigPhase",
    ),
    "FlextInfraConfigFixer": (
        "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraConfigFixer",
    ),
    "FlextInfraDependencyDetectionService": (
        "flext_infra.deps.detection",
        "FlextInfraDependencyDetectionService",
    ),
    "FlextInfraDependencyPathSync": (
        "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSync",
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
    "InjectCommentsPhase": (
        "flext_infra.deps._phases.inject_comments",
        "InjectCommentsPhase",
    ),
    "_phases": ("flext_infra.deps._phases", ""),
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
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyPathSync",
    "FlextInfraExtraPathsManager",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
    "InjectCommentsPhase",
    "_phases",
    "main",
    "shutil",
    "u",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
