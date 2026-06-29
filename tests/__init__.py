# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if TYPE_CHECKING:
    from flext_tests import (
        d as d,
        e as e,
        h as h,
        r as r,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        x as x,
    )

    from tests.base import (
        TestsFlextInfraServiceBase as TestsFlextInfraServiceBase,
        s as s,
    )
    from tests.constants import (
        TestsFlextInfraConstants as TestsFlextInfraConstants,
        c as c,
    )
    from tests.integration.test_infra_integration import (
        TestsFlextInfraIntegrationInfraIntegration as TestsFlextInfraIntegrationInfraIntegration,
    )
    from tests.integration.test_refactor_nesting_file import (
        TestsFlextInfraIntegrationRefactorNestingFile as TestsFlextInfraIntegrationRefactorNestingFile,
    )
    from tests.integration.test_refactor_nesting_idempotency import (
        TestsFlextInfraIntegrationRefactorNestingIdempotency as TestsFlextInfraIntegrationRefactorNestingIdempotency,
    )
    from tests.integration.test_refactor_nesting_performance import (
        TestsFlextInfraIntegrationRefactorNestingPerformance as TestsFlextInfraIntegrationRefactorNestingPerformance,
    )
    from tests.integration.test_refactor_nesting_project import (
        TestsFlextInfraIntegrationRefactorNestingProject as TestsFlextInfraIntegrationRefactorNestingProject,
    )
    from tests.integration.test_refactor_nesting_workspace import (
        TestsFlextInfraIntegrationRefactorNestingWorkspace as TestsFlextInfraIntegrationRefactorNestingWorkspace,
    )
    from tests.integration.test_refactor_policy_mro import (
        TestsFlextInfraIntegrationRefactorPolicyMro as TestsFlextInfraIntegrationRefactorPolicyMro,
    )
    from tests.models import TestsFlextInfraModels as TestsFlextInfraModels, m as m
    from tests.protocols import (
        TestsFlextInfraProtocols as TestsFlextInfraProtocols,
        p as p,
    )
    from tests.refactor.test_rope_semantic import (
        TestsFlextInfraRefactorRopeSemantic as TestsFlextInfraRefactorRopeSemantic,
    )
    from tests.refactor.test_rope_stubs import (
        TestsFlextInfraRefactorRopeStubs as TestsFlextInfraRefactorRopeStubs,
    )
    from tests.settings import TestsFlextInfraSettings as TestsFlextInfraSettings
    from tests.typings import TestsFlextInfraTypes as TestsFlextInfraTypes, t as t
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
    from tests.unit.check.tests_cli import (
        TestWorkspaceCheckCli as TestWorkspaceCheckCli,
    )
    from tests.unit.check.workspace_tests import (
        TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
    )
    from tests.unit.cli_what_selector_tests import (
        TestsFlextInfraCliWhatSelector as TestsFlextInfraCliWhatSelector,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile as TestGenerateFile,
        TestGenerateTypeChecking as TestGenerateTypeChecking,
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
    from tests.unit.deps.test_extra_paths_sync import (
        TestsFlextInfraDepsExtraPathsSync as TestsFlextInfraDepsExtraPathsSync,
    )
    from tests.unit.deps.test_init import (
        TestsFlextInfraDepsInit as TestsFlextInfraDepsInit,
    )
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
    from tests.unit.workspace_factory import (
        TestsFlextInfraWorkspaceFactory as TestsFlextInfraWorkspaceFactory,
    )
    from tests.utilities import (
        TestsFlextInfraUtilities as TestsFlextInfraUtilities,
        u as u,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (
        ".integration",
        ".refactor",
        ".unit",
    ),
    build_lazy_import_map(
        {
            ".base": (
                "TestsFlextInfraServiceBase",
                "s",
            ),
            ".conftest": ("conftest",),
            ".constants": (
                "TestsFlextInfraConstants",
                "c",
            ),
            ".integration": ("integration",),
            ".integration.test_infra_integration": (
                "TestsFlextInfraIntegrationInfraIntegration",
            ),
            ".integration.test_refactor_nesting_file": (
                "TestsFlextInfraIntegrationRefactorNestingFile",
            ),
            ".integration.test_refactor_nesting_idempotency": (
                "TestsFlextInfraIntegrationRefactorNestingIdempotency",
            ),
            ".integration.test_refactor_nesting_performance": (
                "TestsFlextInfraIntegrationRefactorNestingPerformance",
            ),
            ".integration.test_refactor_nesting_project": (
                "TestsFlextInfraIntegrationRefactorNestingProject",
            ),
            ".integration.test_refactor_nesting_workspace": (
                "TestsFlextInfraIntegrationRefactorNestingWorkspace",
            ),
            ".integration.test_refactor_policy_mro": (
                "TestsFlextInfraIntegrationRefactorPolicyMro",
            ),
            ".models": (
                "TestsFlextInfraModels",
                "m",
            ),
            ".protocols": (
                "TestsFlextInfraProtocols",
                "p",
            ),
            ".refactor": ("refactor",),
            ".refactor.test_rope_semantic": ("TestsFlextInfraRefactorRopeSemantic",),
            ".refactor.test_rope_stubs": ("TestsFlextInfraRefactorRopeStubs",),
            ".settings": ("TestsFlextInfraSettings",),
            ".typings": (
                "TestsFlextInfraTypes",
                "t",
            ),
            ".unit": ("unit",),
            ".unit._utilities.test_discovery_consolidated": (
                "TestsFlextInfraUtilitiesdiscoveryconsolidated",
            ),
            ".unit._utilities.test_formatting": ("TestsFlextInfraUtilitiesformatting",),
            ".unit._utilities.test_protected_edit": (
                "TestsFlextInfraUtilitiesProtectedEdit",
            ),
            ".unit._utilities.test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
            ".unit._utilities.test_safety": ("TestsFlextInfraUtilitiessafety",),
            ".unit._utilities.test_scanning": ("TestsFlextInfraUtilitiesscanning",),
            ".unit.basemk.test_engine": ("TestsFlextInfraBasemkEngine",),
            ".unit.basemk.test_generator": ("TestsFlextInfraBasemkGenerator",),
            ".unit.basemk.test_generator_edge_cases": (
                "TestsFlextInfraBasemkGeneratorEdgeCases",
            ),
            ".unit.basemk.test_init": ("TestsFlextInfraBasemkInit",),
            ".unit.basemk.test_main": ("TestsFlextInfraBasemkMain",),
            ".unit.basemk.test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
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
                "TestRunCommandGateParsing",
                "TestWorkspaceCheckerErrorSummary",
            ),
            ".unit.check.extended_project_runners_tests": (
                "TestsExtendedProjectRunners",
            ),
            ".unit.check.extended_resolve_gates_tests": (
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
            ".unit.cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
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
                "TestsFlextInfraContainerInfraContainer",
            ),
            ".unit.deps.test_detection_classify": (
                "TestsFlextInfraDepsDetectionClassify",
            ),
            ".unit.deps.test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
            ".unit.deps.test_detection_discover": (
                "TestsFlextInfraDepsDetectionDiscover",
            ),
            ".unit.deps.test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
            ".unit.deps.test_detection_typings": (
                "TestsFlextInfraDepsDetectionTypings",
            ),
            ".unit.deps.test_detection_typings_flow": (
                "TestsFlextInfraDepsDetectionTypingsFlow",
            ),
            ".unit.deps.test_detection_uncovered": (
                "TestsFlextInfraDepsDetectionUncovered",
            ),
            ".unit.deps.test_detector_detect": ("TestsFlextInfraDepsDetectorDetect",),
            ".unit.deps.test_detector_detect_failures": (
                "TestsFlextInfraDepsDetectorDetectFailures",
            ),
            ".unit.deps.test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
            ".unit.deps.test_detector_main": ("TestsFlextInfraDepsDetectorMain",),
            ".unit.deps.test_detector_models": ("TestsFlextInfraDepsDetectorModels",),
            ".unit.deps.test_detector_report": ("TestsFlextInfraDepsDetectorReport",),
            ".unit.deps.test_detector_report_flags": (
                "TestsFlextInfraDepsDetectorReportFlags",
            ),
            ".unit.deps.test_extra_paths_manager": (
                "TestsFlextInfraExtraPathsManager",
            ),
            ".unit.deps.test_extra_paths_sync": ("TestsFlextInfraDepsExtraPathsSync",),
            ".unit.deps.test_init": ("TestsFlextInfraDepsInit",),
            ".unit.deps.test_internal_sync_discovery": (
                "TestsFlextInfraDepsInternalSyncDiscovery",
            ),
            ".unit.deps.test_internal_sync_discovery_edge": (
                "TestsFlextInfraDepsInternalSyncDiscoveryEdge",
            ),
            ".unit.deps.test_internal_sync_main": (
                "TestsFlextInfraDepsInternalSyncMain",
            ),
            ".unit.deps.test_internal_sync_resolve": (
                "TestsFlextInfraDepsInternalSyncResolve",
            ),
            ".unit.deps.test_internal_sync_sync": (
                "TestsFlextInfraDepsInternalSyncSync",
            ),
            ".unit.deps.test_internal_sync_sync_edge": (
                "TestsFlextInfraDepsInternalSyncSyncEdge",
            ),
            ".unit.deps.test_internal_sync_sync_edge_more": (
                "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
            ),
            ".unit.deps.test_internal_sync_update": (
                "TestsFlextInfraDepsInternalSyncUpdate",
            ),
            ".unit.deps.test_internal_sync_update_checkout_edge": (
                "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
            ),
            ".unit.deps.test_internal_sync_validation": (
                "TestsFlextInfraDepsInternalSyncValidation",
            ),
            ".unit.deps.test_internal_sync_workspace": (
                "TestsFlextInfraDepsInternalSyncWorkspace",
            ),
            ".unit.deps.test_main_dispatch": ("TestsFlextInfraDepsMainDispatch",),
            ".unit.deps.test_modernizer_comments": (
                "TestsFlextInfraDepsModernizerComments",
            ),
            ".unit.deps.test_modernizer_consolidate": (
                "TestsFlextInfraDepsModernizerConsolidate",
            ),
            ".unit.deps.test_modernizer_coverage": (
                "TestsFlextInfraDepsModernizerCoverage",
            ),
            ".unit.deps.test_modernizer_helpers": (
                "TestsFlextInfraDepsModernizerHelpers",
            ),
            ".unit.deps.test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
            ".unit.deps.test_modernizer_main_extra": (
                "TestsFlextInfraDepsModernizerMainExtra",
            ),
            ".unit.deps.test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
            ".unit.deps.test_modernizer_pyrefly": ("TestsFlextInfraModernizerPyrefly",),
            ".unit.deps.test_modernizer_pyright": (
                "TestsFlextInfraDepsModernizerPyright",
            ),
            ".unit.deps.test_modernizer_pytest": (
                "TestsFlextInfraDepsModernizerPytest",
            ),
            ".unit.deps.test_modernizer_tooling": (
                "TestsFlextInfraDepsModernizerTooling",
            ),
            ".unit.deps.test_modernizer_workspace": (
                "TestsFlextInfraDepsModernizerWorkspace",
            ),
            ".unit.deps.test_path_sync_init": ("TestsFlextInfraDepsPathSyncInit",),
            ".unit.deps.test_path_sync_main": ("TestsFlextInfraDepsPathSyncMain",),
            ".unit.deps.test_path_sync_main_edges": (
                "TestsFlextInfraDepsPathSyncMainEdges",
            ),
            ".unit.deps.test_path_sync_main_more": (
                "TestsFlextInfraDepsPathSyncMainMore",
            ),
            ".unit.deps.test_path_sync_main_project_obj": (
                "TestsFlextInfraDepsPathSyncMainProjectObj",
            ),
            ".unit.deps.test_path_sync_rewrite_deps": (
                "TestsFlextInfraDepsPathSyncRewriteDeps",
            ),
            ".unit.deps.test_path_sync_rewrite_pep621": (
                "TestsFlextInfraDepsPathSyncRewritePep621",
            ),
            ".unit.deps.test_path_sync_rewrite_poetry": (
                "TestsFlextInfraDepsPathSyncRewritePoetry",
            ),
            ".unit.discovery.test_infra_discovery_edge_cases": (
                "TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases",
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
            ".unit.fixtures_git": ("real_git_repo",),
            ".unit.io.test_infra_terminal_detection": (
                "TestsFlextInfraIoInfraTerminalDetection",
            ),
            ".unit.refactor.test_infra_refactor_census_preview_cache": (
                "TestsFlextInfraRefactorCensusPreviewCache",
            ),
            ".unit.refactor.test_infra_refactor_class_and_propagation": (
                "TestsFlextInfraRefactorInfraRefactorClassAndPropagation",
            ),
            ".unit.refactor.test_infra_refactor_class_placement": (
                "TestsFlextInfraRefactorInfraRefactorClassPlacement",
            ),
            ".unit.refactor.test_infra_refactor_cli_models_workflow": (
                "TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow",
            ),
            ".unit.refactor.test_infra_refactor_engine": (
                "TestsFlextInfraRefactorInfraRefactorEngine",
            ),
            ".unit.refactor.test_infra_refactor_import_modernizer": (
                "TestsFlextInfraRefactorInfraRefactorImportModernizer",
            ),
            ".unit.refactor.test_infra_refactor_legacy_and_annotations": (
                "TestsFlextInfraRefactorInfraRefactorLegacyAndAnnotations",
            ),
            ".unit.refactor.test_infra_refactor_migrate_to_class_mro": (
                "TestsFlextInfraRefactorInfraRefactorMigrateToClassMro",
            ),
            ".unit.refactor.test_infra_refactor_mro_completeness": (
                "TestsFlextInfraRefactorInfraRefactorMroCompleteness",
            ),
            ".unit.refactor.test_infra_refactor_namespace_aliases": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceAliases",
            ),
            ".unit.refactor.test_infra_refactor_namespace_enforcer": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer",
            ),
            ".unit.refactor.test_infra_refactor_namespace_moves": (
                "TestsFlextInfraRefactorInfraRefactorNamespaceMoves",
            ),
            ".unit.refactor.test_infra_refactor_pattern_corrections": (
                "TestsFlextInfraRefactorInfraRefactorPatternCorrections",
            ),
            ".unit.refactor.test_infra_refactor_policy_family_rules": (
                "TestsFlextInfraRefactorInfraRefactorPolicyFamilyRules",
            ),
            ".unit.refactor.test_infra_refactor_project_classifier": (
                "TestsFlextInfraRefactorInfraRefactorProjectClassifier",
            ),
            ".unit.refactor.test_infra_refactor_safety": (
                "EngineSafetyStub",
                "TestsFlextInfraRefactorInfraRefactorSafety",
            ),
            ".unit.refactor.test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
                "TestsFlextInfraRefactorInfraRefactorTypingUnifier",
            ),
            ".unit.refactor.test_main_cli": ("TestsFlextInfraRefactorMainCli",),
            ".unit.release.test_release_dag": ("TestsFlextInfraReleaseDag",),
            ".unit.runner_service": ("RealSubprocessRunner",),
            ".unit.test_infra_constants_core": ("TestsFlextInfraInfraConstantsCore",),
            ".unit.test_infra_constants_extra": ("TestsFlextInfraInfraConstantsExtra",),
            ".unit.test_infra_main": ("TestsFlextInfraInfraMain",),
            ".unit.test_infra_maintenance_cli": ("TestsFlextInfraInfraMaintenanceCli",),
            ".unit.test_infra_maintenance_init": (
                "TestsFlextInfraInfraMaintenanceInit",
            ),
            ".unit.test_infra_maintenance_main": (
                "TestsFlextInfraInfraMaintenanceMain",
            ),
            ".unit.test_infra_maintenance_python_version": (
                "TestsFlextInfraInfraMaintenancePythonVersion",
            ),
            ".unit.test_infra_paths": ("TestsFlextInfraInfraPaths",),
            ".unit.test_infra_patterns_core": ("TestsFlextInfraInfraPatternsCore",),
            ".unit.test_infra_patterns_extra": ("TestsFlextInfraInfraPatternsExtra",),
            ".unit.test_infra_protocols": ("TestsFlextInfraInfraProtocols",),
            ".unit.test_infra_public_api": ("TestsFlextInfraPublicApi",),
            ".unit.test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".unit.test_infra_reporting_core": ("TestsFlextInfraInfraReportingCore",),
            ".unit.test_infra_reporting_extra": ("TestsFlextInfraInfraReportingExtra",),
            ".unit.test_infra_root_export_contract": (
                "TestsFlextInfraRootExportContract",
            ),
            ".unit.test_infra_rope_imports": ("TestsFlextInfraRopeImports",),
            ".unit.test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".unit.test_infra_selection": ("TestsFlextInfraInfraSelection",),
            ".unit.test_infra_typings": ("TestsFlextInfraInfraTypings",),
            ".unit.test_infra_utilities": ("TestsFlextInfraInfraUtilities",),
            ".unit.test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".unit.test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".unit.test_infra_versioning": ("TestsFlextInfraInfraVersioning",),
            ".unit.test_infra_workspace_detector": (
                "TestsFlextInfraInfraWorkspaceDetector",
            ),
            ".unit.test_infra_workspace_migrator": (
                "TestsFlextInfraInfraWorkspaceMigrator",
            ),
            ".unit.test_infra_workspace_migrator_deps": (
                "TestsFlextInfraInfraWorkspaceMigratorDeps",
            ),
            ".unit.test_infra_workspace_migrator_dryrun": (
                "TestsFlextInfraInfraWorkspaceMigratorDryrun",
            ),
            ".unit.test_infra_workspace_migrator_internal": (
                "TestsFlextInfraInfraWorkspaceMigratorInternal",
            ),
            ".unit.test_infra_workspace_orchestrator": (
                "TestsFlextInfraInfraWorkspaceOrchestrator",
            ),
            ".unit.transformers.test_infra_transformer_class_nesting": (
                "TestsFlextInfraTransformersInfraTransformerClassNesting",
            ),
            ".unit.transformers.test_infra_transformer_cli_modernizer": (
                "TestsFlextInfraTransformersCliModernizer",
            ),
            ".unit.transformers.test_infra_transformer_helper_consolidation": (
                "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
            ),
            ".unit.transformers.test_infra_transformer_logging_modernizer": (
                "TestsFlextInfraTransformersLoggingModernizer",
            ),
            ".unit.transformers.test_infra_transformer_nested_class_propagation": (
                "TestsFlextInfraTransformersInfraTransformerNestedClassPropagation",
            ),
            ".unit.transformers.test_infra_transformer_pattern_modernizer": (
                "TestsFlextInfraTransformersPatternModernizer",
            ),
            ".unit.transformers.test_infra_transformer_pydantic_modernizer": (
                "TestsFlextInfraTransformersPydanticModernizer",
            ),
            ".unit.transformers.test_infra_transformer_result_di_modernizer": (
                "TestsFlextInfraTransformersResultDiModernizer",
            ),
            ".unit.transformers.test_infra_transformer_tests_modernizer": (
                "TestsFlextInfraTransformersTestsModernizer",
            ),
            ".unit.validate.main_cli_tests": ("TestValidateCli",),
            ".unit.validate.namespace_validator_tests": (
                "TestFlextInfraNamespaceValidator",
            ),
            ".unit.workspace.test_main": ("TestsFlextInfraWorkspaceMain",),
            ".unit.workspace.test_makefile_dry_run": (
                "TestsFlextInfraWorkspaceMakefileDryRun",
            ),
            ".unit.workspace.test_makefile_generator": (
                "TestsFlextInfraWorkspaceMakefileGenerator",
            ),
            ".unit.workspace.test_sync": ("TestsFlextInfraWorkspaceSync",),
            ".unit.workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
            ".utilities": (
                "TestsFlextInfraUtilities",
                "u",
            ),
            "flext_tests": (
                "d",
                "e",
                "h",
                "r",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
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


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
