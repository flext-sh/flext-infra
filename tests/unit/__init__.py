# AUTO-GENERATED FILE — Regenerate with: make gen
"""Unit package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if _t.TYPE_CHECKING:
    from flext_tests import (
        c,
        d,
        e,
        h,
        m,
        p,
        r,
        s,
        t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x,
    )

    from tests.unit._utilities import (
        TestsFlextInfraUtilitiesdiscoveryconsolidated as TestsFlextInfraUtilitiesdiscoveryconsolidated,
        TestsFlextInfraUtilitiesformatting as TestsFlextInfraUtilitiesformatting,
        TestsFlextInfraUtilitiesProtectedEdit as TestsFlextInfraUtilitiesProtectedEdit,
        TestsFlextInfraUtilitiesRopeHooks as TestsFlextInfraUtilitiesRopeHooks,
        TestsFlextInfraUtilitiessafety as TestsFlextInfraUtilitiessafety,
        TestsFlextInfraUtilitiesscanning as TestsFlextInfraUtilitiesscanning,
    )
    from tests.unit.basemk import (
        TestsFlextInfraBasemkEngine as TestsFlextInfraBasemkEngine,
        TestsFlextInfraBasemkGenerator as TestsFlextInfraBasemkGenerator,
        TestsFlextInfraBasemkGeneratorEdgeCases as TestsFlextInfraBasemkGeneratorEdgeCases,
        TestsFlextInfraBasemkInit as TestsFlextInfraBasemkInit,
        TestsFlextInfraBasemkMain as TestsFlextInfraBasemkMain,
        TestsFlextInfraBasemkMakeContract as TestsFlextInfraBasemkMakeContract,
    )
    from tests.unit.check import (
        TestCheckIssueFormatted as TestCheckIssueFormatted,
        TestConfigFixerExecute as TestConfigFixerExecute,
        TestConfigFixerProcessFile as TestConfigFixerProcessFile,
        TestConfigFixerPublicBehavior as TestConfigFixerPublicBehavior,
        TestConfigFixerRun as TestConfigFixerRun,
        TestConfigFixerToArray as TestConfigFixerToArray,
        TestExtendedRunnerExtras as TestExtendedRunnerExtras,
        TestFlextInfraCheck as TestFlextInfraCheck,
        TestFlextInfraConfigFixer as TestFlextInfraConfigFixer,
        TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
        TestGateErrorReportingPublicBehavior as TestGateErrorReportingPublicBehavior,
        TestProjectResultProperties as TestProjectResultProperties,
        TestRunCommandGateParsing as TestRunCommandGateParsing,
        TestRunnerPublicBehavior as TestRunnerPublicBehavior,
        TestRunProjectsPublicBehavior as TestRunProjectsPublicBehavior,
        TestsExtendedProjectRunners as TestsExtendedProjectRunners,
        TestWorkspaceCheckCLI as TestWorkspaceCheckCLI,
        TestWorkspaceCheckCli as TestWorkspaceCheckCli,
        TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
        TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.cli_what_selector_tests import (
        TestsFlextInfraCliWhatSelector as TestsFlextInfraCliWhatSelector,
    )
    from tests.unit.codegen import (
        TestAllDirectoriesScanned as TestAllDirectoriesScanned,
        TestCheckOnlyMode as TestCheckOnlyMode,
        TestEdgeCases as TestEdgeCases,
        TestExcludedDirectories as TestExcludedDirectories,
        TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
        TestGenerateFile as TestGenerateFile,
        TestGenerateTypeChecking as TestGenerateTypeChecking,
        TestRunRuffFix as TestRunRuffFix,
        TestsFlextInfraLazyInitHelpers as TestsFlextInfraLazyInitHelpers,
        TestsFlextInfraLazyInitTransforms as TestsFlextInfraLazyInitTransforms,
    )
    from tests.unit.container import (
        TestsFlextInfraContainerInfraContainer as TestsFlextInfraContainerInfraContainer,
    )
    from tests.unit.deps import (
        TestsFlextInfraDepsDetectionClassify as TestsFlextInfraDepsDetectionClassify,
        TestsFlextInfraDepsDetectionDeptry as TestsFlextInfraDepsDetectionDeptry,
        TestsFlextInfraDepsDetectionDiscover as TestsFlextInfraDepsDetectionDiscover,
        TestsFlextInfraDepsDetectionModels as TestsFlextInfraDepsDetectionModels,
        TestsFlextInfraDepsDetectionTypings as TestsFlextInfraDepsDetectionTypings,
        TestsFlextInfraDepsDetectionTypingsFlow as TestsFlextInfraDepsDetectionTypingsFlow,
        TestsFlextInfraDepsDetectionUncovered as TestsFlextInfraDepsDetectionUncovered,
        TestsFlextInfraDepsDetectorDetect as TestsFlextInfraDepsDetectorDetect,
        TestsFlextInfraDepsDetectorDetectFailures as TestsFlextInfraDepsDetectorDetectFailures,
        TestsFlextInfraDepsDetectorInit as TestsFlextInfraDepsDetectorInit,
        TestsFlextInfraDepsDetectorMain as TestsFlextInfraDepsDetectorMain,
        TestsFlextInfraDepsDetectorModels as TestsFlextInfraDepsDetectorModels,
        TestsFlextInfraDepsDetectorReport as TestsFlextInfraDepsDetectorReport,
        TestsFlextInfraDepsDetectorReportFlags as TestsFlextInfraDepsDetectorReportFlags,
        TestsFlextInfraDepsExtraPathsSync as TestsFlextInfraDepsExtraPathsSync,
        TestsFlextInfraDepsInit as TestsFlextInfraDepsInit,
        TestsFlextInfraDepsInternalSyncDiscovery as TestsFlextInfraDepsInternalSyncDiscovery,
        TestsFlextInfraDepsInternalSyncDiscoveryEdge as TestsFlextInfraDepsInternalSyncDiscoveryEdge,
        TestsFlextInfraDepsInternalSyncMain as TestsFlextInfraDepsInternalSyncMain,
        TestsFlextInfraDepsInternalSyncResolve as TestsFlextInfraDepsInternalSyncResolve,
        TestsFlextInfraDepsInternalSyncSync as TestsFlextInfraDepsInternalSyncSync,
        TestsFlextInfraDepsInternalSyncSyncEdge as TestsFlextInfraDepsInternalSyncSyncEdge,
        TestsFlextInfraDepsInternalSyncSyncEdgeMore as TestsFlextInfraDepsInternalSyncSyncEdgeMore,
        TestsFlextInfraDepsInternalSyncUpdate as TestsFlextInfraDepsInternalSyncUpdate,
        TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge as TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge,
        TestsFlextInfraDepsInternalSyncValidation as TestsFlextInfraDepsInternalSyncValidation,
        TestsFlextInfraDepsInternalSyncWorkspace as TestsFlextInfraDepsInternalSyncWorkspace,
        TestsFlextInfraDepsMainDispatch as TestsFlextInfraDepsMainDispatch,
        TestsFlextInfraDepsModernizerComments as TestsFlextInfraDepsModernizerComments,
        TestsFlextInfraDepsModernizerConsolidate as TestsFlextInfraDepsModernizerConsolidate,
        TestsFlextInfraDepsModernizerCoverage as TestsFlextInfraDepsModernizerCoverage,
        TestsFlextInfraDepsModernizerHelpers as TestsFlextInfraDepsModernizerHelpers,
        TestsFlextInfraDepsModernizerMain as TestsFlextInfraDepsModernizerMain,
        TestsFlextInfraDepsModernizerMainExtra as TestsFlextInfraDepsModernizerMainExtra,
        TestsFlextInfraDepsModernizerMypy as TestsFlextInfraDepsModernizerMypy,
        TestsFlextInfraDepsModernizerPyright as TestsFlextInfraDepsModernizerPyright,
        TestsFlextInfraDepsModernizerPytest as TestsFlextInfraDepsModernizerPytest,
        TestsFlextInfraDepsModernizerTooling as TestsFlextInfraDepsModernizerTooling,
        TestsFlextInfraDepsModernizerWorkspace as TestsFlextInfraDepsModernizerWorkspace,
        TestsFlextInfraDepsPathSyncInit as TestsFlextInfraDepsPathSyncInit,
        TestsFlextInfraDepsPathSyncMain as TestsFlextInfraDepsPathSyncMain,
        TestsFlextInfraDepsPathSyncMainEdges as TestsFlextInfraDepsPathSyncMainEdges,
        TestsFlextInfraDepsPathSyncMainMore as TestsFlextInfraDepsPathSyncMainMore,
        TestsFlextInfraDepsPathSyncMainProjectObj as TestsFlextInfraDepsPathSyncMainProjectObj,
        TestsFlextInfraDepsPathSyncRewriteDeps as TestsFlextInfraDepsPathSyncRewriteDeps,
        TestsFlextInfraDepsPathSyncRewritePep621 as TestsFlextInfraDepsPathSyncRewritePep621,
        TestsFlextInfraDepsPathSyncRewritePoetry as TestsFlextInfraDepsPathSyncRewritePoetry,
        TestsFlextInfraExtraPathsManager as TestsFlextInfraExtraPathsManager,
        TestsFlextInfraModernizerPyrefly as TestsFlextInfraModernizerPyrefly,
    )
    from tests.unit.discovery import (
        TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases as TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases,
    )
    from tests.unit.docs import (
        TestAuditorBrokenLinks as TestAuditorBrokenLinks,
        TestAuditorCore as TestAuditorCore,
        TestAuditorForbiddenTerms as TestAuditorForbiddenTerms,
        TestAuditorNormalize as TestAuditorNormalize,
        TestAuditorScope as TestAuditorScope,
        TestAuditorToMarkdown as TestAuditorToMarkdown,
        TestBuilderCore as TestBuilderCore,
        TestIterMarkdownFiles as TestIterMarkdownFiles,
        TestLoadAuditBudgets as TestLoadAuditBudgets,
        TestSelectedProjectNames as TestSelectedProjectNames,
    )
    from tests.unit.fixtures import (
        deptry_report_payload as deptry_report_payload,
        models_resource as models_resource,
        modernizer_workspace as modernizer_workspace,
        modernizer_workspace_with_projects as modernizer_workspace_with_projects,
        real_docs_project as real_docs_project,
        real_makefile_project as real_makefile_project,
        real_python_package as real_python_package,
        real_toml_project as real_toml_project,
        real_workspace as real_workspace,
        rope_workspace as rope_workspace,
        services_resource as services_resource,
        tool_config_document as tool_config_document,
    )
    from tests.unit.fixtures_git import real_git_repo as real_git_repo
    from tests.unit.io import (
        TestsFlextInfraIoInfraTerminalDetection as TestsFlextInfraIoInfraTerminalDetection,
    )
    from tests.unit.refactor import (
        EngineSafetyStub as EngineSafetyStub,
        FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
        TestsFlextInfraRefactorCensusPreviewCache as TestsFlextInfraRefactorCensusPreviewCache,
        TestsFlextInfraRefactorInfraRefactorClassAndPropagation as TestsFlextInfraRefactorInfraRefactorClassAndPropagation,
        TestsFlextInfraRefactorInfraRefactorClassPlacement as TestsFlextInfraRefactorInfraRefactorClassPlacement,
        TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow as TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow,
        TestsFlextInfraRefactorInfraRefactorEngine as TestsFlextInfraRefactorInfraRefactorEngine,
        TestsFlextInfraRefactorInfraRefactorImportModernizer as TestsFlextInfraRefactorInfraRefactorImportModernizer,
        TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations as TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations,
        TestsFlextInfraRefactorInfraRefactorMigrateToClassMro as TestsFlextInfraRefactorInfraRefactorMigrateToClassMro,
        TestsFlextInfraRefactorInfraRefactorMroCompleteness as TestsFlextInfraRefactorInfraRefactorMroCompleteness,
        TestsFlextInfraRefactorInfraRefactorNamespaceAliases as TestsFlextInfraRefactorInfraRefactorNamespaceAliases,
        TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer as TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer,
        TestsFlextInfraRefactorInfraRefactorNamespaceMoves as TestsFlextInfraRefactorInfraRefactorNamespaceMoves,
        TestsFlextInfraRefactorInfraRefactorPatternCorrections as TestsFlextInfraRefactorInfraRefactorPatternCorrections,
        TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules as TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules,
        TestsFlextInfraRefactorInfraRefactorProjectClassifier as TestsFlextInfraRefactorInfraRefactorProjectClassifier,
        TestsFlextInfraRefactorInfraRefactorSafety as TestsFlextInfraRefactorInfraRefactorSafety,
        TestsFlextInfraRefactorInfraRefactorTypingUnifier as TestsFlextInfraRefactorInfraRefactorTypingUnifier,
        TestsFlextInfraRefactorMainCli as TestsFlextInfraRefactorMainCli,
    )
    from tests.unit.release import (
        TestsFlextInfraReleaseDag as TestsFlextInfraReleaseDag,
    )
    from tests.unit.runner_service import RealSubprocessRunner as RealSubprocessRunner
    from tests.unit.test_infra_constants_core import (
        TestsFlextInfraInfraConstantsCore as TestsFlextInfraInfraConstantsCore,
    )
    from tests.unit.test_infra_constants_extra import (
        TestsFlextInfraInfraConstantsExtra as TestsFlextInfraInfraConstantsExtra,
    )
    from tests.unit.test_infra_main import (
        TestsFlextInfraInfraMain as TestsFlextInfraInfraMain,
    )
    from tests.unit.test_infra_maintenance_cli import (
        TestsFlextInfraInfraMaintenanceCli as TestsFlextInfraInfraMaintenanceCli,
    )
    from tests.unit.test_infra_maintenance_init import (
        TestsFlextInfraInfraMaintenanceInit as TestsFlextInfraInfraMaintenanceInit,
    )
    from tests.unit.test_infra_maintenance_main import (
        TestsFlextInfraInfraMaintenanceMain as TestsFlextInfraInfraMaintenanceMain,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestsFlextInfraInfraMaintenancePythonVersion as TestsFlextInfraInfraMaintenancePythonVersion,
    )
    from tests.unit.test_infra_paths import (
        TestsFlextInfraInfraPaths as TestsFlextInfraInfraPaths,
    )
    from tests.unit.test_infra_patterns_core import (
        TestsFlextInfraInfraPatternsCore as TestsFlextInfraInfraPatternsCore,
    )
    from tests.unit.test_infra_patterns_extra import (
        TestsFlextInfraInfraPatternsExtra as TestsFlextInfraInfraPatternsExtra,
    )
    from tests.unit.test_infra_protocols import (
        TestsFlextInfraInfraProtocols as TestsFlextInfraInfraProtocols,
    )
    from tests.unit.test_infra_public_api import (
        TestsFlextInfraPublicApi as TestsFlextInfraPublicApi,
    )
    from tests.unit.test_infra_refactor_rope_migrations import (
        TestsFlextInfraInfraRefactorRopeMigrations as TestsFlextInfraInfraRefactorRopeMigrations,
    )
    from tests.unit.test_infra_reporting_core import (
        TestsFlextInfraInfraReportingCore as TestsFlextInfraInfraReportingCore,
    )
    from tests.unit.test_infra_reporting_extra import (
        TestsFlextInfraInfraReportingExtra as TestsFlextInfraInfraReportingExtra,
    )
    from tests.unit.test_infra_rope_imports import (
        TestsFlextInfraRopeImports as TestsFlextInfraRopeImports,
    )
    from tests.unit.test_infra_rope_service import (
        TestsFlextInfraInfraRopeService as TestsFlextInfraInfraRopeService,
    )
    from tests.unit.test_infra_selection import (
        TestsFlextInfraInfraSelection as TestsFlextInfraInfraSelection,
    )
    from tests.unit.test_infra_typings import (
        TestsFlextInfraInfraTypings as TestsFlextInfraInfraTypings,
    )
    from tests.unit.test_infra_utilities import (
        TestsFlextInfraInfraUtilities as TestsFlextInfraInfraUtilities,
    )
    from tests.unit.test_infra_version_core import (
        TestsFlextInfraInfraVersionCore as TestsFlextInfraInfraVersionCore,
    )
    from tests.unit.test_infra_version_extra import (
        TestsFlextInfraInfraVersionExtra as TestsFlextInfraInfraVersionExtra,
    )
    from tests.unit.test_infra_versioning import (
        TestsFlextInfraInfraVersioning as TestsFlextInfraInfraVersioning,
    )
    from tests.unit.test_infra_workspace_detector import (
        TestsFlextInfraInfraWorkspaceDetector as TestsFlextInfraInfraWorkspaceDetector,
    )
    from tests.unit.test_infra_workspace_migrator import (
        TestsFlextInfraInfraWorkspaceMigrator as TestsFlextInfraInfraWorkspaceMigrator,
    )
    from tests.unit.test_infra_workspace_migrator_deps import (
        TestsFlextInfraInfraWorkspaceMigratorDeps as TestsFlextInfraInfraWorkspaceMigratorDeps,
    )
    from tests.unit.test_infra_workspace_migrator_dryrun import (
        TestsFlextInfraInfraWorkspaceMigratorDryrun as TestsFlextInfraInfraWorkspaceMigratorDryrun,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestsFlextInfraInfraWorkspaceMigratorInternal as TestsFlextInfraInfraWorkspaceMigratorInternal,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestsFlextInfraInfraWorkspaceOrchestrator as TestsFlextInfraInfraWorkspaceOrchestrator,
    )
    from tests.unit.transformers import (
        TestsFlextInfraTransformersCliModernizer as TestsFlextInfraTransformersCliModernizer,
        TestsFlextInfraTransformersInfraTransformerClassNesting as TestsFlextInfraTransformersInfraTransformerClassNesting,
        TestsFlextInfraTransformersInfraTransformerHelperConsolidation as TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
        TestsFlextInfraTransformersInfraTransformerNestedClassPropagation as TestsFlextInfraTransformersInfraTransformerNestedClassPropagation,
        TestsFlextInfraTransformersLoggingModernizer as TestsFlextInfraTransformersLoggingModernizer,
        TestsFlextInfraTransformersPatternModernizer as TestsFlextInfraTransformersPatternModernizer,
        TestsFlextInfraTransformersPydanticModernizer as TestsFlextInfraTransformersPydanticModernizer,
        TestsFlextInfraTransformersResultDiModernizer as TestsFlextInfraTransformersResultDiModernizer,
        TestsFlextInfraTransformersTestsModernizer as TestsFlextInfraTransformersTestsModernizer,
    )
    from tests.unit.validate import (
        TestFlextInfraNamespaceValidator as TestFlextInfraNamespaceValidator,
        TestValidateCli as TestValidateCli,
    )
    from tests.unit.workspace import (
        TestsFlextInfraWorkspaceMain as TestsFlextInfraWorkspaceMain,
        TestsFlextInfraWorkspaceMakefileDryRun as TestsFlextInfraWorkspaceMakefileDryRun,
        TestsFlextInfraWorkspaceMakefileGenerator as TestsFlextInfraWorkspaceMakefileGenerator,
        TestsFlextInfraWorkspaceSync as TestsFlextInfraWorkspaceSync,
    )
    from tests.unit.workspace_factory import (
        TestsFlextInfraWorkspaceFactory as TestsFlextInfraWorkspaceFactory,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._utilities",
        ".basemk",
        ".check",
        ".codegen",
        ".container",
        ".deps",
        ".discovery",
        ".docs",
        ".github",
        ".io",
        ".refactor",
        ".release",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    build_lazy_import_map(
        {
            "._utilities.test_discovery_consolidated": (
                "TestsFlextInfraUtilitiesdiscoveryconsolidated",
            ),
            "._utilities.test_formatting": ("TestsFlextInfraUtilitiesformatting",),
            "._utilities.test_protected_edit": (
                "TestsFlextInfraUtilitiesProtectedEdit",
            ),
            "._utilities.test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
            "._utilities.test_safety": ("TestsFlextInfraUtilitiessafety",),
            "._utilities.test_scanning": ("TestsFlextInfraUtilitiesscanning",),
            ".basemk.test_engine": ("TestsFlextInfraBasemkEngine",),
            ".basemk.test_generator": ("TestsFlextInfraBasemkGenerator",),
            ".basemk.test_generator_edge_cases": (
                "TestsFlextInfraBasemkGeneratorEdgeCases",
            ),
            ".basemk.test_init": ("TestsFlextInfraBasemkInit",),
            ".basemk.test_main": ("TestsFlextInfraBasemkMain",),
            ".basemk.test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
            ".check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
            ".check.extended_config_fixer_errors_tests": (
                "TestConfigFixerPublicBehavior",
            ),
            ".check.extended_config_fixer_tests": (
                "TestConfigFixerExecute",
                "TestConfigFixerProcessFile",
                "TestConfigFixerRun",
                "TestConfigFixerToArray",
            ),
            ".check.extended_error_reporting_tests": (
                "TestGateErrorReportingPublicBehavior",
            ),
            ".check.extended_models_tests": (
                "TestCheckIssueFormatted",
                "TestProjectResultProperties",
                "TestRunCommandGateParsing",
                "TestWorkspaceCheckerErrorSummary",
            ),
            ".check.extended_project_runners_tests": ("TestsExtendedProjectRunners",),
            ".check.extended_resolve_gates_tests": (
                "TestWorkspaceCheckerResolveGates",
            ),
            ".check.extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
            ".check.extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
            ".check.extended_runners_tests": ("TestRunnerPublicBehavior",),
            ".check.init_tests": ("TestFlextInfraCheck",),
            ".check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
            ".check.tests_cli": ("TestWorkspaceCheckCli",),
            ".check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
            ".cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
            ".codegen.lazy_init_generation_tests": (
                "TestGenerateFile",
                "TestGenerateTypeChecking",
                "TestRunRuffFix",
            ),
            ".codegen.lazy_init_helpers_tests": ("TestsFlextInfraLazyInitHelpers",),
            ".codegen.lazy_init_tests": (
                "TestAllDirectoriesScanned",
                "TestCheckOnlyMode",
                "TestEdgeCases",
                "TestExcludedDirectories",
            ),
            ".codegen.lazy_init_transforms_tests": (
                "TestsFlextInfraLazyInitTransforms",
            ),
            ".codegen.scaffolder_naming_tests": (
                "TestGeneratedClassNamingConvention",
                "TestGeneratedFilesAreValidPython",
            ),
            ".container.test_infra_container": (
                "TestsFlextInfraContainerInfraContainer",
            ),
            ".deps.test_detection_classify": ("TestsFlextInfraDepsDetectionClassify",),
            ".deps.test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
            ".deps.test_detection_discover": ("TestsFlextInfraDepsDetectionDiscover",),
            ".deps.test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
            ".deps.test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
            ".deps.test_detection_typings_flow": (
                "TestsFlextInfraDepsDetectionTypingsFlow",
            ),
            ".deps.test_detection_uncovered": (
                "TestsFlextInfraDepsDetectionUncovered",
            ),
            ".deps.test_detector_detect": ("TestsFlextInfraDepsDetectorDetect",),
            ".deps.test_detector_detect_failures": (
                "TestsFlextInfraDepsDetectorDetectFailures",
            ),
            ".deps.test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
            ".deps.test_detector_main": ("TestsFlextInfraDepsDetectorMain",),
            ".deps.test_detector_models": ("TestsFlextInfraDepsDetectorModels",),
            ".deps.test_detector_report": ("TestsFlextInfraDepsDetectorReport",),
            ".deps.test_detector_report_flags": (
                "TestsFlextInfraDepsDetectorReportFlags",
            ),
            ".deps.test_extra_paths_manager": ("TestsFlextInfraExtraPathsManager",),
            ".deps.test_extra_paths_sync": ("TestsFlextInfraDepsExtraPathsSync",),
            ".deps.test_init": ("TestsFlextInfraDepsInit",),
            ".deps.test_internal_sync_discovery": (
                "TestsFlextInfraDepsInternalSyncDiscovery",
            ),
            ".deps.test_internal_sync_discovery_edge": (
                "TestsFlextInfraDepsInternalSyncDiscoveryEdge",
            ),
            ".deps.test_internal_sync_main": ("TestsFlextInfraDepsInternalSyncMain",),
            ".deps.test_internal_sync_resolve": (
                "TestsFlextInfraDepsInternalSyncResolve",
            ),
            ".deps.test_internal_sync_sync": ("TestsFlextInfraDepsInternalSyncSync",),
            ".deps.test_internal_sync_sync_edge": (
                "TestsFlextInfraDepsInternalSyncSyncEdge",
            ),
            ".deps.test_internal_sync_sync_edge_more": (
                "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
            ),
            ".deps.test_internal_sync_update": (
                "TestsFlextInfraDepsInternalSyncUpdate",
            ),
            ".deps.test_internal_sync_update_checkout_edge": (
                "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
            ),
            ".deps.test_internal_sync_validation": (
                "TestsFlextInfraDepsInternalSyncValidation",
            ),
            ".deps.test_internal_sync_workspace": (
                "TestsFlextInfraDepsInternalSyncWorkspace",
            ),
            ".deps.test_main_dispatch": ("TestsFlextInfraDepsMainDispatch",),
            ".deps.test_modernizer_comments": (
                "TestsFlextInfraDepsModernizerComments",
            ),
            ".deps.test_modernizer_consolidate": (
                "TestsFlextInfraDepsModernizerConsolidate",
            ),
            ".deps.test_modernizer_coverage": (
                "TestsFlextInfraDepsModernizerCoverage",
            ),
            ".deps.test_modernizer_helpers": ("TestsFlextInfraDepsModernizerHelpers",),
            ".deps.test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
            ".deps.test_modernizer_main_extra": (
                "TestsFlextInfraDepsModernizerMainExtra",
            ),
            ".deps.test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
            ".deps.test_modernizer_pyrefly": ("TestsFlextInfraModernizerPyrefly",),
            ".deps.test_modernizer_pyright": ("TestsFlextInfraDepsModernizerPyright",),
            ".deps.test_modernizer_pytest": ("TestsFlextInfraDepsModernizerPytest",),
            ".deps.test_modernizer_tooling": ("TestsFlextInfraDepsModernizerTooling",),
            ".deps.test_modernizer_workspace": (
                "TestsFlextInfraDepsModernizerWorkspace",
            ),
            ".deps.test_path_sync_init": ("TestsFlextInfraDepsPathSyncInit",),
            ".deps.test_path_sync_main": ("TestsFlextInfraDepsPathSyncMain",),
            ".deps.test_path_sync_main_edges": (
                "TestsFlextInfraDepsPathSyncMainEdges",
            ),
            ".deps.test_path_sync_main_more": ("TestsFlextInfraDepsPathSyncMainMore",),
            ".deps.test_path_sync_main_project_obj": (
                "TestsFlextInfraDepsPathSyncMainProjectObj",
            ),
            ".deps.test_path_sync_rewrite_deps": (
                "TestsFlextInfraDepsPathSyncRewriteDeps",
            ),
            ".deps.test_path_sync_rewrite_pep621": (
                "TestsFlextInfraDepsPathSyncRewritePep621",
            ),
            ".deps.test_path_sync_rewrite_poetry": (
                "TestsFlextInfraDepsPathSyncRewritePoetry",
            ),
            ".discovery.test_infra_discovery_edge_cases": (
                "TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases",
            ),
            ".docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
            ".docs.auditor_links_tests": (
                "TestAuditorBrokenLinks",
                "TestAuditorToMarkdown",
            ),
            ".docs.auditor_scope_tests": (
                "TestAuditorForbiddenTerms",
                "TestAuditorScope",
            ),
            ".docs.auditor_tests": (
                "TestAuditorCore",
                "TestAuditorNormalize",
            ),
            ".docs.builder_tests": ("TestBuilderCore",),
            ".docs.shared_iter_tests": (
                "TestIterMarkdownFiles",
                "TestSelectedProjectNames",
            ),
            ".fixtures": (
                "deptry_report_payload",
                "models_resource",
                "modernizer_workspace",
                "modernizer_workspace_with_projects",
                "real_docs_project",
                "real_makefile_project",
                "real_python_package",
                "real_toml_project",
                "real_workspace",
                "rope_workspace",
                "services_resource",
                "tool_config_document",
            ),
            ".fixtures_git": ("real_git_repo",),
            ".io.test_infra_terminal_detection": (
                "TestsFlextInfraIoInfraTerminalDetection",
            ),
            ".refactor.test_infra_refactor_census_preview_cache": (
                "TestsFlextInfraRefactorCensusPreviewCache",
            ),
            ".refactor.test_infra_refactor_class_and_propagation": (
                "TestsFlextInfraRefactorInfraRefactorClassAndPropagation",
            ),
            ".refactor.test_infra_refactor_class_placement": (
                "TestsFlextInfraRefactorInfraRefactorClassPlacement",
            ),
            ".refactor.test_infra_refactor_cli_models_workflow": (
                "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
            ),
            ".refactor.test_infra_refactor_engine": (
                "TestsFlextInfraRefactorInfraRefactorEngine",
            ),
            ".refactor.test_infra_refactor_import_modernizer": (
                "TestsFlextInfraRefactorInfraRefactorImportModernizer",
            ),
            ".refactor.test_infra_refactor_legacy_and_annotations": (
                "TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations",
            ),
            ".refactor.test_infra_refactor_migrate_to_class_mro": (
                "TestsFlextInfraRefactorInfraRefactorMigrateToClassMro",
            ),
            ".refactor.test_infra_refactor_mro_completeness": (
                "TestsFlextInfraRefactorInfraRefactorMroCompleteness",
            ),
            ".refactor.test_infra_refactor_namespace_aliases": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceAliases",
            ),
            ".refactor.test_infra_refactor_namespace_enforcer": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer",
            ),
            ".refactor.test_infra_refactor_namespace_moves": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
            ),
            ".refactor.test_infra_refactor_pattern_corrections": (
                "TestsFlextInfraRefactorInfraRefactorPatternCorrections",
            ),
            ".refactor.test_infra_refactor_policy_family_rules": (
                "TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules",
            ),
            ".refactor.test_infra_refactor_project_classifier": (
                "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
            ),
            ".refactor.test_infra_refactor_safety": (
                "EngineSafetyStub",
                "TestsFlextInfraRefactorInfraRefactorSafety",
            ),
            ".refactor.test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
                "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
            ),
            ".refactor.test_main_cli": ("TestsFlextInfraRefactorMainCli",),
            ".release.test_release_dag": ("TestsFlextInfraReleaseDag",),
            ".runner_service": ("RealSubprocessRunner",),
            ".test_infra_constants_core": ("TestsFlextInfraInfraConstantsCore",),
            ".test_infra_constants_extra": ("TestsFlextInfraInfraConstantsExtra",),
            ".test_infra_main": ("TestsFlextInfraInfraMain",),
            ".test_infra_maintenance_cli": ("TestsFlextInfraInfraMaintenanceCli",),
            ".test_infra_maintenance_init": ("TestsFlextInfraInfraMaintenanceInit",),
            ".test_infra_maintenance_main": ("TestsFlextInfraInfraMaintenanceMain",),
            ".test_infra_maintenance_python_version": (
                "TestsFlextInfraInfraMaintenancePythonVersion",
            ),
            ".test_infra_paths": ("TestsFlextInfraInfraPaths",),
            ".test_infra_patterns_core": ("TestsFlextInfraInfraPatternsCore",),
            ".test_infra_patterns_extra": ("TestsFlextInfraInfraPatternsExtra",),
            ".test_infra_protocols": ("TestsFlextInfraInfraProtocols",),
            ".test_infra_public_api": ("TestsFlextInfraPublicApi",),
            ".test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".test_infra_reporting_core": ("TestsFlextInfraInfraReportingCore",),
            ".test_infra_reporting_extra": ("TestsFlextInfraInfraReportingExtra",),
            ".test_infra_rope_imports": ("TestsFlextInfraRopeImports",),
            ".test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".test_infra_selection": ("TestsFlextInfraInfraSelection",),
            ".test_infra_typings": ("TestsFlextInfraInfraTypings",),
            ".test_infra_utilities": ("TestsFlextInfraInfraUtilities",),
            ".test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".test_infra_versioning": ("TestsFlextInfraInfraVersioning",),
            ".test_infra_workspace_detector": (
                "TestsFlextInfraInfraWorkspaceDetector",
            ),
            ".test_infra_workspace_migrator": (
                "TestsFlextInfraInfraWorkspaceMigrator",
            ),
            ".test_infra_workspace_migrator_deps": (
                "TestsFlextInfraInfraWorkspaceMigratorDeps",
            ),
            ".test_infra_workspace_migrator_dryrun": (
                "TestsFlextInfraInfraWorkspaceMigratorDryrun",
            ),
            ".test_infra_workspace_migrator_errors": (
                "test_infra_workspace_migrator_errors",
            ),
            ".test_infra_workspace_migrator_internal": (
                "TestsFlextInfraInfraWorkspaceMigratorInternal",
            ),
            ".test_infra_workspace_migrator_pyproject": (
                "test_infra_workspace_migrator_pyproject",
            ),
            ".test_infra_workspace_orchestrator": (
                "TestsFlextInfraInfraWorkspaceOrchestrator",
            ),
            ".test_mro_service_base_alias": ("test_mro_service_base_alias",),
            ".test_version_diag": ("test_version_diag",),
            ".test_version_diag2": ("test_version_diag2",),
            ".transformers.test_infra_transformer_class_nesting": (
                "TestsFlextInfraTransformersInfraTransformerClassNesting",
            ),
            ".transformers.test_infra_transformer_cli_modernizer": (
                "TestsFlextInfraTransformersCliModernizer",
            ),
            ".transformers.test_infra_transformer_helper_consolidation": (
                "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
            ),
            ".transformers.test_infra_transformer_logging_modernizer": (
                "TestsFlextInfraTransformersLoggingModernizer",
            ),
            ".transformers.test_infra_transformer_nested_class_propagation": (
                "TestsFlextInfraTransformersInfraTransformerNestedClassPropagation",
            ),
            ".transformers.test_infra_transformer_pattern_modernizer": (
                "TestsFlextInfraTransformersPatternModernizer",
            ),
            ".transformers.test_infra_transformer_pydantic_modernizer": (
                "TestsFlextInfraTransformersPydanticModernizer",
            ),
            ".transformers.test_infra_transformer_result_di_modernizer": (
                "TestsFlextInfraTransformersResultDiModernizer",
            ),
            ".transformers.test_infra_transformer_tests_modernizer": (
                "TestsFlextInfraTransformersTestsModernizer",
            ),
            ".validate.main_cli_tests": ("TestValidateCli",),
            ".validate.namespace_validator_tests": (
                "TestFlextInfraNamespaceValidator",
            ),
            ".workspace.test_main": ("TestsFlextInfraWorkspaceMain",),
            ".workspace.test_makefile_dry_run": (
                "TestsFlextInfraWorkspaceMakefileDryRun",
            ),
            ".workspace.test_makefile_generator": (
                "TestsFlextInfraWorkspaceMakefileGenerator",
            ),
            ".workspace.test_sync": ("TestsFlextInfraWorkspaceSync",),
            ".workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
