# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra. Utilities package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._docs_audit_detectors": ("FlextInfraUtilitiesDocsAuditDetectorsMixin",),
    "._docs_scope_build": ("FlextInfraUtilitiesDocsScopeBuildMixin",),
    "._docs_scope_selection": ("FlextInfraUtilitiesDocsScopeSelectionMixin",),
    "._git_worktree": ("FlextInfraUtilitiesGitWorktreeMixin",),
    "._github_pr_execution": ("FlextInfraUtilitiesGithubPrExecutionMixin",),
    "._github_pr_single": ("FlextInfraUtilitiesGithubPrSingleMixin",),
    "._github_sync": ("FlextInfraUtilitiesGithubSyncMixin",),
    "._project_discovery_candidates": (
        "FlextInfraUtilitiesProjectDiscoveryCandidatesMixin",
    ),
    "._project_discovery_shape": ("FlextInfraUtilitiesProjectDiscoveryShapeMixin",),
    "._rope_bracket_balance": ("FlextInfraUtilitiesRopeBracketBalanceMixin",),
    "._rope_core_pymodule": ("FlextInfraUtilitiesRopeCorePyModuleMixin",),
    "._rope_core_resources": ("FlextInfraUtilitiesRopeCoreResourcesMixin",),
    "._rope_method_order": ("FlextInfraUtilitiesRopeMethodOrderMixin",),
    ".base": ("FlextInfraUtilitiesBase",),
    ".census": ("FlextInfraUtilitiesRefactorCensus",),
    ".codegen": ("FlextInfraUtilitiesCodegen",),
    ".dependencies": ("FlextInfraUtilitiesDependencies",),
    ".discovery": ("FlextInfraUtilitiesDiscovery",),
    ".docs": ("FlextInfraUtilitiesDocs",),
    ".docs_api": ("FlextInfraUtilitiesDocsApi",),
    ".docs_audit": ("FlextInfraUtilitiesDocsAudit",),
    ".docs_build": ("FlextInfraUtilitiesDocsBuild",),
    ".docs_contract": ("FlextInfraUtilitiesDocsContract",),
    ".docs_fix": ("FlextInfraUtilitiesDocsFix",),
    ".docs_generate": ("FlextInfraUtilitiesDocsGenerate",),
    ".docs_render": ("FlextInfraUtilitiesDocsRender",),
    ".docs_scope": ("FlextInfraUtilitiesDocsScope",),
    ".docs_validate": ("FlextInfraUtilitiesDocsValidate",),
    ".git_scope": ("FlextInfraUtilitiesGitScope",),
    ".github": ("FlextInfraUtilitiesGithub",),
    ".github_pr": ("FlextInfraUtilitiesGithubPr",),
    ".log_parser": ("FlextInfraUtilitiesLogParser",),
    ".mro_scan": ("FlextInfraUtilitiesRefactorMroScan",),
    ".mro_scan_catalog": ("FlextInfraUtilitiesMroScanCatalog",),
    ".mro_scan_source": ("FlextInfraUtilitiesMroScanSource",),
    ".namespace": ("FlextInfraUtilitiesCodegenNamespace",),
    ".namespace_analysis": ("FlextInfraUtilitiesRefactorNamespaceMro",),
    ".namespace_common": ("FlextInfraUtilitiesRefactorNamespaceCommon",),
    ".namespace_config": ("FlextInfraUtilitiesNamespaceConfig",),
    ".namespace_facades": ("FlextInfraUtilitiesRefactorNamespaceFacades",),
    ".namespace_moves": ("FlextInfraUtilitiesRefactorNamespaceMoves",),
    ".policy": ("FlextInfraUtilitiesRefactorPolicy",),
    ".process": ("FlextInfraUtilitiesProcess",),
    ".project_discovery": ("FlextInfraUtilitiesProjectDiscovery",),
    ".protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
    ".protected_edit_apply": ("FlextInfraUtilitiesProtectedEditApply",),
    ".protected_edit_linting": ("FlextInfraUtilitiesProtectedEditLinting",),
    ".protected_edit_preview": ("FlextInfraUtilitiesProtectedEditPreview",),
    ".protected_edit_writes": ("FlextInfraUtilitiesProtectedEditWrites",),
    ".pyproject": ("FlextInfraUtilitiesPyproject",),
    ".pyproject_conform": ("FlextInfraUtilitiesPyprojectConform",),
    ".refactor": ("FlextInfraUtilitiesRefactor",),
    ".refactor_discovery": ("FlextInfraUtilitiesRefactorDiscovery",),
    ".release": ("FlextInfraUtilitiesRelease",),
    ".repository": ("FlextInfraUtilitiesRepository",),
    ".resource_limits": ("FlextInfraUtilitiesResourceLimits",),
    ".rope_analysis": ("FlextInfraUtilitiesRopeAnalysis",),
    ".rope_analysis_introspection": ("FlextInfraUtilitiesRopeAnalysisIntrospection",),
    ".rope_analysis_workspace": ("FlextInfraUtilitiesRopeAnalysisWorkspace",),
    ".rope_core": ("FlextInfraUtilitiesRopeCore",),
    ".rope_helpers": ("FlextInfraUtilitiesRopeHelpers",),
    ".rope_imports": ("FlextInfraUtilitiesRopeImports",),
    ".rope_inventory": ("FlextInfraUtilitiesRopeInventory",),
    ".rope_module_patch": ("FlextInfraUtilitiesRopeModulePatch",),
    ".rope_mro_transform": ("FlextInfraUtilitiesRopeMroTransform",),
    ".rope_patch": ("rope_patch",),
    ".rope_patch.pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
    ".rope_runtime": ("FlextInfraUtilitiesRopeRuntime",),
    ".rope_runtime_base": ("FlextInfraUtilitiesRopeRuntimeBase",),
    ".rope_runtime_modules": ("FlextInfraUtilitiesRopeRuntimeModules",),
    ".rope_runtime_refactors": ("FlextInfraUtilitiesRopeRuntimeRefactors",),
    ".rope_runtime_types": ("FlextInfraUtilitiesRopeRuntimeTypes",),
    ".rope_source": ("FlextInfraUtilitiesRopeSource",),
    ".rope_structure": ("FlextInfraUtilitiesRopeStructure",),
    ".safety": ("FlextInfraUtilitiesSafety",),
    ".serialization_lock": ("FlextInfraUtilitiesSerializationLock",),
    ".silent_failure_ast": (
        "collect_silent_failure_findings",
        "collect_silent_failure_fixes",
    ),
    ".snapshot": ("FlextInfraUtilitiesSnapshot",),
    ".versioning": ("FlextInfraUtilitiesVersioning",),
    ".workspace_fingerprint": ("FlextInfraUtilitiesWorkspaceFingerprint",),
    ".worktree_transaction": ("FlextInfraUtilitiesWorktreeTransaction",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
