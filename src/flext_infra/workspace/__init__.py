# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.workspace.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.workspace.base import (
        FlextInfraWorkspaceGeneratorBase as FlextInfraWorkspaceGeneratorBase,
    )
    from flext_infra.workspace.detector import (
        FlextInfraWorkspaceDetector as FlextInfraWorkspaceDetector,
    )
    from flext_infra.workspace.environment import (
        FlextInfraWorkspaceEnvironment as FlextInfraWorkspaceEnvironment,
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
    from flext_infra.workspace.rope import (
        FlextInfraRopeWorkspace as FlextInfraRopeWorkspace,
    )
    from flext_infra.workspace.sandbox_orchestrator import (
        FlextInfraSandboxOrchestrator as FlextInfraSandboxOrchestrator,
    )
    from flext_infra.workspace.sync import (
        FlextInfraSyncService as FlextInfraSyncService,
    )
    from flext_infra.workspace.vscode import (
        FlextInfraWorkspaceVscode as FlextInfraWorkspaceVscode,
    )
    from flext_infra.workspace.workspace_makefile import (
        FlextInfraWorkspaceMakefileGenerator as FlextInfraWorkspaceMakefileGenerator,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
