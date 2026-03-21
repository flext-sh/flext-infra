# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Unit package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from . import (
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
        validate as validate,
    )
    from ._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )
    from ._utilities.test_formatting import TestFormattingRunRuffFix
    from ._utilities.test_iteration import TestIterWorkspacePythonModules
    from ._utilities.test_parsing import TestParsingModuleAst, TestParsingModuleCst
    from ._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
        TestSafetyWorkspaceValidation,
    )
    from ._utilities.test_scanning import MockScanner, TestScanFileBatch, TestScanModels
    from .basemk.test_engine import (
        test_basemk_cli_generate_to_file,
        test_basemk_cli_generate_to_stdout,
        test_basemk_engine_execute_calls_render_all,
        test_basemk_engine_render_all_handles_template_error,
        test_basemk_engine_render_all_returns_string,
        test_basemk_engine_render_all_with_valid_config,
        test_generator_fails_for_invalid_make_syntax,
        test_generator_renders_with_config_override,
        test_generator_write_saves_output_file,
        test_render_all_generates_large_makefile,
        test_render_all_has_no_scripts_path_references,
    )
    from .basemk.test_generator import (
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
    from .basemk.test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror,
    )
    from .basemk.test_init import TestFlextInfraBaseMk
    from .basemk.test_main import (
        test_basemk_build_config_with_none,
        test_basemk_build_config_with_project_name,
        test_basemk_main_ensures_structlog_configured,
        test_basemk_main_output_to_stdout,
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
    from .check._shared_fixtures import (
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
    from .check._stubs import (
        Spy,
        make_cmd_result,
        make_gate_exec,
        make_issue,
        make_project,
    )
    from .check.cli_tests import (
        test_resolve_gates_maps_type_alias,
        test_run_cli_run_returns_one_for_fail,
        test_run_cli_run_returns_two_for_error,
        test_run_cli_run_returns_zero_for_pass,
        test_run_cli_with_fail_fast_flag,
        test_run_cli_with_multiple_projects,
    )
    from .check.extended_cli_entry_tests import (
        TestCheckMainEntryPoint,
        TestFixPyrelfyCLI,
        TestRunCLIExtended,
        TestWorkspaceCheckCLI,
    )
    from .check.extended_config_fixer_errors_tests import (
        TestConfigFixerPathResolution,
        TestConfigFixerRunMethods,
        TestConfigFixerRunWithVerbose,
        TestProcessFileReadError,
    )
    from .check.extended_config_fixer_tests import (
        TestConfigFixerEnsureProjectExcludes,
        TestConfigFixerExecute,
        TestConfigFixerFindPyprojectFiles,
        TestConfigFixerFixSearchPaths,
        TestConfigFixerProcessFile,
        TestConfigFixerRemoveIgnoreSubConfig,
        TestConfigFixerRun,
        TestConfigFixerToArray,
    )
    from .check.extended_error_reporting_tests import (
        TestErrorReporting,
        TestGoFmtEmptyLinesInOutput,
        TestMarkdownReportEmptyGates,
        TestMypyEmptyLinesInOutput,
        TestRuffFormatDuplicateFiles,
    )
    from .check.extended_gate_bandit_markdown_tests import (
        TestWorkspaceCheckerRunBandit,
        TestWorkspaceCheckerRunMarkdown,
    )
    from .check.extended_gate_go_cmd_tests import (
        TestWorkspaceCheckerCollectMarkdownFiles,
        TestWorkspaceCheckerRunCommand,
        TestWorkspaceCheckerRunGo,
        run_command_failure_check,
    )
    from .check.extended_gate_mypy_pyright_tests import (
        TestWorkspaceCheckerRunMypy,
        TestWorkspaceCheckerRunPyright,
    )
    from .check.extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary,
    )
    from .check.extended_project_runners_tests import TestJsonWriteFailure
    from .check.extended_projects_tests import (
        TestCheckProjectRunners,
        TestLintAndFormatPublicMethods,
    )
    from .check.extended_reports_tests import (
        TestMarkdownReportSkipsEmptyGates,
        TestMarkdownReportWithErrors,
        TestWorkspaceCheckerMarkdownReport,
        TestWorkspaceCheckerMarkdownReportEdgeCases,
        TestWorkspaceCheckerSARIFReport,
        TestWorkspaceCheckerSARIFReportEdgeCases,
    )
    from .check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates,
    )
    from .check.extended_run_projects_tests import (
        CheckProjectStub,
        ProjectResult,
        TestRunProjectsBehavior,
        TestRunProjectsReports,
        TestRunProjectsValidation,
        TestRunSingleProject,
    )
    from .check.extended_runners_extra_tests import (
        GateClass,
        TestRunBandit,
        TestRunMarkdown,
        TestRunPyright,
    )
    from .check.extended_runners_go_tests import RunCallable, TestRunGo
    from .check.extended_runners_ruff_tests import (
        TestCollectMarkdownFiles,
        TestRunCommand,
        TestRunRuffFormat,
        TestRunRuffLint,
    )
    from .check.extended_runners_tests import TestRunMypy, TestRunPyrefly
    from .check.extended_workspace_init_tests import (
        TestWorkspaceCheckerBuildGateResult,
        TestWorkspaceCheckerDirsWithPy,
        TestWorkspaceCheckerExecute,
        TestWorkspaceCheckerExistingCheckDirs,
        TestWorkspaceCheckerInitialization,
        TestWorkspaceCheckerInitOSError,
        TestWorkspaceCheckerResolveWorkspaceRootFallback,
    )
    from .check.fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help,
    )
    from .check.init_tests import TestFlextInfraCheck
    from .check.main_tests import test_check_main_executes_real_cli
    from .check.pyrefly_tests import TestFlextInfraConfigFixer
    from .check.workspace_check_tests import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from .check.workspace_tests import TestFlextInfraWorkspaceChecker
    from .codegen._project_factory import FlextInfraCodegenTestProjectFactory
    from .codegen.autofix_tests import (
        test_in_context_typevar_not_flagged,
        test_standalone_final_detected_as_fixable,
        test_standalone_typealias_detected_as_fixable,
        test_standalone_typevar_detected_as_fixable,
        test_syntax_error_files_skipped,
    )
    from .codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )
    from .codegen.census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )
    from .codegen.census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )
    from .codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )
    from .codegen.init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )
    from .codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )
    from .codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )
    from .codegen.lazy_init_process_tests import TestProcessDirectory
    from .codegen.lazy_init_service_tests import TestFlextInfraCodegenLazyInit
    from .codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from .codegen.lazy_init_transforms_tests import (
        TestExtractInlineConstants,
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanAstPublicDefs,
        TestShouldBubbleUp,
    )
    from .codegen.main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )
    from .codegen.pipeline_tests import test_codegen_pipeline_end_to_end
    from .codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from .codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )
    from .container.test_infra_container import (
        TestInfraContainerFunctions,
        TestInfraMroPattern,
        TestInfraServiceRetrieval,
    )
    from .deps.test_detection_classify import TestBuildProjectReport, TestClassifyIssues
    from .deps.test_detection_deptry import TestRunDeptry
    from .deps.test_detection_models import (
        TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService,
        TestToInfraValue,
    )
    from .deps.test_detection_pip_check import TestRunPipCheck
    from .deps.test_detection_typings import (
        TestLoadDependencyLimits,
        TestRunMypyStubHints,
    )
    from .deps.test_detection_typings_flow import TestModuleAndTypingsFlow
    from .deps.test_detection_uncovered import TestDetectionUncoveredLines
    from .deps.test_detection_wrappers import (
        TestModuleLevelWrappers,
        test_discover_projects_wrapper,
        test_get_current_typings_from_pyproject_wrapper,
        test_get_required_typings_wrapper,
        test_run_deptry_wrapper,
        test_run_mypy_stub_hints_wrapper,
        test_run_pip_check_wrapper,
    )
    from .deps.test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )
    from .deps.test_detector_detect_failures import TestDetectorRunFailures
    from .deps.test_detector_init import TestFlextInfraRuntimeDevDependencyDetectorInit
    from .deps.test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction,
    )
    from .deps.test_detector_models import TestFlextInfraDependencyDetectorModels
    from .deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )
    from .deps.test_detector_report_flags import TestDetectorReportFlags
    from .deps.test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestGetDepPaths,
        TestSyncOne,
    )
    from .deps.test_extra_paths_pep621 import (
        TestPathDepPathsPep621,
        TestPathDepPathsPoetry,
    )
    from .deps.test_extra_paths_sync import (
        pyright_content,
        test_main_success_modes,
        test_main_sync_failure,
        test_sync_extra_paths_missing_root_pyproject,
        test_sync_extra_paths_success_modes,
        test_sync_extra_paths_sync_failure,
        test_sync_one_edge_cases,
    )
    from .deps.test_init import TestFlextInfraDeps
    from .deps.test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )
    from .deps.test_internal_sync_discovery_edge import TestCollectInternalDepsEdgeCases
    from .deps.test_internal_sync_resolve import (
        TestInferOwnerFromOrigin,
        TestResolveRef,
        TestSynthesizedRepoMap,
    )
    from .deps.test_internal_sync_sync import TestSync
    from .deps.test_internal_sync_sync_edge import TestSyncMethodEdgeCases
    from .deps.test_internal_sync_sync_edge_more import TestSyncMethodEdgeCasesMore
    from .deps.test_internal_sync_update import (
        TestEnsureCheckout,
        TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases,
    )
    from .deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases,
    )
    from .deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases,
    )
    from .deps.test_internal_sync_workspace import (
        TestIsWorkspaceMode,
        TestWorkspaceRootFromEnv,
        TestWorkspaceRootFromParents,
    )
    from .deps.test_main import (
        TestMainHelpAndErrors,
        TestMainReturnValues,
        TestSubcommandMapping,
    )
    from .deps.test_main_dispatch import (
        TestMainDelegation,
        TestMainExceptionHandling,
        TestMainModuleImport,
        TestMainSubcommandDispatch,
        TestMainSysArgvModification,
        test_string_zero_return_value,
    )
    from .deps.test_modernizer_comments import (
        TestInjectCommentsPhase,
        test_inject_comments_phase_apply_banner,
        test_inject_comments_phase_apply_broken_group_section,
        test_inject_comments_phase_apply_markers,
        test_inject_comments_phase_apply_with_optional_dependencies_dev,
    )
    from .deps.test_modernizer_consolidate import (
        TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )
    from .deps.test_modernizer_helpers import (
        doc,
        test_array,
        test_as_string_list,
        test_as_string_list_toml_item,
        test_canonical_dev_dependencies,
        test_dedupe_specs,
        test_dep_name,
        test_ensure_table,
        test_project_dev_groups,
        test_project_dev_groups_missing_sections,
        test_unwrap_item,
        test_unwrap_item_toml_item,
    )
    from .deps.test_modernizer_main import (
        TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain,
    )
    from .deps.test_modernizer_main_extra import (
        TestModernizerEdgeCases,
        TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )
    from .deps.test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path,
    )
    from .deps.test_modernizer_pyright import TestEnsurePyrightConfigPhase
    from .deps.test_modernizer_pytest import (
        TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes,
    )
    from .deps.test_modernizer_workspace import (
        TestParser,
        TestReadDoc,
        test_workspace_root_doc_construction,
    )
    from .deps.test_path_sync_helpers import (
        extract_dep_name,
        test_extract_dep_name,
        test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers,
        test_target_path,
    )
    from .deps.test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object,
    )
    from .deps.test_path_sync_main_edges import TestMainEdgeCases
    from .deps.test_path_sync_main_more import (
        test_main_discovery_failure,
        test_main_no_changes_needed,
        test_main_project_invalid_toml,
        test_main_project_no_name,
        test_main_project_non_string_name,
        test_main_with_changes_and_dry_run,
        test_main_with_changes_no_dry_run,
        test_workspace_root_fallback,
    )
    from .deps.test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop,
    )
    from .deps.test_path_sync_rewrite_deps import (
        TestRewriteDepPaths,
        rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps,
    )
    from .deps.test_path_sync_rewrite_pep621 import (
        TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item,
    )
    from .deps.test_path_sync_rewrite_poetry import (
        TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value,
    )
    from .discovery.test_infra_discovery import TestFlextInfraDiscoveryService
    from .discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines,
    )
    from .docs.auditor_budgets_tests import TestLoadAuditBudgets
    from .docs.auditor_cli_tests import TestAuditorMainCli, TestAuditorScopeFailure
    from .docs.auditor_links_tests import TestAuditorBrokenLinks, TestAuditorToMarkdown
    from .docs.auditor_scope_tests import TestAuditorForbiddenTerms, TestAuditorScope
    from .docs.auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from .docs.builder_scope_tests import TestBuilderScope
    from .docs.builder_tests import TestBuilderCore, builder
    from .docs.fixer_internals_tests import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )
    from .docs.fixer_tests import TestFixerCore
    from .docs.generator_internals_tests import (
        TestGeneratorHelpers,
        TestGeneratorScope,
        gen,
    )
    from .docs.generator_tests import TestGeneratorCore
    from .docs.init_tests import TestFlextInfraDocs
    from .docs.main_commands_tests import TestRunBuild, TestRunGenerate, TestRunValidate
    from .docs.main_entry_tests import TestMainRouting, TestMainWithFlags
    from .docs.main_tests import TestRunAudit, TestRunFix
    from .docs.shared_iter_tests import TestIterMarkdownFiles, TestSelectedProjectNames
    from .docs.shared_tests import TestBuildScopes, TestFlextInfraDocScope
    from .docs.shared_write_tests import TestWriteJson, TestWriteMarkdown
    from .docs.validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )
    from .docs.validator_tests import TestValidateCore, TestValidateReport
    from .github._stubs import (
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
    from .github.main_dispatch_tests import TestRunPrWorkspace
    from .github.main_integration_tests import TestMain
    from .github.main_tests import (
        SyncOperation,
        TestRunLint,
        TestRunPr,
        TestRunWorkflows,
        main,
        run_lint,
        run_pr,
        run_pr_workspace,
        run_workflows,
    )
    from .io.test_infra_json_io import SampleModel, TestFlextInfraJsonService
    from .io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases,
        TestInfraOutputNoColor,
        TestMroFacadeMethods,
    )
    from .io.test_infra_output_formatting import (
        ANSI_RE,
        TestInfraOutputHeader,
        TestInfraOutputMessages,
        TestInfraOutputProgress,
        TestInfraOutputStatus,
        TestInfraOutputSummary,
    )
    from .io.test_infra_terminal_detection import (
        TestShouldUseColor,
        TestShouldUseUnicode,
    )
    from .refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files,
    )
    from .refactor.test_infra_refactor_class_and_propagation import (
        test_class_reconstructor_reorders_each_contiguous_method_block,
        test_class_reconstructor_reorders_methods_by_config,
        test_class_reconstructor_skips_interleaved_non_method_members,
        test_mro_checker_keeps_external_attribute_base,
        test_mro_redundancy_checker_removes_nested_attribute_inheritance,
        test_signature_propagation_removes_and_adds_keywords,
        test_signature_propagation_renames_call_keyword,
        test_symbol_propagation_keeps_alias_reference_when_asname_used,
        test_symbol_propagation_renames_import_and_local_references,
        test_symbol_propagation_updates_mro_base_references,
    )
    from .refactor.test_infra_refactor_class_placement import (
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
    from .refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata,
    )
    from .refactor.test_infra_refactor_import_modernizer import (
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
    from .refactor.test_infra_refactor_legacy_and_annotations import (
        test_ensure_future_annotations_after_docstring,
        test_ensure_future_annotations_moves_existing_import_to_top,
        test_legacy_import_bypass_collapses_to_primary_import,
        test_legacy_rule_uses_fix_action_remove_for_aliases,
        test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias,
        test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias,
        test_legacy_wrapper_function_is_inlined_as_alias,
        test_legacy_wrapper_non_passthrough_is_not_inlined,
    )
    from .refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files,
        test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases,
    )
    from .refactor.test_infra_refactor_namespace_aliases import (
        test_import_alias_detector_skips_facade_and_subclass_files,
        test_import_alias_detector_skips_nested_private_and_as_renames,
        test_import_alias_detector_skips_private_and_class_imports,
        test_namespace_rewriter_keeps_contextual_alias_subset,
        test_namespace_rewriter_only_rewrites_runtime_alias_imports,
        test_namespace_rewriter_skips_facade_and_subclass_files,
        test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates,
    )
    from .refactor.test_infra_refactor_namespace_source import (
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
    from .refactor.test_infra_refactor_pattern_corrections import (
        test_pattern_rule_converts_dict_annotations_to_mapping,
        test_pattern_rule_keeps_dict_param_when_copy_used,
        test_pattern_rule_keeps_dict_param_when_subscript_mutated,
        test_pattern_rule_keeps_type_cast_when_not_nested_object_cast,
        test_pattern_rule_optionally_converts_return_annotations_to_mapping,
        test_pattern_rule_removes_configured_redundant_casts,
        test_pattern_rule_removes_nested_type_object_cast_chain,
        test_pattern_rule_skips_overload_signatures,
    )
    from .refactor.test_infra_refactor_project_classifier import (
        test_expected_dependency_bases_by_family_preserves_internal_dependency_order,
        test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order,
    )
    from .refactor.test_infra_refactor_safety import (
        EngineSafetyStub,
        test_refactor_project_integrates_safety_manager,
    )
    from .refactor.test_infra_refactor_typing_unifier import (
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
    from .release._stubs import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
    )
    from .release.flow_tests import TestReleaseMainFlow
    from .release.main_tests import TestReleaseMainParsing
    from .release.orchestrator_git_tests import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )
    from .release.orchestrator_helpers_tests import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )
    from .release.orchestrator_phases_tests import (
        TestPhaseBuild,
        TestPhaseValidate,
        TestPhaseVersion,
    )
    from .release.orchestrator_publish_tests import TestPhasePublish
    from .release.orchestrator_tests import (
        TestReleaseOrchestratorExecute,
        workspace_root,
    )
    from .release.release_init_tests import TestReleaseInit
    from .release.version_resolution_tests import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
    )
    from .test_infra_constants_core import (
        TestFlextInfraConstantsExcludedNamespace,
        TestFlextInfraConstantsFilesNamespace,
        TestFlextInfraConstantsGatesNamespace,
        TestFlextInfraConstantsPathsNamespace,
        TestFlextInfraConstantsStatusNamespace,
    )
    from .test_infra_constants_extra import (
        TestFlextInfraConstantsAlias,
        TestFlextInfraConstantsCheckNamespace,
        TestFlextInfraConstantsConsistency,
        TestFlextInfraConstantsEncodingNamespace,
        TestFlextInfraConstantsGithubNamespace,
        TestFlextInfraConstantsImmutability,
    )
    from .test_infra_git import (
        TestFlextInfraGitService,
        TestGitPush,
        TestGitTagOperations,
        TestRemovedCompatibilityMethods,
        git_repo,
    )
    from .test_infra_init_lazy_core import TestFlextInfraInitLazyLoading
    from .test_infra_init_lazy_submodules import TestFlextInfraSubmoduleInitLazyLoading
    from .test_infra_main import (
        test_main_all_groups_defined,
        test_main_group_modules_are_valid,
        test_main_help_flag_returns_zero,
        test_main_returns_error_when_no_args,
        test_main_unknown_group_returns_error,
    )
    from .test_infra_maintenance_init import TestFlextInfraMaintenance
    from .test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess,
    )
    from .test_infra_maintenance_python_version import (
        TestDiscoverProjects,
        TestEnforcerExecute,
        TestEnsurePythonVersionFile,
        TestReadRequiredMinor,
        TestWorkspaceRoot,
    )
    from .test_infra_paths import TestFlextInfraPathResolver
    from .test_infra_patterns_core import (
        TestFlextInfraPatternsMarkdown,
        TestFlextInfraPatternsTooling,
    )
    from .test_infra_patterns_extra import (
        TestFlextInfraPatternsEdgeCases,
        TestFlextInfraPatternsPatternTypes,
    )
    from .test_infra_protocols import TestFlextInfraProtocolsImport
    from .test_infra_reporting_core import TestFlextInfraReportingServiceCore
    from .test_infra_reporting_extra import TestFlextInfraReportingServiceExtra
    from .test_infra_selection import TestFlextInfraUtilitiesSelection
    from .test_infra_subprocess_core import (
        runner,
        test_capture_cases,
        test_run_cases,
        test_run_raw_cases,
    )
    from .test_infra_subprocess_extra import TestFlextInfraCommandRunnerExtra
    from .test_infra_toml_io import (
        TestFlextInfraTomlDocument,
        TestFlextInfraTomlHelpers,
        TestFlextInfraTomlRead,
    )
    from .test_infra_typings import TestFlextInfraTypesImport
    from .test_infra_utilities import TestFlextInfraUtilitiesImport
    from .test_infra_version_core import TestFlextInfraVersionClass
    from .test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo,
    )
    from .test_infra_versioning import (
        service,
        test_bump_version_invalid,
        test_bump_version_result_type,
        test_bump_version_valid,
        test_current_workspace_version,
        test_parse_semver_invalid,
        test_parse_semver_result_type,
        test_parse_semver_valid,
        test_release_tag_from_branch_invalid,
        test_release_tag_from_branch_result_type,
        test_release_tag_from_branch_valid,
        test_replace_project_version,
    )
    from .test_infra_workspace_cli import (
        test_workspace_cli_migrate_command,
        test_workspace_cli_migrate_output_contains_summary,
    )
    from .test_infra_workspace_detector import (
        TestDetectorBasicDetection,
        TestDetectorGitRunScenarios,
        TestDetectorRepoNameExtraction,
        detector,
    )
    from .test_infra_workspace_init import TestFlextInfraWorkspace
    from .test_infra_workspace_main import (
        TestMainCli,
        TestRunDetect,
        TestRunMigrate,
        TestRunOrchestrate,
        TestRunSync,
    )
    from .test_infra_workspace_migrator import (
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
    from .test_infra_workspace_migrator_deps import (
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
    from .test_infra_workspace_migrator_dryrun import (
        test_migrator_flext_core_dry_run,
        test_migrator_flext_core_project_skipped,
        test_migrator_gitignore_already_normalized_dry_run,
        test_migrator_makefile_not_found_dry_run,
        test_migrator_makefile_read_failure,
        test_migrator_pyproject_not_found_dry_run,
    )
    from .test_infra_workspace_migrator_errors import (
        TestMigratorReadFailures,
        TestMigratorWriteFailures,
    )
    from .test_infra_workspace_migrator_internal import (
        TestMigratorEdgeCases,
        TestMigratorInternalMakefile,
        TestMigratorInternalPyproject,
    )
    from .test_infra_workspace_migrator_pyproject import (
        TestMigratorDryRun,
        TestMigratorFlextCore,
        TestMigratorPoetryDeps,
    )
    from .test_infra_workspace_orchestrator import (
        TestOrchestratorBasic,
        TestOrchestratorFailures,
        TestOrchestratorGateNormalization,
        orchestrator,
    )
    from .test_infra_workspace_sync import (
        SetupFn,
        svc,
        test_atomic_write_fail,
        test_atomic_write_ok,
        test_cli_result_by_project_root,
        test_gitignore_entry_scenarios,
        test_gitignore_sync_failure,
        test_gitignore_write_failure,
        test_sync_basemk_scenarios,
        test_sync_error_scenarios,
        test_sync_root_validation,
        test_sync_success_scenarios,
    )
    from .validate.basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from .validate.init_tests import TestCoreModuleInit
    from .validate.inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from .validate.main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )
    from .validate.pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )
    from .validate.scanner_tests import (
        TestScannerCore,
        TestScannerHelpers,
        TestScannerMultiFile,
    )
    from .validate.skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )
    from .validate.stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ANSI_RE": ("tests.infra.unit.io.test_infra_output_formatting", "ANSI_RE"),
    "CheckProjectStub": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "CheckProjectStub",
    ),
    "EngineSafetyStub": (
        "tests.infra.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ),
    "FAMILY_FILE_MAP": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_FILE_MAP",
    ),
    "FAMILY_SUFFIX_MAP": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_SUFFIX_MAP",
    ),
    "FakeReporting": ("tests.infra.unit.release._stubs", "FakeReporting"),
    "FakeSelection": ("tests.infra.unit.release._stubs", "FakeSelection"),
    "FakeSubprocess": ("tests.infra.unit.release._stubs", "FakeSubprocess"),
    "FakeUtilsNamespace": ("tests.infra.unit.release._stubs", "FakeUtilsNamespace"),
    "FakeVersioning": ("tests.infra.unit.release._stubs", "FakeVersioning"),
    "FlextInfraCodegenTestProjectFactory": (
        "tests.infra.unit.codegen._project_factory",
        "FlextInfraCodegenTestProjectFactory",
    ),
    "GateClass": ("tests.infra.unit.check.extended_runners_extra_tests", "GateClass"),
    "MockScanner": ("tests.infra.unit._utilities.test_scanning", "MockScanner"),
    "ProjectResult": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "ProjectResult",
    ),
    "RunCallable": ("tests.infra.unit.check.extended_runners_go_tests", "RunCallable"),
    "RunProjectsMock": ("tests.infra.unit.check._shared_fixtures", "RunProjectsMock"),
    "SampleModel": ("tests.infra.unit.io.test_infra_json_io", "SampleModel"),
    "SetupFn": ("tests.infra.unit.test_infra_workspace_sync", "SetupFn"),
    "Spy": ("tests.infra.unit.check._stubs", "Spy"),
    "StubCommandOutput": ("tests.infra.unit.github._stubs", "StubCommandOutput"),
    "StubJsonIo": ("tests.infra.unit.github._stubs", "StubJsonIo"),
    "StubLinter": ("tests.infra.unit.github._stubs", "StubLinter"),
    "StubPrManager": ("tests.infra.unit.github._stubs", "StubPrManager"),
    "StubProjectInfo": ("tests.infra.unit.github._stubs", "StubProjectInfo"),
    "StubReporting": ("tests.infra.unit.github._stubs", "StubReporting"),
    "StubRunner": ("tests.infra.unit.github._stubs", "StubRunner"),
    "StubSelector": ("tests.infra.unit.github._stubs", "StubSelector"),
    "StubSyncer": ("tests.infra.unit.github._stubs", "StubSyncer"),
    "StubTemplates": ("tests.infra.unit.github._stubs", "StubTemplates"),
    "StubUtilities": ("tests.infra.unit.github._stubs", "StubUtilities"),
    "StubVersioning": ("tests.infra.unit.github._stubs", "StubVersioning"),
    "StubWorkspaceManager": ("tests.infra.unit.github._stubs", "StubWorkspaceManager"),
    "SyncOperation": ("tests.infra.unit.github.main_tests", "SyncOperation"),
    "TestAdrHelpers": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestAdrHelpers",
    ),
    "TestAllDirectoriesScanned": (
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestAllDirectoriesScanned",
    ),
    "TestAuditorBrokenLinks": (
        "tests.infra.unit.docs.auditor_links_tests",
        "TestAuditorBrokenLinks",
    ),
    "TestAuditorCore": ("tests.infra.unit.docs.auditor_tests", "TestAuditorCore"),
    "TestAuditorForbiddenTerms": (
        "tests.infra.unit.docs.auditor_scope_tests",
        "TestAuditorForbiddenTerms",
    ),
    "TestAuditorMainCli": (
        "tests.infra.unit.docs.auditor_cli_tests",
        "TestAuditorMainCli",
    ),
    "TestAuditorNormalize": (
        "tests.infra.unit.docs.auditor_tests",
        "TestAuditorNormalize",
    ),
    "TestAuditorScope": (
        "tests.infra.unit.docs.auditor_scope_tests",
        "TestAuditorScope",
    ),
    "TestAuditorScopeFailure": (
        "tests.infra.unit.docs.auditor_cli_tests",
        "TestAuditorScopeFailure",
    ),
    "TestAuditorToMarkdown": (
        "tests.infra.unit.docs.auditor_links_tests",
        "TestAuditorToMarkdown",
    ),
    "TestBaseMkValidatorCore": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorCore",
    ),
    "TestBaseMkValidatorEdgeCases": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorEdgeCases",
    ),
    "TestBaseMkValidatorSha256": (
        "tests.infra.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorSha256",
    ),
    "TestBuildProjectReport": (
        "tests.infra.unit.deps.test_detection_classify",
        "TestBuildProjectReport",
    ),
    "TestBuildScopes": ("tests.infra.unit.docs.shared_tests", "TestBuildScopes"),
    "TestBuildSiblingExportIndex": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestBuildSiblingExportIndex",
    ),
    "TestBuildTargets": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestBuildTargets",
    ),
    "TestBuilderCore": ("tests.infra.unit.docs.builder_tests", "TestBuilderCore"),
    "TestBuilderScope": (
        "tests.infra.unit.docs.builder_scope_tests",
        "TestBuilderScope",
    ),
    "TestBumpNextDev": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestBumpNextDev",
    ),
    "TestCensusReportModel": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestCensusReportModel",
    ),
    "TestCensusViolationModel": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestCensusViolationModel",
    ),
    "TestCheckIssueFormatted": (
        "tests.infra.unit.check.extended_models_tests",
        "TestCheckIssueFormatted",
    ),
    "TestCheckMainEntryPoint": (
        "tests.infra.unit.check.extended_cli_entry_tests",
        "TestCheckMainEntryPoint",
    ),
    "TestCheckOnlyMode": (
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestCheckOnlyMode",
    ),
    "TestCheckProjectRunners": (
        "tests.infra.unit.check.extended_projects_tests",
        "TestCheckProjectRunners",
    ),
    "TestClassifyIssues": (
        "tests.infra.unit.deps.test_detection_classify",
        "TestClassifyIssues",
    ),
    "TestCollectChanges": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCollectChanges",
    ),
    "TestCollectInternalDeps": (
        "tests.infra.unit.deps.test_internal_sync_discovery",
        "TestCollectInternalDeps",
    ),
    "TestCollectInternalDepsEdgeCases": (
        "tests.infra.unit.deps.test_internal_sync_discovery_edge",
        "TestCollectInternalDepsEdgeCases",
    ),
    "TestCollectMarkdownFiles": (
        "tests.infra.unit.check.extended_runners_ruff_tests",
        "TestCollectMarkdownFiles",
    ),
    "TestConfigFixerEnsureProjectExcludes": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerEnsureProjectExcludes",
    ),
    "TestConfigFixerExecute": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerExecute",
    ),
    "TestConfigFixerFindPyprojectFiles": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFindPyprojectFiles",
    ),
    "TestConfigFixerFixSearchPaths": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFixSearchPaths",
    ),
    "TestConfigFixerPathResolution": (
        "tests.infra.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerPathResolution",
    ),
    "TestConfigFixerProcessFile": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerProcessFile",
    ),
    "TestConfigFixerRemoveIgnoreSubConfig": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRemoveIgnoreSubConfig",
    ),
    "TestConfigFixerRun": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRun",
    ),
    "TestConfigFixerRunMethods": (
        "tests.infra.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunMethods",
    ),
    "TestConfigFixerRunWithVerbose": (
        "tests.infra.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunWithVerbose",
    ),
    "TestConfigFixerToArray": (
        "tests.infra.unit.check.extended_config_fixer_tests",
        "TestConfigFixerToArray",
    ),
    "TestConsolidateGroupsPhase": (
        "tests.infra.unit.deps.test_modernizer_consolidate",
        "TestConsolidateGroupsPhase",
    ),
    "TestConstants": (
        "tests.infra.unit.deps.test_extra_paths_manager",
        "TestConstants",
    ),
    "TestConstantsQualityGateCLIDispatch": (
        "tests.infra.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateCLIDispatch",
    ),
    "TestConstantsQualityGateVerdict": (
        "tests.infra.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateVerdict",
    ),
    "TestCoreModuleInit": (
        "tests.infra.unit.validate.init_tests",
        "TestCoreModuleInit",
    ),
    "TestCreateBranches": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCreateBranches",
    ),
    "TestCreateTag": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCreateTag",
    ),
    "TestDetectMode": ("tests.infra.unit.deps.test_path_sync_init", "TestDetectMode"),
    "TestDetectionUncoveredLines": (
        "tests.infra.unit.deps.test_detection_uncovered",
        "TestDetectionUncoveredLines",
    ),
    "TestDetectorBasicDetection": (
        "tests.infra.unit.test_infra_workspace_detector",
        "TestDetectorBasicDetection",
    ),
    "TestDetectorGitRunScenarios": (
        "tests.infra.unit.test_infra_workspace_detector",
        "TestDetectorGitRunScenarios",
    ),
    "TestDetectorRepoNameExtraction": (
        "tests.infra.unit.test_infra_workspace_detector",
        "TestDetectorRepoNameExtraction",
    ),
    "TestDetectorReportFlags": (
        "tests.infra.unit.deps.test_detector_report_flags",
        "TestDetectorReportFlags",
    ),
    "TestDetectorRunFailures": (
        "tests.infra.unit.deps.test_detector_detect_failures",
        "TestDetectorRunFailures",
    ),
    "TestDiscoverProjects": (
        "tests.infra.unit.test_infra_maintenance_python_version",
        "TestDiscoverProjects",
    ),
    "TestDiscoveryDiscoverProjects": (
        "tests.infra.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryDiscoverProjects",
    ),
    "TestDiscoveryFindAllPyprojectFiles": (
        "tests.infra.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryFindAllPyprojectFiles",
    ),
    "TestDiscoveryIterPythonFiles": (
        "tests.infra.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryIterPythonFiles",
    ),
    "TestDiscoveryProjectRoots": (
        "tests.infra.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryProjectRoots",
    ),
    "TestDispatchPhase": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestDispatchPhase",
    ),
    "TestEdgeCases": ("tests.infra.unit.codegen.lazy_init_tests", "TestEdgeCases"),
    "TestEnforcerExecute": (
        "tests.infra.unit.test_infra_maintenance_python_version",
        "TestEnforcerExecute",
    ),
    "TestEnsureCheckout": (
        "tests.infra.unit.deps.test_internal_sync_update",
        "TestEnsureCheckout",
    ),
    "TestEnsureCheckoutEdgeCases": (
        "tests.infra.unit.deps.test_internal_sync_update_checkout_edge",
        "TestEnsureCheckoutEdgeCases",
    ),
    "TestEnsurePyreflyConfigPhase": (
        "tests.infra.unit.deps.test_modernizer_pyrefly",
        "TestEnsurePyreflyConfigPhase",
    ),
    "TestEnsurePyrightConfigPhase": (
        "tests.infra.unit.deps.test_modernizer_pyright",
        "TestEnsurePyrightConfigPhase",
    ),
    "TestEnsurePytestConfigPhase": (
        "tests.infra.unit.deps.test_modernizer_pytest",
        "TestEnsurePytestConfigPhase",
    ),
    "TestEnsurePythonVersionFile": (
        "tests.infra.unit.test_infra_maintenance_python_version",
        "TestEnsurePythonVersionFile",
    ),
    "TestEnsureSymlink": (
        "tests.infra.unit.deps.test_internal_sync_update",
        "TestEnsureSymlink",
    ),
    "TestEnsureSymlinkEdgeCases": (
        "tests.infra.unit.deps.test_internal_sync_update",
        "TestEnsureSymlinkEdgeCases",
    ),
    "TestErrorReporting": (
        "tests.infra.unit.check.extended_error_reporting_tests",
        "TestErrorReporting",
    ),
    "TestExcludedDirectories": (
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestExcludedDirectories",
    ),
    "TestExcludedProjects": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestExcludedProjects",
    ),
    "TestExtractExports": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestExtractExports",
    ),
    "TestExtractInlineConstants": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestExtractInlineConstants",
    ),
    "TestExtractVersionExports": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestExtractVersionExports",
    ),
    "TestFixPyrelfyCLI": (
        "tests.infra.unit.check.extended_cli_entry_tests",
        "TestFixPyrelfyCLI",
    ),
    "TestFixabilityClassification": (
        "tests.infra.unit.codegen.census_tests",
        "TestFixabilityClassification",
    ),
    "TestFixerCore": ("tests.infra.unit.docs.fixer_tests", "TestFixerCore"),
    "TestFixerMaybeFixLink": (
        "tests.infra.unit.docs.fixer_internals_tests",
        "TestFixerMaybeFixLink",
    ),
    "TestFixerProcessFile": (
        "tests.infra.unit.docs.fixer_internals_tests",
        "TestFixerProcessFile",
    ),
    "TestFixerScope": ("tests.infra.unit.docs.fixer_internals_tests", "TestFixerScope"),
    "TestFixerToc": ("tests.infra.unit.docs.fixer_internals_tests", "TestFixerToc"),
    "TestFlextInfraBaseMk": (
        "tests.infra.unit.basemk.test_init",
        "TestFlextInfraBaseMk",
    ),
    "TestFlextInfraCheck": ("tests.infra.unit.check.init_tests", "TestFlextInfraCheck"),
    "TestFlextInfraCodegenLazyInit": (
        "tests.infra.unit.codegen.lazy_init_service_tests",
        "TestFlextInfraCodegenLazyInit",
    ),
    "TestFlextInfraCommandRunnerExtra": (
        "tests.infra.unit.test_infra_subprocess_extra",
        "TestFlextInfraCommandRunnerExtra",
    ),
    "TestFlextInfraConfigFixer": (
        "tests.infra.unit.check.pyrefly_tests",
        "TestFlextInfraConfigFixer",
    ),
    "TestFlextInfraConstantsAlias": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsAlias",
    ),
    "TestFlextInfraConstantsCheckNamespace": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsCheckNamespace",
    ),
    "TestFlextInfraConstantsConsistency": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsConsistency",
    ),
    "TestFlextInfraConstantsEncodingNamespace": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsEncodingNamespace",
    ),
    "TestFlextInfraConstantsExcludedNamespace": (
        "tests.infra.unit.test_infra_constants_core",
        "TestFlextInfraConstantsExcludedNamespace",
    ),
    "TestFlextInfraConstantsFilesNamespace": (
        "tests.infra.unit.test_infra_constants_core",
        "TestFlextInfraConstantsFilesNamespace",
    ),
    "TestFlextInfraConstantsGatesNamespace": (
        "tests.infra.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGatesNamespace",
    ),
    "TestFlextInfraConstantsGithubNamespace": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsGithubNamespace",
    ),
    "TestFlextInfraConstantsImmutability": (
        "tests.infra.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsImmutability",
    ),
    "TestFlextInfraConstantsPathsNamespace": (
        "tests.infra.unit.test_infra_constants_core",
        "TestFlextInfraConstantsPathsNamespace",
    ),
    "TestFlextInfraConstantsStatusNamespace": (
        "tests.infra.unit.test_infra_constants_core",
        "TestFlextInfraConstantsStatusNamespace",
    ),
    "TestFlextInfraDependencyDetectionModels": (
        "tests.infra.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionModels",
    ),
    "TestFlextInfraDependencyDetectionService": (
        "tests.infra.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionService",
    ),
    "TestFlextInfraDependencyDetectorModels": (
        "tests.infra.unit.deps.test_detector_models",
        "TestFlextInfraDependencyDetectorModels",
    ),
    "TestFlextInfraDependencyPathSync": (
        "tests.infra.unit.deps.test_path_sync_init",
        "TestFlextInfraDependencyPathSync",
    ),
    "TestFlextInfraDeps": ("tests.infra.unit.deps.test_init", "TestFlextInfraDeps"),
    "TestFlextInfraDiscoveryService": (
        "tests.infra.unit.discovery.test_infra_discovery",
        "TestFlextInfraDiscoveryService",
    ),
    "TestFlextInfraDiscoveryServiceUncoveredLines": (
        "tests.infra.unit.discovery.test_infra_discovery_edge_cases",
        "TestFlextInfraDiscoveryServiceUncoveredLines",
    ),
    "TestFlextInfraDocScope": (
        "tests.infra.unit.docs.shared_tests",
        "TestFlextInfraDocScope",
    ),
    "TestFlextInfraDocs": ("tests.infra.unit.docs.init_tests", "TestFlextInfraDocs"),
    "TestFlextInfraExtraPathsManager": (
        "tests.infra.unit.deps.test_extra_paths_manager",
        "TestFlextInfraExtraPathsManager",
    ),
    "TestFlextInfraGitService": (
        "tests.infra.unit.test_infra_git",
        "TestFlextInfraGitService",
    ),
    "TestFlextInfraInitLazyLoading": (
        "tests.infra.unit.test_infra_init_lazy_core",
        "TestFlextInfraInitLazyLoading",
    ),
    "TestFlextInfraInternalDependencySyncService": (
        "tests.infra.unit.deps.test_internal_sync_validation",
        "TestFlextInfraInternalDependencySyncService",
    ),
    "TestFlextInfraJsonService": (
        "tests.infra.unit.io.test_infra_json_io",
        "TestFlextInfraJsonService",
    ),
    "TestFlextInfraMaintenance": (
        "tests.infra.unit.test_infra_maintenance_init",
        "TestFlextInfraMaintenance",
    ),
    "TestFlextInfraPathResolver": (
        "tests.infra.unit.test_infra_paths",
        "TestFlextInfraPathResolver",
    ),
    "TestFlextInfraPatternsEdgeCases": (
        "tests.infra.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsEdgeCases",
    ),
    "TestFlextInfraPatternsMarkdown": (
        "tests.infra.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsMarkdown",
    ),
    "TestFlextInfraPatternsPatternTypes": (
        "tests.infra.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsPatternTypes",
    ),
    "TestFlextInfraPatternsTooling": (
        "tests.infra.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsTooling",
    ),
    "TestFlextInfraProtocolsImport": (
        "tests.infra.unit.test_infra_protocols",
        "TestFlextInfraProtocolsImport",
    ),
    "TestFlextInfraPyprojectModernizer": (
        "tests.infra.unit.deps.test_modernizer_main",
        "TestFlextInfraPyprojectModernizer",
    ),
    "TestFlextInfraReportingServiceCore": (
        "tests.infra.unit.test_infra_reporting_core",
        "TestFlextInfraReportingServiceCore",
    ),
    "TestFlextInfraReportingServiceExtra": (
        "tests.infra.unit.test_infra_reporting_extra",
        "TestFlextInfraReportingServiceExtra",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorInit": (
        "tests.infra.unit.deps.test_detector_init",
        "TestFlextInfraRuntimeDevDependencyDetectorInit",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect": (
        "tests.infra.unit.deps.test_detector_detect",
        "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport": (
        "tests.infra.unit.deps.test_detector_report",
        "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings": (
        "tests.infra.unit.deps.test_detector_main",
        "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    ),
    "TestFlextInfraSubmoduleInitLazyLoading": (
        "tests.infra.unit.test_infra_init_lazy_submodules",
        "TestFlextInfraSubmoduleInitLazyLoading",
    ),
    "TestFlextInfraTomlDocument": (
        "tests.infra.unit.test_infra_toml_io",
        "TestFlextInfraTomlDocument",
    ),
    "TestFlextInfraTomlHelpers": (
        "tests.infra.unit.test_infra_toml_io",
        "TestFlextInfraTomlHelpers",
    ),
    "TestFlextInfraTomlRead": (
        "tests.infra.unit.test_infra_toml_io",
        "TestFlextInfraTomlRead",
    ),
    "TestFlextInfraTypesImport": (
        "tests.infra.unit.test_infra_typings",
        "TestFlextInfraTypesImport",
    ),
    "TestFlextInfraUtilitiesImport": (
        "tests.infra.unit.test_infra_utilities",
        "TestFlextInfraUtilitiesImport",
    ),
    "TestFlextInfraUtilitiesSelection": (
        "tests.infra.unit.test_infra_selection",
        "TestFlextInfraUtilitiesSelection",
    ),
    "TestFlextInfraVersionClass": (
        "tests.infra.unit.test_infra_version_core",
        "TestFlextInfraVersionClass",
    ),
    "TestFlextInfraVersionModuleLevel": (
        "tests.infra.unit.test_infra_version_extra",
        "TestFlextInfraVersionModuleLevel",
    ),
    "TestFlextInfraVersionPackageInfo": (
        "tests.infra.unit.test_infra_version_extra",
        "TestFlextInfraVersionPackageInfo",
    ),
    "TestFlextInfraWorkspace": (
        "tests.infra.unit.test_infra_workspace_init",
        "TestFlextInfraWorkspace",
    ),
    "TestFlextInfraWorkspaceChecker": (
        "tests.infra.unit.check.workspace_tests",
        "TestFlextInfraWorkspaceChecker",
    ),
    "TestFormattingRunRuffFix": (
        "tests.infra.unit._utilities.test_formatting",
        "TestFormattingRunRuffFix",
    ),
    "TestGenerateFile": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestGenerateFile",
    ),
    "TestGenerateNotes": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestGenerateNotes",
    ),
    "TestGenerateTypeChecking": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestGenerateTypeChecking",
    ),
    "TestGeneratedClassNamingConvention": (
        "tests.infra.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedClassNamingConvention",
    ),
    "TestGeneratedFilesAreValidPython": (
        "tests.infra.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedFilesAreValidPython",
    ),
    "TestGeneratorCore": ("tests.infra.unit.docs.generator_tests", "TestGeneratorCore"),
    "TestGeneratorHelpers": (
        "tests.infra.unit.docs.generator_internals_tests",
        "TestGeneratorHelpers",
    ),
    "TestGeneratorScope": (
        "tests.infra.unit.docs.generator_internals_tests",
        "TestGeneratorScope",
    ),
    "TestGetDepPaths": (
        "tests.infra.unit.deps.test_extra_paths_manager",
        "TestGetDepPaths",
    ),
    "TestGitPush": ("tests.infra.unit.test_infra_git", "TestGitPush"),
    "TestGitTagOperations": ("tests.infra.unit.test_infra_git", "TestGitTagOperations"),
    "TestGoFmtEmptyLinesInOutput": (
        "tests.infra.unit.check.extended_error_reporting_tests",
        "TestGoFmtEmptyLinesInOutput",
    ),
    "TestHandleLazyInit": ("tests.infra.unit.codegen.main_tests", "TestHandleLazyInit"),
    "TestInferOwnerFromOrigin": (
        "tests.infra.unit.deps.test_internal_sync_resolve",
        "TestInferOwnerFromOrigin",
    ),
    "TestInferPackage": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestInferPackage",
    ),
    "TestInfraContainerFunctions": (
        "tests.infra.unit.container.test_infra_container",
        "TestInfraContainerFunctions",
    ),
    "TestInfraMroPattern": (
        "tests.infra.unit.container.test_infra_container",
        "TestInfraMroPattern",
    ),
    "TestInfraOutputEdgeCases": (
        "tests.infra.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputEdgeCases",
    ),
    "TestInfraOutputHeader": (
        "tests.infra.unit.io.test_infra_output_formatting",
        "TestInfraOutputHeader",
    ),
    "TestInfraOutputMessages": (
        "tests.infra.unit.io.test_infra_output_formatting",
        "TestInfraOutputMessages",
    ),
    "TestInfraOutputNoColor": (
        "tests.infra.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputNoColor",
    ),
    "TestInfraOutputProgress": (
        "tests.infra.unit.io.test_infra_output_formatting",
        "TestInfraOutputProgress",
    ),
    "TestInfraOutputStatus": (
        "tests.infra.unit.io.test_infra_output_formatting",
        "TestInfraOutputStatus",
    ),
    "TestInfraOutputSummary": (
        "tests.infra.unit.io.test_infra_output_formatting",
        "TestInfraOutputSummary",
    ),
    "TestInfraServiceRetrieval": (
        "tests.infra.unit.container.test_infra_container",
        "TestInfraServiceRetrieval",
    ),
    "TestInjectCommentsPhase": (
        "tests.infra.unit.deps.test_modernizer_comments",
        "TestInjectCommentsPhase",
    ),
    "TestInventoryServiceCore": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceCore",
    ),
    "TestInventoryServiceReports": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceReports",
    ),
    "TestInventoryServiceScripts": (
        "tests.infra.unit.validate.inventory_tests",
        "TestInventoryServiceScripts",
    ),
    "TestIsInternalPathDep": (
        "tests.infra.unit.deps.test_internal_sync_validation",
        "TestIsInternalPathDep",
    ),
    "TestIsRelativeTo": (
        "tests.infra.unit.deps.test_internal_sync_validation",
        "TestIsRelativeTo",
    ),
    "TestIsWorkspaceMode": (
        "tests.infra.unit.deps.test_internal_sync_workspace",
        "TestIsWorkspaceMode",
    ),
    "TestIterMarkdownFiles": (
        "tests.infra.unit.docs.shared_iter_tests",
        "TestIterMarkdownFiles",
    ),
    "TestIterWorkspacePythonModules": (
        "tests.infra.unit._utilities.test_iteration",
        "TestIterWorkspacePythonModules",
    ),
    "TestJsonWriteFailure": (
        "tests.infra.unit.check.extended_project_runners_tests",
        "TestJsonWriteFailure",
    ),
    "TestLintAndFormatPublicMethods": (
        "tests.infra.unit.check.extended_projects_tests",
        "TestLintAndFormatPublicMethods",
    ),
    "TestLoadAuditBudgets": (
        "tests.infra.unit.docs.auditor_budgets_tests",
        "TestLoadAuditBudgets",
    ),
    "TestLoadDependencyLimits": (
        "tests.infra.unit.deps.test_detection_typings",
        "TestLoadDependencyLimits",
    ),
    "TestMain": ("tests.infra.unit.github.main_integration_tests", "TestMain"),
    "TestMainBaseMkValidate": (
        "tests.infra.unit.validate.main_tests",
        "TestMainBaseMkValidate",
    ),
    "TestMainCli": ("tests.infra.unit.test_infra_workspace_main", "TestMainCli"),
    "TestMainCliRouting": (
        "tests.infra.unit.validate.main_tests",
        "TestMainCliRouting",
    ),
    "TestMainCommandDispatch": (
        "tests.infra.unit.codegen.main_tests",
        "TestMainCommandDispatch",
    ),
    "TestMainDelegation": (
        "tests.infra.unit.deps.test_main_dispatch",
        "TestMainDelegation",
    ),
    "TestMainEdgeCases": (
        "tests.infra.unit.deps.test_path_sync_main_edges",
        "TestMainEdgeCases",
    ),
    "TestMainEntryPoint": ("tests.infra.unit.codegen.main_tests", "TestMainEntryPoint"),
    "TestMainExceptionHandling": (
        "tests.infra.unit.deps.test_main_dispatch",
        "TestMainExceptionHandling",
    ),
    "TestMainFunction": (
        "tests.infra.unit.deps.test_detector_main",
        "TestMainFunction",
    ),
    "TestMainHelpAndErrors": (
        "tests.infra.unit.deps.test_main",
        "TestMainHelpAndErrors",
    ),
    "TestMainInventory": ("tests.infra.unit.validate.main_tests", "TestMainInventory"),
    "TestMainModuleImport": (
        "tests.infra.unit.deps.test_main_dispatch",
        "TestMainModuleImport",
    ),
    "TestMainReturnValues": ("tests.infra.unit.deps.test_main", "TestMainReturnValues"),
    "TestMainRouting": ("tests.infra.unit.docs.main_entry_tests", "TestMainRouting"),
    "TestMainScan": ("tests.infra.unit.validate.main_tests", "TestMainScan"),
    "TestMainSubcommandDispatch": (
        "tests.infra.unit.deps.test_main_dispatch",
        "TestMainSubcommandDispatch",
    ),
    "TestMainSysArgvModification": (
        "tests.infra.unit.deps.test_main_dispatch",
        "TestMainSysArgvModification",
    ),
    "TestMainWithFlags": (
        "tests.infra.unit.docs.main_entry_tests",
        "TestMainWithFlags",
    ),
    "TestMaintenanceMainEnforcer": (
        "tests.infra.unit.test_infra_maintenance_main",
        "TestMaintenanceMainEnforcer",
    ),
    "TestMaintenanceMainSuccess": (
        "tests.infra.unit.test_infra_maintenance_main",
        "TestMaintenanceMainSuccess",
    ),
    "TestMarkdownReportEmptyGates": (
        "tests.infra.unit.check.extended_error_reporting_tests",
        "TestMarkdownReportEmptyGates",
    ),
    "TestMarkdownReportSkipsEmptyGates": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestMarkdownReportSkipsEmptyGates",
    ),
    "TestMarkdownReportWithErrors": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestMarkdownReportWithErrors",
    ),
    "TestMaybeWriteTodo": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestMaybeWriteTodo",
    ),
    "TestMergeChildExports": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestMergeChildExports",
    ),
    "TestMigratorDryRun": (
        "tests.infra.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorDryRun",
    ),
    "TestMigratorEdgeCases": (
        "tests.infra.unit.test_infra_workspace_migrator_internal",
        "TestMigratorEdgeCases",
    ),
    "TestMigratorFlextCore": (
        "tests.infra.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorFlextCore",
    ),
    "TestMigratorInternalMakefile": (
        "tests.infra.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalMakefile",
    ),
    "TestMigratorInternalPyproject": (
        "tests.infra.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalPyproject",
    ),
    "TestMigratorPoetryDeps": (
        "tests.infra.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorPoetryDeps",
    ),
    "TestMigratorReadFailures": (
        "tests.infra.unit.test_infra_workspace_migrator_errors",
        "TestMigratorReadFailures",
    ),
    "TestMigratorWriteFailures": (
        "tests.infra.unit.test_infra_workspace_migrator_errors",
        "TestMigratorWriteFailures",
    ),
    "TestModernizerEdgeCases": (
        "tests.infra.unit.deps.test_modernizer_main_extra",
        "TestModernizerEdgeCases",
    ),
    "TestModernizerRunAndMain": (
        "tests.infra.unit.deps.test_modernizer_main",
        "TestModernizerRunAndMain",
    ),
    "TestModernizerUncoveredLines": (
        "tests.infra.unit.deps.test_modernizer_main_extra",
        "TestModernizerUncoveredLines",
    ),
    "TestModuleAndTypingsFlow": (
        "tests.infra.unit.deps.test_detection_typings_flow",
        "TestModuleAndTypingsFlow",
    ),
    "TestModuleLevelWrappers": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "TestModuleLevelWrappers",
    ),
    "TestMroFacadeMethods": (
        "tests.infra.unit.io.test_infra_output_edge_cases",
        "TestMroFacadeMethods",
    ),
    "TestMypyEmptyLinesInOutput": (
        "tests.infra.unit.check.extended_error_reporting_tests",
        "TestMypyEmptyLinesInOutput",
    ),
    "TestOrchestratorBasic": (
        "tests.infra.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorBasic",
    ),
    "TestOrchestratorFailures": (
        "tests.infra.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorFailures",
    ),
    "TestOrchestratorGateNormalization": (
        "tests.infra.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorGateNormalization",
    ),
    "TestOwnerFromRemoteUrl": (
        "tests.infra.unit.deps.test_internal_sync_validation",
        "TestOwnerFromRemoteUrl",
    ),
    "TestParseGitmodules": (
        "tests.infra.unit.deps.test_internal_sync_discovery",
        "TestParseGitmodules",
    ),
    "TestParseRepoMap": (
        "tests.infra.unit.deps.test_internal_sync_discovery",
        "TestParseRepoMap",
    ),
    "TestParseViolationInvalid": (
        "tests.infra.unit.codegen.census_tests",
        "TestParseViolationInvalid",
    ),
    "TestParseViolationValid": (
        "tests.infra.unit.codegen.census_tests",
        "TestParseViolationValid",
    ),
    "TestParser": ("tests.infra.unit.deps.test_modernizer_workspace", "TestParser"),
    "TestParsingModuleAst": (
        "tests.infra.unit._utilities.test_parsing",
        "TestParsingModuleAst",
    ),
    "TestParsingModuleCst": (
        "tests.infra.unit._utilities.test_parsing",
        "TestParsingModuleCst",
    ),
    "TestPathDepPathsPep621": (
        "tests.infra.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPep621",
    ),
    "TestPathDepPathsPoetry": (
        "tests.infra.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPoetry",
    ),
    "TestPathSyncEdgeCases": (
        "tests.infra.unit.deps.test_path_sync_init",
        "TestPathSyncEdgeCases",
    ),
    "TestPhaseBuild": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseBuild",
    ),
    "TestPhasePublish": (
        "tests.infra.unit.release.orchestrator_publish_tests",
        "TestPhasePublish",
    ),
    "TestPhaseValidate": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseValidate",
    ),
    "TestPhaseVersion": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseVersion",
    ),
    "TestPreviousTag": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestPreviousTag",
    ),
    "TestProcessDirectory": (
        "tests.infra.unit.codegen.lazy_init_process_tests",
        "TestProcessDirectory",
    ),
    "TestProcessFileReadError": (
        "tests.infra.unit.check.extended_config_fixer_errors_tests",
        "TestProcessFileReadError",
    ),
    "TestProjectResultProperties": (
        "tests.infra.unit.check.extended_models_tests",
        "TestProjectResultProperties",
    ),
    "TestPushRelease": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestPushRelease",
    ),
    "TestPytestDiagExtractorCore": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagExtractorCore",
    ),
    "TestPytestDiagLogParsing": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagLogParsing",
    ),
    "TestPytestDiagParseXml": (
        "tests.infra.unit.validate.pytest_diag",
        "TestPytestDiagParseXml",
    ),
    "TestReadDoc": ("tests.infra.unit.deps.test_modernizer_workspace", "TestReadDoc"),
    "TestReadExistingDocstring": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestReadExistingDocstring",
    ),
    "TestReadRequiredMinor": (
        "tests.infra.unit.test_infra_maintenance_python_version",
        "TestReadRequiredMinor",
    ),
    "TestReleaseInit": (
        "tests.infra.unit.release.release_init_tests",
        "TestReleaseInit",
    ),
    "TestReleaseMainFlow": (
        "tests.infra.unit.release.flow_tests",
        "TestReleaseMainFlow",
    ),
    "TestReleaseMainParsing": (
        "tests.infra.unit.release.main_tests",
        "TestReleaseMainParsing",
    ),
    "TestReleaseMainTagResolution": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestReleaseMainTagResolution",
    ),
    "TestReleaseMainVersionResolution": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestReleaseMainVersionResolution",
    ),
    "TestReleaseOrchestratorExecute": (
        "tests.infra.unit.release.orchestrator_tests",
        "TestReleaseOrchestratorExecute",
    ),
    "TestRemovedCompatibilityMethods": (
        "tests.infra.unit.test_infra_git",
        "TestRemovedCompatibilityMethods",
    ),
    "TestResolveAliases": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestResolveAliases",
    ),
    "TestResolveRef": (
        "tests.infra.unit.deps.test_internal_sync_resolve",
        "TestResolveRef",
    ),
    "TestResolveVersionInteractive": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestResolveVersionInteractive",
    ),
    "TestRewriteDepPaths": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "TestRewriteDepPaths",
    ),
    "TestRewritePep621": (
        "tests.infra.unit.deps.test_path_sync_rewrite_pep621",
        "TestRewritePep621",
    ),
    "TestRewritePoetry": (
        "tests.infra.unit.deps.test_path_sync_rewrite_poetry",
        "TestRewritePoetry",
    ),
    "TestRuffFormatDuplicateFiles": (
        "tests.infra.unit.check.extended_error_reporting_tests",
        "TestRuffFormatDuplicateFiles",
    ),
    "TestRunAudit": ("tests.infra.unit.docs.main_tests", "TestRunAudit"),
    "TestRunBandit": (
        "tests.infra.unit.check.extended_runners_extra_tests",
        "TestRunBandit",
    ),
    "TestRunBuild": ("tests.infra.unit.docs.main_commands_tests", "TestRunBuild"),
    "TestRunCLIExtended": (
        "tests.infra.unit.check.extended_cli_entry_tests",
        "TestRunCLIExtended",
    ),
    "TestRunCommand": (
        "tests.infra.unit.check.extended_runners_ruff_tests",
        "TestRunCommand",
    ),
    "TestRunDeptry": ("tests.infra.unit.deps.test_detection_deptry", "TestRunDeptry"),
    "TestRunDetect": ("tests.infra.unit.test_infra_workspace_main", "TestRunDetect"),
    "TestRunFix": ("tests.infra.unit.docs.main_tests", "TestRunFix"),
    "TestRunGenerate": ("tests.infra.unit.docs.main_commands_tests", "TestRunGenerate"),
    "TestRunGo": ("tests.infra.unit.check.extended_runners_go_tests", "TestRunGo"),
    "TestRunLint": ("tests.infra.unit.github.main_tests", "TestRunLint"),
    "TestRunMake": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestRunMake",
    ),
    "TestRunMarkdown": (
        "tests.infra.unit.check.extended_runners_extra_tests",
        "TestRunMarkdown",
    ),
    "TestRunMigrate": ("tests.infra.unit.test_infra_workspace_main", "TestRunMigrate"),
    "TestRunMypy": ("tests.infra.unit.check.extended_runners_tests", "TestRunMypy"),
    "TestRunMypyStubHints": (
        "tests.infra.unit.deps.test_detection_typings",
        "TestRunMypyStubHints",
    ),
    "TestRunOrchestrate": (
        "tests.infra.unit.test_infra_workspace_main",
        "TestRunOrchestrate",
    ),
    "TestRunPipCheck": (
        "tests.infra.unit.deps.test_detection_pip_check",
        "TestRunPipCheck",
    ),
    "TestRunPr": ("tests.infra.unit.github.main_tests", "TestRunPr"),
    "TestRunPrWorkspace": (
        "tests.infra.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ),
    "TestRunProjectsBehavior": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "TestRunProjectsBehavior",
    ),
    "TestRunProjectsReports": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "TestRunProjectsReports",
    ),
    "TestRunProjectsValidation": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "TestRunProjectsValidation",
    ),
    "TestRunPyrefly": (
        "tests.infra.unit.check.extended_runners_tests",
        "TestRunPyrefly",
    ),
    "TestRunPyright": (
        "tests.infra.unit.check.extended_runners_extra_tests",
        "TestRunPyright",
    ),
    "TestRunRuffFix": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestRunRuffFix",
    ),
    "TestRunRuffFormat": (
        "tests.infra.unit.check.extended_runners_ruff_tests",
        "TestRunRuffFormat",
    ),
    "TestRunRuffLint": (
        "tests.infra.unit.check.extended_runners_ruff_tests",
        "TestRunRuffLint",
    ),
    "TestRunSingleProject": (
        "tests.infra.unit.check.extended_run_projects_tests",
        "TestRunSingleProject",
    ),
    "TestRunSync": ("tests.infra.unit.test_infra_workspace_main", "TestRunSync"),
    "TestRunValidate": ("tests.infra.unit.docs.main_commands_tests", "TestRunValidate"),
    "TestRunWorkflows": ("tests.infra.unit.github.main_tests", "TestRunWorkflows"),
    "TestSafeLoadYaml": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSafeLoadYaml",
    ),
    "TestSafetyCheckpoint": (
        "tests.infra.unit._utilities.test_safety",
        "TestSafetyCheckpoint",
    ),
    "TestSafetyRollback": (
        "tests.infra.unit._utilities.test_safety",
        "TestSafetyRollback",
    ),
    "TestSafetyWorkspaceValidation": (
        "tests.infra.unit._utilities.test_safety",
        "TestSafetyWorkspaceValidation",
    ),
    "TestScaffoldProjectCreatesSrcModules": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesSrcModules",
    ),
    "TestScaffoldProjectCreatesTestsModules": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesTestsModules",
    ),
    "TestScaffoldProjectIdempotency": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectIdempotency",
    ),
    "TestScaffoldProjectNoop": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectNoop",
    ),
    "TestScanAstPublicDefs": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestScanAstPublicDefs",
    ),
    "TestScanFileBatch": (
        "tests.infra.unit._utilities.test_scanning",
        "TestScanFileBatch",
    ),
    "TestScanModels": ("tests.infra.unit._utilities.test_scanning", "TestScanModels"),
    "TestScannerCore": ("tests.infra.unit.validate.scanner_tests", "TestScannerCore"),
    "TestScannerHelpers": (
        "tests.infra.unit.validate.scanner_tests",
        "TestScannerHelpers",
    ),
    "TestScannerMultiFile": (
        "tests.infra.unit.validate.scanner_tests",
        "TestScannerMultiFile",
    ),
    "TestSelectedProjectNames": (
        "tests.infra.unit.docs.shared_iter_tests",
        "TestSelectedProjectNames",
    ),
    "TestShouldBubbleUp": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestShouldBubbleUp",
    ),
    "TestShouldUseColor": (
        "tests.infra.unit.io.test_infra_terminal_detection",
        "TestShouldUseColor",
    ),
    "TestShouldUseUnicode": (
        "tests.infra.unit.io.test_infra_terminal_detection",
        "TestShouldUseUnicode",
    ),
    "TestSkillValidatorAstGrepCount": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorAstGrepCount",
    ),
    "TestSkillValidatorCore": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorCore",
    ),
    "TestSkillValidatorRenderTemplate": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestSkillValidatorRenderTemplate",
    ),
    "TestStringList": (
        "tests.infra.unit.validate.skill_validator_tests",
        "TestStringList",
    ),
    "TestStubChainAnalyze": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainAnalyze",
    ),
    "TestStubChainCore": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainCore",
    ),
    "TestStubChainDiscoverProjects": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainDiscoverProjects",
    ),
    "TestStubChainIsInternal": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainIsInternal",
    ),
    "TestStubChainStubExists": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainStubExists",
    ),
    "TestStubChainValidate": (
        "tests.infra.unit.validate.stub_chain_tests",
        "TestStubChainValidate",
    ),
    "TestSubcommandMapping": (
        "tests.infra.unit.deps.test_main",
        "TestSubcommandMapping",
    ),
    "TestSync": ("tests.infra.unit.deps.test_internal_sync_sync", "TestSync"),
    "TestSyncMethodEdgeCases": (
        "tests.infra.unit.deps.test_internal_sync_sync_edge",
        "TestSyncMethodEdgeCases",
    ),
    "TestSyncMethodEdgeCasesMore": (
        "tests.infra.unit.deps.test_internal_sync_sync_edge_more",
        "TestSyncMethodEdgeCasesMore",
    ),
    "TestSyncOne": ("tests.infra.unit.deps.test_extra_paths_manager", "TestSyncOne"),
    "TestSynthesizedRepoMap": (
        "tests.infra.unit.deps.test_internal_sync_resolve",
        "TestSynthesizedRepoMap",
    ),
    "TestToInfraValue": (
        "tests.infra.unit.deps.test_detection_models",
        "TestToInfraValue",
    ),
    "TestUpdateChangelog": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestUpdateChangelog",
    ),
    "TestValidateCore": ("tests.infra.unit.docs.validator_tests", "TestValidateCore"),
    "TestValidateGitRefEdgeCases": (
        "tests.infra.unit.deps.test_internal_sync_validation",
        "TestValidateGitRefEdgeCases",
    ),
    "TestValidateReport": (
        "tests.infra.unit.docs.validator_tests",
        "TestValidateReport",
    ),
    "TestValidateScope": (
        "tests.infra.unit.docs.validator_internals_tests",
        "TestValidateScope",
    ),
    "TestVersionFiles": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestVersionFiles",
    ),
    "TestViolationPattern": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestViolationPattern",
    ),
    "TestWorkspaceCheckCLI": (
        "tests.infra.unit.check.extended_cli_entry_tests",
        "TestWorkspaceCheckCLI",
    ),
    "TestWorkspaceCheckerBuildGateResult": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerBuildGateResult",
    ),
    "TestWorkspaceCheckerCollectMarkdownFiles": (
        "tests.infra.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerCollectMarkdownFiles",
    ),
    "TestWorkspaceCheckerDirsWithPy": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerDirsWithPy",
    ),
    "TestWorkspaceCheckerErrorSummary": (
        "tests.infra.unit.check.extended_models_tests",
        "TestWorkspaceCheckerErrorSummary",
    ),
    "TestWorkspaceCheckerExecute": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExecute",
    ),
    "TestWorkspaceCheckerExistingCheckDirs": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExistingCheckDirs",
    ),
    "TestWorkspaceCheckerInitOSError": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitOSError",
    ),
    "TestWorkspaceCheckerInitialization": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitialization",
    ),
    "TestWorkspaceCheckerMarkdownReport": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReport",
    ),
    "TestWorkspaceCheckerMarkdownReportEdgeCases": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReportEdgeCases",
    ),
    "TestWorkspaceCheckerParseGateCSV": (
        "tests.infra.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerParseGateCSV",
    ),
    "TestWorkspaceCheckerResolveGates": (
        "tests.infra.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerResolveGates",
    ),
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": (
        "tests.infra.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    ),
    "TestWorkspaceCheckerRunBandit": (
        "tests.infra.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunBandit",
    ),
    "TestWorkspaceCheckerRunCommand": (
        "tests.infra.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunCommand",
    ),
    "TestWorkspaceCheckerRunGo": (
        "tests.infra.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunGo",
    ),
    "TestWorkspaceCheckerRunMarkdown": (
        "tests.infra.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunMarkdown",
    ),
    "TestWorkspaceCheckerRunMypy": (
        "tests.infra.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunMypy",
    ),
    "TestWorkspaceCheckerRunPyright": (
        "tests.infra.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunPyright",
    ),
    "TestWorkspaceCheckerSARIFReport": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReport",
    ),
    "TestWorkspaceCheckerSARIFReportEdgeCases": (
        "tests.infra.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReportEdgeCases",
    ),
    "TestWorkspaceRoot": (
        "tests.infra.unit.test_infra_maintenance_python_version",
        "TestWorkspaceRoot",
    ),
    "TestWorkspaceRootFromEnv": (
        "tests.infra.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromEnv",
    ),
    "TestWorkspaceRootFromParents": (
        "tests.infra.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromParents",
    ),
    "TestWriteJson": ("tests.infra.unit.docs.shared_write_tests", "TestWriteJson"),
    "TestWriteMarkdown": (
        "tests.infra.unit.docs.shared_write_tests",
        "TestWriteMarkdown",
    ),
    "_utilities": ("tests.infra.unit._utilities", ""),
    "auditor": ("tests.infra.unit.docs.auditor_tests", "auditor"),
    "basemk": ("tests.infra.unit.basemk", ""),
    "builder": ("tests.infra.unit.docs.builder_tests", "builder"),
    "census": ("tests.infra.unit.codegen.census_tests", "census"),
    "check": ("tests.infra.unit.check", ""),
    "codegen": ("tests.infra.unit.codegen", ""),
    "container": ("tests.infra.unit.container", ""),
    "create_check_project_iter_stub": (
        "tests.infra.unit.check._shared_fixtures",
        "create_check_project_iter_stub",
    ),
    "create_check_project_stub": (
        "tests.infra.unit.check._shared_fixtures",
        "create_check_project_stub",
    ),
    "create_checker_project": (
        "tests.infra.unit.check._shared_fixtures",
        "create_checker_project",
    ),
    "create_fake_run_projects": (
        "tests.infra.unit.check._shared_fixtures",
        "create_fake_run_projects",
    ),
    "create_fake_run_raw": (
        "tests.infra.unit.check._shared_fixtures",
        "create_fake_run_raw",
    ),
    "create_gate_execution": (
        "tests.infra.unit.check._shared_fixtures",
        "create_gate_execution",
    ),
    "deps": ("tests.infra.unit.deps", ""),
    "detector": ("tests.infra.unit.test_infra_workspace_detector", "detector"),
    "discovery": ("tests.infra.unit.discovery", ""),
    "doc": ("tests.infra.unit.deps.test_modernizer_helpers", "doc"),
    "docs": ("tests.infra.unit.docs", ""),
    "extract_dep_name": (
        "tests.infra.unit.deps.test_path_sync_helpers",
        "extract_dep_name",
    ),
    "fixer": ("tests.infra.unit.docs.fixer_internals_tests", "fixer"),
    "gen": ("tests.infra.unit.docs.generator_internals_tests", "gen"),
    "git_repo": ("tests.infra.unit.test_infra_git", "git_repo"),
    "github": ("tests.infra.unit.github", ""),
    "io": ("tests.infra.unit.io", ""),
    "is_external": ("tests.infra.unit.docs.auditor_tests", "is_external"),
    "main": ("tests.infra.unit.github.main_tests", "main"),
    "make_cmd_result": ("tests.infra.unit.check._stubs", "make_cmd_result"),
    "make_gate_exec": ("tests.infra.unit.check._stubs", "make_gate_exec"),
    "make_issue": ("tests.infra.unit.check._stubs", "make_issue"),
    "make_project": ("tests.infra.unit.check._stubs", "make_project"),
    "normalize_link": ("tests.infra.unit.docs.auditor_tests", "normalize_link"),
    "orchestrator": (
        "tests.infra.unit.test_infra_workspace_orchestrator",
        "orchestrator",
    ),
    "patch_gate_run": ("tests.infra.unit.check._shared_fixtures", "patch_gate_run"),
    "patch_python_dir_detection": (
        "tests.infra.unit.check._shared_fixtures",
        "patch_python_dir_detection",
    ),
    "pyright_content": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "pyright_content",
    ),
    "refactor": ("tests.infra.unit.refactor", ""),
    "release": ("tests.infra.unit.release", ""),
    "rewrite_dep_paths": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "rewrite_dep_paths",
    ),
    "run_command_failure_check": (
        "tests.infra.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ),
    "run_lint": ("tests.infra.unit.github.main_tests", "run_lint"),
    "run_pr": ("tests.infra.unit.github.main_tests", "run_pr"),
    "run_pr_workspace": ("tests.infra.unit.github.main_tests", "run_pr_workspace"),
    "run_workflows": ("tests.infra.unit.github.main_tests", "run_workflows"),
    "runner": ("tests.infra.unit.test_infra_subprocess_core", "runner"),
    "service": ("tests.infra.unit.test_infra_versioning", "service"),
    "should_skip_target": ("tests.infra.unit.docs.auditor_tests", "should_skip_target"),
    "svc": ("tests.infra.unit.test_infra_workspace_sync", "svc"),
    "test_all_three_capabilities_in_one_pass": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_all_three_capabilities_in_one_pass",
    ),
    "test_array": ("tests.infra.unit.deps.test_modernizer_helpers", "test_array"),
    "test_as_string_list": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_as_string_list",
    ),
    "test_as_string_list_toml_item": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_as_string_list_toml_item",
    ),
    "test_atomic_write_fail": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_atomic_write_fail",
    ),
    "test_atomic_write_ok": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_atomic_write_ok",
    ),
    "test_basemk_build_config_with_none": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_build_config_with_none",
    ),
    "test_basemk_build_config_with_project_name": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_build_config_with_project_name",
    ),
    "test_basemk_cli_generate_to_file": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_file",
    ),
    "test_basemk_cli_generate_to_stdout": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_stdout",
    ),
    "test_basemk_engine_execute_calls_render_all": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_engine_execute_calls_render_all",
    ),
    "test_basemk_engine_render_all_handles_template_error": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_engine_render_all_handles_template_error",
    ),
    "test_basemk_engine_render_all_returns_string": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_engine_render_all_returns_string",
    ),
    "test_basemk_engine_render_all_with_valid_config": (
        "tests.infra.unit.basemk.test_engine",
        "test_basemk_engine_render_all_with_valid_config",
    ),
    "test_basemk_main_ensures_structlog_configured": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_ensures_structlog_configured",
    ),
    "test_basemk_main_output_to_stdout": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_output_to_stdout",
    ),
    "test_basemk_main_with_generate_command": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_generate_command",
    ),
    "test_basemk_main_with_generation_failure": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_generation_failure",
    ),
    "test_basemk_main_with_help": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_help",
    ),
    "test_basemk_main_with_invalid_command": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_invalid_command",
    ),
    "test_basemk_main_with_no_command": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_no_command",
    ),
    "test_basemk_main_with_none_argv": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_none_argv",
    ),
    "test_basemk_main_with_output_file": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_output_file",
    ),
    "test_basemk_main_with_project_name": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_project_name",
    ),
    "test_basemk_main_with_write_failure": (
        "tests.infra.unit.basemk.test_main",
        "test_basemk_main_with_write_failure",
    ),
    "test_build_impact_map_extracts_rename_entries": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_rename_entries",
    ),
    "test_build_impact_map_extracts_signature_entries": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_signature_entries",
    ),
    "test_bump_version_invalid": (
        "tests.infra.unit.test_infra_versioning",
        "test_bump_version_invalid",
    ),
    "test_bump_version_result_type": (
        "tests.infra.unit.test_infra_versioning",
        "test_bump_version_result_type",
    ),
    "test_bump_version_valid": (
        "tests.infra.unit.test_infra_versioning",
        "test_bump_version_valid",
    ),
    "test_canonical_dev_dependencies": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_canonical_dev_dependencies",
    ),
    "test_capture_cases": (
        "tests.infra.unit.test_infra_subprocess_core",
        "test_capture_cases",
    ),
    "test_check_main_executes_real_cli": (
        "tests.infra.unit.check.main_tests",
        "test_check_main_executes_real_cli",
    ),
    "test_class_reconstructor_reorders_each_contiguous_method_block": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_each_contiguous_method_block",
    ),
    "test_class_reconstructor_reorders_methods_by_config": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_methods_by_config",
    ),
    "test_class_reconstructor_skips_interleaved_non_method_members": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_skips_interleaved_non_method_members",
    ),
    "test_cli_result_by_project_root": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_cli_result_by_project_root",
    ),
    "test_codegen_dir_returns_all_exports": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_dir_returns_all_exports",
    ),
    "test_codegen_getattr_raises_attribute_error": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_getattr_raises_attribute_error",
    ),
    "test_codegen_init_getattr_raises_attribute_error": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "test_codegen_init_getattr_raises_attribute_error",
    ),
    "test_codegen_lazy_imports_work": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_lazy_imports_work",
    ),
    "test_codegen_pipeline_end_to_end": (
        "tests.infra.unit.codegen.pipeline_tests",
        "test_codegen_pipeline_end_to_end",
    ),
    "test_consolidate_groups_phase_apply_removes_old_groups": (
        "tests.infra.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_removes_old_groups",
    ),
    "test_consolidate_groups_phase_apply_with_empty_poetry_group": (
        "tests.infra.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    ),
    "test_converts_multiple_aliases": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_multiple_aliases",
    ),
    "test_converts_typealias_to_pep695": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_typealias_to_pep695",
    ),
    "test_current_workspace_version": (
        "tests.infra.unit.test_infra_versioning",
        "test_current_workspace_version",
    ),
    "test_dedupe_specs": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_dedupe_specs",
    ),
    "test_dep_name": ("tests.infra.unit.deps.test_modernizer_helpers", "test_dep_name"),
    "test_detect_mode_with_nonexistent_path": (
        "tests.infra.unit.deps.test_path_sync_init",
        "test_detect_mode_with_nonexistent_path",
    ),
    "test_detect_mode_with_path_object": (
        "tests.infra.unit.deps.test_path_sync_init",
        "test_detect_mode_with_path_object",
    ),
    "test_detects_attribute_base_class": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_attribute_base_class",
    ),
    "test_detects_basemodel_in_non_model_file": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_basemodel_in_non_model_file",
    ),
    "test_detects_missing_local_composition_base": (
        "tests.infra.unit.refactor.test_infra_refactor_mro_completeness",
        "test_detects_missing_local_composition_base",
    ),
    "test_detects_multiple_models": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_multiple_models",
    ),
    "test_detects_only_wrong_alias_in_mixed_import": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_only_wrong_alias_in_mixed_import",
    ),
    "test_detects_same_project_submodule_alias_import": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_same_project_submodule_alias_import",
    ),
    "test_detects_wrong_source_m_import": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_m_import",
    ),
    "test_detects_wrong_source_u_import": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_u_import",
    ),
    "test_discover_projects_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_discover_projects_wrapper",
    ),
    "test_engine_always_enables_class_nesting_file_rule": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_engine_always_enables_class_nesting_file_rule",
    ),
    "test_ensure_future_annotations_after_docstring": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_after_docstring",
    ),
    "test_ensure_future_annotations_moves_existing_import_to_top": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_moves_existing_import_to_top",
    ),
    "test_ensure_pyrefly_config_phase_apply_errors": (
        "tests.infra.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_errors",
    ),
    "test_ensure_pyrefly_config_phase_apply_ignore_errors": (
        "tests.infra.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    ),
    "test_ensure_pyrefly_config_phase_apply_python_version": (
        "tests.infra.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_python_version",
    ),
    "test_ensure_pyrefly_config_phase_apply_search_path": (
        "tests.infra.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_search_path",
    ),
    "test_ensure_pytest_config_phase_apply_markers": (
        "tests.infra.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_markers",
    ),
    "test_ensure_pytest_config_phase_apply_minversion": (
        "tests.infra.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_minversion",
    ),
    "test_ensure_pytest_config_phase_apply_python_classes": (
        "tests.infra.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_python_classes",
    ),
    "test_ensure_table": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_ensure_table",
    ),
    "test_expected_dependency_bases_by_family_preserves_internal_dependency_order": (
        "tests.infra.unit.refactor.test_infra_refactor_project_classifier",
        "test_expected_dependency_bases_by_family_preserves_internal_dependency_order",
    ),
    "test_extract_dep_name": (
        "tests.infra.unit.deps.test_path_sync_helpers",
        "test_extract_dep_name",
    ),
    "test_extract_requirement_name": (
        "tests.infra.unit.deps.test_path_sync_helpers",
        "test_extract_requirement_name",
    ),
    "test_files_modified_tracks_affected_files": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_files_modified_tracks_affected_files",
    ),
    "test_fix_pyrefly_config_main_executes_real_cli_help": (
        "tests.infra.unit.check.fix_pyrefly_config_tests",
        "test_fix_pyrefly_config_main_executes_real_cli_help",
    ),
    "test_flexcore_excluded_from_run": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_flexcore_excluded_from_run",
    ),
    "test_flext_infra_pyproject_modernizer_find_pyproject_files": (
        "tests.infra.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    ),
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml": (
        "tests.infra.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    ),
    "test_generator_execute_returns_generated_content": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_execute_returns_generated_content",
    ),
    "test_generator_fails_for_invalid_make_syntax": (
        "tests.infra.unit.basemk.test_engine",
        "test_generator_fails_for_invalid_make_syntax",
    ),
    "test_generator_generate_propagates_render_failure": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_generate_propagates_render_failure",
    ),
    "test_generator_generate_with_basemk_config_object": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_generate_with_basemk_config_object",
    ),
    "test_generator_generate_with_dict_config": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_generate_with_dict_config",
    ),
    "test_generator_generate_with_invalid_dict_config": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_generate_with_invalid_dict_config",
    ),
    "test_generator_generate_with_none_config_uses_default": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_generate_with_none_config_uses_default",
    ),
    "test_generator_initializes_with_custom_engine": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_initializes_with_custom_engine",
    ),
    "test_generator_initializes_with_default_engine": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_initializes_with_default_engine",
    ),
    "test_generator_normalize_config_with_basemk_config": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_basemk_config",
    ),
    "test_generator_normalize_config_with_dict": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_dict",
    ),
    "test_generator_normalize_config_with_invalid_dict": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_invalid_dict",
    ),
    "test_generator_normalize_config_with_none": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_none",
    ),
    "test_generator_renders_with_config_override": (
        "tests.infra.unit.basemk.test_engine",
        "test_generator_renders_with_config_override",
    ),
    "test_generator_validate_generated_output_handles_oserror": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_validate_generated_output_handles_oserror",
    ),
    "test_generator_write_creates_parent_directories": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_write_creates_parent_directories",
    ),
    "test_generator_write_fails_without_output_or_stream": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_write_fails_without_output_or_stream",
    ),
    "test_generator_write_handles_file_permission_error": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_write_handles_file_permission_error",
    ),
    "test_generator_write_saves_output_file": (
        "tests.infra.unit.basemk.test_engine",
        "test_generator_write_saves_output_file",
    ),
    "test_generator_write_to_file": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_write_to_file",
    ),
    "test_generator_write_to_stream": (
        "tests.infra.unit.basemk.test_generator",
        "test_generator_write_to_stream",
    ),
    "test_generator_write_to_stream_handles_oserror": (
        "tests.infra.unit.basemk.test_generator_edge_cases",
        "test_generator_write_to_stream_handles_oserror",
    ),
    "test_get_current_typings_from_pyproject_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_get_current_typings_from_pyproject_wrapper",
    ),
    "test_get_required_typings_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_get_required_typings_wrapper",
    ),
    "test_gitignore_entry_scenarios": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_gitignore_entry_scenarios",
    ),
    "test_gitignore_sync_failure": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_gitignore_sync_failure",
    ),
    "test_gitignore_write_failure": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_gitignore_write_failure",
    ),
    "test_helpers_alias_is_reachable_helpers": (
        "tests.infra.unit.deps.test_path_sync_helpers",
        "test_helpers_alias_is_reachable_helpers",
    ),
    "test_helpers_alias_is_reachable_project_obj": (
        "tests.infra.unit.deps.test_path_sync_main_project_obj",
        "test_helpers_alias_is_reachable_project_obj",
    ),
    "test_import_alias_detector_skips_facade_and_subclass_files": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_facade_and_subclass_files",
    ),
    "test_import_alias_detector_skips_nested_private_and_as_renames": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_nested_private_and_as_renames",
    ),
    "test_import_alias_detector_skips_private_and_class_imports": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_private_and_class_imports",
    ),
    "test_import_modernizer_adds_c_when_existing_c_is_aliased": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    ),
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    ),
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    ),
    "test_import_modernizer_partial_import_keeps_unmapped_symbols": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    ),
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    ),
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    ),
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    ),
    "test_import_modernizer_updates_aliased_symbol_usage": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_updates_aliased_symbol_usage",
    ),
    "test_in_context_typevar_not_flagged": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_in_context_typevar_not_flagged",
    ),
    "test_inject_comments_phase_apply_banner": (
        "tests.infra.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_banner",
    ),
    "test_inject_comments_phase_apply_broken_group_section": (
        "tests.infra.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_broken_group_section",
    ),
    "test_inject_comments_phase_apply_markers": (
        "tests.infra.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_markers",
    ),
    "test_inject_comments_phase_apply_with_optional_dependencies_dev": (
        "tests.infra.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    ),
    "test_injects_t_import_when_needed": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_injects_t_import_when_needed",
    ),
    "test_lazy_import_rule_hoists_import_to_module_level": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_hoists_import_to_module_level",
    ),
    "test_lazy_import_rule_uses_fix_action_for_hoist": (
        "tests.infra.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_uses_fix_action_for_hoist",
    ),
    "test_legacy_import_bypass_collapses_to_primary_import": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_import_bypass_collapses_to_primary_import",
    ),
    "test_legacy_rule_uses_fix_action_remove_for_aliases": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_rule_uses_fix_action_remove_for_aliases",
    ),
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_function_is_inlined_as_alias": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_function_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_non_passthrough_is_not_inlined": (
        "tests.infra.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_non_passthrough_is_not_inlined",
    ),
    "test_main_all_groups_defined": (
        "tests.infra.unit.test_infra_main",
        "test_main_all_groups_defined",
    ),
    "test_main_analyze_violations_is_read_only": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_is_read_only",
    ),
    "test_main_analyze_violations_writes_json_report": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_writes_json_report",
    ),
    "test_main_discovery_failure": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_discovery_failure",
    ),
    "test_main_group_modules_are_valid": (
        "tests.infra.unit.test_infra_main",
        "test_main_group_modules_are_valid",
    ),
    "test_main_help_flag_returns_zero": (
        "tests.infra.unit.test_infra_main",
        "test_main_help_flag_returns_zero",
    ),
    "test_main_no_changes_needed": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_no_changes_needed",
    ),
    "test_main_project_invalid_toml": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_project_invalid_toml",
    ),
    "test_main_project_no_name": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_project_no_name",
    ),
    "test_main_project_non_string_name": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_project_non_string_name",
    ),
    "test_main_project_obj_not_dict_first_loop": (
        "tests.infra.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_first_loop",
    ),
    "test_main_project_obj_not_dict_second_loop": (
        "tests.infra.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_second_loop",
    ),
    "test_main_returns_error_when_no_args": (
        "tests.infra.unit.test_infra_main",
        "test_main_returns_error_when_no_args",
    ),
    "test_main_success_modes": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_main_success_modes",
    ),
    "test_main_sync_failure": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_main_sync_failure",
    ),
    "test_main_unknown_group_returns_error": (
        "tests.infra.unit.test_infra_main",
        "test_main_unknown_group_returns_error",
    ),
    "test_main_with_changes_and_dry_run": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_and_dry_run",
    ),
    "test_main_with_changes_no_dry_run": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_no_dry_run",
    ),
    "test_migrate_makefile_not_found_non_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_migrate_makefile_not_found_non_dry_run",
    ),
    "test_migrate_pyproject_flext_core_non_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_migrate_pyproject_flext_core_non_dry_run",
    ),
    "test_migrator_apply_updates_project_files": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_apply_updates_project_files",
    ),
    "test_migrator_discovery_failure": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_discovery_failure",
    ),
    "test_migrator_dry_run_reports_changes_without_writes": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_dry_run_reports_changes_without_writes",
    ),
    "test_migrator_execute_returns_failure": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_execute_returns_failure",
    ),
    "test_migrator_flext_core_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_dry_run",
    ),
    "test_migrator_flext_core_project_skipped": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_project_skipped",
    ),
    "test_migrator_gitignore_already_normalized_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_gitignore_already_normalized_dry_run",
    ),
    "test_migrator_handles_missing_pyproject_gracefully": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_handles_missing_pyproject_gracefully",
    ),
    "test_migrator_has_flext_core_dependency_in_poetry": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_in_poetry",
    ),
    "test_migrator_has_flext_core_dependency_poetry_deps_not_table": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_deps_not_table",
    ),
    "test_migrator_has_flext_core_dependency_poetry_table_missing": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_table_missing",
    ),
    "test_migrator_makefile_not_found_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_not_found_dry_run",
    ),
    "test_migrator_makefile_read_failure": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_read_failure",
    ),
    "test_migrator_no_changes_needed": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_no_changes_needed",
    ),
    "test_migrator_preserves_custom_makefile_content": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_preserves_custom_makefile_content",
    ),
    "test_migrator_pyproject_not_found_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_pyproject_not_found_dry_run",
    ),
    "test_migrator_workspace_root_not_exists": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_not_exists",
    ),
    "test_migrator_workspace_root_project_detection": (
        "tests.infra.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_project_detection",
    ),
    "test_mro_checker_keeps_external_attribute_base": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_checker_keeps_external_attribute_base",
    ),
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    ),
    "test_namespace_rewriter_keeps_contextual_alias_subset": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_keeps_contextual_alias_subset",
    ),
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_only_rewrites_runtime_alias_imports",
    ),
    "test_namespace_rewriter_skips_facade_and_subclass_files": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_facade_and_subclass_files",
    ),
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates",
    ),
    "test_no_duplicate_t_import_when_t_from_project_package": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_no_duplicate_t_import_when_t_from_project_package",
    ),
    "test_non_pydantic_class_not_flagged": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_non_pydantic_class_not_flagged",
    ),
    "test_noop_clean_module": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_noop_clean_module",
    ),
    "test_parse_semver_invalid": (
        "tests.infra.unit.test_infra_versioning",
        "test_parse_semver_invalid",
    ),
    "test_parse_semver_result_type": (
        "tests.infra.unit.test_infra_versioning",
        "test_parse_semver_result_type",
    ),
    "test_parse_semver_valid": (
        "tests.infra.unit.test_infra_versioning",
        "test_parse_semver_valid",
    ),
    "test_pattern_rule_converts_dict_annotations_to_mapping": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_converts_dict_annotations_to_mapping",
    ),
    "test_pattern_rule_keeps_dict_param_when_copy_used": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_copy_used",
    ),
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    ),
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    ),
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    ),
    "test_pattern_rule_removes_configured_redundant_casts": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_configured_redundant_casts",
    ),
    "test_pattern_rule_removes_nested_type_object_cast_chain": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_nested_type_object_cast_chain",
    ),
    "test_pattern_rule_skips_overload_signatures": (
        "tests.infra.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_skips_overload_signatures",
    ),
    "test_preserves_annotated_in_function_params": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_annotated_in_function_params",
    ),
    "test_preserves_non_matching_unions": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_non_matching_unions",
    ),
    "test_preserves_override_in_method": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_override_in_method",
    ),
    "test_preserves_protocol_and_runtime_checkable": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_protocol_and_runtime_checkable",
    ),
    "test_preserves_type_checking_import": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_type_checking_import",
    ),
    "test_preserves_typealias_import_when_class_level_usage_exists": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_typealias_import_when_class_level_usage_exists",
    ),
    "test_preserves_used_imports_when_import_precedes_usage": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_imports_when_import_precedes_usage",
    ),
    "test_preserves_used_typing_imports": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_typing_imports",
    ),
    "test_project_dev_groups": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups",
    ),
    "test_project_dev_groups_missing_sections": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups_missing_sections",
    ),
    "test_project_without_alias_facade_has_no_violation": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_project_without_alias_facade_has_no_violation",
    ),
    "test_project_without_src_returns_empty": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_project_without_src_returns_empty",
    ),
    "test_read_project_metadata_preserves_pep621_dependency_order": (
        "tests.infra.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_pep621_dependency_order",
    ),
    "test_read_project_metadata_preserves_poetry_dependency_order": (
        "tests.infra.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_poetry_dependency_order",
    ),
    "test_refactor_files_skips_non_python_inputs": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_refactor_files_skips_non_python_inputs",
    ),
    "test_refactor_project_integrates_safety_manager": (
        "tests.infra.unit.refactor.test_infra_refactor_safety",
        "test_refactor_project_integrates_safety_manager",
    ),
    "test_refactor_project_scans_tests_and_scripts_dirs": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_refactor_project_scans_tests_and_scripts_dirs",
    ),
    "test_release_tag_from_branch_invalid": (
        "tests.infra.unit.test_infra_versioning",
        "test_release_tag_from_branch_invalid",
    ),
    "test_release_tag_from_branch_result_type": (
        "tests.infra.unit.test_infra_versioning",
        "test_release_tag_from_branch_result_type",
    ),
    "test_release_tag_from_branch_valid": (
        "tests.infra.unit.test_infra_versioning",
        "test_release_tag_from_branch_valid",
    ),
    "test_removes_all_imports_when_none_used_import_first": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_imports_when_none_used_import_first",
    ),
    "test_removes_all_unused_typing_imports": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_unused_typing_imports",
    ),
    "test_removes_dead_typealias_import": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_dead_typealias_import",
    ),
    "test_removes_typealias_import_only_when_all_usages_converted": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_typealias_import_only_when_all_usages_converted",
    ),
    "test_removes_unused_preserves_used_when_import_precedes_usage": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_unused_preserves_used_when_import_precedes_usage",
    ),
    "test_render_all_generates_large_makefile": (
        "tests.infra.unit.basemk.test_engine",
        "test_render_all_generates_large_makefile",
    ),
    "test_render_all_has_no_scripts_path_references": (
        "tests.infra.unit.basemk.test_engine",
        "test_render_all_has_no_scripts_path_references",
    ),
    "test_replace_project_version": (
        "tests.infra.unit.test_infra_versioning",
        "test_replace_project_version",
    ),
    "test_replaces_container_union": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_container_union",
    ),
    "test_replaces_numeric_union": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_numeric_union",
    ),
    "test_replaces_primitives_union": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_primitives_union",
    ),
    "test_replaces_scalar_union": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_scalar_union",
    ),
    "test_resolve_gates_maps_type_alias": (
        "tests.infra.unit.check.cli_tests",
        "test_resolve_gates_maps_type_alias",
    ),
    "test_rewrite_dep_paths_dry_run": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_dry_run",
    ),
    "test_rewrite_dep_paths_read_failure": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_read_failure",
    ),
    "test_rewrite_dep_paths_with_internal_names": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_internal_names",
    ),
    "test_rewrite_dep_paths_with_no_deps": (
        "tests.infra.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_no_deps",
    ),
    "test_rewrite_pep621_invalid_path_dep_regex": (
        "tests.infra.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_invalid_path_dep_regex",
    ),
    "test_rewrite_pep621_no_project_table": (
        "tests.infra.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_no_project_table",
    ),
    "test_rewrite_pep621_non_string_item": (
        "tests.infra.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_non_string_item",
    ),
    "test_rewrite_poetry_no_poetry_table": (
        "tests.infra.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_poetry_table",
    ),
    "test_rewrite_poetry_no_tool_table": (
        "tests.infra.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_tool_table",
    ),
    "test_rewrite_poetry_with_non_dict_value": (
        "tests.infra.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_with_non_dict_value",
    ),
    "test_rewriter_adds_missing_base_and_formats": (
        "tests.infra.unit.refactor.test_infra_refactor_mro_completeness",
        "test_rewriter_adds_missing_base_and_formats",
    ),
    "test_rewriter_namespace_source_is_idempotent_with_ruff": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_namespace_source_is_idempotent_with_ruff",
    ),
    "test_rewriter_preserves_non_alias_symbols": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_preserves_non_alias_symbols",
    ),
    "test_rewriter_splits_mixed_imports_correctly": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_splits_mixed_imports_correctly",
    ),
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    ),
    "test_rule_dispatch_fails_on_unknown_rule_mapping": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_unknown_rule_mapping",
    ),
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    ),
    "test_rule_dispatch_prefers_fix_action_metadata": (
        "tests.infra.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_prefers_fix_action_metadata",
    ),
    "test_run_cases": ("tests.infra.unit.test_infra_subprocess_core", "test_run_cases"),
    "test_run_cli_run_returns_one_for_fail": (
        "tests.infra.unit.check.cli_tests",
        "test_run_cli_run_returns_one_for_fail",
    ),
    "test_run_cli_run_returns_two_for_error": (
        "tests.infra.unit.check.cli_tests",
        "test_run_cli_run_returns_two_for_error",
    ),
    "test_run_cli_run_returns_zero_for_pass": (
        "tests.infra.unit.check.cli_tests",
        "test_run_cli_run_returns_zero_for_pass",
    ),
    "test_run_cli_with_fail_fast_flag": (
        "tests.infra.unit.check.cli_tests",
        "test_run_cli_with_fail_fast_flag",
    ),
    "test_run_cli_with_multiple_projects": (
        "tests.infra.unit.check.cli_tests",
        "test_run_cli_with_multiple_projects",
    ),
    "test_run_deptry_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_run_deptry_wrapper",
    ),
    "test_run_mypy_stub_hints_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_run_mypy_stub_hints_wrapper",
    ),
    "test_run_pip_check_wrapper": (
        "tests.infra.unit.deps.test_detection_wrappers",
        "test_run_pip_check_wrapper",
    ),
    "test_run_raw_cases": (
        "tests.infra.unit.test_infra_subprocess_core",
        "test_run_raw_cases",
    ),
    "test_signature_propagation_removes_and_adds_keywords": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_removes_and_adds_keywords",
    ),
    "test_signature_propagation_renames_call_keyword": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_renames_call_keyword",
    ),
    "test_skips_definition_files": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_definition_files",
    ),
    "test_skips_facade_declaration_files": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_facade_declaration_files",
    ),
    "test_skips_import_as_rename": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_import_as_rename",
    ),
    "test_skips_init_file": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_init_file",
    ),
    "test_skips_models_directory": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_directory",
    ),
    "test_skips_models_file": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_file",
    ),
    "test_skips_non_alias_symbols": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_non_alias_symbols",
    ),
    "test_skips_non_facade_files": (
        "tests.infra.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_non_facade_files",
    ),
    "test_skips_private_candidate_classes": (
        "tests.infra.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_private_candidate_classes",
    ),
    "test_skips_private_class": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_private_class",
    ),
    "test_skips_protected_files": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_protected_files",
    ),
    "test_skips_r_alias_universal_exception": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_r_alias_universal_exception",
    ),
    "test_skips_same_project_private_submodule": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_private_submodule",
    ),
    "test_skips_same_project_submodule_class_import": (
        "tests.infra.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_submodule_class_import",
    ),
    "test_skips_settings_file": (
        "tests.infra.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_settings_file",
    ),
    "test_skips_union_with_none": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_union_with_none",
    ),
    "test_skips_when_candidate_is_already_in_facade_bases": (
        "tests.infra.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_when_candidate_is_already_in_facade_bases",
    ),
    "test_standalone_final_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_final_detected_as_fixable",
    ),
    "test_standalone_typealias_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_typealias_detected_as_fixable",
    ),
    "test_standalone_typevar_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_typevar_detected_as_fixable",
    ),
    "test_string_zero_return_value": (
        "tests.infra.unit.deps.test_main_dispatch",
        "test_string_zero_return_value",
    ),
    "test_symbol_propagation_keeps_alias_reference_when_asname_used": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    ),
    "test_symbol_propagation_renames_import_and_local_references": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_renames_import_and_local_references",
    ),
    "test_symbol_propagation_updates_mro_base_references": (
        "tests.infra.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_updates_mro_base_references",
    ),
    "test_sync_basemk_scenarios": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_sync_basemk_scenarios",
    ),
    "test_sync_error_scenarios": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_sync_error_scenarios",
    ),
    "test_sync_extra_paths_missing_root_pyproject": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_missing_root_pyproject",
    ),
    "test_sync_extra_paths_success_modes": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_success_modes",
    ),
    "test_sync_extra_paths_sync_failure": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_sync_failure",
    ),
    "test_sync_one_edge_cases": (
        "tests.infra.unit.deps.test_extra_paths_sync",
        "test_sync_one_edge_cases",
    ),
    "test_sync_root_validation": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_sync_root_validation",
    ),
    "test_sync_success_scenarios": (
        "tests.infra.unit.test_infra_workspace_sync",
        "test_sync_success_scenarios",
    ),
    "test_syntax_error_files_skipped": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_syntax_error_files_skipped",
    ),
    "test_target_path": (
        "tests.infra.unit.deps.test_path_sync_helpers",
        "test_target_path",
    ),
    "test_typealias_conversion_preserves_used_typing_siblings": (
        "tests.infra.unit.refactor.test_infra_refactor_typing_unifier",
        "test_typealias_conversion_preserves_used_typing_siblings",
    ),
    "test_unwrap_item": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_unwrap_item",
    ),
    "test_unwrap_item_toml_item": (
        "tests.infra.unit.deps.test_modernizer_helpers",
        "test_unwrap_item_toml_item",
    ),
    "test_violation_analysis_counts_massive_patterns": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analysis_counts_massive_patterns",
    ),
    "test_violation_analyzer_skips_non_utf8_files": (
        "tests.infra.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analyzer_skips_non_utf8_files",
    ),
    "test_workspace_check_main_returns_error_without_projects": (
        "tests.infra.unit.check.workspace_check_tests",
        "test_workspace_check_main_returns_error_without_projects",
    ),
    "test_workspace_cli_migrate_command": (
        "tests.infra.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_command",
    ),
    "test_workspace_cli_migrate_output_contains_summary": (
        "tests.infra.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_output_contains_summary",
    ),
    "test_workspace_migrator_error_handling_on_invalid_workspace": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_error_handling_on_invalid_workspace",
    ),
    "test_workspace_migrator_makefile_not_found_dry_run": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_not_found_dry_run",
    ),
    "test_workspace_migrator_makefile_read_error": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_read_error",
    ),
    "test_workspace_migrator_pyproject_write_error": (
        "tests.infra.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_pyproject_write_error",
    ),
    "test_workspace_root_doc_construction": (
        "tests.infra.unit.deps.test_modernizer_workspace",
        "test_workspace_root_doc_construction",
    ),
    "test_workspace_root_fallback": (
        "tests.infra.unit.deps.test_path_sync_main_more",
        "test_workspace_root_fallback",
    ),
    "v": ("tests.infra.unit.validate.basemk_validator_tests", "v"),
    "validate": ("tests.infra.unit.validate", ""),
    "validator": ("tests.infra.unit.docs.validator_internals_tests", "validator"),
    "workspace_root": ("tests.infra.unit.release.orchestrator_tests", "workspace_root"),
}

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
    "MockScanner",
    "ProjectResult",
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
    "SyncOperation",
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
    "TestExtractInlineConstants",
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
    "TestMarkdownReportSkipsEmptyGates",
    "TestMarkdownReportWithErrors",
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
    "TestModuleLevelWrappers",
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
    "TestParsingModuleAst",
    "TestParsingModuleCst",
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
    "TestRunProjectsBehavior",
    "TestRunProjectsReports",
    "TestRunProjectsValidation",
    "TestRunPyrefly",
    "TestRunPyright",
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
    "TestSafetyWorkspaceValidation",
    "TestScaffoldProjectCreatesSrcModules",
    "TestScaffoldProjectCreatesTestsModules",
    "TestScaffoldProjectIdempotency",
    "TestScaffoldProjectNoop",
    "TestScanAstPublicDefs",
    "TestScanFileBatch",
    "TestScanModels",
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
    "TestWorkspaceCheckerMarkdownReport",
    "TestWorkspaceCheckerMarkdownReportEdgeCases",
    "TestWorkspaceCheckerParseGateCSV",
    "TestWorkspaceCheckerResolveGates",
    "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    "TestWorkspaceCheckerRunBandit",
    "TestWorkspaceCheckerRunCommand",
    "TestWorkspaceCheckerRunGo",
    "TestWorkspaceCheckerRunMarkdown",
    "TestWorkspaceCheckerRunMypy",
    "TestWorkspaceCheckerRunPyright",
    "TestWorkspaceCheckerSARIFReport",
    "TestWorkspaceCheckerSARIFReportEdgeCases",
    "TestWorkspaceRoot",
    "TestWorkspaceRootFromEnv",
    "TestWorkspaceRootFromParents",
    "TestWriteJson",
    "TestWriteMarkdown",
    "_utilities",
    "auditor",
    "basemk",
    "builder",
    "census",
    "check",
    "codegen",
    "container",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_execution",
    "deps",
    "detector",
    "discovery",
    "doc",
    "docs",
    "extract_dep_name",
    "fixer",
    "gen",
    "git_repo",
    "github",
    "io",
    "is_external",
    "main",
    "make_cmd_result",
    "make_gate_exec",
    "make_issue",
    "make_project",
    "normalize_link",
    "orchestrator",
    "patch_gate_run",
    "patch_python_dir_detection",
    "pyright_content",
    "refactor",
    "release",
    "rewrite_dep_paths",
    "run_command_failure_check",
    "run_lint",
    "run_pr",
    "run_pr_workspace",
    "run_workflows",
    "runner",
    "service",
    "should_skip_target",
    "svc",
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
    "test_dedupe_specs",
    "test_dep_name",
    "test_detect_mode_with_nonexistent_path",
    "test_detect_mode_with_path_object",
    "test_detects_attribute_base_class",
    "test_detects_basemodel_in_non_model_file",
    "test_detects_missing_local_composition_base",
    "test_detects_multiple_models",
    "test_detects_only_wrong_alias_in_mixed_import",
    "test_detects_same_project_submodule_alias_import",
    "test_detects_wrong_source_m_import",
    "test_detects_wrong_source_u_import",
    "test_discover_projects_wrapper",
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
    "test_expected_dependency_bases_by_family_preserves_internal_dependency_order",
    "test_extract_dep_name",
    "test_extract_requirement_name",
    "test_files_modified_tracks_affected_files",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_flexcore_excluded_from_run",
    "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
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
    "test_get_current_typings_from_pyproject_wrapper",
    "test_get_required_typings_wrapper",
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
    "test_in_context_typevar_not_flagged",
    "test_inject_comments_phase_apply_banner",
    "test_inject_comments_phase_apply_broken_group_section",
    "test_inject_comments_phase_apply_markers",
    "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    "test_injects_t_import_when_needed",
    "test_lazy_import_rule_hoists_import_to_module_level",
    "test_lazy_import_rule_uses_fix_action_for_hoist",
    "test_legacy_import_bypass_collapses_to_primary_import",
    "test_legacy_rule_uses_fix_action_remove_for_aliases",
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    "test_legacy_wrapper_function_is_inlined_as_alias",
    "test_legacy_wrapper_non_passthrough_is_not_inlined",
    "test_main_all_groups_defined",
    "test_main_analyze_violations_is_read_only",
    "test_main_analyze_violations_writes_json_report",
    "test_main_discovery_failure",
    "test_main_group_modules_are_valid",
    "test_main_help_flag_returns_zero",
    "test_main_no_changes_needed",
    "test_main_project_invalid_toml",
    "test_main_project_no_name",
    "test_main_project_non_string_name",
    "test_main_project_obj_not_dict_first_loop",
    "test_main_project_obj_not_dict_second_loop",
    "test_main_returns_error_when_no_args",
    "test_main_success_modes",
    "test_main_sync_failure",
    "test_main_unknown_group_returns_error",
    "test_main_with_changes_and_dry_run",
    "test_main_with_changes_no_dry_run",
    "test_migrate_makefile_not_found_non_dry_run",
    "test_migrate_pyproject_flext_core_non_dry_run",
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
    "test_mro_checker_keeps_external_attribute_base",
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
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
    "test_pattern_rule_converts_dict_annotations_to_mapping",
    "test_pattern_rule_keeps_dict_param_when_copy_used",
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    "test_pattern_rule_removes_configured_redundant_casts",
    "test_pattern_rule_removes_nested_type_object_cast_chain",
    "test_pattern_rule_skips_overload_signatures",
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
    "test_read_project_metadata_preserves_pep621_dependency_order",
    "test_read_project_metadata_preserves_poetry_dependency_order",
    "test_refactor_files_skips_non_python_inputs",
    "test_refactor_project_integrates_safety_manager",
    "test_refactor_project_scans_tests_and_scripts_dirs",
    "test_release_tag_from_branch_invalid",
    "test_release_tag_from_branch_result_type",
    "test_release_tag_from_branch_valid",
    "test_removes_all_imports_when_none_used_import_first",
    "test_removes_all_unused_typing_imports",
    "test_removes_dead_typealias_import",
    "test_removes_typealias_import_only_when_all_usages_converted",
    "test_removes_unused_preserves_used_when_import_precedes_usage",
    "test_render_all_generates_large_makefile",
    "test_render_all_has_no_scripts_path_references",
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
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    "test_rule_dispatch_fails_on_unknown_rule_mapping",
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    "test_rule_dispatch_prefers_fix_action_metadata",
    "test_run_cases",
    "test_run_cli_run_returns_one_for_fail",
    "test_run_cli_run_returns_two_for_error",
    "test_run_cli_run_returns_zero_for_pass",
    "test_run_cli_with_fail_fast_flag",
    "test_run_cli_with_multiple_projects",
    "test_run_deptry_wrapper",
    "test_run_mypy_stub_hints_wrapper",
    "test_run_pip_check_wrapper",
    "test_run_raw_cases",
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
    "test_standalone_final_detected_as_fixable",
    "test_standalone_typealias_detected_as_fixable",
    "test_standalone_typevar_detected_as_fixable",
    "test_string_zero_return_value",
    "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    "test_symbol_propagation_renames_import_and_local_references",
    "test_symbol_propagation_updates_mro_base_references",
    "test_sync_basemk_scenarios",
    "test_sync_error_scenarios",
    "test_sync_extra_paths_missing_root_pyproject",
    "test_sync_extra_paths_success_modes",
    "test_sync_extra_paths_sync_failure",
    "test_sync_one_edge_cases",
    "test_sync_root_validation",
    "test_sync_success_scenarios",
    "test_syntax_error_files_skipped",
    "test_target_path",
    "test_typealias_conversion_preserves_used_typing_siblings",
    "test_unwrap_item",
    "test_unwrap_item_toml_item",
    "test_violation_analysis_counts_massive_patterns",
    "test_violation_analyzer_skips_non_utf8_files",
    "test_workspace_check_main_returns_error_without_projects",
    "test_workspace_cli_migrate_command",
    "test_workspace_cli_migrate_output_contains_summary",
    "test_workspace_migrator_error_handling_on_invalid_workspace",
    "test_workspace_migrator_makefile_not_found_dry_run",
    "test_workspace_migrator_makefile_read_error",
    "test_workspace_migrator_pyproject_write_error",
    "test_workspace_root_doc_construction",
    "test_workspace_root_fallback",
    "v",
    "validate",
    "validator",
    "workspace_root",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
