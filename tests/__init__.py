# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Infra package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_tests import d, e, h, r, s, x

    from tests import refactor, unit
    from tests.constants import FlextInfraTestConstants, FlextInfraTestConstants as c
    from tests.fixtures import (
        real_docs_project,
        real_makefile_project,
        real_python_package,
        real_toml_project,
        real_workspace,
    )
    from tests.fixtures_git import real_git_repo
    from tests.git_service import RealGitService
    from tests.helpers import FlextInfraTestHelpers
    from tests.models import FlextInfraTestModels, FlextInfraTestModels as m
    from tests.protocols import FlextInfraTestProtocols, FlextInfraTestProtocols as p
    from tests.refactor.test_rope_project import (
        TestHookCallOrdering,
        TestInitRopeProject,
        TestRopeHooks,
        TestRopeProjectProperty,
        engine,
        fake_workspace,
    )
    from tests.refactor.test_rope_stubs import (
        test_rope_find_occurrences_import,
        test_rope_import,
        test_rope_rename_import,
    )
    from tests.runner_service import RealSubprocessRunner
    from tests.scenarios import (
        DependencyScenario,
        DependencyScenarios,
        GitScenario,
        GitScenarios,
        SubprocessScenario,
        SubprocessScenarios,
        WorkspaceScenario,
        WorkspaceScenarios,
    )
    from tests.typings import FlextInfraTestTypes, FlextInfraTestTypes as t
    from tests.unit import (
        basemk,
        check,
        codegen,
        container,
        deps,
        discovery,
        docs,
        github,
        io,
        release,
        validate,
    )
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )
    from tests.unit._utilities.test_formatting import TestFormattingRunRuffFix
    from tests.unit._utilities.test_iteration import TestIterWorkspacePythonModules
    from tests.unit._utilities.test_parsing import (
        TestParsingModuleAst,
        TestParsingModuleCst,
    )
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels
    from tests.unit.basemk.test_engine import (
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
    from tests.unit.basemk.test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror,
    )
    from tests.unit.basemk.test_init import TestFlextInfraBaseMk
    from tests.unit.basemk.test_main import (
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
    from tests.unit.check.cli_tests import (
        test_resolve_gates_maps_type_alias,
        test_run_cli_run_returns_one_for_fail,
        test_run_cli_run_returns_two_for_error,
        test_run_cli_run_returns_zero_for_pass,
        test_run_cli_with_fail_fast_flag,
        test_run_cli_with_multiple_projects,
    )
    from tests.unit.check.extended_cli_entry_tests import (
        TestCheckMainEntryPoint,
        TestFixPyrelfyCLI,
        TestRunCLIExtended,
        TestWorkspaceCheckCLI,
    )
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPathResolution,
        TestConfigFixerRunMethods,
        TestConfigFixerRunWithVerbose,
        TestProcessFileReadError,
    )
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
    from tests.unit.check.extended_error_reporting_tests import (
        TestErrorReporting,
        TestGoFmtEmptyLinesInOutput,
        TestMarkdownReportEmptyGates,
        TestMypyEmptyLinesInOutput,
        TestRuffFormatDuplicateFiles,
    )
    from tests.unit.check.extended_gate_bandit_markdown_tests import (
        TestWorkspaceCheckerRunBandit,
        TestWorkspaceCheckerRunMarkdown,
    )
    from tests.unit.check.extended_gate_go_cmd_tests import (
        TestWorkspaceCheckerCollectMarkdownFiles,
        TestWorkspaceCheckerRunCommand,
        TestWorkspaceCheckerRunGo,
        run_command_failure_check,
    )
    from tests.unit.check.extended_gate_mypy_pyright_tests import (
        TestWorkspaceCheckerRunMypy,
        TestWorkspaceCheckerRunPyright,
    )
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import TestJsonWriteFailure
    from tests.unit.check.extended_projects_tests import (
        TestCheckProjectRunners,
        TestLintAndFormatPublicMethods,
    )
    from tests.unit.check.extended_reports_tests import (
        TestMarkdownReportSkipsEmptyGates,
        TestMarkdownReportWithErrors,
        TestWorkspaceCheckerMarkdownReport,
        TestWorkspaceCheckerMarkdownReportEdgeCases,
        TestWorkspaceCheckerSARIFReport,
        TestWorkspaceCheckerSARIFReportEdgeCases,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.check.extended_run_projects_tests import (
        CheckProjectStub,
        TestRunProjectsBehavior,
        TestRunProjectsReports,
        TestRunProjectsValidation,
        TestRunSingleProject,
    )
    from tests.unit.check.extended_runners_extra_tests import (
        GateClass,
        TestRunBandit,
        TestRunMarkdown,
        TestRunPyright,
    )
    from tests.unit.check.extended_runners_go_tests import RunCallable, TestRunGo
    from tests.unit.check.extended_runners_ruff_tests import (
        TestCollectMarkdownFiles,
        TestRunCommand,
        TestRunRuffFormat,
        TestRunRuffLint,
    )
    from tests.unit.check.extended_runners_tests import TestRunMypy, TestRunPyrefly
    from tests.unit.check.extended_workspace_init_tests import (
        TestWorkspaceCheckerBuildGateResult,
        TestWorkspaceCheckerDirsWithPy,
        TestWorkspaceCheckerExecute,
        TestWorkspaceCheckerExistingCheckDirs,
        TestWorkspaceCheckerInitialization,
        TestWorkspaceCheckerInitOSError,
        TestWorkspaceCheckerResolveWorkspaceRootFallback,
    )
    from tests.unit.check.fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help,
    )
    from tests.unit.check.init_tests import TestFlextInfraCheck
    from tests.unit.check.main_tests import test_check_main_executes_real_cli
    from tests.unit.check.pyrefly_tests import TestFlextInfraConfigFixer
    from tests.unit.check.workspace_check_tests import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from tests.unit.check.workspace_tests import TestFlextInfraWorkspaceChecker
    from tests.unit.codegen._project_factory import FlextInfraCodegenTestProjectFactory
    from tests.unit.codegen.autofix_tests import (
        test_in_context_typevar_not_flagged,
        test_standalone_final_detected_as_fixable,
        test_standalone_typealias_detected_as_fixable,
        test_standalone_typevar_detected_as_fixable,
        test_syntax_error_files_skipped,
    )
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )
    from tests.unit.codegen.lazy_init_process_tests import TestProcessDirectory
    from tests.unit.codegen.lazy_init_service_tests import TestFlextInfraCodegenLazyInit
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractInlineConstants,
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanAstPublicDefs,
        TestShouldBubbleUp,
    )
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )
    from tests.unit.codegen.pipeline_tests import test_codegen_pipeline_end_to_end
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions,
        TestInfraMroPattern,
        TestInfraServiceRetrieval,
    )
    from tests.unit.deps.test_detection_classify import (
        TestBuildProjectReport,
        TestClassifyIssues,
    )
    from tests.unit.deps.test_detection_deptry import TestRunDeptry
    from tests.unit.deps.test_detection_models import (
        TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService,
        TestToInfraValue,
    )
    from tests.unit.deps.test_detection_pip_check import TestRunPipCheck
    from tests.unit.deps.test_detection_typings import (
        TestLoadDependencyLimits,
        TestRunMypyStubHints,
    )
    from tests.unit.deps.test_detection_typings_flow import TestModuleAndTypingsFlow
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
        TestFlextInfraDependencyDetectorModels,
    )
    from tests.unit.deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )
    from tests.unit.deps.test_detector_report_flags import TestDetectorReportFlags
    from tests.unit.deps.test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestGetDepPaths,
        TestSyncOne,
    )
    from tests.unit.deps.test_extra_paths_pep621 import (
        TestPathDepPathsPep621,
        TestPathDepPathsPoetry,
    )
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
    from tests.unit.deps.test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestCollectInternalDepsEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_resolve import (
        TestInferOwnerFromOrigin,
        TestResolveRef,
        TestSynthesizedRepoMap,
    )
    from tests.unit.deps.test_internal_sync_sync import TestSync
    from tests.unit.deps.test_internal_sync_sync_edge import TestSyncMethodEdgeCases
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestSyncMethodEdgeCasesMore,
    )
    from tests.unit.deps.test_internal_sync_update import (
        TestEnsureCheckout,
        TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases,
    )
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
    from tests.unit.deps.test_main_dispatch import (
        TestMainDelegation,
        TestMainExceptionHandling,
        TestMainModuleImport,
        TestMainSubcommandDispatch,
        TestMainSysArgvModification,
        test_string_zero_return_value,
    )
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
    from tests.unit.deps.test_modernizer_consolidate import (
        TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )
    from tests.unit.deps.test_modernizer_helpers import (
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
    from tests.unit.deps.test_modernizer_main import (
        TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain,
    )
    from tests.unit.deps.test_modernizer_main_extra import (
        TestModernizerEdgeCases,
        TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path,
    )
    from tests.unit.deps.test_modernizer_pyright import TestEnsurePyrightConfigPhase
    from tests.unit.deps.test_modernizer_pytest import (
        TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes,
    )
    from tests.unit.deps.test_modernizer_workspace import (
        TestParser,
        TestReadDoc,
        test_workspace_root_doc_construction,
    )
    from tests.unit.deps.test_path_sync_helpers import (
        extract_dep_name,
        test_extract_dep_name,
        test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers,
        test_target_path,
    )
    from tests.unit.deps.test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object,
    )
    from tests.unit.deps.test_path_sync_main_edges import TestMainEdgeCases
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
    from tests.unit.deps.test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop,
    )
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestRewriteDepPaths,
        rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps,
    )
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item,
    )
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value,
    )
    from tests.unit.discovery.test_infra_discovery import TestFlextInfraDiscoveryService
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines,
    )
    from tests.unit.docs.auditor_budgets_tests import TestLoadAuditBudgets
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli,
        TestAuditorScopeFailure,
    )
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorToMarkdown,
    )
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms,
        TestAuditorScope,
    )
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from tests.unit.docs.builder_scope_tests import TestBuilderScope
    from tests.unit.docs.builder_tests import TestBuilderCore, builder
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerMaybeFixLink,
        TestFixerProcessFile,
        TestFixerScope,
        TestFixerToc,
        fixer,
    )
    from tests.unit.docs.fixer_tests import TestFixerCore
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers,
        TestGeneratorScope,
        gen,
    )
    from tests.unit.docs.generator_tests import TestGeneratorCore
    from tests.unit.docs.init_tests import TestFlextInfraDocs
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild,
        TestRunGenerate,
        TestRunValidate,
    )
    from tests.unit.docs.main_entry_tests import TestMainRouting, TestMainWithFlags
    from tests.unit.docs.main_tests import TestRunAudit, TestRunFix
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles,
        TestSelectedProjectNames,
    )
    from tests.unit.docs.shared_tests import TestBuildScopes, TestFlextInfraDocScope
    from tests.unit.docs.shared_write_tests import TestWriteJson, TestWriteMarkdown
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers,
        TestMaybeWriteTodo,
        TestValidateScope,
        validator,
    )
    from tests.unit.docs.validator_tests import TestValidateCore, TestValidateReport
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
    from tests.unit.github.main_dispatch_tests import TestRunPrWorkspace
    from tests.unit.github.main_integration_tests import TestMain, main
    from tests.unit.github.main_tests import TestRunLint, TestRunPr, TestRunWorkflows
    from tests.unit.io.test_infra_json_io import SampleModel, TestFlextInfraJsonService
    from tests.unit.io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases,
        TestInfraOutputNoColor,
        TestMroFacadeMethods,
    )
    from tests.unit.io.test_infra_output_formatting import (
        ANSI_RE,
        TestInfraOutputHeader,
        TestInfraOutputMessages,
        TestInfraOutputProgress,
        TestInfraOutputStatus,
        TestInfraOutputSummary,
    )
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor,
        TestShouldUseUnicode,
    )
    from tests.unit.refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files,
    )
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
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
    from tests.unit.refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata,
    )
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
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files,
        test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
        test_import_alias_detector_skips_facade_and_subclass_files,
        test_import_alias_detector_skips_nested_private_and_as_renames,
        test_import_alias_detector_skips_private_and_class_imports,
        test_namespace_rewriter_keeps_contextual_alias_subset,
        test_namespace_rewriter_only_rewrites_runtime_alias_imports,
        test_namespace_rewriter_skips_facade_and_subclass_files,
        test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates,
    )
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
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order,
    )
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub,
        test_refactor_project_integrates_safety_manager,
    )
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
    from tests.unit.release._stubs import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
    )
    from tests.unit.release.flow_tests import TestReleaseMainFlow
    from tests.unit.release.main_tests import TestReleaseMainParsing
    from tests.unit.release.orchestrator_git_tests import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )
    from tests.unit.release.orchestrator_helpers_tests import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )
    from tests.unit.release.orchestrator_phases_tests import (
        TestPhaseBuild,
        TestPhaseValidate,
        TestPhaseVersion,
    )
    from tests.unit.release.orchestrator_publish_tests import TestPhasePublish
    from tests.unit.release.orchestrator_tests import (
        TestReleaseOrchestratorExecute,
        workspace_root,
    )
    from tests.unit.release.release_init_tests import TestReleaseInit
    from tests.unit.release.version_resolution_tests import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
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
    from tests.unit.test_infra_git import (
        TestFlextInfraGitService,
        TestGitPush,
        TestGitTagOperations,
        TestRemovedCompatibilityMethods,
        git_repo,
    )
    from tests.unit.test_infra_init_lazy_core import TestFlextInfraInitLazyLoading
    from tests.unit.test_infra_init_lazy_submodules import (
        TestFlextInfraSubmoduleInitLazyLoading,
    )
    from tests.unit.test_infra_main import (
        test_main_all_groups_defined,
        test_main_group_modules_are_valid,
        test_main_help_flag_returns_zero,
        test_main_returns_error_when_no_args,
        test_main_unknown_group_returns_error,
    )
    from tests.unit.test_infra_maintenance_init import TestFlextInfraMaintenance
    from tests.unit.test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestDiscoverProjects,
        TestEnforcerExecute,
        TestEnsurePythonVersionFile,
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
        TestFlextInfraPatternsPatternTypes,
    )
    from tests.unit.test_infra_protocols import TestFlextInfraProtocolsImport
    from tests.unit.test_infra_reporting_core import TestFlextInfraReportingServiceCore
    from tests.unit.test_infra_reporting_extra import (
        TestFlextInfraReportingServiceExtra,
    )
    from tests.unit.test_infra_selection import TestFlextInfraUtilitiesSelection
    from tests.unit.test_infra_subprocess_core import (
        runner,
        test_capture_cases,
        test_run_cases,
        test_run_raw_cases,
    )
    from tests.unit.test_infra_subprocess_extra import TestFlextInfraCommandRunnerExtra
    from tests.unit.test_infra_toml_io import (
        TestFlextInfraTomlDocument,
        TestFlextInfraTomlHelpers,
        TestFlextInfraTomlRead,
    )
    from tests.unit.test_infra_typings import TestFlextInfraTypesImport
    from tests.unit.test_infra_utilities import TestFlextInfraUtilitiesImport
    from tests.unit.test_infra_version_core import TestFlextInfraVersionClass
    from tests.unit.test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo,
    )
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
    from tests.unit.test_infra_workspace_cli import (
        test_workspace_cli_migrate_command,
        test_workspace_cli_migrate_output_contains_summary,
    )
    from tests.unit.test_infra_workspace_detector import (
        TestDetectorBasicDetection,
        TestDetectorGitRunScenarios,
        TestDetectorRepoNameExtraction,
        detector,
    )
    from tests.unit.test_infra_workspace_init import TestFlextInfraWorkspace
    from tests.unit.test_infra_workspace_main import (
        TestMainCli,
        TestRunDetect,
        TestRunMigrate,
        TestRunOrchestrate,
        TestRunSync,
    )
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
    from tests.unit.test_infra_workspace_migrator_dryrun import (
        test_migrator_flext_core_dry_run,
        test_migrator_flext_core_project_skipped,
        test_migrator_gitignore_already_normalized_dry_run,
        test_migrator_makefile_not_found_dry_run,
        test_migrator_makefile_read_failure,
        test_migrator_pyproject_not_found_dry_run,
    )
    from tests.unit.test_infra_workspace_migrator_errors import (
        TestMigratorReadFailures,
        TestMigratorWriteFailures,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestMigratorEdgeCases,
        TestMigratorInternalMakefile,
        TestMigratorInternalPyproject,
    )
    from tests.unit.test_infra_workspace_migrator_pyproject import (
        TestMigratorDryRun,
        TestMigratorFlextCore,
        TestMigratorPoetryDeps,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestOrchestratorBasic,
        TestOrchestratorFailures,
        TestOrchestratorGateNormalization,
        orchestrator,
    )
    from tests.unit.test_infra_workspace_sync import (
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
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256,
        v,
    )
    from tests.unit.validate.init_tests import TestCoreModuleInit
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore,
        TestInventoryServiceReports,
        TestInventoryServiceScripts,
    )
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate,
        TestMainCliRouting,
        TestMainInventory,
        TestMainScan,
    )
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing,
        TestPytestDiagParseXml,
    )
    from tests.unit.validate.scanner_tests import (
        TestScannerCore,
        TestScannerHelpers,
        TestScannerMultiFile,
    )
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate,
        TestStringList,
    )
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze,
        TestStubChainCore,
        TestStubChainDiscoverProjects,
        TestStubChainIsInternal,
        TestStubChainStubExists,
        TestStubChainValidate,
    )
    from tests.utilities import FlextInfraTestUtilities, FlextInfraTestUtilities as u
    from tests.workspace_factory import WorkspaceFactory
    from tests.workspace_scenarios import (
        BrokenScenario,
        EmptyScenario,
        FullScenario,
        MinimalScenario,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "ANSI_RE": ["tests.unit.io.test_infra_output_formatting", "ANSI_RE"],
    "BrokenScenario": ["tests.workspace_scenarios", "BrokenScenario"],
    "CheckProjectStub": [
        "tests.unit.check.extended_run_projects_tests",
        "CheckProjectStub",
    ],
    "DependencyScenario": ["tests.scenarios", "DependencyScenario"],
    "DependencyScenarios": ["tests.scenarios", "DependencyScenarios"],
    "EmptyScenario": ["tests.workspace_scenarios", "EmptyScenario"],
    "EngineSafetyStub": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ],
    "FAMILY_FILE_MAP": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_FILE_MAP",
    ],
    "FAMILY_SUFFIX_MAP": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_SUFFIX_MAP",
    ],
    "FakeReporting": ["tests.unit.release._stubs", "FakeReporting"],
    "FakeSelection": ["tests.unit.release._stubs", "FakeSelection"],
    "FakeSubprocess": ["tests.unit.release._stubs", "FakeSubprocess"],
    "FakeUtilsNamespace": ["tests.unit.release._stubs", "FakeUtilsNamespace"],
    "FakeVersioning": ["tests.unit.release._stubs", "FakeVersioning"],
    "FlextInfraCodegenTestProjectFactory": [
        "tests.unit.codegen._project_factory",
        "FlextInfraCodegenTestProjectFactory",
    ],
    "FlextInfraTestConstants": ["tests.constants", "FlextInfraTestConstants"],
    "FlextInfraTestHelpers": ["tests.helpers", "FlextInfraTestHelpers"],
    "FlextInfraTestModels": ["tests.models", "FlextInfraTestModels"],
    "FlextInfraTestProtocols": ["tests.protocols", "FlextInfraTestProtocols"],
    "FlextInfraTestTypes": ["tests.typings", "FlextInfraTestTypes"],
    "FlextInfraTestUtilities": ["tests.utilities", "FlextInfraTestUtilities"],
    "FullScenario": ["tests.workspace_scenarios", "FullScenario"],
    "GateClass": ["tests.unit.check.extended_runners_extra_tests", "GateClass"],
    "GitScenario": ["tests.scenarios", "GitScenario"],
    "GitScenarios": ["tests.scenarios", "GitScenarios"],
    "MinimalScenario": ["tests.workspace_scenarios", "MinimalScenario"],
    "RealGitService": ["tests.git_service", "RealGitService"],
    "RealSubprocessRunner": ["tests.runner_service", "RealSubprocessRunner"],
    "RunCallable": ["tests.unit.check.extended_runners_go_tests", "RunCallable"],
    "RunProjectsMock": ["tests.unit.check._shared_fixtures", "RunProjectsMock"],
    "SampleModel": ["tests.unit.io.test_infra_json_io", "SampleModel"],
    "SetupFn": ["tests.unit.test_infra_workspace_sync", "SetupFn"],
    "Spy": ["tests.unit.check._stubs", "Spy"],
    "StubCommandOutput": ["tests.unit.github._stubs", "StubCommandOutput"],
    "StubJsonIo": ["tests.unit.github._stubs", "StubJsonIo"],
    "StubLinter": ["tests.unit.github._stubs", "StubLinter"],
    "StubPrManager": ["tests.unit.github._stubs", "StubPrManager"],
    "StubProjectInfo": ["tests.unit.github._stubs", "StubProjectInfo"],
    "StubReporting": ["tests.unit.github._stubs", "StubReporting"],
    "StubRunner": ["tests.unit.github._stubs", "StubRunner"],
    "StubSelector": ["tests.unit.github._stubs", "StubSelector"],
    "StubSyncer": ["tests.unit.github._stubs", "StubSyncer"],
    "StubTemplates": ["tests.unit.github._stubs", "StubTemplates"],
    "StubUtilities": ["tests.unit.github._stubs", "StubUtilities"],
    "StubVersioning": ["tests.unit.github._stubs", "StubVersioning"],
    "StubWorkspaceManager": ["tests.unit.github._stubs", "StubWorkspaceManager"],
    "SubprocessScenario": ["tests.scenarios", "SubprocessScenario"],
    "SubprocessScenarios": ["tests.scenarios", "SubprocessScenarios"],
    "TestAdrHelpers": ["tests.unit.docs.validator_internals_tests", "TestAdrHelpers"],
    "TestAllDirectoriesScanned": [
        "tests.unit.codegen.lazy_init_tests",
        "TestAllDirectoriesScanned",
    ],
    "TestAuditorBrokenLinks": [
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorBrokenLinks",
    ],
    "TestAuditorCore": ["tests.unit.docs.auditor_tests", "TestAuditorCore"],
    "TestAuditorForbiddenTerms": [
        "tests.unit.docs.auditor_scope_tests",
        "TestAuditorForbiddenTerms",
    ],
    "TestAuditorMainCli": ["tests.unit.docs.auditor_cli_tests", "TestAuditorMainCli"],
    "TestAuditorNormalize": ["tests.unit.docs.auditor_tests", "TestAuditorNormalize"],
    "TestAuditorScope": ["tests.unit.docs.auditor_scope_tests", "TestAuditorScope"],
    "TestAuditorScopeFailure": [
        "tests.unit.docs.auditor_cli_tests",
        "TestAuditorScopeFailure",
    ],
    "TestAuditorToMarkdown": [
        "tests.unit.docs.auditor_links_tests",
        "TestAuditorToMarkdown",
    ],
    "TestBaseMkValidatorCore": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorCore",
    ],
    "TestBaseMkValidatorEdgeCases": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorEdgeCases",
    ],
    "TestBaseMkValidatorSha256": [
        "tests.unit.validate.basemk_validator_tests",
        "TestBaseMkValidatorSha256",
    ],
    "TestBuildProjectReport": [
        "tests.unit.deps.test_detection_classify",
        "TestBuildProjectReport",
    ],
    "TestBuildScopes": ["tests.unit.docs.shared_tests", "TestBuildScopes"],
    "TestBuildSiblingExportIndex": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestBuildSiblingExportIndex",
    ],
    "TestBuildTargets": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestBuildTargets",
    ],
    "TestBuilderCore": ["tests.unit.docs.builder_tests", "TestBuilderCore"],
    "TestBuilderScope": ["tests.unit.docs.builder_scope_tests", "TestBuilderScope"],
    "TestBumpNextDev": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestBumpNextDev",
    ],
    "TestCensusReportModel": [
        "tests.unit.codegen.census_models_tests",
        "TestCensusReportModel",
    ],
    "TestCensusViolationModel": [
        "tests.unit.codegen.census_models_tests",
        "TestCensusViolationModel",
    ],
    "TestCheckIssueFormatted": [
        "tests.unit.check.extended_models_tests",
        "TestCheckIssueFormatted",
    ],
    "TestCheckMainEntryPoint": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestCheckMainEntryPoint",
    ],
    "TestCheckOnlyMode": ["tests.unit.codegen.lazy_init_tests", "TestCheckOnlyMode"],
    "TestCheckProjectRunners": [
        "tests.unit.check.extended_projects_tests",
        "TestCheckProjectRunners",
    ],
    "TestClassifyIssues": [
        "tests.unit.deps.test_detection_classify",
        "TestClassifyIssues",
    ],
    "TestCollectChanges": [
        "tests.unit.release.orchestrator_git_tests",
        "TestCollectChanges",
    ],
    "TestCollectInternalDeps": [
        "tests.unit.deps.test_internal_sync_discovery",
        "TestCollectInternalDeps",
    ],
    "TestCollectInternalDepsEdgeCases": [
        "tests.unit.deps.test_internal_sync_discovery_edge",
        "TestCollectInternalDepsEdgeCases",
    ],
    "TestCollectMarkdownFiles": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestCollectMarkdownFiles",
    ],
    "TestConfigFixerEnsureProjectExcludes": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerEnsureProjectExcludes",
    ],
    "TestConfigFixerExecute": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerExecute",
    ],
    "TestConfigFixerFindPyprojectFiles": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFindPyprojectFiles",
    ],
    "TestConfigFixerFixSearchPaths": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFixSearchPaths",
    ],
    "TestConfigFixerPathResolution": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerPathResolution",
    ],
    "TestConfigFixerProcessFile": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerProcessFile",
    ],
    "TestConfigFixerRemoveIgnoreSubConfig": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRemoveIgnoreSubConfig",
    ],
    "TestConfigFixerRun": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRun",
    ],
    "TestConfigFixerRunMethods": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunMethods",
    ],
    "TestConfigFixerRunWithVerbose": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunWithVerbose",
    ],
    "TestConfigFixerToArray": [
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerToArray",
    ],
    "TestConsolidateGroupsPhase": [
        "tests.unit.deps.test_modernizer_consolidate",
        "TestConsolidateGroupsPhase",
    ],
    "TestConstants": ["tests.unit.deps.test_extra_paths_manager", "TestConstants"],
    "TestConstantsQualityGateCLIDispatch": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateCLIDispatch",
    ],
    "TestConstantsQualityGateVerdict": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateVerdict",
    ],
    "TestCoreModuleInit": ["tests.unit.validate.init_tests", "TestCoreModuleInit"],
    "TestCreateBranches": [
        "tests.unit.release.orchestrator_git_tests",
        "TestCreateBranches",
    ],
    "TestCreateTag": ["tests.unit.release.orchestrator_git_tests", "TestCreateTag"],
    "TestDetectMode": ["tests.unit.deps.test_path_sync_init", "TestDetectMode"],
    "TestDetectionUncoveredLines": [
        "tests.unit.deps.test_detection_uncovered",
        "TestDetectionUncoveredLines",
    ],
    "TestDetectorBasicDetection": [
        "tests.unit.test_infra_workspace_detector",
        "TestDetectorBasicDetection",
    ],
    "TestDetectorGitRunScenarios": [
        "tests.unit.test_infra_workspace_detector",
        "TestDetectorGitRunScenarios",
    ],
    "TestDetectorRepoNameExtraction": [
        "tests.unit.test_infra_workspace_detector",
        "TestDetectorRepoNameExtraction",
    ],
    "TestDetectorReportFlags": [
        "tests.unit.deps.test_detector_report_flags",
        "TestDetectorReportFlags",
    ],
    "TestDetectorRunFailures": [
        "tests.unit.deps.test_detector_detect_failures",
        "TestDetectorRunFailures",
    ],
    "TestDiscoverProjects": [
        "tests.unit.test_infra_maintenance_python_version",
        "TestDiscoverProjects",
    ],
    "TestDiscoveryDiscoverProjects": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryDiscoverProjects",
    ],
    "TestDiscoveryFindAllPyprojectFiles": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryFindAllPyprojectFiles",
    ],
    "TestDiscoveryIterPythonFiles": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryIterPythonFiles",
    ],
    "TestDiscoveryProjectRoots": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryProjectRoots",
    ],
    "TestDispatchPhase": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestDispatchPhase",
    ],
    "TestEdgeCases": ["tests.unit.codegen.lazy_init_tests", "TestEdgeCases"],
    "TestEnforcerExecute": [
        "tests.unit.test_infra_maintenance_python_version",
        "TestEnforcerExecute",
    ],
    "TestEnsureCheckout": [
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureCheckout",
    ],
    "TestEnsureCheckoutEdgeCases": [
        "tests.unit.deps.test_internal_sync_update_checkout_edge",
        "TestEnsureCheckoutEdgeCases",
    ],
    "TestEnsurePyreflyConfigPhase": [
        "tests.unit.deps.test_modernizer_pyrefly",
        "TestEnsurePyreflyConfigPhase",
    ],
    "TestEnsurePyrightConfigPhase": [
        "tests.unit.deps.test_modernizer_pyright",
        "TestEnsurePyrightConfigPhase",
    ],
    "TestEnsurePytestConfigPhase": [
        "tests.unit.deps.test_modernizer_pytest",
        "TestEnsurePytestConfigPhase",
    ],
    "TestEnsurePythonVersionFile": [
        "tests.unit.test_infra_maintenance_python_version",
        "TestEnsurePythonVersionFile",
    ],
    "TestEnsureSymlink": [
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureSymlink",
    ],
    "TestEnsureSymlinkEdgeCases": [
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureSymlinkEdgeCases",
    ],
    "TestErrorReporting": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestErrorReporting",
    ],
    "TestExcludedDirectories": [
        "tests.unit.codegen.lazy_init_tests",
        "TestExcludedDirectories",
    ],
    "TestExcludedProjects": [
        "tests.unit.codegen.census_models_tests",
        "TestExcludedProjects",
    ],
    "TestExtractExports": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestExtractExports",
    ],
    "TestExtractInlineConstants": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractInlineConstants",
    ],
    "TestExtractVersionExports": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractVersionExports",
    ],
    "TestFixPyrelfyCLI": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestFixPyrelfyCLI",
    ],
    "TestFixabilityClassification": [
        "tests.unit.codegen.census_tests",
        "TestFixabilityClassification",
    ],
    "TestFixerCore": ["tests.unit.docs.fixer_tests", "TestFixerCore"],
    "TestFixerMaybeFixLink": [
        "tests.unit.docs.fixer_internals_tests",
        "TestFixerMaybeFixLink",
    ],
    "TestFixerProcessFile": [
        "tests.unit.docs.fixer_internals_tests",
        "TestFixerProcessFile",
    ],
    "TestFixerScope": ["tests.unit.docs.fixer_internals_tests", "TestFixerScope"],
    "TestFixerToc": ["tests.unit.docs.fixer_internals_tests", "TestFixerToc"],
    "TestFlextInfraBaseMk": ["tests.unit.basemk.test_init", "TestFlextInfraBaseMk"],
    "TestFlextInfraCheck": ["tests.unit.check.init_tests", "TestFlextInfraCheck"],
    "TestFlextInfraCodegenLazyInit": [
        "tests.unit.codegen.lazy_init_service_tests",
        "TestFlextInfraCodegenLazyInit",
    ],
    "TestFlextInfraCommandRunnerExtra": [
        "tests.unit.test_infra_subprocess_extra",
        "TestFlextInfraCommandRunnerExtra",
    ],
    "TestFlextInfraConfigFixer": [
        "tests.unit.check.pyrefly_tests",
        "TestFlextInfraConfigFixer",
    ],
    "TestFlextInfraConstantsAlias": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsAlias",
    ],
    "TestFlextInfraConstantsCheckNamespace": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsCheckNamespace",
    ],
    "TestFlextInfraConstantsConsistency": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsConsistency",
    ],
    "TestFlextInfraConstantsEncodingNamespace": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsEncodingNamespace",
    ],
    "TestFlextInfraConstantsExcludedNamespace": [
        "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsExcludedNamespace",
    ],
    "TestFlextInfraConstantsFilesNamespace": [
        "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsFilesNamespace",
    ],
    "TestFlextInfraConstantsGatesNamespace": [
        "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsGatesNamespace",
    ],
    "TestFlextInfraConstantsGithubNamespace": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsGithubNamespace",
    ],
    "TestFlextInfraConstantsImmutability": [
        "tests.unit.test_infra_constants_extra",
        "TestFlextInfraConstantsImmutability",
    ],
    "TestFlextInfraConstantsPathsNamespace": [
        "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsPathsNamespace",
    ],
    "TestFlextInfraConstantsStatusNamespace": [
        "tests.unit.test_infra_constants_core",
        "TestFlextInfraConstantsStatusNamespace",
    ],
    "TestFlextInfraDependencyDetectionModels": [
        "tests.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionModels",
    ],
    "TestFlextInfraDependencyDetectionService": [
        "tests.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionService",
    ],
    "TestFlextInfraDependencyDetectorModels": [
        "tests.unit.deps.test_detector_models",
        "TestFlextInfraDependencyDetectorModels",
    ],
    "TestFlextInfraDependencyPathSync": [
        "tests.unit.deps.test_path_sync_init",
        "TestFlextInfraDependencyPathSync",
    ],
    "TestFlextInfraDeps": ["tests.unit.deps.test_init", "TestFlextInfraDeps"],
    "TestFlextInfraDiscoveryService": [
        "tests.unit.discovery.test_infra_discovery",
        "TestFlextInfraDiscoveryService",
    ],
    "TestFlextInfraDiscoveryServiceUncoveredLines": [
        "tests.unit.discovery.test_infra_discovery_edge_cases",
        "TestFlextInfraDiscoveryServiceUncoveredLines",
    ],
    "TestFlextInfraDocScope": [
        "tests.unit.docs.shared_tests",
        "TestFlextInfraDocScope",
    ],
    "TestFlextInfraDocs": ["tests.unit.docs.init_tests", "TestFlextInfraDocs"],
    "TestFlextInfraExtraPathsManager": [
        "tests.unit.deps.test_extra_paths_manager",
        "TestFlextInfraExtraPathsManager",
    ],
    "TestFlextInfraGitService": [
        "tests.unit.test_infra_git",
        "TestFlextInfraGitService",
    ],
    "TestFlextInfraInitLazyLoading": [
        "tests.unit.test_infra_init_lazy_core",
        "TestFlextInfraInitLazyLoading",
    ],
    "TestFlextInfraInternalDependencySyncService": [
        "tests.unit.deps.test_internal_sync_validation",
        "TestFlextInfraInternalDependencySyncService",
    ],
    "TestFlextInfraJsonService": [
        "tests.unit.io.test_infra_json_io",
        "TestFlextInfraJsonService",
    ],
    "TestFlextInfraMaintenance": [
        "tests.unit.test_infra_maintenance_init",
        "TestFlextInfraMaintenance",
    ],
    "TestFlextInfraPathResolver": [
        "tests.unit.test_infra_paths",
        "TestFlextInfraPathResolver",
    ],
    "TestFlextInfraPatternsEdgeCases": [
        "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsEdgeCases",
    ],
    "TestFlextInfraPatternsMarkdown": [
        "tests.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsMarkdown",
    ],
    "TestFlextInfraPatternsPatternTypes": [
        "tests.unit.test_infra_patterns_extra",
        "TestFlextInfraPatternsPatternTypes",
    ],
    "TestFlextInfraPatternsTooling": [
        "tests.unit.test_infra_patterns_core",
        "TestFlextInfraPatternsTooling",
    ],
    "TestFlextInfraProtocolsImport": [
        "tests.unit.test_infra_protocols",
        "TestFlextInfraProtocolsImport",
    ],
    "TestFlextInfraPyprojectModernizer": [
        "tests.unit.deps.test_modernizer_main",
        "TestFlextInfraPyprojectModernizer",
    ],
    "TestFlextInfraReportingServiceCore": [
        "tests.unit.test_infra_reporting_core",
        "TestFlextInfraReportingServiceCore",
    ],
    "TestFlextInfraReportingServiceExtra": [
        "tests.unit.test_infra_reporting_extra",
        "TestFlextInfraReportingServiceExtra",
    ],
    "TestFlextInfraRuntimeDevDependencyDetectorInit": [
        "tests.unit.deps.test_detector_init",
        "TestFlextInfraRuntimeDevDependencyDetectorInit",
    ],
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect": [
        "tests.unit.deps.test_detector_detect",
        "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    ],
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport": [
        "tests.unit.deps.test_detector_report",
        "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    ],
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings": [
        "tests.unit.deps.test_detector_main",
        "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    ],
    "TestFlextInfraSubmoduleInitLazyLoading": [
        "tests.unit.test_infra_init_lazy_submodules",
        "TestFlextInfraSubmoduleInitLazyLoading",
    ],
    "TestFlextInfraTomlDocument": [
        "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlDocument",
    ],
    "TestFlextInfraTomlHelpers": [
        "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlHelpers",
    ],
    "TestFlextInfraTomlRead": [
        "tests.unit.test_infra_toml_io",
        "TestFlextInfraTomlRead",
    ],
    "TestFlextInfraTypesImport": [
        "tests.unit.test_infra_typings",
        "TestFlextInfraTypesImport",
    ],
    "TestFlextInfraUtilitiesImport": [
        "tests.unit.test_infra_utilities",
        "TestFlextInfraUtilitiesImport",
    ],
    "TestFlextInfraUtilitiesSelection": [
        "tests.unit.test_infra_selection",
        "TestFlextInfraUtilitiesSelection",
    ],
    "TestFlextInfraVersionClass": [
        "tests.unit.test_infra_version_core",
        "TestFlextInfraVersionClass",
    ],
    "TestFlextInfraVersionModuleLevel": [
        "tests.unit.test_infra_version_extra",
        "TestFlextInfraVersionModuleLevel",
    ],
    "TestFlextInfraVersionPackageInfo": [
        "tests.unit.test_infra_version_extra",
        "TestFlextInfraVersionPackageInfo",
    ],
    "TestFlextInfraWorkspace": [
        "tests.unit.test_infra_workspace_init",
        "TestFlextInfraWorkspace",
    ],
    "TestFlextInfraWorkspaceChecker": [
        "tests.unit.check.workspace_tests",
        "TestFlextInfraWorkspaceChecker",
    ],
    "TestFormattingRunRuffFix": [
        "tests.unit._utilities.test_formatting",
        "TestFormattingRunRuffFix",
    ],
    "TestGenerateFile": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateFile",
    ],
    "TestGenerateNotes": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestGenerateNotes",
    ],
    "TestGenerateTypeChecking": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateTypeChecking",
    ],
    "TestGeneratedClassNamingConvention": [
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedClassNamingConvention",
    ],
    "TestGeneratedFilesAreValidPython": [
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedFilesAreValidPython",
    ],
    "TestGeneratorCore": ["tests.unit.docs.generator_tests", "TestGeneratorCore"],
    "TestGeneratorHelpers": [
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorHelpers",
    ],
    "TestGeneratorScope": [
        "tests.unit.docs.generator_internals_tests",
        "TestGeneratorScope",
    ],
    "TestGetDepPaths": ["tests.unit.deps.test_extra_paths_manager", "TestGetDepPaths"],
    "TestGitPush": ["tests.unit.test_infra_git", "TestGitPush"],
    "TestGitTagOperations": ["tests.unit.test_infra_git", "TestGitTagOperations"],
    "TestGoFmtEmptyLinesInOutput": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestGoFmtEmptyLinesInOutput",
    ],
    "TestHandleLazyInit": ["tests.unit.codegen.main_tests", "TestHandleLazyInit"],
    "TestHookCallOrdering": [
        "tests.refactor.test_rope_project",
        "TestHookCallOrdering",
    ],
    "TestInferOwnerFromOrigin": [
        "tests.unit.deps.test_internal_sync_resolve",
        "TestInferOwnerFromOrigin",
    ],
    "TestInferPackage": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestInferPackage",
    ],
    "TestInfraContainerFunctions": [
        "tests.unit.container.test_infra_container",
        "TestInfraContainerFunctions",
    ],
    "TestInfraMroPattern": [
        "tests.unit.container.test_infra_container",
        "TestInfraMroPattern",
    ],
    "TestInfraOutputEdgeCases": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputEdgeCases",
    ],
    "TestInfraOutputHeader": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputHeader",
    ],
    "TestInfraOutputMessages": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputMessages",
    ],
    "TestInfraOutputNoColor": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputNoColor",
    ],
    "TestInfraOutputProgress": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputProgress",
    ],
    "TestInfraOutputStatus": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputStatus",
    ],
    "TestInfraOutputSummary": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputSummary",
    ],
    "TestInfraServiceRetrieval": [
        "tests.unit.container.test_infra_container",
        "TestInfraServiceRetrieval",
    ],
    "TestInitRopeProject": ["tests.refactor.test_rope_project", "TestInitRopeProject"],
    "TestInjectCommentsPhase": [
        "tests.unit.deps.test_modernizer_comments",
        "TestInjectCommentsPhase",
    ],
    "TestInventoryServiceCore": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceCore",
    ],
    "TestInventoryServiceReports": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceReports",
    ],
    "TestInventoryServiceScripts": [
        "tests.unit.validate.inventory_tests",
        "TestInventoryServiceScripts",
    ],
    "TestIsInternalPathDep": [
        "tests.unit.deps.test_internal_sync_validation",
        "TestIsInternalPathDep",
    ],
    "TestIsRelativeTo": [
        "tests.unit.deps.test_internal_sync_validation",
        "TestIsRelativeTo",
    ],
    "TestIsWorkspaceMode": [
        "tests.unit.deps.test_internal_sync_workspace",
        "TestIsWorkspaceMode",
    ],
    "TestIterMarkdownFiles": [
        "tests.unit.docs.shared_iter_tests",
        "TestIterMarkdownFiles",
    ],
    "TestIterWorkspacePythonModules": [
        "tests.unit._utilities.test_iteration",
        "TestIterWorkspacePythonModules",
    ],
    "TestJsonWriteFailure": [
        "tests.unit.check.extended_project_runners_tests",
        "TestJsonWriteFailure",
    ],
    "TestLintAndFormatPublicMethods": [
        "tests.unit.check.extended_projects_tests",
        "TestLintAndFormatPublicMethods",
    ],
    "TestLoadAuditBudgets": [
        "tests.unit.docs.auditor_budgets_tests",
        "TestLoadAuditBudgets",
    ],
    "TestLoadDependencyLimits": [
        "tests.unit.deps.test_detection_typings",
        "TestLoadDependencyLimits",
    ],
    "TestMain": ["tests.unit.github.main_integration_tests", "TestMain"],
    "TestMainBaseMkValidate": [
        "tests.unit.validate.main_tests",
        "TestMainBaseMkValidate",
    ],
    "TestMainCli": ["tests.unit.test_infra_workspace_main", "TestMainCli"],
    "TestMainCliRouting": ["tests.unit.validate.main_tests", "TestMainCliRouting"],
    "TestMainCommandDispatch": [
        "tests.unit.codegen.main_tests",
        "TestMainCommandDispatch",
    ],
    "TestMainDelegation": ["tests.unit.deps.test_main_dispatch", "TestMainDelegation"],
    "TestMainEdgeCases": [
        "tests.unit.deps.test_path_sync_main_edges",
        "TestMainEdgeCases",
    ],
    "TestMainEntryPoint": ["tests.unit.codegen.main_tests", "TestMainEntryPoint"],
    "TestMainExceptionHandling": [
        "tests.unit.deps.test_main_dispatch",
        "TestMainExceptionHandling",
    ],
    "TestMainFunction": ["tests.unit.deps.test_detector_main", "TestMainFunction"],
    "TestMainHelpAndErrors": ["tests.unit.deps.test_main", "TestMainHelpAndErrors"],
    "TestMainInventory": ["tests.unit.validate.main_tests", "TestMainInventory"],
    "TestMainModuleImport": [
        "tests.unit.deps.test_main_dispatch",
        "TestMainModuleImport",
    ],
    "TestMainReturnValues": ["tests.unit.deps.test_main", "TestMainReturnValues"],
    "TestMainRouting": ["tests.unit.docs.main_entry_tests", "TestMainRouting"],
    "TestMainScan": ["tests.unit.validate.main_tests", "TestMainScan"],
    "TestMainSubcommandDispatch": [
        "tests.unit.deps.test_main_dispatch",
        "TestMainSubcommandDispatch",
    ],
    "TestMainSysArgvModification": [
        "tests.unit.deps.test_main_dispatch",
        "TestMainSysArgvModification",
    ],
    "TestMainWithFlags": ["tests.unit.docs.main_entry_tests", "TestMainWithFlags"],
    "TestMaintenanceMainEnforcer": [
        "tests.unit.test_infra_maintenance_main",
        "TestMaintenanceMainEnforcer",
    ],
    "TestMaintenanceMainSuccess": [
        "tests.unit.test_infra_maintenance_main",
        "TestMaintenanceMainSuccess",
    ],
    "TestMarkdownReportEmptyGates": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestMarkdownReportEmptyGates",
    ],
    "TestMarkdownReportSkipsEmptyGates": [
        "tests.unit.check.extended_reports_tests",
        "TestMarkdownReportSkipsEmptyGates",
    ],
    "TestMarkdownReportWithErrors": [
        "tests.unit.check.extended_reports_tests",
        "TestMarkdownReportWithErrors",
    ],
    "TestMaybeWriteTodo": [
        "tests.unit.docs.validator_internals_tests",
        "TestMaybeWriteTodo",
    ],
    "TestMergeChildExports": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestMergeChildExports",
    ],
    "TestMigratorDryRun": [
        "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorDryRun",
    ],
    "TestMigratorEdgeCases": [
        "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorEdgeCases",
    ],
    "TestMigratorFlextCore": [
        "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorFlextCore",
    ],
    "TestMigratorInternalMakefile": [
        "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalMakefile",
    ],
    "TestMigratorInternalPyproject": [
        "tests.unit.test_infra_workspace_migrator_internal",
        "TestMigratorInternalPyproject",
    ],
    "TestMigratorPoetryDeps": [
        "tests.unit.test_infra_workspace_migrator_pyproject",
        "TestMigratorPoetryDeps",
    ],
    "TestMigratorReadFailures": [
        "tests.unit.test_infra_workspace_migrator_errors",
        "TestMigratorReadFailures",
    ],
    "TestMigratorWriteFailures": [
        "tests.unit.test_infra_workspace_migrator_errors",
        "TestMigratorWriteFailures",
    ],
    "TestModernizerEdgeCases": [
        "tests.unit.deps.test_modernizer_main_extra",
        "TestModernizerEdgeCases",
    ],
    "TestModernizerRunAndMain": [
        "tests.unit.deps.test_modernizer_main",
        "TestModernizerRunAndMain",
    ],
    "TestModernizerUncoveredLines": [
        "tests.unit.deps.test_modernizer_main_extra",
        "TestModernizerUncoveredLines",
    ],
    "TestModuleAndTypingsFlow": [
        "tests.unit.deps.test_detection_typings_flow",
        "TestModuleAndTypingsFlow",
    ],
    "TestMroFacadeMethods": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestMroFacadeMethods",
    ],
    "TestMypyEmptyLinesInOutput": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestMypyEmptyLinesInOutput",
    ],
    "TestOrchestratorBasic": [
        "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorBasic",
    ],
    "TestOrchestratorFailures": [
        "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorFailures",
    ],
    "TestOrchestratorGateNormalization": [
        "tests.unit.test_infra_workspace_orchestrator",
        "TestOrchestratorGateNormalization",
    ],
    "TestOwnerFromRemoteUrl": [
        "tests.unit.deps.test_internal_sync_validation",
        "TestOwnerFromRemoteUrl",
    ],
    "TestParseGitmodules": [
        "tests.unit.deps.test_internal_sync_discovery",
        "TestParseGitmodules",
    ],
    "TestParseRepoMap": [
        "tests.unit.deps.test_internal_sync_discovery",
        "TestParseRepoMap",
    ],
    "TestParseViolationInvalid": [
        "tests.unit.codegen.census_tests",
        "TestParseViolationInvalid",
    ],
    "TestParseViolationValid": [
        "tests.unit.codegen.census_tests",
        "TestParseViolationValid",
    ],
    "TestParser": ["tests.unit.deps.test_modernizer_workspace", "TestParser"],
    "TestParsingModuleAst": [
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleAst",
    ],
    "TestParsingModuleCst": [
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleCst",
    ],
    "TestPathDepPathsPep621": [
        "tests.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPep621",
    ],
    "TestPathDepPathsPoetry": [
        "tests.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPoetry",
    ],
    "TestPathSyncEdgeCases": [
        "tests.unit.deps.test_path_sync_init",
        "TestPathSyncEdgeCases",
    ],
    "TestPhaseBuild": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseBuild",
    ],
    "TestPhasePublish": [
        "tests.unit.release.orchestrator_publish_tests",
        "TestPhasePublish",
    ],
    "TestPhaseValidate": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseValidate",
    ],
    "TestPhaseVersion": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseVersion",
    ],
    "TestPreviousTag": ["tests.unit.release.orchestrator_git_tests", "TestPreviousTag"],
    "TestProcessDirectory": [
        "tests.unit.codegen.lazy_init_process_tests",
        "TestProcessDirectory",
    ],
    "TestProcessFileReadError": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestProcessFileReadError",
    ],
    "TestProjectResultProperties": [
        "tests.unit.check.extended_models_tests",
        "TestProjectResultProperties",
    ],
    "TestPushRelease": ["tests.unit.release.orchestrator_git_tests", "TestPushRelease"],
    "TestPytestDiagExtractorCore": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagExtractorCore",
    ],
    "TestPytestDiagLogParsing": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagLogParsing",
    ],
    "TestPytestDiagParseXml": [
        "tests.unit.validate.pytest_diag",
        "TestPytestDiagParseXml",
    ],
    "TestReadDoc": ["tests.unit.deps.test_modernizer_workspace", "TestReadDoc"],
    "TestReadExistingDocstring": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestReadExistingDocstring",
    ],
    "TestReadRequiredMinor": [
        "tests.unit.test_infra_maintenance_python_version",
        "TestReadRequiredMinor",
    ],
    "TestReleaseInit": ["tests.unit.release.release_init_tests", "TestReleaseInit"],
    "TestReleaseMainFlow": ["tests.unit.release.flow_tests", "TestReleaseMainFlow"],
    "TestReleaseMainParsing": [
        "tests.unit.release.main_tests",
        "TestReleaseMainParsing",
    ],
    "TestReleaseMainTagResolution": [
        "tests.unit.release.version_resolution_tests",
        "TestReleaseMainTagResolution",
    ],
    "TestReleaseMainVersionResolution": [
        "tests.unit.release.version_resolution_tests",
        "TestReleaseMainVersionResolution",
    ],
    "TestReleaseOrchestratorExecute": [
        "tests.unit.release.orchestrator_tests",
        "TestReleaseOrchestratorExecute",
    ],
    "TestRemovedCompatibilityMethods": [
        "tests.unit.test_infra_git",
        "TestRemovedCompatibilityMethods",
    ],
    "TestResolveAliases": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestResolveAliases",
    ],
    "TestResolveRef": ["tests.unit.deps.test_internal_sync_resolve", "TestResolveRef"],
    "TestResolveVersionInteractive": [
        "tests.unit.release.version_resolution_tests",
        "TestResolveVersionInteractive",
    ],
    "TestRewriteDepPaths": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "TestRewriteDepPaths",
    ],
    "TestRewritePep621": [
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "TestRewritePep621",
    ],
    "TestRewritePoetry": [
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "TestRewritePoetry",
    ],
    "TestRopeHooks": ["tests.refactor.test_rope_project", "TestRopeHooks"],
    "TestRopeProjectProperty": [
        "tests.refactor.test_rope_project",
        "TestRopeProjectProperty",
    ],
    "TestRuffFormatDuplicateFiles": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestRuffFormatDuplicateFiles",
    ],
    "TestRunAudit": ["tests.unit.docs.main_tests", "TestRunAudit"],
    "TestRunBandit": ["tests.unit.check.extended_runners_extra_tests", "TestRunBandit"],
    "TestRunBuild": ["tests.unit.docs.main_commands_tests", "TestRunBuild"],
    "TestRunCLIExtended": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestRunCLIExtended",
    ],
    "TestRunCommand": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestRunCommand",
    ],
    "TestRunDeptry": ["tests.unit.deps.test_detection_deptry", "TestRunDeptry"],
    "TestRunDetect": ["tests.unit.test_infra_workspace_main", "TestRunDetect"],
    "TestRunFix": ["tests.unit.docs.main_tests", "TestRunFix"],
    "TestRunGenerate": ["tests.unit.docs.main_commands_tests", "TestRunGenerate"],
    "TestRunGo": ["tests.unit.check.extended_runners_go_tests", "TestRunGo"],
    "TestRunLint": ["tests.unit.github.main_tests", "TestRunLint"],
    "TestRunMake": ["tests.unit.release.orchestrator_helpers_tests", "TestRunMake"],
    "TestRunMarkdown": [
        "tests.unit.check.extended_runners_extra_tests",
        "TestRunMarkdown",
    ],
    "TestRunMigrate": ["tests.unit.test_infra_workspace_main", "TestRunMigrate"],
    "TestRunMypy": ["tests.unit.check.extended_runners_tests", "TestRunMypy"],
    "TestRunMypyStubHints": [
        "tests.unit.deps.test_detection_typings",
        "TestRunMypyStubHints",
    ],
    "TestRunOrchestrate": [
        "tests.unit.test_infra_workspace_main",
        "TestRunOrchestrate",
    ],
    "TestRunPipCheck": ["tests.unit.deps.test_detection_pip_check", "TestRunPipCheck"],
    "TestRunPr": ["tests.unit.github.main_tests", "TestRunPr"],
    "TestRunPrWorkspace": [
        "tests.unit.github.main_dispatch_tests",
        "TestRunPrWorkspace",
    ],
    "TestRunProjectsBehavior": [
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsBehavior",
    ],
    "TestRunProjectsReports": [
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsReports",
    ],
    "TestRunProjectsValidation": [
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsValidation",
    ],
    "TestRunPyrefly": ["tests.unit.check.extended_runners_tests", "TestRunPyrefly"],
    "TestRunPyright": [
        "tests.unit.check.extended_runners_extra_tests",
        "TestRunPyright",
    ],
    "TestRunRuffFix": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestRunRuffFix",
    ],
    "TestRunRuffFormat": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestRunRuffFormat",
    ],
    "TestRunRuffLint": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestRunRuffLint",
    ],
    "TestRunSingleProject": [
        "tests.unit.check.extended_run_projects_tests",
        "TestRunSingleProject",
    ],
    "TestRunSync": ["tests.unit.test_infra_workspace_main", "TestRunSync"],
    "TestRunValidate": ["tests.unit.docs.main_commands_tests", "TestRunValidate"],
    "TestRunWorkflows": ["tests.unit.github.main_tests", "TestRunWorkflows"],
    "TestSafeLoadYaml": [
        "tests.unit.validate.skill_validator_tests",
        "TestSafeLoadYaml",
    ],
    "TestSafetyCheckpoint": [
        "tests.unit._utilities.test_safety",
        "TestSafetyCheckpoint",
    ],
    "TestSafetyRollback": ["tests.unit._utilities.test_safety", "TestSafetyRollback"],
    "TestScaffoldProjectCreatesSrcModules": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesSrcModules",
    ],
    "TestScaffoldProjectCreatesTestsModules": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesTestsModules",
    ],
    "TestScaffoldProjectIdempotency": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectIdempotency",
    ],
    "TestScaffoldProjectNoop": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectNoop",
    ],
    "TestScanAstPublicDefs": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestScanAstPublicDefs",
    ],
    "TestScanModels": ["tests.unit._utilities.test_scanning", "TestScanModels"],
    "TestScannerCore": ["tests.unit.validate.scanner_tests", "TestScannerCore"],
    "TestScannerHelpers": ["tests.unit.validate.scanner_tests", "TestScannerHelpers"],
    "TestScannerMultiFile": [
        "tests.unit.validate.scanner_tests",
        "TestScannerMultiFile",
    ],
    "TestSelectedProjectNames": [
        "tests.unit.docs.shared_iter_tests",
        "TestSelectedProjectNames",
    ],
    "TestShouldBubbleUp": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestShouldBubbleUp",
    ],
    "TestShouldUseColor": [
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseColor",
    ],
    "TestShouldUseUnicode": [
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseUnicode",
    ],
    "TestSkillValidatorAstGrepCount": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorAstGrepCount",
    ],
    "TestSkillValidatorCore": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorCore",
    ],
    "TestSkillValidatorRenderTemplate": [
        "tests.unit.validate.skill_validator_tests",
        "TestSkillValidatorRenderTemplate",
    ],
    "TestStringList": ["tests.unit.validate.skill_validator_tests", "TestStringList"],
    "TestStubChainAnalyze": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainAnalyze",
    ],
    "TestStubChainCore": ["tests.unit.validate.stub_chain_tests", "TestStubChainCore"],
    "TestStubChainDiscoverProjects": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainDiscoverProjects",
    ],
    "TestStubChainIsInternal": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainIsInternal",
    ],
    "TestStubChainStubExists": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainStubExists",
    ],
    "TestStubChainValidate": [
        "tests.unit.validate.stub_chain_tests",
        "TestStubChainValidate",
    ],
    "TestSubcommandMapping": ["tests.unit.deps.test_main", "TestSubcommandMapping"],
    "TestSync": ["tests.unit.deps.test_internal_sync_sync", "TestSync"],
    "TestSyncMethodEdgeCases": [
        "tests.unit.deps.test_internal_sync_sync_edge",
        "TestSyncMethodEdgeCases",
    ],
    "TestSyncMethodEdgeCasesMore": [
        "tests.unit.deps.test_internal_sync_sync_edge_more",
        "TestSyncMethodEdgeCasesMore",
    ],
    "TestSyncOne": ["tests.unit.deps.test_extra_paths_manager", "TestSyncOne"],
    "TestSynthesizedRepoMap": [
        "tests.unit.deps.test_internal_sync_resolve",
        "TestSynthesizedRepoMap",
    ],
    "TestToInfraValue": ["tests.unit.deps.test_detection_models", "TestToInfraValue"],
    "TestUpdateChangelog": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestUpdateChangelog",
    ],
    "TestValidateCore": ["tests.unit.docs.validator_tests", "TestValidateCore"],
    "TestValidateGitRefEdgeCases": [
        "tests.unit.deps.test_internal_sync_validation",
        "TestValidateGitRefEdgeCases",
    ],
    "TestValidateReport": ["tests.unit.docs.validator_tests", "TestValidateReport"],
    "TestValidateScope": [
        "tests.unit.docs.validator_internals_tests",
        "TestValidateScope",
    ],
    "TestVersionFiles": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestVersionFiles",
    ],
    "TestViolationPattern": [
        "tests.unit.codegen.census_models_tests",
        "TestViolationPattern",
    ],
    "TestWorkspaceCheckCLI": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestWorkspaceCheckCLI",
    ],
    "TestWorkspaceCheckerBuildGateResult": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerBuildGateResult",
    ],
    "TestWorkspaceCheckerCollectMarkdownFiles": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerCollectMarkdownFiles",
    ],
    "TestWorkspaceCheckerDirsWithPy": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerDirsWithPy",
    ],
    "TestWorkspaceCheckerErrorSummary": [
        "tests.unit.check.extended_models_tests",
        "TestWorkspaceCheckerErrorSummary",
    ],
    "TestWorkspaceCheckerExecute": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExecute",
    ],
    "TestWorkspaceCheckerExistingCheckDirs": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExistingCheckDirs",
    ],
    "TestWorkspaceCheckerInitOSError": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitOSError",
    ],
    "TestWorkspaceCheckerInitialization": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitialization",
    ],
    "TestWorkspaceCheckerMarkdownReport": [
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReport",
    ],
    "TestWorkspaceCheckerMarkdownReportEdgeCases": [
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReportEdgeCases",
    ],
    "TestWorkspaceCheckerParseGateCSV": [
        "tests.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerParseGateCSV",
    ],
    "TestWorkspaceCheckerResolveGates": [
        "tests.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerResolveGates",
    ],
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": [
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    ],
    "TestWorkspaceCheckerRunBandit": [
        "tests.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunBandit",
    ],
    "TestWorkspaceCheckerRunCommand": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunCommand",
    ],
    "TestWorkspaceCheckerRunGo": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunGo",
    ],
    "TestWorkspaceCheckerRunMarkdown": [
        "tests.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunMarkdown",
    ],
    "TestWorkspaceCheckerRunMypy": [
        "tests.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunMypy",
    ],
    "TestWorkspaceCheckerRunPyright": [
        "tests.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunPyright",
    ],
    "TestWorkspaceCheckerSARIFReport": [
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReport",
    ],
    "TestWorkspaceCheckerSARIFReportEdgeCases": [
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReportEdgeCases",
    ],
    "TestWorkspaceRoot": [
        "tests.unit.test_infra_maintenance_python_version",
        "TestWorkspaceRoot",
    ],
    "TestWorkspaceRootFromEnv": [
        "tests.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromEnv",
    ],
    "TestWorkspaceRootFromParents": [
        "tests.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromParents",
    ],
    "TestWriteJson": ["tests.unit.docs.shared_write_tests", "TestWriteJson"],
    "TestWriteMarkdown": ["tests.unit.docs.shared_write_tests", "TestWriteMarkdown"],
    "WorkspaceFactory": ["tests.workspace_factory", "WorkspaceFactory"],
    "WorkspaceScenario": ["tests.scenarios", "WorkspaceScenario"],
    "WorkspaceScenarios": ["tests.scenarios", "WorkspaceScenarios"],
    "auditor": ["tests.unit.docs.auditor_tests", "auditor"],
    "basemk": ["tests.unit.basemk", ""],
    "builder": ["tests.unit.docs.builder_tests", "builder"],
    "c": ["tests.constants", "FlextInfraTestConstants"],
    "census": ["tests.unit.codegen.census_tests", "census"],
    "check": ["tests.unit.check", ""],
    "codegen": ["tests.unit.codegen", ""],
    "container": ["tests.unit.container", ""],
    "create_check_project_iter_stub": [
        "tests.unit.check._shared_fixtures",
        "create_check_project_iter_stub",
    ],
    "create_check_project_stub": [
        "tests.unit.check._shared_fixtures",
        "create_check_project_stub",
    ],
    "create_checker_project": [
        "tests.unit.check._shared_fixtures",
        "create_checker_project",
    ],
    "create_fake_run_projects": [
        "tests.unit.check._shared_fixtures",
        "create_fake_run_projects",
    ],
    "create_fake_run_raw": ["tests.unit.check._shared_fixtures", "create_fake_run_raw"],
    "create_gate_execution": [
        "tests.unit.check._shared_fixtures",
        "create_gate_execution",
    ],
    "d": ["flext_tests", "d"],
    "deps": ["tests.unit.deps", ""],
    "detector": ["tests.unit.test_infra_workspace_detector", "detector"],
    "discovery": ["tests.unit.discovery", ""],
    "doc": ["tests.unit.deps.test_modernizer_helpers", "doc"],
    "docs": ["tests.unit.docs", ""],
    "e": ["flext_tests", "e"],
    "engine": ["tests.refactor.test_rope_project", "engine"],
    "extract_dep_name": ["tests.unit.deps.test_path_sync_helpers", "extract_dep_name"],
    "fake_workspace": ["tests.refactor.test_rope_project", "fake_workspace"],
    "fixer": ["tests.unit.docs.fixer_internals_tests", "fixer"],
    "gen": ["tests.unit.docs.generator_internals_tests", "gen"],
    "git_repo": ["tests.unit.test_infra_git", "git_repo"],
    "github": ["tests.unit.github", ""],
    "h": ["flext_tests", "h"],
    "io": ["tests.unit.io", ""],
    "is_external": ["tests.unit.docs.auditor_tests", "is_external"],
    "m": ["tests.models", "FlextInfraTestModels"],
    "main": ["tests.unit.github.main_integration_tests", "main"],
    "make_cmd_result": ["tests.unit.check._stubs", "make_cmd_result"],
    "make_gate_exec": ["tests.unit.check._stubs", "make_gate_exec"],
    "make_issue": ["tests.unit.check._stubs", "make_issue"],
    "make_project": ["tests.unit.check._stubs", "make_project"],
    "normalize_link": ["tests.unit.docs.auditor_tests", "normalize_link"],
    "orchestrator": ["tests.unit.test_infra_workspace_orchestrator", "orchestrator"],
    "p": ["tests.protocols", "FlextInfraTestProtocols"],
    "patch_gate_run": ["tests.unit.check._shared_fixtures", "patch_gate_run"],
    "patch_python_dir_detection": [
        "tests.unit.check._shared_fixtures",
        "patch_python_dir_detection",
    ],
    "pyright_content": ["tests.unit.deps.test_extra_paths_sync", "pyright_content"],
    "r": ["flext_tests", "r"],
    "real_docs_project": ["tests.fixtures", "real_docs_project"],
    "real_git_repo": ["tests.fixtures_git", "real_git_repo"],
    "real_makefile_project": ["tests.fixtures", "real_makefile_project"],
    "real_python_package": ["tests.fixtures", "real_python_package"],
    "real_toml_project": ["tests.fixtures", "real_toml_project"],
    "real_workspace": ["tests.fixtures", "real_workspace"],
    "refactor": ["tests.refactor", ""],
    "release": ["tests.unit.release", ""],
    "rewrite_dep_paths": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "rewrite_dep_paths",
    ],
    "run_command_failure_check": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ],
    "runner": ["tests.unit.test_infra_subprocess_core", "runner"],
    "s": ["flext_tests", "s"],
    "service": ["tests.unit.test_infra_versioning", "service"],
    "should_skip_target": ["tests.unit.docs.auditor_tests", "should_skip_target"],
    "svc": ["tests.unit.test_infra_workspace_sync", "svc"],
    "t": ["tests.typings", "FlextInfraTestTypes"],
    "test_all_three_capabilities_in_one_pass": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_all_three_capabilities_in_one_pass",
    ],
    "test_array": ["tests.unit.deps.test_modernizer_helpers", "test_array"],
    "test_as_string_list": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_as_string_list",
    ],
    "test_as_string_list_toml_item": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_as_string_list_toml_item",
    ],
    "test_atomic_write_fail": [
        "tests.unit.test_infra_workspace_sync",
        "test_atomic_write_fail",
    ],
    "test_atomic_write_ok": [
        "tests.unit.test_infra_workspace_sync",
        "test_atomic_write_ok",
    ],
    "test_basemk_build_config_with_none": [
        "tests.unit.basemk.test_main",
        "test_basemk_build_config_with_none",
    ],
    "test_basemk_build_config_with_project_name": [
        "tests.unit.basemk.test_main",
        "test_basemk_build_config_with_project_name",
    ],
    "test_basemk_cli_generate_to_file": [
        "tests.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_file",
    ],
    "test_basemk_cli_generate_to_stdout": [
        "tests.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_stdout",
    ],
    "test_basemk_engine_execute_calls_render_all": [
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_execute_calls_render_all",
    ],
    "test_basemk_engine_render_all_handles_template_error": [
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_handles_template_error",
    ],
    "test_basemk_engine_render_all_returns_string": [
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_returns_string",
    ],
    "test_basemk_engine_render_all_with_valid_config": [
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_with_valid_config",
    ],
    "test_basemk_main_ensures_structlog_configured": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_ensures_structlog_configured",
    ],
    "test_basemk_main_output_to_stdout": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_output_to_stdout",
    ],
    "test_basemk_main_with_generate_command": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_generate_command",
    ],
    "test_basemk_main_with_generation_failure": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_generation_failure",
    ],
    "test_basemk_main_with_help": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_help",
    ],
    "test_basemk_main_with_invalid_command": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_invalid_command",
    ],
    "test_basemk_main_with_no_command": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_no_command",
    ],
    "test_basemk_main_with_none_argv": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_none_argv",
    ],
    "test_basemk_main_with_output_file": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_output_file",
    ],
    "test_basemk_main_with_project_name": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_project_name",
    ],
    "test_basemk_main_with_write_failure": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_write_failure",
    ],
    "test_build_impact_map_extracts_rename_entries": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_rename_entries",
    ],
    "test_build_impact_map_extracts_signature_entries": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_signature_entries",
    ],
    "test_bump_version_invalid": [
        "tests.unit.test_infra_versioning",
        "test_bump_version_invalid",
    ],
    "test_bump_version_result_type": [
        "tests.unit.test_infra_versioning",
        "test_bump_version_result_type",
    ],
    "test_bump_version_valid": [
        "tests.unit.test_infra_versioning",
        "test_bump_version_valid",
    ],
    "test_canonical_dev_dependencies": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_canonical_dev_dependencies",
    ],
    "test_capture_cases": [
        "tests.unit.test_infra_subprocess_core",
        "test_capture_cases",
    ],
    "test_check_main_executes_real_cli": [
        "tests.unit.check.main_tests",
        "test_check_main_executes_real_cli",
    ],
    "test_class_reconstructor_reorders_each_contiguous_method_block": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_each_contiguous_method_block",
    ],
    "test_class_reconstructor_reorders_methods_by_config": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_methods_by_config",
    ],
    "test_class_reconstructor_skips_interleaved_non_method_members": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_skips_interleaved_non_method_members",
    ],
    "test_cli_result_by_project_root": [
        "tests.unit.test_infra_workspace_sync",
        "test_cli_result_by_project_root",
    ],
    "test_codegen_dir_returns_all_exports": [
        "tests.unit.codegen.init_tests",
        "test_codegen_dir_returns_all_exports",
    ],
    "test_codegen_getattr_raises_attribute_error": [
        "tests.unit.codegen.init_tests",
        "test_codegen_getattr_raises_attribute_error",
    ],
    "test_codegen_init_getattr_raises_attribute_error": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "test_codegen_init_getattr_raises_attribute_error",
    ],
    "test_codegen_lazy_imports_work": [
        "tests.unit.codegen.init_tests",
        "test_codegen_lazy_imports_work",
    ],
    "test_codegen_pipeline_end_to_end": [
        "tests.unit.codegen.pipeline_tests",
        "test_codegen_pipeline_end_to_end",
    ],
    "test_consolidate_groups_phase_apply_removes_old_groups": [
        "tests.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_removes_old_groups",
    ],
    "test_consolidate_groups_phase_apply_with_empty_poetry_group": [
        "tests.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    ],
    "test_converts_multiple_aliases": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_multiple_aliases",
    ],
    "test_converts_typealias_to_pep695": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_typealias_to_pep695",
    ],
    "test_current_workspace_version": [
        "tests.unit.test_infra_versioning",
        "test_current_workspace_version",
    ],
    "test_dedupe_specs": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_dedupe_specs",
    ],
    "test_dep_name": ["tests.unit.deps.test_modernizer_helpers", "test_dep_name"],
    "test_detect_mode_with_nonexistent_path": [
        "tests.unit.deps.test_path_sync_init",
        "test_detect_mode_with_nonexistent_path",
    ],
    "test_detect_mode_with_path_object": [
        "tests.unit.deps.test_path_sync_init",
        "test_detect_mode_with_path_object",
    ],
    "test_detects_attribute_base_class": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_attribute_base_class",
    ],
    "test_detects_basemodel_in_non_model_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_basemodel_in_non_model_file",
    ],
    "test_detects_missing_local_composition_base": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_detects_missing_local_composition_base",
    ],
    "test_detects_multiple_models": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_multiple_models",
    ],
    "test_detects_only_wrong_alias_in_mixed_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_only_wrong_alias_in_mixed_import",
    ],
    "test_detects_same_project_submodule_alias_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_same_project_submodule_alias_import",
    ],
    "test_detects_wrong_source_m_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_m_import",
    ],
    "test_detects_wrong_source_u_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_u_import",
    ],
    "test_engine_always_enables_class_nesting_file_rule": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_engine_always_enables_class_nesting_file_rule",
    ],
    "test_ensure_future_annotations_after_docstring": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_after_docstring",
    ],
    "test_ensure_future_annotations_moves_existing_import_to_top": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_moves_existing_import_to_top",
    ],
    "test_ensure_pyrefly_config_phase_apply_errors": [
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_errors",
    ],
    "test_ensure_pyrefly_config_phase_apply_ignore_errors": [
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    ],
    "test_ensure_pyrefly_config_phase_apply_python_version": [
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_python_version",
    ],
    "test_ensure_pyrefly_config_phase_apply_search_path": [
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_search_path",
    ],
    "test_ensure_pytest_config_phase_apply_markers": [
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_markers",
    ],
    "test_ensure_pytest_config_phase_apply_minversion": [
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_minversion",
    ],
    "test_ensure_pytest_config_phase_apply_python_classes": [
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_python_classes",
    ],
    "test_ensure_table": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_ensure_table",
    ],
    "test_extract_dep_name": [
        "tests.unit.deps.test_path_sync_helpers",
        "test_extract_dep_name",
    ],
    "test_extract_requirement_name": [
        "tests.unit.deps.test_path_sync_helpers",
        "test_extract_requirement_name",
    ],
    "test_files_modified_tracks_affected_files": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_files_modified_tracks_affected_files",
    ],
    "test_fix_pyrefly_config_main_executes_real_cli_help": [
        "tests.unit.check.fix_pyrefly_config_tests",
        "test_fix_pyrefly_config_main_executes_real_cli_help",
    ],
    "test_flexcore_excluded_from_run": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_flexcore_excluded_from_run",
    ],
    "test_flext_infra_pyproject_modernizer_find_pyproject_files": [
        "tests.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    ],
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml": [
        "tests.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    ],
    "test_generator_execute_returns_generated_content": [
        "tests.unit.basemk.test_generator",
        "test_generator_execute_returns_generated_content",
    ],
    "test_generator_fails_for_invalid_make_syntax": [
        "tests.unit.basemk.test_engine",
        "test_generator_fails_for_invalid_make_syntax",
    ],
    "test_generator_generate_propagates_render_failure": [
        "tests.unit.basemk.test_generator",
        "test_generator_generate_propagates_render_failure",
    ],
    "test_generator_generate_with_basemk_config_object": [
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_basemk_config_object",
    ],
    "test_generator_generate_with_dict_config": [
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_dict_config",
    ],
    "test_generator_generate_with_invalid_dict_config": [
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_invalid_dict_config",
    ],
    "test_generator_generate_with_none_config_uses_default": [
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_none_config_uses_default",
    ],
    "test_generator_initializes_with_custom_engine": [
        "tests.unit.basemk.test_generator",
        "test_generator_initializes_with_custom_engine",
    ],
    "test_generator_initializes_with_default_engine": [
        "tests.unit.basemk.test_generator",
        "test_generator_initializes_with_default_engine",
    ],
    "test_generator_normalize_config_with_basemk_config": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_basemk_config",
    ],
    "test_generator_normalize_config_with_dict": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_dict",
    ],
    "test_generator_normalize_config_with_invalid_dict": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_invalid_dict",
    ],
    "test_generator_normalize_config_with_none": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_none",
    ],
    "test_generator_renders_with_config_override": [
        "tests.unit.basemk.test_engine",
        "test_generator_renders_with_config_override",
    ],
    "test_generator_validate_generated_output_handles_oserror": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_validate_generated_output_handles_oserror",
    ],
    "test_generator_write_creates_parent_directories": [
        "tests.unit.basemk.test_generator",
        "test_generator_write_creates_parent_directories",
    ],
    "test_generator_write_fails_without_output_or_stream": [
        "tests.unit.basemk.test_generator",
        "test_generator_write_fails_without_output_or_stream",
    ],
    "test_generator_write_handles_file_permission_error": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_write_handles_file_permission_error",
    ],
    "test_generator_write_saves_output_file": [
        "tests.unit.basemk.test_engine",
        "test_generator_write_saves_output_file",
    ],
    "test_generator_write_to_file": [
        "tests.unit.basemk.test_generator",
        "test_generator_write_to_file",
    ],
    "test_generator_write_to_stream": [
        "tests.unit.basemk.test_generator",
        "test_generator_write_to_stream",
    ],
    "test_generator_write_to_stream_handles_oserror": [
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_write_to_stream_handles_oserror",
    ],
    "test_gitignore_entry_scenarios": [
        "tests.unit.test_infra_workspace_sync",
        "test_gitignore_entry_scenarios",
    ],
    "test_gitignore_sync_failure": [
        "tests.unit.test_infra_workspace_sync",
        "test_gitignore_sync_failure",
    ],
    "test_gitignore_write_failure": [
        "tests.unit.test_infra_workspace_sync",
        "test_gitignore_write_failure",
    ],
    "test_helpers_alias_is_reachable_helpers": [
        "tests.unit.deps.test_path_sync_helpers",
        "test_helpers_alias_is_reachable_helpers",
    ],
    "test_helpers_alias_is_reachable_project_obj": [
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_helpers_alias_is_reachable_project_obj",
    ],
    "test_import_alias_detector_skips_facade_and_subclass_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_facade_and_subclass_files",
    ],
    "test_import_alias_detector_skips_nested_private_and_as_renames": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_nested_private_and_as_renames",
    ],
    "test_import_alias_detector_skips_private_and_class_imports": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_private_and_class_imports",
    ],
    "test_import_modernizer_adds_c_when_existing_c_is_aliased": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    ],
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    ],
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    ],
    "test_import_modernizer_partial_import_keeps_unmapped_symbols": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    ],
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    ],
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    ],
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    ],
    "test_import_modernizer_updates_aliased_symbol_usage": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_updates_aliased_symbol_usage",
    ],
    "test_in_context_typevar_not_flagged": [
        "tests.unit.codegen.autofix_tests",
        "test_in_context_typevar_not_flagged",
    ],
    "test_inject_comments_phase_apply_banner": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_banner",
    ],
    "test_inject_comments_phase_apply_broken_group_section": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_broken_group_section",
    ],
    "test_inject_comments_phase_apply_markers": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_markers",
    ],
    "test_inject_comments_phase_apply_with_optional_dependencies_dev": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    ],
    "test_inject_comments_phase_deduplicates_family_markers": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_deduplicates_family_markers",
    ],
    "test_inject_comments_phase_marks_pytest_and_coverage_subtables": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_marks_pytest_and_coverage_subtables",
    ],
    "test_inject_comments_phase_removes_auto_banner_and_auto_marker": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_removes_auto_banner_and_auto_marker",
    ],
    "test_inject_comments_phase_repositions_marker_before_section": [
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_repositions_marker_before_section",
    ],
    "test_injects_t_import_when_needed": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_injects_t_import_when_needed",
    ],
    "test_lazy_import_rule_hoists_import_to_module_level": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_hoists_import_to_module_level",
    ],
    "test_lazy_import_rule_uses_fix_action_for_hoist": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_uses_fix_action_for_hoist",
    ],
    "test_legacy_import_bypass_collapses_to_primary_import": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_import_bypass_collapses_to_primary_import",
    ],
    "test_legacy_rule_uses_fix_action_remove_for_aliases": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_rule_uses_fix_action_remove_for_aliases",
    ],
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_function_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_function_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_non_passthrough_is_not_inlined": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_non_passthrough_is_not_inlined",
    ],
    "test_main_all_groups_defined": [
        "tests.unit.test_infra_main",
        "test_main_all_groups_defined",
    ],
    "test_main_analyze_violations_is_read_only": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_is_read_only",
    ],
    "test_main_analyze_violations_writes_json_report": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_writes_json_report",
    ],
    "test_main_discovery_failure": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_discovery_failure",
    ],
    "test_main_group_modules_are_valid": [
        "tests.unit.test_infra_main",
        "test_main_group_modules_are_valid",
    ],
    "test_main_help_flag_returns_zero": [
        "tests.unit.test_infra_main",
        "test_main_help_flag_returns_zero",
    ],
    "test_main_no_changes_needed": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_no_changes_needed",
    ],
    "test_main_project_invalid_toml": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_invalid_toml",
    ],
    "test_main_project_no_name": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_no_name",
    ],
    "test_main_project_non_string_name": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_non_string_name",
    ],
    "test_main_project_obj_not_dict_first_loop": [
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_first_loop",
    ],
    "test_main_project_obj_not_dict_second_loop": [
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_second_loop",
    ],
    "test_main_returns_error_when_no_args": [
        "tests.unit.test_infra_main",
        "test_main_returns_error_when_no_args",
    ],
    "test_main_success_modes": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_main_success_modes",
    ],
    "test_main_sync_failure": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_main_sync_failure",
    ],
    "test_main_unknown_group_returns_error": [
        "tests.unit.test_infra_main",
        "test_main_unknown_group_returns_error",
    ],
    "test_main_with_changes_and_dry_run": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_and_dry_run",
    ],
    "test_main_with_changes_no_dry_run": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_no_dry_run",
    ],
    "test_migrate_makefile_not_found_non_dry_run": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_makefile_not_found_non_dry_run",
    ],
    "test_migrate_pyproject_flext_core_non_dry_run": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_pyproject_flext_core_non_dry_run",
    ],
    "test_migrator_apply_updates_project_files": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_apply_updates_project_files",
    ],
    "test_migrator_discovery_failure": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_discovery_failure",
    ],
    "test_migrator_dry_run_reports_changes_without_writes": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_dry_run_reports_changes_without_writes",
    ],
    "test_migrator_execute_returns_failure": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_execute_returns_failure",
    ],
    "test_migrator_flext_core_dry_run": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_dry_run",
    ],
    "test_migrator_flext_core_project_skipped": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_flext_core_project_skipped",
    ],
    "test_migrator_gitignore_already_normalized_dry_run": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_gitignore_already_normalized_dry_run",
    ],
    "test_migrator_handles_missing_pyproject_gracefully": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_handles_missing_pyproject_gracefully",
    ],
    "test_migrator_has_flext_core_dependency_in_poetry": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_in_poetry",
    ],
    "test_migrator_has_flext_core_dependency_poetry_deps_not_table": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_deps_not_table",
    ],
    "test_migrator_has_flext_core_dependency_poetry_table_missing": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrator_has_flext_core_dependency_poetry_table_missing",
    ],
    "test_migrator_makefile_not_found_dry_run": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_not_found_dry_run",
    ],
    "test_migrator_makefile_read_failure": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_makefile_read_failure",
    ],
    "test_migrator_no_changes_needed": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_no_changes_needed",
    ],
    "test_migrator_preserves_custom_makefile_content": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_preserves_custom_makefile_content",
    ],
    "test_migrator_pyproject_not_found_dry_run": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_migrator_pyproject_not_found_dry_run",
    ],
    "test_migrator_workspace_root_not_exists": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_not_exists",
    ],
    "test_migrator_workspace_root_project_detection": [
        "tests.unit.test_infra_workspace_migrator",
        "test_migrator_workspace_root_project_detection",
    ],
    "test_mro_checker_keeps_external_attribute_base": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_checker_keeps_external_attribute_base",
    ],
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    ],
    "test_namespace_rewriter_keeps_contextual_alias_subset": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_keeps_contextual_alias_subset",
    ],
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_only_rewrites_runtime_alias_imports",
    ],
    "test_namespace_rewriter_skips_facade_and_subclass_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_facade_and_subclass_files",
    ],
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates",
    ],
    "test_no_duplicate_t_import_when_t_from_project_package": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_no_duplicate_t_import_when_t_from_project_package",
    ],
    "test_non_pydantic_class_not_flagged": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_non_pydantic_class_not_flagged",
    ],
    "test_noop_clean_module": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_noop_clean_module",
    ],
    "test_parse_semver_invalid": [
        "tests.unit.test_infra_versioning",
        "test_parse_semver_invalid",
    ],
    "test_parse_semver_result_type": [
        "tests.unit.test_infra_versioning",
        "test_parse_semver_result_type",
    ],
    "test_parse_semver_valid": [
        "tests.unit.test_infra_versioning",
        "test_parse_semver_valid",
    ],
    "test_pattern_rule_converts_dict_annotations_to_mapping": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_converts_dict_annotations_to_mapping",
    ],
    "test_pattern_rule_keeps_dict_param_when_copy_used": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_copy_used",
    ],
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    ],
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    ],
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    ],
    "test_pattern_rule_removes_configured_redundant_casts": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_configured_redundant_casts",
    ],
    "test_pattern_rule_removes_nested_type_object_cast_chain": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_nested_type_object_cast_chain",
    ],
    "test_pattern_rule_skips_overload_signatures": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_skips_overload_signatures",
    ],
    "test_preserves_annotated_in_function_params": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_annotated_in_function_params",
    ],
    "test_preserves_non_matching_unions": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_non_matching_unions",
    ],
    "test_preserves_override_in_method": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_override_in_method",
    ],
    "test_preserves_protocol_and_runtime_checkable": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_protocol_and_runtime_checkable",
    ],
    "test_preserves_type_checking_import": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_type_checking_import",
    ],
    "test_preserves_typealias_import_when_class_level_usage_exists": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_typealias_import_when_class_level_usage_exists",
    ],
    "test_preserves_used_imports_when_import_precedes_usage": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_imports_when_import_precedes_usage",
    ],
    "test_preserves_used_typing_imports": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_typing_imports",
    ],
    "test_project_dev_groups": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups",
    ],
    "test_project_dev_groups_missing_sections": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups_missing_sections",
    ],
    "test_project_without_alias_facade_has_no_violation": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_project_without_alias_facade_has_no_violation",
    ],
    "test_project_without_src_returns_empty": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_project_without_src_returns_empty",
    ],
    "test_read_project_metadata_preserves_pep621_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_pep621_dependency_order",
    ],
    "test_read_project_metadata_preserves_poetry_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_poetry_dependency_order",
    ],
    "test_refactor_files_skips_non_python_inputs": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_files_skips_non_python_inputs",
    ],
    "test_refactor_project_integrates_safety_manager": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "test_refactor_project_integrates_safety_manager",
    ],
    "test_refactor_project_scans_tests_and_scripts_dirs": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_project_scans_tests_and_scripts_dirs",
    ],
    "test_removes_all_imports_when_none_used_import_first": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_imports_when_none_used_import_first",
    ],
    "test_removes_all_unused_typing_imports": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_unused_typing_imports",
    ],
    "test_removes_dead_typealias_import": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_dead_typealias_import",
    ],
    "test_removes_typealias_import_only_when_all_usages_converted": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_typealias_import_only_when_all_usages_converted",
    ],
    "test_removes_unused_preserves_used_when_import_precedes_usage": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_unused_preserves_used_when_import_precedes_usage",
    ],
    "test_render_all_generates_large_makefile": [
        "tests.unit.basemk.test_engine",
        "test_render_all_generates_large_makefile",
    ],
    "test_render_all_has_no_scripts_path_references": [
        "tests.unit.basemk.test_engine",
        "test_render_all_has_no_scripts_path_references",
    ],
    "test_replace_project_version": [
        "tests.unit.test_infra_versioning",
        "test_replace_project_version",
    ],
    "test_replaces_container_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_container_union",
    ],
    "test_replaces_numeric_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_numeric_union",
    ],
    "test_replaces_primitives_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_primitives_union",
    ],
    "test_replaces_scalar_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_scalar_union",
    ],
    "test_resolve_gates_maps_type_alias": [
        "tests.unit.check.cli_tests",
        "test_resolve_gates_maps_type_alias",
    ],
    "test_rewrite_dep_paths_dry_run": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_dry_run",
    ],
    "test_rewrite_dep_paths_read_failure": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_read_failure",
    ],
    "test_rewrite_dep_paths_with_internal_names": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_internal_names",
    ],
    "test_rewrite_dep_paths_with_no_deps": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_no_deps",
    ],
    "test_rewrite_pep621_invalid_path_dep_regex": [
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_invalid_path_dep_regex",
    ],
    "test_rewrite_pep621_no_project_table": [
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_no_project_table",
    ],
    "test_rewrite_pep621_non_string_item": [
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_non_string_item",
    ],
    "test_rewrite_poetry_no_poetry_table": [
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_poetry_table",
    ],
    "test_rewrite_poetry_no_tool_table": [
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_tool_table",
    ],
    "test_rewrite_poetry_with_non_dict_value": [
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_with_non_dict_value",
    ],
    "test_rewriter_adds_missing_base_and_formats": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_rewriter_adds_missing_base_and_formats",
    ],
    "test_rewriter_namespace_source_is_idempotent_with_ruff": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_namespace_source_is_idempotent_with_ruff",
    ],
    "test_rewriter_preserves_non_alias_symbols": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_preserves_non_alias_symbols",
    ],
    "test_rewriter_splits_mixed_imports_correctly": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_splits_mixed_imports_correctly",
    ],
    "test_rope_find_occurrences_import": [
        "tests.refactor.test_rope_stubs",
        "test_rope_find_occurrences_import",
    ],
    "test_rope_import": ["tests.refactor.test_rope_stubs", "test_rope_import"],
    "test_rope_rename_import": [
        "tests.refactor.test_rope_stubs",
        "test_rope_rename_import",
    ],
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    ],
    "test_rule_dispatch_fails_on_unknown_rule_mapping": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_unknown_rule_mapping",
    ],
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    ],
    "test_rule_dispatch_prefers_fix_action_metadata": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_prefers_fix_action_metadata",
    ],
    "test_run_cases": ["tests.unit.test_infra_subprocess_core", "test_run_cases"],
    "test_run_cli_run_returns_one_for_fail": [
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_one_for_fail",
    ],
    "test_run_cli_run_returns_two_for_error": [
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_two_for_error",
    ],
    "test_run_cli_run_returns_zero_for_pass": [
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_zero_for_pass",
    ],
    "test_run_cli_with_fail_fast_flag": [
        "tests.unit.check.cli_tests",
        "test_run_cli_with_fail_fast_flag",
    ],
    "test_run_cli_with_multiple_projects": [
        "tests.unit.check.cli_tests",
        "test_run_cli_with_multiple_projects",
    ],
    "test_run_raw_cases": [
        "tests.unit.test_infra_subprocess_core",
        "test_run_raw_cases",
    ],
    "test_signature_propagation_removes_and_adds_keywords": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_removes_and_adds_keywords",
    ],
    "test_signature_propagation_renames_call_keyword": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_renames_call_keyword",
    ],
    "test_skips_definition_files": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_definition_files",
    ],
    "test_skips_facade_declaration_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_facade_declaration_files",
    ],
    "test_skips_import_as_rename": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_import_as_rename",
    ],
    "test_skips_init_file": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_init_file",
    ],
    "test_skips_models_directory": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_directory",
    ],
    "test_skips_models_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_file",
    ],
    "test_skips_non_alias_symbols": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_non_alias_symbols",
    ],
    "test_skips_non_facade_files": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_non_facade_files",
    ],
    "test_skips_private_candidate_classes": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_private_candidate_classes",
    ],
    "test_skips_private_class": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_private_class",
    ],
    "test_skips_protected_files": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_protected_files",
    ],
    "test_skips_r_alias_universal_exception": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_r_alias_universal_exception",
    ],
    "test_skips_same_project_private_submodule": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_private_submodule",
    ],
    "test_skips_same_project_submodule_class_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_submodule_class_import",
    ],
    "test_skips_settings_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_settings_file",
    ],
    "test_skips_union_with_none": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_union_with_none",
    ],
    "test_skips_when_candidate_is_already_in_facade_bases": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_when_candidate_is_already_in_facade_bases",
    ],
    "test_standalone_final_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_final_detected_as_fixable",
    ],
    "test_standalone_typealias_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typealias_detected_as_fixable",
    ],
    "test_standalone_typevar_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typevar_detected_as_fixable",
    ],
    "test_string_zero_return_value": [
        "tests.unit.deps.test_main_dispatch",
        "test_string_zero_return_value",
    ],
    "test_symbol_propagation_keeps_alias_reference_when_asname_used": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    ],
    "test_symbol_propagation_renames_import_and_local_references": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_renames_import_and_local_references",
    ],
    "test_symbol_propagation_updates_mro_base_references": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_updates_mro_base_references",
    ],
    "test_sync_basemk_scenarios": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_basemk_scenarios",
    ],
    "test_sync_error_scenarios": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_error_scenarios",
    ],
    "test_sync_extra_paths_missing_root_pyproject": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_missing_root_pyproject",
    ],
    "test_sync_extra_paths_success_modes": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_success_modes",
    ],
    "test_sync_extra_paths_sync_failure": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_sync_failure",
    ],
    "test_sync_one_edge_cases": [
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_one_edge_cases",
    ],
    "test_sync_root_validation": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_root_validation",
    ],
    "test_sync_success_scenarios": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_success_scenarios",
    ],
    "test_syntax_error_files_skipped": [
        "tests.unit.codegen.autofix_tests",
        "test_syntax_error_files_skipped",
    ],
    "test_target_path": ["tests.unit.deps.test_path_sync_helpers", "test_target_path"],
    "test_typealias_conversion_preserves_used_typing_siblings": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_typealias_conversion_preserves_used_typing_siblings",
    ],
    "test_unwrap_item": ["tests.unit.deps.test_modernizer_helpers", "test_unwrap_item"],
    "test_unwrap_item_toml_item": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_unwrap_item_toml_item",
    ],
    "test_violation_analysis_counts_massive_patterns": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analysis_counts_massive_patterns",
    ],
    "test_violation_analyzer_skips_non_utf8_files": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analyzer_skips_non_utf8_files",
    ],
    "test_workspace_check_main_returns_error_without_projects": [
        "tests.unit.check.workspace_check_tests",
        "test_workspace_check_main_returns_error_without_projects",
    ],
    "test_workspace_cli_migrate_command": [
        "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_command",
    ],
    "test_workspace_cli_migrate_output_contains_summary": [
        "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_migrate_output_contains_summary",
    ],
    "test_workspace_migrator_error_handling_on_invalid_workspace": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_error_handling_on_invalid_workspace",
    ],
    "test_workspace_migrator_makefile_not_found_dry_run": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_not_found_dry_run",
    ],
    "test_workspace_migrator_makefile_read_error": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_makefile_read_error",
    ],
    "test_workspace_migrator_pyproject_write_error": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_workspace_migrator_pyproject_write_error",
    ],
    "test_workspace_root_doc_construction": [
        "tests.unit.deps.test_modernizer_workspace",
        "test_workspace_root_doc_construction",
    ],
    "test_workspace_root_fallback": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_workspace_root_fallback",
    ],
    "u": ["tests.utilities", "FlextInfraTestUtilities"],
    "unit": ["tests.unit", ""],
    "v": ["tests.unit.validate.basemk_validator_tests", "v"],
    "validate": ["tests.unit.validate", ""],
    "validator": ["tests.unit.docs.validator_internals_tests", "validator"],
    "workspace_root": ["tests.unit.release.orchestrator_tests", "workspace_root"],
    "x": ["flext_tests", "x"],
}

