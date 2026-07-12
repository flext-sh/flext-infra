# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra._constants.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra._constants.adapters import (
        FlextInfraConstantsAdapters as FlextInfraConstantsAdapters,
    )
    from flext_infra._constants.base import (
        FlextInfraConstantsBase as FlextInfraConstantsBase,
    )
    from flext_infra._constants.basemk import (
        FlextInfraConstantsBasemk as FlextInfraConstantsBasemk,
    )
    from flext_infra._constants.census import (
        FlextInfraConstantsCensus as FlextInfraConstantsCensus,
    )
    from flext_infra._constants.check import (
        FlextInfraConstantsCheck as FlextInfraConstantsCheck,
    )
    from flext_infra._constants.cli import (
        FlextInfraConstantsCli as FlextInfraConstantsCli,
    )
    from flext_infra._constants.cli_routes import (
        CODEGEN_ROUTES as CODEGEN_ROUTES,
        VALIDATE_ROUTES as VALIDATE_ROUTES,
        WORKSPACE_ROUTES as WORKSPACE_ROUTES,
    )
    from flext_infra._constants.cli_routes_validate_commands import (
        VALIDATE_COMMAND_ROUTES as VALIDATE_COMMAND_ROUTES,
    )
    from flext_infra._constants.codegen import (
        FlextInfraConstantsCodegen as FlextInfraConstantsCodegen,
    )
    from flext_infra._constants.codegen_detection import (
        FlextInfraConstantsCodegenDetection as FlextInfraConstantsCodegenDetection,
    )
    from flext_infra._constants.codegen_lazy import (
        FlextInfraConstantsCodegenLazy as FlextInfraConstantsCodegenLazy,
    )
    from flext_infra._constants.codegen_project import (
        FlextInfraConstantsCodegenProject as FlextInfraConstantsCodegenProject,
    )
    from flext_infra._constants.codegen_render_names import (
        FlextInfraConstantsCodegenRenderNames as FlextInfraConstantsCodegenRenderNames,
    )
    from flext_infra._constants.deps import (
        FlextInfraConstantsDeps as FlextInfraConstantsDeps,
    )
    from flext_infra._constants.detectors import (
        FlextInfraConstantsDetectors as FlextInfraConstantsDetectors,
    )
    from flext_infra._constants.docs import (
        FlextInfraConstantsDocs as FlextInfraConstantsDocs,
    )
    from flext_infra._constants.github import (
        FlextInfraConstantsGithub as FlextInfraConstantsGithub,
    )
    from flext_infra._constants.make import (
        FlextInfraConstantsMake as FlextInfraConstantsMake,
    )
    from flext_infra._constants.namespace import (
        FlextInfraConstantsNamespace as FlextInfraConstantsNamespace,
    )
    from flext_infra._constants.refactor import (
        FlextInfraConstantsRefactor as FlextInfraConstantsRefactor,
    )
    from flext_infra._constants.release import (
        FlextInfraConstantsRelease as FlextInfraConstantsRelease,
    )
    from flext_infra._constants.rope import (
        FlextInfraConstantsRope as FlextInfraConstantsRope,
    )
    from flext_infra._constants.source_code import (
        FlextInfraConstantsSourceCode as FlextInfraConstantsSourceCode,
    )
    from flext_infra._constants.validate import (
        FlextInfraConstantsSharedInfra as FlextInfraConstantsSharedInfra,
    )
    from flext_infra._constants.workspace import (
        FlextInfraConstantsWorkspace as FlextInfraConstantsWorkspace,
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
