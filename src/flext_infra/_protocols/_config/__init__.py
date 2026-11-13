# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols. Config package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols._config.artifact import (
        FlextInfraProtocolsConfigArtifact,
    )
    from flext_infra._protocols._config.beads import FlextInfraProtocolsConfigBeads
    from flext_infra._protocols._config.contexts import (
        FlextInfraProtocolsConfigContexts,
    )
    from flext_infra._protocols._config.contract import (
        FlextInfraProtocolsConfigContract,
    )
    from flext_infra._protocols._config.external_cache import (
        FlextInfraProtocolsConfigExternalCache,
    )
    from flext_infra._protocols._config.make import FlextInfraProtocolsConfigMake
    from flext_infra._protocols._config.make_clean import (
        FlextInfraProtocolsConfigMakeClean,
    )
    from flext_infra._protocols._config.make_docs import (
        FlextInfraProtocolsConfigMakeDocs,
    )
    from flext_infra._protocols._config.provider import (
        FlextInfraProtocolsConfigProvider,
    )
    from flext_infra._protocols._config.refactor_campaigns import (
        FlextInfraProtocolsConfigRefactorCampaigns,
    )
    from flext_infra._protocols._config.release import FlextInfraProtocolsConfigRelease
    from flext_infra._protocols._config.render import FlextInfraProtocolsConfigRender
    from flext_infra._protocols._config.repository import (
        FlextInfraProtocolsConfigRepository,
    )
    from flext_infra._protocols._config.root import FlextInfraProtocolsConfigRoot
    from flext_infra._protocols._config.scaffold import (
        FlextInfraProtocolsConfigScaffold,
    )
    from flext_infra._protocols._config.sonarcloud import (
        FlextInfraProtocolsConfigSonarcloud,
    )
    from flext_infra._protocols._config.static import FlextInfraProtocolsConfigStatic
    from flext_infra._protocols._config.templates import (
        FlextInfraProtocolsConfigTemplates,
    )
    from flext_infra._protocols._config.workspace import (
        FlextInfraProtocolsConfigWorkspace,
    )


