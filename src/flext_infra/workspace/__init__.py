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
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_infra.workspace._constants import *
    from flext_infra.workspace._models import *
    from flext_infra.workspace.cli import *
    from flext_infra.workspace.detector import *
    from flext_infra.workspace.maintenance import *
    from flext_infra.workspace.migrator import *
    from flext_infra.workspace.orchestrator import *
    from flext_infra.workspace.project_makefile import *
    from flext_infra.workspace.sync import *
    from flext_infra.workspace.workspace_makefile import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = merge_lazy_imports(
    ("flext_infra.workspace.maintenance",),
    {
        "FlextInfraCliWorkspace": "flext_infra.workspace.cli",
        "FlextInfraOrchestratorService": "flext_infra.workspace.orchestrator",
        "FlextInfraProjectMakefileUpdater": "flext_infra.workspace.project_makefile",
        "FlextInfraProjectMigrator": "flext_infra.workspace.migrator",
        "FlextInfraSyncService": "flext_infra.workspace.sync",
        "FlextInfraWorkspaceConstants": "flext_infra.workspace._constants",
        "FlextInfraWorkspaceDetector": "flext_infra.workspace.detector",
        "FlextInfraWorkspaceMakefileGenerator": "flext_infra.workspace.workspace_makefile",
        "FlextInfraWorkspaceMode": "flext_infra.workspace.detector",
        "FlextInfraWorkspaceModels": "flext_infra.workspace._models",
        "_constants": "flext_infra.workspace._constants",
        "_models": "flext_infra.workspace._models",
        "cli": "flext_infra.workspace.cli",
        "detector": "flext_infra.workspace.detector",
        "main": "flext_infra.workspace.sync",
        "maintenance": "flext_infra.workspace.maintenance",
        "migrator": "flext_infra.workspace.migrator",
        "orchestrator": "flext_infra.workspace.orchestrator",
        "project_makefile": "flext_infra.workspace.project_makefile",
        "sync": "flext_infra.workspace.sync",
        "workspace_makefile": "flext_infra.workspace.workspace_makefile",
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
