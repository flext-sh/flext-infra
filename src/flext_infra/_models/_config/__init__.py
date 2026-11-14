# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models. Config package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models._config.artifact import FlextInfraModelsConfigArtifact
    from flext_infra._models._config.base import FlextInfraModelsConfig
    from flext_infra._models._config.beads import FlextInfraModelsConfigBeads
    from flext_infra._models._config.contexts import FlextInfraModelsConfigContexts
    from flext_infra._models._config.contract import FlextInfraModelsConfigContract
    from flext_infra._models._config.external_cache import (
        FlextInfraExternalCacheDirectorySpec,
    )
    from flext_infra._models._config.make import FlextInfraModelsConfigMake
    from flext_infra._models._config.make_clean import FlextInfraModelsConfigMakeClean
    from flext_infra._models._config.make_docs import FlextInfraModelsConfigMakeDocs
    from flext_infra._models._config.provider import FlextInfraModelsConfigProvider
    from flext_infra._models._config.refactor_campaigns import (
        FlextInfraModelsConfigRefactorCampaigns,
    )
    from flext_infra._models._config.release import FlextInfraModelsConfigRelease
    from flext_infra._models._config.render import FlextInfraModelsConfigRender
    from flext_infra._models._config.repository import FlextInfraModelsConfigRepository
    from flext_infra._models._config.root import FlextInfraModelsConfigRoot
    from flext_infra._models._config.scaffold import FlextInfraModelsConfigScaffold
    from flext_infra._models._config.sonarcloud import FlextInfraModelsConfigSonarcloud
    from flext_infra._models._config.static import FlextInfraModelsConfigStatic
    from flext_infra._models._config.templates import FlextInfraModelsConfigTemplates
    from flext_infra._models._config.workspace import FlextInfraModelsConfigWorkspace


