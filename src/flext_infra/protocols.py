# AUTO-GENERATED FILE - Source bootstrap protocol facade.
"""Structural contracts projected from source model declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliProtocols

from flext_infra._protocols.base import FlextInfraProtocolsBase
from flext_infra._protocols.census import FlextInfraProtocolsCensus
from flext_infra._protocols.check import FlextInfraProtocolsCheck
from flext_infra._protocols.codegen import FlextInfraProtocolsCodegen
from flext_infra._protocols.codegen_render import FlextInfraProtocolsCodegenRender
from flext_infra._protocols.codegen_toolchain import FlextInfraProtocolsCodegenToolchain
from flext_infra._protocols.codemod import FlextInfraProtocolsCodemod
from flext_infra._protocols.config import FlextInfraProtocolsConfig
from flext_infra._protocols.deps import FlextInfraProtocolsDeps
from flext_infra._protocols.deps_toml import FlextInfraProtocolsDepsToml
from flext_infra._protocols.deps_tool_config import FlextInfraProtocolsDepsToolConfig
from flext_infra._protocols.deps_tool_config_linters import (
    FlextInfraProtocolsDepsToolConfigLinters,
)
from flext_infra._protocols.deps_tool_config_project import (
    FlextInfraProtocolsDepsToolConfigProject,
)
from flext_infra._protocols.deps_tool_config_project_artifacts import (
    FlextInfraProtocolsDepsToolConfigProjectArtifacts,
)
from flext_infra._protocols.deps_tool_config_project_gitignore import (
    FlextInfraProtocolsDepsToolConfigProjectGitignore,
)
from flext_infra._protocols.deps_tool_config_project_mise import (
    FlextInfraProtocolsDepsToolConfigProjectMise,
)
from flext_infra._protocols.deps_tool_config_type_checkers import (
    FlextInfraProtocolsDepsToolConfigTypeCheckers,
)
from flext_infra._protocols.docs import FlextInfraProtocolsDocs
from flext_infra._protocols.docs_collection import FlextInfraProtocolsDocsCollection
from flext_infra._protocols.docs_generation import FlextInfraProtocolsDocsGeneration
from flext_infra._protocols.duplication import FlextInfraProtocolsDuplication
from flext_infra._protocols.enforcement_catalog import (
    FlextInfraProtocolsEnforcementCatalog,
)
from flext_infra._protocols.gates import FlextInfraProtocolsGates
from flext_infra._protocols.git import FlextInfraProtocolsGit
from flext_infra._protocols.git_lane_inputs import FlextInfraProtocolsGitLaneInputs
from flext_infra._protocols.git_lane_ownership import (
    FlextInfraProtocolsGitLaneOwnership,
)
from flext_infra._protocols.layout import FlextInfraProtocolsLayout
from flext_infra._protocols.mise_toolchain import FlextInfraProtocolsMiseToolchain
from flext_infra._protocols.mise_toolchain_base import (
    FlextInfraProtocolsMiseToolchainBase,
)
from flext_infra._protocols.mise_toolchain_repair import (
    FlextInfraProtocolsMiseToolchainRepair,
)
from flext_infra._protocols.mixins import FlextInfraProtocolsMixins
from flext_infra._protocols.promoted import FlextInfraProtocolsPromoted
from flext_infra._protocols.refactor import FlextInfraProtocolsRefactor
from flext_infra._protocols.refactor_ast_grep import FlextInfraProtocolsRefactorAstGrep
from flext_infra._protocols.refactor_namespace_enforcer import (
    FlextInfraProtocolsRefactorNamespaceEnforcer,
)
from flext_infra._protocols.release import FlextInfraProtocolsRelease
from flext_infra._protocols.rope import FlextInfraProtocolsRope
from flext_infra._protocols.rope_move import FlextInfraProtocolsRopeMove
from flext_infra._protocols.rope_runtime import FlextInfraProtocolsRopeRuntime
from flext_infra._protocols.scan import FlextInfraProtocolsScan
from flext_infra._protocols.settings import FlextInfraProtocolsSettings
from flext_infra._protocols.sonarcloud import FlextInfraProtocolsSonarcloud
from flext_infra._protocols.testmon import FlextInfraProtocolsTestmon
from flext_infra._protocols.transformers import FlextInfraProtocolsTransformers
from flext_infra._protocols.validate import FlextInfraProtocolsValidate
from flext_infra._protocols.workspace import FlextInfraProtocolsWorkspace
from flext_infra._protocols.workspace_snapshot import (
    FlextInfraProtocolsWorkspaceSnapshot,
)
from flext_infra._protocols.worktree import FlextInfraProtocolsWorktree


class FlextInfraProtocols(FlextCliProtocols):
    """Structural contracts for flext-infra."""

    class Infra(
        FlextInfraProtocolsBase,
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsCodegen,
        FlextInfraProtocolsCodemod,
        FlextInfraProtocolsConfig,
        FlextInfraProtocolsDeps,
        FlextInfraProtocolsDepsToml,
        FlextInfraProtocolsDepsToolConfig,
        FlextInfraProtocolsDepsToolConfigLinters,
        FlextInfraProtocolsDepsToolConfigProject,
        FlextInfraProtocolsDepsToolConfigProjectArtifacts,
        FlextInfraProtocolsDepsToolConfigProjectGitignore,
        FlextInfraProtocolsDepsToolConfigProjectMise,
        FlextInfraProtocolsDepsToolConfigTypeCheckers,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsDocsCollection,
        FlextInfraProtocolsDocsGeneration,
        FlextInfraProtocolsDuplication,
        FlextInfraProtocolsEnforcementCatalog,
        FlextInfraProtocolsGates,
        FlextInfraProtocolsGit,
        FlextInfraProtocolsGitLaneInputs,
        FlextInfraProtocolsLayout,
        FlextInfraProtocolsMiseToolchain,
        FlextInfraProtocolsMiseToolchainBase,
        FlextInfraProtocolsMiseToolchainRepair,
        FlextInfraProtocolsMixins,
        FlextInfraProtocolsPromoted,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsRefactorAstGrep,
        FlextInfraProtocolsRefactorNamespaceEnforcer,
        FlextInfraProtocolsRelease,
        FlextInfraProtocolsRope,
        FlextInfraProtocolsRopeMove,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsScan,
        FlextInfraProtocolsSettings,
        FlextInfraProtocolsSonarcloud,
        FlextInfraProtocolsTestmon,
        FlextInfraProtocolsTransformers,
        FlextInfraProtocolsValidate,
        FlextInfraProtocolsWorkspace,
        FlextInfraProtocolsWorktree,
    ):
        """Aggregate source-derived protocol contracts."""

        AbsoluteFilePathTextMixin = FlextInfraProtocolsMixins.AbsoluteFilePathTextMixin
        AccessorMigrationChange = (
            FlextInfraProtocolsRefactorAstGrep.AccessorMigrationChange
        )
        AccessorMigrationFile = FlextInfraProtocolsRefactorAstGrep.AccessorMigrationFile
        AccessorMigrationInput = FlextInfraProtocolsRefactor.AccessorMigrationInput
        AccessorMigrationReport = (
            FlextInfraProtocolsRefactorAstGrep.AccessorMigrationReport
        )
        AccessorMigrationRule = FlextInfraProtocolsRefactorAstGrep.AccessorMigrationRule
        AccessorPolicyConfig = FlextInfraProtocolsDepsToolConfig.AccessorPolicyConfig
        AliasMigrationContext = FlextInfraProtocolsTransformers.AliasMigrationContext
        ApplyRenamesReport = FlextInfraProtocolsRefactor.ApplyRenamesReport
        ArtifactExpectation = FlextInfraProtocolsRelease.ArtifactExpectation
        AstGrepCapture = FlextInfraProtocolsCodemod.AstGrepCapture
        AstGrepDiagnostic = FlextInfraProtocolsCodemod.AstGrepDiagnostic
        AstGrepOwnedPathDiagnostic = (
            FlextInfraProtocolsCodemod.AstGrepOwnedPathDiagnostic
        )
        AstGrepReport = FlextInfraProtocolsCodemod.AstGrepReport
        AuditIssue = FlextInfraProtocolsDocs.AuditIssue
        AuditScopeParams = FlextInfraProtocolsDocs.AuditScopeParams
        BanditFinding = FlextInfraProtocolsCheck.BanditFinding
        BanditReport = FlextInfraProtocolsCheck.BanditReport
        BanditScanError = FlextInfraProtocolsCheck.BanditScanError
        BeadsEndpointSpec = FlextInfraProtocolsMiseToolchain.BeadsEndpointSpec
        BeadsProjectSpec = FlextInfraProtocolsBase.BeadsProjectSpec
        BuildArtifact = FlextInfraProtocolsRelease.BuildArtifact
        BuildPolicy = FlextInfraProtocolsRelease.BuildPolicy
        BuildRecord = FlextInfraProtocolsRelease.BuildRecord
        BuildReport = FlextInfraProtocolsRelease.BuildReport
        CandidateBootstrapPlanner = FlextInfraProtocolsBase.CandidateBootstrapPlanner
        CensusInput = FlextInfraProtocolsRefactor.CensusInput
        CensusObjectRules = FlextInfraProtocolsBase.CensusObjectRules
        CensusOptions = FlextInfraProtocolsRefactor.CensusOptions
        ChainDeclarationSpec = FlextInfraProtocolsBase.ChainDeclarationSpec
        ChangeTracker = FlextInfraProtocolsRope.ChangeTracker
        CheckProjectTarget = FlextInfraProtocolsCheck.CheckProjectTarget
        CheckReportSummary = FlextInfraProtocolsCheck.CheckReportSummary
        Checker = FlextInfraProtocolsBase.Checker
        ClassBlockLayout = FlextInfraProtocolsTransformers.ClassBlockLayout
        ClassInfo = FlextInfraProtocolsRope.ClassInfo
        ClassMoveRequest = FlextInfraProtocolsRopeMove.ClassMoveRequest
        CodegenCensusService = FlextInfraProtocolsBase.CodegenCensusService
        CodegenConformPorts = FlextInfraProtocolsBase.CodegenConformPorts
        CodegenConformRequest = FlextInfraProtocolsBase.CodegenConformRequest
        CodegenExecutionContext = FlextInfraProtocolsBase.CodegenExecutionContext
        CodegenFileOutcome = FlextInfraProtocolsBase.CodegenFileOutcome
        CodegenFileParticipant = (
            FlextInfraProtocolsCodegenToolchain.CodegenFileParticipant
        )
        CodegenFilePublisher = FlextInfraProtocolsBase.CodegenFilePublisher
        CodegenFixer = FlextInfraProtocolsBase.CodegenFixer
        CodegenGenerateRequest = FlextInfraProtocolsBase.CodegenGenerateRequest
        CodegenInputs = FlextInfraProtocolsBase.CodegenInputs
        CodegenPlanOutcome = FlextInfraProtocolsBase.CodegenPlanOutcome
        CodegenResult = FlextInfraProtocolsBase.CodegenResult
        CodegenService = FlextInfraProtocolsBase.CodegenService
        CodegenSourceAuthority = FlextInfraProtocolsWorkspace.CodegenSourceAuthority
        CodemodBindingSnapshot = FlextInfraProtocolsCodemod.CodemodBindingSnapshot
        CodemodNativeGenerated = (
            FlextInfraProtocolsRefactorAstGrep.CodemodNativeGenerated
        )
        CodemodPackageExportsFacts = (
            FlextInfraProtocolsRefactorAstGrep.CodemodPackageExportsFacts
        )
        CodemodPrimitiveOwner = FlextInfraProtocolsRefactorAstGrep.CodemodPrimitiveOwner
        CodemodScopeFacts = FlextInfraProtocolsRefactorAstGrep.CodemodScopeFacts
        CodemodScopePartition = FlextInfraProtocolsRefactorAstGrep.CodemodScopePartition
        CommandContext = FlextInfraProtocolsBase.CommandContext
        CommandPayloadContext = FlextInfraProtocolsBase.CommandPayloadContext
        CompatibilityAliasRewritePlan = (
            FlextInfraProtocolsTransformers.CompatibilityAliasRewritePlan
        )
        ConsolidatorScannedFile = FlextInfraProtocolsRope.ConsolidatorScannedFile
        ConstantInfo = FlextInfraProtocolsRope.ConstantInfo
        ContractAdmissionOptions = FlextInfraProtocolsCodemod.ContractAdmissionOptions
        CurrentImportMixin = FlextInfraProtocolsMixins.CurrentImportMixin
        DeclarationRelocationFinding = (
            FlextInfraProtocolsTransformers.DeclarationRelocationFinding
        )
        DependencyMarkerEnvironment = (
            FlextInfraProtocolsDeps.DependencyMarkerEnvironment
        )
        DepsService = FlextInfraProtocolsBase.DepsService
        DeptryDiagnostic = FlextInfraProtocolsGates.DeptryDiagnostic
        DeptryError = FlextInfraProtocolsGates.DeptryError
        DeptryIssueGroups = FlextInfraProtocolsDeps.DeptryIssueGroups
        DeptryLocation = FlextInfraProtocolsGates.DeptryLocation
        DeptryNativeReport = FlextInfraProtocolsGates.DeptryNativeReport
        DeptryReport = FlextInfraProtocolsDeps.DeptryReport
        DeptryScan = FlextInfraProtocolsGates.DeptryScan
        DetectCommand = FlextInfraProtocolsDeps.DetectCommand
        DetectorRuntime = FlextInfraProtocolsBase.DetectorRuntime
        DiagResult = FlextInfraProtocolsValidate.DiagResult
        DiagnosticPathException = (
            FlextInfraProtocolsDepsToolConfigTypeCheckers.DiagnosticPathException
        )
        DiagnosticRuleChange = (
            FlextInfraProtocolsDepsToolConfigLinters.DiagnosticRuleChange
        )
        DirectUrlDirectoryInfo = FlextInfraProtocolsWorkspace.DirectUrlDirectoryInfo
        DirectUrlReceipt = FlextInfraProtocolsWorkspace.DirectUrlReceipt
        DirectUrlVcsInfo = FlextInfraProtocolsWorkspace.DirectUrlVcsInfo
        Discovery = FlextInfraProtocolsBase.Discovery
        DistroDockerRenderSpec = FlextInfraProtocolsCodegenRender.DistroDockerRenderSpec
        DocScope = FlextInfraProtocolsDocsGeneration.DocScope
        DocsApiReadmeContext = FlextInfraProtocolsDocs.DocsApiReadmeContext
        DocsArtifactPlanner = FlextInfraProtocolsBase.DocsArtifactPlanner
        DocsArtifactPlannerFactory = FlextInfraProtocolsBase.DocsArtifactPlannerFactory
        DocsCatalogEntry = FlextInfraProtocolsDocsGeneration.DocsCatalogEntry
        DocsClassCount = FlextInfraProtocolsDocs.DocsClassCount
        DocsCollectRequest = FlextInfraProtocolsDocs.DocsCollectRequest
        DocsDependencyReference = (
            FlextInfraProtocolsDocsGeneration.DocsDependencyReference
        )
        DocsDirectivePageContext = FlextInfraProtocolsDocs.DocsDirectivePageContext
        DocsExportBinding = FlextInfraProtocolsDocs.DocsExportBinding
        DocsGenerateRequest = FlextInfraProtocolsDocs.DocsGenerateRequest
        DocsGenerationBundle = FlextInfraProtocolsDocsGeneration.DocsGenerationBundle
        DocsGovernanceLinks = FlextInfraProtocolsDocs.DocsGovernanceLinks
        DocsGuideEntry = FlextInfraProtocolsDocs.DocsGuideEntry
        DocsGuidesIndexContext = FlextInfraProtocolsDocs.DocsGuidesIndexContext
        DocsLlmsContext = FlextInfraProtocolsDocsGeneration.DocsLlmsContext
        DocsModuleEntry = FlextInfraProtocolsDocs.DocsModuleEntry
        DocsModulesIndexContext = FlextInfraProtocolsDocs.DocsModulesIndexContext
        DocsOverviewContext = FlextInfraProtocolsDocs.DocsOverviewContext
        DocsPageContext = FlextInfraProtocolsDocs.DocsPageContext
        DocsPhaseItemModel = FlextInfraProtocolsDocs.DocsPhaseItemModel
        DocsPhaseReport = FlextInfraProtocolsDocs.DocsPhaseReport
        DocsPhaseReports = FlextInfraProtocolsDocs.DocsPhaseReports
        DocsProjectCatalogContext = FlextInfraProtocolsDocs.DocsProjectCatalogContext
        DocsProjectIndexContext = FlextInfraProtocolsDocs.DocsProjectIndexContext
        DocsProjectIndexEntry = FlextInfraProtocolsDocs.DocsProjectIndexEntry
        DocsProjectReadmeContext = FlextInfraProtocolsDocs.DocsProjectReadmeContext
        DocsPublicContract = FlextInfraProtocolsDocs.DocsPublicContract
        DocsRenderedArtifact = FlextInfraProtocolsDocsGeneration.DocsRenderedArtifact
        DocsRenderedToc = FlextInfraProtocolsDocs.DocsRenderedToc
        DocsRepositoryRef = FlextInfraProtocolsDocs.DocsRepositoryRef
        DocsRootInputs = FlextInfraProtocolsDocsGeneration.DocsRootInputs
        DocsRootOverviewContext = FlextInfraProtocolsDocs.DocsRootOverviewContext
        DocsRootProjectsIndexContext = (
            FlextInfraProtocolsDocs.DocsRootProjectsIndexContext
        )
        DocsScopeArtifacts = FlextInfraProtocolsDocsGeneration.DocsScopeArtifacts
        DocsTocToken = FlextInfraProtocolsDocs.DocsTocToken
        DocstringCoverage = FlextInfraProtocolsDocs.DocstringCoverage
        DuplicateCopyCure = FlextInfraProtocolsCensus.DuplicateCopyCure
        DuplicateCureEdit = FlextInfraProtocolsCensus.DuplicateCureEdit
        DuplicateCureOutcome = FlextInfraProtocolsCensus.DuplicateCureOutcome
        DuplicateCurePlan = FlextInfraProtocolsCensus.DuplicateCurePlan
        DuplicateDefinition = FlextInfraProtocolsCensus.DuplicateDefinition
        DuplicateDeletion = FlextInfraProtocolsCensus.DuplicateDeletion
        DuplicateGroup = FlextInfraProtocolsCensus.DuplicateGroup
        DuplicateGroupCure = FlextInfraProtocolsCensus.DuplicateGroupCure
        DuplicationAssessment = FlextInfraProtocolsDuplication.DuplicationAssessment
        DuplicationCandidateEvidence = (
            FlextInfraProtocolsDuplication.DuplicationCandidateEvidence
        )
        DuplicationClassification = (
            FlextInfraProtocolsDuplication.DuplicationClassification
        )
        DuplicationSpanMeasure = FlextInfraProtocolsDuplication.DuplicationSpanMeasure
        EditableDirectUrl = FlextInfraProtocolsWorkspace.EditableDirectUrl
        EnforcementCatalog = FlextInfraProtocolsEnforcementCatalog.EnforcementCatalog
        EnforcementClaim = FlextInfraProtocolsEnforcementCatalog.EnforcementClaim
        EnvironmentContractViolation = (
            FlextInfraProtocolsWorkspace.EnvironmentContractViolation
        )
        EnvrcRenderSpec = FlextInfraProtocolsCodegenRender.EnvrcRenderSpec
        ErrorDetailMixin = FlextInfraProtocolsMixins.ErrorDetailMixin
        ExportOptions = FlextInfraProtocolsRope.ExportOptions
        ExternalCacheDirectory = FlextInfraProtocolsBase.ExternalCacheDirectory
        FacadeCensus = FlextInfraProtocolsRope.FacadeCensus
        FacadeMembersConfig = FlextInfraProtocolsDepsToolConfig.FacadeMembersConfig
        FacadeNamespaceCutover = FlextInfraProtocolsTransformers.FacadeNamespaceCutover
        FacadeNamespaceSite = FlextInfraProtocolsTransformers.FacadeNamespaceSite
        FamilyFlattenRule = FlextInfraProtocolsCodemod.FamilyFlattenRule
        FamilyWrapperFlatten = FlextInfraProtocolsRope.FamilyWrapperFlatten
        FileImportData = FlextInfraProtocolsRefactor.FileImportData
        FileLineViolationMixin = FlextInfraProtocolsMixins.FileLineViolationMixin
        FilePathMixin = FlextInfraProtocolsMixins.FilePathMixin
        FixPyreflyConfigCommand = FlextInfraProtocolsCheck.FixPyreflyConfigCommand
        FleetGapsReport = FlextInfraProtocolsWorkspace.FleetGapsReport
        FleetPullRequest = FlextInfraProtocolsWorkspace.FleetPullRequest
        FleetRepoGaps = FlextInfraProtocolsWorkspace.FleetRepoGaps
        FlextEditableRequest = FlextInfraProtocolsWorkspace.FlextEditableRequest
        FlextEditableSelection = FlextInfraProtocolsWorkspace.FlextEditableSelection
        FreshImportEntryPoints = FlextInfraProtocolsValidate.FreshImportEntryPoints
        FreshImportMetadata = FlextInfraProtocolsValidate.FreshImportMetadata
        FreshImportProbe = FlextInfraProtocolsValidate.FreshImportProbe
        FrozenArbitrary = FlextInfraProtocolsBase.FrozenArbitrary
        FunctionDescriptor = FlextInfraProtocolsBase.FunctionDescriptor
        GateAttestationCreateRequest = (
            FlextInfraProtocolsGates.GateAttestationCreateRequest
        )
        GateAttestationPredicate = FlextInfraProtocolsGates.GateAttestationPredicate
        GateAttestationReport = FlextInfraProtocolsGates.GateAttestationReport
        GateAttestationRuntimeContext = (
            FlextInfraProtocolsBase.GateAttestationRuntimeContext
        )
        GateAttestationVerifyRequest = (
            FlextInfraProtocolsGates.GateAttestationVerifyRequest
        )
        GateCaptureBeginRequest = FlextInfraProtocolsGates.GateCaptureBeginRequest
        GateCaptureFinishRequest = FlextInfraProtocolsGates.GateCaptureFinishRequest
        GateCaptureReport = FlextInfraProtocolsGates.GateCaptureReport
        GateCaptureRequest = FlextInfraProtocolsGates.GateCaptureRequest
        GateCaptureStart = FlextInfraProtocolsGates.GateCaptureStart
        GateCommandEvidence = FlextInfraProtocolsGates.GateCommandEvidence
        GateContext = FlextInfraProtocolsGates.GateContext
        GateExecution = FlextInfraProtocolsCheck.GateExecution
        GateExecutionFacts = FlextInfraProtocolsGates.GateExecutionFacts
        GateExecutionIntent = FlextInfraProtocolsGates.GateExecutionIntent
        GateOutputReceipt = FlextInfraProtocolsCheck.GateOutputReceipt
        GateReportEvidence = FlextInfraProtocolsGates.GateReportEvidence
        GateResult = FlextInfraProtocolsCheck.GateResult
        GateTestIntent = FlextInfraProtocolsGates.GateTestIntent
        GeneratedFile = FlextInfraProtocolsDocs.GeneratedFile
        Generator = FlextInfraProtocolsBase.Generator
        GitAncestryRequest = FlextInfraProtocolsGit.GitAncestryRequest
        GitBoolReport = FlextInfraProtocolsGit.GitBoolReport
        GitBranchCreateRequest = FlextInfraProtocolsGit.GitBranchCreateRequest
        GitBranchRequest = FlextInfraProtocolsGit.GitBranchRequest
        GitBytesReport = FlextInfraProtocolsGit.GitBytesReport
        GitCheckoutPathsRequest = FlextInfraProtocolsGit.GitCheckoutPathsRequest
        GitCommitRequest = FlextInfraProtocolsGit.GitCommitRequest
        GitCommitishRequest = FlextInfraProtocolsGit.GitCommitishRequest
        GitDeleteRefRequest = FlextInfraProtocolsGit.GitDeleteRefRequest
        GitFingerprintInputsReport = FlextInfraProtocolsGit.GitFingerprintInputsReport
        GitHookRenderSpec = FlextInfraProtocolsCodegenRender.GitHookRenderSpec
        GitIndexLock = FlextInfraProtocolsBase.GitIndexLock
        GitIndexScope = FlextInfraProtocolsGit.GitIndexScope
        GitLaneBead = FlextInfraProtocolsGitLaneOwnership.GitLaneBead
        GitLaneBeadMetadata = FlextInfraProtocolsGitLaneInputs.GitLaneBeadMetadata
        GitLaneCoordinationPolicy = (
            FlextInfraProtocolsGitLaneInputs.GitLaneCoordinationPolicy
        )
        GitLaneEvidence = FlextInfraProtocolsGit.GitLaneEvidence
        GitLaneFacts = FlextInfraProtocolsGit.GitLaneFacts
        GitLaneGovernance = FlextInfraProtocolsGitLaneOwnership.GitLaneGovernance
        GitLaneOwnershipRequest = FlextInfraProtocolsGit.GitLaneOwnershipRequest
        GitLanePullRequest = FlextInfraProtocolsGitLaneInputs.GitLanePullRequest
        GitLaneRef = FlextInfraProtocolsGitLaneInputs.GitLaneRef
        GitLaneReport = FlextInfraProtocolsGit.GitLaneReport
        GitLaneRequest = FlextInfraProtocolsGit.GitLaneRequest
        GitLaneVerificationRequest = FlextInfraProtocolsGit.GitLaneVerificationRequest
        GitLaneViolation = FlextInfraProtocolsGitLaneInputs.GitLaneViolation
        GitMergeProbeRequest = FlextInfraProtocolsGit.GitMergeProbeRequest
        GitNumstatReport = FlextInfraProtocolsGit.GitNumstatReport
        GitOidListReport = FlextInfraProtocolsGit.GitOidListReport
        GitOidReport = FlextInfraProtocolsGit.GitOidReport
        GitPathPairRequest = FlextInfraProtocolsGit.GitPathPairRequest
        GitPathsRequest = FlextInfraProtocolsGit.GitPathsRequest
        GitPrimaryRootReport = FlextInfraProtocolsGit.GitPrimaryRootReport
        GitPushRequest = FlextInfraProtocolsGit.GitPushRequest
        GitRefHeadsReport = FlextInfraProtocolsGit.GitRefHeadsReport
        GitRefHeadsRequest = FlextInfraProtocolsGit.GitRefHeadsRequest
        GitRefRequest = FlextInfraProtocolsGit.GitRefRequest
        GitRelativePathRequest = FlextInfraProtocolsGit.GitRelativePathRequest
        GitRemoteBranchRequest = FlextInfraProtocolsGit.GitRemoteBranchRequest
        GitRemoteRequest = FlextInfraProtocolsGit.GitRemoteRequest
        GitRemoteUrlRequest = FlextInfraProtocolsGit.GitRemoteUrlRequest
        GitRepoRequest = FlextInfraProtocolsGit.GitRepoRequest
        GitRootReport = FlextInfraProtocolsGit.GitRootReport
        GitScopeFacts = FlextInfraProtocolsCheck.GitScopeFacts
        GitSigningConfigObservation = FlextInfraProtocolsGit.GitSigningConfigObservation
        GitSigningIdentityReport = FlextInfraProtocolsGit.GitSigningIdentityReport
        GitSourceReferenceMigration = (
            FlextInfraProtocolsDeps.GitSourceReferenceMigration
        )
        GitStashDropRequest = FlextInfraProtocolsGit.GitStashDropRequest
        GitStatusReport = FlextInfraProtocolsGit.GitStatusReport
        GitStatusRequest = FlextInfraProtocolsGit.GitStatusRequest
        GitSubmoduleContractRequest = FlextInfraProtocolsGit.GitSubmoduleContractRequest
        GitTextReport = FlextInfraProtocolsGit.GitTextReport
        GitTimestampReport = FlextInfraProtocolsGit.GitTimestampReport
        GitUpdateIndexGitlinkRequest = (
            FlextInfraProtocolsGit.GitUpdateIndexGitlinkRequest
        )
        GitWorktreeAddRequest = FlextInfraProtocolsGit.GitWorktreeAddRequest
        GitWorktreeEntry = FlextInfraProtocolsGit.GitWorktreeEntry
        GitWorktreeListReport = FlextInfraProtocolsGit.GitWorktreeListReport
        GithubReleaseAsset = FlextInfraProtocolsRelease.GithubReleaseAsset
        GithubReleaseAssets = FlextInfraProtocolsRelease.GithubReleaseAssets
        GithubReleaseIdentity = FlextInfraProtocolsRelease.GithubReleaseIdentity
        GithubReleaseInventory = FlextInfraProtocolsRelease.GithubReleaseInventory
        GithubService = FlextInfraProtocolsBase.GithubService
        GithubWorkflowRenderSpec = (
            FlextInfraProtocolsCodegenRender.GithubWorkflowRenderSpec
        )
        GlobalCheckTargetPlanner = FlextInfraProtocolsCheck.GlobalCheckTargetPlanner
        HeaderInfo = FlextInfraProtocolsTransformers.HeaderInfo
        HeaderSpan = FlextInfraProtocolsTransformers.HeaderSpan
        ImportLawPass = FlextInfraProtocolsRefactor.ImportLawPass
        ImportLawScope = FlextInfraProtocolsRefactor.ImportLawScope
        InfraSettings = FlextInfraProtocolsSettings.InfraSettings
        InventoryReport = FlextInfraProtocolsValidate.InventoryReport
        Issue = FlextInfraProtocolsCheck.Issue
        JscpdConfig = FlextInfraProtocolsDuplication.JscpdConfig
        JscpdDuplicate = FlextInfraProtocolsDuplication.JscpdDuplicate
        JscpdFile = FlextInfraProtocolsDuplication.JscpdFile
        JscpdLocation = FlextInfraProtocolsDuplication.JscpdLocation
        JscpdProjectOverlay = FlextInfraProtocolsDuplication.JscpdProjectOverlay
        JscpdReport = FlextInfraProtocolsDuplication.JscpdReport
        JscpdScan = FlextInfraProtocolsDuplication.JscpdScan
        JscpdSemantic = FlextInfraProtocolsDuplication.JscpdSemantic
        JscpdStatistics = FlextInfraProtocolsDuplication.JscpdStatistics
        JscpdStatisticsSummary = FlextInfraProtocolsDuplication.JscpdStatisticsSummary
        JscpdToolConfig = FlextInfraProtocolsDepsToolConfig.JscpdToolConfig
        JsonService = FlextInfraProtocolsBase.JsonService
        LayoutFinding = FlextInfraProtocolsLayout.LayoutFinding
        LayoutMoveSpec = FlextInfraProtocolsLayout.LayoutMoveSpec
        LayoutProjectOverrideSpec = FlextInfraProtocolsLayout.LayoutProjectOverrideSpec
        LayoutProjectReport = FlextInfraProtocolsLayout.LayoutProjectReport
        LayoutRunReport = FlextInfraProtocolsLayout.LayoutRunReport
        LayoutSpec = FlextInfraProtocolsLayout.LayoutSpec
        LazyInitConfig = FlextInfraProtocolsDepsToolConfig.LazyInitConfig
        LineWrapLiteral = FlextInfraProtocolsCheck.LineWrapLiteral
        LintGateResult = FlextInfraProtocolsBase.LintGateResult
        LintSnapshot = FlextInfraProtocolsWorktree.LintSnapshot
        ListOp = FlextInfraProtocolsDepsToml.ListOp
        LockedDependency = FlextInfraProtocolsWorkspace.LockedDependency
        LockedEnvironment = FlextInfraProtocolsWorkspace.LockedEnvironment
        LockedPackage = FlextInfraProtocolsWorkspace.LockedPackage
        LockedPackageSource = FlextInfraProtocolsWorkspace.LockedPackageSource
        LogicalStatement = FlextInfraProtocolsRope.LogicalStatement
        LoopOutcome = FlextInfraProtocolsCheck.LoopOutcome
        MakeWorkflowRenderSpec = FlextInfraProtocolsCodegenRender.MakeWorkflowRenderSpec
        MarkdownConfig = FlextInfraProtocolsDepsToolConfig.MarkdownConfig
        MarkdownFormatGate = FlextInfraProtocolsBase.MarkdownFormatGate
        MarkdownFormatGateFactory = FlextInfraProtocolsBase.MarkdownFormatGateFactory
        MarkdownLintRenderSpec = FlextInfraProtocolsCodegenRender.MarkdownLintRenderSpec
        MarkdownProjectedBlock = (
            FlextInfraProtocolsDepsToolConfig.MarkdownProjectedBlock
        )
        MemberRequirements = FlextInfraProtocolsDepsToml.MemberRequirements
        MiseHttpToolOptions = FlextInfraProtocolsMiseToolchain.MiseHttpToolOptions
        MisePostinstallOptions = FlextInfraProtocolsMiseToolchain.MisePostinstallOptions
        MiseToolEntry = FlextInfraProtocolsMiseToolchain.MiseToolEntry
        MiseToolVersionProbe = FlextInfraProtocolsMiseToolchain.MiseToolVersionProbe
        MiseToolchainConfigState = (
            FlextInfraProtocolsCodegenToolchain.MiseToolchainConfigState
        )
        MiseToolchainProjectLayout = (
            FlextInfraProtocolsCodegenToolchain.MiseToolchainProjectLayout
        )
        MiseToolchainProjectState = (
            FlextInfraProtocolsCodegenToolchain.MiseToolchainProjectState
        )
        MiseToolchainProofOptions = (
            FlextInfraProtocolsMiseToolchain.MiseToolchainProofOptions
        )
        MiseToolchainRepairPlan = (
            FlextInfraProtocolsMiseToolchainRepair.MiseToolchainRepairPlan
        )
        MiseToolchainWorkspaceLayout = (
            FlextInfraProtocolsCodegenToolchain.MiseToolchainWorkspaceLayout
        )
        MiseToolchainWorkspacePlan = (
            FlextInfraProtocolsCodegenToolchain.MiseToolchainWorkspacePlan
        )
        MkDocsConfigLoader = FlextInfraProtocolsDocs.MkDocsConfigLoader
        MkDocsConfigModule = FlextInfraProtocolsDocs.MkDocsConfigModule
        MkDocsServeModule = FlextInfraProtocolsDocs.MkDocsServeModule
        MkDocsServer = FlextInfraProtocolsDocs.MkDocsServer
        MkdocsProjectRenderContext = (
            FlextInfraProtocolsCodegenRender.MkdocsProjectRenderContext
        )
        MkdocsRenderContext = FlextInfraProtocolsCodegenRender.MkdocsRenderContext
        ModCommand = FlextInfraProtocolsRefactor.ModCommand
        ModConfig = FlextInfraProtocolsDepsToolConfig.ModConfig
        ModExecutionContext = FlextInfraProtocolsBase.ModExecutionContext
        ModFixtureDirectories = FlextInfraProtocolsCodemod.ModFixtureDirectories
        ModLoopPhase = FlextInfraProtocolsBase.ModLoopPhase
        ModModuleQuarantine = FlextInfraProtocolsScan.ModModuleQuarantine
        ModNativeRecord = FlextInfraProtocolsScan.ModNativeRecord
        ModOccurrence = FlextInfraProtocolsScan.ModOccurrence
        ModOccurrenceReport = FlextInfraProtocolsScan.ModOccurrenceReport
        ModPhaseAdvance = FlextInfraProtocolsScan.ModPhaseAdvance
        ModPhasesConfig = FlextInfraProtocolsDepsToolConfig.ModPhasesConfig
        ModProgress = FlextInfraProtocolsBase.ModProgress
        ModQuarantineExclusion = FlextInfraProtocolsScan.ModQuarantineExclusion
        ModReplacementOffsets = FlextInfraProtocolsScan.ModReplacementOffsets
        ModRequest = FlextInfraProtocolsBase.ModRequest
        ModRuleBatch = FlextInfraProtocolsCodemod.ModRuleBatch
        ModRuleOwnerRunner = FlextInfraProtocolsBase.ModRuleOwnerRunner
        ModRuleRoute = FlextInfraProtocolsRefactor.ModRuleRoute
        ModScanCounts = FlextInfraProtocolsScan.ModScanCounts
        ModScanEvidence = FlextInfraProtocolsScan.ModScanEvidence
        ModScanEvidenceReceipt = FlextInfraProtocolsScan.ModScanEvidenceReceipt
        ModScanFinding = FlextInfraProtocolsScan.ModScanFinding
        ModScanFindingReference = FlextInfraProtocolsScan.ModScanFindingReference
        ModScanPublication = FlextInfraProtocolsScan.ModScanPublication
        ModScanReport = FlextInfraProtocolsScan.ModScanReport
        ModScanSourceContext = FlextInfraProtocolsScan.ModScanSourceContext
        ModStageConfig = FlextInfraProtocolsDepsToolConfig.ModStageConfig
        ModTextCommand = FlextInfraProtocolsRefactor.ModTextCommand
        ModTextFinding = FlextInfraProtocolsScan.ModTextFinding
        ModTextReport = FlextInfraProtocolsScan.ModTextReport
        ModTextRule = FlextInfraProtocolsScan.ModTextRule
        ModelProtocolConformanceRenderContext = (
            FlextInfraProtocolsCodegenRender.ModelProtocolConformanceRenderContext
        )
        ModelProtocolRenderContext = (
            FlextInfraProtocolsCodegenRender.ModelProtocolRenderContext
        )
        ModuleMoveCommand = FlextInfraProtocolsRefactor.ModuleMoveCommand
        ModuleSelectionMixin = FlextInfraProtocolsMixins.ModuleSelectionMixin
        ModuleSemanticState = FlextInfraProtocolsRope.ModuleSemanticState
        ModuleSkeletonRenderContext = (
            FlextInfraProtocolsCodegenRender.ModuleSkeletonRenderContext
        )
        MypyConfig = FlextInfraProtocolsDepsToolConfigLinters.MypyConfig
        MypyDiagnostic = FlextInfraProtocolsGates.MypyDiagnostic
        MypyInvocation = FlextInfraProtocolsCheck.MypyInvocation
        MypyOverrideConfig = FlextInfraProtocolsDepsToolConfigLinters.MypyOverrideConfig
        MypyResourceLimit = FlextInfraProtocolsCheck.MypyResourceLimit
        NamespaceRelocationRequest = (
            FlextInfraProtocolsRefactor.NamespaceRelocationRequest
        )
        NamespaceRelocationState = FlextInfraProtocolsRefactor.NamespaceRelocationState
        NamespaceSelectionMixin = FlextInfraProtocolsMixins.NamespaceSelectionMixin
        NamespaceValidateCommand = FlextInfraProtocolsValidate.NamespaceValidateCommand
        NativeBindingEvidence = FlextInfraProtocolsWorkspace.NativeBindingEvidence
        NativeClassMetadata = FlextInfraProtocolsRopeRuntime.NativeClassMetadata
        NativeCodeEvidence = FlextInfraProtocolsWorkspace.NativeCodeEvidence
        NativeFunctionObservationContext = (
            FlextInfraProtocolsWorkspace.NativeFunctionObservationContext
        )
        NativeImportObservation = FlextInfraProtocolsWorkspace.NativeImportObservation
        NativeImportReference = FlextInfraProtocolsWorkspace.NativeImportReference
        NativeImportRequest = FlextInfraProtocolsWorkspace.NativeImportRequest
        NativeModuleSpec = FlextInfraProtocolsCheck.NativeModuleSpec
        NativeObservationContext = FlextInfraProtocolsWorkspace.NativeObservationContext
        NativeSemanticRenamePlanner = (
            FlextInfraProtocolsBase.NativeSemanticRenamePlanner
        )
        NativeStorageSlot = FlextInfraProtocolsCheck.NativeStorageSlot
        NestedClassPathMixin = FlextInfraProtocolsMixins.NestedClassPathMixin
        NonNegativeLineMixin = FlextInfraProtocolsMixins.NonNegativeLineMixin
        Object = FlextInfraProtocolsCensus.Object
        OperatorAuthorization = (
            FlextInfraProtocolsDepsToolConfigLinters.OperatorAuthorization
        )
        OutputStream = FlextInfraProtocolsBase.OutputStream
        PackagedDataSelection = FlextInfraProtocolsDeps.PackagedDataSelection
        ParseFailureViolation = (
            FlextInfraProtocolsRefactorNamespaceEnforcer.ParseFailureViolation
        )
        ParsedPythonModule = FlextInfraProtocolsRefactor.ParsedPythonModule
        PhaseConfig = FlextInfraProtocolsDepsToml.PhaseConfig
        PipCheckReport = FlextInfraProtocolsDeps.PipCheckReport
        PlanCollectionBundle = FlextInfraProtocolsDocsCollection.PlanCollectionBundle
        PlanCollectionConfig = FlextInfraProtocolsDocsCollection.PlanCollectionConfig
        PlanCollectionCoverage = (
            FlextInfraProtocolsDocsCollection.PlanCollectionCoverage
        )
        PlanCollectionManifest = (
            FlextInfraProtocolsDocsCollection.PlanCollectionManifest
        )
        PlanCollectionOwnedArtifact = (
            FlextInfraProtocolsDocsCollection.PlanCollectionOwnedArtifact
        )
        PlanCollectionRevision = (
            FlextInfraProtocolsDocsCollection.PlanCollectionRevision
        )
        PlanCollectionSource = FlextInfraProtocolsDocsCollection.PlanCollectionSource
        PlanCollectionTimestamp = (
            FlextInfraProtocolsDocsCollection.PlanCollectionTimestamp
        )
        PositiveLineMixin = FlextInfraProtocolsMixins.PositiveLineMixin
        PrimitiveOwnerCondition = FlextInfraProtocolsRope.PrimitiveOwnerCondition
        PrivateImportRewritePlan = (
            FlextInfraProtocolsTransformers.PrivateImportRewritePlan
        )
        ProcessExit = FlextInfraProtocolsBase.ProcessExit
        ProjectClassification = FlextInfraProtocolsRefactor.ProjectClassification
        ProjectConfigDocument = (
            FlextInfraProtocolsDepsToolConfigProject.ProjectConfigDocument
        )
        ProjectDependencyReport = FlextInfraProtocolsDeps.ProjectDependencyReport
        ProjectDuplicationOverrides = (
            FlextInfraProtocolsDuplication.ProjectDuplicationOverrides
        )
        ProjectEnforcementReport = FlextInfraProtocolsRefactor.ProjectEnforcementReport
        ProjectEntryNameMixin = FlextInfraProtocolsMixins.ProjectEntryNameMixin
        ProjectGitignoreConfig = (
            FlextInfraProtocolsDepsToolConfigProjectGitignore.ProjectGitignoreConfig
        )
        ProjectGitignorePreservedBlock = FlextInfraProtocolsDepsToolConfigProjectGitignore.ProjectGitignorePreservedBlock
        ProjectManagedArtifactsConfig = FlextInfraProtocolsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsConfig
        ProjectManagedArtifactsFragment = (
            FlextInfraProtocolsDepsToolConfigProject.ProjectManagedArtifactsFragment
        )
        ProjectManagedArtifactsResolution = FlextInfraProtocolsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsResolution
        ProjectManagedArtifactsSnapshot = FlextInfraProtocolsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsSnapshot
        ProjectMetadataState = FlextInfraProtocolsDeps.ProjectMetadataState
        ProjectMiseConfig = (
            FlextInfraProtocolsDepsToolConfigProjectMise.ProjectMiseConfig
        )
        ProjectMiseTool = FlextInfraProtocolsDepsToolConfigProjectMise.ProjectMiseTool
        ProjectNameMixin = FlextInfraProtocolsMixins.ProjectNameMixin
        ProjectNamesListMixin = FlextInfraProtocolsMixins.ProjectNamesListMixin
        ProjectNamesOptionalMixin = FlextInfraProtocolsMixins.ProjectNamesOptionalMixin
        ProjectPackagingDeclaration = (
            FlextInfraProtocolsDeps.ProjectPackagingDeclaration
        )
        ProjectPyprojectState = FlextInfraProtocolsWorkspace.ProjectPyprojectState
        ProjectReport = FlextInfraProtocolsCensus.ProjectReport
        ProjectResult = FlextInfraProtocolsCheck.ProjectResult
        ProjectSpec = FlextInfraProtocolsBase.ProjectSpec
        PromotedAliasTarget = FlextInfraProtocolsPromoted.PromotedAliasTarget
        PromotedCommand = FlextInfraProtocolsPromoted.PromotedCommand
        PromotedParam = FlextInfraProtocolsPromoted.PromotedParam
        PromotedRegistry = FlextInfraProtocolsPromoted.PromotedRegistry
        PromotedWorkspaceSpec = FlextInfraProtocolsPromoted.PromotedWorkspaceSpec
        ProtectedFileEditRequest = FlextInfraProtocolsBase.ProtectedFileEditRequest
        ProtectedSourceWriteRequest = (
            FlextInfraProtocolsBase.ProtectedSourceWriteRequest
        )
        ProtectedSourceWritesRequest = (
            FlextInfraProtocolsBase.ProtectedSourceWritesRequest
        )
        PruneAction = FlextInfraProtocolsWorktree.PruneAction
        PrunePlan = FlextInfraProtocolsWorktree.PrunePlan
        PyprojectAnalyzerContext = FlextInfraProtocolsDeps.PyprojectAnalyzerContext
        PyprojectDeclaredTopology = FlextInfraProtocolsDeps.PyprojectDeclaredTopology
        PyprojectDocumentState = FlextInfraProtocolsDeps.PyprojectDocumentState
        PyprojectModernizer = FlextInfraProtocolsBase.PyprojectModernizer
        PyreflyConfig = FlextInfraProtocolsDepsToolConfigTypeCheckers.PyreflyConfig
        PyreflyDiagnostic = FlextInfraProtocolsGates.PyreflyDiagnostic
        PyreflyReport = FlextInfraProtocolsGates.PyreflyReport
        PyrightConfig = FlextInfraProtocolsDepsToolConfigTypeCheckers.PyrightConfig
        PyrightDiagnostic = FlextInfraProtocolsGates.PyrightDiagnostic
        PyrightPosition = FlextInfraProtocolsGates.PyrightPosition
        PyrightRange = FlextInfraProtocolsGates.PyrightRange
        PyrightReport = FlextInfraProtocolsGates.PyrightReport
        PyrightSummary = FlextInfraProtocolsGates.PyrightSummary
        PytestCollectionManifest = FlextInfraProtocolsValidate.PytestCollectionManifest
        PytestConfig = FlextInfraProtocolsDepsToolConfig.PytestConfig
        PytestDiagnostics = FlextInfraProtocolsValidate.PytestDiagnostics
        PytestInvocation = FlextInfraProtocolsValidate.PytestInvocation
        PytestMarkdownAttempt = FlextInfraProtocolsValidate.PytestMarkdownAttempt
        PytestMarkdownCollection = FlextInfraProtocolsValidate.PytestMarkdownCollection
        PytestMarkdownItem = FlextInfraProtocolsValidate.PytestMarkdownItem
        PytestMarkdownOrigin = FlextInfraProtocolsValidate.PytestMarkdownOrigin
        PytestMarkdownReconciliation = (
            FlextInfraProtocolsValidate.PytestMarkdownReconciliation
        )
        PytestPhaseOutcome = FlextInfraProtocolsValidate.PytestPhaseOutcome
        PytestReportEvent = FlextInfraProtocolsValidate.PytestReportEvent
        PytestRunContext = FlextInfraProtocolsValidate.PytestRunContext
        PytestRunContextReceiver = FlextInfraProtocolsCheck.PytestRunContextReceiver
        PytestSelectionPlan = FlextInfraProtocolsValidate.PytestSelectionPlan
        PytestStopController = FlextInfraProtocolsBase.PytestStopController
        PytestWarningEvent = FlextInfraProtocolsValidate.PytestWarningEvent
        PytestWorkerCeiling = FlextInfraProtocolsDepsToolConfig.PytestWorkerCeiling
        PytestWorkerConfig = FlextInfraProtocolsBase.PytestWorkerConfig
        PythonEnvironmentObservation = (
            FlextInfraProtocolsWorkspace.PythonEnvironmentObservation
        )
        QltyRenderSpec = FlextInfraProtocolsCodegenRender.QltyRenderSpec
        ReadMixin = FlextInfraProtocolsMixins.ReadMixin
        RefactorCliArgs = FlextInfraProtocolsBase.RefactorCliArgs
        RefactorNamespaceEnforceInput = (
            FlextInfraProtocolsRefactor.RefactorNamespaceEnforceInput
        )
        RefactorProjectInfo = FlextInfraProtocolsRefactor.RefactorProjectInfo
        RefactorService = FlextInfraProtocolsBase.RefactorService
        ReferenceSite = FlextInfraProtocolsCensus.ReferenceSite
        ReleaseOptions = FlextInfraProtocolsRelease.ReleaseOptions
        ReleaseOrchestrator = FlextInfraProtocolsBase.ReleaseOrchestrator
        ReleasePhaseDispatchConfig = (
            FlextInfraProtocolsRelease.ReleasePhaseDispatchConfig
        )
        ReleasePlan = FlextInfraProtocolsRelease.ReleasePlan
        ReleaseRunCommand = FlextInfraProtocolsRelease.ReleaseRunCommand
        RemovalCandidate = FlextInfraProtocolsCensus.RemovalCandidate
        RemovalPreviewOptions = FlextInfraProtocolsCensus.RemovalPreviewOptions
        RemoveOp = FlextInfraProtocolsDepsToml.RemoveOp
        RenameCampaignRunner = FlextInfraProtocolsBase.RenameCampaignRunner
        RenderableTemplate = FlextInfraProtocolsBase.RenderableTemplate
        RepositoryDelta = FlextInfraProtocolsWorktree.RepositoryDelta
        RepositoryRef = FlextInfraProtocolsBase.RepositoryRef
        RepositoryRootPathMixin = FlextInfraProtocolsMixins.RepositoryRootPathMixin
        RepositoryWorktree = FlextInfraProtocolsWorktree.RepositoryWorktree
        RequiredNonNegativeLineMixin = (
            FlextInfraProtocolsMixins.RequiredNonNegativeLineMixin
        )
        RequirementsProvenance = FlextInfraProtocolsDeps.RequirementsProvenance
        ResolvedClassMove = FlextInfraProtocolsRopeMove.ResolvedClassMove
        Result = FlextInfraProtocolsRefactor.Result
        RopeAnalysisMethods = FlextInfraProtocolsRope.RopeAnalysisMethods
        RopeAssignedName = FlextInfraProtocolsRopeRuntime.RopeAssignedName
        RopeAssignment = FlextInfraProtocolsRopeRuntime.RopeAssignment
        RopeAstNode = FlextInfraProtocolsRopeRuntime.RopeAstNode
        RopeAttributeReadProof = FlextInfraProtocolsRope.RopeAttributeReadProof
        RopeBuiltinClass = FlextInfraProtocolsRopeRuntime.RopeBuiltinClass
        RopeCachedLogicalLineFinder = (
            FlextInfraProtocolsRopeRuntime.RopeCachedLogicalLineFinder
        )
        RopeChangeContents = FlextInfraProtocolsRopeRuntime.RopeChangeContents
        RopeChangeObserver = FlextInfraProtocolsRopeRuntime.RopeChangeObserver
        RopeChangeSet = FlextInfraProtocolsWorkspaceSnapshot.RopeChangeSet
        RopeClassObject = FlextInfraProtocolsRopeRuntime.RopeClassObject
        RopeContractCapturePolicy = FlextInfraProtocolsRope.RopeContractCapturePolicy
        RopeContractMatch = FlextInfraProtocolsRopeRuntime.RopeContractMatch
        RopeContractOrigin = FlextInfraProtocolsCodemod.RopeContractOrigin
        RopeContractRules = FlextInfraProtocolsCodemod.RopeContractRules
        RopeContractScope = FlextInfraProtocolsCodemod.RopeContractScope
        RopeContractScopeTarget = FlextInfraProtocolsCodemod.RopeContractScopeTarget
        RopeDefaultWildcard = FlextInfraProtocolsRopeRuntime.RopeDefaultWildcard
        RopeExternalResourceOwner = (
            FlextInfraProtocolsRopeRuntime.RopeExternalResourceOwner
        )
        RopeFile = FlextInfraProtocolsWorkspaceSnapshot.RopeFile
        RopeFromImport = FlextInfraProtocolsRopeRuntime.RopeFromImport
        RopeImportInfo = FlextInfraProtocolsRopeRuntime.RopeImportInfo
        RopeImportOrganizer = FlextInfraProtocolsRopeRuntime.RopeImportOrganizer
        RopeImportStatement = FlextInfraProtocolsRopeRuntime.RopeImportStatement
        RopeImportTools = FlextInfraProtocolsRopeRuntime.RopeImportTools
        RopeImportedModule = FlextInfraProtocolsRopeRuntime.RopeImportedModule
        RopeImportedName = FlextInfraProtocolsRopeRuntime.RopeImportedName
        RopeInlineVariable = FlextInfraProtocolsRopeRuntime.RopeInlineVariable
        RopeInventoryRecordInput = FlextInfraProtocolsRope.RopeInventoryRecordInput
        RopeLocation = FlextInfraProtocolsRopeRuntime.RopeLocation
        RopeLogicalLineFinder = FlextInfraProtocolsRopeRuntime.RopeLogicalLineFinder
        RopeMethodTransfer = FlextInfraProtocolsCodemod.RopeMethodTransfer
        RopeModuleConvention = FlextInfraProtocolsRope.RopeModuleConvention
        RopeModuleFinder = FlextInfraProtocolsWorkspaceSnapshot.RopeModuleFinder
        RopeModuleImports = FlextInfraProtocolsRopeRuntime.RopeModuleImports
        RopeModuleScope = FlextInfraProtocolsRopeRuntime.RopeModuleScope
        RopeMoveGlobal = FlextInfraProtocolsRopeRuntime.RopeMoveGlobal
        RopeMoveResource = FlextInfraProtocolsRopeRuntime.RopeMoveResource
        RopeNamedObject = FlextInfraProtocolsRopeRuntime.RopeNamedObject
        RopeNormalImport = FlextInfraProtocolsRopeRuntime.RopeNormalImport
        RopeOccurrence = FlextInfraProtocolsRopeRuntime.RopeOccurrence
        RopeOccurrenceFinder = FlextInfraProtocolsRopeRuntime.RopeOccurrenceFinder
        RopeParsedModule = FlextInfraProtocolsRopeRuntime.RopeParsedModule
        RopePreferences = FlextInfraProtocolsWorkspaceSnapshot.RopePreferences
        RopeProject = FlextInfraProtocolsWorkspaceSnapshot.RopeProject
        RopeProjectElection = FlextInfraProtocolsRope.RopeProjectElection
        RopeProjectFiles = FlextInfraProtocolsWorkspaceSnapshot.RopeProjectFiles
        RopeProjectInitializer = FlextInfraProtocolsRopeRuntime.RopeProjectInitializer
        RopePyCore = FlextInfraProtocolsRopeRuntime.RopePyCore
        RopePyModule = FlextInfraProtocolsRopeRuntime.RopePyModule
        RopePyName = FlextInfraProtocolsRopeRuntime.RopePyName
        RopePyObject = FlextInfraProtocolsRopeRuntime.RopePyObject
        RopeRenameOptions = FlextInfraProtocolsRefactor.RopeRenameOptions
        RopeResource = FlextInfraProtocolsWorkspaceSnapshot.RopeResource
        RopeResourceObserver = FlextInfraProtocolsRopeRuntime.RopeResourceObserver
        RopeResourceOwner = FlextInfraProtocolsRopeRuntime.RopeResourceOwner
        RopeRestructure = FlextInfraProtocolsRopeRuntime.RopeRestructure
        RopeRestructureRequest = FlextInfraProtocolsRope.RopeRestructureRequest
        RopeRoot = FlextInfraProtocolsWorkspaceSnapshot.RopeRoot
        RopeRuntimeSequence = FlextInfraProtocolsRopeRuntime.RopeRuntimeSequence
        RopeScope = FlextInfraProtocolsRopeRuntime.RopeScope
        RopeScopeDsl = FlextInfraProtocolsRope.RopeScopeDsl
        RopeScopeNameFinder = FlextInfraProtocolsRopeRuntime.RopeScopeNameFinder
        RopeScopedObject = FlextInfraProtocolsRopeRuntime.RopeScopedObject
        RopeSemanticModule = FlextInfraProtocolsRopeRuntime.RopeSemanticModule
        RopeSessionLifecycleDsl = FlextInfraProtocolsRope.RopeSessionLifecycleDsl
        RopeSignatureAddition = FlextInfraProtocolsCodemod.RopeSignatureAddition
        RopeSignatureRemoval = FlextInfraProtocolsCodemod.RopeSignatureRemoval
        RopeSimilarFinder = FlextInfraProtocolsRopeRuntime.RopeSimilarFinder
        RopeSourceAccess = FlextInfraProtocolsWorkspaceSnapshot.RopeSourceAccess
        RopeSourceAssignmentLayout = (
            FlextInfraProtocolsRopeRuntime.RopeSourceAssignmentLayout
        )
        RopeSourceBindingContext = (
            FlextInfraProtocolsRopeRuntime.RopeSourceBindingContext
        )
        RopeSourceBindingIndex = FlextInfraProtocolsRopeRuntime.RopeSourceBindingIndex
        RopeSourceClass = FlextInfraProtocolsRopeRuntime.RopeSourceClass
        RopeSourceClassLayout = FlextInfraProtocolsRopeRuntime.RopeSourceClassLayout
        RopeSourceDeclarationLines = (
            FlextInfraProtocolsRopeRuntime.RopeSourceDeclarationLines
        )
        RopeSourceDefinition = FlextInfraProtocolsRopeRuntime.RopeSourceDefinition
        RopeSourceFragment = FlextInfraProtocolsRopeRuntime.RopeSourceFragment
        RopeSourceFunction = FlextInfraProtocolsRopeRuntime.RopeSourceFunction
        RopeSourceImport = FlextInfraProtocolsRope.RopeSourceImport
        RopeSourceImportLayout = FlextInfraProtocolsRopeRuntime.RopeSourceImportLayout
        RopeSourceLines = FlextInfraProtocolsRopeRuntime.RopeSourceLines
        RopeSourceMemberResolver = (
            FlextInfraProtocolsRopeRuntime.RopeSourceMemberResolver
        )
        RopeSourceModule = FlextInfraProtocolsRopeRuntime.RopeSourceModule
        RopeSourceObject = FlextInfraProtocolsRopeRuntime.RopeSourceObject
        RopeSourceStringMapping = FlextInfraProtocolsRopeRuntime.RopeSourceStringMapping
        RopeUnresolvedBase = FlextInfraProtocolsRopeRuntime.RopeUnresolvedBase
        RopeWildcard = FlextInfraProtocolsRopeRuntime.RopeWildcard
        RopeWordFinder = FlextInfraProtocolsRopeRuntime.RopeWordFinder
        RopeWorder = FlextInfraProtocolsRopeRuntime.RopeWorder
        RopeWorkspaceDsl = FlextInfraProtocolsRope.RopeWorkspaceDsl
        RopeWorkspaceSession = FlextInfraProtocolsRope.RopeWorkspaceSession
        RuffConfig = FlextInfraProtocolsDepsToolConfigLinters.RuffConfig
        RuffLintConfig = FlextInfraProtocolsDepsToolConfigLinters.RuffLintConfig
        RuffProjectFacts = FlextInfraProtocolsDeps.RuffProjectFacts
        RuffTypeCheckingConfig = (
            FlextInfraProtocolsDepsToolConfigLinters.RuffTypeCheckingConfig
        )
        RuleDeltaOptions = FlextInfraProtocolsRefactor.RuleDeltaOptions
        RuleDeltaSpec = FlextInfraProtocolsBase.RuleDeltaSpec
        RunCommand = FlextInfraProtocolsCheck.RunCommand
        RuntimeDependencyCollector = FlextInfraProtocolsDeps.RuntimeDependencyCollector
        RuntimeDependencyInputs = FlextInfraProtocolsDeps.RuntimeDependencyInputs
        RuntimeDependencyPlan = FlextInfraProtocolsDeps.RuntimeDependencyPlan
        RuntimeDependencyProvider = FlextInfraProtocolsDeps.RuntimeDependencyProvider
        SafetyRunner = FlextInfraProtocolsBase.SafetyRunner
        SarifLocation = FlextInfraProtocolsCheck.SarifLocation
        SarifReport = FlextInfraProtocolsCheck.SarifReport
        SarifResult = FlextInfraProtocolsCheck.SarifResult
        SarifRule = FlextInfraProtocolsCheck.SarifRule
        SarifRun = FlextInfraProtocolsCheck.SarifRun
        ScanConfig = FlextInfraProtocolsCensus.ScanConfig
        ScanFindings = FlextInfraProtocolsCensus.ScanFindings
        ScanResult = FlextInfraProtocolsScan.ScanResult
        ScanViolation = FlextInfraProtocolsScan.ScanViolation
        Scanner = FlextInfraProtocolsBase.Scanner
        SccFile = FlextInfraProtocolsGates.SccFile
        SccLanguage = FlextInfraProtocolsGates.SccLanguage
        SccReport = FlextInfraProtocolsGates.SccReport
        SchemaRecord = FlextInfraProtocolsMiseToolchainBase.SchemaRecord
        ScopeDefinition = FlextInfraProtocolsRope.ScopeDefinition
        ScopeMixin = FlextInfraProtocolsMixins.ScopeMixin
        SemanticBehaviorOwners = FlextInfraProtocolsRefactor.SemanticBehaviorOwners
        SemanticBehaviorResolution = (
            FlextInfraProtocolsRefactor.SemanticBehaviorResolution
        )
        SemanticBehaviorRewriteRequest = (
            FlextInfraProtocolsTransformers.SemanticBehaviorRewriteRequest
        )
        SemanticFilePlan = FlextInfraProtocolsTransformers.SemanticFilePlan
        SemanticPublicationOptions = (
            FlextInfraProtocolsTransformers.SemanticPublicationOptions
        )
        SemanticRenameCandidateProvider = (
            FlextInfraProtocolsBase.SemanticRenameCandidateProvider
        )
        SemanticRenameDecision = FlextInfraProtocolsRefactor.SemanticRenameDecision
        SemanticRenamePlan = FlextInfraProtocolsRefactor.SemanticRenamePlan
        SemanticRenamePlanCommand = (
            FlextInfraProtocolsRefactor.SemanticRenamePlanCommand
        )
        SemanticRenamePreviewCommand = (
            FlextInfraProtocolsRefactor.SemanticRenamePreviewCommand
        )
        SemanticRenameSelection = FlextInfraProtocolsRefactor.SemanticRenameSelection
        SemanticRenameSelections = FlextInfraProtocolsRefactor.SemanticRenameSelections
        SemanticSourceState = FlextInfraProtocolsRope.SemanticSourceState
        SetOp = FlextInfraProtocolsDepsToml.SetOp
        SkillReportContext = FlextInfraProtocolsValidate.SkillReportContext
        SkillRuleEvaluationContext = (
            FlextInfraProtocolsValidate.SkillRuleEvaluationContext
        )
        SmellsConfig = FlextInfraProtocolsDepsToolConfig.SmellsConfig
        SonarcloudAuthentication = (
            FlextInfraProtocolsSonarcloud.SonarcloudAuthentication
        )
        SonarcloudIssue = FlextInfraProtocolsSonarcloud.SonarcloudIssue
        SonarcloudIssueFieldValue = (
            FlextInfraProtocolsSonarcloud.SonarcloudIssueFieldValue
        )
        SonarcloudIssuePaging = FlextInfraProtocolsSonarcloud.SonarcloudIssuePaging
        SonarcloudIssueSearch = FlextInfraProtocolsSonarcloud.SonarcloudIssueSearch
        SonarcloudRenderSpec = FlextInfraProtocolsCodegenRender.SonarcloudRenderSpec
        SonarcloudSetting = FlextInfraProtocolsSonarcloud.SonarcloudSetting
        SonarcloudSettingsPlan = FlextInfraProtocolsSonarcloud.SonarcloudSettingsPlan
        SonarcloudSettingsValues = (
            FlextInfraProtocolsSonarcloud.SonarcloudSettingsValues
        )
        SonarcloudSettingsWriteRequest = (
            FlextInfraProtocolsSonarcloud.SonarcloudSettingsWriteRequest
        )
        SourceBindingCollectorSpec = FlextInfraProtocolsRope.SourceBindingCollectorSpec
        SourceBindingInventoryRequest = (
            FlextInfraProtocolsRope.SourceBindingInventoryRequest
        )
        SourceClassDefinition = FlextInfraProtocolsRope.SourceClassDefinition
        SourceClassReference = FlextInfraProtocolsRope.SourceClassReference
        SourceComponentPlanner = FlextInfraProtocolsBase.SourceComponentPlanner
        SourceConclusions = FlextInfraProtocolsRopeRuntime.SourceConclusions
        SourceImportNormalizer = FlextInfraProtocolsBase.SourceImportNormalizer
        SourceInitializerPlanner = FlextInfraProtocolsBase.SourceInitializerPlanner
        SourcePreview = FlextInfraProtocolsBase.SourcePreview
        SourceScanRequest = FlextInfraProtocolsRope.SourceScanRequest
        SourceSnapshot = FlextInfraProtocolsRelease.SourceSnapshot
        StubAnalysisReport = FlextInfraProtocolsValidate.StubAnalysisReport
        SubprojectLoadContext = FlextInfraProtocolsWorkspace.SubprojectLoadContext
        SubscriptRebind = FlextInfraProtocolsRope.SubscriptRebind
        SummaryStats = FlextInfraProtocolsBase.SummaryStats
        SupervisedProcess = FlextInfraProtocolsBase.SupervisedProcess
        SymbolInfo = FlextInfraProtocolsRope.SymbolInfo
        TemplateEntrySpec = FlextInfraProtocolsBase.TemplateEntrySpec
        TestModuleSkeletonRenderContext = (
            FlextInfraProtocolsCodegenRender.TestModuleSkeletonRenderContext
        )
        TestmonCachePublication = FlextInfraProtocolsTestmon.TestmonCachePublication
        TestmonCacheState = FlextInfraProtocolsTestmon.TestmonCacheState
        TestmonRunAccounting = FlextInfraProtocolsTestmon.TestmonRunAccounting
        Tier0ImportAnalysis = FlextInfraProtocolsTransformers.Tier0ImportAnalysis
        TomlsortConfig = FlextInfraProtocolsDepsToolConfig.TomlsortConfig
        ToolConfigDocument = FlextInfraProtocolsDepsToolConfig.ToolConfigDocument
        ToolConfigTools = FlextInfraProtocolsDepsToolConfig.ToolConfigTools
        ToolingContextRequest = FlextInfraProtocolsDeps.ToolingContextRequest
        ToolingInputs = FlextInfraProtocolsDepsToolConfig.ToolingInputs
        ToolingRuntimeContext = FlextInfraProtocolsDepsToolConfig.ToolingRuntimeContext
        TrackerAuthorization = (
            FlextInfraProtocolsDepsToolConfigLinters.TrackerAuthorization
        )
        TransformStep = FlextInfraProtocolsBase.TransformStep
        TypeCheckerPathRules = FlextInfraProtocolsDeps.TypeCheckerPathRules
        UvOverrideEntries = FlextInfraProtocolsMiseToolchain.UvOverrideEntries
        UvOverridePackage = FlextInfraProtocolsMiseToolchain.UvOverridePackage
        UvResolutionSpec = FlextInfraProtocolsCodegenRender.UvResolutionSpec
        UvScopedOverride = FlextInfraProtocolsMiseToolchain.UvScopedOverride
        ValidationReport = FlextInfraProtocolsValidate.ValidationReport
        ValidationReportOutcome = FlextInfraProtocolsBase.ValidationReportOutcome
        Validator = FlextInfraProtocolsBase.Validator
        VersionTagMixin = FlextInfraProtocolsMixins.VersionTagMixin
        Violation = FlextInfraProtocolsCensus.Violation
        ViolationWithLine = FlextInfraProtocolsBase.ViolationWithLine
        ViolationsEngineCoverage = FlextInfraProtocolsRefactor.ViolationsEngineCoverage
        ViolationsRuleDelta = FlextInfraProtocolsRefactor.ViolationsRuleDelta
        ViolationsRuleEvaluation = FlextInfraProtocolsRefactor.ViolationsRuleEvaluation
        ViolationsSweepSources = FlextInfraProtocolsRefactor.ViolationsSweepSources
        ViolationsSweepStage = FlextInfraProtocolsRefactor.ViolationsSweepStage
        ViolationsTotals = FlextInfraProtocolsRefactor.ViolationsTotals
        WorkspaceBootstrapDependencies = (
            FlextInfraProtocolsWorkspaceSnapshot.WorkspaceBootstrapDependencies
        )
        WorkspaceDependencyReport = FlextInfraProtocolsDeps.WorkspaceDependencyReport
        WorkspaceEnforcementReport = (
            FlextInfraProtocolsRefactor.WorkspaceEnforcementReport
        )
        WorkspaceEnvironmentContracts = (
            FlextInfraProtocolsBase.WorkspaceEnvironmentContracts
        )
        WorkspaceLoopOutcome = FlextInfraProtocolsCheck.WorkspaceLoopOutcome
        WorkspaceOperationApplicability = (
            FlextInfraProtocolsWorkspace.WorkspaceOperationApplicability
        )
        WorkspaceOperationReceipt = (
            FlextInfraProtocolsWorkspace.WorkspaceOperationReceipt
        )
        WorkspaceOperationReport = FlextInfraProtocolsWorkspace.WorkspaceOperationReport
        WorkspaceOperationTarget = FlextInfraProtocolsWorkspace.WorkspaceOperationTarget
        WorkspaceProjectContext = FlextInfraProtocolsWorkspace.WorkspaceProjectContext
        WorkspaceReport = FlextInfraProtocolsCensus.WorkspaceReport
        WorkspaceRuntimeContext = FlextInfraProtocolsWorkspace.WorkspaceRuntimeContext
        WorkspaceSnapshot = FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot
        WorkspaceSnapshotSource = (
            FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshotSource
        )
        WorkspaceSpec = FlextInfraProtocolsBase.WorkspaceSpec
        WorkspaceTestsRequest = FlextInfraProtocolsWorkspace.WorkspaceTestsRequest
        WorktreeCandidate = FlextInfraProtocolsWorktree.WorktreeCandidate
        WorktreeFact = FlextInfraProtocolsWorktree.WorktreeFact
        WorktreeFactsPolicy = FlextInfraProtocolsWorktree.WorktreeFactsPolicy
        WorktreeFactsQuery = FlextInfraProtocolsWorktree.WorktreeFactsQuery
        WorktreesReport = FlextInfraProtocolsWorktree.WorktreesReport
        WrapperRewriteAccumulator = (
            FlextInfraProtocolsRefactor.WrapperRewriteAccumulator
        )
        WriteMixin = FlextInfraProtocolsMixins.WriteMixin
        XmlElementLike = FlextInfraProtocolsBase.XmlElementLike


p = FlextInfraProtocols
__all__: list[str] = ["FlextInfraProtocols", "p"]
