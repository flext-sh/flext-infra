# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._constants._exports import (
        FLEXT_INFRA_LAZY_IMPORTS as FLEXT_INFRA_LAZY_IMPORTS,
    )
    from flext_infra._constants._exports_lazy_part_01 import (
        FLEXT_INFRA_LAZY_IMPORTS_PART_01 as FLEXT_INFRA_LAZY_IMPORTS_PART_01,
    )
    from flext_infra._constants._exports_lazy_part_02 import (
        FLEXT_INFRA_LAZY_IMPORTS_PART_02 as FLEXT_INFRA_LAZY_IMPORTS_PART_02,
    )
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
_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._exports": ("FLEXT_INFRA_LAZY_IMPORTS",),
        "._exports_lazy_part_01": ("FLEXT_INFRA_LAZY_IMPORTS_PART_01",),
        "._exports_lazy_part_02": ("FLEXT_INFRA_LAZY_IMPORTS_PART_02",),
        ".adapters": ("FlextInfraConstantsAdapters",),
        ".base": ("FlextInfraConstantsBase",),
        ".basemk": ("FlextInfraConstantsBasemk",),
        ".census": ("FlextInfraConstantsCensus",),
        ".check": ("FlextInfraConstantsCheck",),
        ".cli": ("FlextInfraConstantsCli",),
        ".cli_routes": (
            "CODEGEN_ROUTES",
            "VALIDATE_ROUTES",
            "WORKSPACE_ROUTES",
        ),
        ".cli_routes_validate_commands": ("VALIDATE_COMMAND_ROUTES",),
        ".codegen": ("FlextInfraConstantsCodegen",),
        ".codegen_detection": ("FlextInfraConstantsCodegenDetection",),
        ".codegen_lazy": ("FlextInfraConstantsCodegenLazy",),
        ".codegen_render_names": ("FlextInfraConstantsCodegenRenderNames",),
        ".deps": ("FlextInfraConstantsDeps",),
        ".detectors": ("FlextInfraConstantsDetectors",),
        ".docs": ("FlextInfraConstantsDocs",),
        ".github": ("FlextInfraConstantsGithub",),
        ".make": ("FlextInfraConstantsMake",),
        ".namespace": ("FlextInfraConstantsNamespace",),
        ".refactor": ("FlextInfraConstantsRefactor",),
        ".release": ("FlextInfraConstantsRelease",),
        ".rope": ("FlextInfraConstantsRope",),
        ".source_code": ("FlextInfraConstantsSourceCode",),
        ".validate": ("FlextInfraConstantsSharedInfra",),
        ".workspace": ("FlextInfraConstantsWorkspace",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
