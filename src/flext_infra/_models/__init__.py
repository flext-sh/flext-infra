# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra. Models package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextInfraModelsBase",),
    ".census": ("FlextInfraModelsCensus",),
    ".check": ("FlextInfraModelsCheck",),
    ".codegen": ("FlextInfraModelsCodegen",),
    ".codegen_render": ("FlextInfraModelsCodegenRender",),
    ".config": ("FlextInfraConfigModels",),
    ".deps": ("FlextInfraModelsDeps",),
    ".deps_toml": ("FlextInfraModelsDepsToml",),
    ".deps_tool_config": ("FlextInfraModelsDepsToolSettings",),
    ".deps_tool_config_linters": ("FlextInfraModelsDepsToolConfigLinters",),
    ".deps_tool_config_type_checkers": ("FlextInfraModelsDepsToolConfigTypeCheckers",),
    ".docs": ("FlextInfraModelsDocs",),
    ".enforcement": ("FlextInfraModelsEnforcement",),
    ".gates": ("FlextInfraModelsGates",),
    ".github": ("FlextInfraModelsGithub",),
    ".layout": ("FlextInfraModelsLayout",),
    ".mixins": ("FlextInfraModelsMixins",),
    ".mro_scan": ("FlextInfraModelsMroScan",),
    ".refactor": ("FlextInfraModelsRefactor",),
    ".refactor_ast_grep": ("FlextInfraModelsRefactorGrep",),
    ".refactor_census": ("FlextInfraModelsRefactorCensus",),
    ".refactor_namespace_enforcer": ("FlextInfraModelsNamespaceEnforcer",),
    ".refactor_renames": ("FlextInfraModelsRefactorRenames",),
    ".refactor_violations": ("FlextInfraModelsRefactorViolations",),
    ".release": ("FlextInfraModelsRelease",),
    ".rope": ("FlextInfraModelsRope",),
    ".scan": ("FlextInfraModelsScan",),
    ".settings": ("FlextInfraSettingsModels",),
    ".transformers": ("FlextInfraModelsTransformers",),
    ".validate": ("FlextInfraModelsCore",),
    ".workspace": ("FlextInfraModelsWorkspace",),
    ".worktree": ("FlextInfraModelsWorktree",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
