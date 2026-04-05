# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Workspace package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import flext_infra.workspace.cli as _flext_infra_workspace_cli

    cli = _flext_infra_workspace_cli
    import flext_infra.workspace.detector as _flext_infra_workspace_detector
    from flext_infra.workspace.cli import FlextInfraCliWorkspace

    detector = _flext_infra_workspace_detector
    import flext_infra.workspace.maintenance as _flext_infra_workspace_maintenance
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode,
    )

    maintenance = _flext_infra_workspace_maintenance
    import flext_infra.workspace.migrator as _flext_infra_workspace_migrator
    from flext_infra.workspace.maintenance import (
        FlextInfraCliMaintenance,
        FlextInfraPythonVersionEnforcer,
        logger,
        python_version,
    )

    migrator = _flext_infra_workspace_migrator
    import flext_infra.workspace.orchestrator as _flext_infra_workspace_orchestrator
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator

    orchestrator = _flext_infra_workspace_orchestrator
    import flext_infra.workspace.project_makefile as _flext_infra_workspace_project_makefile
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService

    project_makefile = _flext_infra_workspace_project_makefile
    import flext_infra.workspace.sync as _flext_infra_workspace_sync
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater

    sync = _flext_infra_workspace_sync
    import flext_infra.workspace.workspace_makefile as _flext_infra_workspace_workspace_makefile
    from flext_infra.workspace.sync import FlextInfraSyncService, main

    workspace_makefile = _flext_infra_workspace_workspace_makefile
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    ("flext_infra.workspace.maintenance",),
    {
        "FlextInfraCliWorkspace": "flext_infra.workspace.cli",
        "FlextInfraOrchestratorService": "flext_infra.workspace.orchestrator",
        "FlextInfraProjectMakefileUpdater": "flext_infra.workspace.project_makefile",
        "FlextInfraProjectMigrator": "flext_infra.workspace.migrator",
        "FlextInfraSyncService": "flext_infra.workspace.sync",
        "FlextInfraWorkspaceDetector": "flext_infra.workspace.detector",
        "FlextInfraWorkspaceMakefileGenerator": "flext_infra.workspace.workspace_makefile",
        "FlextInfraWorkspaceMode": "flext_infra.workspace.detector",
        "cli": "flext_infra.workspace.cli",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "detector": "flext_infra.workspace.detector",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "h": ("flext_core.handlers", "FlextHandlers"),
        "main": "flext_infra.workspace.sync",
        "maintenance": "flext_infra.workspace.maintenance",
        "migrator": "flext_infra.workspace.migrator",
        "orchestrator": "flext_infra.workspace.orchestrator",
        "project_makefile": "flext_infra.workspace.project_makefile",
        "r": ("flext_core.result", "FlextResult"),
        "s": ("flext_core.service", "FlextService"),
        "sync": "flext_infra.workspace.sync",
        "workspace_makefile": "flext_infra.workspace.workspace_makefile",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)

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
    "d",
    "detector",
    "e",
    "h",
    "logger",
    "main",
    "maintenance",
    "migrator",
    "orchestrator",
    "project_makefile",
    "python_version",
    "r",
    "s",
    "sync",
    "workspace_makefile",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
