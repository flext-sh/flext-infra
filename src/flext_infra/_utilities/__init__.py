# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra._utilities._docs_audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectorsMixin as FlextInfraUtilitiesDocsAuditDetectorsMixin,
    )
    from flext_infra._utilities._docs_scope_build import (
        FlextInfraUtilitiesDocsScopeBuildMixin as FlextInfraUtilitiesDocsScopeBuildMixin,
    )
    from flext_infra._utilities._docs_scope_selection import (
        FlextInfraUtilitiesDocsScopeSelectionMixin as FlextInfraUtilitiesDocsScopeSelectionMixin,
    )
    from flext_infra._utilities._github_pr_single import (
        FlextInfraUtilitiesGithubPrSingleMixin as FlextInfraUtilitiesGithubPrSingleMixin,
    )
    from flext_infra._utilities._github_sync import (
        FlextInfraUtilitiesGithubSyncMixin as FlextInfraUtilitiesGithubSyncMixin,
    )
    from flext_infra._utilities._rope_bracket_balance import (
        FlextInfraUtilitiesRopeBracketBalanceMixin as FlextInfraUtilitiesRopeBracketBalanceMixin,
    )
    from flext_infra._utilities._rope_core_pymodule import (
        FlextInfraUtilitiesRopeCorePyModuleMixin as FlextInfraUtilitiesRopeCorePyModuleMixin,
    )
    from flext_infra._utilities._rope_core_resources import (
        FlextInfraUtilitiesRopeCoreResourcesMixin as FlextInfraUtilitiesRopeCoreResourcesMixin,
    )
    from flext_infra._utilities._rope_method_order import (
        FlextInfraUtilitiesRopeMethodOrderMixin as FlextInfraUtilitiesRopeMethodOrderMixin,
    )
    from flext_infra._utilities.base import (
        FlextInfraUtilitiesBase as FlextInfraUtilitiesBase,
    )
    from flext_infra._utilities.census import (
        FlextInfraUtilitiesRefactorCensus as FlextInfraUtilitiesRefactorCensus,
    )
    from flext_infra._utilities.codegen import (
        FlextInfraUtilitiesCodegen as FlextInfraUtilitiesCodegen,
    )
    from flext_infra._utilities.dependencies import (
        FlextInfraUtilitiesDependencies as FlextInfraUtilitiesDependencies,
    )
    from flext_infra._utilities.deps_path_sync import (
        FlextInfraUtilitiesDependencyPathSync as FlextInfraUtilitiesDependencyPathSync,
    )
    from flext_infra._utilities.deps_repos import (
        FlextInfraInternalSyncRepoMixin as FlextInfraInternalSyncRepoMixin,
    )
    from flext_infra._utilities.discovery import (
        FlextInfraUtilitiesDiscovery as FlextInfraUtilitiesDiscovery,
    )
    from flext_infra._utilities.docs import (
        FlextInfraUtilitiesDocs as FlextInfraUtilitiesDocs,
    )
    from flext_infra._utilities.docs_api import (
        FlextInfraUtilitiesDocsApi as FlextInfraUtilitiesDocsApi,
    )
    from flext_infra._utilities.docs_audit import (
        FlextInfraUtilitiesDocsAudit as FlextInfraUtilitiesDocsAudit,
    )
    from flext_infra._utilities.docs_build import (
        FlextInfraUtilitiesDocsBuild as FlextInfraUtilitiesDocsBuild,
    )
    from flext_infra._utilities.docs_contract import (
        FlextInfraUtilitiesDocsContract as FlextInfraUtilitiesDocsContract,
    )
    from flext_infra._utilities.docs_fix import (
        FlextInfraUtilitiesDocsFix as FlextInfraUtilitiesDocsFix,
    )
    from flext_infra._utilities.docs_generate import (
        FlextInfraUtilitiesDocsGenerate as FlextInfraUtilitiesDocsGenerate,
    )
    from flext_infra._utilities.docs_render import (
        FlextInfraUtilitiesDocsRender as FlextInfraUtilitiesDocsRender,
    )
    from flext_infra._utilities.docs_scope import (
        FlextInfraUtilitiesDocsScope as FlextInfraUtilitiesDocsScope,
    )
    from flext_infra._utilities.docs_validate import (
        FlextInfraUtilitiesDocsValidate as FlextInfraUtilitiesDocsValidate,
    )
    from flext_infra._utilities.engine import (
        FlextInfraUtilitiesRefactorEngine as FlextInfraUtilitiesRefactorEngine,
    )
    from flext_infra._utilities.git_scope import (
        FlextInfraUtilitiesGitScope as FlextInfraUtilitiesGitScope,
    )
    from flext_infra._utilities.github import (
        FlextInfraUtilitiesGithub as FlextInfraUtilitiesGithub,
    )
    from flext_infra._utilities.github_pr import (
        FlextInfraUtilitiesGithubPr as FlextInfraUtilitiesGithubPr,
    )
    from flext_infra._utilities.log_parser import (
        FlextInfraUtilitiesLogParser as FlextInfraUtilitiesLogParser,
    )
    from flext_infra._utilities.mro_scan import (
        FlextInfraUtilitiesRefactorMroScan as FlextInfraUtilitiesRefactorMroScan,
    )
    from flext_infra._utilities.mro_scan_catalog import (
        FlextInfraUtilitiesMroScanCatalog as FlextInfraUtilitiesMroScanCatalog,
    )
    from flext_infra._utilities.mro_scan_source import (
        FlextInfraUtilitiesMroScanSource as FlextInfraUtilitiesMroScanSource,
    )
    from flext_infra._utilities.namespace import (
        FlextInfraUtilitiesCodegenNamespace as FlextInfraUtilitiesCodegenNamespace,
    )
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceMro as FlextInfraUtilitiesRefactorNamespaceMro,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon as FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_config import (
        FlextInfraUtilitiesNamespaceConfig as FlextInfraUtilitiesNamespaceConfig,
    )
    from flext_infra._utilities.namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades as FlextInfraUtilitiesRefactorNamespaceFacades,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves as FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.policy import (
        FlextInfraUtilitiesRefactorPolicy as FlextInfraUtilitiesRefactorPolicy,
    )
    from flext_infra._utilities.project_discovery import (
        FlextInfraUtilitiesProjectDiscovery as FlextInfraUtilitiesProjectDiscovery,
    )
    from flext_infra._utilities.protected_edit import (
        FlextInfraUtilitiesProtectedEdit as FlextInfraUtilitiesProtectedEdit,
    )
    from flext_infra._utilities.protected_edit_apply import (
        FlextInfraUtilitiesProtectedEditApply as FlextInfraUtilitiesProtectedEditApply,
    )
    from flext_infra._utilities.protected_edit_linting import (
        FlextInfraUtilitiesProtectedEditLinting as FlextInfraUtilitiesProtectedEditLinting,
    )
    from flext_infra._utilities.protected_edit_preview import (
        FlextInfraUtilitiesProtectedEditPreview as FlextInfraUtilitiesProtectedEditPreview,
    )
    from flext_infra._utilities.protected_edit_writes import (
        FlextInfraUtilitiesProtectedEditWrites as FlextInfraUtilitiesProtectedEditWrites,
    )
    from flext_infra._utilities.pyproject import (
        FlextInfraUtilitiesPyproject as FlextInfraUtilitiesPyproject,
    )
    from flext_infra._utilities.refactor import (
        FlextInfraUtilitiesRefactor as FlextInfraUtilitiesRefactor,
    )
    from flext_infra._utilities.release import (
        FlextInfraUtilitiesRelease as FlextInfraUtilitiesRelease,
    )
    from flext_infra._utilities.rope_analysis import (
        FlextInfraUtilitiesRopeAnalysis as FlextInfraUtilitiesRopeAnalysis,
    )
    from flext_infra._utilities.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection as FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace as FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities.rope_core import (
        FlextInfraUtilitiesRopeCore as FlextInfraUtilitiesRopeCore,
    )
    from flext_infra._utilities.rope_helpers import (
        FlextInfraUtilitiesRopeHelpers as FlextInfraUtilitiesRopeHelpers,
    )
    from flext_infra._utilities.rope_imports import (
        FlextInfraUtilitiesRopeImports as FlextInfraUtilitiesRopeImports,
    )
    from flext_infra._utilities.rope_inventory import (
        FlextInfraUtilitiesRopeInventory as FlextInfraUtilitiesRopeInventory,
    )
    from flext_infra._utilities.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch as FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities.rope_mro_transform import (
        FlextInfraUtilitiesRopeMroTransform as FlextInfraUtilitiesRopeMroTransform,
    )
    from flext_infra._utilities.rope_pep695_patch import (
        FlextInfraUtilitiesRopePep695Patch as FlextInfraUtilitiesRopePep695Patch,
    )
    from flext_infra._utilities.rope_source import (
        FlextInfraUtilitiesRopeSource as FlextInfraUtilitiesRopeSource,
    )
    from flext_infra._utilities.safety import (
        FlextInfraUtilitiesSafety as FlextInfraUtilitiesSafety,
    )
    from flext_infra._utilities.snapshot import (
        FlextInfraUtilitiesSnapshot as FlextInfraUtilitiesSnapshot,
    )
    from flext_infra._utilities.versioning import (
        FlextInfraUtilitiesVersioning as FlextInfraUtilitiesVersioning,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._docs_audit_detectors": ("FlextInfraUtilitiesDocsAuditDetectorsMixin",),
        "._docs_scope_build": ("FlextInfraUtilitiesDocsScopeBuildMixin",),
        "._docs_scope_selection": ("FlextInfraUtilitiesDocsScopeSelectionMixin",),
        "._github_pr_single": ("FlextInfraUtilitiesGithubPrSingleMixin",),
        "._github_sync": ("FlextInfraUtilitiesGithubSyncMixin",),
        "._rope_bracket_balance": ("FlextInfraUtilitiesRopeBracketBalanceMixin",),
        "._rope_core_pymodule": ("FlextInfraUtilitiesRopeCorePyModuleMixin",),
        "._rope_core_resources": ("FlextInfraUtilitiesRopeCoreResourcesMixin",),
        "._rope_method_order": ("FlextInfraUtilitiesRopeMethodOrderMixin",),
        ".base": ("FlextInfraUtilitiesBase",),
        ".census": ("FlextInfraUtilitiesRefactorCensus",),
        ".codegen": ("FlextInfraUtilitiesCodegen",),
        ".dependencies": ("FlextInfraUtilitiesDependencies",),
        ".deps_path_sync": ("FlextInfraUtilitiesDependencyPathSync",),
        ".deps_repos": ("FlextInfraInternalSyncRepoMixin",),
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
        ".engine": ("FlextInfraUtilitiesRefactorEngine",),
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
        ".project_discovery": ("FlextInfraUtilitiesProjectDiscovery",),
        ".protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
        ".protected_edit_apply": ("FlextInfraUtilitiesProtectedEditApply",),
        ".protected_edit_linting": ("FlextInfraUtilitiesProtectedEditLinting",),
        ".protected_edit_preview": ("FlextInfraUtilitiesProtectedEditPreview",),
        ".protected_edit_writes": ("FlextInfraUtilitiesProtectedEditWrites",),
        ".pyproject": ("FlextInfraUtilitiesPyproject",),
        ".refactor": ("FlextInfraUtilitiesRefactor",),
        ".release": ("FlextInfraUtilitiesRelease",),
        ".rope_analysis": ("FlextInfraUtilitiesRopeAnalysis",),
        ".rope_analysis_introspection": (
            "FlextInfraUtilitiesRopeAnalysisIntrospection",
        ),
        ".rope_analysis_workspace": ("FlextInfraUtilitiesRopeAnalysisWorkspace",),
        ".rope_core": ("FlextInfraUtilitiesRopeCore",),
        ".rope_helpers": ("FlextInfraUtilitiesRopeHelpers",),
        ".rope_imports": ("FlextInfraUtilitiesRopeImports",),
        ".rope_inventory": ("FlextInfraUtilitiesRopeInventory",),
        ".rope_module_patch": ("FlextInfraUtilitiesRopeModulePatch",),
        ".rope_mro_transform": ("FlextInfraUtilitiesRopeMroTransform",),
        ".rope_pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
        ".rope_source": ("FlextInfraUtilitiesRopeSource",),
        ".safety": ("FlextInfraUtilitiesSafety",),
        ".snapshot": ("FlextInfraUtilitiesSnapshot",),
        ".versioning": ("FlextInfraUtilitiesVersioning",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
