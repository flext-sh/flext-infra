# AUTO-GENERATED FILE — Regenerate with: make gen
"""Services package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.services._codegen.vscode import FlextInfraCodegenVscode
    from flext_infra.services.candidate_bootstrap import (
        FlextInfraCandidateBootstrapService,
    )
    from flext_infra.services.cli_dispatch import FlextInfraCliDispatchService
    from flext_infra.services.cli_mod_progress import FlextInfraCliModProgress
    from flext_infra.services.cli_routes import FlextInfraCliRouteService
    from flext_infra.services.cli_routes_codegen import FlextInfraCodegenRoutes
    from flext_infra.services.cli_routes_refactor import FlextInfraRefactorRoutes
    from flext_infra.services.cli_routes_validate import FlextInfraValidationRoutes
    from flext_infra.services.cli_routes_validate_commands import (
        FlextInfraValidationCommandRoutes,
    )
    from flext_infra.services.cli_routes_workspace import FlextInfraWorkspaceRoutes
    from flext_infra.services.codegen import FlextInfraCodegenHandlers
    from flext_infra.services.mod import FlextInfraModHandlers


__all__: tuple[str, ...] = (
    "FlextInfraCandidateBootstrapService",
    "FlextInfraCliDispatchService",
    "FlextInfraCliModProgress",
    "FlextInfraCliRouteService",
    "FlextInfraCodegenHandlers",
    "FlextInfraCodegenRoutes",
    "FlextInfraCodegenVscode",
    "FlextInfraModHandlers",
    "FlextInfraRefactorRoutes",
    "FlextInfraValidationCommandRoutes",
    "FlextInfraValidationRoutes",
    "FlextInfraWorkspaceRoutes",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCandidateBootstrapService": ".candidate_bootstrap",
        "FlextInfraCliDispatchService": ".cli_dispatch",
        "FlextInfraCliModProgress": ".cli_mod_progress",
        "FlextInfraCliRouteService": ".cli_routes",
        "FlextInfraCodegenHandlers": ".codegen",
        "FlextInfraCodegenRoutes": ".cli_routes_codegen",
        "FlextInfraCodegenVscode": "._codegen.vscode",
        "FlextInfraModHandlers": ".mod",
        "FlextInfraRefactorRoutes": ".cli_routes_refactor",
        "FlextInfraValidationCommandRoutes": ".cli_routes_validate_commands",
        "FlextInfraValidationRoutes": ".cli_routes_validate",
        "FlextInfraWorkspaceRoutes": ".cli_routes_workspace",
    }),
    public_exports=__all__,
)
