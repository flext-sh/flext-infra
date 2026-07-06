# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if TYPE_CHECKING:
    from flext_infra._utilities._constants._exports import (
        FLEXT_INFRA__UTILITIES_LAZY_IMPORTS,
    )
    from flext_infra._utilities._docs_audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectorsMixin,
    )
    from flext_infra._utilities._docs_scope_build import (
        FlextInfraUtilitiesDocsScopeBuildMixin,
    )
    from flext_infra._utilities._docs_scope_selection import (
        FlextInfraUtilitiesDocsScopeSelectionMixin,
    )
    from flext_infra._utilities._github_pr_single import (
        FlextInfraUtilitiesGithubPrSingleMixin,
    )
    from flext_infra._utilities._github_sync import FlextInfraUtilitiesGithubSyncMixin
    from flext_infra._utilities._project_discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
    )
    from flext_infra._utilities._project_discovery_shape import (
        FlextInfraUtilitiesProjectDiscoveryShapeMixin,
    )
    from flext_infra._utilities._rope_bracket_balance import (
        FlextInfraUtilitiesRopeBracketBalanceMixin,
    )
    from flext_infra._utilities._rope_core_pymodule import (
        FlextInfraUtilitiesRopeCorePyModuleMixin,
    )
    from flext_infra._utilities._rope_core_resources import (
        FlextInfraUtilitiesRopeCoreResourcesMixin,
    )
    from flext_infra._utilities._rope_method_order import (
        FlextInfraUtilitiesRopeMethodOrderMixin,
    )
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
    from flext_infra._utilities.deps_path_sync import (
        FlextInfraUtilitiesDependencyPathSync,
    )
    from flext_infra._utilities.deps_repos import FlextInfraInternalSyncRepoMixin
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
    from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
    from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit
    from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild
    from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
    from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix
    from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate
    from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
    from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
    from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate
    from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub
    from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.mro_scan import FlextInfraUtilitiesRefactorMroScan
    from flext_infra._utilities.mro_scan_catalog import (
        FlextInfraUtilitiesMroScanCatalog,
    )
    from flext_infra._utilities.mro_scan_source import FlextInfraUtilitiesMroScanSource
    from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceMro,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_config import (
        FlextInfraUtilitiesNamespaceConfig,
    )
    from flext_infra._utilities.namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.policy import FlextInfraUtilitiesRefactorPolicy
    from flext_infra._utilities.project_discovery import (
        FlextInfraUtilitiesProjectDiscovery,
    )
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
    from flext_infra._utilities.protected_edit_apply import (
        FlextInfraUtilitiesProtectedEditApply,
    )
    from flext_infra._utilities.protected_edit_linting import (
        FlextInfraUtilitiesProtectedEditLinting,
    )
    from flext_infra._utilities.protected_edit_preview import (
        FlextInfraUtilitiesProtectedEditPreview,
    )
    from flext_infra._utilities.protected_edit_writes import (
        FlextInfraUtilitiesProtectedEditWrites,
    )
    from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject
    from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
    from flext_infra._utilities.refactor_discovery import (
        FlextInfraUtilitiesRefactorDiscovery,
    )
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
    from flext_infra._utilities.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
    from flext_infra._utilities.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities.rope_mro_transform import (
        FlextInfraUtilitiesRopeMroTransform,
    )
    from flext_infra._utilities.rope_pep695_patch import (
        FlextInfraUtilitiesRopePep695Patch,
    )
    from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime
    from flext_infra._utilities.rope_runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities.rope_runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities.rope_runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities.rope_runtime_types import (
        FlextInfraUtilitiesRopeRuntimeTypes,
    )
    from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.silent_failure_ast import (
        collect_silent_failure_findings,
        collect_silent_failure_fixes,
    )
    from flext_infra._utilities.snapshot import FlextInfraUtilitiesSnapshot
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
_LAZY_IMPORTS = merge_lazy_imports(
    ("._constants",),
    build_lazy_import_map(
        {
            "._constants": ("_constants",),
            "._constants._exports": ("FLEXT_INFRA__UTILITIES_LAZY_IMPORTS",),
            "._docs_audit_detectors": ("FlextInfraUtilitiesDocsAuditDetectorsMixin",),
            "._docs_scope_build": ("FlextInfraUtilitiesDocsScopeBuildMixin",),
            "._docs_scope_selection": ("FlextInfraUtilitiesDocsScopeSelectionMixin",),
            "._github_pr_single": ("FlextInfraUtilitiesGithubPrSingleMixin",),
            "._github_sync": ("FlextInfraUtilitiesGithubSyncMixin",),
            "._project_discovery_candidates": (
                "FlextInfraUtilitiesProjectDiscoveryCandidatesMixin",
            ),
            "._project_discovery_shape": (
                "FlextInfraUtilitiesProjectDiscoveryShapeMixin",
            ),
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
            ".refactor_discovery": ("FlextInfraUtilitiesRefactorDiscovery",),
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
            ".rope_runtime": ("FlextInfraUtilitiesRopeRuntime",),
            ".rope_runtime_base": ("FlextInfraUtilitiesRopeRuntimeBase",),
            ".rope_runtime_modules": ("FlextInfraUtilitiesRopeRuntimeModules",),
            ".rope_runtime_refactors": ("FlextInfraUtilitiesRopeRuntimeRefactors",),
            ".rope_runtime_types": ("FlextInfraUtilitiesRopeRuntimeTypes",),
            ".rope_source": ("FlextInfraUtilitiesRopeSource",),
            ".safety": ("FlextInfraUtilitiesSafety",),
            ".silent_failure_ast": (
                "collect_silent_failure_findings",
                "collect_silent_failure_fixes",
            ),
            ".snapshot": ("FlextInfraUtilitiesSnapshot",),
            ".versioning": ("FlextInfraUtilitiesVersioning",),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name=__name__,
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
