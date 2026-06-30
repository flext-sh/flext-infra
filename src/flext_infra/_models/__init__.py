# AUTO-GENERATED FILE — Regenerate with: make gen
"""Models package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models.base import FlextInfraModelsBase as FlextInfraModelsBase
    from flext_infra._models.basemk import (
        FlextInfraModelsBasemk as FlextInfraModelsBasemk,
    )
    from flext_infra._models.census import (
        FlextInfraModelsCensus as FlextInfraModelsCensus,
    )
    from flext_infra._models.check import FlextInfraModelsCheck as FlextInfraModelsCheck
    from flext_infra._models.codegen import (
        FlextInfraModelsCodegen as FlextInfraModelsCodegen,
    )
    from flext_infra._models.codegen_render import (
        FlextInfraModelsCodegenRender as FlextInfraModelsCodegenRender,
    )
    from flext_infra._models.deps import FlextInfraModelsDeps as FlextInfraModelsDeps
    from flext_infra._models.deps_toml import (
        FlextInfraModelsDepsToml as FlextInfraModelsDepsToml,
    )
    from flext_infra._models.deps_tool_config import (
        FlextInfraModelsDepsToolSettings as FlextInfraModelsDepsToolSettings,
    )
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraModelsDepsToolConfigLinters as FlextInfraModelsDepsToolConfigLinters,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers as FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs as FlextInfraModelsDocs
    from flext_infra._models.gates import FlextInfraModelsGates as FlextInfraModelsGates
    from flext_infra._models.github import (
        FlextInfraModelsGithub as FlextInfraModelsGithub,
    )
    from flext_infra._models.mixins import (
        FlextInfraModelsMixins as FlextInfraModelsMixins,
    )
    from flext_infra._models.mro_scan import (
        FlextInfraModelsMroScan as FlextInfraModelsMroScan,
    )
    from flext_infra._models.refactor import (
        FlextInfraModelsRefactor as FlextInfraModelsRefactor,
    )
    from flext_infra._models.refactor_ast_grep import (
        FlextInfraModelsRefactorGrep as FlextInfraModelsRefactorGrep,
    )
    from flext_infra._models.refactor_census import (
        FlextInfraModelsRefactorCensus as FlextInfraModelsRefactorCensus,
    )
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraModelsNamespaceEnforcer as FlextInfraModelsNamespaceEnforcer,
    )
    from flext_infra._models.refactor_violations import (
        FlextInfraModelsRefactorViolations as FlextInfraModelsRefactorViolations,
    )
    from flext_infra._models.release import (
        FlextInfraModelsRelease as FlextInfraModelsRelease,
    )
    from flext_infra._models.rope import FlextInfraModelsRope as FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan as FlextInfraModelsScan
    from flext_infra._models.validate import (
        FlextInfraModelsCore as FlextInfraModelsCore,
    )
    from flext_infra._models.workspace import (
        FlextInfraModelsWorkspace as FlextInfraModelsWorkspace,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraModelsBase",),
        ".basemk": ("FlextInfraModelsBasemk",),
        ".census": ("FlextInfraModelsCensus",),
        ".check": ("FlextInfraModelsCheck",),
        ".codegen": ("FlextInfraModelsCodegen",),
        ".codegen_render": ("FlextInfraModelsCodegenRender",),
        ".deps": ("FlextInfraModelsDeps",),
        ".deps_toml": ("FlextInfraModelsDepsToml",),
        ".deps_tool_config": ("FlextInfraModelsDepsToolSettings",),
        ".deps_tool_config_linters": ("FlextInfraModelsDepsToolConfigLinters",),
        ".deps_tool_config_type_checkers": (
            "FlextInfraModelsDepsToolConfigTypeCheckers",
        ),
        ".docs": ("FlextInfraModelsDocs",),
        ".gates": ("FlextInfraModelsGates",),
        ".github": ("FlextInfraModelsGithub",),
        ".mixins": ("FlextInfraModelsMixins",),
        ".mro_scan": ("FlextInfraModelsMroScan",),
        ".refactor": ("FlextInfraModelsRefactor",),
        ".refactor_ast_grep": ("FlextInfraModelsRefactorGrep",),
        ".refactor_census": ("FlextInfraModelsRefactorCensus",),
        ".refactor_namespace_enforcer": ("FlextInfraModelsNamespaceEnforcer",),
        ".refactor_violations": ("FlextInfraModelsRefactorViolations",),
        ".release": ("FlextInfraModelsRelease",),
        ".rope": ("FlextInfraModelsRope",),
        ".scan": ("FlextInfraModelsScan",),
        ".validate": ("FlextInfraModelsCore",),
        ".workspace": ("FlextInfraModelsWorkspace",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
