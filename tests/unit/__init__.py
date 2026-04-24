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
                "TestsFlextInfraUtilitiesDiscoveryConsolidated",
            ),
            "._utilities.test_formatting": (
                "TestsFlextInfraUtilitiesFormattingRunRuffFix",
            ),
            "._utilities.test_safety": (
                "TestSafetyCheckpoint",
                "TestSafetyRollback",
            ),
            "._utilities.test_scanning": ("TestScanModels",),
            ".basemk.test_init": ("TestFlextInfraBaseMk",),
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
                "TestInfraContainerFunctions",
                "TestInfraMroPattern",
                "TestInfraServiceRetrieval",
            ),
            ".deps.test_detection_classify": (
                "TestBuildProjectReport",
                "TestClassifyIssues",
                "TestDetectionUncoveredLinesClassify",
            ),
            ".deps.test_detection_deptry": (
                "TestDiscoverProjectPathsDeptry",
                "TestRunDeptry",
            ),
            ".deps.test_detection_discover": ("TestDiscoverProjectPathsSelection",),
            ".deps.test_detection_models": (
                "TestFlextInfraDependencyDetectionService",
                "TestFlextInfraModelsDependencyDetection",
                "TestToInfraValue",
            ),
            ".deps.test_detection_typings": (
                "TestLoadDependencyLimits",
                "TestRunMypyStubHints",
            ),
            ".deps.test_detection_typings_flow": ("TestDetectionTypingsFlow",),
            ".deps.test_detection_uncovered": ("TestDetectionUncoveredLines",),
            ".deps.test_detector_detect": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
            ),
            ".deps.test_detector_detect_failures": ("TestDetectorRunFailures",),
            ".deps.test_detector_init": (
                "TestFlextInfraRuntimeDevDependencyDetectorInit",
            ),
            ".deps.test_detector_main": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
                "TestMainFunction",
            ),
            ".deps.test_detector_models": ("TestFlextInfraModelsDependencyDetector",),
            ".deps.test_detector_report": (
                "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
            ),
            ".deps.test_detector_report_flags": ("TestDetectorReportFlags",),
            ".deps.test_extra_paths_manager": (
                "TestConstants",
                "TestFlextInfraExtraPathsManager",
                "TestSyncOne",
            ),
            ".deps.test_init": ("TestFlextInfraDeps",),
            ".deps.test_internal_sync_discovery": (
                "TestCollectInternalDeps",
                "TestParseGitmodules",
                "TestParseRepoMap",
            ),
            ".deps.test_internal_sync_discovery_edge": (
                "TestCollectInternalDepsEdgeCases",
            ),
            ".deps.test_internal_sync_main": ("TestMain",),
            ".deps.test_internal_sync_sync": ("TestSync",),
            ".deps.test_internal_sync_sync_edge": ("TestSyncMethodEdgeCases",),
            ".deps.test_internal_sync_sync_edge_more": ("TestSyncMethodEdgeCasesMore",),
            ".deps.test_internal_sync_update_checkout_edge": (
                "TestEnsureCheckoutEdgeCases",
            ),
            ".deps.test_internal_sync_validation": (
                "TestFlextInfraInternalDependencySyncService",
                "TestIsRelativeTo",
                "TestOwnerFromRemoteUrl",
                "TestResolveInternalRepoName",
                "TestValidateGitRefEdgeCases",
            ),
            ".deps.test_main": ("TestPublicDepsSurface",),
            ".deps.test_main_dispatch": ("TestDepsGroupEntry",),
            ".deps.test_modernizer_comments": ("TestInjectCommentsPhase",),
            ".deps.test_modernizer_consolidate": ("TestConsolidateGroupsPhase",),
            ".deps.test_modernizer_coverage": ("TestEnsureCoverageConfigPhase",),
            ".deps.test_modernizer_main": ("TestFlextInfraPyprojectModernizer",),
            ".deps.test_modernizer_main_extra": (
                "TestFlextInfraPyprojectModernizerEdgeCases",
            ),
            ".deps.test_modernizer_mypy": ("TestDepsModernizerMypy",),
            ".deps.test_modernizer_pyrefly": ("TestEnsurePyreflyConfigPhase",),
            ".deps.test_modernizer_pyright": ("TestDepsModernizerPyright",),
            ".deps.test_modernizer_pytest": ("TestEnsurePytestConfigPhase",),
            ".deps.test_modernizer_tooling": ("TestDepsModernizerTooling",),
            ".deps.test_modernizer_workspace": (
                "TestFlextInfraPyprojectModernizerWorkspace",
            ),
            ".deps.test_path_sync_init": (
                "TestDetectMode",
                "TestFlextInfraDependencyPathSync",
                "TestPathSyncEdgeCases",
            ),
            ".deps.test_path_sync_rewrite_deps": ("TestRewriteDepPaths",),
            ".deps.test_path_sync_rewrite_pep621": ("TestRewritePep621",),
            ".deps.test_path_sync_rewrite_poetry": ("TestRewritePoetry",),
            ".discovery.test_infra_discovery_edge_cases": (
                "TestFlextInfraDiscoveryServiceUncoveredLines",
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
            ".refactor.test_main_cli": ("TestFlextInfraRefactorMainCli",),
            ".runner_service": ("RealSubprocessRunner",),
            ".test_infra_constants_core": (
                "TestFlextInfraConstantsExcludedNamespace",
                "TestFlextInfraConstantsFilesNamespace",
                "TestFlextInfraConstantsGatesNamespace",
                "TestFlextInfraConstantsPathsNamespace",
                "TestFlextInfraConstantsStatusNamespace",
            ),
            ".test_infra_constants_extra": (
                "TestFlextInfraConstantsAlias",
                "TestFlextInfraConstantsCheckNamespace",
                "TestFlextInfraConstantsConsistency",
                "TestFlextInfraConstantsEncodingNamespace",
                "TestFlextInfraConstantsGithubNamespace",
                "TestFlextInfraConstantsImmutability",
            ),
            ".test_infra_init_lazy_core": ("TestFlextInfraInitLazyLoading",),
            ".test_infra_main": ("test_infra_main",),
            ".test_infra_maintenance_cli": ("test_infra_maintenance_cli",),
            ".test_infra_maintenance_init": ("TestFlextInfraMaintenance",),
            ".test_infra_maintenance_main": (
                "TestMaintenanceMainEnforcer",
                "TestMaintenanceMainSuccess",
            ),
            ".test_infra_maintenance_python_version": (
                "TestEnforcerExecute",
                "TestEnsurePythonVersionFile",
                "TestPublicProjectDiscovery",
                "TestReadRequiredMinor",
                "TestWorkspaceRoot",
            ),
            ".test_infra_paths": ("TestFlextInfraPathResolver",),
            ".test_infra_patterns_core": (
                "TestFlextInfraPatternsMarkdown",
                "TestFlextInfraPatternsTooling",
            ),
            ".test_infra_patterns_extra": (
                "TestFlextInfraPatternsEdgeCases",
                "TestFlextInfraTypesPatternsPattern",
            ),
            ".test_infra_protocols": ("TestFlextInfraProtocolsImport",),
            ".test_infra_refactor_rope_migrations": (
                "TestNestedClassPropagationRopeMigration",
                "TestSymbolPropagatorRopeMigration",
            ),
            ".test_infra_reporting_core": ("TestFlextInfraReportingServiceCore",),
            ".test_infra_reporting_extra": ("TestFlextInfraReportingServiceExtra",),
            ".test_infra_rope_service": ("TestFlextInfraRopeWorkspace",),
            ".test_infra_selection": ("TestFlextInfraUtilitiesSelection",),
            ".test_infra_typings": (
                "TestInfraTypingAdapters",
                "TestInfraTypingGuards",
            ),
            ".test_infra_utilities": ("TestFlextInfraUtilitiesImport",),
            ".test_infra_version_core": ("TestFlextInfraVersionClass",),
            ".test_infra_version_extra": (
                "TestFlextInfraVersionModuleLevel",
                "TestFlextInfraVersionPackageInfo",
            ),
            ".test_infra_versioning": ("test_infra_versioning",),
            ".test_infra_workspace_detector": ("TestWorkspaceDetector",),
            ".test_infra_workspace_init": ("TestFlextInfraWorkspace",),
            ".test_infra_workspace_migrator": ("test_infra_workspace_migrator",),
            ".test_infra_workspace_migrator_deps": (
                "TestWorkspaceMigratorDependencyBehavior",
            ),
            ".test_infra_workspace_migrator_dryrun": (
                "test_infra_workspace_migrator_dryrun",
            ),
            ".test_infra_workspace_migrator_errors": (
                "test_infra_workspace_migrator_errors",
            ),
            ".test_infra_workspace_migrator_internal": ("TestMigratorPublicBehavior",),
            ".test_infra_workspace_migrator_pyproject": (
                "test_infra_workspace_migrator_pyproject",
            ),
            ".test_infra_workspace_orchestrator": (
                "TestOrchestratorBasic",
                "TestOrchestratorFailures",
                "TestOrchestratorGateNormalization",
            ),
            ".transformers.test_infra_transformer_helper_consolidation": (
                "TestHelperConsolidationTransformer",
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
