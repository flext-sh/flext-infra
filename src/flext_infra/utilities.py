# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliUtilities

from flext_infra._utilities import (
    FlextInfraUtilitiesGitRemote,
    FlextInfraUtilitiesGitWorktreeIO,
    )
from flext_infra._utilities import FlextInfraUtilitiesBase
from flext_infra._utilities import FlextInfraUtilitiesCodegen
from flext_infra._utilities import FlextInfraUtilitiesCodegenFacades
from flext_infra._utilities import FlextInfraUtilitiesCodegenFilePlan
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenPathCutover,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodBindingChain,
)
from flext_infra._utilities import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities import (
    FlextInfraUtilitiesCompatibilityAliasValidation,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDeferredSelfReferenceRewrite,
)
from flext_infra._utilities import FlextInfraUtilitiesDependencies
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencyRequirements,
)
from flext_infra._utilities import FlextInfraUtilitiesDiscovery
from flext_infra._utilities import FlextInfraUtilitiesDocs
from flext_infra._utilities import FlextInfraUtilitiesDocsApi
from flext_infra._utilities import FlextInfraUtilitiesDocsAudit
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsAuditDetectorsMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesDocsBuild
from flext_infra._utilities import FlextInfraUtilitiesDocsCollection
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsCollectionSources,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsCollectionVerify,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsCommandContractMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesDocsContract
from flext_infra._utilities import FlextInfraUtilitiesDocsFix
from flext_infra._utilities import FlextInfraUtilitiesDocsGenerate
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsGeneratePlanMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsGenerateProjectMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsGenerateRootMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsGenerateSourcesMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesDocsGithubLinks
from flext_infra._utilities import FlextInfraUtilitiesDocsGuidesMixin
from flext_infra._utilities import FlextInfraUtilitiesDocsRender
from flext_infra._utilities import FlextInfraUtilitiesDocsScope
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopeBuildMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopePathsMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopePolicyMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopeProjectsMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopeSelectionMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopeStateMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesDocsValidate
from flext_infra._utilities import FlextInfraUtilitiesGit
from flext_infra._utilities import FlextInfraUtilitiesGitignore
from flext_infra._utilities import FlextInfraUtilitiesImportLaw
from flext_infra._utilities import FlextInfraUtilitiesIteration
from flext_infra._utilities import (
    FlextInfraUtilitiesIterationDirectory,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesIterationMatching,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesIterationWorkspace,
)
from flext_infra._utilities import FlextInfraUtilitiesLintRecipes
from flext_infra._utilities import FlextInfraUtilitiesLogParser
from flext_infra._utilities import FlextInfraUtilitiesManagedConflicts
from flext_infra._utilities import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities import FlextInfraUtilitiesNetwork
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportAncestry,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportFacades,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportValidation,
)
from flext_infra._utilities import FlextInfraUtilitiesProcess
from flext_infra._utilities import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities import FlextInfraUtilitiesPromoted
from flext_infra._utilities import FlextInfraUtilitiesProtectedEdit
from flext_infra._utilities import (
    FlextInfraUtilitiesProtectedEditApply,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesProtectedEditLinting,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesProtectedEditPreview,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesProtectedEditWrites,
)
from flext_infra._utilities import FlextInfraUtilitiesPyproject
from flext_infra._utilities import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities import FlextInfraUtilitiesPyrefly
from flext_infra._utilities import FlextInfraUtilitiesQualifiedNames
from flext_infra._utilities import FlextInfraUtilitiesRefactor
from flext_infra._utilities import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities import (
    FlextInfraUtilitiesRefactorNamespaceCommon,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRefactorNamespaceFlext,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra._utilities import FlextInfraUtilitiesRelease
from flext_infra._utilities import FlextInfraUtilitiesRepository
from flext_infra._utilities import FlextInfraUtilitiesResourceLimits
from flext_infra._utilities import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities import FlextInfraUtilitiesRopeClassMove
from flext_infra._utilities import FlextInfraUtilitiesRopeCore
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCorePyModuleMixin,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCoreResourcesMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesRopeHelpers
from flext_infra._utilities import FlextInfraUtilitiesRopeImports
from flext_infra._utilities import FlextInfraUtilitiesRopeInventory
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeMethodOrderMixin,
)
from flext_infra._utilities import FlextInfraUtilitiesRopeModulePatch
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntimeBase
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities import FlextInfraUtilitiesRopeSource
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeSourceBasesInventory,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities import FlextInfraUtilitiesSemanticCutover
from flext_infra._utilities import (
    FlextInfraUtilitiesTransformerHeader,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesTransformerHeaderParser,
)
from flext_infra._utilities import FlextInfraUtilitiesVersioning
from flext_infra._utilities import (
    FlextInfraUtilitiesWorkspaceFingerprint,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesWorkspaceManifest,
)
from flext_infra._utilities import FlextInfraWorktreeLifecycle
from flext_infra._utilities import FlextInfraWorktreeProvisioning
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeSourceBindingCollector,
)


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
        FlextInfraUtilitiesRopeSourceBindingCollector,
        FlextInfraUtilitiesRopeSourceBasesRuntime,
        FlextInfraUtilitiesBase,
        FlextInfraUtilitiesRefactorCensus,
        FlextInfraUtilitiesCodegen,
        FlextInfraUtilitiesCodegenFacades,
        FlextInfraUtilitiesCodegenFilePlan,
        FlextInfraUtilitiesGitignore,
        FlextInfraUtilitiesCodegenPathCutover,
        FlextInfraUtilitiesCodemodBindingChain,
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
        FlextInfraUtilitiesGitWorktreeIO,
    ):
        """Infrastructure-domain utilities - all methods exposed directly."""


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
