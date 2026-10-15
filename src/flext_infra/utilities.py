"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities

from flext_infra._utilities._docs_audit_detectors import (
    FlextInfraUtilitiesDocsAuditDetectorsMixin,
)
from flext_infra._utilities._docs_command_contract import (
    FlextInfraUtilitiesDocsCommandContractMixin,
)
from flext_infra._utilities._docs_generate_plan import (
    FlextInfraUtilitiesDocsGeneratePlanMixin,
)
from flext_infra._utilities._docs_generate_project import (
    FlextInfraUtilitiesDocsGenerateProjectMixin,
)
from flext_infra._utilities._docs_generate_root import (
    FlextInfraUtilitiesDocsGenerateRootMixin,
)
from flext_infra._utilities._docs_generate_sources import (
    FlextInfraUtilitiesDocsGenerateSourcesMixin,
)
from flext_infra._utilities._docs_github_links import FlextInfraUtilitiesDocsGithubLinks
from flext_infra._utilities._docs_guides import FlextInfraUtilitiesDocsGuidesMixin
from flext_infra._utilities._docs_scope_build import (
    FlextInfraUtilitiesDocsScopeBuildMixin,
)
from flext_infra._utilities._docs_scope_paths import (
    FlextInfraUtilitiesDocsScopePathsMixin,
)
from flext_infra._utilities._docs_scope_policy import (
    FlextInfraUtilitiesDocsScopePolicyMixin,
)
from flext_infra._utilities._docs_scope_projects import (
    FlextInfraUtilitiesDocsScopeProjectsMixin,
)
from flext_infra._utilities._docs_scope_selection import (
    FlextInfraUtilitiesDocsScopeSelectionMixin,
)
from flext_infra._utilities._docs_scope_state import (
    FlextInfraUtilitiesDocsScopeStateMixin,
)
from flext_infra._utilities._git.remote import FlextInfraUtilitiesGitRemote
from flext_infra._utilities._git.worktree_io import FlextInfraUtilitiesGitWorktreeIO
from flext_infra._utilities._project_discovery_candidates import (
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
)
from flext_infra._utilities._project_discovery_shape import (
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
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
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope_source_bases_inventory import (
    FlextInfraUtilitiesRopeSourceBasesInventory,
)
from flext_infra._utilities._rope_source_bases_inventory_collector import (
    FlextInfraUtilitiesRopeSourceBindingCollector,
)
from flext_infra._utilities._rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
from flext_infra._utilities.codegen_facades import FlextInfraUtilitiesCodegenFacades
from flext_infra._utilities.codegen_file_plan import FlextInfraUtilitiesCodegenFilePlan
from flext_infra._utilities.codegen_path_cutover import (
    FlextInfraUtilitiesCodegenPathCutover,
)
from flext_infra._utilities.codemod_binding_chain import (
    FlextInfraFlextUtilitiesCodemodBindingChain,
)
from flext_infra._utilities.codemod_project import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities.codemod_rules import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities.compatibility_alias_validation import (
    FlextInfraUtilitiesCompatibilityAliasValidation,
)
from flext_infra._utilities.deferred_self_reference_rewrite import (
    FlextInfraUtilitiesDeferredSelfReferenceRewrite,
)
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.dependency_requirements import (
    FlextInfraUtilitiesDependencyRequirements,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit
from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild
from flext_infra._utilities.docs_collection import FlextInfraUtilitiesDocsCollection
from flext_infra._utilities.docs_collection_sources import (
    FlextInfraUtilitiesDocsCollectionSources,
)
from flext_infra._utilities.docs_collection_verify import (
    FlextInfraUtilitiesDocsCollectionVerify,
)
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix
from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities.gitignore import FlextInfraUtilitiesGitignore
from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra._utilities.iteration_directory import (
    FlextInfraUtilitiesIterationDirectory,
)
from flext_infra._utilities.iteration_matching import (
    FlextInfraUtilitiesIterationMatching,
)
from flext_infra._utilities.iteration_workspace import (
    FlextInfraUtilitiesIterationWorkspace,
)
from flext_infra._utilities.lint_recipes import FlextInfraUtilitiesLintRecipes
from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from flext_infra._utilities.managed_conflicts import FlextInfraUtilitiesManagedConflicts
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.namespace_analysis import (
    FlextInfraUtilitiesRefactorNamespaceFlext,
)
from flext_infra._utilities.namespace_common import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.namespace_moves import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra._utilities.network import FlextInfraUtilitiesNetwork
from flext_infra._utilities.private_import_ancestry import (
    FlextInfraUtilitiesPrivateImportAncestry,
)
from flext_infra._utilities.private_import_facades import (
    FlextInfraUtilitiesPrivateImportFacades,
)
from flext_infra._utilities.private_import_validation import (
    FlextInfraUtilitiesPrivateImportValidation,
)
from flext_infra._utilities.process import FlextInfraUtilitiesProcess
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities.promoted import FlextInfraUtilitiesPromoted
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
from flext_infra._utilities.pyproject_conform import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities.pyrefly import FlextInfraUtilitiesPyrefly
from flext_infra._utilities.qualified_names import FlextInfraUtilitiesQualifiedNames
from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
from flext_infra._utilities.release import FlextInfraUtilitiesRelease
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
from flext_infra._utilities.resource_limits import FlextInfraUtilitiesResourceLimits
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities.rope_class_move import FlextInfraUtilitiesRopeClassMove
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_inventory import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities.rope_module_patch import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities.rope_runtime_base import FlextInfraUtilitiesRopeRuntimeBase
from flext_infra._utilities.rope_runtime_module_queries import (
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
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
from flext_infra._utilities.rope_structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities.semantic_cutover import FlextInfraUtilitiesSemanticCutover
from flext_infra._utilities.transformer_header import (
    FlextInfraUtilitiesTransformerHeader,
)
from flext_infra._utilities.transformer_header_parser import (
    FlextInfraUtilitiesTransformerHeaderParser,
)
from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
from flext_infra._utilities.workspace_fingerprint import (
    FlextInfraUtilitiesWorkspaceFingerprint,
)
from flext_infra._utilities.workspace_inventory import (
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra._utilities.workspace_manifest import (
    FlextInfraUtilitiesWorkspaceManifest,
)
from flext_infra._utilities.worktree_lifecycle import FlextInfraWorktreeLifecycle
from flext_infra._utilities.worktree_provisioning import FlextInfraWorktreeProvisioning


class FlextInfraUtilities(FlextCliUtilities):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import m, u

        u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=Path(".")))
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(repository_root)
        u.Infra.parse_semver("1.2.3")
    """

    class Infra(
        FlextInfraUtilitiesDocsGithubLinks,
        FlextInfraUtilitiesRopeSourceBasesAliases,
        FlextInfraUtilitiesRopeSourceBasesInventory,
        FlextInfraUtilitiesRopeSourceBasesRuntime,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCodegenFacades,
        FlextInfraUtilitiesCodegenFilePlan,
        FlextInfraUtilitiesGitignore,
        FlextInfraUtilitiesCodegenPathCutover,
        FlextInfraFlextUtilitiesCodemodBindingChain,
        FlextInfraUtilitiesCodemodProject,
        FlextInfraUtilitiesCodemodRules,
        FlextInfraUtilitiesCompatibilityAliasValidation,
        FlextInfraUtilitiesDeferredSelfReferenceRewrite,
        FlextInfraUtilitiesDependencies,
        FlextInfraUtilitiesDependencyRequirements,
        FlextInfraUtilitiesDiscovery,
        FlextInfraUtilitiesNamespaceConfig,
        FlextInfraUtilitiesProjectDiscovery,
        FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
        FlextInfraUtilitiesProjectDiscoveryShapeMixin,
        FlextInfraUtilitiesPyproject,
        FlextInfraUtilitiesRopeAnalysis,
        FlextInfraUtilitiesDocs,
        FlextInfraUtilitiesDocsScopeBuildMixin,
        FlextInfraUtilitiesDocsScopeSelectionMixin,
        FlextInfraUtilitiesDocsApi,
        FlextInfraUtilitiesDocsAudit,
        FlextInfraUtilitiesDocsAuditDetectorsMixin,
        FlextInfraUtilitiesDocsCommandContractMixin,
        FlextInfraUtilitiesDocsBuild,
        FlextInfraUtilitiesDocsContract,
        FlextInfraUtilitiesDocsFix,
        FlextInfraUtilitiesDocsGenerate,
        FlextInfraUtilitiesDocsGenerateRootMixin,
        FlextInfraUtilitiesDocsGenerateProjectMixin,
        FlextInfraUtilitiesDocsGeneratePlanMixin,
        FlextInfraUtilitiesDocsGenerateSourcesMixin,
        FlextInfraUtilitiesDocsGuidesMixin,
        FlextInfraUtilitiesDocsCollection,
        FlextInfraUtilitiesDocsCollectionVerify,
        FlextInfraUtilitiesDocsCollectionSources,
        FlextInfraUtilitiesDocsRender,
        FlextInfraUtilitiesDocsScope,
        FlextInfraUtilitiesDocsScopeProjectsMixin,
        FlextInfraUtilitiesDocsScopePolicyMixin,
        FlextInfraUtilitiesDocsScopeStateMixin,
        FlextInfraUtilitiesDocsScopePathsMixin,
        FlextInfraUtilitiesDocsValidate,
        FlextInfraUtilitiesGit,
        FlextInfraUtilitiesImportLaw,
        FlextInfraUtilitiesIteration,
        FlextInfraUtilitiesIterationMatching,
        FlextInfraUtilitiesIterationWorkspace,
        FlextInfraUtilitiesIterationDirectory,
        FlextInfraUtilitiesLintRecipes,
        FlextInfraUtilitiesLogParser,
        FlextInfraUtilitiesManagedConflicts,
        FlextInfraUtilitiesCodegenNamespace,
        FlextInfraUtilitiesRefactorNamespaceFlext,
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceMoves,
        FlextInfraUtilitiesNetwork,
        FlextInfraUtilitiesPrivateImportAncestry,
        FlextInfraUtilitiesPrivateImportFacades,
        FlextInfraUtilitiesPrivateImportValidation,
        FlextInfraUtilitiesProcess,
        FlextInfraUtilitiesProjectManagedArtifacts,
        FlextInfraUtilitiesPromoted,
        FlextInfraUtilitiesProtectedEdit,
        FlextInfraUtilitiesProtectedEditWrites,
        FlextInfraUtilitiesProtectedEditApply,
        FlextInfraUtilitiesProtectedEditPreview,
        FlextInfraUtilitiesProtectedEditLinting,
        FlextInfraUtilitiesPyprojectConform,
        FlextInfraUtilitiesPyrefly,
        FlextInfraUtilitiesQualifiedNames,
        FlextInfraUtilitiesRefactor,
        FlextInfraUtilitiesRelease,
        FlextInfraUtilitiesRepository,
        FlextInfraUtilitiesResourceLimits,
        FlextInfraUtilitiesRopeAnalysisIntrospection,
        FlextInfraUtilitiesRopeAnalysisWorkspace,
        FlextInfraUtilitiesRopeClassMove,
        FlextInfraUtilitiesRopeCore,
        FlextInfraUtilitiesRopeCoreResourcesMixin,
        FlextInfraUtilitiesRopeCorePyModuleMixin,
        FlextInfraUtilitiesRopeHelpers,
        FlextInfraUtilitiesRopeMethodOrderMixin,
        FlextInfraUtilitiesRopeImports,
        FlextInfraUtilitiesRopeInventory,
        FlextInfraUtilitiesRopeModulePatch,
        FlextInfraUtilitiesRopeRuntime,
        FlextInfraUtilitiesRopeRuntimeModules,
        FlextInfraUtilitiesRopeRuntimeModuleQueries,
        FlextInfraUtilitiesRopeRuntimeRefactors,
        FlextInfraUtilitiesRopeRuntimeTypes,
        FlextInfraUtilitiesRopeRuntimeBase,
        FlextInfraUtilitiesRopeSource,
        FlextInfraUtilitiesRopeStructure,
        FlextInfraUtilitiesSemanticCutover,
        FlextInfraUtilitiesTransformerHeader,
        FlextInfraUtilitiesTransformerHeaderParser,
        FlextInfraUtilitiesVersioning,
        FlextInfraUtilitiesWorkspaceFingerprint,
        FlextInfraUtilitiesWorkspaceInventory,
        FlextInfraUtilitiesWorkspaceManifest,
        FlextInfraWorktreeLifecycle,
        FlextInfraWorktreeProvisioning,
        FlextInfraUtilitiesGitRemote,
        FlextInfraUtilitiesRopeSourceBindingCollector,
        FlextInfraUtilitiesGitWorktreeIO,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
