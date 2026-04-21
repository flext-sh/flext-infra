# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if _t.TYPE_CHECKING:
    from flext_tests import td, tf, tk, tm, tv

    from flext_infra import d, e, h, r, s, x
    from tests._constants.domain import TestsFlextInfraConstantsDomain
    from tests._constants.fixtures import TestsFlextInfraConstantsFixtures
    from tests.constants import TestsFlextInfraConstants, c
    from tests.integration.test_infra_integration import TestInfraIntegration
    from tests.integration.test_refactor_nesting_idempotency import TestIdempotency
    from tests.integration.test_refactor_nesting_performance import (
        TestPerformanceBenchmarks,
    )
    from tests.integration.test_refactor_nesting_project import TestProjectLevelRefactor
    from tests.integration.test_refactor_nesting_workspace import (
        TestWorkspaceLevelRefactor,
    )
    from tests.integration.test_refactor_policy_mro import TestRefactorPolicyMRO
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.refactor.test_rope_semantic import (
        TestFindDefinitionOffset,
        TestGetClassBases,
        TestGetClassMethods,
        TestGetModuleClasses,
        TestGetModuleImports,
    )
    from tests.typings import TestsFlextInfraTypes, t
    from tests.unit._utilities.test_discovery_consolidated import (
        TestsFlextInfraUtilitiesDiscoveryConsolidated,
    )
    from tests.unit._utilities.test_formatting import (
        TestsFlextInfraUtilitiesFormattingRunRuffFix,
    )
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels
    from tests.unit.basemk.test_init import TestFlextInfraBaseMk
    from tests.unit.check.extended_cli_entry_tests import TestWorkspaceCheckCLI
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPublicBehavior,
    )
    from tests.unit.check.extended_config_fixer_tests import (
        TestConfigFixerExecute,
        TestConfigFixerProcessFile,
        TestConfigFixerRun,
        TestConfigFixerToArray,
    )
    from tests.unit.check.extended_error_reporting_tests import (
        TestGateErrorReportingPublicBehavior,
    )
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import (
        TestsExtendedProjectRunners,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.check.extended_run_projects_tests import (
        TestRunProjectsPublicBehavior,
    )
    from tests.unit.check.extended_runners_extra_tests import TestExtendedRunnerExtras
    from tests.unit.check.extended_runners_tests import TestRunnerPublicBehavior
    from tests.unit.check.init_tests import TestFlextInfraCheck
    from tests.unit.check.pyrefly_tests import TestFlextInfraConfigFixer
    from tests.unit.check.tests_cli import TestWorkspaceCheckCli
    from tests.unit.check.workspace_tests import TestFlextInfraWorkspaceChecker
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestRunRuffFix,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestsFlextInfraLazyInitHelpers,
    )
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestsFlextInfraLazyInitTransforms,
    )
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions,
        TestInfraMroPattern,
        TestInfraServiceRetrieval,
    )
    from tests.unit.deps.test_detection_classify import (
        TestBuildProjectReport,
        TestClassifyIssues,
        TestDetectionUncoveredLinesClassify,
    )
    from tests.unit.deps.test_detection_deptry import (
        TestDiscoverProjectPathsDeptry,
        TestRunDeptry,
    )
    from tests.unit.deps.test_detection_discover import (
        TestDiscoverProjectPathsSelection,
    )
    from tests.unit.deps.test_detection_models import (
        TestFlextInfraDependencyDetectionService,
        TestFlextInfraModelsDependencyDetection,
        TestToInfraValue,
    )
    from tests.unit.deps.test_detection_typings import (
        TestLoadDependencyLimits,
        TestRunMypyStubHints,
    )
    from tests.unit.deps.test_detection_typings_flow import TestDetectionTypingsFlow
    from tests.unit.deps.test_detection_uncovered import TestDetectionUncoveredLines
    from tests.unit.deps.test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )
    from tests.unit.deps.test_detector_detect_failures import TestDetectorRunFailures
    from tests.unit.deps.test_detector_init import (
        TestFlextInfraRuntimeDevDependencyDetectorInit,
    )
    from tests.unit.deps.test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction,
    )
    from tests.unit.deps.test_detector_models import (
        TestFlextInfraModelsDependencyDetector,
    )
    from tests.unit.deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )
    from tests.unit.deps.test_detector_report_flags import TestDetectorReportFlags
    from tests.unit.deps.test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestSyncOne,
    )
    from tests.unit.deps.test_init import TestFlextInfraDeps
    from tests.unit.deps.test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestCollectInternalDepsEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_main import TestMain
    from tests.unit.deps.test_internal_sync_sync import TestSync
    from tests.unit.deps.test_internal_sync_sync_edge import TestSyncMethodEdgeCases
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestSyncMethodEdgeCasesMore,
    )
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestResolveInternalRepoName,
        TestValidateGitRefEdgeCases,
    )
    from tests.unit.deps.test_main import TestPublicDepsSurface
    from tests.unit.deps.test_main_dispatch import TestDepsGroupEntry
    from tests.unit.deps.test_modernizer_comments import TestInjectCommentsPhase
    from tests.unit.deps.test_modernizer_consolidate import TestConsolidateGroupsPhase
    from tests.unit.deps.test_modernizer_coverage import TestEnsureCoverageConfigPhase
    from tests.unit.deps.test_modernizer_main import TestFlextInfraPyprojectModernizer
    from tests.unit.deps.test_modernizer_main_extra import (
        TestFlextInfraPyprojectModernizerEdgeCases,
    )
    from tests.unit.deps.test_modernizer_mypy import TestDepsModernizerMypy
    from tests.unit.deps.test_modernizer_pyrefly import TestEnsurePyreflyConfigPhase
    from tests.unit.deps.test_modernizer_pyright import TestDepsModernizerPyright
    from tests.unit.deps.test_modernizer_pytest import TestEnsurePytestConfigPhase
    from tests.unit.deps.test_modernizer_tooling import TestDepsModernizerTooling
    from tests.unit.deps.test_modernizer_workspace import (
        TestFlextInfraPyprojectModernizerWorkspace,
    )
    from tests.unit.deps.test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
    )
    from tests.unit.deps.test_path_sync_rewrite_deps import TestRewriteDepPaths
    from tests.unit.deps.test_path_sync_rewrite_pep621 import TestRewritePep621
    from tests.unit.deps.test_path_sync_rewrite_poetry import TestRewritePoetry
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines,
    )
    from tests.unit.docs.auditor_budgets_tests import TestLoadAuditBudgets
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorToMarkdown,
    )
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms,
        TestAuditorScope,
    )
    from tests.unit.docs.auditor_tests import TestAuditorCore, TestAuditorNormalize
    from tests.unit.docs.builder_tests import TestBuilderCore
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles,
        TestSelectedProjectNames,
    )
    from tests.unit.fixtures import (
        deptry_report_payload,
        modernizer_workspace,
        modernizer_workspace_with_projects,
        real_docs_project,
        real_makefile_project,
        real_python_package,
        real_toml_project,
        real_workspace,
        tool_config_document,
    )
    from tests.unit.fixtures_git import real_git_repo
    from tests.unit.refactor.test_infra_refactor_safety import EngineSafetyStub
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        FlextInfraRefactorTypingUnificationRule,
    )
    from tests.unit.refactor.test_main_cli import TestFlextInfraRefactorMainCli
    from tests.unit.runner_service import RealSubprocessRunner
    from tests.unit.scenarios import (
        DependencyScenario,
        DependencyScenarios,
        GitScenario,
        GitScenarios,
        SubprocessScenario,
        SubprocessScenarios,
        WorkspaceScenario,
        WorkspaceScenarios,
    )
    from tests.unit.test_infra_constants_core import (
        TestFlextInfraConstantsExcludedNamespace,
        TestFlextInfraConstantsFilesNamespace,
        TestFlextInfraConstantsGatesNamespace,
        TestFlextInfraConstantsPathsNamespace,
        TestFlextInfraConstantsStatusNamespace,
    )
    from tests.unit.test_infra_constants_extra import (
        TestFlextInfraConstantsAlias,
        TestFlextInfraConstantsCheckNamespace,
        TestFlextInfraConstantsConsistency,
        TestFlextInfraConstantsEncodingNamespace,
        TestFlextInfraConstantsGithubNamespace,
        TestFlextInfraConstantsImmutability,
    )
    from tests.unit.test_infra_init_lazy_core import TestFlextInfraInitLazyLoading
    from tests.unit.test_infra_maintenance_init import TestFlextInfraMaintenance
    from tests.unit.test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestEnforcerExecute,
        TestEnsurePythonVersionFile,
        TestPublicProjectDiscovery,
        TestReadRequiredMinor,
        TestWorkspaceRoot,
    )
    from tests.unit.test_infra_paths import TestFlextInfraPathResolver
    from tests.unit.test_infra_patterns_core import (
        TestFlextInfraPatternsMarkdown,
        TestFlextInfraPatternsTooling,
    )
    from tests.unit.test_infra_patterns_extra import (
        TestFlextInfraPatternsEdgeCases,
        TestFlextInfraTypesPatternsPattern,
    )
    from tests.unit.test_infra_protocols import TestFlextInfraProtocolsImport
    from tests.unit.test_infra_refactor_rope_migrations import (
        TestNestedClassPropagationRopeMigration,
        TestSymbolPropagatorRopeMigration,
    )
    from tests.unit.test_infra_reporting_core import TestFlextInfraReportingServiceCore
    from tests.unit.test_infra_reporting_extra import (
        TestFlextInfraReportingServiceExtra,
    )
    from tests.unit.test_infra_rope_service import TestFlextInfraRopeWorkspace
    from tests.unit.test_infra_selection import TestFlextInfraUtilitiesSelection
    from tests.unit.test_infra_typings import (
        TestInfraTypingAdapters,
        TestInfraTypingGuards,
    )
    from tests.unit.test_infra_utilities import TestFlextInfraUtilitiesImport
    from tests.unit.test_infra_version_core import TestFlextInfraVersionClass
    from tests.unit.test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo,
    )
    from tests.unit.test_infra_workspace_detector import TestWorkspaceDetector
    from tests.unit.test_infra_workspace_init import TestFlextInfraWorkspace
    from tests.unit.test_infra_workspace_migrator_deps import (
        TestWorkspaceMigratorDependencyBehavior,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestMigratorPublicBehavior,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestOrchestratorBasic,
        TestOrchestratorFailures,
        TestOrchestratorGateNormalization,
    )
    from tests.unit.transformers.test_infra_transformer_helper_consolidation import (
        TestHelperConsolidationTransformer,
    )
    from tests.unit.validate.main_cli_tests import TestValidateCli
    from tests.unit.validate.namespace_validator_tests import (
        TestFlextInfraNamespaceValidator,
    )
    from tests.unit.workspace_factory import WorkspaceFactory
    from tests.unit.workspace_scenarios import (
        BrokenScenario,
        EmptyScenario,
        FullScenario,
        MinimalScenario,
    )
    from tests.utilities import TestsFlextInfraUtilities, u
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._constants",
        ".integration",
        ".refactor",
        ".unit",
    ),
    build_lazy_import_map(
        {
            "._constants.domain": ("TestsFlextInfraConstantsDomain",),
            "._constants.fixtures": ("TestsFlextInfraConstantsFixtures",),
            ".constants": (
                "TestsFlextInfraConstants",
                "c",
            ),
            ".integration.test_infra_integration": ("TestInfraIntegration",),
            ".integration.test_refactor_nesting_idempotency": ("TestIdempotency",),
            ".integration.test_refactor_nesting_performance": (
                "TestPerformanceBenchmarks",
            ),
            ".integration.test_refactor_nesting_project": ("TestProjectLevelRefactor",),
            ".integration.test_refactor_nesting_workspace": (
                "TestWorkspaceLevelRefactor",
            ),
            ".integration.test_refactor_policy_mro": ("TestRefactorPolicyMRO",),
            ".models": (
                "TestsFlextInfraModels",
                "m",
            ),
            ".protocols": (
                "TestsFlextInfraProtocols",
                "p",
            ),
            ".refactor.test_rope_semantic": (
                "TestFindDefinitionOffset",
                "TestGetClassBases",
                "TestGetClassMethods",
                "TestGetModuleClasses",
                "TestGetModuleImports",
            ),
            ".typings": (
                "TestsFlextInfraTypes",
                "t",
            ),
            ".unit._utilities.test_discovery_consolidated": (
                "TestsFlextInfraUtilitiesDiscoveryConsolidated",
            ),
            ".unit._utilities.test_formatting": (
                "TestsFlextInfraUtilitiesFormattingRunRuffFix",
            ),
            ".unit._utilities.test_safety": (
                "TestSafetyCheckpoint",
                "TestSafetyRollback",
            ),
            ".unit._utilities.test_scanning": ("TestScanModels",),
            ".unit.basemk.test_init": ("TestFlextInfraBaseMk",),
            ".unit.check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
            ".unit.check.extended_config_fixer_errors_tests": (
                "TestConfigFixerPublicBehavior",
            ),
            ".unit.check.extended_config_fixer_tests": (
                "TestConfigFixerExecute",
                "TestConfigFixerProcessFile",
                "TestConfigFixerRun",
                "TestConfigFixerToArray",
            ),
            ".unit.check.extended_error_reporting_tests": (
                "TestGateErrorReportingPublicBehavior",
            ),
            ".unit.check.extended_models_tests": (
                "TestCheckIssueFormatted",
                "TestProjectResultProperties",
                "TestWorkspaceCheckerErrorSummary",
            ),
            ".unit.check.extended_project_runners_tests": (
                "TestsExtendedProjectRunners",
            ),
            ".unit.check.extended_resolve_gates_tests": (
                "TestWorkspaceCheckerParseGateCSV",
                "TestWorkspaceCheckerResolveGates",
            ),
            ".unit.check.extended_run_projects_tests": (
                "TestRunProjectsPublicBehavior",
            ),
            ".unit.check.extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
            ".unit.check.extended_runners_tests": ("TestRunnerPublicBehavior",),
            ".unit.check.init_tests": ("TestFlextInfraCheck",),
            ".unit.check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
            ".unit.check.tests_cli": ("TestWorkspaceCheckCli",),
            ".unit.check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
            ".unit.codegen.lazy_init_generation_tests": (
                "TestGenerateFile",
                "TestGenerateTypeChecking",
                "TestRunRuffFix",
            ),
            ".unit.codegen.lazy_init_helpers_tests": (
                "TestsFlextInfraLazyInitHelpers",
            ),
            ".unit.codegen.lazy_init_tests": (
                "TestAllDirectoriesScanned",
                "TestCheckOnlyMode",
                "TestEdgeCases",
                "TestExcludedDirectories",
            ),
            ".unit.codegen.lazy_init_transforms_tests": (
                "TestsFlextInfraLazyInitTransforms",
            ),
            ".unit.codegen.scaffolder_naming_tests": (
                "TestGeneratedClassNamingConvention",
                "TestGeneratedFilesAreValidPython",
            ),
            ".unit.container.test_infra_container": (
                "TestInfraContainerFunctions",
                "TestInfraMroPattern",
                "TestInfraServiceRetrieval",
            ),
            ".unit.deps.test_detection_classify": (
                "TestBuildProjectReport",
                "TestClassifyIssues",
                "TestDetectionUncoveredLinesClassify",
            ),
            ".unit.deps.test_detection_deptry": (
                "TestDiscoverProjectPathsDeptry",
                "TestRunDeptry",
            ),
            ".unit.deps.test_detection_discover": (
                "TestDiscoverProjectPathsSelection",
            ),
            ".unit.deps.test_detection_models": (
                "TestFlextInfraDependencyDetectionService",
                "TestFlextInfraModelsDependencyDetection",
                "TestToInfraValue",
            ),
            ".unit.deps.test_detection_typings": (
                "TestLoadDependencyLimits",
                "TestRunMypyStubHints",
            ),
            ".unit.deps.test_detection_typings_flow": ("TestDetectionTypingsFlow",),
            ".unit.deps.test_detection_uncovered": ("TestDetectionUncoveredLines",),
            ".unit.deps.test_detector_detect": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
            ),
            ".unit.deps.test_detector_detect_failures": ("TestDetectorRunFailures",),
            ".unit.deps.test_detector_init": (
                "TestFlextInfraRuntimeDevDependencyDetectorInit",
            ),
            ".unit.deps.test_detector_main": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
                "TestMainFunction",
            ),
            ".unit.deps.test_detector_models": (
                "TestFlextInfraModelsDependencyDetector",
            ),
            ".unit.deps.test_detector_report": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
            ),
            ".unit.deps.test_detector_report_flags": ("TestDetectorReportFlags",),
            ".unit.deps.test_extra_paths_manager": (
                "TestConstants",
                "TestFlextInfraExtraPathsManager",
                "TestSyncOne",
            ),
            ".unit.deps.test_init": ("TestFlextInfraDeps",),
            ".unit.deps.test_internal_sync_discovery": (
                "TestCollectInternalDeps",
                "TestParseGitmodules",
                "TestParseRepoMap",
            ),
            ".unit.deps.test_internal_sync_discovery_edge": (
                "TestCollectInternalDepsEdgeCases",
            ),
            ".unit.deps.test_internal_sync_main": ("TestMain",),
            ".unit.deps.test_internal_sync_sync": ("TestSync",),
            ".unit.deps.test_internal_sync_sync_edge": ("TestSyncMethodEdgeCases",),
            ".unit.deps.test_internal_sync_sync_edge_more": (
                "TestSyncMethodEdgeCasesMore",
            ),
            ".unit.deps.test_internal_sync_update_checkout_edge": (
                "TestEnsureCheckoutEdgeCases",
            ),
            ".unit.deps.test_internal_sync_validation": (
                "TestFlextInfraInternalDependencySyncService",
                "TestIsRelativeTo",
                "TestOwnerFromRemoteUrl",
                "TestResolveInternalRepoName",
                "TestValidateGitRefEdgeCases",
            ),
            ".unit.deps.test_main": ("TestPublicDepsSurface",),
            ".unit.deps.test_main_dispatch": ("TestDepsGroupEntry",),
            ".unit.deps.test_modernizer_comments": ("TestInjectCommentsPhase",),
            ".unit.deps.test_modernizer_consolidate": ("TestConsolidateGroupsPhase",),
            ".unit.deps.test_modernizer_coverage": ("TestEnsureCoverageConfigPhase",),
            ".unit.deps.test_modernizer_main": ("TestFlextInfraPyprojectModernizer",),
            ".unit.deps.test_modernizer_main_extra": (
                "TestFlextInfraPyprojectModernizerEdgeCases",
            ),
            ".unit.deps.test_modernizer_mypy": ("TestDepsModernizerMypy",),
            ".unit.deps.test_modernizer_pyrefly": ("TestEnsurePyreflyConfigPhase",),
            ".unit.deps.test_modernizer_pyright": ("TestDepsModernizerPyright",),
            ".unit.deps.test_modernizer_pytest": ("TestEnsurePytestConfigPhase",),
            ".unit.deps.test_modernizer_tooling": ("TestDepsModernizerTooling",),
            ".unit.deps.test_modernizer_workspace": (
                "TestFlextInfraPyprojectModernizerWorkspace",
            ),
            ".unit.deps.test_path_sync_init": (
                "TestDetectMode",
                "TestFlextInfraDependencyPathSync",
                "TestPathSyncEdgeCases",
            ),
            ".unit.deps.test_path_sync_rewrite_deps": ("TestRewriteDepPaths",),
            ".unit.deps.test_path_sync_rewrite_pep621": ("TestRewritePep621",),
            ".unit.deps.test_path_sync_rewrite_poetry": ("TestRewritePoetry",),
            ".unit.discovery.test_infra_discovery_edge_cases": (
                "TestFlextInfraDiscoveryServiceUncoveredLines",
            ),
            ".unit.docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
            ".unit.docs.auditor_links_tests": (
                "TestAuditorBrokenLinks",
                "TestAuditorToMarkdown",
            ),
            ".unit.docs.auditor_scope_tests": (
                "TestAuditorForbiddenTerms",
                "TestAuditorScope",
            ),
            ".unit.docs.auditor_tests": (
                "TestAuditorCore",
                "TestAuditorNormalize",
            ),
            ".unit.docs.builder_tests": ("TestBuilderCore",),
            ".unit.docs.shared_iter_tests": (
                "TestIterMarkdownFiles",
                "TestSelectedProjectNames",
            ),
            ".unit.fixtures": (
                "deptry_report_payload",
                "modernizer_workspace",
                "modernizer_workspace_with_projects",
                "real_docs_project",
                "real_makefile_project",
                "real_python_package",
                "real_toml_project",
                "real_workspace",
                "tool_config_document",
            ),
            ".unit.fixtures_git": ("real_git_repo",),
            ".unit.refactor.test_infra_refactor_safety": ("EngineSafetyStub",),
            ".unit.refactor.test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
            ),
            ".unit.refactor.test_main_cli": ("TestFlextInfraRefactorMainCli",),
            ".unit.runner_service": ("RealSubprocessRunner",),
            ".unit.scenarios": (
                "DependencyScenario",
                "DependencyScenarios",
                "GitScenario",
                "GitScenarios",
                "SubprocessScenario",
                "SubprocessScenarios",
                "WorkspaceScenario",
                "WorkspaceScenarios",
            ),
            ".unit.test_infra_constants_core": (
                "TestFlextInfraConstantsExcludedNamespace",
                "TestFlextInfraConstantsFilesNamespace",
                "TestFlextInfraConstantsGatesNamespace",
                "TestFlextInfraConstantsPathsNamespace",
                "TestFlextInfraConstantsStatusNamespace",
            ),
            ".unit.test_infra_constants_extra": (
                "TestFlextInfraConstantsAlias",
                "TestFlextInfraConstantsCheckNamespace",
                "TestFlextInfraConstantsConsistency",
                "TestFlextInfraConstantsEncodingNamespace",
                "TestFlextInfraConstantsGithubNamespace",
                "TestFlextInfraConstantsImmutability",
            ),
            ".unit.test_infra_init_lazy_core": ("TestFlextInfraInitLazyLoading",),
            ".unit.test_infra_maintenance_init": ("TestFlextInfraMaintenance",),
            ".unit.test_infra_maintenance_main": (
                "TestMaintenanceMainEnforcer",
                "TestMaintenanceMainSuccess",
            ),
            ".unit.test_infra_maintenance_python_version": (
                "TestEnforcerExecute",
                "TestEnsurePythonVersionFile",
                "TestPublicProjectDiscovery",
                "TestReadRequiredMinor",
                "TestWorkspaceRoot",
            ),
            ".unit.test_infra_paths": ("TestFlextInfraPathResolver",),
            ".unit.test_infra_patterns_core": (
                "TestFlextInfraPatternsMarkdown",
                "TestFlextInfraPatternsTooling",
            ),
            ".unit.test_infra_patterns_extra": (
                "TestFlextInfraPatternsEdgeCases",
                "TestFlextInfraTypesPatternsPattern",
            ),
            ".unit.test_infra_protocols": ("TestFlextInfraProtocolsImport",),
            ".unit.test_infra_refactor_rope_migrations": (
                "TestNestedClassPropagationRopeMigration",
                "TestSymbolPropagatorRopeMigration",
            ),
            ".unit.test_infra_reporting_core": ("TestFlextInfraReportingServiceCore",),
            ".unit.test_infra_reporting_extra": (
                "TestFlextInfraReportingServiceExtra",
            ),
            ".unit.test_infra_rope_service": ("TestFlextInfraRopeWorkspace",),
            ".unit.test_infra_selection": ("TestFlextInfraUtilitiesSelection",),
            ".unit.test_infra_typings": (
                "TestInfraTypingAdapters",
                "TestInfraTypingGuards",
            ),
            ".unit.test_infra_utilities": ("TestFlextInfraUtilitiesImport",),
            ".unit.test_infra_version_core": ("TestFlextInfraVersionClass",),
            ".unit.test_infra_version_extra": (
                "TestFlextInfraVersionModuleLevel",
                "TestFlextInfraVersionPackageInfo",
            ),
            ".unit.test_infra_workspace_detector": ("TestWorkspaceDetector",),
            ".unit.test_infra_workspace_init": ("TestFlextInfraWorkspace",),
            ".unit.test_infra_workspace_migrator_deps": (
                "TestWorkspaceMigratorDependencyBehavior",
            ),
            ".unit.test_infra_workspace_migrator_internal": (
                "TestMigratorPublicBehavior",
            ),
            ".unit.test_infra_workspace_orchestrator": (
                "TestOrchestratorBasic",
                "TestOrchestratorFailures",
                "TestOrchestratorGateNormalization",
            ),
            ".unit.transformers.test_infra_transformer_helper_consolidation": (
                "TestHelperConsolidationTransformer",
            ),
            ".unit.validate.main_cli_tests": ("TestValidateCli",),
            ".unit.validate.namespace_validator_tests": (
                "TestFlextInfraNamespaceValidator",
            ),
            ".unit.workspace_factory": ("WorkspaceFactory",),
            ".unit.workspace_scenarios": (
                "BrokenScenario",
                "EmptyScenario",
                "FullScenario",
                "MinimalScenario",
            ),
            ".utilities": (
                "TestsFlextInfraUtilities",
                "u",
            ),
            "flext_infra": (
                "d",
                "e",
                "h",
                "r",
                "s",
                "x",
            ),
            "flext_tests": (
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
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
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)

