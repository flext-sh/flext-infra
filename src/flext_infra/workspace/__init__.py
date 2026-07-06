# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.workspace.base import FlextInfraWorkspaceGeneratorBase
    from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
    from flext_infra.workspace.environment import FlextInfraWorkspaceEnvironment
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
    from flext_infra.workspace.rope import FlextInfraRopeWorkspace
    from flext_infra.workspace.sandbox_orchestrator import FlextInfraSandboxOrchestrator
    from flext_infra.workspace.sync import FlextInfraSyncService
    from flext_infra.workspace.vscode import FlextInfraWorkspaceVscode
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraWorkspaceGeneratorBase",),
        ".detector": ("FlextInfraWorkspaceDetector",),
        ".environment": ("FlextInfraWorkspaceEnvironment",),
        ".migrator": ("FlextInfraProjectMigrator",),
        ".orchestrator": ("FlextInfraOrchestratorService",),
        ".project_makefile": ("FlextInfraProjectMakefileUpdater",),
        ".rope": ("FlextInfraRopeWorkspace",),
        ".sandbox_orchestrator": ("FlextInfraSandboxOrchestrator",),
        ".sync": ("FlextInfraSyncService",),
        ".vscode": ("FlextInfraWorkspaceVscode",),
        ".workspace_makefile": ("FlextInfraWorkspaceMakefileGenerator",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