__all__ = [
    "ANSI_RE",
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "BrokenScenario",
    "CheckProjectStub",
    "DependencyScenario",
    "DependencyScenarios",
    "EmptyScenario",
    "EngineSafetyStub",
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "FlextInfraCodegenTestProjectFactory",
    "FlextInfraTestConstants",
    "FlextInfraTestHelpers",
    "FlextInfraTestModels",
    "FlextInfraTestProtocols",
    "FlextInfraTestTypes",
    "FlextInfraTestUtilities",
    "FullScenario",
    "GateClass",
    "GitScenario",
    "GitScenarios",
    "MinimalScenario",
    "RealGitService",
    "RealSubprocessRunner",
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
    "SubprocessScenario",
    "SubprocessScenarios",
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
    "TestHookCallOrdering",
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
    "TestInitRopeProject",
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
    "TestRopeHooks",
    "TestRopeProjectProperty",
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
    "TestScaffoldProjectCreatesSrcModules",
    "TestScaffoldProjectCreatesTestsModules",
    "TestScaffoldProjectIdempotency",
    "TestScaffoldProjectNoop",
    "TestScanAstPublicDefs",
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
    "WorkspaceFactory",
    "WorkspaceScenario",
    "WorkspaceScenarios",
    "auditor",
    "basemk",
    "builder",
    "c",
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
    "d",
    "deps",
    "detector",
    "discovery",
    "doc",
    "docs",
    "e",
    "engine",
    "extract_dep_name",
    "fake_workspace",
    "fixer",
    "gen",
    "git_repo",
    "github",
    "h",
    "io",
    "is_external",
    "m",
    "main",
    "make_cmd_result",
    "make_gate_exec",
    "make_issue",
    "make_project",
    "normalize_link",
    "orchestrator",
    "p",
    "patch_gate_run",
    "patch_python_dir_detection",
    "pyright_content",
    "r",
    "real_docs_project",
    "real_git_repo",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "refactor",
    "release",
    "rewrite_dep_paths",
    "run_command_failure_check",
    "runner",
    "s",
    "service",
    "should_skip_target",
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
    "test_inject_comments_phase_deduplicates_family_markers",
    "test_inject_comments_phase_marks_pytest_and_coverage_subtables",
    "test_inject_comments_phase_removes_auto_banner_and_auto_marker",
    "test_inject_comments_phase_repositions_marker_before_section",
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
    "test_rope_find_occurrences_import",
    "test_rope_import",
    "test_rope_rename_import",
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
    "u",
    "unit",
    "v",
    "validate",
    "validator",
    "workspace_root",
    "x",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
