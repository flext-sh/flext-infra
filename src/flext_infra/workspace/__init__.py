# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Workspace package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

_LAZY_IMPORTS = merge_lazy_imports(
    ("flext_infra.workspace.maintenance",),
    {
        "FlextInfraCliWorkspace": (
            "flext_infra.workspace.cli",
            "FlextInfraCliWorkspace",
        ),
        "FlextInfraOrchestratorService": (
            "flext_infra.workspace.orchestrator",
            "FlextInfraOrchestratorService",
        ),
        "FlextInfraProjectMakefileUpdater": (
            "flext_infra.workspace.project_makefile",
            "FlextInfraProjectMakefileUpdater",
        ),
        "FlextInfraProjectMigrator": (
            "flext_infra.workspace.migrator",
            "FlextInfraProjectMigrator",
        ),
        "FlextInfraSyncService": (
            "flext_infra.workspace.sync",
            "FlextInfraSyncService",
        ),
        "FlextInfraWorkspaceDetector": (
            "flext_infra.workspace.detector",
            "FlextInfraWorkspaceDetector",
        ),
        "FlextInfraWorkspaceMakefileGenerator": (
            "flext_infra.workspace.workspace_makefile",
            "FlextInfraWorkspaceMakefileGenerator",
        ),
        "c": ("flext_core.constants", "FlextConstants"),
        "cli": "flext_infra.workspace.cli",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "detector": "flext_infra.workspace.detector",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "h": ("flext_core.handlers", "FlextHandlers"),
        "m": ("flext_core.models", "FlextModels"),
        "maintenance": "flext_infra.workspace.maintenance",
        "migrator": "flext_infra.workspace.migrator",
        "orchestrator": "flext_infra.workspace.orchestrator",
        "p": ("flext_core.protocols", "FlextProtocols"),
        "project_makefile": "flext_infra.workspace.project_makefile",
        "r": ("flext_core.result", "FlextResult"),
        "s": ("flext_core.service", "FlextService"),
        "sync": "flext_infra.workspace.sync",
        "t": ("flext_core.typings", "FlextTypes"),
        "u": ("flext_core.utilities", "FlextUtilities"),
        "workspace_makefile": "flext_infra.workspace.workspace_makefile",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("logger", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
