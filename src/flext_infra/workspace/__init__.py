# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Workspace package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.workspace import (
        _constants,
        _models,
        cli,
        detector,
        maintenance,
        migrator,
        orchestrator,
        project_makefile,
        sync,
        workspace_makefile,
    )
    from flext_infra.workspace._constants import FlextInfraWorkspaceConstants
    from flext_infra.workspace._models import FlextInfraWorkspaceModels
    from flext_infra.workspace.cli import FlextInfraCliWorkspace
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector,
        FlextInfraWorkspaceMode,
    )
    from flext_infra.workspace.maintenance import (
        FlextInfraCliMaintenance,
        FlextInfraPythonVersionEnforcer,
        logger,
        python_version,
    )
    from flext_infra.workspace.migrator import FlextInfraProjectMigrator
    from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
    from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
    from flext_infra.workspace.sync import FlextInfraSyncService, main
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = merge_lazy_imports(
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
        "c": ("flext_core.constants", "FlextConstants"),
        "cli": "flext_infra.workspace.cli",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "detector": "flext_infra.workspace.detector",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "h": ("flext_core.handlers", "FlextHandlers"),
        "m": ("flext_core.models", "FlextModels"),
        "main": "flext_infra.workspace.sync",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
