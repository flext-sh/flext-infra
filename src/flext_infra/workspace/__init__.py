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
        cli,
        detector,
        migrator,
        orchestrator,
        project_makefile,
        sync,
        workspace_makefile,
    )
    from flext_infra.workspace.cli import *
    from flext_infra.workspace.detector import *
    from flext_infra.workspace.maintenance import *
    from flext_infra.workspace.migrator import *
    from flext_infra.workspace.orchestrator import *
    from flext_infra.workspace.project_makefile import *
    from flext_infra.workspace.sync import *
    from flext_infra.workspace.workspace_makefile import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliMaintenance": "flext_infra.workspace.maintenance.cli",
    "FlextInfraCliWorkspace": "flext_infra.workspace.cli",
    "FlextInfraOrchestratorService": "flext_infra.workspace.orchestrator",
    "FlextInfraProjectMakefileUpdater": "flext_infra.workspace.project_makefile",
    "FlextInfraProjectMigrator": "flext_infra.workspace.migrator",
    "FlextInfraPythonVersionEnforcer": "flext_infra.workspace.maintenance.python_version",
    "FlextInfraSyncService": "flext_infra.workspace.sync",
    "FlextInfraWorkspaceDetector": "flext_infra.workspace.detector",
    "FlextInfraWorkspaceMakefileGenerator": "flext_infra.workspace.workspace_makefile",
    "FlextInfraWorkspaceMode": "flext_infra.workspace.detector",
    "cli": "flext_infra.workspace.cli",
    "detector": "flext_infra.workspace.detector",
    "logger": "flext_infra.workspace.maintenance.python_version",
    "main": "flext_infra.workspace.sync",
    "maintenance": "flext_infra.workspace.maintenance",
    "migrator": "flext_infra.workspace.migrator",
    "orchestrator": "flext_infra.workspace.orchestrator",
    "project_makefile": "flext_infra.workspace.project_makefile",
    "python_version": "flext_infra.workspace.maintenance.python_version",
    "sync": "flext_infra.workspace.sync",
    "workspace_makefile": "flext_infra.workspace.workspace_makefile",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
