# AUTO-GENERATED FILE — Regenerate with: make gen
from flext_tests import (
    c as c,
    d as d,
    e as e,
    h as h,
    m as m,
    p as p,
    r as r,
    s as s,
    t as t,
    td as td,
    tf as tf,
    tk as tk,
    tm as tm,
    tv as tv,
    u as u,
    x as x,
)

from tests.unit import (
    _utilities as _utilities,
    basemk as basemk,
    check as check,
    codegen as codegen,
    container as container,
    deps as deps,
    discovery as discovery,
    docs as docs,
    github as github,
    io as io,
    refactor as refactor,
    release as release,
    test_infra_workspace_migrator_errors as test_infra_workspace_migrator_errors,
    test_infra_workspace_migrator_pyproject as test_infra_workspace_migrator_pyproject,
    test_mro_service_base_alias as test_mro_service_base_alias,
    test_version_diag as test_version_diag,
    test_version_diag2 as test_version_diag2,
    transformers as transformers,
    validate as validate,
    workspace as workspace,
)
from tests.unit._utilities.test_discovery_consolidated import (
    TestsFlextInfraUtilitiesdiscoveryconsolidated as TestsFlextInfraUtilitiesdiscoveryconsolidated,
)
from tests.unit._utilities.test_formatting import (
    TestsFlextInfraUtilitiesformatting as TestsFlextInfraUtilitiesformatting,
)
from tests.unit._utilities.test_protected_edit import (
    TestsFlextInfraUtilitiesProtectedEdit as TestsFlextInfraUtilitiesProtectedEdit,
)
from tests.unit._utilities.test_rope_hooks import (
    TestsFlextInfraUtilitiesRopeHooks as TestsFlextInfraUtilitiesRopeHooks,
)
from tests.unit._utilities.test_safety import (
    TestsFlextInfraUtilitiessafety as TestsFlextInfraUtilitiessafety,
)
from tests.unit._utilities.test_scanning import (
    TestsFlextInfraUtilitiesscanning as TestsFlextInfraUtilitiesscanning,
)
from tests.unit.basemk.test_engine import (
    TestsFlextInfraBasemkEngine as TestsFlextInfraBasemkEngine,
)
from tests.unit.basemk.test_generator import (
    TestsFlextInfraBasemkGenerator as TestsFlextInfraBasemkGenerator,
)
from tests.unit.basemk.test_generator_edge_cases import (
    TestsFlextInfraBasemkGeneratorEdgeCases as TestsFlextInfraBasemkGeneratorEdgeCases,
)
from tests.unit.basemk.test_init import (
    TestsFlextInfraBasemkInit as TestsFlextInfraBasemkInit,
)
from tests.unit.basemk.test_main import (
    TestsFlextInfraBasemkMain as TestsFlextInfraBasemkMain,
)
from tests.unit.basemk.test_make_contract import (
    TestsFlextInfraBasemkMakeContract as TestsFlextInfraBasemkMakeContract,
)
from tests.unit.check.extended_cli_entry_tests import (
    TestWorkspaceCheckCLI as TestWorkspaceCheckCLI,
)
from tests.unit.check.extended_config_fixer_errors_tests import (
    TestConfigFixerPublicBehavior as TestConfigFixerPublicBehavior,
)
from tests.unit.check.extended_config_fixer_tests import (
    TestConfigFixerExecute as TestConfigFixerExecute,
    TestConfigFixerProcessFile as TestConfigFixerProcessFile,
    TestConfigFixerRun as TestConfigFixerRun,
    TestConfigFixerToArray as TestConfigFixerToArray,
)
from tests.unit.check.extended_error_reporting_tests import (
    TestGateErrorReportingPublicBehavior as TestGateErrorReportingPublicBehavior,
)
from tests.unit.check.extended_models_tests import (
    TestCheckIssueFormatted as TestCheckIssueFormatted,
    TestProjectResultProperties as TestProjectResultProperties,
    TestRunCommandGateParsing as TestRunCommandGateParsing,
    TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
)
from tests.unit.check.extended_project_runners_tests import (
    TestsExtendedProjectRunners as TestsExtendedProjectRunners,
)
from tests.unit.check.extended_resolve_gates_tests import (
    TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
)
from tests.unit.check.extended_run_projects_tests import (
    TestRunProjectsPublicBehavior as TestRunProjectsPublicBehavior,
)
from tests.unit.check.extended_runners_extra_tests import (
    TestExtendedRunnerExtras as TestExtendedRunnerExtras,
)
from tests.unit.check.extended_runners_tests import (
    TestRunnerPublicBehavior as TestRunnerPublicBehavior,
)
from tests.unit.check.init_tests import TestFlextInfraCheck as TestFlextInfraCheck
from tests.unit.check.pyrefly_tests import (
    TestFlextInfraConfigFixer as TestFlextInfraConfigFixer,
)
from tests.unit.check.tests_cli import TestWorkspaceCheckCli as TestWorkspaceCheckCli
from tests.unit.check.workspace_tests import (
    TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
)
from tests.unit.cli_what_selector_tests import (
    TestsFlextInfraCliWhatSelector as TestsFlextInfraCliWhatSelector,
)
from tests.unit.codegen.lazy_init_generation_tests import (
    TestGenerateFile as TestGenerateFile,
    TestGenerateTypeChecking as TestGenerateTypeChecking,
    TestLazyInitPlannerCollision as TestLazyInitPlannerCollision,
    TestRunRuffFix as TestRunRuffFix,
)
from tests.unit.codegen.lazy_init_helpers_tests import (
    TestsFlextInfraLazyInitHelpers as TestsFlextInfraLazyInitHelpers,
)
from tests.unit.codegen.lazy_init_tests import (
    TestAllDirectoriesScanned as TestAllDirectoriesScanned,
    TestCheckOnlyMode as TestCheckOnlyMode,
    TestEdgeCases as TestEdgeCases,
    TestExcludedDirectories as TestExcludedDirectories,
)
from tests.unit.codegen.lazy_init_transforms_tests import (
    TestsFlextInfraLazyInitTransforms as TestsFlextInfraLazyInitTransforms,
)
from tests.unit.codegen.scaffolder_naming_tests import (
    TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
    TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
)
from tests.unit.container.test_infra_container import (
    TestsFlextInfraContainerInfraContainer as TestsFlextInfraContainerInfraContainer,
)
from tests.unit.deps.test_detection_classify import (
    TestsFlextInfraDepsDetectionClassify as TestsFlextInfraDepsDetectionClassify,
)
from tests.unit.deps.test_detection_deptry import (
    TestsFlextInfraDepsDetectionDeptry as TestsFlextInfraDepsDetectionDeptry,
)
from tests.unit.deps.test_detection_discover import (
    TestsFlextInfraDepsDetectionDiscover as TestsFlextInfraDepsDetectionDiscover,
)
from tests.unit.deps.test_detection_models import (
    TestsFlextInfraDepsDetectionModels as TestsFlextInfraDepsDetectionModels,
)
from tests.unit.deps.test_detection_typings import (
    TestsFlextInfraDepsDetectionTypings as TestsFlextInfraDepsDetectionTypings,
)
from tests.unit.deps.test_detection_typings_flow import (
    TestsFlextInfraDepsDetectionTypingsFlow as TestsFlextInfraDepsDetectionTypingsFlow,
)
from tests.unit.deps.test_detection_uncovered import (
    TestsFlextInfraDepsDetectionUncovered as TestsFlextInfraDepsDetectionUncovered,
)
from tests.unit.deps.test_detector_detect import (
    TestsFlextInfraDepsDetectorDetect as TestsFlextInfraDepsDetectorDetect,
)
from tests.unit.deps.test_detector_detect_failures import (
    TestsFlextInfraDepsDetectorDetectFailures as TestsFlextInfraDepsDetectorDetectFailures,
)
from tests.unit.deps.test_detector_init import (
    TestsFlextInfraDepsDetectorInit as TestsFlextInfraDepsDetectorInit,
)
from tests.unit.deps.test_detector_main import (
    TestsFlextInfraDepsDetectorMain as TestsFlextInfraDepsDetectorMain,
)
from tests.unit.deps.test_detector_models import (
    TestsFlextInfraDepsDetectorModels as TestsFlextInfraDepsDetectorModels,
)
from tests.unit.deps.test_detector_report import (
    TestsFlextInfraDepsDetectorReport as TestsFlextInfraDepsDetectorReport,
)
from tests.unit.deps.test_detector_report_flags import (
    TestsFlextInfraDepsDetectorReportFlags as TestsFlextInfraDepsDetectorReportFlags,
)
from tests.unit.deps.test_extra_paths_manager import (
    TestsFlextInfraExtraPathsManager as TestsFlextInfraExtraPathsManager,
)
from tests.unit.deps.test_extra_paths_search_paths import (
    TestsFlextInfraExtraPathsSearchPaths as TestsFlextInfraExtraPathsSearchPaths,
)
from tests.unit.deps.test_extra_paths_sync import (
    TestsFlextInfraDepsExtraPathsSync as TestsFlextInfraDepsExtraPathsSync,
)
from tests.unit.deps.test_extra_paths_uv_sources import (
    TestsFlextInfraExtraPathsUvSources as TestsFlextInfraExtraPathsUvSources,
)
from tests.unit.deps.test_init import TestsFlextInfraDepsInit as TestsFlextInfraDepsInit
from tests.unit.deps.test_internal_sync_discovery import (
    TestsFlextInfraDepsInternalSyncDiscovery as TestsFlextInfraDepsInternalSyncDiscovery,
)
from tests.unit.deps.test_internal_sync_discovery_edge import (
    TestsFlextInfraDepsInternalSyncDiscoveryEdge as TestsFlextInfraDepsInternalSyncDiscoveryEdge,
)
from tests.unit.deps.test_internal_sync_main import (
    TestsFlextInfraDepsInternalSyncMain as TestsFlextInfraDepsInternalSyncMain,
)
from tests.unit.deps.test_internal_sync_resolve import (
    TestsFlextInfraDepsInternalSyncResolve as TestsFlextInfraDepsInternalSyncResolve,
)
from tests.unit.deps.test_internal_sync_sync import (
    TestsFlextInfraDepsInternalSyncSync as TestsFlextInfraDepsInternalSyncSync,
)
from tests.unit.deps.test_internal_sync_sync_edge import (
    TestsFlextInfraDepsInternalSyncSyncEdge as TestsFlextInfraDepsInternalSyncSyncEdge,
)
from tests.unit.deps.test_internal_sync_sync_edge_more import (
    TestsFlextInfraDepsInternalSyncSyncEdgeMore as TestsFlextInfraDepsInternalSyncSyncEdgeMore,
)
from tests.unit.deps.test_internal_sync_update import (
    TestsFlextInfraDepsInternalSyncUpdate as TestsFlextInfraDepsInternalSyncUpdate,
)
from tests.unit.deps.test_internal_sync_update_checkout_edge import (
    TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge as TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge,
)
from tests.unit.deps.test_internal_sync_validation import (
    TestsFlextInfraDepsInternalSyncValidation as TestsFlextInfraDepsInternalSyncValidation,
)
from tests.unit.deps.test_internal_sync_workspace import (
    TestsFlextInfraDepsInternalSyncWorkspace as TestsFlextInfraDepsInternalSyncWorkspace,
)
from tests.unit.deps.test_main_dispatch import (
    TestsFlextInfraDepsMainDispatch as TestsFlextInfraDepsMainDispatch,
)
from tests.unit.deps.test_modernizer_comments import (
    TestsFlextInfraDepsModernizerComments as TestsFlextInfraDepsModernizerComments,
)
from tests.unit.deps.test_modernizer_consolidate import (
    TestsFlextInfraDepsModernizerConsolidate as TestsFlextInfraDepsModernizerConsolidate,
)
from tests.unit.deps.test_modernizer_coverage import (
    TestsFlextInfraDepsModernizerCoverage as TestsFlextInfraDepsModernizerCoverage,
)
from tests.unit.deps.test_modernizer_helpers import (
    TestsFlextInfraDepsModernizerHelpers as TestsFlextInfraDepsModernizerHelpers,
)
from tests.unit.deps.test_modernizer_main import (
    TestsFlextInfraDepsModernizerMain as TestsFlextInfraDepsModernizerMain,
)
from tests.unit.deps.test_modernizer_main_extra import (
    TestsFlextInfraDepsModernizerMainExtra as TestsFlextInfraDepsModernizerMainExtra,
)
from tests.unit.deps.test_modernizer_mypy import (
    TestsFlextInfraDepsModernizerMypy as TestsFlextInfraDepsModernizerMypy,
)
from tests.unit.deps.test_modernizer_pyrefly import (
    TestsFlextInfraModernizerPyrefly as TestsFlextInfraModernizerPyrefly,
)
from tests.unit.deps.test_modernizer_pyright import (
    TestsFlextInfraDepsModernizerPyright as TestsFlextInfraDepsModernizerPyright,
)
from tests.unit.deps.test_modernizer_pytest import (
    TestsFlextInfraDepsModernizerPytest as TestsFlextInfraDepsModernizerPytest,
)
from tests.unit.deps.test_modernizer_tooling import (
    TestsFlextInfraDepsModernizerTooling as TestsFlextInfraDepsModernizerTooling,
)
from tests.unit.deps.test_modernizer_workspace import (
    TestsFlextInfraDepsModernizerWorkspace as TestsFlextInfraDepsModernizerWorkspace,
)
from tests.unit.deps.test_path_sync_init import (
    TestsFlextInfraDepsPathSyncInit as TestsFlextInfraDepsPathSyncInit,
)
from tests.unit.deps.test_path_sync_main import (
    TestsFlextInfraDepsPathSyncMain as TestsFlextInfraDepsPathSyncMain,
)
from tests.unit.deps.test_path_sync_main_edges import (
    TestsFlextInfraDepsPathSyncMainEdges as TestsFlextInfraDepsPathSyncMainEdges,
)
from tests.unit.deps.test_path_sync_main_more import (
    TestsFlextInfraDepsPathSyncMainMore as TestsFlextInfraDepsPathSyncMainMore,
)
from tests.unit.deps.test_path_sync_main_project_obj import (
    TestsFlextInfraDepsPathSyncMainProjectObj as TestsFlextInfraDepsPathSyncMainProjectObj,
)
from tests.unit.deps.test_path_sync_rewrite_deps import (
    TestsFlextInfraDepsPathSyncRewriteDeps as TestsFlextInfraDepsPathSyncRewriteDeps,
)
from tests.unit.deps.test_path_sync_rewrite_pep621 import (
    TestsFlextInfraDepsPathSyncRewritePep621 as TestsFlextInfraDepsPathSyncRewritePep621,
)
from tests.unit.deps.test_path_sync_rewrite_poetry import (
    TestsFlextInfraDepsPathSyncRewritePoetry as TestsFlextInfraDepsPathSyncRewritePoetry,
)
from tests.unit.discovery.test_infra_discovery_edge_cases import (
    TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases as TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases,
)
from tests.unit.docs.auditor_budgets_tests import (
    TestLoadAuditBudgets as TestLoadAuditBudgets,
)
from tests.unit.docs.auditor_links_tests import (
    TestAuditorBrokenLinks as TestAuditorBrokenLinks,
    TestAuditorToMarkdown as TestAuditorToMarkdown,
)
from tests.unit.docs.auditor_scope_tests import (
    TestAuditorForbiddenTerms as TestAuditorForbiddenTerms,
    TestAuditorScope as TestAuditorScope,
)
from tests.unit.docs.auditor_tests import (
    TestAuditorCore as TestAuditorCore,
    TestAuditorNormalize as TestAuditorNormalize,
)
from tests.unit.docs.builder_tests import TestBuilderCore as TestBuilderCore
from tests.unit.docs.shared_iter_tests import (
    TestIterMarkdownFiles as TestIterMarkdownFiles,
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
from tests.unit.io.test_infra_terminal_detection import (
    TestsFlextInfraIoInfraTerminalDetection as TestsFlextInfraIoInfraTerminalDetection,
)
from tests.unit.refactor.test_infra_refactor_census_preview_cache import (
    TestsFlextInfraRefactorCensusPreviewCache as TestsFlextInfraRefactorCensusPreviewCache,
)
from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
    TestsFlextInfraRefactorInfraRefactorClassAndPropagation as TestsFlextInfraRefactorInfraRefactorClassAndPropagation,
)
from tests.unit.refactor.test_infra_refactor_class_placement import (
    TestsFlextInfraRefactorInfraRefactorClassPlacement as TestsFlextInfraRefactorInfraRefactorClassPlacement,
)
from tests.unit.refactor.test_infra_refactor_cli_models_workflow import (
    TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow as TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow,
)
from tests.unit.refactor.test_infra_refactor_engine import (
    TestsFlextInfraRefactorInfraRefactorEngine as TestsFlextInfraRefactorInfraRefactorEngine,
)
from tests.unit.refactor.test_infra_refactor_import_modernizer import (
    TestsFlextInfraRefactorInfraRefactorImportModernizer as TestsFlextInfraRefactorInfraRefactorImportModernizer,
)
from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
    TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations as TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations,
)
from tests.unit.refactor.test_infra_refactor_migrate_to_class_mro import (
    TestsFlextInfraRefactorInfraRefactorMigrateToClassMro as TestsFlextInfraRefactorInfraRefactorMigrateToClassMro,
)
from tests.unit.refactor.test_infra_refactor_mro_completeness import (
    TestsFlextInfraRefactorInfraRefactorMroCompleteness as TestsFlextInfraRefactorInfraRefactorMroCompleteness,
)
from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
    TestsFlextInfraRefactorInfraRefactorNamespaceAliases as TestsFlextInfraRefactorInfraRefactorNamespaceAliases,
)
from tests.unit.refactor.test_infra_refactor_namespace_enforcer import (
    TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer as TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer,
)
from tests.unit.refactor.test_infra_refactor_namespace_moves import (
    TestsFlextInfraRefactorInfraRefactorNamespaceMoves as TestsFlextInfraRefactorInfraRefactorNamespaceMoves,
)
from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
    TestsFlextInfraRefactorInfraRefactorPatternCorrections as TestsFlextInfraRefactorInfraRefactorPatternCorrections,
)
from tests.unit.refactor.test_infra_refactor_policy_family_rules import (
    TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules as TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules,
)
from tests.unit.refactor.test_infra_refactor_project_classifier import (
    TestsFlextInfraRefactorInfraRefactorProjectClassifier as TestsFlextInfraRefactorInfraRefactorProjectClassifier,
)
from tests.unit.refactor.test_infra_refactor_safety import (
    EngineSafetyStub as EngineSafetyStub,
    TestsFlextInfraRefactorInfraRefactorSafety as TestsFlextInfraRefactorInfraRefactorSafety,
)
from tests.unit.refactor.test_infra_refactor_typing_unifier import (
    FlextInfraRefactorTypingUnificationRule as FlextInfraRefactorTypingUnificationRule,
    TestsFlextInfraRefactorInfraRefactorTypingUnifier as TestsFlextInfraRefactorInfraRefactorTypingUnifier,
)
from tests.unit.refactor.test_main_cli import (
    TestsFlextInfraRefactorMainCli as TestsFlextInfraRefactorMainCli,
)
from tests.unit.release.test_release_dag import (
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
from tests.unit.test_infra_root_export_contract import (
    TestsFlextInfraRootExportContract as TestsFlextInfraRootExportContract,
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
from tests.unit.transformers.test_infra_transformer_class_nesting import (
    TestsFlextInfraTransformersInfraTransformerClassNesting as TestsFlextInfraTransformersInfraTransformerClassNesting,
)
from tests.unit.transformers.test_infra_transformer_cli_modernizer import (
    TestsFlextInfraTransformersCliModernizer as TestsFlextInfraTransformersCliModernizer,
)
from tests.unit.transformers.test_infra_transformer_helper_consolidation import (
    TestsFlextInfraTransformersInfraTransformerHelperConsolidation as TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
)
from tests.unit.transformers.test_infra_transformer_logging_modernizer import (
    TestsFlextInfraTransformersLoggingModernizer as TestsFlextInfraTransformersLoggingModernizer,
)
from tests.unit.transformers.test_infra_transformer_nested_class_propagation import (
    TestsFlextInfraTransformersInfraTransformerNestedClassPropagation as TestsFlextInfraTransformersInfraTransformerNestedClassPropagation,
)
from tests.unit.transformers.test_infra_transformer_pattern_modernizer import (
    TestsFlextInfraTransformersPatternModernizer as TestsFlextInfraTransformersPatternModernizer,
)
from tests.unit.transformers.test_infra_transformer_pydantic_modernizer import (
    TestsFlextInfraTransformersPydanticModernizer as TestsFlextInfraTransformersPydanticModernizer,
)
from tests.unit.transformers.test_infra_transformer_result_di_modernizer import (
    TestsFlextInfraTransformersResultDiModernizer as TestsFlextInfraTransformersResultDiModernizer,
)
from tests.unit.transformers.test_infra_transformer_tests_modernizer import (
    TestsFlextInfraTransformersTestsModernizer as TestsFlextInfraTransformersTestsModernizer,
)
from tests.unit.validate.main_cli_tests import TestValidateCli as TestValidateCli
from tests.unit.validate.namespace_validator_tests import (
    TestFlextInfraNamespaceValidator as TestFlextInfraNamespaceValidator,
)
from tests.unit.workspace.test_main import (
    TestsFlextInfraWorkspaceMain as TestsFlextInfraWorkspaceMain,
)
from tests.unit.workspace.test_makefile_dry_run import (
    TestsFlextInfraWorkspaceMakefileDryRun as TestsFlextInfraWorkspaceMakefileDryRun,
)
from tests.unit.workspace.test_makefile_generator import (
    TestsFlextInfraWorkspaceMakefileGenerator as TestsFlextInfraWorkspaceMakefileGenerator,
)
from tests.unit.workspace.test_sync import (
    TestsFlextInfraWorkspaceSync as TestsFlextInfraWorkspaceSync,
)
from tests.unit.workspace.test_sync_environment import (
    TestsFlextInfraWorkspaceSyncEnvironment as TestsFlextInfraWorkspaceSyncEnvironment,
)
from tests.unit.workspace_factory import (
    TestsFlextInfraWorkspaceFactory as TestsFlextInfraWorkspaceFactory,
)
