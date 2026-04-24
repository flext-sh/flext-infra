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
    from tests.integration.test_infra_integration import (
        TestsFlextInfraIntegrationInfraIntegration,
    )
    from tests.integration.test_refactor_nesting_idempotency import (
        TestsFlextInfraIntegrationRefactorNestingIdempotency,
    )
    from tests.integration.test_refactor_nesting_performance import (
        TestsFlextInfraIntegrationRefactorNestingPerformance,
    )
    from tests.integration.test_refactor_nesting_project import (
        TestsFlextInfraIntegrationRefactorNestingProject,
    )
    from tests.integration.test_refactor_nesting_workspace import (
        TestsFlextInfraIntegrationRefactorNestingWorkspace,
    )
    from tests.integration.test_refactor_policy_mro import (
        TestsFlextInfraIntegrationRefactorPolicyMro,
    )
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.refactor.test_rope_semantic import TestsFlextInfraRefactorRopeSemantic
    from tests.typings import TestsFlextInfraTypes, t
    from tests.unit._utilities.test_discovery_consolidated import (
        TestsFlextInfraUtilitiesdiscoveryconsolidated,
    )
    from tests.unit._utilities.test_formatting import TestsFlextInfraUtilitiesformatting
    from tests.unit._utilities.test_safety import TestsFlextInfraUtilitiessafety
    from tests.unit._utilities.test_scanning import TestsFlextInfraUtilitiesscanning
    from tests.unit.basemk.test_init import TestsFlextInfraBasemkInit
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
        TestRunCommandGateParsing,
        TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import (
        TestsExtendedProjectRunners,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
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
        TestsFlextInfraContainerInfraContainer,
    )
    from tests.unit.deps.test_detection_classify import (
        TestsFlextInfraDepsDetectionClassify,
    )
    from tests.unit.deps.test_detection_deptry import TestsFlextInfraDepsDetectionDeptry
    from tests.unit.deps.test_detection_discover import (
        TestsFlextInfraDepsDetectionDiscover,
    )
    from tests.unit.deps.test_detection_models import TestsFlextInfraDepsDetectionModels
    from tests.unit.deps.test_detection_typings import (
        TestsFlextInfraDepsDetectionTypings,
    )
    from tests.unit.deps.test_detection_typings_flow import (
        TestsFlextInfraDepsDetectionTypingsFlow,
    )
    from tests.unit.deps.test_detection_uncovered import (
        TestsFlextInfraDepsDetectionUncovered,
    )
    from tests.unit.deps.test_detector_detect import TestsFlextInfraDepsDetectorDetect
    from tests.unit.deps.test_detector_detect_failures import (
        TestsFlextInfraDepsDetectorDetectFailures,
    )
    from tests.unit.deps.test_detector_init import TestsFlextInfraDepsDetectorInit
    from tests.unit.deps.test_detector_main import TestsFlextInfraDepsDetectorMain
    from tests.unit.deps.test_detector_models import TestsFlextInfraDepsDetectorModels
    from tests.unit.deps.test_detector_report import TestsFlextInfraDepsDetectorReport
    from tests.unit.deps.test_detector_report_flags import (
        TestsFlextInfraDepsDetectorReportFlags,
    )
    from tests.unit.deps.test_extra_paths_manager import (
        TestsFlextInfraDepsExtraPathsManager,
    )
    from tests.unit.deps.test_init import TestsFlextInfraDepsInit
    from tests.unit.deps.test_internal_sync_discovery import (
        TestsFlextInfraDepsInternalSyncDiscovery,
    )
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestsFlextInfraDepsInternalSyncDiscoveryEdge,
    )
    from tests.unit.deps.test_internal_sync_main import (
        TestsFlextInfraDepsInternalSyncMain,
    )
    from tests.unit.deps.test_internal_sync_sync import (
        TestsFlextInfraDepsInternalSyncSync,
    )
    from tests.unit.deps.test_internal_sync_sync_edge import (
        TestsFlextInfraDepsInternalSyncSyncEdge,
    )
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestsFlextInfraDepsInternalSyncSyncEdgeMore,
    )
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge,
    )
    from tests.unit.deps.test_internal_sync_validation import (
        TestsFlextInfraDepsInternalSyncValidation,
    )
    from tests.unit.deps.test_main import TestsFlextInfraDepsMain
    from tests.unit.deps.test_main_dispatch import TestsFlextInfraDepsMainDispatch
    from tests.unit.deps.test_modernizer_comments import (
        TestsFlextInfraDepsModernizerComments,
    )
    from tests.unit.deps.test_modernizer_consolidate import (
        TestsFlextInfraDepsModernizerConsolidate,
    )
    from tests.unit.deps.test_modernizer_coverage import (
        TestsFlextInfraDepsModernizerCoverage,
    )
    from tests.unit.deps.test_modernizer_main import TestsFlextInfraDepsModernizerMain
    from tests.unit.deps.test_modernizer_main_extra import (
        TestsFlextInfraDepsModernizerMainExtra,
    )
    from tests.unit.deps.test_modernizer_mypy import TestsFlextInfraDepsModernizerMypy
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestsFlextInfraDepsModernizerPyrefly,
    )
    from tests.unit.deps.test_modernizer_pyright import (
        TestsFlextInfraDepsModernizerPyright,
    )
    from tests.unit.deps.test_modernizer_pytest import (
        TestsFlextInfraDepsModernizerPytest,
    )
    from tests.unit.deps.test_modernizer_tooling import (
        TestsFlextInfraDepsModernizerTooling,
    )
    from tests.unit.deps.test_modernizer_workspace import (
        TestsFlextInfraDepsModernizerWorkspace,
    )
    from tests.unit.deps.test_path_sync_init import TestsFlextInfraDepsPathSyncInit
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestsFlextInfraDepsPathSyncRewriteDeps,
    )
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestsFlextInfraDepsPathSyncRewritePep621,
    )
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestsFlextInfraDepsPathSyncRewritePoetry,
    )
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases,
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
        models_resource,
        modernizer_workspace,
        modernizer_workspace_with_projects,
        real_docs_project,
        real_makefile_project,
        real_python_package,
        real_toml_project,
        real_workspace,
        rope_workspace,
        services_resource,
        tool_config_document,
    )
    from tests.unit.fixtures_git import real_git_repo
    from tests.unit.refactor.test_infra_refactor_safety import EngineSafetyStub
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        FlextInfraRefactorTypingUnificationRule,
    )
    from tests.unit.refactor.test_main_cli import TestsFlextInfraRefactorMainCli
    from tests.unit.runner_service import RealSubprocessRunner
    from tests.unit.test_infra_constants_core import TestsFlextInfraInfraConstantsCore
    from tests.unit.test_infra_constants_extra import TestsFlextInfraInfraConstantsExtra
    from tests.unit.test_infra_init_lazy_core import TestsFlextInfraInfraInitLazyCore
    from tests.unit.test_infra_maintenance_init import (
        TestsFlextInfraInfraMaintenanceInit,
    )
    from tests.unit.test_infra_maintenance_main import (
        TestsFlextInfraInfraMaintenanceMain,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestsFlextInfraInfraMaintenancePythonVersion,
    )
    from tests.unit.test_infra_paths import TestsFlextInfraInfraPaths
    from tests.unit.test_infra_patterns_core import TestsFlextInfraInfraPatternsCore
    from tests.unit.test_infra_patterns_extra import TestsFlextInfraInfraPatternsExtra
    from tests.unit.test_infra_protocols import TestsFlextInfraInfraProtocols
    from tests.unit.test_infra_refactor_rope_migrations import (
        TestsFlextInfraInfraRefactorRopeMigrations,
    )
    from tests.unit.test_infra_reporting_core import TestsFlextInfraInfraReportingCore
    from tests.unit.test_infra_reporting_extra import TestsFlextInfraInfraReportingExtra
    from tests.unit.test_infra_rope_service import TestsFlextInfraInfraRopeService
    from tests.unit.test_infra_selection import TestsFlextInfraInfraSelection
    from tests.unit.test_infra_typings import TestsFlextInfraInfraTypings
    from tests.unit.test_infra_utilities import TestsFlextInfraInfraUtilities
    from tests.unit.test_infra_version_core import TestsFlextInfraInfraVersionCore
    from tests.unit.test_infra_version_extra import TestsFlextInfraInfraVersionExtra
    from tests.unit.test_infra_workspace_detector import (
        TestsFlextInfraInfraWorkspaceDetector,
    )
    from tests.unit.test_infra_workspace_init import TestsFlextInfraInfraWorkspaceInit
    from tests.unit.test_infra_workspace_migrator_deps import (
        TestsFlextInfraInfraWorkspaceMigratorDeps,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestsFlextInfraInfraWorkspaceMigratorInternal,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestsFlextInfraInfraWorkspaceOrchestrator,
    )
    from tests.unit.transformers.test_infra_transformer_helper_consolidation import (
        TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
    )
    from tests.unit.validate.main_cli_tests import TestValidateCli
    from tests.unit.validate.namespace_validator_tests import (
        TestFlextInfraNamespaceValidator,
    )
    from tests.unit.workspace_factory import TestsFlextInfraWorkspaceFactory
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
            ".integration.test_infra_integration": (
                "TestsFlextInfraIntegrationInfraIntegration",
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
            ".refactor.test_rope_semantic": ("TestsFlextInfraRefactorRopeSemantic",),
            ".typings": (
                "TestsFlextInfraTypes",
                "t",
            ),
            ".unit._utilities.test_discovery_consolidated": (
                "TestsFlextInfraUtilitiesdiscoveryconsolidated",
            ),
            ".unit._utilities.test_formatting": ("TestsFlextInfraUtilitiesformatting",),
            ".unit._utilities.test_safety": ("TestsFlextInfraUtilitiessafety",),
            ".unit._utilities.test_scanning": ("TestsFlextInfraUtilitiesscanning",),
            ".unit.basemk.test_init": ("TestsFlextInfraBasemkInit",),
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
                "TestsFlextInfraDepsExtraPathsManager",
            ),
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
            ".unit.deps.test_internal_sync_sync": (
                "TestsFlextInfraDepsInternalSyncSync",
            ),
            ".unit.deps.test_internal_sync_sync_edge": (
                "TestsFlextInfraDepsInternalSyncSyncEdge",
            ),
            ".unit.deps.test_internal_sync_sync_edge_more": (
                "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
            ),
            ".unit.deps.test_internal_sync_update_checkout_edge": (
                "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
            ),
            ".unit.deps.test_internal_sync_validation": (
                "TestsFlextInfraDepsInternalSyncValidation",
            ),
            ".unit.deps.test_main": ("TestsFlextInfraDepsMain",),
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
            ".unit.deps.test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
            ".unit.deps.test_modernizer_main_extra": (
                "TestsFlextInfraDepsModernizerMainExtra",
            ),
            ".unit.deps.test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
            ".unit.deps.test_modernizer_pyrefly": (
                "TestsFlextInfraDepsModernizerPyrefly",
            ),
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
            ".unit.refactor.test_infra_refactor_safety": ("EngineSafetyStub",),
            ".unit.refactor.test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
            ),
            ".unit.refactor.test_main_cli": ("TestsFlextInfraRefactorMainCli",),
            ".unit.runner_service": ("RealSubprocessRunner",),
            ".unit.test_infra_constants_core": ("TestsFlextInfraInfraConstantsCore",),
            ".unit.test_infra_constants_extra": ("TestsFlextInfraInfraConstantsExtra",),
            ".unit.test_infra_init_lazy_core": ("TestsFlextInfraInfraInitLazyCore",),
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
            ".unit.test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".unit.test_infra_reporting_core": ("TestsFlextInfraInfraReportingCore",),
            ".unit.test_infra_reporting_extra": ("TestsFlextInfraInfraReportingExtra",),
            ".unit.test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".unit.test_infra_selection": ("TestsFlextInfraInfraSelection",),
            ".unit.test_infra_typings": ("TestsFlextInfraInfraTypings",),
            ".unit.test_infra_utilities": ("TestsFlextInfraInfraUtilities",),
            ".unit.test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".unit.test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".unit.test_infra_workspace_detector": (
                "TestsFlextInfraInfraWorkspaceDetector",
            ),
            ".unit.test_infra_workspace_init": ("TestsFlextInfraInfraWorkspaceInit",),
            ".unit.test_infra_workspace_migrator_deps": (
                "TestsFlextInfraInfraWorkspaceMigratorDeps",
            ),
            ".unit.test_infra_workspace_migrator_internal": (
                "TestsFlextInfraInfraWorkspaceMigratorInternal",
            ),
            ".unit.test_infra_workspace_orchestrator": (
                "TestsFlextInfraInfraWorkspaceOrchestrator",
            ),
            ".unit.transformers.test_infra_transformer_helper_consolidation": (
                "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
            ),
            ".unit.validate.main_cli_tests": ("TestValidateCli",),
            ".unit.validate.namespace_validator_tests": (
                "TestFlextInfraNamespaceValidator",
            ),
            ".unit.workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
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
    "EngineSafetyStub",
    "FlextInfraRefactorTypingUnificationRule",
    "RealSubprocessRunner",
    "TestAllDirectoriesScanned",
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorToMarkdown",
    "TestBuilderCore",
    "TestCheckIssueFormatted",
    "TestCheckOnlyMode",
    "TestConfigFixerExecute",
    "TestConfigFixerProcessFile",
    "TestConfigFixerPublicBehavior",
    "TestConfigFixerRun",
    "TestConfigFixerToArray",
    "TestEdgeCases",
    "TestExcludedDirectories",
    "TestExtendedRunnerExtras",
    "TestFlextInfraCheck",
    "TestFlextInfraConfigFixer",
    "TestFlextInfraNamespaceValidator",
    "TestFlextInfraWorkspaceChecker",
    "TestGateErrorReportingPublicBehavior",
    "TestGenerateFile",
    "TestGenerateTypeChecking",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestProjectResultProperties",
    "TestRunCommandGateParsing",
    "TestRunProjectsPublicBehavior",
    "TestRunRuffFix",
    "TestRunnerPublicBehavior",
    "TestSelectedProjectNames",
    "TestValidateCli",
    "TestWorkspaceCheckCLI",
    "TestWorkspaceCheckCli",
    "TestWorkspaceCheckerErrorSummary",
    "TestWorkspaceCheckerResolveGates",
    "TestsExtendedProjectRunners",
    "TestsFlextInfraBasemkInit",
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsDomain",
    "TestsFlextInfraConstantsFixtures",
    "TestsFlextInfraContainerInfraContainer",
    "TestsFlextInfraDepsDetectionClassify",
    "TestsFlextInfraDepsDetectionDeptry",
    "TestsFlextInfraDepsDetectionDiscover",
    "TestsFlextInfraDepsDetectionModels",
    "TestsFlextInfraDepsDetectionTypings",
    "TestsFlextInfraDepsDetectionTypingsFlow",
    "TestsFlextInfraDepsDetectionUncovered",
    "TestsFlextInfraDepsDetectorDetect",
    "TestsFlextInfraDepsDetectorDetectFailures",
    "TestsFlextInfraDepsDetectorInit",
    "TestsFlextInfraDepsDetectorMain",
    "TestsFlextInfraDepsDetectorModels",
    "TestsFlextInfraDepsDetectorReport",
    "TestsFlextInfraDepsDetectorReportFlags",
    "TestsFlextInfraDepsExtraPathsManager",
    "TestsFlextInfraDepsInit",
    "TestsFlextInfraDepsInternalSyncDiscovery",
    "TestsFlextInfraDepsInternalSyncDiscoveryEdge",
    "TestsFlextInfraDepsInternalSyncMain",
    "TestsFlextInfraDepsInternalSyncSync",
    "TestsFlextInfraDepsInternalSyncSyncEdge",
    "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
    "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
    "TestsFlextInfraDepsInternalSyncValidation",
    "TestsFlextInfraDepsMain",
    "TestsFlextInfraDepsMainDispatch",
    "TestsFlextInfraDepsModernizerComments",
    "TestsFlextInfraDepsModernizerConsolidate",
    "TestsFlextInfraDepsModernizerCoverage",
    "TestsFlextInfraDepsModernizerMain",
    "TestsFlextInfraDepsModernizerMainExtra",
    "TestsFlextInfraDepsModernizerMypy",
    "TestsFlextInfraDepsModernizerPyrefly",
    "TestsFlextInfraDepsModernizerPyright",
    "TestsFlextInfraDepsModernizerPytest",
    "TestsFlextInfraDepsModernizerTooling",
    "TestsFlextInfraDepsModernizerWorkspace",
    "TestsFlextInfraDepsPathSyncInit",
    "TestsFlextInfraDepsPathSyncRewriteDeps",
    "TestsFlextInfraDepsPathSyncRewritePep621",
    "TestsFlextInfraDepsPathSyncRewritePoetry",
    "TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases",
    "TestsFlextInfraInfraConstantsCore",
    "TestsFlextInfraInfraConstantsExtra",
    "TestsFlextInfraInfraInitLazyCore",
    "TestsFlextInfraInfraMaintenanceInit",
    "TestsFlextInfraInfraMaintenanceMain",
    "TestsFlextInfraInfraMaintenancePythonVersion",
    "TestsFlextInfraInfraPaths",
    "TestsFlextInfraInfraPatternsCore",
    "TestsFlextInfraInfraPatternsExtra",
    "TestsFlextInfraInfraProtocols",
    "TestsFlextInfraInfraRefactorRopeMigrations",
    "TestsFlextInfraInfraReportingCore",
    "TestsFlextInfraInfraReportingExtra",
    "TestsFlextInfraInfraRopeService",
    "TestsFlextInfraInfraSelection",
    "TestsFlextInfraInfraTypings",
    "TestsFlextInfraInfraUtilities",
    "TestsFlextInfraInfraVersionCore",
    "TestsFlextInfraInfraVersionExtra",
    "TestsFlextInfraInfraWorkspaceDetector",
    "TestsFlextInfraInfraWorkspaceInit",
    "TestsFlextInfraInfraWorkspaceMigratorDeps",
    "TestsFlextInfraInfraWorkspaceMigratorInternal",
    "TestsFlextInfraInfraWorkspaceOrchestrator",
    "TestsFlextInfraIntegrationInfraIntegration",
    "TestsFlextInfraIntegrationRefactorNestingIdempotency",
    "TestsFlextInfraIntegrationRefactorNestingPerformance",
    "TestsFlextInfraIntegrationRefactorNestingProject",
    "TestsFlextInfraIntegrationRefactorNestingWorkspace",
    "TestsFlextInfraIntegrationRefactorPolicyMro",
    "TestsFlextInfraLazyInitHelpers",
    "TestsFlextInfraLazyInitTransforms",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraRefactorMainCli",
    "TestsFlextInfraRefactorRopeSemantic",
    "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesdiscoveryconsolidated",
    "TestsFlextInfraUtilitiesformatting",
    "TestsFlextInfraUtilitiessafety",
    "TestsFlextInfraUtilitiesscanning",
    "TestsFlextInfraWorkspaceFactory",
    "c",
    "d",
    "deptry_report_payload",
    "e",
    "h",
    "m",
    "models_resource",
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
    "rope_workspace",
    "s",
    "services_resource",
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