__all__: tuple[str, ...] = (
    "FlextInfraExternalCacheDirectorySpec",
    "FlextInfraModelsConfig",
    "FlextInfraModelsConfigArtifact",
    "FlextInfraModelsConfigBeads",
    "FlextInfraModelsConfigContexts",
    "FlextInfraModelsConfigContract",
    "FlextInfraModelsConfigMake",
    "FlextInfraModelsConfigMakeClean",
    "FlextInfraModelsConfigMakeDocs",
    "FlextInfraModelsConfigProvider",
    "FlextInfraModelsConfigRefactorCampaigns",
    "FlextInfraModelsConfigRelease",
    "FlextInfraModelsConfigRender",
    "FlextInfraModelsConfigRepository",
    "FlextInfraModelsConfigRoot",
    "FlextInfraModelsConfigScaffold",
    "FlextInfraModelsConfigSonarcloud",
    "FlextInfraModelsConfigStatic",
    "FlextInfraModelsConfigTemplates",
    "FlextInfraModelsConfigWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraExternalCacheDirectorySpec": ".external_cache",
        "FlextInfraModelsConfig": ".base",
        "FlextInfraModelsConfigArtifact": ".artifact",
        "FlextInfraModelsConfigBeads": ".beads",
        "FlextInfraModelsConfigContexts": ".contexts",
        "FlextInfraModelsConfigContract": ".contract",
        "FlextInfraModelsConfigMake": ".make",
        "FlextInfraModelsConfigMakeClean": ".make_clean",
        "FlextInfraModelsConfigMakeDocs": ".make_docs",
        "FlextInfraModelsConfigProvider": ".provider",
        "FlextInfraModelsConfigRefactorCampaigns": ".refactor_campaigns",
        "FlextInfraModelsConfigRelease": ".release",
        "FlextInfraModelsConfigRender": ".render",
        "FlextInfraModelsConfigRepository": ".repository",
        "FlextInfraModelsConfigRoot": ".root",
        "FlextInfraModelsConfigScaffold": ".scaffold",
        "FlextInfraModelsConfigSonarcloud": ".sonarcloud",
        "FlextInfraModelsConfigStatic": ".static",
        "FlextInfraModelsConfigTemplates": ".templates",
        "FlextInfraModelsConfigWorkspace": ".workspace",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraExternalCacheDirectorySpec": ("Directory",),
        "FlextInfraModelsConfig": (),
        "FlextInfraModelsConfigArtifact": (
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
        "FlextInfraModelsConfigBeads": (
            "BeadsProjectSpec",
            "BeadsConfigRenderSpec",
            "BeadsMetadataRenderSpec",
        ),
        "FlextInfraModelsConfigContexts": (
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
        "FlextInfraModelsConfigContract": (
            "ConfigContract",
            "DocsAuditOverridesSpec",
            "DocsAuditPolicySpec",
        ),
        "FlextInfraModelsConfigMake": (
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
            "MakeAdmissionOverrideSpec",
            "MakeAdmissionLimitsSpec",
            "MakeAdmissionSpec",
            "MakeVerbCatalogSpec",
            "MakeSpec",
            "CustomHandlerPolicy",
            "CustomHandlerPolicyOverride",
        ),
        "FlextInfraModelsConfigMakeClean": ("MakeCleanSpec",),
        "FlextInfraModelsConfigMakeDocs": (
            "DocsOverviewPreviewLimitsSpec",
            "DocsGithubRepoSpec",
            "MakeDocsSpec",
        ),
        "FlextInfraModelsConfigProvider": (
            "ProviderIdentitySpec",
            "RepositorySourceSpec",
            "BranchPolicySpec",
            "GithubActionPinSpec",
            "CiPrivateSubmoduleDeployKeySpec",
            "CiPrivateDependencyAuthSpec",
            "CiSuperprojectCheckoutSpec",
            "CiPrivateSubmodulesSpec",
        ),
        "FlextInfraModelsConfigRefactorCampaigns": (
            "RenameCampaignSpec",
            "ModOwnerSpec",
            "RefactorCsvCampaignsSpec",
        ),
        "FlextInfraModelsConfigRelease": (
            "ReleaseAutomationOverrideSpec",
            "ReleaseAutomationSpec",
            "ReleasePolicySpec",
            "BuildConstraintSpec",
            "UvEnvironmentPlan",
        ),
        "FlextInfraModelsConfigRender": ("SonarcloudSpec",),
        "FlextInfraModelsConfigRepository": (
            "validated_hatch_build_hook_path",
            "ProjectIdentitySpec",
            "ProjectSpec",
            "WorkspaceIntegrationSpec",
            "RepositoryRefIdentity",
            "RepositoryRef",
            "RepositoryConformTarget",
            "ConsoleScriptSpec",
            "ScriptDispatchSpec",
        ),
        "FlextInfraModelsConfigRoot": (
            "Infra",
            "Root",
        ),
        "FlextInfraModelsConfigScaffold": (
            "ScaffoldBuildSpec",
            "ScaffoldConfigBaseSpec",
            "ScaffoldProjectSpec",
            "ScaffoldPingExampleSpec",
            "ScaffoldGitignoreSectionSpec",
            "ScaffoldDependencyProfileSpec",
            "ScaffoldSpec",
        ),
        "FlextInfraModelsConfigSonarcloud": ("SonarcloudIssueExclusionSpec",),
        "FlextInfraModelsConfigStatic": (
            "RopePreferencesSpec",
            "SourceScanSpec",
            "RouteBudgetSpec",
            "GateRepeatWindow",
            "GateRepeatSpec",
            "ModEvidenceSpec",
            "GateAdmissionSpec",
            "ConsolidationOutcome",
        ),
        "FlextInfraModelsConfigTemplates": (
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
        "FlextInfraModelsConfigWorkspace": (
            "GitSubmoduleDeclaration",
            "RefactorConfigSpec",
            "DependencyCommitSourceSpec",
            "CandidateDependenciesSpec",
            "RepositoryDeltaAnalysisSpec",
            "RepositoryDeltaSpec",
            "CandidateBootstrapTargetSpec",
            "DependencyGroupInclude",
            "DependencyGroupEntries",
            "DependencyGroupDeclarations",
            "DependencyManifestSpec",
            "DependencyEdgeSpec",
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

defer_lazy_bases(
    __name__,
    {
        "FlextInfraModelsConfig": (
            (".", "FlextInfraModelsConfigContract"),
            (".", "FlextInfraExternalCacheDirectorySpec"),
            (".", "FlextInfraModelsConfigProvider"),
            (".", "FlextInfraModelsConfigRender"),
            (".", "FlextInfraModelsConfigRoot"),
            (".", "FlextInfraModelsConfigScaffold"),
            (".", "FlextInfraModelsConfigStatic"),
            (".", "FlextInfraModelsConfigMake"),
            (".", "FlextInfraModelsConfigBeads"),
            (".", "FlextInfraModelsConfigTemplates"),
            (".", "FlextInfraModelsConfigContexts"),
            (".", "FlextInfraModelsConfigWorkspace"),
            (".", "FlextInfraModelsConfigRelease"),
            (".", "FlextInfraModelsConfigArtifact"),
        ),
        "FlextInfraModelsConfigArtifact": (
            (".", "FlextInfraModelsConfigRefactorCampaigns"),
            ("flext_infra._models._codegen", "FlextInfraModelsCodegenTransaction"),
        ),
        "FlextInfraModelsConfigContexts": ((".", "FlextInfraModelsConfigRepository"),),
        "FlextInfraModelsConfigContract": (
            ("flext_infra._models", "FlextInfraModelsMiseToolchain"),
        ),
        "FlextInfraModelsConfigMake": (
            (".", "FlextInfraModelsConfigMakeClean"),
            (".", "FlextInfraModelsConfigMakeDocs"),
        ),
        "FlextInfraModelsConfigRender": ((".", "FlextInfraModelsConfigSonarcloud"),),
    },
)
