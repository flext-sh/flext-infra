# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _git as _git
    from . import _rope as _rope
    from ._docs_audit_detectors import FlextInfraUtilitiesDocsAuditDetectorsMixin
    from ._docs_github_links import FlextInfraUtilitiesDocsGithubLinks
    from ._docs_scope_build import FlextInfraUtilitiesDocsScopeBuildMixin
    from ._docs_scope_selection import FlextInfraUtilitiesDocsScopeSelectionMixin
    from ._git.repo import (
        FlextInfraUtilitiesGitRepo,
        git_open_repo,
        git_refresh_binary,
        git_repo,
    )
    from ._git.scope import FlextInfraUtilitiesGitScopeMixin
    from ._git.semantic import FlextInfraUtilitiesGitSemanticMixin
    from ._git.worktree import FlextInfraUtilitiesGitWorktreeMixin
    from ._github_pr_execution import FlextInfraUtilitiesGithubPrExecutionMixin
    from ._github_pr_single import FlextInfraUtilitiesGithubPrSingleMixin
    from ._github_sync import FlextInfraUtilitiesGithubSyncMixin
    from ._project_discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
    )
    from ._project_discovery_shape import FlextInfraUtilitiesProjectDiscoveryShapeMixin
    from ._rope.pep695_patch import FlextInfraUtilitiesRopePep695Patch
    from ._rope_bracket_balance import FlextInfraUtilitiesRopeBracketBalanceMixin
    from ._rope_core_pymodule import FlextInfraUtilitiesRopeCorePyModuleMixin
    from ._rope_core_resources import FlextInfraUtilitiesRopeCoreResourcesMixin
    from ._rope_method_order import FlextInfraUtilitiesRopeMethodOrderMixin
    from .base import FlextInfraUtilitiesBase
    from .beads_lane import FlextInfraUtilitiesBeadsLane
    from .census import FlextInfraUtilitiesRefactorCensus
    from .codegen import FlextInfraUtilitiesCodegen
    from .dependencies import FlextInfraUtilitiesDependencies
    from .discovery import FlextInfraUtilitiesDiscovery
    from .docs import FlextInfraUtilitiesDocs
    from .docs_api import FlextInfraUtilitiesDocsApi
    from .docs_audit import FlextInfraUtilitiesDocsAudit
    from .docs_build import FlextInfraUtilitiesDocsBuild
    from .docs_contract import FlextInfraUtilitiesDocsContract
    from .docs_fix import FlextInfraUtilitiesDocsFix
    from .docs_generate import FlextInfraUtilitiesDocsGenerate
    from .docs_render import FlextInfraUtilitiesDocsRender
    from .docs_scope import FlextInfraUtilitiesDocsScope
    from .docs_validate import FlextInfraUtilitiesDocsValidate
    from .git import FlextInfraUtilitiesGit
    from .github import FlextInfraUtilitiesGithub
    from .github_pr import FlextInfraUtilitiesGithubPr
    from .infra import FlextInfraUtilitiesInfra
    from .log_parser import FlextInfraUtilitiesLogParser
    from .mro_scan import FlextInfraUtilitiesRefactorMroScan
    from .mro_scan_catalog import FlextInfraUtilitiesMroScanCatalog
    from .mro_scan_source import FlextInfraUtilitiesMroScanSource
    from .namespace import FlextInfraUtilitiesCodegenNamespace
    from .namespace_analysis import FlextInfraUtilitiesRefactorNamespaceMro
    from .namespace_common import FlextInfraUtilitiesRefactorNamespaceCommon
    from .namespace_config import FlextInfraUtilitiesNamespaceConfig
    from .namespace_facades import FlextInfraUtilitiesRefactorNamespaceFacades
    from .namespace_moves import FlextInfraUtilitiesRefactorNamespaceMoves
    from .policy import FlextInfraUtilitiesRefactorPolicy
    from .process import FlextInfraUtilitiesProcess
    from .project_discovery import FlextInfraUtilitiesProjectDiscovery
    from .protected_edit import FlextInfraUtilitiesProtectedEdit
    from .protected_edit_apply import FlextInfraUtilitiesProtectedEditApply
    from .protected_edit_linting import FlextInfraUtilitiesProtectedEditLinting
    from .protected_edit_preview import FlextInfraUtilitiesProtectedEditPreview
    from .protected_edit_writes import FlextInfraUtilitiesProtectedEditWrites
    from .pyproject import FlextInfraUtilitiesPyproject
    from .pyproject_conform import FlextInfraUtilitiesPyprojectConform
    from .refactor import FlextInfraUtilitiesRefactor
    from .refactor_discovery import FlextInfraUtilitiesRefactorDiscovery
    from .release import FlextInfraUtilitiesRelease
    from .repository import FlextInfraUtilitiesRepository
    from .resource_limits import FlextInfraUtilitiesResourceLimits
    from .rope_analysis import FlextInfraUtilitiesRopeAnalysis
    from .rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from .rope_analysis_workspace import FlextInfraUtilitiesRopeAnalysisWorkspace
    from .rope_core import FlextInfraUtilitiesRopeCore
    from .rope_helpers import FlextInfraUtilitiesRopeHelpers
    from .rope_imports import FlextInfraUtilitiesRopeImports
    from .rope_inventory import FlextInfraUtilitiesRopeInventory
    from .rope_module_patch import FlextInfraUtilitiesRopeModulePatch
    from .rope_mro_transform import FlextInfraUtilitiesRopeMroTransform
    from .rope_runtime import FlextInfraUtilitiesRopeRuntime
    from .rope_runtime_base import FlextInfraUtilitiesRopeRuntimeBase
    from .rope_runtime_modules import FlextInfraUtilitiesRopeRuntimeModules
    from .rope_runtime_refactors import FlextInfraUtilitiesRopeRuntimeRefactors
    from .rope_runtime_types import FlextInfraUtilitiesRopeRuntimeTypes
    from .rope_source import FlextInfraUtilitiesRopeSource
    from .rope_structure import FlextInfraUtilitiesRopeStructure
    from .safety import FlextInfraUtilitiesSafety
    from .serialization_lock import FlextInfraUtilitiesSerializationLock
    from .silent_failure_ast import (
        collect_silent_failure_findings,
        collect_silent_failure_fixes,
    )
    from .snapshot import FlextInfraUtilitiesSnapshot
    from .versioning import FlextInfraUtilitiesVersioning
    from .work_saga_common import FlextInfraWorkSagaCommon
    from .work_saga_finish import FlextInfraWorkSagaFinish
    from .work_saga_publish import FlextInfraWorkSagaPublish
    from .work_saga_start import FlextInfraWorkSagaStart
    from .workspace_fingerprint import FlextInfraUtilitiesWorkspaceFingerprint
    from .worktree_transaction import FlextInfraUtilitiesWorktreeTransaction

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._docs_audit_detectors": ("FlextInfraUtilitiesDocsAuditDetectorsMixin",),
    "._docs_github_links": ("FlextInfraUtilitiesDocsGithubLinks",),
    "._docs_scope_build": ("FlextInfraUtilitiesDocsScopeBuildMixin",),
    "._docs_scope_selection": ("FlextInfraUtilitiesDocsScopeSelectionMixin",),
    "._git": ("_git",),
    "._git.repo": (
        "FlextInfraUtilitiesGitRepo",
        "git_open_repo",
        "git_refresh_binary",
        "git_repo",
    ),
    "._git.scope": ("FlextInfraUtilitiesGitScopeMixin",),
    "._git.semantic": ("FlextInfraUtilitiesGitSemanticMixin",),
    "._git.worktree": ("FlextInfraUtilitiesGitWorktreeMixin",),
    "._github_pr_execution": ("FlextInfraUtilitiesGithubPrExecutionMixin",),
    "._github_pr_single": ("FlextInfraUtilitiesGithubPrSingleMixin",),
    "._github_sync": ("FlextInfraUtilitiesGithubSyncMixin",),
    "._project_discovery_candidates": (
        "FlextInfraUtilitiesProjectDiscoveryCandidatesMixin",
    ),
    "._project_discovery_shape": ("FlextInfraUtilitiesProjectDiscoveryShapeMixin",),
    "._rope": ("_rope",),
    "._rope.pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
    "._rope_bracket_balance": ("FlextInfraUtilitiesRopeBracketBalanceMixin",),
    "._rope_core_pymodule": ("FlextInfraUtilitiesRopeCorePyModuleMixin",),
    "._rope_core_resources": ("FlextInfraUtilitiesRopeCoreResourcesMixin",),
    "._rope_method_order": ("FlextInfraUtilitiesRopeMethodOrderMixin",),
    ".base": ("FlextInfraUtilitiesBase",),
    ".beads_lane": ("FlextInfraUtilitiesBeadsLane",),
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
    ".git": ("FlextInfraUtilitiesGit",),
    ".github": ("FlextInfraUtilitiesGithub",),
    ".github_pr": ("FlextInfraUtilitiesGithubPr",),
    ".infra": ("FlextInfraUtilitiesInfra",),
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
    ".work_saga_common": ("FlextInfraWorkSagaCommon",),
    ".work_saga_finish": ("FlextInfraWorkSagaFinish",),
    ".work_saga_publish": ("FlextInfraWorkSagaPublish",),
    ".work_saga_start": ("FlextInfraWorkSagaStart",),
    ".workspace_fingerprint": ("FlextInfraUtilitiesWorkspaceFingerprint",),
    ".worktree_transaction": ("FlextInfraUtilitiesWorktreeTransaction",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesBeadsLane",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesDependencies",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectorsMixin",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsGithubLinks",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsScopeBuildMixin",
    "FlextInfraUtilitiesDocsScopeSelectionMixin",
    "FlextInfraUtilitiesDocsValidate",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGitRepo",
    "FlextInfraUtilitiesGitScopeMixin",
    "FlextInfraUtilitiesGitSemanticMixin",
    "FlextInfraUtilitiesGitWorktreeMixin",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesGithubPrExecutionMixin",
    "FlextInfraUtilitiesGithubPrSingleMixin",
    "FlextInfraUtilitiesGithubSyncMixin",
    "FlextInfraUtilitiesInfra",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesMroScanCatalog",
    "FlextInfraUtilitiesMroScanSource",
    "FlextInfraUtilitiesNamespaceConfig",
    "FlextInfraUtilitiesProcess",
    "FlextInfraUtilitiesProjectDiscovery",
    "FlextInfraUtilitiesProjectDiscoveryCandidatesMixin",
    "FlextInfraUtilitiesProjectDiscoveryShapeMixin",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesProtectedEditApply",
    "FlextInfraUtilitiesProtectedEditLinting",
    "FlextInfraUtilitiesProtectedEditPreview",
    "FlextInfraUtilitiesProtectedEditWrites",
    "FlextInfraUtilitiesPyproject",
    "FlextInfraUtilitiesPyprojectConform",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorDiscovery",
    "FlextInfraUtilitiesRefactorMroScan",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFacades",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRefactorNamespaceMro",
    "FlextInfraUtilitiesRefactorPolicy",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesRepository",
    "FlextInfraUtilitiesResourceLimits",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeAnalysisWorkspace",
    "FlextInfraUtilitiesRopeBracketBalanceMixin",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeCorePyModuleMixin",
    "FlextInfraUtilitiesRopeCoreResourcesMixin",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeMethodOrderMixin",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMroTransform",
    "FlextInfraUtilitiesRopePep695Patch",
    "FlextInfraUtilitiesRopeRuntime",
    "FlextInfraUtilitiesRopeRuntimeBase",
    "FlextInfraUtilitiesRopeRuntimeModules",
    "FlextInfraUtilitiesRopeRuntimeRefactors",
    "FlextInfraUtilitiesRopeRuntimeTypes",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRopeStructure",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesSerializationLock",
    "FlextInfraUtilitiesSnapshot",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesWorkspaceFingerprint",
    "FlextInfraUtilitiesWorktreeTransaction",
    "FlextInfraWorkSagaCommon",
    "FlextInfraWorkSagaFinish",
    "FlextInfraWorkSagaPublish",
    "FlextInfraWorkSagaStart",
    "_git",
    "_rope",
    "collect_silent_failure_findings",
    "collect_silent_failure_fixes",
    "git_open_repo",
    "git_refresh_binary",
    "git_repo",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
