# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Workspace management services.

Provides services for workspace detection, synchronization, and orchestration
across the FLEXT ecosystem.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes


if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.workspace import maintenance
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        WorkspaceMode,
    )
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer,
        logger,
    )
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.sync import FlextInfraSyncService, main

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "FlextInfraOrchestratorService": ("flext_infra.workspace.orchestrator", "FlextInfraOrchestratorService"),
    "FlextInfraProjectMigrator": ("flext_infra.workspace.migrator", "FlextInfraProjectMigrator"),
    "FlextInfraPythonVersionEnforcer": ("flext_infra.workspace.maintenance.python_version", "FlextInfraPythonVersionEnforcer"),
    "FlextInfraSyncService": ("flext_infra.workspace.sync", "FlextInfraSyncService"),
    "FlextInfraWorkspaceDetector": ("flext_infra.workspace.detector", "FlextInfraWorkspaceDetector"),
    "WorkspaceMode": ("flext_infra.workspace.detector", "WorkspaceMode"),
    "logger": ("flext_infra.workspace.maintenance.python_version", "logger"),
    "main": ("flext_infra.workspace.sync", "main"),
    "maintenance": ("flext_infra.workspace.maintenance", ""),
}

__all__ = [
    "FlextInfraOrchestratorService",
    "FlextInfraProjectMigrator",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraSyncService",
    "FlextInfraWorkspaceDetector",
    "WorkspaceMode",
    "logger",
    "main",
    "maintenance",
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
