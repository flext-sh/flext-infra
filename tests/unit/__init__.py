# AUTO-GENERATED FILE — Regenerate with: make gen
"""Unit package."""

from __future__ import annotations

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
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
            "._utilities.test_safety": ("TestsFlextInfraUtilitiessafety",),
            "._utilities.test_scanning": ("TestsFlextInfraUtilitiesscanning",),
            ".basemk.test_init": ("TestsFlextInfraBasemkInit",),
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
            ".deps.test_extra_paths_manager": ("TestsFlextInfraDepsExtraPathsManager",),
            ".deps.test_init": ("TestsFlextInfraDepsInit",),
            ".deps.test_internal_sync_discovery": (
                "TestsFlextInfraDepsInternalSyncDiscovery",
            ),
            ".deps.test_internal_sync_discovery_edge": (
                "TestsFlextInfraDepsInternalSyncDiscoveryEdge",
            ),
            ".deps.test_internal_sync_main": ("TestsFlextInfraDepsInternalSyncMain",),
            ".deps.test_internal_sync_sync": ("TestsFlextInfraDepsInternalSyncSync",),
            ".deps.test_internal_sync_sync_edge": (
                "TestsFlextInfraDepsInternalSyncSyncEdge",
            ),
            ".deps.test_internal_sync_sync_edge_more": (
                "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
            ),
            ".deps.test_internal_sync_update_checkout_edge": (
                "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
            ),
            ".deps.test_internal_sync_validation": (
                "TestsFlextInfraDepsInternalSyncValidation",
            ),
            ".deps.test_main": ("TestsFlextInfraDepsMain",),
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
            ".deps.test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
            ".deps.test_modernizer_main_extra": (
                "TestsFlextInfraDepsModernizerMainExtra",
            ),
            ".deps.test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
            ".deps.test_modernizer_pyrefly": ("TestsFlextInfraDepsModernizerPyrefly",),
            ".deps.test_modernizer_pyright": ("TestsFlextInfraDepsModernizerPyright",),
            ".deps.test_modernizer_pytest": ("TestsFlextInfraDepsModernizerPytest",),
            ".deps.test_modernizer_tooling": ("TestsFlextInfraDepsModernizerTooling",),
            ".deps.test_modernizer_workspace": (
                "TestsFlextInfraDepsModernizerWorkspace",
            ),
            ".deps.test_path_sync_init": ("TestsFlextInfraDepsPathSyncInit",),
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
            ".refactor.test_infra_refactor_safety": ("EngineSafetyStub",),
            ".refactor.test_infra_refactor_typing_unifier": (
                "FlextInfraRefactorTypingUnificationRule",
            ),
            ".refactor.test_main_cli": ("TestsFlextInfraRefactorMainCli",),
            ".runner_service": ("RealSubprocessRunner",),
            ".test_infra_constants_core": ("TestsFlextInfraInfraConstantsCore",),
            ".test_infra_constants_extra": ("TestsFlextInfraInfraConstantsExtra",),
            ".test_infra_init_lazy_core": ("TestsFlextInfraInfraInitLazyCore",),
            ".test_infra_main": ("test_infra_main",),
            ".test_infra_maintenance_cli": ("test_infra_maintenance_cli",),
            ".test_infra_maintenance_init": ("TestsFlextInfraInfraMaintenanceInit",),
            ".test_infra_maintenance_main": ("TestsFlextInfraInfraMaintenanceMain",),
            ".test_infra_maintenance_python_version": (
                "TestsFlextInfraInfraMaintenancePythonVersion",
            ),
            ".test_infra_paths": ("TestsFlextInfraInfraPaths",),
            ".test_infra_patterns_core": ("TestsFlextInfraInfraPatternsCore",),
            ".test_infra_patterns_extra": ("TestsFlextInfraInfraPatternsExtra",),
            ".test_infra_protocols": ("TestsFlextInfraInfraProtocols",),
            ".test_infra_refactor_rope_migrations": (
                "TestsFlextInfraInfraRefactorRopeMigrations",
            ),
            ".test_infra_reporting_core": ("TestsFlextInfraInfraReportingCore",),
            ".test_infra_reporting_extra": ("TestsFlextInfraInfraReportingExtra",),
            ".test_infra_rope_service": ("TestsFlextInfraInfraRopeService",),
            ".test_infra_selection": ("TestsFlextInfraInfraSelection",),
            ".test_infra_typings": ("TestsFlextInfraInfraTypings",),
            ".test_infra_utilities": ("TestsFlextInfraInfraUtilities",),
            ".test_infra_version_core": ("TestsFlextInfraInfraVersionCore",),
            ".test_infra_version_extra": ("TestsFlextInfraInfraVersionExtra",),
            ".test_infra_versioning": ("test_infra_versioning",),
            ".test_infra_workspace_detector": (
                "TestsFlextInfraInfraWorkspaceDetector",
            ),
            ".test_infra_workspace_init": ("TestsFlextInfraInfraWorkspaceInit",),
            ".test_infra_workspace_migrator": ("test_infra_workspace_migrator",),
            ".test_infra_workspace_migrator_deps": (
                "TestsFlextInfraInfraWorkspaceMigratorDeps",
            ),
            ".test_infra_workspace_migrator_dryrun": (
                "test_infra_workspace_migrator_dryrun",
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
            ".transformers.test_infra_transformer_helper_consolidation": (
                "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
            ),
            ".validate.main_cli_tests": ("TestValidateCli",),
            ".validate.namespace_validator_tests": (
                "TestFlextInfraNamespaceValidator",
            ),
            ".workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
