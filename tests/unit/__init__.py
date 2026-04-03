# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import tests.unit._utilities as _tests_unit__utilities

    _utilities = _tests_unit__utilities
    import tests.unit._utilities.test_discovery_consolidated as _tests_unit__utilities_test_discovery_consolidated

    test_discovery_consolidated = _tests_unit__utilities_test_discovery_consolidated
    import tests.unit._utilities.test_formatting as _tests_unit__utilities_test_formatting
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )

    test_formatting = _tests_unit__utilities_test_formatting
    import tests.unit._utilities.test_iteration as _tests_unit__utilities_test_iteration
    from tests.unit._utilities.test_formatting import TestFormattingRunRuffFix

    test_iteration = _tests_unit__utilities_test_iteration
    import tests.unit._utilities.test_rope_hooks as _tests_unit__utilities_test_rope_hooks
    from tests.unit._utilities.test_iteration import TestIterWorkspacePythonModules

    test_rope_hooks = _tests_unit__utilities_test_rope_hooks
    import tests.unit._utilities.test_safety as _tests_unit__utilities_test_safety
    from tests.unit._utilities.test_rope_hooks import (
        test_run_rope_post_hooks_applies_mro_migration,
        test_run_rope_post_hooks_dry_run_is_non_mutating,
    )

    test_safety = _tests_unit__utilities_test_safety
    import tests.unit._utilities.test_scanning as _tests_unit__utilities_test_scanning
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )

    test_scanning = _tests_unit__utilities_test_scanning
    import tests.unit.basemk as _tests_unit_basemk
    from tests.unit._utilities.test_scanning import TestScanModels

    basemk = _tests_unit_basemk
    import tests.unit.basemk.test_engine as _tests_unit_basemk_test_engine

    test_engine = _tests_unit_basemk_test_engine
    import tests.unit.basemk.test_generator as _tests_unit_basemk_test_generator
    from tests.unit.basemk.test_engine import (
        basemk_main,
        test_basemk_cli_generate_to_file,
        test_basemk_cli_generate_to_stdout,
        test_basemk_engine_execute_calls_render_all,
        test_basemk_engine_render_all_handles_template_error,
        test_basemk_engine_render_all_returns_string,
        test_basemk_engine_render_all_with_valid_config,
        test_generator_fails_for_invalid_make_syntax,
        test_generator_renders_with_config_override,
        test_generator_write_saves_output_file,
        test_render_all_declares_and_documents_runtime_options,
        test_render_all_exposes_canonical_public_targets,
        test_render_all_generates_large_makefile,
        test_render_all_has_no_scripts_path_references,
    )

    test_generator = _tests_unit_basemk_test_generator
    import tests.unit.basemk.test_generator_edge_cases as _tests_unit_basemk_test_generator_edge_cases
    from tests.unit.basemk.test_generator import (
        test_generator_execute_returns_generated_content,
        test_generator_generate_propagates_render_failure,
        test_generator_generate_with_basemk_config_object,
        test_generator_generate_with_dict_config,
        test_generator_generate_with_invalid_dict_config,
        test_generator_generate_with_none_config_uses_default,
        test_generator_initializes_with_custom_engine,
        test_generator_initializes_with_default_engine,
        test_generator_write_creates_parent_directories,
        test_generator_write_fails_without_output_or_stream,
        test_generator_write_to_file,
        test_generator_write_to_stream,
    )

    test_generator_edge_cases = _tests_unit_basemk_test_generator_edge_cases
    import tests.unit.basemk.test_init as _tests_unit_basemk_test_init
    from tests.unit.basemk.test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror,
    )

    test_init = _tests_unit_basemk_test_init
    import tests.unit.basemk.test_main as _tests_unit_basemk_test_main
    from tests.unit.basemk.test_init import TestFlextInfraBaseMk

    test_main = _tests_unit_basemk_test_main
    import tests.unit.basemk.test_make_contract as _tests_unit_basemk_test_make_contract
    from tests.unit.basemk.test_main import (
        test_basemk_build_config_with_none,
        test_basemk_build_config_with_project_name,
        test_basemk_main_ensures_structlog_configured,
        test_basemk_main_output_to_stdout,
        test_basemk_main_rejects_apply_flag,
        test_basemk_main_with_generate_command,
        test_basemk_main_with_generation_failure,
        test_basemk_main_with_help,
        test_basemk_main_with_invalid_command,
        test_basemk_main_with_no_command,
        test_basemk_main_with_none_argv,
        test_basemk_main_with_output_file,
        test_basemk_main_with_project_name,
        test_basemk_main_with_write_failure,
    )

    test_make_contract = _tests_unit_basemk_test_make_contract
    import tests.unit.check as _tests_unit_check
    from tests.unit.basemk.test_make_contract import (
        test_make_boot_works_without_existing_venv_in_workspace_mode,
        test_make_check_fast_path_check_only_suppresses_fix_writes,
        test_make_check_file_scope_rejects_unsupported_gates,
        test_make_check_file_scope_runs_mypy,
        test_make_check_file_scope_unsets_python_path_env,
        test_make_check_full_run_forwards_fix_and_tool_args,
        test_make_check_full_run_unsets_python_path_env,
        test_make_help_lists_supported_options,
        test_rendered_base_mk_declares_cli_group_roots,
        test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight,
    )

    check = _tests_unit_check
    import tests.unit.check.cli_tests as _tests_unit_check_cli_tests
    from tests.unit.check._shared_fixtures import (
        RunProjectsMock,
        create_check_project_iter_stub,
        create_check_project_stub,
        create_checker_project,
        create_fake_run_projects,
        create_fake_run_raw,
        create_gate_execution,
        patch_gate_run,
        patch_python_dir_detection,
    )
    from tests.unit.check._stubs import (
        Spy,
        make_cmd_result,
        make_gate_exec,
        make_issue,
        make_project,
    )

    cli_tests = _tests_unit_check_cli_tests
    import tests.unit.check.extended_cli_entry_tests as _tests_unit_check_extended_cli_entry_tests
    from tests.unit.check.cli_tests import (
        test_resolve_gates_maps_type_alias,
        test_run_cli_rejects_fix_flags_for_run,
        test_run_cli_run_forwards_fix_and_tool_args,
        test_run_cli_run_returns_one_for_fail,
        test_run_cli_run_returns_two_for_error,
        test_run_cli_run_returns_zero_for_pass,
        test_run_cli_with_fail_fast_flag,
        test_run_cli_with_multiple_projects,
    )

    extended_cli_entry_tests = _tests_unit_check_extended_cli_entry_tests
    import tests.unit.check.extended_config_fixer_errors_tests as _tests_unit_check_extended_config_fixer_errors_tests
    from tests.unit.check.extended_cli_entry_tests import (
        TestCheckMainEntryPoint,
        TestFixPyrelfyCLI,
        TestRunCLIExtended,
        TestWorkspaceCheckCLI,
    )

    extended_config_fixer_errors_tests = (
        _tests_unit_check_extended_config_fixer_errors_tests
    )
    import tests.unit.check.extended_config_fixer_tests as _tests_unit_check_extended_config_fixer_tests
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPathResolution,
        TestConfigFixerRunMethods,
        TestConfigFixerRunWithVerbose,
        TestProcessFileReadError,
    )

    extended_config_fixer_tests = _tests_unit_check_extended_config_fixer_tests
    import tests.unit.check.extended_error_reporting_tests as _tests_unit_check_extended_error_reporting_tests
    from tests.unit.check.extended_config_fixer_tests import (
        TestConfigFixerEnsureProjectExcludes,
        TestConfigFixerExecute,
        TestConfigFixerFindPyprojectFiles,
        TestConfigFixerFixSearchPaths,
        TestConfigFixerProcessFile,
        TestConfigFixerRemoveIgnoreSubConfig,
        TestConfigFixerRun,
        TestConfigFixerToArray,
    )

    extended_error_reporting_tests = _tests_unit_check_extended_error_reporting_tests
    import tests.unit.check.extended_gate_bandit_markdown_tests as _tests_unit_check_extended_gate_bandit_markdown_tests
    from tests.unit.check.extended_error_reporting_tests import (
        TestErrorReporting,
        TestGoFmtEmptyLinesInOutput,
        TestMarkdownReportEmptyGates,
        TestMypyEmptyLinesInOutput,
        TestRuffFormatDuplicateFiles,
    )

    extended_gate_bandit_markdown_tests = (
        _tests_unit_check_extended_gate_bandit_markdown_tests
    )
    import tests.unit.check.extended_gate_go_cmd_tests as _tests_unit_check_extended_gate_go_cmd_tests
    from tests.unit.check.extended_gate_bandit_markdown_tests import (
        TestWorkspaceCheckerRunBandit,
        TestWorkspaceCheckerRunMarkdown,
    )

    extended_gate_go_cmd_tests = _tests_unit_check_extended_gate_go_cmd_tests
    import tests.unit.check.extended_gate_mypy_pyright_tests as _tests_unit_check_extended_gate_mypy_pyright_tests
    from tests.unit.check.extended_gate_go_cmd_tests import (
        TestWorkspaceCheckerCollectMarkdownFiles,
        TestWorkspaceCheckerRunCommand,
        TestWorkspaceCheckerRunGo,
        run_command_failure_check,
    )

    extended_gate_mypy_pyright_tests = (
        _tests_unit_check_extended_gate_mypy_pyright_tests
    )
    import tests.unit.check.extended_models_tests as _tests_unit_check_extended_models_tests
    from tests.unit.check.extended_gate_mypy_pyright_tests import (
        TestWorkspaceCheckerRunMypy,
        TestWorkspaceCheckerRunPyright,
    )

    extended_models_tests = _tests_unit_check_extended_models_tests
    import tests.unit.check.extended_project_runners_tests as _tests_unit_check_extended_project_runners_tests
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary,
    )

    extended_project_runners_tests = _tests_unit_check_extended_project_runners_tests
    import tests.unit.check.extended_projects_tests as _tests_unit_check_extended_projects_tests
    from tests.unit.check.extended_project_runners_tests import TestJsonWriteFailure

    extended_projects_tests = _tests_unit_check_extended_projects_tests
    import tests.unit.check.extended_resolve_gates_tests as _tests_unit_check_extended_resolve_gates_tests
    from tests.unit.check.extended_projects_tests import (
        TestCheckProjectRunners,
        TestLintAndFormatPublicMethods,
    )

    extended_resolve_gates_tests = _tests_unit_check_extended_resolve_gates_tests
    import tests.unit.check.extended_run_projects_tests as _tests_unit_check_extended_run_projects_tests
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates,
    )

    extended_run_projects_tests = _tests_unit_check_extended_run_projects_tests
    import tests.unit.check.extended_runners_extra_tests as _tests_unit_check_extended_runners_extra_tests
    from tests.unit.check.extended_run_projects_tests import (
        CheckProjectStub,
        TestRunProjectFixMode,
        TestRunProjectsBehavior,
        TestRunProjectsReports,
        TestRunProjectsValidation,
        TestRunSingleProject,
    )

    extended_runners_extra_tests = _tests_unit_check_extended_runners_extra_tests
    import tests.unit.check.extended_runners_go_tests as _tests_unit_check_extended_runners_go_tests
    from tests.unit.check.extended_runners_extra_tests import (
        GateClass,
        TestRunBandit,
        TestRunMarkdown,
        TestRunPyright,
    )

    extended_runners_go_tests = _tests_unit_check_extended_runners_go_tests
    import tests.unit.check.extended_runners_ruff_tests as _tests_unit_check_extended_runners_ruff_tests
    from tests.unit.check.extended_runners_go_tests import RunCallable, TestRunGo

    extended_runners_ruff_tests = _tests_unit_check_extended_runners_ruff_tests
    import tests.unit.check.extended_runners_tests as _tests_unit_check_extended_runners_tests
    from tests.unit.check.extended_runners_ruff_tests import (
        TestCollectMarkdownFiles,
        TestRunCommand,
        TestRunPyrightArgs,
        TestRunRuffFormat,
        TestRunRuffLint,
    )

    extended_runners_tests = _tests_unit_check_extended_runners_tests
    import tests.unit.check.extended_workspace_init_tests as _tests_unit_check_extended_workspace_init_tests
    from tests.unit.check.extended_runners_tests import TestRunMypy, TestRunPyrefly

    extended_workspace_init_tests = _tests_unit_check_extended_workspace_init_tests
    import tests.unit.check.fix_pyrefly_config_tests as _tests_unit_check_fix_pyrefly_config_tests
    from tests.unit.check.extended_workspace_init_tests import (
        TestWorkspaceCheckerBuildGateResult,
        TestWorkspaceCheckerDirsWithPy,
        TestWorkspaceCheckerExecute,
        TestWorkspaceCheckerExistingCheckDirs,
        TestWorkspaceCheckerInitialization,
        TestWorkspaceCheckerInitOSError,
        TestWorkspaceCheckerResolveWorkspaceRootFallback,
    )

    fix_pyrefly_config_tests = _tests_unit_check_fix_pyrefly_config_tests
    import tests.unit.check.init_tests as _tests_unit_check_init_tests
    from tests.unit.check.fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help,
    )

    init_tests = _tests_unit_check_init_tests
    import tests.unit.check.main_tests as _tests_unit_check_main_tests
    from tests.unit.check.init_tests import TestFlextInfraCheck

    main_tests = _tests_unit_check_main_tests
    import tests.unit.check.pyrefly_tests as _tests_unit_check_pyrefly_tests
    from tests.unit.check.main_tests import test_check_main_executes_real_cli

    pyrefly_tests = _tests_unit_check_pyrefly_tests
    import tests.unit.check.workspace_check_tests as _tests_unit_check_workspace_check_tests
    from tests.unit.check.pyrefly_tests import TestFlextInfraConfigFixer

    workspace_check_tests = _tests_unit_check_workspace_check_tests
    import tests.unit.check.workspace_tests as _tests_unit_check_workspace_tests
    from tests.unit.check.workspace_check_tests import (
        test_workspace_check_main_returns_error_without_projects,
    )

    workspace_tests = _tests_unit_check_workspace_tests
    import tests.unit.codegen as _tests_unit_codegen
    from tests.unit.check.workspace_tests import TestFlextInfraWorkspaceChecker

    codegen = _tests_unit_codegen
    import tests.unit.codegen.autofix_workspace_tests as _tests_unit_codegen_autofix_workspace_tests
    from tests.unit.codegen._project_factory import FlextInfraCodegenTestProjectFactory

    autofix_workspace_tests = _tests_unit_codegen_autofix_workspace_tests
    import tests.unit.codegen.census_models_tests as _tests_unit_codegen_census_models_tests
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )

    census_models_tests = _tests_unit_codegen_census_models_tests
    import tests.unit.codegen.census_tests as _tests_unit_codegen_census_tests
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )

    census_tests = _tests_unit_codegen_census_tests
    import tests.unit.codegen.constants_quality_gate_tests as _tests_unit_codegen_constants_quality_gate_tests
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )

    constants_quality_gate_tests = _tests_unit_codegen_constants_quality_gate_tests
    import tests.unit.codegen.lazy_init_generation_tests as _tests_unit_codegen_lazy_init_generation_tests
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )

    lazy_init_generation_tests = _tests_unit_codegen_lazy_init_generation_tests
    import tests.unit.codegen.lazy_init_helpers_tests as _tests_unit_codegen_lazy_init_helpers_tests
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )

    lazy_init_helpers_tests = _tests_unit_codegen_lazy_init_helpers_tests
    import tests.unit.codegen.lazy_init_process_tests as _tests_unit_codegen_lazy_init_process_tests
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )

    lazy_init_process_tests = _tests_unit_codegen_lazy_init_process_tests
    import tests.unit.codegen.lazy_init_service_tests as _tests_unit_codegen_lazy_init_service_tests
    from tests.unit.codegen.lazy_init_process_tests import TestProcessDirectory

    lazy_init_service_tests = _tests_unit_codegen_lazy_init_service_tests
    import tests.unit.codegen.lazy_init_tests as _tests_unit_codegen_lazy_init_tests
    from tests.unit.codegen.lazy_init_service_tests import TestFlextInfraCodegenLazyInit

    lazy_init_tests = _tests_unit_codegen_lazy_init_tests
    import tests.unit.codegen.lazy_init_transforms_tests as _tests_unit_codegen_lazy_init_transforms_tests
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )

    lazy_init_transforms_tests = _tests_unit_codegen_lazy_init_transforms_tests
    import tests.unit.codegen.pipeline_tests as _tests_unit_codegen_pipeline_tests
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanPublicDefs,
        TestShouldBubbleUp,
    )
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )

    pipeline_tests = _tests_unit_codegen_pipeline_tests
    import tests.unit.codegen.scaffolder_naming_tests as _tests_unit_codegen_scaffolder_naming_tests
    from tests.unit.codegen.pipeline_tests import test_codegen_pipeline_end_to_end

    scaffolder_naming_tests = _tests_unit_codegen_scaffolder_naming_tests
    import tests.unit.codegen.scaffolder_tests as _tests_unit_codegen_scaffolder_tests
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )

    scaffolder_tests = _tests_unit_codegen_scaffolder_tests
    import tests.unit.container as _tests_unit_container
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )

    container = _tests_unit_container
    import tests.unit.container.test_infra_container as _tests_unit_container_test_infra_container

    test_infra_container = _tests_unit_container_test_infra_container
    import tests.unit.deps as _tests_unit_deps
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions,
        TestInfraMroPattern,
        TestInfraServiceRetrieval,
    )

    deps = _tests_unit_deps
    import tests.unit.deps.test_detection_classify as _tests_unit_deps_test_detection_classify

    test_detection_classify = _tests_unit_deps_test_detection_classify
    import tests.unit.deps.test_detection_deptry as _tests_unit_deps_test_detection_deptry
    from tests.unit.deps.test_detection_classify import (
        TestBuildProjectReport,
        TestClassifyIssues,
    )

    test_detection_deptry = _tests_unit_deps_test_detection_deptry
    import tests.unit.deps.test_detection_discover as _tests_unit_deps_test_detection_discover
    from tests.unit.deps.test_detection_deptry import TestRunDeptry

    test_detection_discover = _tests_unit_deps_test_detection_discover
    import tests.unit.deps.test_detection_models as _tests_unit_deps_test_detection_models

    test_detection_models = _tests_unit_deps_test_detection_models
    import tests.unit.deps.test_detection_pip_check as _tests_unit_deps_test_detection_pip_check
    from tests.unit.deps.test_detection_models import (
        TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService,
        TestToInfraValue,
    )

    test_detection_pip_check = _tests_unit_deps_test_detection_pip_check
    import tests.unit.deps.test_detection_typings as _tests_unit_deps_test_detection_typings
    from tests.unit.deps.test_detection_pip_check import TestRunPipCheck

    test_detection_typings = _tests_unit_deps_test_detection_typings
    import tests.unit.deps.test_detection_typings_flow as _tests_unit_deps_test_detection_typings_flow
    from tests.unit.deps.test_detection_typings import (
        TestLoadDependencyLimits,
        TestRunMypyStubHints,
    )

    test_detection_typings_flow = _tests_unit_deps_test_detection_typings_flow
    import tests.unit.deps.test_detection_uncovered as _tests_unit_deps_test_detection_uncovered
    from tests.unit.deps.test_detection_typings_flow import TestModuleAndTypingsFlow

    test_detection_uncovered = _tests_unit_deps_test_detection_uncovered
    import tests.unit.deps.test_detector_detect as _tests_unit_deps_test_detector_detect
    from tests.unit.deps.test_detection_uncovered import TestDetectionUncoveredLines

    test_detector_detect = _tests_unit_deps_test_detector_detect
    import tests.unit.deps.test_detector_detect_failures as _tests_unit_deps_test_detector_detect_failures
    from tests.unit.deps.test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )

    test_detector_detect_failures = _tests_unit_deps_test_detector_detect_failures
    import tests.unit.deps.test_detector_init as _tests_unit_deps_test_detector_init
    from tests.unit.deps.test_detector_detect_failures import TestDetectorRunFailures

    test_detector_init = _tests_unit_deps_test_detector_init
    import tests.unit.deps.test_detector_main as _tests_unit_deps_test_detector_main
    from tests.unit.deps.test_detector_init import (
        TestFlextInfraRuntimeDevDependencyDetectorInit,
    )

    test_detector_main = _tests_unit_deps_test_detector_main
    import tests.unit.deps.test_detector_models as _tests_unit_deps_test_detector_models
    from tests.unit.deps.test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction,
    )

    test_detector_models = _tests_unit_deps_test_detector_models
    import tests.unit.deps.test_detector_report as _tests_unit_deps_test_detector_report
    from tests.unit.deps.test_detector_models import (
        TestFlextInfraDependencyDetectorModels,
    )

    test_detector_report = _tests_unit_deps_test_detector_report
    import tests.unit.deps.test_detector_report_flags as _tests_unit_deps_test_detector_report_flags
    from tests.unit.deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )

    test_detector_report_flags = _tests_unit_deps_test_detector_report_flags
    import tests.unit.deps.test_extra_paths_manager as _tests_unit_deps_test_extra_paths_manager
    from tests.unit.deps.test_detector_report_flags import TestDetectorReportFlags

    test_extra_paths_manager = _tests_unit_deps_test_extra_paths_manager
    import tests.unit.deps.test_extra_paths_pep621 as _tests_unit_deps_test_extra_paths_pep621
    from tests.unit.deps.test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestGetDepPaths,
        TestSyncOne,
        test_pyrefly_search_paths_include_workspace_declared_dev_dependencies,
    )

    test_extra_paths_pep621 = _tests_unit_deps_test_extra_paths_pep621
    import tests.unit.deps.test_extra_paths_sync as _tests_unit_deps_test_extra_paths_sync
    from tests.unit.deps.test_extra_paths_pep621 import (
        TestPathDepPathsPep621,
        TestPathDepPathsPoetry,
    )

    test_extra_paths_sync = _tests_unit_deps_test_extra_paths_sync
    import tests.unit.deps.test_internal_sync_discovery as _tests_unit_deps_test_internal_sync_discovery
    from tests.unit.deps.test_extra_paths_sync import (
        pyright_content,
        test_main_success_modes,
        test_main_sync_failure,
        test_sync_extra_paths_missing_root_pyproject,
        test_sync_extra_paths_success_modes,
        test_sync_extra_paths_sync_failure,
        test_sync_one_edge_cases,
    )
    from tests.unit.deps.test_init import TestFlextInfraDeps

    test_internal_sync_discovery = _tests_unit_deps_test_internal_sync_discovery
    import tests.unit.deps.test_internal_sync_discovery_edge as _tests_unit_deps_test_internal_sync_discovery_edge
    from tests.unit.deps.test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )

    test_internal_sync_discovery_edge = (
        _tests_unit_deps_test_internal_sync_discovery_edge
    )
    import tests.unit.deps.test_internal_sync_main as _tests_unit_deps_test_internal_sync_main
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestCollectInternalDepsEdgeCases,
    )

    test_internal_sync_main = _tests_unit_deps_test_internal_sync_main
    import tests.unit.deps.test_internal_sync_resolve as _tests_unit_deps_test_internal_sync_resolve

    test_internal_sync_resolve = _tests_unit_deps_test_internal_sync_resolve
    import tests.unit.deps.test_internal_sync_sync as _tests_unit_deps_test_internal_sync_sync
    from tests.unit.deps.test_internal_sync_resolve import (
        TestInferOwnerFromOrigin,
        TestResolveRef,
        TestSynthesizedRepoMap,
    )

    test_internal_sync_sync = _tests_unit_deps_test_internal_sync_sync
    import tests.unit.deps.test_internal_sync_sync_edge as _tests_unit_deps_test_internal_sync_sync_edge
    from tests.unit.deps.test_internal_sync_sync import TestSync

    test_internal_sync_sync_edge = _tests_unit_deps_test_internal_sync_sync_edge
    import tests.unit.deps.test_internal_sync_sync_edge_more as _tests_unit_deps_test_internal_sync_sync_edge_more
    from tests.unit.deps.test_internal_sync_sync_edge import TestSyncMethodEdgeCases

    test_internal_sync_sync_edge_more = (
        _tests_unit_deps_test_internal_sync_sync_edge_more
    )
    import tests.unit.deps.test_internal_sync_update as _tests_unit_deps_test_internal_sync_update
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestSyncMethodEdgeCasesMore,
    )

    test_internal_sync_update = _tests_unit_deps_test_internal_sync_update
    import tests.unit.deps.test_internal_sync_update_checkout_edge as _tests_unit_deps_test_internal_sync_update_checkout_edge
    from tests.unit.deps.test_internal_sync_update import (
        TestEnsureCheckout,
        TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases,
    )

    test_internal_sync_update_checkout_edge = (
        _tests_unit_deps_test_internal_sync_update_checkout_edge
    )
    import tests.unit.deps.test_internal_sync_validation as _tests_unit_deps_test_internal_sync_validation
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases,
    )

    test_internal_sync_validation = _tests_unit_deps_test_internal_sync_validation
    import tests.unit.deps.test_internal_sync_workspace as _tests_unit_deps_test_internal_sync_workspace
    from tests.unit.deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases,
    )

    test_internal_sync_workspace = _tests_unit_deps_test_internal_sync_workspace
    import tests.unit.deps.test_main_dispatch as _tests_unit_deps_test_main_dispatch
    from tests.unit.deps.test_internal_sync_workspace import (
        TestIsWorkspaceMode,
        TestWorkspaceRootFromEnv,
        TestWorkspaceRootFromParents,
    )
    from tests.unit.deps.test_main import (
        TestMainHelpAndErrors,
        TestMainReturnValues,
        TestSubcommandMapping,
    )

    test_main_dispatch = _tests_unit_deps_test_main_dispatch
    import tests.unit.deps.test_modernizer_comments as _tests_unit_deps_test_modernizer_comments
    from tests.unit.deps.test_main_dispatch import (
        TestMainDelegation,
        TestMainExceptionHandling,
        TestMainModuleImport,
        TestMainSubcommandDispatch,
        TestMainSysArgvModification,
        test_string_zero_return_value,
    )

    test_modernizer_comments = _tests_unit_deps_test_modernizer_comments
    import tests.unit.deps.test_modernizer_consolidate as _tests_unit_deps_test_modernizer_consolidate
    from tests.unit.deps.test_modernizer_comments import (
        TestInjectCommentsPhase,
        test_inject_comments_phase_apply_banner,
        test_inject_comments_phase_apply_broken_group_section,
        test_inject_comments_phase_apply_markers,
        test_inject_comments_phase_apply_with_optional_dependencies_dev,
        test_inject_comments_phase_deduplicates_family_markers,
        test_inject_comments_phase_marks_pytest_and_coverage_subtables,
        test_inject_comments_phase_removes_auto_banner_and_auto_marker,
        test_inject_comments_phase_repositions_marker_before_section,
    )

    test_modernizer_consolidate = _tests_unit_deps_test_modernizer_consolidate
    import tests.unit.deps.test_modernizer_coverage as _tests_unit_deps_test_modernizer_coverage
    from tests.unit.deps.test_modernizer_consolidate import (
        TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )

    test_modernizer_coverage = _tests_unit_deps_test_modernizer_coverage
    import tests.unit.deps.test_modernizer_helpers as _tests_unit_deps_test_modernizer_helpers
    from tests.unit.deps.test_modernizer_coverage import TestEnsureCoverageConfigPhase

    test_modernizer_helpers = _tests_unit_deps_test_modernizer_helpers
    import tests.unit.deps.test_modernizer_main as _tests_unit_deps_test_modernizer_main
    from tests.unit.deps.test_modernizer_helpers import (
        doc,
        test_array,
        test_as_string_list,
        test_as_string_list_toml_item,
        test_canonical_dev_dependencies,
        test_declared_dependency_names_collects_all_supported_groups,
        test_dedupe_specs,
        test_dep_name,
        test_ensure_table,
        test_project_dev_groups,
        test_project_dev_groups_missing_sections,
        test_unwrap_item,
        test_unwrap_item_toml_item,
    )

    test_modernizer_main = _tests_unit_deps_test_modernizer_main
    import tests.unit.deps.test_modernizer_main_extra as _tests_unit_deps_test_modernizer_main_extra
    from tests.unit.deps.test_modernizer_main import (
        TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain,
    )

    test_modernizer_main_extra = _tests_unit_deps_test_modernizer_main_extra
    import tests.unit.deps.test_modernizer_pyrefly as _tests_unit_deps_test_modernizer_pyrefly
    from tests.unit.deps.test_modernizer_main_extra import (
        TestModernizerEdgeCases,
        TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )

    test_modernizer_pyrefly = _tests_unit_deps_test_modernizer_pyrefly
    import tests.unit.deps.test_modernizer_pyright as _tests_unit_deps_test_modernizer_pyright
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path,
    )

    test_modernizer_pyright = _tests_unit_deps_test_modernizer_pyright
    import tests.unit.deps.test_modernizer_pytest as _tests_unit_deps_test_modernizer_pytest
    from tests.unit.deps.test_modernizer_pyright import TestEnsurePyrightConfigPhase

    test_modernizer_pytest = _tests_unit_deps_test_modernizer_pytest
    import tests.unit.deps.test_modernizer_workspace as _tests_unit_deps_test_modernizer_workspace
    from tests.unit.deps.test_modernizer_pytest import (
        TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes,
    )

    test_modernizer_workspace = _tests_unit_deps_test_modernizer_workspace
    import tests.unit.deps.test_path_sync_helpers as _tests_unit_deps_test_path_sync_helpers
    from tests.unit.deps.test_modernizer_workspace import (
        TestParser,
        TestReadDoc,
        test_workspace_root_doc_construction,
    )

    test_path_sync_helpers = _tests_unit_deps_test_path_sync_helpers
    import tests.unit.deps.test_path_sync_init as _tests_unit_deps_test_path_sync_init
    from tests.unit.deps.test_path_sync_helpers import (
        extract_dep_name,
        test_extract_dep_name,
        test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers,
        test_target_path,
    )

    test_path_sync_init = _tests_unit_deps_test_path_sync_init
    import tests.unit.deps.test_path_sync_main as _tests_unit_deps_test_path_sync_main
    from tests.unit.deps.test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object,
    )

    test_path_sync_main = _tests_unit_deps_test_path_sync_main
    import tests.unit.deps.test_path_sync_main_edges as _tests_unit_deps_test_path_sync_main_edges

    test_path_sync_main_edges = _tests_unit_deps_test_path_sync_main_edges
    import tests.unit.deps.test_path_sync_main_more as _tests_unit_deps_test_path_sync_main_more
    from tests.unit.deps.test_path_sync_main_edges import TestMainEdgeCases

    test_path_sync_main_more = _tests_unit_deps_test_path_sync_main_more
    import tests.unit.deps.test_path_sync_main_project_obj as _tests_unit_deps_test_path_sync_main_project_obj
    from tests.unit.deps.test_path_sync_main_more import (
        test_main_discovery_failure,
        test_main_no_changes_needed,
        test_main_project_invalid_toml,
        test_main_project_no_name,
        test_main_project_non_string_name,
        test_main_with_changes_and_dry_run,
        test_main_with_changes_no_dry_run,
        test_workspace_root_fallback,
    )

    test_path_sync_main_project_obj = _tests_unit_deps_test_path_sync_main_project_obj
    import tests.unit.deps.test_path_sync_rewrite_deps as _tests_unit_deps_test_path_sync_rewrite_deps
    from tests.unit.deps.test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop,
    )

    test_path_sync_rewrite_deps = _tests_unit_deps_test_path_sync_rewrite_deps
    import tests.unit.deps.test_path_sync_rewrite_pep621 as _tests_unit_deps_test_path_sync_rewrite_pep621
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestRewriteDepPaths,
        rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps,
    )

    test_path_sync_rewrite_pep621 = _tests_unit_deps_test_path_sync_rewrite_pep621
    import tests.unit.deps.test_path_sync_rewrite_poetry as _tests_unit_deps_test_path_sync_rewrite_poetry
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item,
    )

    test_path_sync_rewrite_poetry = _tests_unit_deps_test_path_sync_rewrite_poetry
    import tests.unit.discovery as _tests_unit_discovery
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value,
    )

    discovery = _tests_unit_discovery
    import tests.unit.discovery.test_infra_discovery as _tests_unit_discovery_test_infra_discovery

    test_infra_discovery = _tests_unit_discovery_test_infra_discovery
    import tests.unit.discovery.test_infra_discovery_edge_cases as _tests_unit_discovery_test_infra_discovery_edge_cases
    from tests.unit.discovery.test_infra_discovery import TestFlextInfraDiscoveryService

    test_infra_discovery_edge_cases = (
        _tests_unit_discovery_test_infra_discovery_edge_cases
    )
    import tests.unit.docs as _tests_unit_docs
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines,
    )

    docs = _tests_unit_docs
    import tests.unit.docs.auditor_budgets_tests as _tests_unit_docs_auditor_budgets_tests

    auditor_budgets_tests = _tests_unit_docs_auditor_budgets_tests
    import tests.unit.docs.auditor_cli_tests as _tests_unit_docs_auditor_cli_tests
    from tests.unit.docs.auditor_budgets_tests import TestLoadAuditBudgets

    auditor_cli_tests = _tests_unit_docs_auditor_cli_tests
    import tests.unit.docs.auditor_links_tests as _tests_unit_docs_auditor_links_tests
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli,
        TestAuditorScopeFailure,
    )

    auditor_links_tests = _tests_unit_docs_auditor_links_tests
    import tests.unit.docs.auditor_scope_tests as _tests_unit_docs_auditor_scope_tests
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorToMarkdown,
    )

    auditor_scope_tests = _tests_unit_docs_auditor_scope_tests
    import tests.unit.docs.auditor_tests as _tests_unit_docs_auditor_tests
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms,
        TestAuditorScope,
    )

    auditor_tests = _tests_unit_docs_auditor_tests
    import tests.unit.docs.builder_scope_tests as _tests_unit_docs_builder_scope_tests
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )

    builder_scope_tests = _tests_unit_docs_builder_scope_tests
    import tests.unit.docs.builder_tests as _tests_unit_docs_builder_tests
    from tests.unit.docs.builder_scope_tests import TestBuilderScope

    builder_tests = _tests_unit_docs_builder_tests
    import tests.unit.docs.fixer_internals_tests as _tests_unit_docs_fixer_internals_tests
    from tests.unit.docs.builder_tests import TestBuilderCore, builder

    fixer_internals_tests = _tests_unit_docs_fixer_internals_tests
    import tests.unit.docs.fixer_tests as _tests_unit_docs_fixer_tests
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )

    fixer_tests = _tests_unit_docs_fixer_tests
    import tests.unit.docs.generator_internals_tests as _tests_unit_docs_generator_internals_tests
    from tests.unit.docs.fixer_tests import TestFixerCore

    generator_internals_tests = _tests_unit_docs_generator_internals_tests
    import tests.unit.docs.generator_tests as _tests_unit_docs_generator_tests
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers,
        TestGeneratorScope,
        gen,
    )

    generator_tests = _tests_unit_docs_generator_tests
    import tests.unit.docs.main_commands_tests as _tests_unit_docs_main_commands_tests
    from tests.unit.docs.generator_tests import TestGeneratorCore
    from tests.unit.docs.init_tests import TestFlextInfraDocs

    main_commands_tests = _tests_unit_docs_main_commands_tests
    import tests.unit.docs.main_entry_tests as _tests_unit_docs_main_entry_tests
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild,
        TestRunGenerate,
        TestRunValidate,
    )

    main_entry_tests = _tests_unit_docs_main_entry_tests
    import tests.unit.docs.shared_iter_tests as _tests_unit_docs_shared_iter_tests
    from tests.unit.docs.main_entry_tests import TestMainRouting, TestMainWithFlags
    from tests.unit.docs.main_tests import TestRunAudit, TestRunFix

    shared_iter_tests = _tests_unit_docs_shared_iter_tests
    import tests.unit.docs.shared_tests as _tests_unit_docs_shared_tests
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles,
        TestSelectedProjectNames,
    )

    shared_tests = _tests_unit_docs_shared_tests
    import tests.unit.docs.shared_write_tests as _tests_unit_docs_shared_write_tests
    from tests.unit.docs.shared_tests import TestBuildScopes, TestFlextInfraDocScope

    shared_write_tests = _tests_unit_docs_shared_write_tests
    import tests.unit.docs.validator_internals_tests as _tests_unit_docs_validator_internals_tests
    from tests.unit.docs.shared_write_tests import TestWriteJson, TestWriteMarkdown

    validator_internals_tests = _tests_unit_docs_validator_internals_tests
    import tests.unit.docs.validator_tests as _tests_unit_docs_validator_tests
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )

    validator_tests = _tests_unit_docs_validator_tests
    import tests.unit.github as _tests_unit_github
    from tests.unit.docs.validator_tests import TestValidateCore, TestValidateReport

    github = _tests_unit_github
    import tests.unit.github.main_cli_tests as _tests_unit_github_main_cli_tests
    from tests.unit.github._stubs import (
        StubCommandOutput,
        StubJsonIo,
        StubLinter,
        StubPrManager,
        StubProjectInfo,
        StubReporting,
        StubRunner,
        StubSelector,
        StubSyncer,
        StubTemplates,
        StubUtilities,
        StubVersioning,
        StubWorkspaceManager,
    )

    main_cli_tests = _tests_unit_github_main_cli_tests
    import tests.unit.github.main_dispatch_tests as _tests_unit_github_main_dispatch_tests
    from tests.unit.github.main_cli_tests import (
        test_main_returns_nonzero_on_unknown,
        test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options,
    )

    main_dispatch_tests = _tests_unit_github_main_dispatch_tests
    import tests.unit.github.main_integration_tests as _tests_unit_github_main_integration_tests
    from tests.unit.github.main_dispatch_tests import TestRunPrWorkspace

    main_integration_tests = _tests_unit_github_main_integration_tests
    import tests.unit.io as _tests_unit_io
    from tests.unit.github.main_integration_tests import TestMain
    from tests.unit.github.main_tests import TestRunLint, TestRunPr, TestRunWorkflows

    io = _tests_unit_io
    import tests.unit.io.test_infra_json_io as _tests_unit_io_test_infra_json_io

    test_infra_json_io = _tests_unit_io_test_infra_json_io
    import tests.unit.io.test_infra_output_edge_cases as _tests_unit_io_test_infra_output_edge_cases
    from tests.unit.io.test_infra_json_io import SampleModel, TestFlextInfraJsonService

    test_infra_output_edge_cases = _tests_unit_io_test_infra_output_edge_cases
    import tests.unit.io.test_infra_output_formatting as _tests_unit_io_test_infra_output_formatting
    from tests.unit.io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases,
        TestInfraOutputNoColor,
        TestMroFacadeMethods,
    )

    test_infra_output_formatting = _tests_unit_io_test_infra_output_formatting
    import tests.unit.io.test_infra_terminal_detection as _tests_unit_io_test_infra_terminal_detection
    from tests.unit.io.test_infra_output_formatting import (
        ANSI_RE,
        TestInfraOutputHeader,
        TestInfraOutputMessages,
        TestInfraOutputProgress,
        TestInfraOutputStatus,
        TestInfraOutputSummary,
    )

    test_infra_terminal_detection = _tests_unit_io_test_infra_terminal_detection
    import tests.unit.refactor as _tests_unit_refactor
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor,
        TestShouldUseUnicode,
    )

    refactor = _tests_unit_refactor
    import tests.unit.refactor.test_infra_refactor_analysis as _tests_unit_refactor_test_infra_refactor_analysis

    test_infra_refactor_analysis = _tests_unit_refactor_test_infra_refactor_analysis
    import tests.unit.refactor.test_infra_refactor_class_and_propagation as _tests_unit_refactor_test_infra_refactor_class_and_propagation
    from tests.unit.refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files,
    )

    test_infra_refactor_class_and_propagation = (
        _tests_unit_refactor_test_infra_refactor_class_and_propagation
    )
    import tests.unit.refactor.test_infra_refactor_class_placement as _tests_unit_refactor_test_infra_refactor_class_placement
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
        test_class_reconstructor_reorders_each_contiguous_method_block,
        test_class_reconstructor_reorders_methods_by_config,
        test_class_reconstructor_skips_interleaved_non_method_members,
        test_signature_propagation_removes_and_adds_keywords,
        test_signature_propagation_renames_call_keyword,
        test_symbol_propagation_keeps_alias_reference_when_asname_used,
        test_symbol_propagation_renames_import_and_local_references,
        test_symbol_propagation_updates_mro_base_references,
    )

    test_infra_refactor_class_placement = (
        _tests_unit_refactor_test_infra_refactor_class_placement
    )
    import tests.unit.refactor.test_infra_refactor_engine as _tests_unit_refactor_test_infra_refactor_engine
    from tests.unit.refactor.test_infra_refactor_class_placement import (
        test_detects_attribute_base_class,
        test_detects_basemodel_in_non_model_file,
        test_detects_multiple_models,
        test_non_pydantic_class_not_flagged,
        test_skips_models_directory,
        test_skips_models_file,
        test_skips_private_class,
        test_skips_protected_files,
        test_skips_settings_file,
    )

    test_infra_refactor_engine = _tests_unit_refactor_test_infra_refactor_engine
    import tests.unit.refactor.test_infra_refactor_import_modernizer as _tests_unit_refactor_test_infra_refactor_import_modernizer
    from tests.unit.refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata,
    )

    test_infra_refactor_import_modernizer = (
        _tests_unit_refactor_test_infra_refactor_import_modernizer
    )
    import tests.unit.refactor.test_infra_refactor_legacy_and_annotations as _tests_unit_refactor_test_infra_refactor_legacy_and_annotations
    from tests.unit.refactor.test_infra_refactor_import_modernizer import (
        test_import_modernizer_adds_c_when_existing_c_is_aliased,
        test_import_modernizer_does_not_rewrite_function_parameter_shadow,
        test_import_modernizer_does_not_rewrite_rebound_local_name_usage,
        test_import_modernizer_partial_import_keeps_unmapped_symbols,
        test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias,
        test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function,
        test_import_modernizer_skips_when_runtime_alias_name_is_blocked,
        test_import_modernizer_updates_aliased_symbol_usage,
        test_lazy_import_rule_hoists_import_to_module_level,
        test_lazy_import_rule_uses_fix_action_for_hoist,
    )

    test_infra_refactor_legacy_and_annotations = (
        _tests_unit_refactor_test_infra_refactor_legacy_and_annotations
    )
    import tests.unit.refactor.test_infra_refactor_mro_completeness as _tests_unit_refactor_test_infra_refactor_mro_completeness
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
        test_ensure_future_annotations_after_docstring,
        test_ensure_future_annotations_moves_existing_import_to_top,
        test_legacy_import_bypass_collapses_to_primary_import,
        test_legacy_rule_uses_fix_action_remove_for_aliases,
        test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias,
        test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias,
        test_legacy_wrapper_function_is_inlined_as_alias,
        test_legacy_wrapper_non_passthrough_is_not_inlined,
    )

    test_infra_refactor_mro_completeness = (
        _tests_unit_refactor_test_infra_refactor_mro_completeness
    )
    import tests.unit.refactor.test_infra_refactor_mro_import_rewriter as _tests_unit_refactor_test_infra_refactor_mro_import_rewriter
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files,
        test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases,
    )

    test_infra_refactor_mro_import_rewriter = (
        _tests_unit_refactor_test_infra_refactor_mro_import_rewriter
    )
    import tests.unit.refactor.test_infra_refactor_namespace_aliases as _tests_unit_refactor_test_infra_refactor_namespace_aliases
    from tests.unit.refactor.test_infra_refactor_mro_import_rewriter import (
        test_migrate_workspace_applies_consumer_rewrites,
        test_migrate_workspace_dry_run_preserves_files,
    )

    test_infra_refactor_namespace_aliases = (
        _tests_unit_refactor_test_infra_refactor_namespace_aliases
    )
    import tests.unit.refactor.test_infra_refactor_namespace_source as _tests_unit_refactor_test_infra_refactor_namespace_source
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
        rope_project,
        test_import_alias_detector_skips_facade_and_subclass_files,
        test_import_alias_detector_skips_nested_private_and_as_renames,
        test_import_alias_detector_skips_private_and_class_imports,
        test_namespace_rewriter_keeps_contextual_alias_subset,
        test_namespace_rewriter_only_rewrites_runtime_alias_imports,
        test_namespace_rewriter_skips_facade_and_subclass_files,
        test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates,
        test_runtime_alias_migrator_merges_local_imports_in_src,
        test_runtime_alias_migrator_merges_local_imports_in_tests,
        test_runtime_alias_migrator_skips_unsafe_local_cycle,
    )

    test_infra_refactor_namespace_source = (
        _tests_unit_refactor_test_infra_refactor_namespace_source
    )
    import tests.unit.refactor.test_infra_refactor_pattern_corrections as _tests_unit_refactor_test_infra_refactor_pattern_corrections
    from tests.unit.refactor.test_infra_refactor_namespace_source import (
        FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP,
        test_detects_only_wrong_alias_in_mixed_import,
        test_detects_same_project_submodule_alias_import,
        test_detects_wrong_source_m_import,
        test_detects_wrong_source_u_import,
        test_project_without_alias_facade_has_no_violation,
        test_rewriter_namespace_source_is_idempotent_with_ruff,
        test_rewriter_preserves_non_alias_symbols,
        test_rewriter_splits_mixed_imports_correctly,
        test_skips_facade_declaration_files,
        test_skips_import_as_rename,
        test_skips_init_file,
        test_skips_non_alias_symbols,
        test_skips_r_alias_universal_exception,
        test_skips_same_project_private_submodule,
        test_skips_same_project_submodule_class_import,
    )

    test_infra_refactor_pattern_corrections = (
        _tests_unit_refactor_test_infra_refactor_pattern_corrections
    )
    import tests.unit.refactor.test_infra_refactor_project_classifier as _tests_unit_refactor_test_infra_refactor_project_classifier
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
        test_pattern_rule_converts_dict_annotations_to_mapping,
        test_pattern_rule_keeps_dict_param_when_copy_used,
        test_pattern_rule_keeps_dict_param_when_subscript_mutated,
        test_pattern_rule_keeps_type_cast_when_not_nested_object_cast,
        test_pattern_rule_optionally_converts_return_annotations_to_mapping,
        test_pattern_rule_removes_configured_redundant_casts,
        test_pattern_rule_removes_nested_type_object_cast_chain,
        test_pattern_rule_skips_overload_signatures,
    )

    test_infra_refactor_project_classifier = (
        _tests_unit_refactor_test_infra_refactor_project_classifier
    )
    import tests.unit.refactor.test_infra_refactor_safety as _tests_unit_refactor_test_infra_refactor_safety
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order,
    )

    test_infra_refactor_safety = _tests_unit_refactor_test_infra_refactor_safety
    import tests.unit.refactor.test_infra_refactor_typing_unifier as _tests_unit_refactor_test_infra_refactor_typing_unifier
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub,
        test_refactor_project_integrates_safety_manager,
    )

    test_infra_refactor_typing_unifier = (
        _tests_unit_refactor_test_infra_refactor_typing_unifier
    )
    import tests.unit.refactor.test_main_cli as _tests_unit_refactor_test_main_cli
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        test_all_three_capabilities_in_one_pass,
        test_converts_multiple_aliases,
        test_converts_typealias_to_pep695,
        test_injects_t_import_when_needed,
        test_no_duplicate_t_import_when_t_from_project_package,
        test_noop_clean_module,
        test_preserves_annotated_in_function_params,
        test_preserves_non_matching_unions,
        test_preserves_override_in_method,
        test_preserves_protocol_and_runtime_checkable,
        test_preserves_type_checking_import,
        test_preserves_typealias_import_when_class_level_usage_exists,
        test_preserves_used_imports_when_import_precedes_usage,
        test_preserves_used_typing_imports,
        test_removes_all_imports_when_none_used_import_first,
        test_removes_all_unused_typing_imports,
        test_removes_dead_typealias_import,
        test_removes_typealias_import_only_when_all_usages_converted,
        test_removes_unused_preserves_used_when_import_precedes_usage,
        test_replaces_container_union,
        test_replaces_numeric_union,
        test_replaces_primitives_union,
        test_replaces_scalar_union,
        test_skips_definition_files,
        test_skips_union_with_none,
        test_typealias_conversion_preserves_used_typing_siblings,
    )

    test_main_cli = _tests_unit_refactor_test_main_cli
    import tests.unit.release as _tests_unit_release
    from tests.unit.refactor.test_main_cli import (
        refactor_main,
        test_refactor_census_rejects_apply_before_subcommand,
        test_refactor_centralize_accepts_apply_before_subcommand,
        test_refactor_runtime_alias_imports_accepts_aliases_and_project,
    )

    release = _tests_unit_release
    import tests.unit.release.flow_tests as _tests_unit_release_flow_tests
    from tests.unit.release._stubs import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
    )

    flow_tests = _tests_unit_release_flow_tests
    import tests.unit.release.orchestrator_git_tests as _tests_unit_release_orchestrator_git_tests
    from tests.unit.release.flow_tests import TestReleaseMainFlow
    from tests.unit.release.main_tests import TestReleaseMainParsing

    orchestrator_git_tests = _tests_unit_release_orchestrator_git_tests
    import tests.unit.release.orchestrator_helpers_tests as _tests_unit_release_orchestrator_helpers_tests
    from tests.unit.release.orchestrator_git_tests import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )

    orchestrator_helpers_tests = _tests_unit_release_orchestrator_helpers_tests
    import tests.unit.release.orchestrator_phases_tests as _tests_unit_release_orchestrator_phases_tests
    from tests.unit.release.orchestrator_helpers_tests import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )

    orchestrator_phases_tests = _tests_unit_release_orchestrator_phases_tests
    import tests.unit.release.orchestrator_publish_tests as _tests_unit_release_orchestrator_publish_tests
    from tests.unit.release.orchestrator_phases_tests import (
        TestPhaseBuild,
        TestPhaseValidate,
        TestPhaseVersion,
    )

    orchestrator_publish_tests = _tests_unit_release_orchestrator_publish_tests
    import tests.unit.release.orchestrator_tests as _tests_unit_release_orchestrator_tests
    from tests.unit.release.orchestrator_publish_tests import TestPhasePublish

    orchestrator_tests = _tests_unit_release_orchestrator_tests
    import tests.unit.release.release_init_tests as _tests_unit_release_release_init_tests
    from tests.unit.release.orchestrator_tests import (
        TestReleaseOrchestratorExecute,
        workspace_root,
    )

    release_init_tests = _tests_unit_release_release_init_tests
    import tests.unit.release.version_resolution_tests as _tests_unit_release_version_resolution_tests
    from tests.unit.release.release_init_tests import TestReleaseInit

    version_resolution_tests = _tests_unit_release_version_resolution_tests
    import tests.unit.test_infra_constants_core as _tests_unit_test_infra_constants_core
    from tests.unit.release.version_resolution_tests import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
    )

    test_infra_constants_core = _tests_unit_test_infra_constants_core
    import tests.unit.test_infra_constants_extra as _tests_unit_test_infra_constants_extra
    from tests.unit.test_infra_constants_core import (
        TestFlextInfraConstantsExcludedNamespace,
        TestFlextInfraConstantsFilesNamespace,
        TestFlextInfraConstantsGatesNamespace,
        TestFlextInfraConstantsPathsNamespace,
        TestFlextInfraConstantsStatusNamespace,
    )

    test_infra_constants_extra = _tests_unit_test_infra_constants_extra
    import tests.unit.test_infra_git as _tests_unit_test_infra_git
    from tests.unit.test_infra_constants_extra import (
        TestFlextInfraConstantsAlias,
        TestFlextInfraConstantsCheckNamespace,
        TestFlextInfraConstantsConsistency,
        TestFlextInfraConstantsEncodingNamespace,
        TestFlextInfraConstantsGithubNamespace,
        TestFlextInfraConstantsImmutability,
    )

    test_infra_git = _tests_unit_test_infra_git
    import tests.unit.test_infra_init_lazy_core as _tests_unit_test_infra_init_lazy_core
    from tests.unit.test_infra_git import (
        TestFlextInfraGitService,
        TestGitPush,
        TestGitTagOperations,
        TestRemovedCompatibilityMethods,
        git_repo,
    )

    test_infra_init_lazy_core = _tests_unit_test_infra_init_lazy_core
    import tests.unit.test_infra_init_lazy_submodules as _tests_unit_test_infra_init_lazy_submodules
    from tests.unit.test_infra_init_lazy_core import TestFlextInfraInitLazyLoading

    test_infra_init_lazy_submodules = _tests_unit_test_infra_init_lazy_submodules
    import tests.unit.test_infra_main as _tests_unit_test_infra_main
    from tests.unit.test_infra_init_lazy_submodules import (
        TestFlextInfraSubmoduleInitLazyLoading,
    )

    test_infra_main = _tests_unit_test_infra_main
    import tests.unit.test_infra_maintenance_cli as _tests_unit_test_infra_maintenance_cli
    from tests.unit.test_infra_main import (
        test_main_all_groups_defined,
        test_main_group_descriptions_are_present,
        test_main_help_flag_returns_zero,
        test_main_returns_error_when_no_args,
        test_main_unknown_group_returns_error,
    )

    test_infra_maintenance_cli = _tests_unit_test_infra_maintenance_cli
    import tests.unit.test_infra_maintenance_init as _tests_unit_test_infra_maintenance_init
    from tests.unit.test_infra_maintenance_cli import (
        test_maintenance_rejects_apply_flag,
    )

    test_infra_maintenance_init = _tests_unit_test_infra_maintenance_init
    import tests.unit.test_infra_maintenance_main as _tests_unit_test_infra_maintenance_main
    from tests.unit.test_infra_maintenance_init import TestFlextInfraMaintenance

    test_infra_maintenance_main = _tests_unit_test_infra_maintenance_main
    import tests.unit.test_infra_maintenance_python_version as _tests_unit_test_infra_maintenance_python_version
    from tests.unit.test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess,
        main,
    )

    test_infra_maintenance_python_version = (
        _tests_unit_test_infra_maintenance_python_version
    )
    import tests.unit.test_infra_paths as _tests_unit_test_infra_paths
    from tests.unit.test_infra_maintenance_python_version import (
        TestDiscoverProjects,
        TestEnforcerExecute,
        TestEnsurePythonVersionFile,
        TestReadRequiredMinor,
        TestWorkspaceRoot,
    )

    test_infra_paths = _tests_unit_test_infra_paths
    import tests.unit.test_infra_patterns_core as _tests_unit_test_infra_patterns_core
    from tests.unit.test_infra_paths import TestFlextInfraPathResolver

    test_infra_patterns_core = _tests_unit_test_infra_patterns_core
    import tests.unit.test_infra_patterns_extra as _tests_unit_test_infra_patterns_extra
    from tests.unit.test_infra_patterns_core import (
        TestFlextInfraPatternsMarkdown,
        TestFlextInfraPatternsTooling,
    )

    test_infra_patterns_extra = _tests_unit_test_infra_patterns_extra
    import tests.unit.test_infra_protocols as _tests_unit_test_infra_protocols
    from tests.unit.test_infra_patterns_extra import (
        TestFlextInfraPatternsEdgeCases,
        TestFlextInfraPatternsPatternTypes,
    )

    test_infra_protocols = _tests_unit_test_infra_protocols
    import tests.unit.test_infra_reporting_core as _tests_unit_test_infra_reporting_core
    from tests.unit.test_infra_protocols import TestFlextInfraProtocolsImport

    test_infra_reporting_core = _tests_unit_test_infra_reporting_core
    import tests.unit.test_infra_reporting_extra as _tests_unit_test_infra_reporting_extra
    from tests.unit.test_infra_reporting_core import TestFlextInfraReportingServiceCore

    test_infra_reporting_extra = _tests_unit_test_infra_reporting_extra
    import tests.unit.test_infra_selection as _tests_unit_test_infra_selection
    from tests.unit.test_infra_reporting_extra import (
        TestFlextInfraReportingServiceExtra,
    )

    test_infra_selection = _tests_unit_test_infra_selection
    import tests.unit.test_infra_subprocess_core as _tests_unit_test_infra_subprocess_core
    from tests.unit.test_infra_selection import TestFlextInfraUtilitiesSelection

    test_infra_subprocess_core = _tests_unit_test_infra_subprocess_core
    import tests.unit.test_infra_subprocess_extra as _tests_unit_test_infra_subprocess_extra
    from tests.unit.test_infra_subprocess_core import (
        runner,
        test_capture_cases,
        test_run_cases,
        test_run_raw_cases,
    )

    test_infra_subprocess_extra = _tests_unit_test_infra_subprocess_extra
    import tests.unit.test_infra_toml_io as _tests_unit_test_infra_toml_io
    from tests.unit.test_infra_subprocess_extra import TestFlextInfraCommandRunnerExtra

    test_infra_toml_io = _tests_unit_test_infra_toml_io
    import tests.unit.test_infra_typings as _tests_unit_test_infra_typings
    from tests.unit.test_infra_toml_io import (
        TestFlextInfraTomlDocument,
        TestFlextInfraTomlHelpers,
        TestFlextInfraTomlRead,
    )

    test_infra_typings = _tests_unit_test_infra_typings
    import tests.unit.test_infra_utilities as _tests_unit_test_infra_utilities
    from tests.unit.test_infra_typings import TestFlextInfraTypesImport

    test_infra_utilities = _tests_unit_test_infra_utilities
    import tests.unit.test_infra_version_core as _tests_unit_test_infra_version_core
    from tests.unit.test_infra_utilities import TestFlextInfraUtilitiesImport

    test_infra_version_core = _tests_unit_test_infra_version_core
    import tests.unit.test_infra_version_extra as _tests_unit_test_infra_version_extra
    from tests.unit.test_infra_version_core import TestFlextInfraVersionClass

    test_infra_version_extra = _tests_unit_test_infra_version_extra
    import tests.unit.test_infra_versioning as _tests_unit_test_infra_versioning
    from tests.unit.test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo,
    )

    test_infra_versioning = _tests_unit_test_infra_versioning
    import tests.unit.test_infra_workspace_cli as _tests_unit_test_infra_workspace_cli
    from tests.unit.test_infra_versioning import (
        service,
        test_bump_version_invalid,
        test_bump_version_result_type,
        test_bump_version_valid,
        test_current_workspace_version,
        test_parse_semver_invalid,
        test_parse_semver_result_type,
        test_parse_semver_valid,
        test_replace_project_version,
    )

    test_infra_workspace_cli = _tests_unit_test_infra_workspace_cli
    import tests.unit.test_infra_workspace_detector as _tests_unit_test_infra_workspace_detector
    from tests.unit.test_infra_workspace_cli import (
        test_workspace_cli_migrate_command,
        test_workspace_cli_migrate_output_contains_summary,
        test_workspace_cli_rejects_migrate_flags_for_detect,
    )

    test_infra_workspace_detector = _tests_unit_test_infra_workspace_detector
    import tests.unit.test_infra_workspace_init as _tests_unit_test_infra_workspace_init
    from tests.unit.test_infra_workspace_detector import (
        TestDetectorBasicDetection,
        TestDetectorGitRunScenarios,
        TestDetectorRepoNameExtraction,
        detector,
    )

    test_infra_workspace_init = _tests_unit_test_infra_workspace_init
    import tests.unit.test_infra_workspace_main as _tests_unit_test_infra_workspace_main
    from tests.unit.test_infra_workspace_init import TestFlextInfraWorkspace

    test_infra_workspace_main = _tests_unit_test_infra_workspace_main
    import tests.unit.test_infra_workspace_migrator as _tests_unit_test_infra_workspace_migrator
    from tests.unit.test_infra_workspace_main import (
        TestMainCli,
        TestRunDetect,
        TestRunMigrate,
        TestRunOrchestrate,
        TestRunSync,
        workspace_main,
    )

    test_infra_workspace_migrator = _tests_unit_test_infra_workspace_migrator
    import tests.unit.test_infra_workspace_migrator_deps as _tests_unit_test_infra_workspace_migrator_deps
    from tests.unit.test_infra_workspace_migrator import (
        test_migrator_apply_updates_project_files,
        test_migrator_discovery_failure,
        test_migrator_dry_run_reports_changes_without_writes,
        test_migrator_execute_returns_failure,
        test_migrator_handles_missing_pyproject_gracefully,
        test_migrator_no_changes_needed,
        test_migrator_preserves_custom_makefile_content,
        test_migrator_workspace_root_not_exists,
        test_migrator_workspace_root_project_detection,
    )

    test_infra_workspace_migrator_deps = _tests_unit_test_infra_workspace_migrator_deps
    import tests.unit.test_infra_workspace_migrator_dryrun as _tests_unit_test_infra_workspace_migrator_dryrun
    from tests.unit.test_infra_workspace_migrator_deps import (
        test_migrate_makefile_not_found_non_dry_run,
        test_migrate_pyproject_flext_core_non_dry_run,
        test_migrator_has_flext_core_dependency_in_poetry,
        test_migrator_has_flext_core_dependency_poetry_deps_not_table,
        test_migrator_has_flext_core_dependency_poetry_table_missing,
        test_workspace_migrator_error_handling_on_invalid_workspace,
        test_workspace_migrator_makefile_not_found_dry_run,
        test_workspace_migrator_makefile_read_error,
        test_workspace_migrator_pyproject_write_error,
    )

    test_infra_workspace_migrator_dryrun = (
        _tests_unit_test_infra_workspace_migrator_dryrun
    )
    import tests.unit.test_infra_workspace_migrator_errors as _tests_unit_test_infra_workspace_migrator_errors
    from tests.unit.test_infra_workspace_migrator_dryrun import (
        test_migrator_flext_core_dry_run,
        test_migrator_flext_core_project_skipped,
        test_migrator_gitignore_already_normalized_dry_run,
        test_migrator_makefile_not_found_dry_run,
        test_migrator_makefile_read_failure,
        test_migrator_pyproject_not_found_dry_run,
    )

    test_infra_workspace_migrator_errors = (
        _tests_unit_test_infra_workspace_migrator_errors
    )
    import tests.unit.test_infra_workspace_migrator_internal as _tests_unit_test_infra_workspace_migrator_internal
    from tests.unit.test_infra_workspace_migrator_errors import (
        TestMigratorReadFailures,
        TestMigratorWriteFailures,
    )

    test_infra_workspace_migrator_internal = (
        _tests_unit_test_infra_workspace_migrator_internal
    )
    import tests.unit.test_infra_workspace_migrator_pyproject as _tests_unit_test_infra_workspace_migrator_pyproject
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestMigratorEdgeCases,
        TestMigratorInternalMakefile,
        TestMigratorInternalPyproject,
    )

    test_infra_workspace_migrator_pyproject = (
        _tests_unit_test_infra_workspace_migrator_pyproject
    )
    import tests.unit.test_infra_workspace_orchestrator as _tests_unit_test_infra_workspace_orchestrator
    from tests.unit.test_infra_workspace_migrator_pyproject import (
        TestMigratorDryRun,
        TestMigratorFlextCore,
        TestMigratorPoetryDeps,
    )

    test_infra_workspace_orchestrator = _tests_unit_test_infra_workspace_orchestrator
    import tests.unit.test_infra_workspace_sync as _tests_unit_test_infra_workspace_sync
    from tests.unit.test_infra_workspace_orchestrator import (
        TestOrchestratorBasic,
        TestOrchestratorFailures,
        TestOrchestratorGateNormalization,
        orchestrator,
    )

    test_infra_workspace_sync = _tests_unit_test_infra_workspace_sync
    import tests.unit.validate as _tests_unit_validate
    from tests.unit.test_infra_workspace_sync import (
        SetupFn,
        svc,
        test_atomic_write_fail,
        test_atomic_write_ok,
        test_cli_forwards_canonical_root,
        test_cli_result_by_project_root,
        test_gitignore_entry_scenarios,
        test_gitignore_sync_failure,
        test_gitignore_write_failure,
        test_sync_basemk_scenarios,
        test_sync_error_scenarios,
        test_sync_regenerates_project_makefile_without_legacy_passthrough,
        test_sync_root_validation,
        test_sync_success_scenarios,
        test_sync_updates_project_makefile_for_standalone_project,
        test_sync_updates_workspace_makefile_for_workspace_root,
        test_workspace_makefile_generator_declares_canonical_workspace_variables,
        test_workspace_makefile_generator_reuses_mod_and_boot_feedback,
        test_workspace_makefile_generator_sanitizes_orchestrator_env,
    )

    validate = _tests_unit_validate
    import tests.unit.validate.basemk_validator_tests as _tests_unit_validate_basemk_validator_tests

    basemk_validator_tests = _tests_unit_validate_basemk_validator_tests
    import tests.unit.validate.inventory_tests as _tests_unit_validate_inventory_tests
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from tests.unit.validate.init_tests import TestCoreModuleInit

    inventory_tests = _tests_unit_validate_inventory_tests
    import tests.unit.validate.pytest_diag as _tests_unit_validate_pytest_diag
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from tests.unit.validate.main_cli_tests import (
        test_stub_validate_help_returns_zero,
        test_stub_validate_uses_all_flag,
    )
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )

    pytest_diag = _tests_unit_validate_pytest_diag
    import tests.unit.validate.scanner_tests as _tests_unit_validate_scanner_tests
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )

    scanner_tests = _tests_unit_validate_scanner_tests
    import tests.unit.validate.skill_validator_tests as _tests_unit_validate_skill_validator_tests
    from tests.unit.validate.scanner_tests import (
        TestScannerCore,
        TestScannerHelpers,
        TestScannerMultiFile,
    )

    skill_validator_tests = _tests_unit_validate_skill_validator_tests
    import tests.unit.validate.stub_chain_tests as _tests_unit_validate_stub_chain_tests
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )

    stub_chain_tests = _tests_unit_validate_stub_chain_tests
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "tests.unit._utilities",
        "tests.unit.basemk",
        "tests.unit.check",
        "tests.unit.codegen",
        "tests.unit.container",
        "tests.unit.deps",
        "tests.unit.discovery",
        "tests.unit.docs",
        "tests.unit.github",
        "tests.unit.io",
        "tests.unit.refactor",
        "tests.unit.release",
        "tests.unit.validate",
    ),
    {
        "SetupFn": "tests.unit.test_infra_workspace_sync",
        "TestDetectorBasicDetection": "tests.unit.test_infra_workspace_detector",
        "TestDetectorGitRunScenarios": "tests.unit.test_infra_workspace_detector",
        "TestDetectorRepoNameExtraction": "tests.unit.test_infra_workspace_detector",
        "TestDiscoverProjects": "tests.unit.test_infra_maintenance_python_version",
        "TestEnforcerExecute": "tests.unit.test_infra_maintenance_python_version",
        "TestEnsurePythonVersionFile": "tests.unit.test_infra_maintenance_python_version",
        "TestFlextInfraCommandRunnerExtra": "tests.unit.test_infra_subprocess_extra",
        "TestFlextInfraConstantsAlias": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsCheckNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsConsistency": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsEncodingNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsExcludedNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsFilesNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGatesNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGithubNamespace": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsImmutability": "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsPathsNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsStatusNamespace": "tests.unit.test_infra_constants_core",
        "TestFlextInfraGitService": "tests.unit.test_infra_git",
        "TestFlextInfraInitLazyLoading": "tests.unit.test_infra_init_lazy_core",
        "TestFlextInfraMaintenance": "tests.unit.test_infra_maintenance_init",
        "TestFlextInfraPathResolver": "tests.unit.test_infra_paths",
        "TestFlextInfraPatternsEdgeCases": "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsMarkdown": "tests.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsPatternTypes": "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsTooling": "tests.unit.test_infra_patterns_core",
        "TestFlextInfraProtocolsImport": "tests.unit.test_infra_protocols",
        "TestFlextInfraReportingServiceCore": "tests.unit.test_infra_reporting_core",
        "TestFlextInfraReportingServiceExtra": "tests.unit.test_infra_reporting_extra",
        "TestFlextInfraSubmoduleInitLazyLoading": "tests.unit.test_infra_init_lazy_submodules",
        "TestFlextInfraTomlDocument": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlHelpers": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlRead": "tests.unit.test_infra_toml_io",
        "TestFlextInfraTypesImport": "tests.unit.test_infra_typings",
        "TestFlextInfraUtilitiesImport": "tests.unit.test_infra_utilities",
        "TestFlextInfraUtilitiesSelection": "tests.unit.test_infra_selection",
        "TestFlextInfraVersionClass": "tests.unit.test_infra_version_core",
        "TestFlextInfraVersionModuleLevel": "tests.unit.test_infra_version_extra",
        "TestFlextInfraVersionPackageInfo": "tests.unit.test_infra_version_extra",
        "TestFlextInfraWorkspace": "tests.unit.test_infra_workspace_init",
        "TestGitPush": "tests.unit.test_infra_git",
        "TestGitTagOperations": "tests.unit.test_infra_git",
        "TestMainCli": "tests.unit.test_infra_workspace_main",
        "TestMaintenanceMainEnforcer": "tests.unit.test_infra_maintenance_main",
        "TestMaintenanceMainSuccess": "tests.unit.test_infra_maintenance_main",
        "TestMigratorDryRun": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorEdgeCases": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorFlextCore": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorInternalMakefile": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalPyproject": "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorPoetryDeps": "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorReadFailures": "tests.unit.test_infra_workspace_migrator_errors",
        "TestMigratorWriteFailures": "tests.unit.test_infra_workspace_migrator_errors",
        "TestOrchestratorBasic": "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorFailures": "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorGateNormalization": "tests.unit.test_infra_workspace_orchestrator",
        "TestReadRequiredMinor": "tests.unit.test_infra_maintenance_python_version",
        "TestRemovedCompatibilityMethods": "tests.unit.test_infra_git",
        "TestRunDetect": "tests.unit.test_infra_workspace_main",
        "TestRunMigrate": "tests.unit.test_infra_workspace_main",
        "TestRunOrchestrate": "tests.unit.test_infra_workspace_main",
        "TestRunSync": "tests.unit.test_infra_workspace_main",
        "TestWorkspaceRoot": "tests.unit.test_infra_maintenance_python_version",
        "_utilities": "tests.unit._utilities",
        "basemk": "tests.unit.basemk",
        "c": ("flext_core.constants", "FlextConstants"),
        "check": "tests.unit.check",
        "codegen": "tests.unit.codegen",
        "container": "tests.unit.container",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "deps": "tests.unit.deps",
        "detector": "tests.unit.test_infra_workspace_detector",
        "discovery": "tests.unit.discovery",
        "docs": "tests.unit.docs",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "git_repo": "tests.unit.test_infra_git",
        "github": "tests.unit.github",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "io": "tests.unit.io",
        "m": ("flext_core.models", "FlextModels"),
        "main": "tests.unit.test_infra_maintenance_main",
        "orchestrator": "tests.unit.test_infra_workspace_orchestrator",
        "p": ("flext_core.protocols", "FlextProtocols"),
        "r": ("flext_core.result", "FlextResult"),
        "refactor": "tests.unit.refactor",
        "release": "tests.unit.release",
        "runner": "tests.unit.test_infra_subprocess_core",
        "s": ("flext_core.service", "FlextService"),
        "service": "tests.unit.test_infra_versioning",
        "svc": "tests.unit.test_infra_workspace_sync",
        "t": ("flext_core.typings", "FlextTypes"),
        "test_atomic_write_fail": "tests.unit.test_infra_workspace_sync",
        "test_atomic_write_ok": "tests.unit.test_infra_workspace_sync",
        "test_bump_version_invalid": "tests.unit.test_infra_versioning",
        "test_bump_version_result_type": "tests.unit.test_infra_versioning",
        "test_bump_version_valid": "tests.unit.test_infra_versioning",
        "test_capture_cases": "tests.unit.test_infra_subprocess_core",
        "test_cli_forwards_canonical_root": "tests.unit.test_infra_workspace_sync",
        "test_cli_result_by_project_root": "tests.unit.test_infra_workspace_sync",
        "test_current_workspace_version": "tests.unit.test_infra_versioning",
        "test_gitignore_entry_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_gitignore_sync_failure": "tests.unit.test_infra_workspace_sync",
        "test_gitignore_write_failure": "tests.unit.test_infra_workspace_sync",
        "test_infra_constants_core": "tests.unit.test_infra_constants_core",
        "test_infra_constants_extra": "tests.unit.test_infra_constants_extra",
        "test_infra_git": "tests.unit.test_infra_git",
        "test_infra_init_lazy_core": "tests.unit.test_infra_init_lazy_core",
        "test_infra_init_lazy_submodules": "tests.unit.test_infra_init_lazy_submodules",
        "test_infra_main": "tests.unit.test_infra_main",
        "test_infra_maintenance_cli": "tests.unit.test_infra_maintenance_cli",
        "test_infra_maintenance_init": "tests.unit.test_infra_maintenance_init",
        "test_infra_maintenance_main": "tests.unit.test_infra_maintenance_main",
        "test_infra_maintenance_python_version": "tests.unit.test_infra_maintenance_python_version",
        "test_infra_paths": "tests.unit.test_infra_paths",
        "test_infra_patterns_core": "tests.unit.test_infra_patterns_core",
        "test_infra_patterns_extra": "tests.unit.test_infra_patterns_extra",
        "test_infra_protocols": "tests.unit.test_infra_protocols",
        "test_infra_reporting_core": "tests.unit.test_infra_reporting_core",
        "test_infra_reporting_extra": "tests.unit.test_infra_reporting_extra",
        "test_infra_selection": "tests.unit.test_infra_selection",
        "test_infra_subprocess_core": "tests.unit.test_infra_subprocess_core",
        "test_infra_subprocess_extra": "tests.unit.test_infra_subprocess_extra",
        "test_infra_toml_io": "tests.unit.test_infra_toml_io",
        "test_infra_typings": "tests.unit.test_infra_typings",
        "test_infra_utilities": "tests.unit.test_infra_utilities",
        "test_infra_version_core": "tests.unit.test_infra_version_core",
        "test_infra_version_extra": "tests.unit.test_infra_version_extra",
        "test_infra_versioning": "tests.unit.test_infra_versioning",
        "test_infra_workspace_cli": "tests.unit.test_infra_workspace_cli",
        "test_infra_workspace_detector": "tests.unit.test_infra_workspace_detector",
        "test_infra_workspace_init": "tests.unit.test_infra_workspace_init",
        "test_infra_workspace_main": "tests.unit.test_infra_workspace_main",
        "test_infra_workspace_migrator": "tests.unit.test_infra_workspace_migrator",
        "test_infra_workspace_migrator_deps": "tests.unit.test_infra_workspace_migrator_deps",
        "test_infra_workspace_migrator_dryrun": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_infra_workspace_migrator_errors": "tests.unit.test_infra_workspace_migrator_errors",
        "test_infra_workspace_migrator_internal": "tests.unit.test_infra_workspace_migrator_internal",
        "test_infra_workspace_migrator_pyproject": "tests.unit.test_infra_workspace_migrator_pyproject",
        "test_infra_workspace_orchestrator": "tests.unit.test_infra_workspace_orchestrator",
        "test_infra_workspace_sync": "tests.unit.test_infra_workspace_sync",
        "test_main_all_groups_defined": "tests.unit.test_infra_main",
        "test_main_group_descriptions_are_present": "tests.unit.test_infra_main",
        "test_main_help_flag_returns_zero": "tests.unit.test_infra_main",
        "test_main_returns_error_when_no_args": "tests.unit.test_infra_main",
        "test_main_unknown_group_returns_error": "tests.unit.test_infra_main",
        "test_maintenance_rejects_apply_flag": "tests.unit.test_infra_maintenance_cli",
        "test_migrate_makefile_not_found_non_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_pyproject_flext_core_non_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_apply_updates_project_files": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_discovery_failure": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_dry_run_reports_changes_without_writes": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_execute_returns_failure": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_flext_core_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_project_skipped": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_gitignore_already_normalized_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_handles_missing_pyproject_gracefully": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_has_flext_core_dependency_in_poetry": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_deps_not_table": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_table_missing": "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_makefile_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_read_failure": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_no_changes_needed": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_preserves_custom_makefile_content": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_pyproject_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_workspace_root_not_exists": "tests.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_project_detection": "tests.unit.test_infra_workspace_migrator",
        "test_parse_semver_invalid": "tests.unit.test_infra_versioning",
        "test_parse_semver_result_type": "tests.unit.test_infra_versioning",
        "test_parse_semver_valid": "tests.unit.test_infra_versioning",
        "test_replace_project_version": "tests.unit.test_infra_versioning",
        "test_run_cases": "tests.unit.test_infra_subprocess_core",
        "test_run_raw_cases": "tests.unit.test_infra_subprocess_core",
        "test_sync_basemk_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_error_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_regenerates_project_makefile_without_legacy_passthrough": "tests.unit.test_infra_workspace_sync",
        "test_sync_root_validation": "tests.unit.test_infra_workspace_sync",
        "test_sync_success_scenarios": "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_project_makefile_for_standalone_project": "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_workspace_makefile_for_workspace_root": "tests.unit.test_infra_workspace_sync",
        "test_workspace_cli_migrate_command": "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_output_contains_summary": "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_rejects_migrate_flags_for_detect": "tests.unit.test_infra_workspace_cli",
        "test_workspace_makefile_generator_declares_canonical_workspace_variables": "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_reuses_mod_and_boot_feedback": "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_sanitizes_orchestrator_env": "tests.unit.test_infra_workspace_sync",
        "test_workspace_migrator_error_handling_on_invalid_workspace": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_not_found_dry_run": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_read_error": "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_pyproject_write_error": "tests.unit.test_infra_workspace_migrator_deps",
        "u": ("flext_core.utilities", "FlextUtilities"),
        "validate": "tests.unit.validate",
        "workspace_main": "tests.unit.test_infra_workspace_main",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)

