# AUTO-GENERATED FILE — Regenerate with: make gen
"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TypeAlias

from flext_cli import FlextCliModels

from flext_infra._models._codegen import FlextInfraCodegen
from flext_infra._models._config.base import FlextInfraModelsConfig
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.check import FlextInfraModelsCheck
from flext_infra._models.codegen import FlextInfraModelsCodegen
from flext_infra._models.codemod import FlextInfraModelsCodemod
from flext_infra._models.deps import FlextInfraModelsDeps
from flext_infra._models.docs import FlextInfraModelsDocs
from flext_infra._models.enforcement_catalog import FlextInfraModelsEnforcementCatalog
from flext_infra._models.gates import FlextInfraModelsGates
from flext_infra._models.git import FlextInfraModelsGit
from flext_infra._models.layout import FlextInfraModelsLayout
from flext_infra._models.mise_toolchain_base import FlextInfraModelsMiseToolchainBase
from flext_infra._models.mise_toolchain_repair import (
    FlextInfraModelsMiseToolchainRepair,
)
from flext_infra._models.mixins import FlextInfraModelsMixins
from flext_infra._models.promoted import FlextInfraModelsPromoted
from flext_infra._models.refactor import FlextInfraModelsRefactor
from flext_infra._models.release import FlextInfraModelsRelease
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.rope_move import FlextInfraModelsRopeMove
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._models.settings import FlextInfraModelsSettings
from flext_infra._models.sonarcloud import FlextInfraModelsSonarcloud
from flext_infra._models.testmon import FlextInfraModelsTestmon
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._models.validate import FlextInfraModelsCore
from flext_infra._models.workspace import FlextInfraModelsWorkspace
from flext_infra._models.workspace_snapshot import FlextInfraModelsWorkspaceSnapshot
from flext_infra._models.worktree import FlextInfraModelsWorktree