__all__: tuple[str, ...] = (
    "FlextInfraProtocolsConfigArtifact",
    "FlextInfraProtocolsConfigBeads",
    "FlextInfraProtocolsConfigContexts",
    "FlextInfraProtocolsConfigContract",
    "FlextInfraProtocolsConfigExternalCache",
    "FlextInfraProtocolsConfigMake",
    "FlextInfraProtocolsConfigMakeClean",
    "FlextInfraProtocolsConfigMakeDocs",
    "FlextInfraProtocolsConfigProvider",
    "FlextInfraProtocolsConfigRefactorCampaigns",
    "FlextInfraProtocolsConfigRelease",
    "FlextInfraProtocolsConfigRender",
    "FlextInfraProtocolsConfigRepository",
    "FlextInfraProtocolsConfigRoot",
    "FlextInfraProtocolsConfigScaffold",
    "FlextInfraProtocolsConfigSonarcloud",
    "FlextInfraProtocolsConfigStatic",
    "FlextInfraProtocolsConfigTemplates",
    "FlextInfraProtocolsConfigWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraProtocolsConfigArtifact": ".artifact",
        "FlextInfraProtocolsConfigBeads": ".beads",
        "FlextInfraProtocolsConfigContexts": ".contexts",
        "FlextInfraProtocolsConfigContract": ".contract",
        "FlextInfraProtocolsConfigExternalCache": ".external_cache",
        "FlextInfraProtocolsConfigMake": ".make",
        "FlextInfraProtocolsConfigMakeClean": ".make_clean",
        "FlextInfraProtocolsConfigMakeDocs": ".make_docs",
        "FlextInfraProtocolsConfigProvider": ".provider",
        "FlextInfraProtocolsConfigRefactorCampaigns": ".refactor_campaigns",
        "FlextInfraProtocolsConfigRelease": ".release",
        "FlextInfraProtocolsConfigRender": ".render",
        "FlextInfraProtocolsConfigRepository": ".repository",
        "FlextInfraProtocolsConfigRoot": ".root",
        "FlextInfraProtocolsConfigScaffold": ".scaffold",
        "FlextInfraProtocolsConfigSonarcloud": ".sonarcloud",
        "FlextInfraProtocolsConfigStatic": ".static",
        "FlextInfraProtocolsConfigTemplates": ".templates",
        "FlextInfraProtocolsConfigWorkspace": ".workspace",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraProtocolsConfigArtifact": (
            "CodegenArtifactSpec",
            "DeclaredExclusionsSpec",
            "CodegenGovernedPlanRequest",
            "CodegenLocCapSpec",
            "CodegenAstGrepRendererSpec",
            "CodegenAstGrepSpec",
            "RetiredProjectionSpec",
            "CodegenModesSpec",
            "CodegenArtifactScopeSpec",
            "CodegenEngineSpec",
            "CodegenCiSpec",
            "CodegenWorkspaceSpec",
            "CodegenConfigSpec",
            "RepositoryDeclarationInputs",
            "CodegenInputs",
            "CodegenConformSurfaceContract",
            "CodegenGenerateRequest",
            "CodegenConformRequest",
            "ArtifactRenderRoute",
            "CodegenRenderInputs",
            "CodegenRepositoryPlanTask",
            "CodegenPlanningFileEvidence",
            "CodegenPlanningRepositoryEvidence",
            "CodegenPlanningReport",
        ),
        "FlextInfraProtocolsConfigBeads": (
            "BeadsProjectSpec",
            "BeadsConfigRenderSpec",
            "BeadsMetadataRenderSpec",
        ),
        "FlextInfraProtocolsConfigContexts": (
            "MakeCommandContext",
            "BootstrapRequirementsRenderSpec",
            "MakefileProjectRenderSpec",
            "MakefileToolchainRenderSpec",
            "MakefileRenderSpec",
            "MakeRenderContext",
            "ProjectRenderRuntimeContext",
            "ProjectRenderDependencyContext",
            "ProjectRenderPackageContext",
            "ProjectRenderContext",
            "ProfileSpec",
        ),
        "FlextInfraProtocolsConfigContract": (
            "ConfigContract",
            "DocsAuditOverridesSpec",
            "DocsAuditPolicySpec",
        ),
        "FlextInfraProtocolsConfigExternalCache": ("Directory",),
        "FlextInfraProtocolsConfigMake": (
            "MakeProjectCheckGateSpec",
            "RuffCacheSpec",
            "MakeCiSpec",
            "MakeVerbSpec",
            "MakeVerbGroupSpec",
            "MakeOperationSpec",
            "MakeLifecycleStepSpec",
            "MakeWorkflowRequirementSpec",
            "MakeWorkflowStepSpec",
            "TestmonCachePolicySpec",
            "MypyCacheSpec",
            "MakeRuffSpec",
            "MakeExecutionSpec",
            "MakeHarnessSpec",
            "MakeHarnessSpecTestmonCachePolicySpec",
            "MakeHarnessSpecTestmonCacheSpec",
            "MakeHarnessSpecExecutorEnvironmentSpec",
            "MakeAdmissionOverrideSpec",
            "MakeAdmissionLimitsSpec",
            "MakeAdmissionSpec",
            "MakeVerbCatalogSpec",
            "MakeSpec",
            "CustomHandlerPolicy",
            "CustomHandlerPolicyOverride",
        ),
        "FlextInfraProtocolsConfigMakeClean": ("MakeCleanSpec",),
        "FlextInfraProtocolsConfigMakeDocs": (
            "DocsOverviewPreviewLimitsSpec",
            "DocsGithubRepoSpec",
            "MakeDocsSpec",
        ),
        "FlextInfraProtocolsConfigProvider": (
            "ProviderIdentitySpec",
            "RepositorySourceSpec",
            "BranchPolicySpec",
            "GithubActionPinSpec",
            "CiPrivateSubmoduleDeployKeySpec",
            "CiPrivateDependencyAuthSpec",
            "CiSuperprojectCheckoutSpec",
            "CiPrivateSubmodulesSpec",
        ),
        "FlextInfraProtocolsConfigRefactorCampaigns": (
            "RenameCampaignSpec",
            "ModOwnerSpec",
            "RefactorCsvCampaignsSpec",
        ),
        "FlextInfraProtocolsConfigRelease": (
            "ReleaseAutomationOverrideSpec",
            "ReleaseAutomationSpec",
            "ReleasePolicySpec",
            "BuildConstraintSpec",
            "UvEnvironmentPlan",
        ),
        "FlextInfraProtocolsConfigRender": ("SonarcloudSpec",),
        "FlextInfraProtocolsConfigRepository": (
            "ProjectIdentitySpec",
            "ProjectSpec",
            "WorkspaceIntegrationSpec",
            "RepositoryRefIdentity",
            "RepositoryRef",
            "RepositoryConformTarget",
            "ConsoleScriptSpec",
            "ScriptDispatchSpec",
        ),
        "FlextInfraProtocolsConfigRoot": (
            "Infra",
            "Root",
        ),
        "FlextInfraProtocolsConfigScaffold": (
            "ScaffoldBuildSpec",
            "ScaffoldConfigBaseSpec",
            "ScaffoldProjectSpec",
            "ScaffoldPingExampleSpec",
            "ScaffoldGitignoreSectionSpec",
            "ScaffoldDependencyProfileSpec",
            "ScaffoldSpec",
        ),
        "FlextInfraProtocolsConfigSonarcloud": ("SonarcloudIssueExclusionSpec",),
        "FlextInfraProtocolsConfigStatic": (
            "RopePreferencesSpec",
            "SourceScanSpec",
            "MutationLockSpec",
            "RouteBudgetSpec",
            "GateRepeatWindow",
            "GateRepeatSpec",
            "GateAdmissionSpec",
            "ConsolidationOutcome",
        ),
        "FlextInfraProtocolsConfigTemplates": (
            "CodegenVscodeSpec",
            "CodegenVscodeDeclarationDelta",
            "CodegenLayerProjection",
            "ConfigDocumentInputs",
            "ManagedFileOwnership",
            "TemplateDeclarationSpec",
            "TemplateEntrySpec",
            "TemplatesSpec",
            "ManagedFileSpec",
            "GitignoreRenderContext",
            "GitignoreRenderSpec",
            "StaticTextRenderSpec",
        ),
        "FlextInfraProtocolsConfigWorkspace": (
            "GitSubmoduleDeclaration",
            "DependencyGroupInclude",
            "DependencyGroupDeclarations",
            "DependencyManifestSpec",
            "DependencyEdgeSpec",
            "RefactorConfigSpec",
            "DependencyCommitSourceSpec",
            "CandidateDependenciesSpec",
            "RepositoryDeltaAnalysisSpec",
            "RepositoryDeltaSpec",
            "CandidateBootstrapTargetSpec",
            "DependencyGroupEntries",
            "WorkspaceBeadsServerSpec",
            "RepositoryPolicyOverlaySpec",
            "WorkspaceExclusionSpec",
            "WorkspaceManifestSpec",
            "CodegenBootstrapSource",
            "HostWorkspaceInventoryEntry",
            "HostWorkspaceInventory",
            "ExternalConsumerSpec",
            "WorkspaceSpec",
        ),
    },
)
