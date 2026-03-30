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

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.workspace import (
        cli as cli,
        detector as detector,
        maintenance as maintenance,
        migrator as migrator,
        orchestrator as orchestrator,
        project_makefile as project_makefile,
        sync as sync,
        workspace_makefile as workspace_makefile,
    )
    from flext_infra.workspace.cli import (
        FlextInfraCliWorkspace as FlextInfraCliWorkspace,
    )
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector as FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode as FlextInfraWorkspaceMode,
    )
    from flext_infra.workspace.maintenance import python_version as python_version
    from flext_infra.workspace.maintenance.cli import (
        FlextInfraCliMaintenance as FlextInfraCliMaintenance,
    )
    from flext_infra.workspace.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer as FlextInfraPythonVersionEnforcer,
        logger as logger,
    )
    from flext_infra.workspace.migrator import (
        FlextInfraProjectMigrator as FlextInfraProjectMigrator,
    )
    from flext_infra.workspace.orchestrator import (
        FlextInfraOrchestratorService as FlextInfraOrchestratorService,
    )
    from flext_infra.workspace.project_makefile import (
        FlextInfraProjectMakefileUpdater as FlextInfraProjectMakefileUpdater,
    )
    from flext_infra.workspace.sync import (
        FlextInfraSyncService as FlextInfraSyncService,
        main as main,
    )
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator as FlextInfraWorkspaceMakefileGenerator,
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

_EXPORTS: Sequence[str] = [
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
