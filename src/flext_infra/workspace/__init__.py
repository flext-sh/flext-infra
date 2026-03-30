# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Workspace management services.

Provides services for workspace detection, synchronization, and orchestration
across the FLEXT ecosystem.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.workspace import (
        cli,
        detector,
        maintenance,
        migrator,
        orchestrator,
        project_makefile,
        sync,
        workspace_makefile,
    )
    from flext_infra.workspace.cli import FlextInfraCliWorkspace
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode,
    )
    from flext_infra.workspace.maintenance import python_version
    from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer,
        logger,
    )
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
    from flext_infra.workspace.sync import FlextInfraSyncService, main
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliMaintenance": [
        "flext_infra.workspace.maintenance.cli",
        "FlextInfraCliMaintenance",
    ],
    "FlextInfraCliWorkspace": ["flext_infra.workspace.cli", "FlextInfraCliWorkspace"],
    "FlextInfraOrchestratorService": [
        "flext_infra.workspace.orchestrator",
        "FlextInfraOrchestratorService",
    ],
    "FlextInfraProjectMakefileUpdater": [
        "flext_infra.workspace.project_makefile",
        "FlextInfraProjectMakefileUpdater",
    ],
    "FlextInfraProjectMigrator": [
        "flext_infra.workspace.migrator",
        "FlextInfraProjectMigrator",
    ],
    "FlextInfraPythonVersionEnforcer": [
        "flext_infra.workspace.maintenance.python_version",
        "FlextInfraPythonVersionEnforcer",
    ],
    "FlextInfraSyncService": ["flext_infra.workspace.sync", "FlextInfraSyncService"],
    "FlextInfraWorkspaceDetector": [
        "flext_infra.workspace.detector",
        "FlextInfraWorkspaceDetector",
    ],
    "FlextInfraWorkspaceMakefileGenerator": [
        "flext_infra.workspace.workspace_makefile",
        "FlextInfraWorkspaceMakefileGenerator",
    ],
    "FlextInfraWorkspaceMode": [
        "flext_infra.workspace.detector",
        "FlextInfraWorkspaceMode",
    ],
    "cli": ["flext_infra.workspace.cli", ""],
    "detector": ["flext_infra.workspace.detector", ""],
    "logger": ["flext_infra.workspace.maintenance.python_version", "logger"],
    "main": ["flext_infra.workspace.sync", "main"],
    "maintenance": ["flext_infra.workspace.maintenance", ""],
    "migrator": ["flext_infra.workspace.migrator", ""],
    "orchestrator": ["flext_infra.workspace.orchestrator", ""],
    "project_makefile": ["flext_infra.workspace.project_makefile", ""],
    "python_version": ["flext_infra.workspace.maintenance.python_version", ""],
    "sync": ["flext_infra.workspace.sync", ""],
    "workspace_makefile": ["flext_infra.workspace.workspace_makefile", ""],
}

__all__ = [
    "FlextInfraCliMaintenance",
    "FlextInfraCliWorkspace",
    "FlextInfraOrchestratorService",
    "FlextInfraProjectMakefileUpdater",
    "FlextInfraProjectMigrator",
    "FlextInfraPythonVersionEnforcer",
    "FlextInfraSyncService",
    "FlextInfraWorkspaceDetector",
    "FlextInfraWorkspaceMakefileGenerator",
    "FlextInfraWorkspaceMode",
    "cli",
    "detector",
    "logger",
    "main",
    "maintenance",
    "migrator",
    "orchestrator",
    "project_makefile",
    "python_version",
    "sync",
    "workspace_makefile",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
