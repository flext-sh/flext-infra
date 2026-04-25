# AUTO-GENERATED FILE — Regenerate with: make gen
"""Models package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraModelsBase",),
        ".basemk": ("FlextInfraModelsBasemk",),
        ".census": ("FlextInfraModelsCensus",),
        ".check": ("FlextInfraModelsCheck",),
        ".codegen": ("FlextInfraModelsCodegen",),
        ".deps": ("FlextInfraModelsDeps",),
        ".deps_tool_config": ("FlextInfraModelsDepsToolSettings",),
        ".deps_tool_config_linters": ("FlextInfraModelsDepsToolConfigLinters",),
        ".deps_tool_config_type_checkers": (
            "FlextInfraModelsDepsToolConfigTypeCheckers",
        ),
        ".docs": ("FlextInfraModelsDocs",),
        ".engine": ("FlextInfraModelsEngine",),
        ".engine_ops": ("FlextInfraModelsEngineOperation",),
        ".gates": ("FlextInfraModelsGates",),
        ".github": ("FlextInfraModelsGithub",),
        ".mixins": ("FlextInfraModelsMixins",),
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