__all__ = [
    "ANSI_RE",
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "CheckProjectStub",
    "EngineSafetyStub",
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "FlextInfraCodegenTestProjectFactory",
    "GateClass",
    "RunCallable",
    "RunProjectsMock",
    "SampleModel",
    "SetupFn",
    "Spy",
    "StubCommandOutput",
    "StubJsonIo",
    "StubLinter",
    "StubPrManager",
    "StubProjectInfo",
    "StubReporting",
    "StubRunner",
    "StubSelector",
    "StubSyncer",
    "StubTemplates",
    "StubUtilities",
    "StubVersioning",
    "StubWorkspaceManager",
    "TestAdrHelpers",
    "TestAllDirectoriesScanned",
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorMainCli",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorScopeFailure",
    "TestAuditorToMarkdown",
    "TestBaseMkValidatorCore",
    "TestBaseMkValidatorEdgeCases",
    "TestBaseMkValidatorSha256",
    "TestBuildProjectReport",
    "TestBuildScopes",
    "TestBuildSiblingExportIndex",
    "TestBuildTargets",
    "TestBuilderCore",
    "TestBuilderScope",
    "TestBumpNextDev",
    "TestCensusReportModel",
    "TestCensusViolationModel",
    "TestCheckIssueFormatted",
    "TestCheckMainEntryPoint",
    "TestCheckOnlyMode",
    "TestCheckProjectRunners",
    "TestClassifyIssues",
    "TestCollectChanges",
    "TestCollectInternalDeps",
    "TestCollectInternalDepsEdgeCases",
    "TestCollectMarkdownFiles",
    "TestConfigFixerEnsureProjectExcludes",
    "TestConfigFixerExecute",
    "TestConfigFixerFindPyprojectFiles",
    "TestConfigFixerFixSearchPaths",
    "TestConfigFixerPathResolution",
    "TestConfigFixerProcessFile",
    "TestConfigFixerRemoveIgnoreSubConfig",
    "TestConfigFixerRun",
    "TestConfigFixerRunMethods",
    "TestConfigFixerRunWithVerbose",
    "TestConfigFixerToArray",
    "TestConsolidateGroupsPhase",
    "TestConstants",
    "TestConstantsQualityGateCLIDispatch",
    "TestConstantsQualityGateVerdict",
    "TestCoreModuleInit",
    "TestCreateBranches",
    "TestCreateTag",
    "TestDetectMode",
    "TestDetectionUncoveredLines",
    "TestDetectorBasicDetection",
    "TestDetectorGitRunScenarios",
    "TestDetectorRepoNameExtraction",
    "TestDetectorReportFlags",
    "TestDetectorRunFailures",
    "TestDiscoverProjects",
    "TestDiscoveryDiscoverProjects",
    "TestDiscoveryFindAllPyprojectFiles",
    "TestDiscoveryIterPythonFiles",
    "TestDiscoveryProjectRoots",
    "TestDispatchPhase",
    "TestEdgeCases",
    "TestEnforcerExecute",
    "TestEnsureCheckout",
    "TestEnsureCheckoutEdgeCases",
    "TestEnsureCoverageConfigPhase",
    "TestEnsurePyreflyConfigPhase",
    "TestEnsurePyrightConfigPhase",
    "TestEnsurePytestConfigPhase",
    "TestEnsurePythonVersionFile",
    "TestEnsureSymlink",
    "TestEnsureSymlinkEdgeCases",
    "TestErrorReporting",
    "TestExcludedDirectories",
    "TestExcludedProjects",
    "TestExtractExports",
    "TestExtractVersionExports",
    "TestFixPyrelfyCLI",
    "TestFixabilityClassification",
    "TestFixerCore",
    "TestFixerMaybeFixLink",
    "TestFixerProcessFile",
    "TestFixerScope",
    "TestFixerToc",
    "TestFlextInfraBaseMk",
    "TestFlextInfraCheck",
    "TestFlextInfraCodegenLazyInit",
    "TestFlextInfraCommandRunnerExtra",
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
    "TestFlextInfraDependencyDetectionModels",
    "TestFlextInfraDependencyDetectionService",
    "TestFlextInfraDependencyDetectorModels",
    "TestFlextInfraDependencyPathSync",
    "TestFlextInfraDeps",
    "TestFlextInfraDiscoveryService",
    "TestFlextInfraDiscoveryServiceUncoveredLines",
    "TestFlextInfraDocScope",
    "TestFlextInfraDocs",
    "TestFlextInfraExtraPathsManager",
    "TestFlextInfraGitService",
    "TestFlextInfraInitLazyLoading",
    "TestFlextInfraInternalDependencySyncService",
    "TestFlextInfraJsonService",
    "TestFlextInfraMaintenance",
    "TestFlextInfraPathResolver",
    "TestFlextInfraPatternsEdgeCases",
    "TestFlextInfraPatternsMarkdown",
    "TestFlextInfraPatternsPatternTypes",
    "TestFlextInfraPatternsTooling",
    "TestFlextInfraProtocolsImport",
    "TestFlextInfraPyprojectModernizer",
    "TestFlextInfraReportingServiceCore",
    "TestFlextInfraReportingServiceExtra",
    "TestFlextInfraRuntimeDevDependencyDetectorInit",
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    "TestFlextInfraSubmoduleInitLazyLoading",
    "TestFlextInfraTomlDocument",
    "TestFlextInfraTomlHelpers",
    "TestFlextInfraTomlRead",
    "TestFlextInfraTypesImport",
    "TestFlextInfraUtilitiesImport",
    "TestFlextInfraUtilitiesSelection",
    "TestFlextInfraVersionClass",
    "TestFlextInfraVersionModuleLevel",
    "TestFlextInfraVersionPackageInfo",
    "TestFlextInfraWorkspace",
    "TestFlextInfraWorkspaceChecker",
    "TestFormattingRunRuffFix",
    "TestGenerateFile",
    "TestGenerateNotes",
    "TestGenerateTypeChecking",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestGeneratorCore",
    "TestGeneratorHelpers",
    "TestGeneratorScope",
    "TestGetDepPaths",
    "TestGitPush",
    "TestGitTagOperations",
    "TestGoFmtEmptyLinesInOutput",
    "TestHandleLazyInit",
    "TestInferOwnerFromOrigin",
    "TestInferPackage",
    "TestInfraContainerFunctions",
    "TestInfraMroPattern",
    "TestInfraOutputEdgeCases",
    "TestInfraOutputHeader",
    "TestInfraOutputMessages",
    "TestInfraOutputNoColor",
    "TestInfraOutputProgress",
    "TestInfraOutputStatus",
    "TestInfraOutputSummary",
    "TestInfraServiceRetrieval",
    "TestInjectCommentsPhase",
    "TestInventoryServiceCore",
    "TestInventoryServiceReports",
    "TestInventoryServiceScripts",
    "TestIsInternalPathDep",
    "TestIsRelativeTo",
    "TestIsWorkspaceMode",
    "TestIterMarkdownFiles",
    "TestIterWorkspacePythonModules",
    "TestJsonWriteFailure",
    "TestLintAndFormatPublicMethods",
    "TestLoadAuditBudgets",
    "TestLoadDependencyLimits",
    "TestMain",
    "TestMainBaseMkValidate",
    "TestMainCli",
    "TestMainCliRouting",
    "TestMainCommandDispatch",
    "TestMainDelegation",
    "TestMainEdgeCases",
    "TestMainEntryPoint",
    "TestMainExceptionHandling",
    "TestMainFunction",
    "TestMainHelpAndErrors",
    "TestMainInventory",
    "TestMainModuleImport",
    "TestMainReturnValues",
    "TestMainRouting",
    "TestMainScan",
    "TestMainSubcommandDispatch",
    "TestMainSysArgvModification",
    "TestMainWithFlags",
    "TestMaintenanceMainEnforcer",
    "TestMaintenanceMainSuccess",
    "TestMarkdownReportEmptyGates",
    "TestMaybeWriteTodo",
    "TestMergeChildExports",
    "TestMigratorDryRun",
    "TestMigratorEdgeCases",
    "TestMigratorFlextCore",
    "TestMigratorInternalMakefile",
    "TestMigratorInternalPyproject",
    "TestMigratorPoetryDeps",
    "TestMigratorReadFailures",
    "TestMigratorWriteFailures",
    "TestModernizerEdgeCases",
    "TestModernizerRunAndMain",
    "TestModernizerUncoveredLines",
    "TestModuleAndTypingsFlow",
    "TestMroFacadeMethods",
    "TestMypyEmptyLinesInOutput",
    "TestOrchestratorBasic",
    "TestOrchestratorFailures",
    "TestOrchestratorGateNormalization",
    "TestOwnerFromRemoteUrl",
    "TestParseGitmodules",
    "TestParseRepoMap",
    "TestParseViolationInvalid",
    "TestParseViolationValid",
    "TestParser",
    "TestPathDepPathsPep621",
    "TestPathDepPathsPoetry",
    "TestPathSyncEdgeCases",
    "TestPhaseBuild",
    "TestPhasePublish",
    "TestPhaseValidate",
    "TestPhaseVersion",
    "TestPreviousTag",
    "TestProcessDirectory",
    "TestProcessFileReadError",
    "TestProjectResultProperties",
    "TestPushRelease",
    "TestPytestDiagExtractorCore",
    "TestPytestDiagLogParsing",
    "TestPytestDiagParseXml",
    "TestReadDoc",
    "TestReadExistingDocstring",
    "TestReadRequiredMinor",
    "TestReleaseInit",
    "TestReleaseMainFlow",
    "TestReleaseMainParsing",
    "TestReleaseMainTagResolution",
    "TestReleaseMainVersionResolution",
    "TestReleaseOrchestratorExecute",
    "TestRemovedCompatibilityMethods",
    "TestResolveAliases",
    "TestResolveRef",
    "TestResolveVersionInteractive",
    "TestRewriteDepPaths",
    "TestRewritePep621",
    "TestRewritePoetry",
    "TestRuffFormatDuplicateFiles",
    "TestRunAudit",
    "TestRunBandit",
    "TestRunBuild",
    "TestRunCLIExtended",
    "TestRunCommand",
    "TestRunDeptry",
    "TestRunDetect",
    "TestRunFix",
    "TestRunGenerate",
    "TestRunGo",
    "TestRunLint",
    "TestRunMake",
    "TestRunMarkdown",
    "TestRunMigrate",
    "TestRunMypy",
    "TestRunMypyStubHints",
    "TestRunOrchestrate",
    "TestRunPipCheck",
    "TestRunPr",
    "TestRunPrWorkspace",
    "TestRunProjectFixMode",
    "TestRunProjectsBehavior",
    "TestRunProjectsReports",
    "TestRunProjectsValidation",
    "TestRunPyrefly",
    "TestRunPyright",
    "TestRunPyrightArgs",
    "TestRunRuffFix",
    "TestRunRuffFormat",
    "TestRunRuffLint",
    "TestRunSingleProject",
    "TestRunSync",
    "TestRunValidate",
    "TestRunWorkflows",
    "TestSafeLoadYaml",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScaffoldProjectCreatesSrcModules",
    "TestScaffoldProjectCreatesTestsModules",
    "TestScaffoldProjectIdempotency",
    "TestScaffoldProjectNoop",
    "TestScanModels",
    "TestScanPublicDefs",
    "TestScannerCore",
    "TestScannerHelpers",
    "TestScannerMultiFile",
    "TestSelectedProjectNames",
    "TestShouldBubbleUp",
    "TestShouldUseColor",
    "TestShouldUseUnicode",
    "TestSkillValidatorAstGrepCount",
    "TestSkillValidatorCore",
    "TestSkillValidatorRenderTemplate",
    "TestStringList",
    "TestStubChainAnalyze",
    "TestStubChainCore",
    "TestStubChainDiscoverProjects",
    "TestStubChainIsInternal",
    "TestStubChainStubExists",
    "TestStubChainValidate",
    "TestSubcommandMapping",
    "TestSync",
    "TestSyncMethodEdgeCases",
    "TestSyncMethodEdgeCasesMore",
    "TestSyncOne",
    "TestSynthesizedRepoMap",
    "TestToInfraValue",
    "TestUpdateChangelog",
    "TestValidateCore",
    "TestValidateGitRefEdgeCases",
    "TestValidateReport",
    "TestValidateScope",
    "TestVersionFiles",
    "TestViolationPattern",
    "TestWorkspaceCheckCLI",
    "TestWorkspaceCheckerBuildGateResult",
    "TestWorkspaceCheckerCollectMarkdownFiles",
    "TestWorkspaceCheckerDirsWithPy",
    "TestWorkspaceCheckerErrorSummary",
    "TestWorkspaceCheckerExecute",
    "TestWorkspaceCheckerExistingCheckDirs",
    "TestWorkspaceCheckerInitOSError",
    "TestWorkspaceCheckerInitialization",
    "TestWorkspaceCheckerParseGateCSV",
    "TestWorkspaceCheckerResolveGates",
    "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    "TestWorkspaceCheckerRunBandit",
    "TestWorkspaceCheckerRunCommand",
    "TestWorkspaceCheckerRunGo",
    "TestWorkspaceCheckerRunMarkdown",
    "TestWorkspaceCheckerRunMypy",
    "TestWorkspaceCheckerRunPyright",
    "TestWorkspaceRoot",
    "TestWorkspaceRootFromEnv",
    "TestWorkspaceRootFromParents",
    "TestWriteJson",
    "TestWriteMarkdown",
    "_utilities",
    "auditor",
    "auditor_budgets_tests",
    "auditor_cli_tests",
    "auditor_links_tests",
    "auditor_scope_tests",
    "auditor_tests",
    "autofix_workspace_tests",
    "basemk",
    "basemk_main",
    "basemk_validator_tests",
    "builder",
    "builder_scope_tests",
    "builder_tests",
    "c",
    "census",
    "census_models_tests",
    "census_tests",
    "check",
    "cli_tests",
    "codegen",
    "constants_quality_gate_tests",
    "container",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_execution",
    "d",
    "deps",
    "detector",
    "discovery",
    "doc",
    "docs",
    "e",
    "extended_cli_entry_tests",
    "extended_config_fixer_errors_tests",
    "extended_config_fixer_tests",
    "extended_error_reporting_tests",
    "extended_gate_bandit_markdown_tests",
    "extended_gate_go_cmd_tests",
    "extended_gate_mypy_pyright_tests",
    "extended_models_tests",
    "extended_project_runners_tests",
    "extended_projects_tests",
    "extended_resolve_gates_tests",
    "extended_run_projects_tests",
    "extended_runners_extra_tests",
    "extended_runners_go_tests",
    "extended_runners_ruff_tests",
    "extended_runners_tests",
    "extended_workspace_init_tests",
    "extract_dep_name",
    "fix_pyrefly_config_tests",
    "fixer",
    "fixer_internals_tests",
    "fixer_tests",
    "flow_tests",
    "gen",
    "generator_internals_tests",
    "generator_tests",
    "git_repo",
    "github",
    "h",
    "init_tests",
    "inventory_tests",
    "io",
    "is_external",
    "lazy_init_generation_tests",
    "lazy_init_helpers_tests",
    "lazy_init_process_tests",
    "lazy_init_service_tests",
    "lazy_init_tests",
    "lazy_init_transforms_tests",
    "m",
    "main",
    "main_cli_tests",
    "main_commands_tests",
    "main_dispatch_tests",
    "main_entry_tests",
    "main_integration_tests",
    "main_tests",
    "make_cmd_result",
    "make_gate_exec",
    "make_issue",
    "make_project",
    "normalize_link",
    "orchestrator",
    "orchestrator_git_tests",
    "orchestrator_helpers_tests",
    "orchestrator_phases_tests",
    "orchestrator_publish_tests",
    "orchestrator_tests",
    "p",
    "patch_gate_run",
    "patch_python_dir_detection",
    "pipeline_tests",
    "pyrefly_tests",
    "pyright_content",
    "pytest_diag",
    "r",
    "refactor",
    "refactor_main",
    "release",
    "release_init_tests",
    "rewrite_dep_paths",
    "rope_project",
    "run_command_failure_check",
    "runner",
    "s",
    "scaffolder_naming_tests",
    "scaffolder_tests",
    "scanner_tests",
    "service",
    "shared_iter_tests",
    "shared_tests",
    "shared_write_tests",
    "should_skip_target",
    "skill_validator_tests",
    "stub_chain_tests",
    "svc",
    "t",
    "test_all_three_capabilities_in_one_pass",
    "test_array",
    "test_as_string_list",
    "test_as_string_list_toml_item",
    "test_atomic_write_fail",
    "test_atomic_write_ok",
    "test_basemk_build_config_with_none",
    "test_basemk_build_config_with_project_name",
    "test_basemk_cli_generate_to_file",
    "test_basemk_cli_generate_to_stdout",
    "test_basemk_engine_execute_calls_render_all",
    "test_basemk_engine_render_all_handles_template_error",
    "test_basemk_engine_render_all_returns_string",
    "test_basemk_engine_render_all_with_valid_config",
    "test_basemk_main_ensures_structlog_configured",
    "test_basemk_main_output_to_stdout",
    "test_basemk_main_rejects_apply_flag",
    "test_basemk_main_with_generate_command",
    "test_basemk_main_with_generation_failure",
    "test_basemk_main_with_help",
    "test_basemk_main_with_invalid_command",
    "test_basemk_main_with_no_command",
    "test_basemk_main_with_none_argv",
    "test_basemk_main_with_output_file",
    "test_basemk_main_with_project_name",
    "test_basemk_main_with_write_failure",
    "test_build_impact_map_extracts_rename_entries",
    "test_build_impact_map_extracts_signature_entries",
    "test_bump_version_invalid",
    "test_bump_version_result_type",
    "test_bump_version_valid",
    "test_canonical_dev_dependencies",
    "test_capture_cases",
    "test_check_main_executes_real_cli",
    "test_class_reconstructor_reorders_each_contiguous_method_block",
    "test_class_reconstructor_reorders_methods_by_config",
    "test_class_reconstructor_skips_interleaved_non_method_members",
    "test_cli_forwards_canonical_root",
    "test_cli_result_by_project_root",
    "test_codegen_dir_returns_all_exports",
    "test_codegen_getattr_raises_attribute_error",
    "test_codegen_init_getattr_raises_attribute_error",
    "test_codegen_lazy_imports_work",
    "test_codegen_pipeline_end_to_end",
    "test_consolidate_groups_phase_apply_removes_old_groups",
    "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    "test_converts_multiple_aliases",
    "test_converts_typealias_to_pep695",
    "test_current_workspace_version",
    "test_declared_dependency_names_collects_all_supported_groups",
    "test_dedupe_specs",
    "test_dep_name",
    "test_detect_mode_with_nonexistent_path",
    "test_detect_mode_with_path_object",
    "test_detection_classify",
    "test_detection_deptry",
    "test_detection_discover",
    "test_detection_models",
    "test_detection_pip_check",
    "test_detection_typings",
    "test_detection_typings_flow",
    "test_detection_uncovered",
    "test_detector_detect",
    "test_detector_detect_failures",
    "test_detector_init",
    "test_detector_main",
    "test_detector_models",
    "test_detector_report",
    "test_detector_report_flags",
    "test_detects_attribute_base_class",
    "test_detects_basemodel_in_non_model_file",
    "test_detects_missing_local_composition_base",
    "test_detects_multiple_models",
    "test_detects_only_wrong_alias_in_mixed_import",
    "test_detects_same_project_submodule_alias_import",
    "test_detects_wrong_source_m_import",
    "test_detects_wrong_source_u_import",
    "test_discovery_consolidated",
    "test_engine",
    "test_engine_always_enables_class_nesting_file_rule",
    "test_ensure_future_annotations_after_docstring",
    "test_ensure_future_annotations_moves_existing_import_to_top",
    "test_ensure_pyrefly_config_phase_apply_errors",
    "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    "test_ensure_pyrefly_config_phase_apply_python_version",
    "test_ensure_pyrefly_config_phase_apply_search_path",
    "test_ensure_pytest_config_phase_apply_markers",
    "test_ensure_pytest_config_phase_apply_minversion",
    "test_ensure_pytest_config_phase_apply_python_classes",
    "test_ensure_table",
    "test_extra_paths_manager",
    "test_extra_paths_pep621",
    "test_extra_paths_sync",
    "test_extract_dep_name",
    "test_extract_requirement_name",
    "test_files_modified_tracks_affected_files",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_flexcore_excluded_from_run",
    "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    "test_formatting",
    "test_generator",
    "test_generator_edge_cases",
    "test_generator_execute_returns_generated_content",
    "test_generator_fails_for_invalid_make_syntax",
    "test_generator_generate_propagates_render_failure",
    "test_generator_generate_with_basemk_config_object",
    "test_generator_generate_with_dict_config",
    "test_generator_generate_with_invalid_dict_config",
    "test_generator_generate_with_none_config_uses_default",
    "test_generator_initializes_with_custom_engine",
    "test_generator_initializes_with_default_engine",
    "test_generator_normalize_config_with_basemk_config",
    "test_generator_normalize_config_with_dict",
    "test_generator_normalize_config_with_invalid_dict",
    "test_generator_normalize_config_with_none",
    "test_generator_renders_with_config_override",
    "test_generator_validate_generated_output_handles_oserror",
    "test_generator_write_creates_parent_directories",
    "test_generator_write_fails_without_output_or_stream",
    "test_generator_write_handles_file_permission_error",
    "test_generator_write_saves_output_file",
    "test_generator_write_to_file",
    "test_generator_write_to_stream",
    "test_generator_write_to_stream_handles_oserror",
    "test_gitignore_entry_scenarios",
    "test_gitignore_sync_failure",
    "test_gitignore_write_failure",
    "test_helpers_alias_is_reachable_helpers",
    "test_helpers_alias_is_reachable_project_obj",
    "test_import_alias_detector_skips_facade_and_subclass_files",
    "test_import_alias_detector_skips_nested_private_and_as_renames",
    "test_import_alias_detector_skips_private_and_class_imports",
    "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    "test_import_modernizer_updates_aliased_symbol_usage",
    "test_infra_constants_core",
    "test_infra_constants_extra",
    "test_infra_container",
    "test_infra_discovery",
    "test_infra_discovery_edge_cases",
    "test_infra_git",
    "test_infra_init_lazy_core",
    "test_infra_init_lazy_submodules",
    "test_infra_json_io",
    "test_infra_main",
    "test_infra_maintenance_cli",
    "test_infra_maintenance_init",
    "test_infra_maintenance_main",
    "test_infra_maintenance_python_version",
    "test_infra_output_edge_cases",
    "test_infra_output_formatting",
    "test_infra_paths",
    "test_infra_patterns_core",
    "test_infra_patterns_extra",
    "test_infra_protocols",
    "test_infra_refactor_analysis",
    "test_infra_refactor_class_and_propagation",
    "test_infra_refactor_class_placement",
    "test_infra_refactor_engine",
    "test_infra_refactor_import_modernizer",
    "test_infra_refactor_legacy_and_annotations",
    "test_infra_refactor_mro_completeness",
    "test_infra_refactor_mro_import_rewriter",
    "test_infra_refactor_namespace_aliases",
    "test_infra_refactor_namespace_source",
    "test_infra_refactor_pattern_corrections",
    "test_infra_refactor_project_classifier",
    "test_infra_refactor_safety",
    "test_infra_refactor_typing_unifier",
    "test_infra_reporting_core",
    "test_infra_reporting_extra",
    "test_infra_selection",
    "test_infra_subprocess_core",
    "test_infra_subprocess_extra",
    "test_infra_terminal_detection",
    "test_infra_toml_io",
    "test_infra_typings",
    "test_infra_utilities",
    "test_infra_version_core",
    "test_infra_version_extra",
    "test_infra_versioning",
    "test_infra_workspace_cli",
    "test_infra_workspace_detector",
    "test_infra_workspace_init",
    "test_infra_workspace_main",
    "test_infra_workspace_migrator",
    "test_infra_workspace_migrator_deps",
    "test_infra_workspace_migrator_dryrun",
    "test_infra_workspace_migrator_errors",
    "test_infra_workspace_migrator_internal",
    "test_infra_workspace_migrator_pyproject",
    "test_infra_workspace_orchestrator",
    "test_infra_workspace_sync",
    "test_init",
    "test_inject_comments_phase_apply_banner",
    "test_inject_comments_phase_apply_broken_group_section",
    "test_inject_comments_phase_apply_markers",
    "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    "test_inject_comments_phase_deduplicates_family_markers",
    "test_inject_comments_phase_marks_pytest_and_coverage_subtables",
    "test_inject_comments_phase_removes_auto_banner_and_auto_marker",
    "test_inject_comments_phase_repositions_marker_before_section",
    "test_injects_t_import_when_needed",
    "test_internal_sync_discovery",
    "test_internal_sync_discovery_edge",
    "test_internal_sync_main",
    "test_internal_sync_resolve",
    "test_internal_sync_sync",
    "test_internal_sync_sync_edge",
    "test_internal_sync_sync_edge_more",
    "test_internal_sync_update",
    "test_internal_sync_update_checkout_edge",
    "test_internal_sync_validation",
    "test_internal_sync_workspace",
    "test_iteration",
    "test_lazy_import_rule_hoists_import_to_module_level",
    "test_lazy_import_rule_uses_fix_action_for_hoist",
    "test_legacy_import_bypass_collapses_to_primary_import",
    "test_legacy_rule_uses_fix_action_remove_for_aliases",
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    "test_legacy_wrapper_function_is_inlined_as_alias",
    "test_legacy_wrapper_non_passthrough_is_not_inlined",
    "test_main",
    "test_main_all_groups_defined",
    "test_main_analyze_violations_is_read_only",
    "test_main_analyze_violations_writes_json_report",
    "test_main_cli",
    "test_main_discovery_failure",
    "test_main_dispatch",
    "test_main_group_descriptions_are_present",
    "test_main_help_flag_returns_zero",
    "test_main_no_changes_needed",
    "test_main_project_invalid_toml",
    "test_main_project_no_name",
    "test_main_project_non_string_name",
    "test_main_project_obj_not_dict_first_loop",
    "test_main_project_obj_not_dict_second_loop",
    "test_main_returns_error_when_no_args",
    "test_main_returns_nonzero_on_unknown",
    "test_main_returns_zero_on_help",
    "test_main_success_modes",
    "test_main_sync_failure",
    "test_main_unknown_group_returns_error",
    "test_main_with_changes_and_dry_run",
    "test_main_with_changes_no_dry_run",
    "test_maintenance_rejects_apply_flag",
    "test_make_boot_works_without_existing_venv_in_workspace_mode",
    "test_make_check_fast_path_check_only_suppresses_fix_writes",
    "test_make_check_file_scope_rejects_unsupported_gates",
    "test_make_check_file_scope_runs_mypy",
    "test_make_check_file_scope_unsets_python_path_env",
    "test_make_check_full_run_forwards_fix_and_tool_args",
    "test_make_check_full_run_unsets_python_path_env",
    "test_make_contract",
    "test_make_help_lists_supported_options",
    "test_migrate_makefile_not_found_non_dry_run",
    "test_migrate_pyproject_flext_core_non_dry_run",
    "test_migrate_workspace_applies_consumer_rewrites",
    "test_migrate_workspace_dry_run_preserves_files",
    "test_migrator_apply_updates_project_files",
    "test_migrator_discovery_failure",
    "test_migrator_dry_run_reports_changes_without_writes",
    "test_migrator_execute_returns_failure",
    "test_migrator_flext_core_dry_run",
    "test_migrator_flext_core_project_skipped",
    "test_migrator_gitignore_already_normalized_dry_run",
    "test_migrator_handles_missing_pyproject_gracefully",
    "test_migrator_has_flext_core_dependency_in_poetry",
    "test_migrator_has_flext_core_dependency_poetry_deps_not_table",
    "test_migrator_has_flext_core_dependency_poetry_table_missing",
    "test_migrator_makefile_not_found_dry_run",
    "test_migrator_makefile_read_failure",
    "test_migrator_no_changes_needed",
    "test_migrator_preserves_custom_makefile_content",
    "test_migrator_pyproject_not_found_dry_run",
    "test_migrator_workspace_root_not_exists",
    "test_migrator_workspace_root_project_detection",
    "test_modernizer_comments",
    "test_modernizer_consolidate",
    "test_modernizer_coverage",
    "test_modernizer_helpers",
    "test_modernizer_main",
    "test_modernizer_main_extra",
    "test_modernizer_pyrefly",
    "test_modernizer_pyright",
    "test_modernizer_pytest",
    "test_modernizer_workspace",
    "test_namespace_rewriter_keeps_contextual_alias_subset",
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports",
    "test_namespace_rewriter_skips_facade_and_subclass_files",
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates",
    "test_no_duplicate_t_import_when_t_from_project_package",
    "test_non_pydantic_class_not_flagged",
    "test_noop_clean_module",
    "test_parse_semver_invalid",
    "test_parse_semver_result_type",
    "test_parse_semver_valid",
    "test_path_sync_helpers",
    "test_path_sync_init",
    "test_path_sync_main",
    "test_path_sync_main_edges",
    "test_path_sync_main_more",
    "test_path_sync_main_project_obj",
    "test_path_sync_rewrite_deps",
    "test_path_sync_rewrite_pep621",
    "test_path_sync_rewrite_poetry",
    "test_pattern_rule_converts_dict_annotations_to_mapping",
    "test_pattern_rule_keeps_dict_param_when_copy_used",
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    "test_pattern_rule_removes_configured_redundant_casts",
    "test_pattern_rule_removes_nested_type_object_cast_chain",
    "test_pattern_rule_skips_overload_signatures",
    "test_pr_workspace_accepts_repeated_project_options",
    "test_preserves_annotated_in_function_params",
    "test_preserves_non_matching_unions",
    "test_preserves_override_in_method",
    "test_preserves_protocol_and_runtime_checkable",
    "test_preserves_type_checking_import",
    "test_preserves_typealias_import_when_class_level_usage_exists",
    "test_preserves_used_imports_when_import_precedes_usage",
    "test_preserves_used_typing_imports",
    "test_project_dev_groups",
    "test_project_dev_groups_missing_sections",
    "test_project_without_alias_facade_has_no_violation",
    "test_project_without_src_returns_empty",
    "test_pyrefly_search_paths_include_workspace_declared_dev_dependencies",
    "test_read_project_metadata_preserves_pep621_dependency_order",
    "test_read_project_metadata_preserves_poetry_dependency_order",
    "test_refactor_census_rejects_apply_before_subcommand",
    "test_refactor_centralize_accepts_apply_before_subcommand",
    "test_refactor_files_skips_non_python_inputs",
    "test_refactor_project_integrates_safety_manager",
    "test_refactor_project_scans_tests_and_scripts_dirs",
    "test_refactor_runtime_alias_imports_accepts_aliases_and_project",
    "test_removes_all_imports_when_none_used_import_first",
    "test_removes_all_unused_typing_imports",
    "test_removes_dead_typealias_import",
    "test_removes_typealias_import_only_when_all_usages_converted",
    "test_removes_unused_preserves_used_when_import_precedes_usage",
    "test_render_all_declares_and_documents_runtime_options",
    "test_render_all_exposes_canonical_public_targets",
    "test_render_all_generates_large_makefile",
    "test_render_all_has_no_scripts_path_references",
    "test_rendered_base_mk_declares_cli_group_roots",
    "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight",
    "test_replace_project_version",
    "test_replaces_container_union",
    "test_replaces_numeric_union",
    "test_replaces_primitives_union",
    "test_replaces_scalar_union",
    "test_resolve_gates_maps_type_alias",
    "test_rewrite_dep_paths_dry_run",
    "test_rewrite_dep_paths_read_failure",
    "test_rewrite_dep_paths_with_internal_names",
    "test_rewrite_dep_paths_with_no_deps",
    "test_rewrite_pep621_invalid_path_dep_regex",
    "test_rewrite_pep621_no_project_table",
    "test_rewrite_pep621_non_string_item",
    "test_rewrite_poetry_no_poetry_table",
    "test_rewrite_poetry_no_tool_table",
    "test_rewrite_poetry_with_non_dict_value",
    "test_rewriter_adds_missing_base_and_formats",
    "test_rewriter_namespace_source_is_idempotent_with_ruff",
    "test_rewriter_preserves_non_alias_symbols",
    "test_rewriter_splits_mixed_imports_correctly",
    "test_rope_hooks",
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    "test_rule_dispatch_fails_on_unknown_rule_mapping",
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    "test_rule_dispatch_prefers_fix_action_metadata",
    "test_run_cases",
    "test_run_cli_rejects_fix_flags_for_run",
    "test_run_cli_run_forwards_fix_and_tool_args",
    "test_run_cli_run_returns_one_for_fail",
    "test_run_cli_run_returns_two_for_error",
    "test_run_cli_run_returns_zero_for_pass",
    "test_run_cli_with_fail_fast_flag",
    "test_run_cli_with_multiple_projects",
    "test_run_raw_cases",
    "test_run_rope_post_hooks_applies_mro_migration",
    "test_run_rope_post_hooks_dry_run_is_non_mutating",
    "test_runtime_alias_migrator_merges_local_imports_in_src",
    "test_runtime_alias_migrator_merges_local_imports_in_tests",
    "test_runtime_alias_migrator_skips_unsafe_local_cycle",
    "test_safety",
    "test_scanning",
    "test_signature_propagation_removes_and_adds_keywords",
    "test_signature_propagation_renames_call_keyword",
    "test_skips_definition_files",
    "test_skips_facade_declaration_files",
    "test_skips_import_as_rename",
    "test_skips_init_file",
    "test_skips_models_directory",
    "test_skips_models_file",
    "test_skips_non_alias_symbols",
    "test_skips_non_facade_files",
    "test_skips_private_candidate_classes",
    "test_skips_private_class",
    "test_skips_protected_files",
    "test_skips_r_alias_universal_exception",
    "test_skips_same_project_private_submodule",
    "test_skips_same_project_submodule_class_import",
    "test_skips_settings_file",
    "test_skips_union_with_none",
    "test_skips_when_candidate_is_already_in_facade_bases",
    "test_string_zero_return_value",
    "test_stub_validate_help_returns_zero",
    "test_stub_validate_uses_all_flag",
    "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    "test_symbol_propagation_renames_import_and_local_references",
    "test_symbol_propagation_updates_mro_base_references",
    "test_sync_basemk_scenarios",
    "test_sync_error_scenarios",
    "test_sync_extra_paths_missing_root_pyproject",
    "test_sync_extra_paths_success_modes",
    "test_sync_extra_paths_sync_failure",
    "test_sync_one_edge_cases",
    "test_sync_regenerates_project_makefile_without_legacy_passthrough",
    "test_sync_root_validation",
    "test_sync_success_scenarios",
    "test_sync_updates_project_makefile_for_standalone_project",
    "test_sync_updates_workspace_makefile_for_workspace_root",
    "test_target_path",
    "test_typealias_conversion_preserves_used_typing_siblings",
    "test_unwrap_item",
    "test_unwrap_item_toml_item",
    "test_violation_analysis_counts_massive_patterns",
    "test_violation_analyzer_skips_non_utf8_files",
    "test_workspace_check_main_returns_error_without_projects",
    "test_workspace_cli_migrate_command",
    "test_workspace_cli_migrate_output_contains_summary",
    "test_workspace_cli_rejects_migrate_flags_for_detect",
    "test_workspace_makefile_generator_declares_canonical_workspace_variables",
    "test_workspace_makefile_generator_reuses_mod_and_boot_feedback",
    "test_workspace_makefile_generator_sanitizes_orchestrator_env",
    "test_workspace_migrator_error_handling_on_invalid_workspace",
    "test_workspace_migrator_makefile_not_found_dry_run",
    "test_workspace_migrator_makefile_read_error",
    "test_workspace_migrator_pyproject_write_error",
    "test_workspace_root_doc_construction",
    "test_workspace_root_fallback",
    "u",
    "v",
    "validate",
    "validator",
    "validator_internals_tests",
    "validator_tests",
    "version_resolution_tests",
    "workspace_check_tests",
    "workspace_main",
    "workspace_root",
    "workspace_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