__all__: list[str] = [
    "BrokenScenario",
    "DependencyScenario",
    "DependencyScenarios",
    "EmptyScenario",
    "EngineSafetyStub",
    "FlextInfraRefactorTypingUnificationRule",
    "FullScenario",
    "GitScenario",
    "GitScenarios",
    "MinimalScenario",
    "RealSubprocessRunner",
    "SubprocessScenario",
    "SubprocessScenarios",
    "TestAllDirectoriesScanned",
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorToMarkdown",
    "TestBuildProjectReport",
    "TestBuilderCore",
    "TestCheckIssueFormatted",
    "TestCheckOnlyMode",
    "TestClassifyIssues",
    "TestCollectInternalDeps",
    "TestCollectInternalDepsEdgeCases",
    "TestConfigFixerExecute",
    "TestConfigFixerProcessFile",
    "TestConfigFixerPublicBehavior",
    "TestConfigFixerRun",
    "TestConfigFixerToArray",
    "TestConsolidateGroupsPhase",
    "TestConstants",
    "TestDepsGroupEntry",
    "TestDepsModernizerMypy",
    "TestDepsModernizerPyright",
    "TestDepsModernizerTooling",
    "TestDetectMode",
    "TestDetectionTypingsFlow",
    "TestDetectionUncoveredLines",
    "TestDetectionUncoveredLinesClassify",
    "TestDetectorReportFlags",
    "TestDetectorRunFailures",
    "TestDiscoverProjectPathsDeptry",
    "TestDiscoverProjectPathsSelection",
    "TestEdgeCases",
    "TestEnforcerExecute",
    "TestEnsureCheckoutEdgeCases",
    "TestEnsureCoverageConfigPhase",
    "TestEnsurePyreflyConfigPhase",
    "TestEnsurePytestConfigPhase",
    "TestEnsurePythonVersionFile",
    "TestExcludedDirectories",
    "TestExtendedRunnerExtras",
    "TestFindDefinitionOffset",
    "TestFlextInfraBaseMk",
    "TestFlextInfraCheck",
    "TestFlextInfraConfigFixer",
    "TestFlextInfraConstantsAlias",
    "TestFlextInfraConstantsCheckNamespace",
    "TestFlextInfraConstantsConsistency",
    "TestFlextInfraConstantsEncodingNamespace",
    "TestFlextInfraConstantsExcludedNamespace",
    "TestFlextInfraConstantsFilesNamespace",
    "TestFlextInfraConstantsGatesNamespace",
    "TestFlextInfraConstantsGithubNamespace",
    "TestFlextInfraConstantsImmutability",
    "TestFlextInfraConstantsPathsNamespace",
    "TestFlextInfraConstantsStatusNamespace",
    "TestFlextInfraDependencyDetectionService",
    "TestFlextInfraDependencyPathSync",
    "TestFlextInfraDeps",
    "TestFlextInfraDiscoveryServiceUncoveredLines",
    "TestFlextInfraExtraPathsManager",
    "TestFlextInfraInitLazyLoading",
    "TestFlextInfraInternalDependencySyncService",
    "TestFlextInfraMaintenance",
    "TestFlextInfraModelsDependencyDetection",
    "TestFlextInfraModelsDependencyDetector",
    "TestFlextInfraNamespaceValidator",
    "TestFlextInfraPathResolver",
    "TestFlextInfraPatternsEdgeCases",
    "TestFlextInfraPatternsMarkdown",
    "TestFlextInfraPatternsTooling",
    "TestFlextInfraProtocolsImport",
    "TestFlextInfraPyprojectModernizer",
    "TestFlextInfraPyprojectModernizerEdgeCases",
    "TestFlextInfraPyprojectModernizerWorkspace",
    "TestFlextInfraRefactorMainCli",
    "TestFlextInfraReportingServiceCore",
    "TestFlextInfraReportingServiceExtra",
    "TestFlextInfraRopeWorkspace",
    "TestFlextInfraRuntimeDevDependencyDetectorInit",
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    "TestFlextInfraTypesPatternsPattern",
    "TestFlextInfraUtilitiesImport",
    "TestFlextInfraUtilitiesSelection",
    "TestFlextInfraVersionClass",
    "TestFlextInfraVersionModuleLevel",
    "TestFlextInfraVersionPackageInfo",
    "TestFlextInfraWorkspace",
    "TestFlextInfraWorkspaceChecker",
    "TestGateErrorReportingPublicBehavior",
    "TestGenerateFile",
    "TestGenerateTypeChecking",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestGetClassBases",
    "TestGetClassMethods",
    "TestGetModuleClasses",
    "TestGetModuleImports",
    "TestHelperConsolidationTransformer",
    "TestIdempotency",
    "TestInfraContainerFunctions",
    "TestInfraIntegration",
    "TestInfraMroPattern",
    "TestInfraServiceRetrieval",
    "TestInfraTypingAdapters",
    "TestInfraTypingGuards",
    "TestInjectCommentsPhase",
    "TestIsRelativeTo",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestLoadDependencyLimits",
    "TestMain",
    "TestMainFunction",
    "TestMaintenanceMainEnforcer",
    "TestMaintenanceMainSuccess",
    "TestMigratorPublicBehavior",
    "TestNestedClassPropagationRopeMigration",
    "TestOrchestratorBasic",
    "TestOrchestratorFailures",
    "TestOrchestratorGateNormalization",
    "TestOwnerFromRemoteUrl",
    "TestParseGitmodules",
    "TestParseRepoMap",
    "TestPathSyncEdgeCases",
    "TestPerformanceBenchmarks",
    "TestProjectLevelRefactor",
    "TestProjectResultProperties",
    "TestPublicDepsSurface",
    "TestPublicProjectDiscovery",
    "TestReadRequiredMinor",
    "TestRefactorPolicyMRO",
    "TestResolveInternalRepoName",
    "TestRewriteDepPaths",
    "TestRewritePep621",
    "TestRewritePoetry",
    "TestRunDeptry",
    "TestRunMypyStubHints",
    "TestRunProjectsPublicBehavior",
    "TestRunRuffFix",
    "TestRunnerPublicBehavior",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScanModels",
    "TestSelectedProjectNames",
    "TestSymbolPropagatorRopeMigration",
    "TestSync",
    "TestSyncMethodEdgeCases",
    "TestSyncMethodEdgeCasesMore",
    "TestSyncOne",
    "TestToInfraValue",
    "TestValidateCli",
    "TestValidateGitRefEdgeCases",
    "TestWorkspaceCheckCLI",
    "TestWorkspaceCheckCli",
    "TestWorkspaceCheckerErrorSummary",
    "TestWorkspaceCheckerParseGateCSV",
    "TestWorkspaceCheckerResolveGates",
    "TestWorkspaceDetector",
    "TestWorkspaceLevelRefactor",
    "TestWorkspaceMigratorDependencyBehavior",
    "TestWorkspaceRoot",
    "TestsExtendedProjectRunners",
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsDomain",
    "TestsFlextInfraConstantsFixtures",
    "TestsFlextInfraLazyInitHelpers",
    "TestsFlextInfraLazyInitTransforms",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesDiscoveryConsolidated",
    "TestsFlextInfraUtilitiesFormattingRunRuffFix",
    "WorkspaceFactory",
    "WorkspaceScenario",
    "WorkspaceScenarios",
    "c",
    "d",
    "deptry_report_payload",
    "e",
    "h",
    "m",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "p",
    "r",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "s",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tool_config_document",
    "tv",
    "u",
    "x",
]
