# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._constants.adapters import FlextInfraConstantsAdapters
    from flext_infra._constants.base import FlextInfraConstantsBase
    from flext_infra._constants.basemk import FlextInfraConstantsBasemk
    from flext_infra._constants.census import FlextInfraConstantsCensus
    from flext_infra._constants.check import FlextInfraConstantsCheck
    from flext_infra._constants.cli import FlextInfraConstantsCli
    from flext_infra._constants.cli_routes import (
        CODEGEN_ROUTES,
        VALIDATE_ROUTES,
        WORKSPACE_ROUTES,
    )
    from flext_infra._constants.cli_routes_validate_commands import (
        VALIDATE_COMMAND_ROUTES,
    )
    from flext_infra._constants.codegen import FlextInfraConstantsCodegen
    from flext_infra._constants.codegen_detection import (
        FlextInfraConstantsCodegenDetection,
    )
    from flext_infra._constants.codegen_lazy import FlextInfraConstantsCodegenLazy
    from flext_infra._constants.codegen_render_names import (
        FlextInfraConstantsCodegenRenderNames,
    )
    from flext_infra._constants.deps import FlextInfraConstantsDeps
    from flext_infra._constants.detectors import FlextInfraConstantsDetectors
    from flext_infra._constants.docs import FlextInfraConstantsDocs
    from flext_infra._constants.github import FlextInfraConstantsGithub
    from flext_infra._constants.make import FlextInfraConstantsMake
    from flext_infra._constants.namespace import FlextInfraConstantsNamespace
    from flext_infra._constants.refactor import FlextInfraConstantsRefactor
    from flext_infra._constants.release import FlextInfraConstantsRelease
    from flext_infra._constants.rope import FlextInfraConstantsRope
    from flext_infra._constants.source_code import FlextInfraConstantsSourceCode
    from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
    from flext_infra._constants.workspace import FlextInfraConstantsWorkspace
_LAZY_IMPORTS = build_lazy_import_map(
    {
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
