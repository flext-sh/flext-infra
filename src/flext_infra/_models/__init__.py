# AUTO-GENERATED FILE — Regenerate with: make gen
"""Models package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models.base import FlextInfraModelsBase
    from flext_infra._models.basemk import FlextInfraModelsBasemk
    from flext_infra._models.census import FlextInfraModelsCensus
    from flext_infra._models.check import FlextInfraModelsCheck
    from flext_infra._models.codegen import FlextInfraModelsCodegen
    from flext_infra._models.codegen_render import FlextInfraModelsCodegenRender
    from flext_infra._models.deps import FlextInfraModelsDeps
    from flext_infra._models.deps_toml import FlextInfraModelsDepsToml
    from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolSettings
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraModelsDepsToolConfigLinters,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs
    from flext_infra._models.gates import FlextInfraModelsGates
    from flext_infra._models.github import FlextInfraModelsGithub
    from flext_infra._models.mixins import FlextInfraModelsMixins
    from flext_infra._models.mro_scan import FlextInfraModelsMroScan
    from flext_infra._models.refactor import FlextInfraModelsRefactor
    from flext_infra._models.refactor_ast_grep import FlextInfraModelsRefactorGrep
    from flext_infra._models.refactor_census import FlextInfraModelsRefactorCensus
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraModelsNamespaceEnforcer,
    )
    from flext_infra._models.refactor_violations import (
        FlextInfraModelsRefactorViolations,
    )
    from flext_infra._models.release import FlextInfraModelsRelease
    from flext_infra._models.rope import FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan
    from flext_infra._models.validate import FlextInfraModelsCore
    from flext_infra._models.workspace import FlextInfraModelsWorkspace
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