class FlextInfraModels(FlextCliModels):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraCodegen,
        FlextInfraModelsCensus,
        FlextInfraModelsCheck,
        FlextInfraModelsCodegen,
        FlextInfraModelsCodemod,
        FlextInfraModelsDeps,
        FlextInfraModelsDocs,
        FlextInfraModelsEnforcementCatalog,
        FlextInfraModelsGates,
        FlextInfraModelsGit,
        FlextInfraModelsLayout,
        FlextInfraModelsMiseToolchainBase,
        FlextInfraModelsMiseToolchainRepair,
        FlextInfraModelsMixins,
        FlextInfraModelsPromoted,
        FlextInfraModelsRefactor,
        FlextInfraModelsRelease,
        FlextInfraModelsRope,
        FlextInfraModelsRopeMove,
        FlextInfraModelsScan,
        FlextInfraModelsSettings,
        FlextInfraModelsSonarcloud,
        FlextInfraModelsTestmon,
        FlextInfraModelsTransformers,
        FlextInfraModelsCore,
        FlextInfraModelsWorkspace,
        FlextInfraModelsWorkspaceSnapshot,
        FlextInfraModelsWorktree,
        FlextInfraModelsConfig,
    ):
        """Infrastructure-domain models - all classes exposed directly."""

        AutoFixResult: TypeAlias = FlextInfraCodegen.AutoFixResult
        CandidateBootstrapCommand: TypeAlias = (
            FlextInfraCodegen.CandidateBootstrapCommand
        )
        CensusReport: TypeAlias = FlextInfraCodegen.CensusReport
        CensusViolation: TypeAlias = FlextInfraCodegen.CensusViolation
        CodegenAutoFixCommand: TypeAlias = FlextInfraCodegen.CodegenAutoFixCommand
        CodegenCommand: TypeAlias = FlextInfraCodegen.CodegenCommand
        CodegenConformPorts: TypeAlias = FlextInfraCodegen.CodegenConformPorts
        CodegenConformState: TypeAlias = FlextInfraCodegen.CodegenConformState
        CodegenFileParticipant: TypeAlias = FlextInfraCodegen.CodegenFileParticipant
        CodegenFilePlan: TypeAlias = FlextInfraCodegen.CodegenFilePlan
        CodegenPlan: TypeAlias = FlextInfraCodegen.CodegenPlan
        CodegenRepositoryPlanOutcome: TypeAlias = (
            FlextInfraCodegen.CodegenRepositoryPlanOutcome
        )
        CodegenResult: TypeAlias = FlextInfraCodegen.CodegenResult
        ConsolidatorFileResult: TypeAlias = FlextInfraCodegen.ConsolidatorFileResult
        ConsolidatorReport: TypeAlias = FlextInfraCodegen.ConsolidatorReport
        DistroDockerRenderSpec: TypeAlias = FlextInfraCodegen.DistroDockerRenderSpec
        EnvrcRenderSpec: TypeAlias = FlextInfraCodegen.EnvrcRenderSpec
        FacadeFamily: TypeAlias = FlextInfraCodegen.FacadeFamily
        FixContext: TypeAlias = FlextInfraCodegen.FixContext
        GitHookRenderSpec: TypeAlias = FlextInfraCodegen.GitHookRenderSpec
        GithubWorkflowRenderSpec: TypeAlias = FlextInfraCodegen.GithubWorkflowRenderSpec
        LazyInitPackageContext: TypeAlias = FlextInfraCodegen.LazyInitPackageContext
        LazyInitPlan: TypeAlias = FlextInfraCodegen.LazyInitPlan
        LazyInitRootRender: TypeAlias = FlextInfraCodegen.LazyInitRootRender
        LazyInitRun: TypeAlias = FlextInfraCodegen.LazyInitRun
        MakeWorkflowRenderSpec: TypeAlias = FlextInfraCodegen.MakeWorkflowRenderSpec
        MarkdownLintRenderSpec: TypeAlias = FlextInfraCodegen.MarkdownLintRenderSpec
        MiseToolchainConfigState: TypeAlias = FlextInfraCodegen.MiseToolchainConfigState
        MiseToolchainProjectLayout: TypeAlias = (
            FlextInfraCodegen.MiseToolchainProjectLayout
        )
        MiseToolchainProjectState: TypeAlias = (
            FlextInfraCodegen.MiseToolchainProjectState
        )
        MiseToolchainWorkspaceLayout: TypeAlias = (
            FlextInfraCodegen.MiseToolchainWorkspaceLayout
        )
        MiseToolchainWorkspacePlan: TypeAlias = (
            FlextInfraCodegen.MiseToolchainWorkspacePlan
        )
        MkdocsProjectRenderContext: TypeAlias = (
            FlextInfraCodegen.MkdocsProjectRenderContext
        )
        MkdocsRenderContext: TypeAlias = FlextInfraCodegen.MkdocsRenderContext
        ModelProtocolConformanceRenderContext: TypeAlias = (
            FlextInfraCodegen.ModelProtocolConformanceRenderContext
        )
        ModelProtocolRenderContext: TypeAlias = (
            FlextInfraCodegen.ModelProtocolRenderContext
        )
        ModuleSkeletonRenderContext: TypeAlias = (
            FlextInfraCodegen.ModuleSkeletonRenderContext
        )
        NamespaceModulePolicy: TypeAlias = FlextInfraCodegen.NamespaceModulePolicy
        PythonModelRun: TypeAlias = FlextInfraCodegen.PythonModelRun
        PythonModuleFacts: TypeAlias = FlextInfraCodegen.PythonModuleFacts
        PythonModuleFactsDraft: TypeAlias = FlextInfraCodegen.PythonModuleFactsDraft
        QltyRenderSpec: TypeAlias = FlextInfraCodegen.QltyRenderSpec
        QualityGateCheck: TypeAlias = FlextInfraCodegen.QualityGateCheck
        QualityGateProjectFinding: TypeAlias = (
            FlextInfraCodegen.QualityGateProjectFinding
        )
        RopeModuleIndexEntry: TypeAlias = FlextInfraCodegen.RopeModuleIndexEntry
        RopePackageIndexEntry: TypeAlias = FlextInfraCodegen.RopePackageIndexEntry
        RopeProjectLayout: TypeAlias = FlextInfraCodegen.RopeProjectLayout
        RopeWorkspaceIndex: TypeAlias = FlextInfraCodegen.RopeWorkspaceIndex
        ScaffoldDirRequest: TypeAlias = FlextInfraCodegen.ScaffoldDirRequest
        ScaffoldResult: TypeAlias = FlextInfraCodegen.ScaffoldResult
        SemanticSourcePlan: TypeAlias = FlextInfraCodegen.SemanticSourcePlan
        SonarcloudRenderSpec: TypeAlias = FlextInfraCodegen.SonarcloudRenderSpec
        StageSourceOptions: TypeAlias = FlextInfraCodegen.StageSourceOptions
        StageSourcePlan: TypeAlias = FlextInfraCodegen.StageSourcePlan
        TestModuleSkeletonRenderContext: TypeAlias = (
            FlextInfraCodegen.TestModuleSkeletonRenderContext
        )
        UvResolutionSpec: TypeAlias = FlextInfraCodegen.UvResolutionSpec
        ViolationKey: TypeAlias = FlextInfraCodegen.ViolationKey
        DuplicateCopyCure: TypeAlias = FlextInfraModelsCensus.DuplicateCopyCure
        DuplicateCureEdit: TypeAlias = FlextInfraModelsCensus.DuplicateCureEdit
        DuplicateCureOutcome: TypeAlias = FlextInfraModelsCensus.DuplicateCureOutcome
        DuplicateCurePlan: TypeAlias = FlextInfraModelsCensus.DuplicateCurePlan
        DuplicateDefinition: TypeAlias = FlextInfraModelsCensus.DuplicateDefinition
        DuplicateDeletion: TypeAlias = FlextInfraModelsCensus.DuplicateDeletion
        DuplicateGroup: TypeAlias = FlextInfraModelsCensus.DuplicateGroup
        DuplicateGroupCure: TypeAlias = FlextInfraModelsCensus.DuplicateGroupCure
        Object: TypeAlias = FlextInfraModelsCensus.Object
        ProjectReport: TypeAlias = FlextInfraModelsCensus.ProjectReport
        ReferenceSite: TypeAlias = FlextInfraModelsCensus.ReferenceSite
        RemovalCandidate: TypeAlias = FlextInfraModelsCensus.RemovalCandidate
        RemovalPreviewOptions: TypeAlias = FlextInfraModelsCensus.RemovalPreviewOptions
        ScanConfig: TypeAlias = FlextInfraModelsCensus.ScanConfig
        ScanFindings: TypeAlias = FlextInfraModelsCensus.ScanFindings
        Violation: TypeAlias = FlextInfraModelsCensus.Violation
        WorkspaceReport: TypeAlias = FlextInfraModelsCensus.WorkspaceReport
        BanditFinding: TypeAlias = FlextInfraModelsCheck.BanditFinding
        BanditReport: TypeAlias = FlextInfraModelsCheck.BanditReport
        BanditScanError: TypeAlias = FlextInfraModelsCheck.BanditScanError
        CheckProjectTarget: TypeAlias = FlextInfraModelsCheck.CheckProjectTarget
        CheckReportSummary: TypeAlias = FlextInfraModelsCheck.CheckReportSummary
        FixPyreflyConfigCommand: TypeAlias = (
            FlextInfraModelsCheck.FixPyreflyConfigCommand
        )
        GateExecution: TypeAlias = FlextInfraModelsCheck.GateExecution
        GateExecutionParams: TypeAlias = FlextInfraModelsCheck.GateExecutionParams
        GateOutputReceipt: TypeAlias = FlextInfraModelsCheck.GateOutputReceipt
        GateResult: TypeAlias = FlextInfraModelsCheck.GateResult
        Issue: TypeAlias = FlextInfraModelsCheck.Issue
        LineWrapLiteral: TypeAlias = FlextInfraModelsCheck.LineWrapLiteral
        LoopOutcome: TypeAlias = FlextInfraModelsCheck.LoopOutcome
        MypyInvocation: TypeAlias = FlextInfraModelsCheck.MypyInvocation
        MypyResourceLimit: TypeAlias = FlextInfraModelsCheck.MypyResourceLimit
        ProjectResult: TypeAlias = FlextInfraModelsCheck.ProjectResult
        RunCommand: TypeAlias = FlextInfraModelsCheck.RunCommand
        SarifLocation: TypeAlias = FlextInfraModelsCheck.SarifLocation
        SarifReport: TypeAlias = FlextInfraModelsCheck.SarifReport
        SarifResult: TypeAlias = FlextInfraModelsCheck.SarifResult
        SarifRule: TypeAlias = FlextInfraModelsCheck.SarifRule
        SarifRun: TypeAlias = FlextInfraModelsCheck.SarifRun
        AstGrepCapture: TypeAlias = FlextInfraModelsCodemod.AstGrepCapture
        AstGrepDiagnostic: TypeAlias = FlextInfraModelsCodemod.AstGrepDiagnostic
        AstGrepOwnedPathDiagnostic: TypeAlias = (
            FlextInfraModelsCodemod.AstGrepOwnedPathDiagnostic
        )
        AstGrepReport: TypeAlias = FlextInfraModelsCodemod.AstGrepReport
        CodemodBindingSnapshot: TypeAlias = (
            FlextInfraModelsCodemod.CodemodBindingSnapshot
        )
        ContractAdmissionOptions: TypeAlias = (
            FlextInfraModelsCodemod.ContractAdmissionOptions
        )
        FamilyFlattenRule: TypeAlias = FlextInfraModelsCodemod.FamilyFlattenRule
        ModFixtureDirectories: TypeAlias = FlextInfraModelsCodemod.ModFixtureDirectories
        ModRuleBatch: TypeAlias = FlextInfraModelsCodemod.ModRuleBatch
        RopeContractOrigin: TypeAlias = FlextInfraModelsCodemod.RopeContractOrigin
        RopeContractRule: TypeAlias = FlextInfraModelsCodemod.RopeContractRule
        RopeContractRules: TypeAlias = FlextInfraModelsCodemod.RopeContractRules
        RopeContractScope: TypeAlias = FlextInfraModelsCodemod.RopeContractScope
        RopeContractScopeTarget: TypeAlias = (
            FlextInfraModelsCodemod.RopeContractScopeTarget
        )
        RopeMethodTransfer: TypeAlias = FlextInfraModelsCodemod.RopeMethodTransfer
        RopeSignatureAddition: TypeAlias = FlextInfraModelsCodemod.RopeSignatureAddition
        RopeSignatureRemoval: TypeAlias = FlextInfraModelsCodemod.RopeSignatureRemoval
        AccessorPolicyConfig: TypeAlias = FlextInfraModelsDeps.AccessorPolicyConfig
        DependencyMarkerEnvironment: TypeAlias = (
            FlextInfraModelsDeps.DependencyMarkerEnvironment
        )
        DepsToml: TypeAlias = FlextInfraModelsDeps.DepsToml
        DeptryIssueGroups: TypeAlias = FlextInfraModelsDeps.DeptryIssueGroups
        DeptryReport: TypeAlias = FlextInfraModelsDeps.DeptryReport
        DetectCommand: TypeAlias = FlextInfraModelsDeps.DetectCommand
        DiagnosticPathException: TypeAlias = (
            FlextInfraModelsDeps.DiagnosticPathException
        )
        DiagnosticRuleChange: TypeAlias = FlextInfraModelsDeps.DiagnosticRuleChange
        FacadeMembersConfig: TypeAlias = FlextInfraModelsDeps.FacadeMembersConfig
        GitSourceReferenceMigration: TypeAlias = (
            FlextInfraModelsDeps.GitSourceReferenceMigration
        )
        JscpdToolConfig: TypeAlias = FlextInfraModelsDeps.JscpdToolConfig
        LazyInitConfig: TypeAlias = FlextInfraModelsDeps.LazyInitConfig
        MarkdownConfig: TypeAlias = FlextInfraModelsDeps.MarkdownConfig
        MarkdownProjectedBlock: TypeAlias = FlextInfraModelsDeps.MarkdownProjectedBlock
        ModConfig: TypeAlias = FlextInfraModelsDeps.ModConfig
        ModPhasesConfig: TypeAlias = FlextInfraModelsDeps.ModPhasesConfig
        ModStageConfig: TypeAlias = FlextInfraModelsDeps.ModStageConfig
        MypyConfig: TypeAlias = FlextInfraModelsDeps.MypyConfig
        MypyOverrideConfig: TypeAlias = FlextInfraModelsDeps.MypyOverrideConfig
        OperatorAuthorization: TypeAlias = FlextInfraModelsDeps.OperatorAuthorization
        PackagedDataSelection: TypeAlias = FlextInfraModelsDeps.PackagedDataSelection
        PipCheckReport: TypeAlias = FlextInfraModelsDeps.PipCheckReport
        ProjectConfigDocument: TypeAlias = FlextInfraModelsDeps.ProjectConfigDocument
        ProjectDependencyReport: TypeAlias = (
            FlextInfraModelsDeps.ProjectDependencyReport
        )
        ProjectGitignoreConfig: TypeAlias = FlextInfraModelsDeps.ProjectGitignoreConfig
        ProjectGitignorePreservedBlock: TypeAlias = (
            FlextInfraModelsDeps.ProjectGitignorePreservedBlock
        )
        ProjectManagedArtifactsConfig: TypeAlias = (
            FlextInfraModelsDeps.ProjectManagedArtifactsConfig
        )
        ProjectManagedArtifactsFragment: TypeAlias = (
            FlextInfraModelsDeps.ProjectManagedArtifactsFragment
        )
        ProjectManagedArtifactsResolution: TypeAlias = (
            FlextInfraModelsDeps.ProjectManagedArtifactsResolution
        )
        ProjectManagedArtifactsSnapshot: TypeAlias = (
            FlextInfraModelsDeps.ProjectManagedArtifactsSnapshot
        )
        ProjectMetadataState: TypeAlias = FlextInfraModelsDeps.ProjectMetadataState
        ProjectMiseConfig: TypeAlias = FlextInfraModelsDeps.ProjectMiseConfig
        ProjectMiseTool: TypeAlias = FlextInfraModelsDeps.ProjectMiseTool
        ProjectPackagingDeclaration: TypeAlias = (
            FlextInfraModelsDeps.ProjectPackagingDeclaration
        )
        PyprojectAnalyzerContext: TypeAlias = (
            FlextInfraModelsDeps.PyprojectAnalyzerContext
        )
        PyprojectDeclaredTopology: TypeAlias = (
            FlextInfraModelsDeps.PyprojectDeclaredTopology
        )
        PyprojectDocumentState: TypeAlias = FlextInfraModelsDeps.PyprojectDocumentState
        PyreflyConfig: TypeAlias = FlextInfraModelsDeps.PyreflyConfig
        PyrightConfig: TypeAlias = FlextInfraModelsDeps.PyrightConfig
        PytestConfig: TypeAlias = FlextInfraModelsDeps.PytestConfig
        PytestWorkerCeiling: TypeAlias = FlextInfraModelsDeps.PytestWorkerCeiling
        RequirementsProvenance: TypeAlias = FlextInfraModelsDeps.RequirementsProvenance
        RuffConfig: TypeAlias = FlextInfraModelsDeps.RuffConfig
        RuffLintConfig: TypeAlias = FlextInfraModelsDeps.RuffLintConfig
        RuffProjectFacts: TypeAlias = FlextInfraModelsDeps.RuffProjectFacts
        RuffTypeCheckingConfig: TypeAlias = FlextInfraModelsDeps.RuffTypeCheckingConfig
        RuntimeDependencyInputs: TypeAlias = (
            FlextInfraModelsDeps.RuntimeDependencyInputs
        )
        RuntimeDependencyPlan: TypeAlias = FlextInfraModelsDeps.RuntimeDependencyPlan
        RuntimeDependencyProvider: TypeAlias = (
            FlextInfraModelsDeps.RuntimeDependencyProvider
        )
        SmellsConfig: TypeAlias = FlextInfraModelsDeps.SmellsConfig
        TomlsortConfig: TypeAlias = FlextInfraModelsDeps.TomlsortConfig
        ToolConfigDocument: TypeAlias = FlextInfraModelsDeps.ToolConfigDocument
        ToolConfigTools: TypeAlias = FlextInfraModelsDeps.ToolConfigTools
        ToolingContextRequest: TypeAlias = FlextInfraModelsDeps.ToolingContextRequest
        ToolingInputs: TypeAlias = FlextInfraModelsDeps.ToolingInputs
        ToolingRuntimeContext: TypeAlias = FlextInfraModelsDeps.ToolingRuntimeContext
        TrackerAuthorization: TypeAlias = FlextInfraModelsDeps.TrackerAuthorization
        WorkspaceDependencyReport: TypeAlias = (
            FlextInfraModelsDeps.WorkspaceDependencyReport
        )
        AuditIssue: TypeAlias = FlextInfraModelsDocs.AuditIssue
        AuditScopeParams: TypeAlias = FlextInfraModelsDocs.AuditScopeParams
        DocScope: TypeAlias = FlextInfraModelsDocs.DocScope
        DocsApiReadmeContext: TypeAlias = FlextInfraModelsDocs.DocsApiReadmeContext
        DocsCatalogEntry: TypeAlias = FlextInfraModelsDocs.DocsCatalogEntry
        DocsClassCount: TypeAlias = FlextInfraModelsDocs.DocsClassCount
        DocsCollectRequest: TypeAlias = FlextInfraModelsDocs.DocsCollectRequest
        DocsDependencyReference: TypeAlias = (
            FlextInfraModelsDocs.DocsDependencyReference
        )
        DocsDirectivePageContext: TypeAlias = (
            FlextInfraModelsDocs.DocsDirectivePageContext
        )
        DocsExportBinding: TypeAlias = FlextInfraModelsDocs.DocsExportBinding
        DocsGenerateRequest: TypeAlias = FlextInfraModelsDocs.DocsGenerateRequest
        DocsGenerationBundle: TypeAlias = FlextInfraModelsDocs.DocsGenerationBundle
        DocsGovernanceLinks: TypeAlias = FlextInfraModelsDocs.DocsGovernanceLinks
        DocsGuideEntry: TypeAlias = FlextInfraModelsDocs.DocsGuideEntry
        DocsGuidesIndexContext: TypeAlias = FlextInfraModelsDocs.DocsGuidesIndexContext
        DocsLlmsContext: TypeAlias = FlextInfraModelsDocs.DocsLlmsContext
        DocsModuleEntry: TypeAlias = FlextInfraModelsDocs.DocsModuleEntry
        DocsModulesIndexContext: TypeAlias = (
            FlextInfraModelsDocs.DocsModulesIndexContext
        )
        DocsOverviewContext: TypeAlias = FlextInfraModelsDocs.DocsOverviewContext
        DocsPageContext: TypeAlias = FlextInfraModelsDocs.DocsPageContext
        DocsPhaseItemModel: TypeAlias = FlextInfraModelsDocs.DocsPhaseItemModel
        DocsPhaseReport: TypeAlias = FlextInfraModelsDocs.DocsPhaseReport
        DocsPhaseReports: TypeAlias = FlextInfraModelsDocs.DocsPhaseReports
        DocsProjectCatalogContext: TypeAlias = (
            FlextInfraModelsDocs.DocsProjectCatalogContext
        )
        DocsProjectIndexContext: TypeAlias = (
            FlextInfraModelsDocs.DocsProjectIndexContext
        )
        DocsProjectIndexEntry: TypeAlias = FlextInfraModelsDocs.DocsProjectIndexEntry
        DocsProjectReadmeContext: TypeAlias = (
            FlextInfraModelsDocs.DocsProjectReadmeContext
        )
        DocsPublicContract: TypeAlias = FlextInfraModelsDocs.DocsPublicContract
        DocsRenderedArtifact: TypeAlias = FlextInfraModelsDocs.DocsRenderedArtifact
        DocsRenderedToc: TypeAlias = FlextInfraModelsDocs.DocsRenderedToc
        DocsRootInputs: TypeAlias = FlextInfraModelsDocs.DocsRootInputs
        DocsRootOverviewContext: TypeAlias = (
            FlextInfraModelsDocs.DocsRootOverviewContext
        )
        DocsRootProjectsIndexContext: TypeAlias = (
            FlextInfraModelsDocs.DocsRootProjectsIndexContext
        )
        DocsScopeArtifacts: TypeAlias = FlextInfraModelsDocs.DocsScopeArtifacts
        DocsTocToken: TypeAlias = FlextInfraModelsDocs.DocsTocToken
        DocstringCoverage: TypeAlias = FlextInfraModelsDocs.DocstringCoverage
        GeneratedFile: TypeAlias = FlextInfraModelsDocs.GeneratedFile
        PlanCollectionBundle: TypeAlias = FlextInfraModelsDocs.PlanCollectionBundle
        PlanCollectionConfig: TypeAlias = FlextInfraModelsDocs.PlanCollectionConfig
        PlanCollectionCoverage: TypeAlias = FlextInfraModelsDocs.PlanCollectionCoverage
        PlanCollectionManifest: TypeAlias = FlextInfraModelsDocs.PlanCollectionManifest
        PlanCollectionOwnedArtifact: TypeAlias = (
            FlextInfraModelsDocs.PlanCollectionOwnedArtifact
        )
        PlanCollectionRevision: TypeAlias = FlextInfraModelsDocs.PlanCollectionRevision
        PlanCollectionSource: TypeAlias = FlextInfraModelsDocs.PlanCollectionSource
        PlanCollectionTimestamp: TypeAlias = (
            FlextInfraModelsDocs.PlanCollectionTimestamp
        )
        EnforcementCatalog: TypeAlias = (
            FlextInfraModelsEnforcementCatalog.EnforcementCatalog
        )
        EnforcementClaim: TypeAlias = (
            FlextInfraModelsEnforcementCatalog.EnforcementClaim
        )
        DeptryDiagnostic: TypeAlias = FlextInfraModelsGates.DeptryDiagnostic
        DeptryError: TypeAlias = FlextInfraModelsGates.DeptryError
        DeptryLocation: TypeAlias = FlextInfraModelsGates.DeptryLocation
        DeptryNativeReport: TypeAlias = FlextInfraModelsGates.DeptryNativeReport
        DeptryScan: TypeAlias = FlextInfraModelsGates.DeptryScan
        DuplicationAssessment: TypeAlias = FlextInfraModelsGates.DuplicationAssessment
        DuplicationCandidateEvidence: TypeAlias = (
            FlextInfraModelsGates.DuplicationCandidateEvidence
        )
        DuplicationClassification: TypeAlias = (
            FlextInfraModelsGates.DuplicationClassification
        )
        DuplicationSpanMeasure: TypeAlias = FlextInfraModelsGates.DuplicationSpanMeasure
        GateAttestationCreateRequest: TypeAlias = (
            FlextInfraModelsGates.GateAttestationCreateRequest
        )
        GateAttestationPredicate: TypeAlias = (
            FlextInfraModelsGates.GateAttestationPredicate
        )
        GateAttestationReport: TypeAlias = FlextInfraModelsGates.GateAttestationReport
        GateAttestationVerifyRequest: TypeAlias = (
            FlextInfraModelsGates.GateAttestationVerifyRequest
        )
        GateCaptureBeginRequest: TypeAlias = (
            FlextInfraModelsGates.GateCaptureBeginRequest
        )
        GateCaptureFinishRequest: TypeAlias = (
            FlextInfraModelsGates.GateCaptureFinishRequest
        )
        GateCaptureReport: TypeAlias = FlextInfraModelsGates.GateCaptureReport
        GateCaptureRequest: TypeAlias = FlextInfraModelsGates.GateCaptureRequest
        GateCaptureStart: TypeAlias = FlextInfraModelsGates.GateCaptureStart
        GateCommandEvidence: TypeAlias = FlextInfraModelsGates.GateCommandEvidence
        GateContext: TypeAlias = FlextInfraModelsGates.GateContext
        GateExecutionFacts: TypeAlias = FlextInfraModelsGates.GateExecutionFacts
        GateExecutionIntent: TypeAlias = FlextInfraModelsGates.GateExecutionIntent
        GateReportEvidence: TypeAlias = FlextInfraModelsGates.GateReportEvidence
        GateTestIntent: TypeAlias = FlextInfraModelsGates.GateTestIntent
        JscpdConfig: TypeAlias = FlextInfraModelsGates.JscpdConfig
        JscpdDuplicate: TypeAlias = FlextInfraModelsGates.JscpdDuplicate
        JscpdFile: TypeAlias = FlextInfraModelsGates.JscpdFile
        JscpdLocation: TypeAlias = FlextInfraModelsGates.JscpdLocation
        JscpdProjectOverlay: TypeAlias = FlextInfraModelsGates.JscpdProjectOverlay
        JscpdReport: TypeAlias = FlextInfraModelsGates.JscpdReport
        JscpdScan: TypeAlias = FlextInfraModelsGates.JscpdScan
        JscpdSemantic: TypeAlias = FlextInfraModelsGates.JscpdSemantic
        JscpdStatistics: TypeAlias = FlextInfraModelsGates.JscpdStatistics
        JscpdStatisticsSummary: TypeAlias = FlextInfraModelsGates.JscpdStatisticsSummary
        MypyDiagnostic: TypeAlias = FlextInfraModelsGates.MypyDiagnostic
        ProjectDuplicationOverrides: TypeAlias = (
            FlextInfraModelsGates.ProjectDuplicationOverrides
        )
        PyreflyDiagnostic: TypeAlias = FlextInfraModelsGates.PyreflyDiagnostic
        PyreflyReport: TypeAlias = FlextInfraModelsGates.PyreflyReport
        PyrightDiagnostic: TypeAlias = FlextInfraModelsGates.PyrightDiagnostic
        PyrightPosition: TypeAlias = FlextInfraModelsGates.PyrightPosition
        PyrightRange: TypeAlias = FlextInfraModelsGates.PyrightRange
        PyrightReport: TypeAlias = FlextInfraModelsGates.PyrightReport
        PyrightSummary: TypeAlias = FlextInfraModelsGates.PyrightSummary
        SccFile: TypeAlias = FlextInfraModelsGates.SccFile
        SccLanguage: TypeAlias = FlextInfraModelsGates.SccLanguage
        SccReport: TypeAlias = FlextInfraModelsGates.SccReport
        GitAncestryRequest: TypeAlias = FlextInfraModelsGit.GitAncestryRequest
        GitBoolReport: TypeAlias = FlextInfraModelsGit.GitBoolReport
        GitBranchCreateRequest: TypeAlias = FlextInfraModelsGit.GitBranchCreateRequest
        GitBranchRequest: TypeAlias = FlextInfraModelsGit.GitBranchRequest
        GitBytesReport: TypeAlias = FlextInfraModelsGit.GitBytesReport
        GitCheckoutPathsRequest: TypeAlias = FlextInfraModelsGit.GitCheckoutPathsRequest
        GitCommitRequest: TypeAlias = FlextInfraModelsGit.GitCommitRequest
        GitCommitishRequest: TypeAlias = FlextInfraModelsGit.GitCommitishRequest
        GitDeleteRefRequest: TypeAlias = FlextInfraModelsGit.GitDeleteRefRequest
        GitFingerprintInputsReport: TypeAlias = (
            FlextInfraModelsGit.GitFingerprintInputsReport
        )
        GitIdentityReport: TypeAlias = FlextInfraModelsGit.GitIdentityReport
        GitIndexFileState: TypeAlias = FlextInfraModelsGit.GitIndexFileState
        GitIndexRetirementRequest: TypeAlias = (
            FlextInfraModelsGit.GitIndexRetirementRequest
        )
        GitIndexScope: TypeAlias = FlextInfraModelsGit.GitIndexScope
        GitLaneBead: TypeAlias = FlextInfraModelsGit.GitLaneBead
        GitLaneBeadMetadata: TypeAlias = FlextInfraModelsGit.GitLaneBeadMetadata
        GitLaneCoordinationPolicy: TypeAlias = (
            FlextInfraModelsGit.GitLaneCoordinationPolicy
        )
        GitLaneEvidence: TypeAlias = FlextInfraModelsGit.GitLaneEvidence
        GitLaneFacts: TypeAlias = FlextInfraModelsGit.GitLaneFacts
        GitLaneGovernance: TypeAlias = FlextInfraModelsGit.GitLaneGovernance
        GitLaneOwnershipReceipt: TypeAlias = FlextInfraModelsGit.GitLaneOwnershipReceipt
        GitLaneOwnershipRequest: TypeAlias = FlextInfraModelsGit.GitLaneOwnershipRequest
        GitLanePullRequest: TypeAlias = FlextInfraModelsGit.GitLanePullRequest
        GitLaneRef: TypeAlias = FlextInfraModelsGit.GitLaneRef
        GitLaneReport: TypeAlias = FlextInfraModelsGit.GitLaneReport
        GitLaneRequest: TypeAlias = FlextInfraModelsGit.GitLaneRequest
        GitLaneVerificationRequest: TypeAlias = (
            FlextInfraModelsGit.GitLaneVerificationRequest
        )
        GitLaneViolation: TypeAlias = FlextInfraModelsGit.GitLaneViolation
        GitMergeProbeRequest: TypeAlias = FlextInfraModelsGit.GitMergeProbeRequest
        GitMutationScope: TypeAlias = FlextInfraModelsGit.GitMutationScope
        GitNumstatReport: TypeAlias = FlextInfraModelsGit.GitNumstatReport
        GitOidListReport: TypeAlias = FlextInfraModelsGit.GitOidListReport
        GitOidReport: TypeAlias = FlextInfraModelsGit.GitOidReport
        GitPathPairRequest: TypeAlias = FlextInfraModelsGit.GitPathPairRequest
        GitPathsRequest: TypeAlias = FlextInfraModelsGit.GitPathsRequest
        GitPrimaryRootReport: TypeAlias = FlextInfraModelsGit.GitPrimaryRootReport
        GitPushRequest: TypeAlias = FlextInfraModelsGit.GitPushRequest
        GitRefHeadsReport: TypeAlias = FlextInfraModelsGit.GitRefHeadsReport
        GitRefHeadsRequest: TypeAlias = FlextInfraModelsGit.GitRefHeadsRequest
        GitRefRequest: TypeAlias = FlextInfraModelsGit.GitRefRequest
        GitRelativePathRequest: TypeAlias = FlextInfraModelsGit.GitRelativePathRequest
        GitRemoteBranchRequest: TypeAlias = FlextInfraModelsGit.GitRemoteBranchRequest
        GitRemoteRequest: TypeAlias = FlextInfraModelsGit.GitRemoteRequest
        GitRemoteUrlRequest: TypeAlias = FlextInfraModelsGit.GitRemoteUrlRequest
        GitRepoRequest: TypeAlias = FlextInfraModelsGit.GitRepoRequest
        GitRootReport: TypeAlias = FlextInfraModelsGit.GitRootReport
        GitSigningConfigObservation: TypeAlias = (
            FlextInfraModelsGit.GitSigningConfigObservation
        )
        GitSigningIdentityReport: TypeAlias = (
            FlextInfraModelsGit.GitSigningIdentityReport
        )
        GitStashDropRequest: TypeAlias = FlextInfraModelsGit.GitStashDropRequest
        GitStatusReport: TypeAlias = FlextInfraModelsGit.GitStatusReport
        GitStatusRequest: TypeAlias = FlextInfraModelsGit.GitStatusRequest
        GitSubmoduleContractRequest: TypeAlias = (
            FlextInfraModelsGit.GitSubmoduleContractRequest
        )
        GitTextReport: TypeAlias = FlextInfraModelsGit.GitTextReport
        GitTimestampReport: TypeAlias = FlextInfraModelsGit.GitTimestampReport
        GitTreeStats: TypeAlias = FlextInfraModelsGit.GitTreeStats
        GitUpdateIndexGitlinkRequest: TypeAlias = (
            FlextInfraModelsGit.GitUpdateIndexGitlinkRequest
        )
        GitWorktreeAddRequest: TypeAlias = FlextInfraModelsGit.GitWorktreeAddRequest
        GitWorktreeCheckpointPublication: TypeAlias = (
            FlextInfraModelsGit.GitWorktreeCheckpointPublication
        )
        GitWorktreeEntry: TypeAlias = FlextInfraModelsGit.GitWorktreeEntry
        GitWorktreeFileState: TypeAlias = FlextInfraModelsGit.GitWorktreeFileState
        GitWorktreeIndexEntry: TypeAlias = FlextInfraModelsGit.GitWorktreeIndexEntry
        GitWorktreeListReport: TypeAlias = FlextInfraModelsGit.GitWorktreeListReport
        GitWorktreeObservedContent: TypeAlias = (
            FlextInfraModelsGit.GitWorktreeObservedContent
        )
        GitWorktreeObservedFile: TypeAlias = FlextInfraModelsGit.GitWorktreeObservedFile
        GitWorktreeStateCheckpoint: TypeAlias = (
            FlextInfraModelsGit.GitWorktreeStateCheckpoint
        )
        GitWorktreeStateRequest: TypeAlias = FlextInfraModelsGit.GitWorktreeStateRequest
        GitWorktreeStateSnapshot: TypeAlias = (
            FlextInfraModelsGit.GitWorktreeStateSnapshot
        )
        MutationLockHolder: TypeAlias = FlextInfraModelsGit.MutationLockHolder
        LayoutFinding: TypeAlias = FlextInfraModelsLayout.LayoutFinding
        LayoutMoveSpec: TypeAlias = FlextInfraModelsLayout.LayoutMoveSpec
        LayoutProjectOverrideSpec: TypeAlias = (
            FlextInfraModelsLayout.LayoutProjectOverrideSpec
        )
        LayoutProjectReport: TypeAlias = FlextInfraModelsLayout.LayoutProjectReport
        LayoutRunReport: TypeAlias = FlextInfraModelsLayout.LayoutRunReport
        LayoutSpec: TypeAlias = FlextInfraModelsLayout.LayoutSpec
        SchemaRecord: TypeAlias = FlextInfraModelsMiseToolchainBase.SchemaRecord
        MiseToolchainRepairPlan: TypeAlias = (
            FlextInfraModelsMiseToolchainRepair.MiseToolchainRepairPlan
        )
        AbsoluteFilePathTextMixin: TypeAlias = (
            FlextInfraModelsMixins.AbsoluteFilePathTextMixin
        )
        CurrentImportMixin: TypeAlias = FlextInfraModelsMixins.CurrentImportMixin
        ErrorDetailMixin: TypeAlias = FlextInfraModelsMixins.ErrorDetailMixin
        FileLineViolationMixin: TypeAlias = (
            FlextInfraModelsMixins.FileLineViolationMixin
        )
        FilePathMixin: TypeAlias = FlextInfraModelsMixins.FilePathMixin
        ModuleSelectionMixin: TypeAlias = FlextInfraModelsMixins.ModuleSelectionMixin
        NamespaceSelectionMixin: TypeAlias = (
            FlextInfraModelsMixins.NamespaceSelectionMixin
        )
        NestedClassPathMixin: TypeAlias = FlextInfraModelsMixins.NestedClassPathMixin
        NonNegativeLineMixin: TypeAlias = FlextInfraModelsMixins.NonNegativeLineMixin
        PositiveLineMixin: TypeAlias = FlextInfraModelsMixins.PositiveLineMixin
        ProjectEntryNameMixin: TypeAlias = FlextInfraModelsMixins.ProjectEntryNameMixin
        ProjectNameMixin: TypeAlias = FlextInfraModelsMixins.ProjectNameMixin
        ProjectNamesListMixin: TypeAlias = FlextInfraModelsMixins.ProjectNamesListMixin
        ProjectNamesOptionalMixin: TypeAlias = (
            FlextInfraModelsMixins.ProjectNamesOptionalMixin
        )
        ReadMixin: TypeAlias = FlextInfraModelsMixins.ReadMixin
        RepositoryRootPathMixin: TypeAlias = (
            FlextInfraModelsMixins.RepositoryRootPathMixin
        )
        RequiredNonNegativeLineMixin: TypeAlias = (
            FlextInfraModelsMixins.RequiredNonNegativeLineMixin
        )
        ScopeMixin: TypeAlias = FlextInfraModelsMixins.ScopeMixin
        VersionTagMixin: TypeAlias = FlextInfraModelsMixins.VersionTagMixin
        WriteMixin: TypeAlias = FlextInfraModelsMixins.WriteMixin
        CommandContext: TypeAlias = FlextInfraModelsPromoted.CommandContext
        FrozenArbitrary: TypeAlias = FlextInfraModelsPromoted.FrozenArbitrary
        LintGateResult: TypeAlias = FlextInfraModelsPromoted.LintGateResult
        ProcessExit: TypeAlias = FlextInfraModelsPromoted.ProcessExit
        PromotedAliasTarget: TypeAlias = FlextInfraModelsPromoted.PromotedAliasTarget
        PromotedCommand: TypeAlias = FlextInfraModelsPromoted.PromotedCommand
        PromotedParam: TypeAlias = FlextInfraModelsPromoted.PromotedParam
        PromotedWorkspaceSpec: TypeAlias = (
            FlextInfraModelsPromoted.PromotedWorkspaceSpec
        )
        ProtectedFileEditRequest: TypeAlias = (
            FlextInfraModelsPromoted.ProtectedFileEditRequest
        )
        ProtectedSourceWriteRequest: TypeAlias = (
            FlextInfraModelsPromoted.ProtectedSourceWriteRequest
        )
        ProtectedSourceWritesRequest: TypeAlias = (
            FlextInfraModelsPromoted.ProtectedSourceWritesRequest
        )
        SummaryStats: TypeAlias = FlextInfraModelsPromoted.SummaryStats
        TransformStep: TypeAlias = FlextInfraModelsPromoted.TransformStep
        AccessorMigrationChange: TypeAlias = (
            FlextInfraModelsRefactor.AccessorMigrationChange
        )
        AccessorMigrationFile: TypeAlias = (
            FlextInfraModelsRefactor.AccessorMigrationFile
        )
        AccessorMigrationInput: TypeAlias = (
            FlextInfraModelsRefactor.AccessorMigrationInput
        )
        AccessorMigrationReport: TypeAlias = (
            FlextInfraModelsRefactor.AccessorMigrationReport
        )
        AccessorMigrationRule: TypeAlias = (
            FlextInfraModelsRefactor.AccessorMigrationRule
        )
        ApplyRenamesInput: TypeAlias = FlextInfraModelsRefactor.ApplyRenamesInput
        ApplyRenamesReport: TypeAlias = FlextInfraModelsRefactor.ApplyRenamesReport
        CensusInput: TypeAlias = FlextInfraModelsRefactor.CensusInput
        CensusOptions: TypeAlias = FlextInfraModelsRefactor.CensusOptions
        CodemodNativeGenerated: TypeAlias = (
            FlextInfraModelsRefactor.CodemodNativeGenerated
        )
        CodemodPackageExportsFacts: TypeAlias = (
            FlextInfraModelsRefactor.CodemodPackageExportsFacts
        )
        CodemodPrimitiveOwner: TypeAlias = (
            FlextInfraModelsRefactor.CodemodPrimitiveOwner
        )
        CodemodRule: TypeAlias = FlextInfraModelsRefactor.CodemodRule
        CodemodRulePlan: TypeAlias = FlextInfraModelsRefactor.CodemodRulePlan
        CodemodRuleset: TypeAlias = FlextInfraModelsRefactor.CodemodRuleset
        CodemodScopeFacts: TypeAlias = FlextInfraModelsRefactor.CodemodScopeFacts
        CodemodScopePartition: TypeAlias = (
            FlextInfraModelsRefactor.CodemodScopePartition
        )
        FileImportData: TypeAlias = FlextInfraModelsRefactor.FileImportData
        ImportLawPass: TypeAlias = FlextInfraModelsRefactor.ImportLawPass
        ImportLawScope: TypeAlias = FlextInfraModelsRefactor.ImportLawScope
        ModCommand: TypeAlias = FlextInfraModelsRefactor.ModCommand
        ModRuleRoute: TypeAlias = FlextInfraModelsRefactor.ModRuleRoute
        ModTextCommand: TypeAlias = FlextInfraModelsRefactor.ModTextCommand
        ModuleMoveCommand: TypeAlias = FlextInfraModelsRefactor.ModuleMoveCommand
        NamespaceRelocationRequest: TypeAlias = (
            FlextInfraModelsRefactor.NamespaceRelocationRequest
        )
        NamespaceRelocationState: TypeAlias = (
            FlextInfraModelsRefactor.NamespaceRelocationState
        )
        ParseFailureViolation: TypeAlias = (
            FlextInfraModelsRefactor.ParseFailureViolation
        )
        ParsedPythonModule: TypeAlias = FlextInfraModelsRefactor.ParsedPythonModule
        ProjectClassification: TypeAlias = (
            FlextInfraModelsRefactor.ProjectClassification
        )
        ProjectEnforcementReport: TypeAlias = (
            FlextInfraModelsRefactor.ProjectEnforcementReport
        )
        RefactorNamespaceEnforceInput: TypeAlias = (
            FlextInfraModelsRefactor.RefactorNamespaceEnforceInput
        )
        RefactorProjectInfo: TypeAlias = FlextInfraModelsRefactor.RefactorProjectInfo
        Result: TypeAlias = FlextInfraModelsRefactor.Result
        RopeRenameOptions: TypeAlias = FlextInfraModelsRefactor.RopeRenameOptions
        RuleDeltaOptions: TypeAlias = FlextInfraModelsRefactor.RuleDeltaOptions
        SemanticBehaviorOwners: TypeAlias = (
            FlextInfraModelsRefactor.SemanticBehaviorOwners
        )
        SemanticBehaviorResolution: TypeAlias = (
            FlextInfraModelsRefactor.SemanticBehaviorResolution
        )
        SemanticRenameDecision: TypeAlias = (
            FlextInfraModelsRefactor.SemanticRenameDecision
        )
        SemanticRenamePlan: TypeAlias = FlextInfraModelsRefactor.SemanticRenamePlan
        SemanticRenamePlanCommand: TypeAlias = (
            FlextInfraModelsRefactor.SemanticRenamePlanCommand
        )
        SemanticRenamePreviewCommand: TypeAlias = (
            FlextInfraModelsRefactor.SemanticRenamePreviewCommand
        )
        SemanticRenameSelection: TypeAlias = (
            FlextInfraModelsRefactor.SemanticRenameSelection
        )
        SemanticRenameSelections: TypeAlias = (
            FlextInfraModelsRefactor.SemanticRenameSelections
        )
        ViolationsEngineCoverage: TypeAlias = (
            FlextInfraModelsRefactor.ViolationsEngineCoverage
        )
        ViolationsRuleDelta: TypeAlias = FlextInfraModelsRefactor.ViolationsRuleDelta
        ViolationsRuleEvaluation: TypeAlias = (
            FlextInfraModelsRefactor.ViolationsRuleEvaluation
        )
        ViolationsSweepReport: TypeAlias = (
            FlextInfraModelsRefactor.ViolationsSweepReport
        )
        ViolationsSweepSources: TypeAlias = (
            FlextInfraModelsRefactor.ViolationsSweepSources
        )
        ViolationsSweepStage: TypeAlias = FlextInfraModelsRefactor.ViolationsSweepStage
        ViolationsTotals: TypeAlias = FlextInfraModelsRefactor.ViolationsTotals
        WorkspaceEnforcementReport: TypeAlias = (
            FlextInfraModelsRefactor.WorkspaceEnforcementReport
        )
        WrapperRewriteAccumulator: TypeAlias = (
            FlextInfraModelsRefactor.WrapperRewriteAccumulator
        )
        ArtifactExpectation: TypeAlias = FlextInfraModelsRelease.ArtifactExpectation
        BuildArtifact: TypeAlias = FlextInfraModelsRelease.BuildArtifact
        BuildPolicy: TypeAlias = FlextInfraModelsRelease.BuildPolicy
        BuildRecord: TypeAlias = FlextInfraModelsRelease.BuildRecord
        BuildReport: TypeAlias = FlextInfraModelsRelease.BuildReport
        GithubReleaseAsset: TypeAlias = FlextInfraModelsRelease.GithubReleaseAsset
        GithubReleaseAssets: TypeAlias = FlextInfraModelsRelease.GithubReleaseAssets
        GithubReleaseIdentity: TypeAlias = FlextInfraModelsRelease.GithubReleaseIdentity
        GithubReleaseInventory: TypeAlias = (
            FlextInfraModelsRelease.GithubReleaseInventory
        )
        ReleaseOptions: TypeAlias = FlextInfraModelsRelease.ReleaseOptions
        ReleasePhaseDispatchConfig: TypeAlias = (
            FlextInfraModelsRelease.ReleasePhaseDispatchConfig
        )
        ReleasePlan: TypeAlias = FlextInfraModelsRelease.ReleasePlan
        ReleaseRunCommand: TypeAlias = FlextInfraModelsRelease.ReleaseRunCommand
        SourceSnapshot: TypeAlias = FlextInfraModelsRelease.SourceSnapshot
        ClassInfo: TypeAlias = FlextInfraModelsRope.ClassInfo
        ConsolidatorScannedFile: TypeAlias = (
            FlextInfraModelsRope.ConsolidatorScannedFile
        )
        ConstantInfo: TypeAlias = FlextInfraModelsRope.ConstantInfo
        ExportOptions: TypeAlias = FlextInfraModelsRope.ExportOptions
        FacadeCensus: TypeAlias = FlextInfraModelsRope.FacadeCensus
        FamilyWrapperFlatten: TypeAlias = FlextInfraModelsRope.FamilyWrapperFlatten
        LogicalStatement: TypeAlias = FlextInfraModelsRope.LogicalStatement
        ModuleSemanticState: TypeAlias = FlextInfraModelsRope.ModuleSemanticState
        RopeAttributeReadProof: TypeAlias = FlextInfraModelsRope.RopeAttributeReadProof
        RopeInventoryRecordInput: TypeAlias = (
            FlextInfraModelsRope.RopeInventoryRecordInput
        )
        RopeModuleConvention: TypeAlias = FlextInfraModelsRope.RopeModuleConvention
        RopeProjectElection: TypeAlias = FlextInfraModelsRope.RopeProjectElection
        RopeRestructureRequest: TypeAlias = FlextInfraModelsRope.RopeRestructureRequest
        RopeSourceImport: TypeAlias = FlextInfraModelsRope.RopeSourceImport
        RopeWorkspaceSession: TypeAlias = FlextInfraModelsRope.RopeWorkspaceSession
        ScopeDefinition: TypeAlias = FlextInfraModelsRope.ScopeDefinition
        SourceBindingCollectorSpec: TypeAlias = (
            FlextInfraModelsRope.SourceBindingCollectorSpec
        )
        SourceBindingInventoryRequest: TypeAlias = (
            FlextInfraModelsRope.SourceBindingInventoryRequest
        )
        SourceClassDefinition: TypeAlias = FlextInfraModelsRope.SourceClassDefinition
        SourceClassReference: TypeAlias = FlextInfraModelsRope.SourceClassReference
        SourceScanRequest: TypeAlias = FlextInfraModelsRope.SourceScanRequest
        SubscriptRebind: TypeAlias = FlextInfraModelsRope.SubscriptRebind
        SymbolInfo: TypeAlias = FlextInfraModelsRope.SymbolInfo
        ClassMoveRequest: TypeAlias = FlextInfraModelsRopeMove.ClassMoveRequest
        ResolvedClassMove: TypeAlias = FlextInfraModelsRopeMove.ResolvedClassMove
        ModModuleQuarantine: TypeAlias = FlextInfraModelsScan.ModModuleQuarantine
        ModNativeRecord: TypeAlias = FlextInfraModelsScan.ModNativeRecord
        ModOccurrence: TypeAlias = FlextInfraModelsScan.ModOccurrence
        ModOccurrenceReport: TypeAlias = FlextInfraModelsScan.ModOccurrenceReport
        ModPhaseAdvance: TypeAlias = FlextInfraModelsScan.ModPhaseAdvance
        ModQuarantineExclusion: TypeAlias = FlextInfraModelsScan.ModQuarantineExclusion
        ModReplacementOffsets: TypeAlias = FlextInfraModelsScan.ModReplacementOffsets
        ModScanCounts: TypeAlias = FlextInfraModelsScan.ModScanCounts
        ModScanEvidence: TypeAlias = FlextInfraModelsScan.ModScanEvidence
        ModScanEvidenceReceipt: TypeAlias = FlextInfraModelsScan.ModScanEvidenceReceipt
        ModScanFinding: TypeAlias = FlextInfraModelsScan.ModScanFinding
        ModScanFindingReference: TypeAlias = (
            FlextInfraModelsScan.ModScanFindingReference
        )
        ModScanPublication: TypeAlias = FlextInfraModelsScan.ModScanPublication
        ModScanReport: TypeAlias = FlextInfraModelsScan.ModScanReport
        ModScanSourceContext: TypeAlias = FlextInfraModelsScan.ModScanSourceContext
        ModTextFinding: TypeAlias = FlextInfraModelsScan.ModTextFinding
        ModTextReport: TypeAlias = FlextInfraModelsScan.ModTextReport
        ModTextRule: TypeAlias = FlextInfraModelsScan.ModTextRule
        ScanResult: TypeAlias = FlextInfraModelsScan.ScanResult
        ScanViolation: TypeAlias = FlextInfraModelsScan.ScanViolation
        InfraSettings: TypeAlias = FlextInfraModelsSettings.InfraSettings
        SonarcloudAuthentication: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudAuthentication
        )
        SonarcloudIssue: TypeAlias = FlextInfraModelsSonarcloud.SonarcloudIssue
        SonarcloudIssueFieldValue: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudIssueFieldValue
        )
        SonarcloudIssuePaging: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudIssuePaging
        )
        SonarcloudIssueSearch: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudIssueSearch
        )
        SonarcloudSetting: TypeAlias = FlextInfraModelsSonarcloud.SonarcloudSetting
        SonarcloudSettingsPlan: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudSettingsPlan
        )
        SonarcloudSettingsValues: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudSettingsValues
        )
        SonarcloudSettingsWriteRequest: TypeAlias = (
            FlextInfraModelsSonarcloud.SonarcloudSettingsWriteRequest
        )
        TestmonCachePublication: TypeAlias = (
            FlextInfraModelsTestmon.TestmonCachePublication
        )
        TestmonCacheState: TypeAlias = FlextInfraModelsTestmon.TestmonCacheState
        TestmonRunAccounting: TypeAlias = FlextInfraModelsTestmon.TestmonRunAccounting
        AliasMigrationContext: TypeAlias = (
            FlextInfraModelsTransformers.AliasMigrationContext
        )
        ClassBlockLayout: TypeAlias = FlextInfraModelsTransformers.ClassBlockLayout
        CompatibilityAliasRewritePlan: TypeAlias = (
            FlextInfraModelsTransformers.CompatibilityAliasRewritePlan
        )
        DeclarationRelocationFinding: TypeAlias = (
            FlextInfraModelsTransformers.DeclarationRelocationFinding
        )
        FacadeNamespaceCutover: TypeAlias = (
            FlextInfraModelsTransformers.FacadeNamespaceCutover
        )
        FacadeNamespaceSite: TypeAlias = (
            FlextInfraModelsTransformers.FacadeNamespaceSite
        )
        HeaderInfo: TypeAlias = FlextInfraModelsTransformers.HeaderInfo
        HeaderSpan: TypeAlias = FlextInfraModelsTransformers.HeaderSpan
        PrivateImportRewritePlan: TypeAlias = (
            FlextInfraModelsTransformers.PrivateImportRewritePlan
        )
        SemanticBehaviorRewriteRequest: TypeAlias = (
            FlextInfraModelsTransformers.SemanticBehaviorRewriteRequest
        )
        SemanticFilePlan: TypeAlias = FlextInfraModelsTransformers.SemanticFilePlan
        SemanticMigrationEdit: TypeAlias = (
            FlextInfraModelsTransformers.SemanticMigrationEdit
        )
        SemanticPublicationOptions: TypeAlias = (
            FlextInfraModelsTransformers.SemanticPublicationOptions
        )
        SourceRewrite: TypeAlias = FlextInfraModelsTransformers.SourceRewrite
        Tier0ImportAnalysis: TypeAlias = (
            FlextInfraModelsTransformers.Tier0ImportAnalysis
        )
        DiagResult: TypeAlias = FlextInfraModelsCore.DiagResult
        FreshImportEntryPoints: TypeAlias = FlextInfraModelsCore.FreshImportEntryPoints
        FreshImportMetadata: TypeAlias = FlextInfraModelsCore.FreshImportMetadata
        FreshImportProbe: TypeAlias = FlextInfraModelsCore.FreshImportProbe
        InventoryReport: TypeAlias = FlextInfraModelsCore.InventoryReport
        NamespaceValidateCommand: TypeAlias = (
            FlextInfraModelsCore.NamespaceValidateCommand
        )
        PytestCollectionManifest: TypeAlias = (
            FlextInfraModelsCore.PytestCollectionManifest
        )
        PytestDiagnostics: TypeAlias = FlextInfraModelsCore.PytestDiagnostics
        PytestInvocation: TypeAlias = FlextInfraModelsCore.PytestInvocation
        PytestMarkdownAttempt: TypeAlias = FlextInfraModelsCore.PytestMarkdownAttempt
        PytestMarkdownCollection: TypeAlias = (
            FlextInfraModelsCore.PytestMarkdownCollection
        )
        PytestMarkdownItem: TypeAlias = FlextInfraModelsCore.PytestMarkdownItem
        PytestMarkdownOrigin: TypeAlias = FlextInfraModelsCore.PytestMarkdownOrigin
        PytestMarkdownReconciliation: TypeAlias = (
            FlextInfraModelsCore.PytestMarkdownReconciliation
        )
        PytestPhaseOutcome: TypeAlias = FlextInfraModelsCore.PytestPhaseOutcome
        PytestReportEvent: TypeAlias = FlextInfraModelsCore.PytestReportEvent
        PytestRunContext: TypeAlias = FlextInfraModelsCore.PytestRunContext
        PytestSelectionPlan: TypeAlias = FlextInfraModelsCore.PytestSelectionPlan
        PytestWarningEvent: TypeAlias = FlextInfraModelsCore.PytestWarningEvent
        SkillReportContext: TypeAlias = FlextInfraModelsCore.SkillReportContext
        SkillRuleEvaluationContext: TypeAlias = (
            FlextInfraModelsCore.SkillRuleEvaluationContext
        )
        StubAnalysisReport: TypeAlias = FlextInfraModelsCore.StubAnalysisReport
        ValidationReport: TypeAlias = FlextInfraModelsCore.ValidationReport
        CodegenSourceAuthority: TypeAlias = (
            FlextInfraModelsWorkspace.CodegenSourceAuthority
        )
        DirectUrlDirectoryInfo: TypeAlias = (
            FlextInfraModelsWorkspace.DirectUrlDirectoryInfo
        )
        DirectUrlReceipt: TypeAlias = FlextInfraModelsWorkspace.DirectUrlReceipt
        DirectUrlVcsInfo: TypeAlias = FlextInfraModelsWorkspace.DirectUrlVcsInfo
        EditableDirectUrl: TypeAlias = FlextInfraModelsWorkspace.EditableDirectUrl
        EnvironmentContractViolation: TypeAlias = (
            FlextInfraModelsWorkspace.EnvironmentContractViolation
        )
        FleetGapsReport: TypeAlias = FlextInfraModelsWorkspace.FleetGapsReport
        FleetPullRequest: TypeAlias = FlextInfraModelsWorkspace.FleetPullRequest
        FleetRepoGaps: TypeAlias = FlextInfraModelsWorkspace.FleetRepoGaps
        FlextEditableRequest: TypeAlias = FlextInfraModelsWorkspace.FlextEditableRequest
        FlextEditableSelection: TypeAlias = (
            FlextInfraModelsWorkspace.FlextEditableSelection
        )
        LockedDependency: TypeAlias = FlextInfraModelsWorkspace.LockedDependency
        LockedEnvironment: TypeAlias = FlextInfraModelsWorkspace.LockedEnvironment
        LockedPackage: TypeAlias = FlextInfraModelsWorkspace.LockedPackage
        LockedPackageSource: TypeAlias = FlextInfraModelsWorkspace.LockedPackageSource
        NativeBindingEvidence: TypeAlias = (
            FlextInfraModelsWorkspace.NativeBindingEvidence
        )
        NativeCodeEvidence: TypeAlias = FlextInfraModelsWorkspace.NativeCodeEvidence
        NativeFunctionObservationContext: TypeAlias = (
            FlextInfraModelsWorkspace.NativeFunctionObservationContext
        )
        NativeImportObservation: TypeAlias = (
            FlextInfraModelsWorkspace.NativeImportObservation
        )
        NativeImportReference: TypeAlias = (
            FlextInfraModelsWorkspace.NativeImportReference
        )
        NativeImportRequest: TypeAlias = FlextInfraModelsWorkspace.NativeImportRequest
        NativeObservationContext: TypeAlias = (
            FlextInfraModelsWorkspace.NativeObservationContext
        )
        ProjectInfo: TypeAlias = FlextInfraModelsWorkspace.ProjectInfo
        ProjectPyprojectState: TypeAlias = (
            FlextInfraModelsWorkspace.ProjectPyprojectState
        )
        PythonEnvironmentObservation: TypeAlias = (
            FlextInfraModelsWorkspace.PythonEnvironmentObservation
        )
        SubprojectLoadContext: TypeAlias = (
            FlextInfraModelsWorkspace.SubprojectLoadContext
        )
        WorkspaceOperationApplicability: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceOperationApplicability
        )
        WorkspaceOperationReceipt: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceOperationReceipt
        )
        WorkspaceOperationReport: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceOperationReport
        )
        WorkspaceOperationTarget: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceOperationTarget
        )
        WorkspaceProjectContext: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceProjectContext
        )
        WorkspaceRequest: TypeAlias = FlextInfraModelsWorkspace.WorkspaceRequest
        WorkspaceRuntimeContext: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceRuntimeContext
        )
        WorkspaceTestsRequest: TypeAlias = (
            FlextInfraModelsWorkspace.WorkspaceTestsRequest
        )
        WorkspaceBootstrapDependencies: TypeAlias = (
            FlextInfraModelsWorkspaceSnapshot.WorkspaceBootstrapDependencies
        )
        WorkspaceSnapshot: TypeAlias = (
            FlextInfraModelsWorkspaceSnapshot.WorkspaceSnapshot
        )
        WorkspaceSnapshotSource: TypeAlias = (
            FlextInfraModelsWorkspaceSnapshot.WorkspaceSnapshotSource
        )
        LintSnapshot: TypeAlias = FlextInfraModelsWorktree.LintSnapshot
        PruneAction: TypeAlias = FlextInfraModelsWorktree.PruneAction
        PrunePlan: TypeAlias = FlextInfraModelsWorktree.PrunePlan
        RepositoryDelta: TypeAlias = FlextInfraModelsWorktree.RepositoryDelta
        RepositoryWorktree: TypeAlias = FlextInfraModelsWorktree.RepositoryWorktree
        WorktreeCandidate: TypeAlias = FlextInfraModelsWorktree.WorktreeCandidate
        WorktreeFact: TypeAlias = FlextInfraModelsWorktree.WorktreeFact
        WorktreeFactsPolicy: TypeAlias = FlextInfraModelsWorktree.WorktreeFactsPolicy
        WorktreeFactsQuery: TypeAlias = FlextInfraModelsWorktree.WorktreeFactsQuery
        WorktreesReport: TypeAlias = FlextInfraModelsWorktree.WorktreesReport
        ArtifactRenderRoute: TypeAlias = FlextInfraModelsConfig.ArtifactRenderRoute
        BeadsConfigRenderSpec: TypeAlias = FlextInfraModelsConfig.BeadsConfigRenderSpec
        BeadsEndpointSpec: TypeAlias = FlextInfraModelsConfig.BeadsEndpointSpec
        BeadsMetadataRenderSpec: TypeAlias = (
            FlextInfraModelsConfig.BeadsMetadataRenderSpec
        )
        BeadsProjectSpec: TypeAlias = FlextInfraModelsConfig.BeadsProjectSpec
        BeadsToolSpec: TypeAlias = FlextInfraModelsConfig.BeadsToolSpec
        BootstrapRequirementsRenderSpec: TypeAlias = (
            FlextInfraModelsConfig.BootstrapRequirementsRenderSpec
        )
        BranchPolicySpec: TypeAlias = FlextInfraModelsConfig.BranchPolicySpec
        BuildConstraintSpec: TypeAlias = FlextInfraModelsConfig.BuildConstraintSpec
        CandidateBootstrapTargetSpec: TypeAlias = (
            FlextInfraModelsConfig.CandidateBootstrapTargetSpec
        )
        CandidateDependenciesSpec: TypeAlias = (
            FlextInfraModelsConfig.CandidateDependenciesSpec
        )
        CiPrivateDependencyAuthSpec: TypeAlias = (
            FlextInfraModelsConfig.CiPrivateDependencyAuthSpec
        )
        CiPrivateSubmoduleDeployKeySpec: TypeAlias = (
            FlextInfraModelsConfig.CiPrivateSubmoduleDeployKeySpec
        )
        CiPrivateSubmodulesSpec: TypeAlias = (
            FlextInfraModelsConfig.CiPrivateSubmodulesSpec
        )
        CiSuperprojectCheckoutSpec: TypeAlias = (
            FlextInfraModelsConfig.CiSuperprojectCheckoutSpec
        )
        CodegenArtifactScopeSpec: TypeAlias = (
            FlextInfraModelsConfig.CodegenArtifactScopeSpec
        )
        CodegenArtifactSpec: TypeAlias = FlextInfraModelsConfig.CodegenArtifactSpec
        CodegenAstGrepRendererSpec: TypeAlias = (
            FlextInfraModelsConfig.CodegenAstGrepRendererSpec
        )
        CodegenAstGrepSpec: TypeAlias = FlextInfraModelsConfig.CodegenAstGrepSpec
        CodegenBootstrapSource: TypeAlias = (
            FlextInfraModelsConfig.CodegenBootstrapSource
        )
        CodegenConfigSpec: TypeAlias = FlextInfraModelsConfig.CodegenConfigSpec
        CodegenConformRequest: TypeAlias = FlextInfraModelsConfig.CodegenConformRequest
        CodegenConformSurfaceContract: TypeAlias = (
            FlextInfraModelsConfig.CodegenConformSurfaceContract
        )
        CodegenGenerateRequest: TypeAlias = (
            FlextInfraModelsConfig.CodegenGenerateRequest
        )
        CodegenGovernedPlanRequest: TypeAlias = (
            FlextInfraModelsConfig.CodegenGovernedPlanRequest
        )
        CodegenInputs: TypeAlias = FlextInfraModelsConfig.CodegenInputs
        CodegenLayerProjection: TypeAlias = (
            FlextInfraModelsConfig.CodegenLayerProjection
        )
        CodegenLocCapSpec: TypeAlias = FlextInfraModelsConfig.CodegenLocCapSpec
        CodegenModesSpec: TypeAlias = FlextInfraModelsConfig.CodegenModesSpec
        CodegenPlanningFileEvidence: TypeAlias = (
            FlextInfraModelsConfig.CodegenPlanningFileEvidence
        )
        CodegenPlanningReport: TypeAlias = FlextInfraModelsConfig.CodegenPlanningReport
        CodegenPlanningRepositoryEvidence: TypeAlias = (
            FlextInfraModelsConfig.CodegenPlanningRepositoryEvidence
        )
        CodegenRenderInputs: TypeAlias = FlextInfraModelsConfig.CodegenRenderInputs
        CodegenRepositoryPlanTask: TypeAlias = (
            FlextInfraModelsConfig.CodegenRepositoryPlanTask
        )
        CodegenVscodeDeclarationDelta: TypeAlias = (
            FlextInfraModelsConfig.CodegenVscodeDeclarationDelta
        )
        CodegenVscodeSpec: TypeAlias = FlextInfraModelsConfig.CodegenVscodeSpec
        ConfigContract: TypeAlias = FlextInfraModelsConfig.ConfigContract
        ConfigDocumentInputs: TypeAlias = FlextInfraModelsConfig.ConfigDocumentInputs
        ConsolidationOutcome: TypeAlias = FlextInfraModelsConfig.ConsolidationOutcome
        CustomHandlerPolicy: TypeAlias = FlextInfraModelsConfig.CustomHandlerPolicy
        CustomHandlerPolicyOverride: TypeAlias = (
            FlextInfraModelsConfig.CustomHandlerPolicyOverride
        )
        DeclaredExclusionsSpec: TypeAlias = (
            FlextInfraModelsConfig.DeclaredExclusionsSpec
        )
        DependencyCommitSourceSpec: TypeAlias = (
            FlextInfraModelsConfig.DependencyCommitSourceSpec
        )
        DependencyEdgeSpec: TypeAlias = FlextInfraModelsConfig.DependencyEdgeSpec
        DependencyGroupDeclarations: TypeAlias = (
            FlextInfraModelsConfig.DependencyGroupDeclarations
        )
        DependencyGroupEntries: TypeAlias = (
            FlextInfraModelsConfig.DependencyGroupEntries
        )
        DependencyGroupInclude: TypeAlias = (
            FlextInfraModelsConfig.DependencyGroupInclude
        )
        DependencyManifestSpec: TypeAlias = (
            FlextInfraModelsConfig.DependencyManifestSpec
        )
        Directory: TypeAlias = FlextInfraModelsConfig.Directory
        DocsAuditOverridesSpec: TypeAlias = (
            FlextInfraModelsConfig.DocsAuditOverridesSpec
        )
        DocsAuditPolicySpec: TypeAlias = FlextInfraModelsConfig.DocsAuditPolicySpec
        DocsGithubRepoSpec: TypeAlias = FlextInfraModelsConfig.DocsGithubRepoSpec
        DocsOverviewPreviewLimitsSpec: TypeAlias = (
            FlextInfraModelsConfig.DocsOverviewPreviewLimitsSpec
        )
        ExternalConsumerSpec: TypeAlias = FlextInfraModelsConfig.ExternalConsumerSpec
        GitSubmoduleDeclaration: TypeAlias = (
            FlextInfraModelsConfig.GitSubmoduleDeclaration
        )
        GithubActionPinSpec: TypeAlias = FlextInfraModelsConfig.GithubActionPinSpec
        GitignoreRenderContext: TypeAlias = (
            FlextInfraModelsConfig.GitignoreRenderContext
        )
        GitignoreRenderSpec: TypeAlias = FlextInfraModelsConfig.GitignoreRenderSpec
        HostWorkspaceInventory: TypeAlias = (
            FlextInfraModelsConfig.HostWorkspaceInventory
        )
        HostWorkspaceInventoryEntry: TypeAlias = (
            FlextInfraModelsConfig.HostWorkspaceInventoryEntry
        )
        Infra: TypeAlias = FlextInfraModelsConfig.Infra
        MakeCiSpec: TypeAlias = FlextInfraModelsConfig.MakeCiSpec
        MakeCleanSpec: TypeAlias = FlextInfraModelsConfig.MakeCleanSpec
        MakeCommandContext: TypeAlias = FlextInfraModelsConfig.MakeCommandContext
        MakeDocsSpec: TypeAlias = FlextInfraModelsConfig.MakeDocsSpec
        MakeLifecycleStepSpec: TypeAlias = FlextInfraModelsConfig.MakeLifecycleStepSpec
        MakeOperationSpec: TypeAlias = FlextInfraModelsConfig.MakeOperationSpec
        MakeProjectCheckGateSpec: TypeAlias = (
            FlextInfraModelsConfig.MakeProjectCheckGateSpec
        )
        MakeRenderContext: TypeAlias = FlextInfraModelsConfig.MakeRenderContext
        MakeRuffSpec: TypeAlias = FlextInfraModelsConfig.MakeRuffSpec
        MakeSpec: TypeAlias = FlextInfraModelsConfig.MakeSpec
        MakeVerbSpec: TypeAlias = FlextInfraModelsConfig.MakeVerbSpec
        MakeWorkflowRequirementSpec: TypeAlias = (
            FlextInfraModelsConfig.MakeWorkflowRequirementSpec
        )
        MakeWorkflowStepSpec: TypeAlias = FlextInfraModelsConfig.MakeWorkflowStepSpec
        MakefileRenderSpec: TypeAlias = FlextInfraModelsConfig.MakefileRenderSpec
        ManagedFileOwnership: TypeAlias = FlextInfraModelsConfig.ManagedFileOwnership
        ManagedFileSpec: TypeAlias = FlextInfraModelsConfig.ManagedFileSpec
        MiseHttpToolOptions: TypeAlias = FlextInfraModelsConfig.MiseHttpToolOptions
        MisePostinstallOptions: TypeAlias = (
            FlextInfraModelsConfig.MisePostinstallOptions
        )
        MiseToolEntry: TypeAlias = FlextInfraModelsConfig.MiseToolEntry
        MiseToolVersionProbe: TypeAlias = FlextInfraModelsConfig.MiseToolVersionProbe
        MiseToolchainProofOptions: TypeAlias = (
            FlextInfraModelsConfig.MiseToolchainProofOptions
        )
        ModOwnerSpec: TypeAlias = FlextInfraModelsConfig.ModOwnerSpec
        MutationLockSpec: TypeAlias = FlextInfraModelsConfig.MutationLockSpec
        MypyCacheSpec: TypeAlias = FlextInfraModelsConfig.MypyCacheSpec
        ProfileSpec: TypeAlias = FlextInfraModelsConfig.ProfileSpec
        ProjectRenderContext: TypeAlias = FlextInfraModelsConfig.ProjectRenderContext
        ProjectSpec: TypeAlias = FlextInfraModelsConfig.ProjectSpec
        ProviderIdentitySpec: TypeAlias = FlextInfraModelsConfig.ProviderIdentitySpec
        RefactorConfigSpec: TypeAlias = FlextInfraModelsConfig.RefactorConfigSpec
        RefactorCsvCampaignsSpec: TypeAlias = (
            FlextInfraModelsConfig.RefactorCsvCampaignsSpec
        )
        ReleaseAutomationOverrideSpec: TypeAlias = (
            FlextInfraModelsConfig.ReleaseAutomationOverrideSpec
        )
        ReleaseAutomationSpec: TypeAlias = FlextInfraModelsConfig.ReleaseAutomationSpec
        ReleasePolicySpec: TypeAlias = FlextInfraModelsConfig.ReleasePolicySpec
        RenameCampaignSpec: TypeAlias = FlextInfraModelsConfig.RenameCampaignSpec
        RepositoryConformTarget: TypeAlias = (
            FlextInfraModelsConfig.RepositoryConformTarget
        )
        RepositoryDeclarationInputs: TypeAlias = (
            FlextInfraModelsConfig.RepositoryDeclarationInputs
        )
        RepositoryDeltaSpec: TypeAlias = FlextInfraModelsConfig.RepositoryDeltaSpec
        RepositoryPolicyOverlaySpec: TypeAlias = (
            FlextInfraModelsConfig.RepositoryPolicyOverlaySpec
        )
        RepositoryRef: TypeAlias = FlextInfraModelsConfig.RepositoryRef
        RepositorySourceSpec: TypeAlias = FlextInfraModelsConfig.RepositorySourceSpec
        RetiredProjectionSpec: TypeAlias = FlextInfraModelsConfig.RetiredProjectionSpec
        Root: TypeAlias = FlextInfraModelsConfig.Root
        RuffCacheSpec: TypeAlias = FlextInfraModelsConfig.RuffCacheSpec
        ScaffoldBuildSpec: TypeAlias = FlextInfraModelsConfig.ScaffoldBuildSpec
        ScaffoldConfigBaseSpec: TypeAlias = (
            FlextInfraModelsConfig.ScaffoldConfigBaseSpec
        )
        ScaffoldDependencyProfileSpec: TypeAlias = (
            FlextInfraModelsConfig.ScaffoldDependencyProfileSpec
        )
        ScaffoldGitignoreSectionSpec: TypeAlias = (
            FlextInfraModelsConfig.ScaffoldGitignoreSectionSpec
        )
        ScaffoldPingExampleSpec: TypeAlias = (
            FlextInfraModelsConfig.ScaffoldPingExampleSpec
        )
        ScaffoldProjectSpec: TypeAlias = FlextInfraModelsConfig.ScaffoldProjectSpec
        ScaffoldSpec: TypeAlias = FlextInfraModelsConfig.ScaffoldSpec
        ScriptDispatchSpec: TypeAlias = FlextInfraModelsConfig.ScriptDispatchSpec
        SonarcloudIssueExclusionSpec: TypeAlias = (
            FlextInfraModelsConfig.SonarcloudIssueExclusionSpec
        )
        SonarcloudSpec: TypeAlias = FlextInfraModelsConfig.SonarcloudSpec
        SourceScanSpec: TypeAlias = FlextInfraModelsConfig.SourceScanSpec
        StaticTextRenderSpec: TypeAlias = FlextInfraModelsConfig.StaticTextRenderSpec
        TemplateDeclarationSpec: TypeAlias = (
            FlextInfraModelsConfig.TemplateDeclarationSpec
        )
        TemplateEntrySpec: TypeAlias = FlextInfraModelsConfig.TemplateEntrySpec
        TemplatesSpec: TypeAlias = FlextInfraModelsConfig.TemplatesSpec
        TestmonCachePolicySpec: TypeAlias = (
            FlextInfraModelsConfig.TestmonCachePolicySpec
        )
        ToolchainSpec: TypeAlias = FlextInfraModelsConfig.ToolchainSpec
        UvEnvironmentPlan: TypeAlias = FlextInfraModelsConfig.UvEnvironmentPlan
        UvOverrideEntries: TypeAlias = FlextInfraModelsConfig.UvOverrideEntries
        UvOverridePackage: TypeAlias = FlextInfraModelsConfig.UvOverridePackage
        UvScopedOverride: TypeAlias = FlextInfraModelsConfig.UvScopedOverride
        WorkspaceBeadsServerSpec: TypeAlias = (
            FlextInfraModelsConfig.WorkspaceBeadsServerSpec
        )
        WorkspaceExclusionSpec: TypeAlias = (
            FlextInfraModelsConfig.WorkspaceExclusionSpec
        )
        WorkspaceIntegrationSpec: TypeAlias = (
            FlextInfraModelsConfig.WorkspaceIntegrationSpec
        )
        WorkspaceManifestSpec: TypeAlias = FlextInfraModelsConfig.WorkspaceManifestSpec
        WorkspaceSpec: TypeAlias = FlextInfraModelsConfig.WorkspaceSpec

        ModelProtocolContract: TypeAlias = (
            FlextInfraCodegen.ModelProtocolRenderContext.ModelProtocolContract
        )
        ListOp: TypeAlias = FlextInfraModelsDeps.DepsToml.ListOp
        MemberRequirements: TypeAlias = FlextInfraModelsDeps.DepsToml.MemberRequirements
        PhaseConfig: TypeAlias = FlextInfraModelsDeps.DepsToml.PhaseConfig
        RemoveOp: TypeAlias = FlextInfraModelsDeps.DepsToml.RemoveOp
        SetOp: TypeAlias = FlextInfraModelsDeps.DepsToml.SetOp
        PathRulesConfig: TypeAlias = FlextInfraModelsDeps.PyreflyConfig.PathRulesConfig
        ExecutionEnvironment: TypeAlias = (
            FlextInfraModelsDeps.PyrightConfig.ExecutionEnvironment
        )
        ExecutorEnvironmentSpec: TypeAlias = (
            FlextInfraModelsConfig.MakeSpec.ExecutorEnvironmentSpec
        )
        PytestScratchSpec: TypeAlias = FlextInfraModelsConfig.MakeSpec.PytestScratchSpec
        TestmonCacheSpec: TypeAlias = FlextInfraModelsConfig.MakeSpec.TestmonCacheSpec


m = FlextInfraModels
__all__: list[str] = ["FlextInfraModels", "m"]
