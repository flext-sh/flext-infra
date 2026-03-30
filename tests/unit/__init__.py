# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
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
        test_infra_constants_core as test_infra_constants_core,
        test_infra_constants_extra as test_infra_constants_extra,
        test_infra_git as test_infra_git,
        test_infra_init_lazy_core as test_infra_init_lazy_core,
        test_infra_init_lazy_submodules as test_infra_init_lazy_submodules,
        test_infra_main as test_infra_main,
        test_infra_maintenance_cli as test_infra_maintenance_cli,
        test_infra_maintenance_init as test_infra_maintenance_init,
        test_infra_maintenance_main as test_infra_maintenance_main,
        test_infra_maintenance_python_version as test_infra_maintenance_python_version,
        test_infra_paths as test_infra_paths,
        test_infra_patterns_core as test_infra_patterns_core,
        test_infra_patterns_extra as test_infra_patterns_extra,
        test_infra_protocols as test_infra_protocols,
        test_infra_reporting_core as test_infra_reporting_core,
        test_infra_reporting_extra as test_infra_reporting_extra,
        test_infra_selection as test_infra_selection,
        test_infra_subprocess_core as test_infra_subprocess_core,
        test_infra_subprocess_extra as test_infra_subprocess_extra,
        test_infra_toml_io as test_infra_toml_io,
        test_infra_typings as test_infra_typings,
        test_infra_utilities as test_infra_utilities,
        test_infra_version_core as test_infra_version_core,
        test_infra_version_extra as test_infra_version_extra,
        test_infra_versioning as test_infra_versioning,
        test_infra_workspace_cli as test_infra_workspace_cli,
        test_infra_workspace_detector as test_infra_workspace_detector,
        test_infra_workspace_init as test_infra_workspace_init,
        test_infra_workspace_main as test_infra_workspace_main,
        test_infra_workspace_migrator as test_infra_workspace_migrator,
        test_infra_workspace_migrator_deps as test_infra_workspace_migrator_deps,
        test_infra_workspace_migrator_dryrun as test_infra_workspace_migrator_dryrun,
        test_infra_workspace_migrator_errors as test_infra_workspace_migrator_errors,
        test_infra_workspace_migrator_internal as test_infra_workspace_migrator_internal,
        test_infra_workspace_migrator_pyproject as test_infra_workspace_migrator_pyproject,
        test_infra_workspace_orchestrator as test_infra_workspace_orchestrator,
        test_infra_workspace_sync as test_infra_workspace_sync,
        validate as validate,
    )
    from tests.unit._utilities import (
        test_discovery_consolidated as test_discovery_consolidated,
        test_formatting as test_formatting,
        test_iteration as test_iteration,
        test_parsing as test_parsing,
        test_rope_hooks as test_rope_hooks,
        test_safety as test_safety,
        test_scanning as test_scanning,
    )
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects as TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles as TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles as TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots as TestDiscoveryProjectRoots,
    )
    from tests.unit._utilities.test_formatting import (
        TestFormattingRunRuffFix as TestFormattingRunRuffFix,
    )
    from tests.unit._utilities.test_iteration import (
        TestIterWorkspacePythonModules as TestIterWorkspacePythonModules,
    )
    from tests.unit._utilities.test_parsing import (
        TestParsingModuleAst as TestParsingModuleAst,
        TestParsingModuleCst as TestParsingModuleCst,
    )
    from tests.unit._utilities.test_rope_hooks import (
        test_run_rope_post_hooks_applies_mro_migration as test_run_rope_post_hooks_applies_mro_migration,
        test_run_rope_post_hooks_dry_run_is_non_mutating as test_run_rope_post_hooks_dry_run_is_non_mutating,
    )
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint as TestSafetyCheckpoint,
        TestSafetyRollback as TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels as TestScanModels
    from tests.unit.basemk import (
        test_engine as test_engine,
        test_generator as test_generator,
        test_generator_edge_cases as test_generator_edge_cases,
        test_init as test_init,
        test_main as test_main,
        test_make_contract as test_make_contract,
    )
    from tests.unit.basemk.test_engine import (
        basemk_main as basemk_main,
        test_basemk_cli_generate_to_file as test_basemk_cli_generate_to_file,
        test_basemk_cli_generate_to_stdout as test_basemk_cli_generate_to_stdout,
        test_basemk_engine_execute_calls_render_all as test_basemk_engine_execute_calls_render_all,
        test_basemk_engine_render_all_handles_template_error as test_basemk_engine_render_all_handles_template_error,
        test_basemk_engine_render_all_returns_string as test_basemk_engine_render_all_returns_string,
        test_basemk_engine_render_all_with_valid_config as test_basemk_engine_render_all_with_valid_config,
        test_generator_fails_for_invalid_make_syntax as test_generator_fails_for_invalid_make_syntax,
        test_generator_renders_with_config_override as test_generator_renders_with_config_override,
        test_generator_write_saves_output_file as test_generator_write_saves_output_file,
        test_render_all_declares_and_documents_runtime_options as test_render_all_declares_and_documents_runtime_options,
        test_render_all_exposes_canonical_public_targets as test_render_all_exposes_canonical_public_targets,
        test_render_all_generates_large_makefile as test_render_all_generates_large_makefile,
        test_render_all_has_no_scripts_path_references as test_render_all_has_no_scripts_path_references,
    )
    from tests.unit.basemk.test_generator import (
        test_generator_execute_returns_generated_content as test_generator_execute_returns_generated_content,
        test_generator_generate_propagates_render_failure as test_generator_generate_propagates_render_failure,
        test_generator_generate_with_basemk_config_object as test_generator_generate_with_basemk_config_object,
        test_generator_generate_with_dict_config as test_generator_generate_with_dict_config,
        test_generator_generate_with_invalid_dict_config as test_generator_generate_with_invalid_dict_config,
        test_generator_generate_with_none_config_uses_default as test_generator_generate_with_none_config_uses_default,
        test_generator_initializes_with_custom_engine as test_generator_initializes_with_custom_engine,
        test_generator_initializes_with_default_engine as test_generator_initializes_with_default_engine,
        test_generator_write_creates_parent_directories as test_generator_write_creates_parent_directories,
        test_generator_write_fails_without_output_or_stream as test_generator_write_fails_without_output_or_stream,
        test_generator_write_to_file as test_generator_write_to_file,
        test_generator_write_to_stream as test_generator_write_to_stream,
    )
    from tests.unit.basemk.test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config as test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict as test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict as test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none as test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror as test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error as test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror as test_generator_write_to_stream_handles_oserror,
    )
    from tests.unit.basemk.test_init import TestFlextInfraBaseMk as TestFlextInfraBaseMk
    from tests.unit.basemk.test_main import (
        test_basemk_build_config_with_none as test_basemk_build_config_with_none,
        test_basemk_build_config_with_project_name as test_basemk_build_config_with_project_name,
        test_basemk_main_ensures_structlog_configured as test_basemk_main_ensures_structlog_configured,
        test_basemk_main_output_to_stdout as test_basemk_main_output_to_stdout,
        test_basemk_main_rejects_apply_flag as test_basemk_main_rejects_apply_flag,
        test_basemk_main_with_generate_command as test_basemk_main_with_generate_command,
        test_basemk_main_with_generation_failure as test_basemk_main_with_generation_failure,
        test_basemk_main_with_help as test_basemk_main_with_help,
        test_basemk_main_with_invalid_command as test_basemk_main_with_invalid_command,
        test_basemk_main_with_no_command as test_basemk_main_with_no_command,
        test_basemk_main_with_none_argv as test_basemk_main_with_none_argv,
        test_basemk_main_with_output_file as test_basemk_main_with_output_file,
        test_basemk_main_with_project_name as test_basemk_main_with_project_name,
        test_basemk_main_with_write_failure as test_basemk_main_with_write_failure,
    )
    from tests.unit.basemk.test_make_contract import (
        test_make_boot_works_without_existing_venv_in_workspace_mode as test_make_boot_works_without_existing_venv_in_workspace_mode,
        test_make_check_fast_path_check_only_suppresses_fix_writes as test_make_check_fast_path_check_only_suppresses_fix_writes,
        test_make_check_file_scope_rejects_unsupported_gates as test_make_check_file_scope_rejects_unsupported_gates,
        test_make_check_file_scope_runs_mypy as test_make_check_file_scope_runs_mypy,
        test_make_check_file_scope_unsets_python_path_env as test_make_check_file_scope_unsets_python_path_env,
        test_make_check_full_run_forwards_fix_and_tool_args as test_make_check_full_run_forwards_fix_and_tool_args,
        test_make_check_full_run_unsets_python_path_env as test_make_check_full_run_unsets_python_path_env,
        test_make_help_lists_supported_options as test_make_help_lists_supported_options,
        test_rendered_base_mk_declares_cli_group_roots as test_rendered_base_mk_declares_cli_group_roots,
        test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight as test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight,
    )
    from tests.unit.check import (
        cli_tests as cli_tests,
        extended_cli_entry_tests as extended_cli_entry_tests,
        extended_config_fixer_errors_tests as extended_config_fixer_errors_tests,
        extended_config_fixer_tests as extended_config_fixer_tests,
        extended_error_reporting_tests as extended_error_reporting_tests,
        extended_gate_bandit_markdown_tests as extended_gate_bandit_markdown_tests,
        extended_gate_go_cmd_tests as extended_gate_go_cmd_tests,
        extended_gate_mypy_pyright_tests as extended_gate_mypy_pyright_tests,
        extended_models_tests as extended_models_tests,
        extended_project_runners_tests as extended_project_runners_tests,
        extended_projects_tests as extended_projects_tests,
        extended_reports_tests as extended_reports_tests,
        extended_resolve_gates_tests as extended_resolve_gates_tests,
        extended_run_projects_tests as extended_run_projects_tests,
        extended_runners_extra_tests as extended_runners_extra_tests,
        extended_runners_go_tests as extended_runners_go_tests,
        extended_runners_ruff_tests as extended_runners_ruff_tests,
        extended_runners_tests as extended_runners_tests,
        extended_workspace_init_tests as extended_workspace_init_tests,
        fix_pyrefly_config_tests as fix_pyrefly_config_tests,
        init_tests as init_tests,
        main_tests as main_tests,
        pyrefly_tests as pyrefly_tests,
        workspace_check_tests as workspace_check_tests,
        workspace_tests as workspace_tests,
    )
    from tests.unit.check._shared_fixtures import (
        RunProjectsMock as RunProjectsMock,
        create_check_project_iter_stub as create_check_project_iter_stub,
        create_check_project_stub as create_check_project_stub,
        create_checker_project as create_checker_project,
        create_fake_run_projects as create_fake_run_projects,
        create_fake_run_raw as create_fake_run_raw,
        create_gate_execution as create_gate_execution,
        patch_gate_run as patch_gate_run,
        patch_python_dir_detection as patch_python_dir_detection,
    )
    from tests.unit.check._stubs import (
        Spy as Spy,
        make_cmd_result as make_cmd_result,
        make_gate_exec as make_gate_exec,
        make_issue as make_issue,
        make_project as make_project,
    )
    from tests.unit.check.cli_tests import (
        test_resolve_gates_maps_type_alias as test_resolve_gates_maps_type_alias,
        test_run_cli_rejects_fix_flags_for_run as test_run_cli_rejects_fix_flags_for_run,
        test_run_cli_run_forwards_fix_and_tool_args as test_run_cli_run_forwards_fix_and_tool_args,
        test_run_cli_run_returns_one_for_fail as test_run_cli_run_returns_one_for_fail,
        test_run_cli_run_returns_two_for_error as test_run_cli_run_returns_two_for_error,
        test_run_cli_run_returns_zero_for_pass as test_run_cli_run_returns_zero_for_pass,
        test_run_cli_with_fail_fast_flag as test_run_cli_with_fail_fast_flag,
        test_run_cli_with_multiple_projects as test_run_cli_with_multiple_projects,
    )
    from tests.unit.check.extended_cli_entry_tests import (
        TestCheckMainEntryPoint as TestCheckMainEntryPoint,
        TestFixPyrelfyCLI as TestFixPyrelfyCLI,
        TestRunCLIExtended as TestRunCLIExtended,
        TestWorkspaceCheckCLI as TestWorkspaceCheckCLI,
    )
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPathResolution as TestConfigFixerPathResolution,
        TestConfigFixerRunMethods as TestConfigFixerRunMethods,
        TestConfigFixerRunWithVerbose as TestConfigFixerRunWithVerbose,
        TestProcessFileReadError as TestProcessFileReadError,
    )
    from tests.unit.check.extended_config_fixer_tests import (
        TestConfigFixerEnsureProjectExcludes as TestConfigFixerEnsureProjectExcludes,
        TestConfigFixerExecute as TestConfigFixerExecute,
        TestConfigFixerFindPyprojectFiles as TestConfigFixerFindPyprojectFiles,
        TestConfigFixerFixSearchPaths as TestConfigFixerFixSearchPaths,
        TestConfigFixerProcessFile as TestConfigFixerProcessFile,
        TestConfigFixerRemoveIgnoreSubConfig as TestConfigFixerRemoveIgnoreSubConfig,
        TestConfigFixerRun as TestConfigFixerRun,
        TestConfigFixerToArray as TestConfigFixerToArray,
    )
    from tests.unit.check.extended_error_reporting_tests import (
        TestErrorReporting as TestErrorReporting,
        TestGoFmtEmptyLinesInOutput as TestGoFmtEmptyLinesInOutput,
        TestMarkdownReportEmptyGates as TestMarkdownReportEmptyGates,
        TestMypyEmptyLinesInOutput as TestMypyEmptyLinesInOutput,
        TestRuffFormatDuplicateFiles as TestRuffFormatDuplicateFiles,
    )
    from tests.unit.check.extended_gate_bandit_markdown_tests import (
        TestWorkspaceCheckerRunBandit as TestWorkspaceCheckerRunBandit,
        TestWorkspaceCheckerRunMarkdown as TestWorkspaceCheckerRunMarkdown,
    )
    from tests.unit.check.extended_gate_go_cmd_tests import (
        TestWorkspaceCheckerCollectMarkdownFiles as TestWorkspaceCheckerCollectMarkdownFiles,
        TestWorkspaceCheckerRunCommand as TestWorkspaceCheckerRunCommand,
        TestWorkspaceCheckerRunGo as TestWorkspaceCheckerRunGo,
        run_command_failure_check as run_command_failure_check,
    )
    from tests.unit.check.extended_gate_mypy_pyright_tests import (
        TestWorkspaceCheckerRunMypy as TestWorkspaceCheckerRunMypy,
        TestWorkspaceCheckerRunPyright as TestWorkspaceCheckerRunPyright,
    )
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted as TestCheckIssueFormatted,
        TestProjectResultProperties as TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import (
        TestJsonWriteFailure as TestJsonWriteFailure,
    )
    from tests.unit.check.extended_projects_tests import (
        TestCheckProjectRunners as TestCheckProjectRunners,
        TestLintAndFormatPublicMethods as TestLintAndFormatPublicMethods,
    )
    from tests.unit.check.extended_reports_tests import (
        TestMarkdownReportSkipsEmptyGates as TestMarkdownReportSkipsEmptyGates,
        TestMarkdownReportWithErrors as TestMarkdownReportWithErrors,
        TestWorkspaceCheckerMarkdownReport as TestWorkspaceCheckerMarkdownReport,
        TestWorkspaceCheckerMarkdownReportEdgeCases as TestWorkspaceCheckerMarkdownReportEdgeCases,
        TestWorkspaceCheckerSARIFReport as TestWorkspaceCheckerSARIFReport,
        TestWorkspaceCheckerSARIFReportEdgeCases as TestWorkspaceCheckerSARIFReportEdgeCases,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV as TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.check.extended_run_projects_tests import (
        CheckProjectStub as CheckProjectStub,
        TestRunProjectFixMode as TestRunProjectFixMode,
        TestRunProjectsBehavior as TestRunProjectsBehavior,
        TestRunProjectsReports as TestRunProjectsReports,
        TestRunProjectsValidation as TestRunProjectsValidation,
        TestRunSingleProject as TestRunSingleProject,
    )
    from tests.unit.check.extended_runners_extra_tests import (
        GateClass as GateClass,
        TestRunBandit as TestRunBandit,
        TestRunMarkdown as TestRunMarkdown,
        TestRunPyright as TestRunPyright,
    )
    from tests.unit.check.extended_runners_go_tests import (
        RunCallable as RunCallable,
        TestRunGo as TestRunGo,
    )
    from tests.unit.check.extended_runners_ruff_tests import (
        TestCollectMarkdownFiles as TestCollectMarkdownFiles,
        TestRunCommand as TestRunCommand,
        TestRunPyrightArgs as TestRunPyrightArgs,
        TestRunRuffFormat as TestRunRuffFormat,
        TestRunRuffLint as TestRunRuffLint,
    )
    from tests.unit.check.extended_runners_tests import (
        TestRunMypy as TestRunMypy,
        TestRunPyrefly as TestRunPyrefly,
    )
    from tests.unit.check.extended_workspace_init_tests import (
        TestWorkspaceCheckerBuildGateResult as TestWorkspaceCheckerBuildGateResult,
        TestWorkspaceCheckerDirsWithPy as TestWorkspaceCheckerDirsWithPy,
        TestWorkspaceCheckerExecute as TestWorkspaceCheckerExecute,
        TestWorkspaceCheckerExistingCheckDirs as TestWorkspaceCheckerExistingCheckDirs,
        TestWorkspaceCheckerInitialization as TestWorkspaceCheckerInitialization,
        TestWorkspaceCheckerInitOSError as TestWorkspaceCheckerInitOSError,
        TestWorkspaceCheckerResolveWorkspaceRootFallback as TestWorkspaceCheckerResolveWorkspaceRootFallback,
    )
    from tests.unit.check.fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help as test_fix_pyrefly_config_main_executes_real_cli_help,
    )
    from tests.unit.check.init_tests import TestFlextInfraCheck as TestFlextInfraCheck
    from tests.unit.check.main_tests import (
        test_check_main_executes_real_cli as test_check_main_executes_real_cli,
    )
    from tests.unit.check.pyrefly_tests import (
        TestFlextInfraConfigFixer as TestFlextInfraConfigFixer,
    )
    from tests.unit.check.workspace_check_tests import (
        test_workspace_check_main_returns_error_without_projects as test_workspace_check_main_returns_error_without_projects,
    )
    from tests.unit.check.workspace_tests import (
        TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
    )
    from tests.unit.codegen import (
        autofix_tests as autofix_tests,
        autofix_workspace_tests as autofix_workspace_tests,
        census_models_tests as census_models_tests,
        census_tests as census_tests,
        constants_quality_gate_tests as constants_quality_gate_tests,
        lazy_init_generation_tests as lazy_init_generation_tests,
        lazy_init_helpers_tests as lazy_init_helpers_tests,
        lazy_init_process_tests as lazy_init_process_tests,
        lazy_init_service_tests as lazy_init_service_tests,
        lazy_init_tests as lazy_init_tests,
        lazy_init_transforms_tests as lazy_init_transforms_tests,
        pipeline_tests as pipeline_tests,
        scaffolder_naming_tests as scaffolder_naming_tests,
        scaffolder_tests as scaffolder_tests,
    )
    from tests.unit.codegen._project_factory import (
        FlextInfraCodegenTestProjectFactory as FlextInfraCodegenTestProjectFactory,
    )
    from tests.unit.codegen.autofix_tests import (
        test_in_context_typevar_not_flagged as test_in_context_typevar_not_flagged,
        test_standalone_final_detected_as_fixable as test_standalone_final_detected_as_fixable,
        test_standalone_typealias_detected_as_fixable as test_standalone_typealias_detected_as_fixable,
        test_standalone_typevar_detected_as_fixable as test_standalone_typevar_detected_as_fixable,
        test_syntax_error_files_skipped as test_syntax_error_files_skipped,
    )
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files as test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run as test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty as test_project_without_src_returns_empty,
    )
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel as TestCensusReportModel,
        TestCensusViolationModel as TestCensusViolationModel,
        TestExcludedProjects as TestExcludedProjects,
        TestViolationPattern as TestViolationPattern,
    )
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification as TestFixabilityClassification,
        TestParseViolationInvalid as TestParseViolationInvalid,
        TestParseViolationValid as TestParseViolationValid,
        census as census,
    )
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch as TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict as TestConstantsQualityGateVerdict,
    )
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports as test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error as test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work as test_codegen_lazy_imports_work,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile as TestGenerateFile,
        TestGenerateTypeChecking as TestGenerateTypeChecking,
        TestResolveAliases as TestResolveAliases,
        TestRunRuffFix as TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error as test_codegen_init_getattr_raises_attribute_error,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex as TestBuildSiblingExportIndex,
        TestExtractExports as TestExtractExports,
        TestInferPackage as TestInferPackage,
        TestReadExistingDocstring as TestReadExistingDocstring,
    )
    from tests.unit.codegen.lazy_init_process_tests import (
        TestProcessDirectory as TestProcessDirectory,
    )
    from tests.unit.codegen.lazy_init_service_tests import (
        TestFlextInfraCodegenLazyInit as TestFlextInfraCodegenLazyInit,
    )
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned as TestAllDirectoriesScanned,
        TestCheckOnlyMode as TestCheckOnlyMode,
        TestEdgeCases as TestEdgeCases,
        TestExcludedDirectories as TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractInlineConstants as TestExtractInlineConstants,
        TestExtractVersionExports as TestExtractVersionExports,
        TestMergeChildExports as TestMergeChildExports,
        TestScanAstPublicDefs as TestScanAstPublicDefs,
        TestShouldBubbleUp as TestShouldBubbleUp,
    )
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit as TestHandleLazyInit,
        TestMainCommandDispatch as TestMainCommandDispatch,
        TestMainEntryPoint as TestMainEntryPoint,
    )
    from tests.unit.codegen.pipeline_tests import (
        test_codegen_pipeline_end_to_end as test_codegen_pipeline_end_to_end,
    )
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
    )
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules as TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules as TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency as TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop as TestScaffoldProjectNoop,
    )
    from tests.unit.container import test_infra_container as test_infra_container
    from tests.unit.container.test_infra_container import (
        TestInfraContainerFunctions as TestInfraContainerFunctions,
        TestInfraMroPattern as TestInfraMroPattern,
        TestInfraServiceRetrieval as TestInfraServiceRetrieval,
    )
    from tests.unit.deps import (
        test_detection_classify as test_detection_classify,
        test_detection_deptry as test_detection_deptry,
        test_detection_discover as test_detection_discover,
        test_detection_models as test_detection_models,
        test_detection_pip_check as test_detection_pip_check,
        test_detection_typings as test_detection_typings,
        test_detection_typings_flow as test_detection_typings_flow,
        test_detection_uncovered as test_detection_uncovered,
        test_detector_detect as test_detector_detect,
        test_detector_detect_failures as test_detector_detect_failures,
        test_detector_init as test_detector_init,
        test_detector_main as test_detector_main,
        test_detector_models as test_detector_models,
        test_detector_report as test_detector_report,
        test_detector_report_flags as test_detector_report_flags,
        test_extra_paths_manager as test_extra_paths_manager,
        test_extra_paths_pep621 as test_extra_paths_pep621,
        test_extra_paths_sync as test_extra_paths_sync,
        test_internal_sync_discovery as test_internal_sync_discovery,
        test_internal_sync_discovery_edge as test_internal_sync_discovery_edge,
        test_internal_sync_main as test_internal_sync_main,
        test_internal_sync_resolve as test_internal_sync_resolve,
        test_internal_sync_sync as test_internal_sync_sync,
        test_internal_sync_sync_edge as test_internal_sync_sync_edge,
        test_internal_sync_sync_edge_more as test_internal_sync_sync_edge_more,
        test_internal_sync_update as test_internal_sync_update,
        test_internal_sync_update_checkout_edge as test_internal_sync_update_checkout_edge,
        test_internal_sync_validation as test_internal_sync_validation,
        test_internal_sync_workspace as test_internal_sync_workspace,
        test_main_dispatch as test_main_dispatch,
        test_modernizer_comments as test_modernizer_comments,
        test_modernizer_consolidate as test_modernizer_consolidate,
        test_modernizer_coverage as test_modernizer_coverage,
        test_modernizer_helpers as test_modernizer_helpers,
        test_modernizer_main as test_modernizer_main,
        test_modernizer_main_extra as test_modernizer_main_extra,
        test_modernizer_pyrefly as test_modernizer_pyrefly,
        test_modernizer_pyright as test_modernizer_pyright,
        test_modernizer_pytest as test_modernizer_pytest,
        test_modernizer_workspace as test_modernizer_workspace,
        test_path_sync_helpers as test_path_sync_helpers,
        test_path_sync_init as test_path_sync_init,
        test_path_sync_main as test_path_sync_main,
        test_path_sync_main_edges as test_path_sync_main_edges,
        test_path_sync_main_more as test_path_sync_main_more,
        test_path_sync_main_project_obj as test_path_sync_main_project_obj,
        test_path_sync_rewrite_deps as test_path_sync_rewrite_deps,
        test_path_sync_rewrite_pep621 as test_path_sync_rewrite_pep621,
        test_path_sync_rewrite_poetry as test_path_sync_rewrite_poetry,
    )
    from tests.unit.deps.test_detection_classify import (
        TestBuildProjectReport as TestBuildProjectReport,
        TestClassifyIssues as TestClassifyIssues,
    )
    from tests.unit.deps.test_detection_deptry import TestRunDeptry as TestRunDeptry
    from tests.unit.deps.test_detection_models import (
        TestFlextInfraDependencyDetectionModels as TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService as TestFlextInfraDependencyDetectionService,
        TestToInfraValue as TestToInfraValue,
    )
    from tests.unit.deps.test_detection_pip_check import (
        TestRunPipCheck as TestRunPipCheck,
    )
    from tests.unit.deps.test_detection_typings import (
        TestLoadDependencyLimits as TestLoadDependencyLimits,
        TestRunMypyStubHints as TestRunMypyStubHints,
    )
    from tests.unit.deps.test_detection_typings_flow import (
        TestModuleAndTypingsFlow as TestModuleAndTypingsFlow,
    )
    from tests.unit.deps.test_detection_uncovered import (
        TestDetectionUncoveredLines as TestDetectionUncoveredLines,
    )
    from tests.unit.deps.test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect as TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )
    from tests.unit.deps.test_detector_detect_failures import (
        TestDetectorRunFailures as TestDetectorRunFailures,
    )
    from tests.unit.deps.test_detector_init import (
        TestFlextInfraRuntimeDevDependencyDetectorInit as TestFlextInfraRuntimeDevDependencyDetectorInit,
    )
    from tests.unit.deps.test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings as TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction as TestMainFunction,
    )
    from tests.unit.deps.test_detector_models import (
        TestFlextInfraDependencyDetectorModels as TestFlextInfraDependencyDetectorModels,
    )
    from tests.unit.deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport as TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )
    from tests.unit.deps.test_detector_report_flags import (
        TestDetectorReportFlags as TestDetectorReportFlags,
    )
    from tests.unit.deps.test_extra_paths_manager import (
        TestConstants as TestConstants,
        TestFlextInfraExtraPathsManager as TestFlextInfraExtraPathsManager,
        TestGetDepPaths as TestGetDepPaths,
        TestSyncOne as TestSyncOne,
        test_pyrefly_search_paths_include_workspace_declared_dev_dependencies as test_pyrefly_search_paths_include_workspace_declared_dev_dependencies,
    )
    from tests.unit.deps.test_extra_paths_pep621 import (
        TestPathDepPathsPep621 as TestPathDepPathsPep621,
        TestPathDepPathsPoetry as TestPathDepPathsPoetry,
    )
    from tests.unit.deps.test_extra_paths_sync import (
        pyright_content as pyright_content,
        test_main_success_modes as test_main_success_modes,
        test_main_sync_failure as test_main_sync_failure,
        test_sync_extra_paths_missing_root_pyproject as test_sync_extra_paths_missing_root_pyproject,
        test_sync_extra_paths_success_modes as test_sync_extra_paths_success_modes,
        test_sync_extra_paths_sync_failure as test_sync_extra_paths_sync_failure,
        test_sync_one_edge_cases as test_sync_one_edge_cases,
    )
    from tests.unit.deps.test_init import TestFlextInfraDeps as TestFlextInfraDeps
    from tests.unit.deps.test_internal_sync_discovery import (
        TestCollectInternalDeps as TestCollectInternalDeps,
        TestParseGitmodules as TestParseGitmodules,
        TestParseRepoMap as TestParseRepoMap,
    )
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestCollectInternalDepsEdgeCases as TestCollectInternalDepsEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_resolve import (
        TestInferOwnerFromOrigin as TestInferOwnerFromOrigin,
        TestResolveRef as TestResolveRef,
        TestSynthesizedRepoMap as TestSynthesizedRepoMap,
    )
    from tests.unit.deps.test_internal_sync_sync import TestSync as TestSync
    from tests.unit.deps.test_internal_sync_sync_edge import (
        TestSyncMethodEdgeCases as TestSyncMethodEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestSyncMethodEdgeCasesMore as TestSyncMethodEdgeCasesMore,
    )
    from tests.unit.deps.test_internal_sync_update import (
        TestEnsureCheckout as TestEnsureCheckout,
        TestEnsureSymlink as TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases as TestEnsureSymlinkEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases as TestEnsureCheckoutEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService as TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep as TestIsInternalPathDep,
        TestIsRelativeTo as TestIsRelativeTo,
        TestOwnerFromRemoteUrl as TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases as TestValidateGitRefEdgeCases,
    )
    from tests.unit.deps.test_internal_sync_workspace import (
        TestIsWorkspaceMode as TestIsWorkspaceMode,
        TestWorkspaceRootFromEnv as TestWorkspaceRootFromEnv,
        TestWorkspaceRootFromParents as TestWorkspaceRootFromParents,
    )
    from tests.unit.deps.test_main import (
        TestMainHelpAndErrors as TestMainHelpAndErrors,
        TestMainReturnValues as TestMainReturnValues,
        TestSubcommandMapping as TestSubcommandMapping,
    )
    from tests.unit.deps.test_main_dispatch import (
        TestMainDelegation as TestMainDelegation,
        TestMainExceptionHandling as TestMainExceptionHandling,
        TestMainModuleImport as TestMainModuleImport,
        TestMainSubcommandDispatch as TestMainSubcommandDispatch,
        TestMainSysArgvModification as TestMainSysArgvModification,
        test_string_zero_return_value as test_string_zero_return_value,
    )
    from tests.unit.deps.test_modernizer_comments import (
        TestInjectCommentsPhase as TestInjectCommentsPhase,
        test_inject_comments_phase_apply_banner as test_inject_comments_phase_apply_banner,
        test_inject_comments_phase_apply_broken_group_section as test_inject_comments_phase_apply_broken_group_section,
        test_inject_comments_phase_apply_markers as test_inject_comments_phase_apply_markers,
        test_inject_comments_phase_apply_with_optional_dependencies_dev as test_inject_comments_phase_apply_with_optional_dependencies_dev,
        test_inject_comments_phase_deduplicates_family_markers as test_inject_comments_phase_deduplicates_family_markers,
        test_inject_comments_phase_marks_pytest_and_coverage_subtables as test_inject_comments_phase_marks_pytest_and_coverage_subtables,
        test_inject_comments_phase_removes_auto_banner_and_auto_marker as test_inject_comments_phase_removes_auto_banner_and_auto_marker,
        test_inject_comments_phase_repositions_marker_before_section as test_inject_comments_phase_repositions_marker_before_section,
    )
    from tests.unit.deps.test_modernizer_consolidate import (
        TestConsolidateGroupsPhase as TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups as test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group as test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )
    from tests.unit.deps.test_modernizer_coverage import (
        TestEnsureCoverageConfigPhase as TestEnsureCoverageConfigPhase,
    )
    from tests.unit.deps.test_modernizer_helpers import (
        doc as doc,
        test_array as test_array,
        test_as_string_list as test_as_string_list,
        test_as_string_list_toml_item as test_as_string_list_toml_item,
        test_canonical_dev_dependencies as test_canonical_dev_dependencies,
        test_declared_dependency_names_collects_all_supported_groups as test_declared_dependency_names_collects_all_supported_groups,
        test_dedupe_specs as test_dedupe_specs,
        test_dep_name as test_dep_name,
        test_ensure_table as test_ensure_table,
        test_project_dev_groups as test_project_dev_groups,
        test_project_dev_groups_missing_sections as test_project_dev_groups_missing_sections,
        test_unwrap_item as test_unwrap_item,
        test_unwrap_item_toml_item as test_unwrap_item_toml_item,
    )
    from tests.unit.deps.test_modernizer_main import (
        TestFlextInfraPyprojectModernizer as TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain as TestModernizerRunAndMain,
    )
    from tests.unit.deps.test_modernizer_main_extra import (
        TestModernizerEdgeCases as TestModernizerEdgeCases,
        TestModernizerUncoveredLines as TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files as test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml as test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase as TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors as test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors as test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version as test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path as test_ensure_pyrefly_config_phase_apply_search_path,
    )
    from tests.unit.deps.test_modernizer_pyright import (
        TestEnsurePyrightConfigPhase as TestEnsurePyrightConfigPhase,
    )
    from tests.unit.deps.test_modernizer_pytest import (
        TestEnsurePytestConfigPhase as TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers as test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion as test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes as test_ensure_pytest_config_phase_apply_python_classes,
    )
    from tests.unit.deps.test_modernizer_workspace import (
        TestParser as TestParser,
        TestReadDoc as TestReadDoc,
        test_workspace_root_doc_construction as test_workspace_root_doc_construction,
    )
    from tests.unit.deps.test_path_sync_helpers import (
        extract_dep_name as extract_dep_name,
        test_extract_dep_name as test_extract_dep_name,
        test_extract_requirement_name as test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers as test_helpers_alias_is_reachable_helpers,
        test_target_path as test_target_path,
    )
    from tests.unit.deps.test_path_sync_init import (
        TestDetectMode as TestDetectMode,
        TestFlextInfraDependencyPathSync as TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases as TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path as test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object as test_detect_mode_with_path_object,
    )
    from tests.unit.deps.test_path_sync_main_edges import (
        TestMainEdgeCases as TestMainEdgeCases,
    )
    from tests.unit.deps.test_path_sync_main_more import (
        test_main_discovery_failure as test_main_discovery_failure,
        test_main_no_changes_needed as test_main_no_changes_needed,
        test_main_project_invalid_toml as test_main_project_invalid_toml,
        test_main_project_no_name as test_main_project_no_name,
        test_main_project_non_string_name as test_main_project_non_string_name,
        test_main_with_changes_and_dry_run as test_main_with_changes_and_dry_run,
        test_main_with_changes_no_dry_run as test_main_with_changes_no_dry_run,
        test_workspace_root_fallback as test_workspace_root_fallback,
    )
    from tests.unit.deps.test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj as test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop as test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop as test_main_project_obj_not_dict_second_loop,
    )
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestRewriteDepPaths as TestRewriteDepPaths,
        rewrite_dep_paths as rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run as test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure as test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names as test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps as test_rewrite_dep_paths_with_no_deps,
    )
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestRewritePep621 as TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex as test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table as test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item as test_rewrite_pep621_non_string_item,
    )
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestRewritePoetry as TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table as test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table as test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value as test_rewrite_poetry_with_non_dict_value,
    )
    from tests.unit.discovery import (
        test_infra_discovery as test_infra_discovery,
        test_infra_discovery_edge_cases as test_infra_discovery_edge_cases,
    )
    from tests.unit.discovery.test_infra_discovery import (
        TestFlextInfraDiscoveryService as TestFlextInfraDiscoveryService,
    )
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines as TestFlextInfraDiscoveryServiceUncoveredLines,
    )
    from tests.unit.docs import (
        auditor_budgets_tests as auditor_budgets_tests,
        auditor_cli_tests as auditor_cli_tests,
        auditor_links_tests as auditor_links_tests,
        auditor_scope_tests as auditor_scope_tests,
        auditor_tests as auditor_tests,
        builder_scope_tests as builder_scope_tests,
        builder_tests as builder_tests,
        fixer_internals_tests as fixer_internals_tests,
        fixer_tests as fixer_tests,
        generator_internals_tests as generator_internals_tests,
        generator_tests as generator_tests,
        main_commands_tests as main_commands_tests,
        main_entry_tests as main_entry_tests,
        shared_iter_tests as shared_iter_tests,
        shared_tests as shared_tests,
        shared_write_tests as shared_write_tests,
        validator_internals_tests as validator_internals_tests,
        validator_tests as validator_tests,
    )
    from tests.unit.docs.auditor_budgets_tests import (
        TestLoadAuditBudgets as TestLoadAuditBudgets,
    )
    from tests.unit.docs.auditor_cli_tests import (
        TestAuditorMainCli as TestAuditorMainCli,
        TestAuditorScopeFailure as TestAuditorScopeFailure,
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
        auditor as auditor,
        is_external as is_external,
        normalize_link as normalize_link,
        should_skip_target as should_skip_target,
    )
    from tests.unit.docs.builder_scope_tests import TestBuilderScope as TestBuilderScope
    from tests.unit.docs.builder_tests import (
        TestBuilderCore as TestBuilderCore,
        builder as builder,
    )
    from tests.unit.docs.fixer_internals_tests import (
        TestFixerMaybeFixLink as TestFixerMaybeFixLink,
        TestFixerProcessFile as TestFixerProcessFile,
        TestFixerScope as TestFixerScope,
        TestFixerToc as TestFixerToc,
        fixer as fixer,
    )
    from tests.unit.docs.fixer_tests import TestFixerCore as TestFixerCore
    from tests.unit.docs.generator_internals_tests import (
        TestGeneratorHelpers as TestGeneratorHelpers,
        TestGeneratorScope as TestGeneratorScope,
        gen as gen,
    )
    from tests.unit.docs.generator_tests import TestGeneratorCore as TestGeneratorCore
    from tests.unit.docs.init_tests import TestFlextInfraDocs as TestFlextInfraDocs
    from tests.unit.docs.main_commands_tests import (
        TestRunBuild as TestRunBuild,
        TestRunGenerate as TestRunGenerate,
        TestRunValidate as TestRunValidate,
    )
    from tests.unit.docs.main_entry_tests import (
        TestMainRouting as TestMainRouting,
        TestMainWithFlags as TestMainWithFlags,
    )
    from tests.unit.docs.main_tests import (
        TestRunAudit as TestRunAudit,
        TestRunFix as TestRunFix,
    )
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles as TestIterMarkdownFiles,
        TestSelectedProjectNames as TestSelectedProjectNames,
    )
    from tests.unit.docs.shared_tests import (
        TestBuildScopes as TestBuildScopes,
        TestFlextInfraDocScope as TestFlextInfraDocScope,
    )
    from tests.unit.docs.shared_write_tests import (
        TestWriteJson as TestWriteJson,
        TestWriteMarkdown as TestWriteMarkdown,
    )
    from tests.unit.docs.validator_internals_tests import (
        TestAdrHelpers as TestAdrHelpers,
        TestMaybeWriteTodo as TestMaybeWriteTodo,
        TestValidateScope as TestValidateScope,
        validator as validator,
    )
    from tests.unit.docs.validator_tests import (
        TestValidateCore as TestValidateCore,
        TestValidateReport as TestValidateReport,
    )
    from tests.unit.github import (
        main_cli_tests as main_cli_tests,
        main_dispatch_tests as main_dispatch_tests,
        main_integration_tests as main_integration_tests,
    )
    from tests.unit.github._stubs import (
        StubCommandOutput as StubCommandOutput,
        StubJsonIo as StubJsonIo,
        StubLinter as StubLinter,
        StubPrManager as StubPrManager,
        StubProjectInfo as StubProjectInfo,
        StubReporting as StubReporting,
        StubRunner as StubRunner,
        StubSelector as StubSelector,
        StubSyncer as StubSyncer,
        StubTemplates as StubTemplates,
        StubUtilities as StubUtilities,
        StubVersioning as StubVersioning,
        StubWorkspaceManager as StubWorkspaceManager,
    )
    from tests.unit.github.main_cli_tests import (
        test_main_returns_nonzero_on_unknown as test_main_returns_nonzero_on_unknown,
        test_main_returns_zero_on_help as test_main_returns_zero_on_help,
        test_pr_workspace_accepts_repeated_project_options as test_pr_workspace_accepts_repeated_project_options,
    )
    from tests.unit.github.main_dispatch_tests import (
        TestRunPrWorkspace as TestRunPrWorkspace,
    )
    from tests.unit.github.main_integration_tests import TestMain as TestMain
    from tests.unit.github.main_tests import (
        TestRunLint as TestRunLint,
        TestRunPr as TestRunPr,
        TestRunWorkflows as TestRunWorkflows,
    )
    from tests.unit.io import (
        test_infra_json_io as test_infra_json_io,
        test_infra_output_edge_cases as test_infra_output_edge_cases,
        test_infra_output_formatting as test_infra_output_formatting,
        test_infra_terminal_detection as test_infra_terminal_detection,
    )
    from tests.unit.io.test_infra_json_io import (
        SampleModel as SampleModel,
        TestFlextInfraJsonService as TestFlextInfraJsonService,
    )
    from tests.unit.io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases as TestInfraOutputEdgeCases,
        TestInfraOutputNoColor as TestInfraOutputNoColor,
        TestMroFacadeMethods as TestMroFacadeMethods,
    )
    from tests.unit.io.test_infra_output_formatting import (
        ANSI_RE as ANSI_RE,
        TestInfraOutputHeader as TestInfraOutputHeader,
        TestInfraOutputMessages as TestInfraOutputMessages,
        TestInfraOutputProgress as TestInfraOutputProgress,
        TestInfraOutputStatus as TestInfraOutputStatus,
        TestInfraOutputSummary as TestInfraOutputSummary,
    )
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor as TestShouldUseColor,
        TestShouldUseUnicode as TestShouldUseUnicode,
    )
    from tests.unit.refactor import (
        test_infra_refactor_analysis as test_infra_refactor_analysis,
        test_infra_refactor_class_and_propagation as test_infra_refactor_class_and_propagation,
        test_infra_refactor_class_placement as test_infra_refactor_class_placement,
        test_infra_refactor_engine as test_infra_refactor_engine,
        test_infra_refactor_import_modernizer as test_infra_refactor_import_modernizer,
        test_infra_refactor_legacy_and_annotations as test_infra_refactor_legacy_and_annotations,
        test_infra_refactor_mro_completeness as test_infra_refactor_mro_completeness,
        test_infra_refactor_mro_import_rewriter as test_infra_refactor_mro_import_rewriter,
        test_infra_refactor_namespace_aliases as test_infra_refactor_namespace_aliases,
        test_infra_refactor_namespace_source as test_infra_refactor_namespace_source,
        test_infra_refactor_pattern_corrections as test_infra_refactor_pattern_corrections,
        test_infra_refactor_project_classifier as test_infra_refactor_project_classifier,
        test_infra_refactor_safety as test_infra_refactor_safety,
        test_infra_refactor_typing_unifier as test_infra_refactor_typing_unifier,
        test_main_cli as test_main_cli,
    )
    from tests.unit.refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries as test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries as test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only as test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report as test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns as test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files as test_violation_analyzer_skips_non_utf8_files,
    )
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
        test_class_reconstructor_reorders_each_contiguous_method_block as test_class_reconstructor_reorders_each_contiguous_method_block,
        test_class_reconstructor_reorders_methods_by_config as test_class_reconstructor_reorders_methods_by_config,
        test_class_reconstructor_skips_interleaved_non_method_members as test_class_reconstructor_skips_interleaved_non_method_members,
        test_mro_checker_keeps_external_attribute_base as test_mro_checker_keeps_external_attribute_base,
        test_mro_redundancy_checker_removes_nested_attribute_inheritance as test_mro_redundancy_checker_removes_nested_attribute_inheritance,
        test_signature_propagation_removes_and_adds_keywords as test_signature_propagation_removes_and_adds_keywords,
        test_signature_propagation_renames_call_keyword as test_signature_propagation_renames_call_keyword,
        test_symbol_propagation_keeps_alias_reference_when_asname_used as test_symbol_propagation_keeps_alias_reference_when_asname_used,
        test_symbol_propagation_renames_import_and_local_references as test_symbol_propagation_renames_import_and_local_references,
        test_symbol_propagation_updates_mro_base_references as test_symbol_propagation_updates_mro_base_references,
    )
    from tests.unit.refactor.test_infra_refactor_class_placement import (
        test_detects_attribute_base_class as test_detects_attribute_base_class,
        test_detects_basemodel_in_non_model_file as test_detects_basemodel_in_non_model_file,
        test_detects_multiple_models as test_detects_multiple_models,
        test_non_pydantic_class_not_flagged as test_non_pydantic_class_not_flagged,
        test_skips_models_directory as test_skips_models_directory,
        test_skips_models_file as test_skips_models_file,
        test_skips_private_class as test_skips_private_class,
        test_skips_protected_files as test_skips_protected_files,
        test_skips_settings_file as test_skips_settings_file,
    )
    from tests.unit.refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule as test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs as test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs as test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config as test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping as test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping as test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata as test_rule_dispatch_prefers_fix_action_metadata,
    )
    from tests.unit.refactor.test_infra_refactor_import_modernizer import (
        test_import_modernizer_adds_c_when_existing_c_is_aliased as test_import_modernizer_adds_c_when_existing_c_is_aliased,
        test_import_modernizer_does_not_rewrite_function_parameter_shadow as test_import_modernizer_does_not_rewrite_function_parameter_shadow,
        test_import_modernizer_does_not_rewrite_rebound_local_name_usage as test_import_modernizer_does_not_rewrite_rebound_local_name_usage,
        test_import_modernizer_partial_import_keeps_unmapped_symbols as test_import_modernizer_partial_import_keeps_unmapped_symbols,
        test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias as test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias,
        test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function as test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function,
        test_import_modernizer_skips_when_runtime_alias_name_is_blocked as test_import_modernizer_skips_when_runtime_alias_name_is_blocked,
        test_import_modernizer_updates_aliased_symbol_usage as test_import_modernizer_updates_aliased_symbol_usage,
        test_lazy_import_rule_hoists_import_to_module_level as test_lazy_import_rule_hoists_import_to_module_level,
        test_lazy_import_rule_uses_fix_action_for_hoist as test_lazy_import_rule_uses_fix_action_for_hoist,
    )
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
        test_ensure_future_annotations_after_docstring as test_ensure_future_annotations_after_docstring,
        test_ensure_future_annotations_moves_existing_import_to_top as test_ensure_future_annotations_moves_existing_import_to_top,
        test_legacy_import_bypass_collapses_to_primary_import as test_legacy_import_bypass_collapses_to_primary_import,
        test_legacy_rule_uses_fix_action_remove_for_aliases as test_legacy_rule_uses_fix_action_remove_for_aliases,
        test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias as test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias,
        test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias as test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias,
        test_legacy_wrapper_function_is_inlined_as_alias as test_legacy_wrapper_function_is_inlined_as_alias,
        test_legacy_wrapper_non_passthrough_is_not_inlined as test_legacy_wrapper_non_passthrough_is_not_inlined,
    )
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base as test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats as test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files as test_skips_non_facade_files,
        test_skips_private_candidate_classes as test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases as test_skips_when_candidate_is_already_in_facade_bases,
    )
    from tests.unit.refactor.test_infra_refactor_mro_import_rewriter import (
        test_migrate_workspace_applies_consumer_rewrites as test_migrate_workspace_applies_consumer_rewrites,
        test_migrate_workspace_dry_run_preserves_files as test_migrate_workspace_dry_run_preserves_files,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
        rope_project as rope_project,
        test_import_alias_detector_skips_facade_and_subclass_files as test_import_alias_detector_skips_facade_and_subclass_files,
        test_import_alias_detector_skips_nested_private_and_as_renames as test_import_alias_detector_skips_nested_private_and_as_renames,
        test_import_alias_detector_skips_private_and_class_imports as test_import_alias_detector_skips_private_and_class_imports,
        test_namespace_rewriter_keeps_contextual_alias_subset as test_namespace_rewriter_keeps_contextual_alias_subset,
        test_namespace_rewriter_only_rewrites_runtime_alias_imports as test_namespace_rewriter_only_rewrites_runtime_alias_imports,
        test_namespace_rewriter_skips_facade_and_subclass_files as test_namespace_rewriter_skips_facade_and_subclass_files,
        test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates as test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_source import (
        FAMILY_FILE_MAP as FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP as FAMILY_SUFFIX_MAP,
        test_detects_only_wrong_alias_in_mixed_import as test_detects_only_wrong_alias_in_mixed_import,
        test_detects_same_project_submodule_alias_import as test_detects_same_project_submodule_alias_import,
        test_detects_wrong_source_m_import as test_detects_wrong_source_m_import,
        test_detects_wrong_source_u_import as test_detects_wrong_source_u_import,
        test_project_without_alias_facade_has_no_violation as test_project_without_alias_facade_has_no_violation,
        test_rewriter_namespace_source_is_idempotent_with_ruff as test_rewriter_namespace_source_is_idempotent_with_ruff,
        test_rewriter_preserves_non_alias_symbols as test_rewriter_preserves_non_alias_symbols,
        test_rewriter_splits_mixed_imports_correctly as test_rewriter_splits_mixed_imports_correctly,
        test_skips_facade_declaration_files as test_skips_facade_declaration_files,
        test_skips_import_as_rename as test_skips_import_as_rename,
        test_skips_init_file as test_skips_init_file,
        test_skips_non_alias_symbols as test_skips_non_alias_symbols,
        test_skips_r_alias_universal_exception as test_skips_r_alias_universal_exception,
        test_skips_same_project_private_submodule as test_skips_same_project_private_submodule,
        test_skips_same_project_submodule_class_import as test_skips_same_project_submodule_class_import,
    )
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
        test_pattern_rule_converts_dict_annotations_to_mapping as test_pattern_rule_converts_dict_annotations_to_mapping,
        test_pattern_rule_keeps_dict_param_when_copy_used as test_pattern_rule_keeps_dict_param_when_copy_used,
        test_pattern_rule_keeps_dict_param_when_subscript_mutated as test_pattern_rule_keeps_dict_param_when_subscript_mutated,
        test_pattern_rule_keeps_type_cast_when_not_nested_object_cast as test_pattern_rule_keeps_type_cast_when_not_nested_object_cast,
        test_pattern_rule_optionally_converts_return_annotations_to_mapping as test_pattern_rule_optionally_converts_return_annotations_to_mapping,
        test_pattern_rule_removes_configured_redundant_casts as test_pattern_rule_removes_configured_redundant_casts,
        test_pattern_rule_removes_nested_type_object_cast_chain as test_pattern_rule_removes_nested_type_object_cast_chain,
        test_pattern_rule_skips_overload_signatures as test_pattern_rule_skips_overload_signatures,
    )
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        test_read_project_metadata_preserves_pep621_dependency_order as test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order as test_read_project_metadata_preserves_poetry_dependency_order,
    )
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub as EngineSafetyStub,
        test_refactor_project_integrates_safety_manager as test_refactor_project_integrates_safety_manager,
    )
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        test_all_three_capabilities_in_one_pass as test_all_three_capabilities_in_one_pass,
        test_converts_multiple_aliases as test_converts_multiple_aliases,
        test_converts_typealias_to_pep695 as test_converts_typealias_to_pep695,
        test_injects_t_import_when_needed as test_injects_t_import_when_needed,
        test_no_duplicate_t_import_when_t_from_project_package as test_no_duplicate_t_import_when_t_from_project_package,
        test_noop_clean_module as test_noop_clean_module,
        test_preserves_annotated_in_function_params as test_preserves_annotated_in_function_params,
        test_preserves_non_matching_unions as test_preserves_non_matching_unions,
        test_preserves_override_in_method as test_preserves_override_in_method,
        test_preserves_protocol_and_runtime_checkable as test_preserves_protocol_and_runtime_checkable,
        test_preserves_type_checking_import as test_preserves_type_checking_import,
        test_preserves_typealias_import_when_class_level_usage_exists as test_preserves_typealias_import_when_class_level_usage_exists,
        test_preserves_used_imports_when_import_precedes_usage as test_preserves_used_imports_when_import_precedes_usage,
        test_preserves_used_typing_imports as test_preserves_used_typing_imports,
        test_removes_all_imports_when_none_used_import_first as test_removes_all_imports_when_none_used_import_first,
        test_removes_all_unused_typing_imports as test_removes_all_unused_typing_imports,
        test_removes_dead_typealias_import as test_removes_dead_typealias_import,
        test_removes_typealias_import_only_when_all_usages_converted as test_removes_typealias_import_only_when_all_usages_converted,
        test_removes_unused_preserves_used_when_import_precedes_usage as test_removes_unused_preserves_used_when_import_precedes_usage,
        test_replaces_container_union as test_replaces_container_union,
        test_replaces_numeric_union as test_replaces_numeric_union,
        test_replaces_primitives_union as test_replaces_primitives_union,
        test_replaces_scalar_union as test_replaces_scalar_union,
        test_skips_definition_files as test_skips_definition_files,
        test_skips_union_with_none as test_skips_union_with_none,
        test_typealias_conversion_preserves_used_typing_siblings as test_typealias_conversion_preserves_used_typing_siblings,
    )
    from tests.unit.refactor.test_main_cli import (
        refactor_main as refactor_main,
        test_refactor_census_rejects_apply_before_subcommand as test_refactor_census_rejects_apply_before_subcommand,
        test_refactor_centralize_accepts_apply_before_subcommand as test_refactor_centralize_accepts_apply_before_subcommand,
    )
    from tests.unit.release import (
        flow_tests as flow_tests,
        orchestrator_git_tests as orchestrator_git_tests,
        orchestrator_helpers_tests as orchestrator_helpers_tests,
        orchestrator_phases_tests as orchestrator_phases_tests,
        orchestrator_publish_tests as orchestrator_publish_tests,
        orchestrator_tests as orchestrator_tests,
        release_init_tests as release_init_tests,
        version_resolution_tests as version_resolution_tests,
    )
    from tests.unit.release._stubs import (
        FakeReporting as FakeReporting,
        FakeSelection as FakeSelection,
        FakeSubprocess as FakeSubprocess,
        FakeUtilsNamespace as FakeUtilsNamespace,
        FakeVersioning as FakeVersioning,
    )
    from tests.unit.release.flow_tests import TestReleaseMainFlow as TestReleaseMainFlow
    from tests.unit.release.main_tests import (
        TestReleaseMainParsing as TestReleaseMainParsing,
    )
    from tests.unit.release.orchestrator_git_tests import (
        TestCollectChanges as TestCollectChanges,
        TestCreateBranches as TestCreateBranches,
        TestCreateTag as TestCreateTag,
        TestPreviousTag as TestPreviousTag,
        TestPushRelease as TestPushRelease,
    )
    from tests.unit.release.orchestrator_helpers_tests import (
        TestBuildTargets as TestBuildTargets,
        TestBumpNextDev as TestBumpNextDev,
        TestDispatchPhase as TestDispatchPhase,
        TestGenerateNotes as TestGenerateNotes,
        TestRunMake as TestRunMake,
        TestUpdateChangelog as TestUpdateChangelog,
        TestVersionFiles as TestVersionFiles,
    )
    from tests.unit.release.orchestrator_phases_tests import (
        TestPhaseBuild as TestPhaseBuild,
        TestPhaseValidate as TestPhaseValidate,
        TestPhaseVersion as TestPhaseVersion,
    )
    from tests.unit.release.orchestrator_publish_tests import (
        TestPhasePublish as TestPhasePublish,
    )
    from tests.unit.release.orchestrator_tests import (
        TestReleaseOrchestratorExecute as TestReleaseOrchestratorExecute,
        workspace_root as workspace_root,
    )
    from tests.unit.release.release_init_tests import TestReleaseInit as TestReleaseInit
    from tests.unit.release.version_resolution_tests import (
        TestReleaseMainTagResolution as TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution as TestReleaseMainVersionResolution,
        TestResolveVersionInteractive as TestResolveVersionInteractive,
    )
    from tests.unit.test_infra_constants_core import (
        TestFlextInfraConstantsExcludedNamespace as TestFlextInfraConstantsExcludedNamespace,
        TestFlextInfraConstantsFilesNamespace as TestFlextInfraConstantsFilesNamespace,
        TestFlextInfraConstantsGatesNamespace as TestFlextInfraConstantsGatesNamespace,
        TestFlextInfraConstantsPathsNamespace as TestFlextInfraConstantsPathsNamespace,
        TestFlextInfraConstantsStatusNamespace as TestFlextInfraConstantsStatusNamespace,
    )
    from tests.unit.test_infra_constants_extra import (
        TestFlextInfraConstantsAlias as TestFlextInfraConstantsAlias,
        TestFlextInfraConstantsCheckNamespace as TestFlextInfraConstantsCheckNamespace,
        TestFlextInfraConstantsConsistency as TestFlextInfraConstantsConsistency,
        TestFlextInfraConstantsEncodingNamespace as TestFlextInfraConstantsEncodingNamespace,
        TestFlextInfraConstantsGithubNamespace as TestFlextInfraConstantsGithubNamespace,
        TestFlextInfraConstantsImmutability as TestFlextInfraConstantsImmutability,
    )
    from tests.unit.test_infra_git import (
        TestFlextInfraGitService as TestFlextInfraGitService,
        TestGitPush as TestGitPush,
        TestGitTagOperations as TestGitTagOperations,
        TestRemovedCompatibilityMethods as TestRemovedCompatibilityMethods,
        git_repo as git_repo,
    )
    from tests.unit.test_infra_init_lazy_core import (
        TestFlextInfraInitLazyLoading as TestFlextInfraInitLazyLoading,
    )
    from tests.unit.test_infra_init_lazy_submodules import (
        TestFlextInfraSubmoduleInitLazyLoading as TestFlextInfraSubmoduleInitLazyLoading,
    )
    from tests.unit.test_infra_main import (
        test_main_all_groups_defined as test_main_all_groups_defined,
        test_main_group_descriptions_are_present as test_main_group_descriptions_are_present,
        test_main_help_flag_returns_zero as test_main_help_flag_returns_zero,
        test_main_returns_error_when_no_args as test_main_returns_error_when_no_args,
        test_main_unknown_group_returns_error as test_main_unknown_group_returns_error,
    )
    from tests.unit.test_infra_maintenance_cli import (
        test_maintenance_rejects_apply_flag as test_maintenance_rejects_apply_flag,
    )
    from tests.unit.test_infra_maintenance_init import (
        TestFlextInfraMaintenance as TestFlextInfraMaintenance,
    )
    from tests.unit.test_infra_maintenance_main import (
        TestMaintenanceMainEnforcer as TestMaintenanceMainEnforcer,
        TestMaintenanceMainSuccess as TestMaintenanceMainSuccess,
        main as main,
    )
    from tests.unit.test_infra_maintenance_python_version import (
        TestDiscoverProjects as TestDiscoverProjects,
        TestEnforcerExecute as TestEnforcerExecute,
        TestEnsurePythonVersionFile as TestEnsurePythonVersionFile,
        TestReadRequiredMinor as TestReadRequiredMinor,
        TestWorkspaceRoot as TestWorkspaceRoot,
    )
    from tests.unit.test_infra_paths import (
        TestFlextInfraPathResolver as TestFlextInfraPathResolver,
    )
    from tests.unit.test_infra_patterns_core import (
        TestFlextInfraPatternsMarkdown as TestFlextInfraPatternsMarkdown,
        TestFlextInfraPatternsTooling as TestFlextInfraPatternsTooling,
    )
    from tests.unit.test_infra_patterns_extra import (
        TestFlextInfraPatternsEdgeCases as TestFlextInfraPatternsEdgeCases,
        TestFlextInfraPatternsPatternTypes as TestFlextInfraPatternsPatternTypes,
    )
    from tests.unit.test_infra_protocols import (
        TestFlextInfraProtocolsImport as TestFlextInfraProtocolsImport,
    )
    from tests.unit.test_infra_reporting_core import (
        TestFlextInfraReportingServiceCore as TestFlextInfraReportingServiceCore,
    )
    from tests.unit.test_infra_reporting_extra import (
        TestFlextInfraReportingServiceExtra as TestFlextInfraReportingServiceExtra,
    )
    from tests.unit.test_infra_selection import (
        TestFlextInfraUtilitiesSelection as TestFlextInfraUtilitiesSelection,
    )
    from tests.unit.test_infra_subprocess_core import (
        runner as runner,
        test_capture_cases as test_capture_cases,
        test_run_cases as test_run_cases,
        test_run_raw_cases as test_run_raw_cases,
    )
    from tests.unit.test_infra_subprocess_extra import (
        TestFlextInfraCommandRunnerExtra as TestFlextInfraCommandRunnerExtra,
    )
    from tests.unit.test_infra_toml_io import (
        TestFlextInfraTomlDocument as TestFlextInfraTomlDocument,
        TestFlextInfraTomlHelpers as TestFlextInfraTomlHelpers,
        TestFlextInfraTomlRead as TestFlextInfraTomlRead,
    )
    from tests.unit.test_infra_typings import (
        TestFlextInfraTypesImport as TestFlextInfraTypesImport,
    )
    from tests.unit.test_infra_utilities import (
        TestFlextInfraUtilitiesImport as TestFlextInfraUtilitiesImport,
    )
    from tests.unit.test_infra_version_core import (
        TestFlextInfraVersionClass as TestFlextInfraVersionClass,
    )
    from tests.unit.test_infra_version_extra import (
        TestFlextInfraVersionModuleLevel as TestFlextInfraVersionModuleLevel,
        TestFlextInfraVersionPackageInfo as TestFlextInfraVersionPackageInfo,
    )
    from tests.unit.test_infra_versioning import (
        service as service,
        test_bump_version_invalid as test_bump_version_invalid,
        test_bump_version_result_type as test_bump_version_result_type,
        test_bump_version_valid as test_bump_version_valid,
        test_current_workspace_version as test_current_workspace_version,
        test_parse_semver_invalid as test_parse_semver_invalid,
        test_parse_semver_result_type as test_parse_semver_result_type,
        test_parse_semver_valid as test_parse_semver_valid,
        test_replace_project_version as test_replace_project_version,
    )
    from tests.unit.test_infra_workspace_cli import (
        test_workspace_cli_migrate_command as test_workspace_cli_migrate_command,
        test_workspace_cli_migrate_output_contains_summary as test_workspace_cli_migrate_output_contains_summary,
        test_workspace_cli_rejects_migrate_flags_for_detect as test_workspace_cli_rejects_migrate_flags_for_detect,
    )
    from tests.unit.test_infra_workspace_detector import (
        TestDetectorBasicDetection as TestDetectorBasicDetection,
        TestDetectorGitRunScenarios as TestDetectorGitRunScenarios,
        TestDetectorRepoNameExtraction as TestDetectorRepoNameExtraction,
        detector as detector,
    )
    from tests.unit.test_infra_workspace_init import (
        TestFlextInfraWorkspace as TestFlextInfraWorkspace,
    )
    from tests.unit.test_infra_workspace_main import (
        TestMainCli as TestMainCli,
        TestRunDetect as TestRunDetect,
        TestRunMigrate as TestRunMigrate,
        TestRunOrchestrate as TestRunOrchestrate,
        TestRunSync as TestRunSync,
        workspace_main as workspace_main,
    )
    from tests.unit.test_infra_workspace_migrator import (
        test_migrator_apply_updates_project_files as test_migrator_apply_updates_project_files,
        test_migrator_discovery_failure as test_migrator_discovery_failure,
        test_migrator_dry_run_reports_changes_without_writes as test_migrator_dry_run_reports_changes_without_writes,
        test_migrator_execute_returns_failure as test_migrator_execute_returns_failure,
        test_migrator_handles_missing_pyproject_gracefully as test_migrator_handles_missing_pyproject_gracefully,
        test_migrator_no_changes_needed as test_migrator_no_changes_needed,
        test_migrator_preserves_custom_makefile_content as test_migrator_preserves_custom_makefile_content,
        test_migrator_workspace_root_not_exists as test_migrator_workspace_root_not_exists,
        test_migrator_workspace_root_project_detection as test_migrator_workspace_root_project_detection,
    )
    from tests.unit.test_infra_workspace_migrator_deps import (
        test_migrate_makefile_not_found_non_dry_run as test_migrate_makefile_not_found_non_dry_run,
        test_migrate_pyproject_flext_core_non_dry_run as test_migrate_pyproject_flext_core_non_dry_run,
        test_migrator_has_flext_core_dependency_in_poetry as test_migrator_has_flext_core_dependency_in_poetry,
        test_migrator_has_flext_core_dependency_poetry_deps_not_table as test_migrator_has_flext_core_dependency_poetry_deps_not_table,
        test_migrator_has_flext_core_dependency_poetry_table_missing as test_migrator_has_flext_core_dependency_poetry_table_missing,
        test_workspace_migrator_error_handling_on_invalid_workspace as test_workspace_migrator_error_handling_on_invalid_workspace,
        test_workspace_migrator_makefile_not_found_dry_run as test_workspace_migrator_makefile_not_found_dry_run,
        test_workspace_migrator_makefile_read_error as test_workspace_migrator_makefile_read_error,
        test_workspace_migrator_pyproject_write_error as test_workspace_migrator_pyproject_write_error,
    )
    from tests.unit.test_infra_workspace_migrator_dryrun import (
        test_migrator_flext_core_dry_run as test_migrator_flext_core_dry_run,
        test_migrator_flext_core_project_skipped as test_migrator_flext_core_project_skipped,
        test_migrator_gitignore_already_normalized_dry_run as test_migrator_gitignore_already_normalized_dry_run,
        test_migrator_makefile_not_found_dry_run as test_migrator_makefile_not_found_dry_run,
        test_migrator_makefile_read_failure as test_migrator_makefile_read_failure,
        test_migrator_pyproject_not_found_dry_run as test_migrator_pyproject_not_found_dry_run,
    )
    from tests.unit.test_infra_workspace_migrator_errors import (
        TestMigratorReadFailures as TestMigratorReadFailures,
        TestMigratorWriteFailures as TestMigratorWriteFailures,
    )
    from tests.unit.test_infra_workspace_migrator_internal import (
        TestMigratorEdgeCases as TestMigratorEdgeCases,
        TestMigratorInternalMakefile as TestMigratorInternalMakefile,
        TestMigratorInternalPyproject as TestMigratorInternalPyproject,
    )
    from tests.unit.test_infra_workspace_migrator_pyproject import (
        TestMigratorDryRun as TestMigratorDryRun,
        TestMigratorFlextCore as TestMigratorFlextCore,
        TestMigratorPoetryDeps as TestMigratorPoetryDeps,
    )
    from tests.unit.test_infra_workspace_orchestrator import (
        TestOrchestratorBasic as TestOrchestratorBasic,
        TestOrchestratorFailures as TestOrchestratorFailures,
        TestOrchestratorGateNormalization as TestOrchestratorGateNormalization,
        orchestrator as orchestrator,
    )
    from tests.unit.test_infra_workspace_sync import (
        SetupFn as SetupFn,
        svc as svc,
        test_atomic_write_fail as test_atomic_write_fail,
        test_atomic_write_ok as test_atomic_write_ok,
        test_cli_forwards_canonical_root as test_cli_forwards_canonical_root,
        test_cli_result_by_project_root as test_cli_result_by_project_root,
        test_gitignore_entry_scenarios as test_gitignore_entry_scenarios,
        test_gitignore_sync_failure as test_gitignore_sync_failure,
        test_gitignore_write_failure as test_gitignore_write_failure,
        test_sync_basemk_scenarios as test_sync_basemk_scenarios,
        test_sync_error_scenarios as test_sync_error_scenarios,
        test_sync_regenerates_project_makefile_without_legacy_passthrough as test_sync_regenerates_project_makefile_without_legacy_passthrough,
        test_sync_root_validation as test_sync_root_validation,
        test_sync_success_scenarios as test_sync_success_scenarios,
        test_sync_updates_project_makefile_for_standalone_project as test_sync_updates_project_makefile_for_standalone_project,
        test_sync_updates_workspace_makefile_for_workspace_root as test_sync_updates_workspace_makefile_for_workspace_root,
        test_workspace_makefile_generator_declares_canonical_workspace_variables as test_workspace_makefile_generator_declares_canonical_workspace_variables,
        test_workspace_makefile_generator_reuses_mod_and_boot_feedback as test_workspace_makefile_generator_reuses_mod_and_boot_feedback,
        test_workspace_makefile_generator_sanitizes_orchestrator_env as test_workspace_makefile_generator_sanitizes_orchestrator_env,
    )
    from tests.unit.validate import (
        basemk_validator_tests as basemk_validator_tests,
        inventory_tests as inventory_tests,
        pytest_diag as pytest_diag,
        scanner_tests as scanner_tests,
        skill_validator_tests as skill_validator_tests,
        stub_chain_tests as stub_chain_tests,
    )
    from tests.unit.validate.basemk_validator_tests import (
        TestBaseMkValidatorCore as TestBaseMkValidatorCore,
        TestBaseMkValidatorEdgeCases as TestBaseMkValidatorEdgeCases,
        TestBaseMkValidatorSha256 as TestBaseMkValidatorSha256,
        v as v,
    )
    from tests.unit.validate.init_tests import TestCoreModuleInit as TestCoreModuleInit
    from tests.unit.validate.inventory_tests import (
        TestInventoryServiceCore as TestInventoryServiceCore,
        TestInventoryServiceReports as TestInventoryServiceReports,
        TestInventoryServiceScripts as TestInventoryServiceScripts,
    )
    from tests.unit.validate.main_cli_tests import (
        test_stub_validate_help_returns_zero as test_stub_validate_help_returns_zero,
        test_stub_validate_uses_all_flag as test_stub_validate_uses_all_flag,
    )
    from tests.unit.validate.main_tests import (
        TestMainBaseMkValidate as TestMainBaseMkValidate,
        TestMainCliRouting as TestMainCliRouting,
        TestMainInventory as TestMainInventory,
        TestMainScan as TestMainScan,
    )
    from tests.unit.validate.pytest_diag import (
        TestPytestDiagExtractorCore as TestPytestDiagExtractorCore,
        TestPytestDiagLogParsing as TestPytestDiagLogParsing,
        TestPytestDiagParseXml as TestPytestDiagParseXml,
    )
    from tests.unit.validate.scanner_tests import (
        TestScannerCore as TestScannerCore,
        TestScannerHelpers as TestScannerHelpers,
        TestScannerMultiFile as TestScannerMultiFile,
    )
    from tests.unit.validate.skill_validator_tests import (
        TestSafeLoadYaml as TestSafeLoadYaml,
        TestSkillValidatorAstGrepCount as TestSkillValidatorAstGrepCount,
        TestSkillValidatorCore as TestSkillValidatorCore,
        TestSkillValidatorRenderTemplate as TestSkillValidatorRenderTemplate,
        TestStringList as TestStringList,
    )
    from tests.unit.validate.stub_chain_tests import (
        TestStubChainAnalyze as TestStubChainAnalyze,
        TestStubChainCore as TestStubChainCore,
        TestStubChainDiscoverProjects as TestStubChainDiscoverProjects,
        TestStubChainIsInternal as TestStubChainIsInternal,
        TestStubChainStubExists as TestStubChainStubExists,
        TestStubChainValidate as TestStubChainValidate,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "ANSI_RE": ["tests.unit.io.test_infra_output_formatting", "ANSI_RE"],
    "CheckProjectStub": [
        "tests.unit.check.extended_run_projects_tests",
        "CheckProjectStub",
    ],
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
    "GateClass": ["tests.unit.check.extended_runners_extra_tests", "GateClass"],
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
    "TestEnsureCoverageConfigPhase": [
        "tests.unit.deps.test_modernizer_coverage",
        "TestEnsureCoverageConfigPhase",
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
    "TestRunProjectFixMode": [
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectFixMode",
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
    "TestRunPyrightArgs": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestRunPyrightArgs",
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
    "_utilities": ["tests.unit._utilities", ""],
    "auditor": ["tests.unit.docs.auditor_tests", "auditor"],
    "auditor_budgets_tests": ["tests.unit.docs.auditor_budgets_tests", ""],
    "auditor_cli_tests": ["tests.unit.docs.auditor_cli_tests", ""],
    "auditor_links_tests": ["tests.unit.docs.auditor_links_tests", ""],
    "auditor_scope_tests": ["tests.unit.docs.auditor_scope_tests", ""],
    "auditor_tests": ["tests.unit.docs.auditor_tests", ""],
    "autofix_tests": ["tests.unit.codegen.autofix_tests", ""],
    "autofix_workspace_tests": ["tests.unit.codegen.autofix_workspace_tests", ""],
    "basemk": ["tests.unit.basemk", ""],
    "basemk_main": ["tests.unit.basemk.test_engine", "basemk_main"],
    "basemk_validator_tests": ["tests.unit.validate.basemk_validator_tests", ""],
    "builder": ["tests.unit.docs.builder_tests", "builder"],
    "builder_scope_tests": ["tests.unit.docs.builder_scope_tests", ""],
    "builder_tests": ["tests.unit.docs.builder_tests", ""],
    "census": ["tests.unit.codegen.census_tests", "census"],
    "census_models_tests": ["tests.unit.codegen.census_models_tests", ""],
    "census_tests": ["tests.unit.codegen.census_tests", ""],
    "check": ["tests.unit.check", ""],
    "cli_tests": ["tests.unit.check.cli_tests", ""],
    "codegen": ["tests.unit.codegen", ""],
    "constants_quality_gate_tests": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "",
    ],
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
    "deps": ["tests.unit.deps", ""],
    "detector": ["tests.unit.test_infra_workspace_detector", "detector"],
    "discovery": ["tests.unit.discovery", ""],
    "doc": ["tests.unit.deps.test_modernizer_helpers", "doc"],
    "docs": ["tests.unit.docs", ""],
    "extended_cli_entry_tests": ["tests.unit.check.extended_cli_entry_tests", ""],
    "extended_config_fixer_errors_tests": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "",
    ],
    "extended_config_fixer_tests": ["tests.unit.check.extended_config_fixer_tests", ""],
    "extended_error_reporting_tests": [
        "tests.unit.check.extended_error_reporting_tests",
        "",
    ],
    "extended_gate_bandit_markdown_tests": [
        "tests.unit.check.extended_gate_bandit_markdown_tests",
        "",
    ],
    "extended_gate_go_cmd_tests": ["tests.unit.check.extended_gate_go_cmd_tests", ""],
    "extended_gate_mypy_pyright_tests": [
        "tests.unit.check.extended_gate_mypy_pyright_tests",
        "",
    ],
    "extended_models_tests": ["tests.unit.check.extended_models_tests", ""],
    "extended_project_runners_tests": [
        "tests.unit.check.extended_project_runners_tests",
        "",
    ],
    "extended_projects_tests": ["tests.unit.check.extended_projects_tests", ""],
    "extended_reports_tests": ["tests.unit.check.extended_reports_tests", ""],
    "extended_resolve_gates_tests": [
        "tests.unit.check.extended_resolve_gates_tests",
        "",
    ],
    "extended_run_projects_tests": ["tests.unit.check.extended_run_projects_tests", ""],
    "extended_runners_extra_tests": [
        "tests.unit.check.extended_runners_extra_tests",
        "",
    ],
    "extended_runners_go_tests": ["tests.unit.check.extended_runners_go_tests", ""],
    "extended_runners_ruff_tests": ["tests.unit.check.extended_runners_ruff_tests", ""],
    "extended_runners_tests": ["tests.unit.check.extended_runners_tests", ""],
    "extended_workspace_init_tests": [
        "tests.unit.check.extended_workspace_init_tests",
        "",
    ],
    "extract_dep_name": ["tests.unit.deps.test_path_sync_helpers", "extract_dep_name"],
    "fix_pyrefly_config_tests": ["tests.unit.check.fix_pyrefly_config_tests", ""],
    "fixer": ["tests.unit.docs.fixer_internals_tests", "fixer"],
    "fixer_internals_tests": ["tests.unit.docs.fixer_internals_tests", ""],
    "fixer_tests": ["tests.unit.docs.fixer_tests", ""],
    "flow_tests": ["tests.unit.release.flow_tests", ""],
    "gen": ["tests.unit.docs.generator_internals_tests", "gen"],
    "generator_internals_tests": ["tests.unit.docs.generator_internals_tests", ""],
    "generator_tests": ["tests.unit.docs.generator_tests", ""],
    "git_repo": ["tests.unit.test_infra_git", "git_repo"],
    "github": ["tests.unit.github", ""],
    "init_tests": ["tests.unit.check.init_tests", ""],
    "inventory_tests": ["tests.unit.validate.inventory_tests", ""],
    "io": ["tests.unit.io", ""],
    "is_external": ["tests.unit.docs.auditor_tests", "is_external"],
    "lazy_init_generation_tests": ["tests.unit.codegen.lazy_init_generation_tests", ""],
    "lazy_init_helpers_tests": ["tests.unit.codegen.lazy_init_helpers_tests", ""],
    "lazy_init_process_tests": ["tests.unit.codegen.lazy_init_process_tests", ""],
    "lazy_init_service_tests": ["tests.unit.codegen.lazy_init_service_tests", ""],
    "lazy_init_tests": ["tests.unit.codegen.lazy_init_tests", ""],
    "lazy_init_transforms_tests": ["tests.unit.codegen.lazy_init_transforms_tests", ""],
    "main": ["tests.unit.test_infra_maintenance_main", "main"],
    "main_cli_tests": ["tests.unit.github.main_cli_tests", ""],
    "main_commands_tests": ["tests.unit.docs.main_commands_tests", ""],
    "main_dispatch_tests": ["tests.unit.github.main_dispatch_tests", ""],
    "main_entry_tests": ["tests.unit.docs.main_entry_tests", ""],
    "main_integration_tests": ["tests.unit.github.main_integration_tests", ""],
    "main_tests": ["tests.unit.check.main_tests", ""],
    "make_cmd_result": ["tests.unit.check._stubs", "make_cmd_result"],
    "make_gate_exec": ["tests.unit.check._stubs", "make_gate_exec"],
    "make_issue": ["tests.unit.check._stubs", "make_issue"],
    "make_project": ["tests.unit.check._stubs", "make_project"],
    "normalize_link": ["tests.unit.docs.auditor_tests", "normalize_link"],
    "orchestrator": ["tests.unit.test_infra_workspace_orchestrator", "orchestrator"],
    "orchestrator_git_tests": ["tests.unit.release.orchestrator_git_tests", ""],
    "orchestrator_helpers_tests": ["tests.unit.release.orchestrator_helpers_tests", ""],
    "orchestrator_phases_tests": ["tests.unit.release.orchestrator_phases_tests", ""],
    "orchestrator_publish_tests": ["tests.unit.release.orchestrator_publish_tests", ""],
    "orchestrator_tests": ["tests.unit.release.orchestrator_tests", ""],
    "patch_gate_run": ["tests.unit.check._shared_fixtures", "patch_gate_run"],
    "patch_python_dir_detection": [
        "tests.unit.check._shared_fixtures",
        "patch_python_dir_detection",
    ],
    "pipeline_tests": ["tests.unit.codegen.pipeline_tests", ""],
    "pyrefly_tests": ["tests.unit.check.pyrefly_tests", ""],
    "pyright_content": ["tests.unit.deps.test_extra_paths_sync", "pyright_content"],
    "pytest_diag": ["tests.unit.validate.pytest_diag", ""],
    "refactor": ["tests.unit.refactor", ""],
    "refactor_main": ["tests.unit.refactor.test_main_cli", "refactor_main"],
    "release": ["tests.unit.release", ""],
    "release_init_tests": ["tests.unit.release.release_init_tests", ""],
    "rewrite_dep_paths": [
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "rewrite_dep_paths",
    ],
    "rope_project": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "rope_project",
    ],
    "run_command_failure_check": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ],
    "runner": ["tests.unit.test_infra_subprocess_core", "runner"],
    "scaffolder_naming_tests": ["tests.unit.codegen.scaffolder_naming_tests", ""],
    "scaffolder_tests": ["tests.unit.codegen.scaffolder_tests", ""],
    "scanner_tests": ["tests.unit.validate.scanner_tests", ""],
    "service": ["tests.unit.test_infra_versioning", "service"],
    "shared_iter_tests": ["tests.unit.docs.shared_iter_tests", ""],
    "shared_tests": ["tests.unit.docs.shared_tests", ""],
    "shared_write_tests": ["tests.unit.docs.shared_write_tests", ""],
    "should_skip_target": ["tests.unit.docs.auditor_tests", "should_skip_target"],
    "skill_validator_tests": ["tests.unit.validate.skill_validator_tests", ""],
    "stub_chain_tests": ["tests.unit.validate.stub_chain_tests", ""],
    "svc": ["tests.unit.test_infra_workspace_sync", "svc"],
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
    "test_basemk_main_rejects_apply_flag": [
        "tests.unit.basemk.test_main",
        "test_basemk_main_rejects_apply_flag",
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
    "test_cli_forwards_canonical_root": [
        "tests.unit.test_infra_workspace_sync",
        "test_cli_forwards_canonical_root",
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
    "test_declared_dependency_names_collects_all_supported_groups": [
        "tests.unit.deps.test_modernizer_helpers",
        "test_declared_dependency_names_collects_all_supported_groups",
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
    "test_detection_classify": ["tests.unit.deps.test_detection_classify", ""],
    "test_detection_deptry": ["tests.unit.deps.test_detection_deptry", ""],
    "test_detection_discover": ["tests.unit.deps.test_detection_discover", ""],
    "test_detection_models": ["tests.unit.deps.test_detection_models", ""],
    "test_detection_pip_check": ["tests.unit.deps.test_detection_pip_check", ""],
    "test_detection_typings": ["tests.unit.deps.test_detection_typings", ""],
    "test_detection_typings_flow": ["tests.unit.deps.test_detection_typings_flow", ""],
    "test_detection_uncovered": ["tests.unit.deps.test_detection_uncovered", ""],
    "test_detector_detect": ["tests.unit.deps.test_detector_detect", ""],
    "test_detector_detect_failures": [
        "tests.unit.deps.test_detector_detect_failures",
        "",
    ],
    "test_detector_init": ["tests.unit.deps.test_detector_init", ""],
    "test_detector_main": ["tests.unit.deps.test_detector_main", ""],
    "test_detector_models": ["tests.unit.deps.test_detector_models", ""],
    "test_detector_report": ["tests.unit.deps.test_detector_report", ""],
    "test_detector_report_flags": ["tests.unit.deps.test_detector_report_flags", ""],
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
    "test_discovery_consolidated": [
        "tests.unit._utilities.test_discovery_consolidated",
        "",
    ],
    "test_engine": ["tests.unit.basemk.test_engine", ""],
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
    "test_extra_paths_manager": ["tests.unit.deps.test_extra_paths_manager", ""],
    "test_extra_paths_pep621": ["tests.unit.deps.test_extra_paths_pep621", ""],
    "test_extra_paths_sync": ["tests.unit.deps.test_extra_paths_sync", ""],
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
    "test_formatting": ["tests.unit._utilities.test_formatting", ""],
    "test_generator": ["tests.unit.basemk.test_generator", ""],
    "test_generator_edge_cases": ["tests.unit.basemk.test_generator_edge_cases", ""],
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
    "test_infra_constants_core": ["tests.unit.test_infra_constants_core", ""],
    "test_infra_constants_extra": ["tests.unit.test_infra_constants_extra", ""],
    "test_infra_container": ["tests.unit.container.test_infra_container", ""],
    "test_infra_discovery": ["tests.unit.discovery.test_infra_discovery", ""],
    "test_infra_discovery_edge_cases": [
        "tests.unit.discovery.test_infra_discovery_edge_cases",
        "",
    ],
    "test_infra_git": ["tests.unit.test_infra_git", ""],
    "test_infra_init_lazy_core": ["tests.unit.test_infra_init_lazy_core", ""],
    "test_infra_init_lazy_submodules": [
        "tests.unit.test_infra_init_lazy_submodules",
        "",
    ],
    "test_infra_json_io": ["tests.unit.io.test_infra_json_io", ""],
    "test_infra_main": ["tests.unit.test_infra_main", ""],
    "test_infra_maintenance_cli": ["tests.unit.test_infra_maintenance_cli", ""],
    "test_infra_maintenance_init": ["tests.unit.test_infra_maintenance_init", ""],
    "test_infra_maintenance_main": ["tests.unit.test_infra_maintenance_main", ""],
    "test_infra_maintenance_python_version": [
        "tests.unit.test_infra_maintenance_python_version",
        "",
    ],
    "test_infra_output_edge_cases": ["tests.unit.io.test_infra_output_edge_cases", ""],
    "test_infra_output_formatting": ["tests.unit.io.test_infra_output_formatting", ""],
    "test_infra_paths": ["tests.unit.test_infra_paths", ""],
    "test_infra_patterns_core": ["tests.unit.test_infra_patterns_core", ""],
    "test_infra_patterns_extra": ["tests.unit.test_infra_patterns_extra", ""],
    "test_infra_protocols": ["tests.unit.test_infra_protocols", ""],
    "test_infra_refactor_analysis": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "",
    ],
    "test_infra_refactor_class_and_propagation": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "",
    ],
    "test_infra_refactor_class_placement": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "",
    ],
    "test_infra_refactor_engine": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "",
    ],
    "test_infra_refactor_import_modernizer": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "",
    ],
    "test_infra_refactor_legacy_and_annotations": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "",
    ],
    "test_infra_refactor_mro_completeness": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "",
    ],
    "test_infra_refactor_mro_import_rewriter": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "",
    ],
    "test_infra_refactor_namespace_aliases": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "",
    ],
    "test_infra_refactor_namespace_source": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "",
    ],
    "test_infra_refactor_pattern_corrections": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "",
    ],
    "test_infra_refactor_project_classifier": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "",
    ],
    "test_infra_refactor_safety": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "",
    ],
    "test_infra_refactor_typing_unifier": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "",
    ],
    "test_infra_reporting_core": ["tests.unit.test_infra_reporting_core", ""],
    "test_infra_reporting_extra": ["tests.unit.test_infra_reporting_extra", ""],
    "test_infra_selection": ["tests.unit.test_infra_selection", ""],
    "test_infra_subprocess_core": ["tests.unit.test_infra_subprocess_core", ""],
    "test_infra_subprocess_extra": ["tests.unit.test_infra_subprocess_extra", ""],
    "test_infra_terminal_detection": [
        "tests.unit.io.test_infra_terminal_detection",
        "",
    ],
    "test_infra_toml_io": ["tests.unit.test_infra_toml_io", ""],
    "test_infra_typings": ["tests.unit.test_infra_typings", ""],
    "test_infra_utilities": ["tests.unit.test_infra_utilities", ""],
    "test_infra_version_core": ["tests.unit.test_infra_version_core", ""],
    "test_infra_version_extra": ["tests.unit.test_infra_version_extra", ""],
    "test_infra_versioning": ["tests.unit.test_infra_versioning", ""],
    "test_infra_workspace_cli": ["tests.unit.test_infra_workspace_cli", ""],
    "test_infra_workspace_detector": ["tests.unit.test_infra_workspace_detector", ""],
    "test_infra_workspace_init": ["tests.unit.test_infra_workspace_init", ""],
    "test_infra_workspace_main": ["tests.unit.test_infra_workspace_main", ""],
    "test_infra_workspace_migrator": ["tests.unit.test_infra_workspace_migrator", ""],
    "test_infra_workspace_migrator_deps": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "",
    ],
    "test_infra_workspace_migrator_dryrun": [
        "tests.unit.test_infra_workspace_migrator_dryrun",
        "",
    ],
    "test_infra_workspace_migrator_errors": [
        "tests.unit.test_infra_workspace_migrator_errors",
        "",
    ],
    "test_infra_workspace_migrator_internal": [
        "tests.unit.test_infra_workspace_migrator_internal",
        "",
    ],
    "test_infra_workspace_migrator_pyproject": [
        "tests.unit.test_infra_workspace_migrator_pyproject",
        "",
    ],
    "test_infra_workspace_orchestrator": [
        "tests.unit.test_infra_workspace_orchestrator",
        "",
    ],
    "test_infra_workspace_sync": ["tests.unit.test_infra_workspace_sync", ""],
    "test_init": ["tests.unit.basemk.test_init", ""],
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
    "test_internal_sync_discovery": [
        "tests.unit.deps.test_internal_sync_discovery",
        "",
    ],
    "test_internal_sync_discovery_edge": [
        "tests.unit.deps.test_internal_sync_discovery_edge",
        "",
    ],
    "test_internal_sync_main": ["tests.unit.deps.test_internal_sync_main", ""],
    "test_internal_sync_resolve": ["tests.unit.deps.test_internal_sync_resolve", ""],
    "test_internal_sync_sync": ["tests.unit.deps.test_internal_sync_sync", ""],
    "test_internal_sync_sync_edge": [
        "tests.unit.deps.test_internal_sync_sync_edge",
        "",
    ],
    "test_internal_sync_sync_edge_more": [
        "tests.unit.deps.test_internal_sync_sync_edge_more",
        "",
    ],
    "test_internal_sync_update": ["tests.unit.deps.test_internal_sync_update", ""],
    "test_internal_sync_update_checkout_edge": [
        "tests.unit.deps.test_internal_sync_update_checkout_edge",
        "",
    ],
    "test_internal_sync_validation": [
        "tests.unit.deps.test_internal_sync_validation",
        "",
    ],
    "test_internal_sync_workspace": [
        "tests.unit.deps.test_internal_sync_workspace",
        "",
    ],
    "test_iteration": ["tests.unit._utilities.test_iteration", ""],
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
    "test_main": ["tests.unit.basemk.test_main", ""],
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
    "test_main_cli": ["tests.unit.refactor.test_main_cli", ""],
    "test_main_discovery_failure": [
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_discovery_failure",
    ],
    "test_main_dispatch": ["tests.unit.deps.test_main_dispatch", ""],
    "test_main_group_descriptions_are_present": [
        "tests.unit.test_infra_main",
        "test_main_group_descriptions_are_present",
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
    "test_main_returns_nonzero_on_unknown": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_nonzero_on_unknown",
    ],
    "test_main_returns_zero_on_help": [
        "tests.unit.github.main_cli_tests",
        "test_main_returns_zero_on_help",
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
    "test_maintenance_rejects_apply_flag": [
        "tests.unit.test_infra_maintenance_cli",
        "test_maintenance_rejects_apply_flag",
    ],
    "test_make_boot_works_without_existing_venv_in_workspace_mode": [
        "tests.unit.basemk.test_make_contract",
        "test_make_boot_works_without_existing_venv_in_workspace_mode",
    ],
    "test_make_check_fast_path_check_only_suppresses_fix_writes": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_fast_path_check_only_suppresses_fix_writes",
    ],
    "test_make_check_file_scope_rejects_unsupported_gates": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_rejects_unsupported_gates",
    ],
    "test_make_check_file_scope_runs_mypy": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_runs_mypy",
    ],
    "test_make_check_file_scope_unsets_python_path_env": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_unsets_python_path_env",
    ],
    "test_make_check_full_run_forwards_fix_and_tool_args": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_full_run_forwards_fix_and_tool_args",
    ],
    "test_make_check_full_run_unsets_python_path_env": [
        "tests.unit.basemk.test_make_contract",
        "test_make_check_full_run_unsets_python_path_env",
    ],
    "test_make_contract": ["tests.unit.basemk.test_make_contract", ""],
    "test_make_help_lists_supported_options": [
        "tests.unit.basemk.test_make_contract",
        "test_make_help_lists_supported_options",
    ],
    "test_migrate_makefile_not_found_non_dry_run": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_makefile_not_found_non_dry_run",
    ],
    "test_migrate_pyproject_flext_core_non_dry_run": [
        "tests.unit.test_infra_workspace_migrator_deps",
        "test_migrate_pyproject_flext_core_non_dry_run",
    ],
    "test_migrate_workspace_applies_consumer_rewrites": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "test_migrate_workspace_applies_consumer_rewrites",
    ],
    "test_migrate_workspace_dry_run_preserves_files": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "test_migrate_workspace_dry_run_preserves_files",
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
    "test_modernizer_comments": ["tests.unit.deps.test_modernizer_comments", ""],
    "test_modernizer_consolidate": ["tests.unit.deps.test_modernizer_consolidate", ""],
    "test_modernizer_coverage": ["tests.unit.deps.test_modernizer_coverage", ""],
    "test_modernizer_helpers": ["tests.unit.deps.test_modernizer_helpers", ""],
    "test_modernizer_main": ["tests.unit.deps.test_modernizer_main", ""],
    "test_modernizer_main_extra": ["tests.unit.deps.test_modernizer_main_extra", ""],
    "test_modernizer_pyrefly": ["tests.unit.deps.test_modernizer_pyrefly", ""],
    "test_modernizer_pyright": ["tests.unit.deps.test_modernizer_pyright", ""],
    "test_modernizer_pytest": ["tests.unit.deps.test_modernizer_pytest", ""],
    "test_modernizer_workspace": ["tests.unit.deps.test_modernizer_workspace", ""],
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
    "test_parsing": ["tests.unit._utilities.test_parsing", ""],
    "test_path_sync_helpers": ["tests.unit.deps.test_path_sync_helpers", ""],
    "test_path_sync_init": ["tests.unit.deps.test_path_sync_init", ""],
    "test_path_sync_main": ["tests.unit.deps.test_path_sync_main", ""],
    "test_path_sync_main_edges": ["tests.unit.deps.test_path_sync_main_edges", ""],
    "test_path_sync_main_more": ["tests.unit.deps.test_path_sync_main_more", ""],
    "test_path_sync_main_project_obj": [
        "tests.unit.deps.test_path_sync_main_project_obj",
        "",
    ],
    "test_path_sync_rewrite_deps": ["tests.unit.deps.test_path_sync_rewrite_deps", ""],
    "test_path_sync_rewrite_pep621": [
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "",
    ],
    "test_path_sync_rewrite_poetry": [
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "",
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
    "test_pr_workspace_accepts_repeated_project_options": [
        "tests.unit.github.main_cli_tests",
        "test_pr_workspace_accepts_repeated_project_options",
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
    "test_pyrefly_search_paths_include_workspace_declared_dev_dependencies": [
        "tests.unit.deps.test_extra_paths_manager",
        "test_pyrefly_search_paths_include_workspace_declared_dev_dependencies",
    ],
    "test_read_project_metadata_preserves_pep621_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_pep621_dependency_order",
    ],
    "test_read_project_metadata_preserves_poetry_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_poetry_dependency_order",
    ],
    "test_refactor_census_rejects_apply_before_subcommand": [
        "tests.unit.refactor.test_main_cli",
        "test_refactor_census_rejects_apply_before_subcommand",
    ],
    "test_refactor_centralize_accepts_apply_before_subcommand": [
        "tests.unit.refactor.test_main_cli",
        "test_refactor_centralize_accepts_apply_before_subcommand",
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
    "test_render_all_declares_and_documents_runtime_options": [
        "tests.unit.basemk.test_engine",
        "test_render_all_declares_and_documents_runtime_options",
    ],
    "test_render_all_exposes_canonical_public_targets": [
        "tests.unit.basemk.test_engine",
        "test_render_all_exposes_canonical_public_targets",
    ],
    "test_render_all_generates_large_makefile": [
        "tests.unit.basemk.test_engine",
        "test_render_all_generates_large_makefile",
    ],
    "test_render_all_has_no_scripts_path_references": [
        "tests.unit.basemk.test_engine",
        "test_render_all_has_no_scripts_path_references",
    ],
    "test_rendered_base_mk_declares_cli_group_roots": [
        "tests.unit.basemk.test_make_contract",
        "test_rendered_base_mk_declares_cli_group_roots",
    ],
    "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight": [
        "tests.unit.basemk.test_make_contract",
        "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight",
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
    "test_rope_hooks": ["tests.unit._utilities.test_rope_hooks", ""],
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
    "test_run_cli_rejects_fix_flags_for_run": [
        "tests.unit.check.cli_tests",
        "test_run_cli_rejects_fix_flags_for_run",
    ],
    "test_run_cli_run_forwards_fix_and_tool_args": [
        "tests.unit.check.cli_tests",
        "test_run_cli_run_forwards_fix_and_tool_args",
    ],
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
    "test_run_rope_post_hooks_applies_mro_migration": [
        "tests.unit._utilities.test_rope_hooks",
        "test_run_rope_post_hooks_applies_mro_migration",
    ],
    "test_run_rope_post_hooks_dry_run_is_non_mutating": [
        "tests.unit._utilities.test_rope_hooks",
        "test_run_rope_post_hooks_dry_run_is_non_mutating",
    ],
    "test_safety": ["tests.unit._utilities.test_safety", ""],
    "test_scanning": ["tests.unit._utilities.test_scanning", ""],
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
    "test_stub_validate_help_returns_zero": [
        "tests.unit.validate.main_cli_tests",
        "test_stub_validate_help_returns_zero",
    ],
    "test_stub_validate_uses_all_flag": [
        "tests.unit.validate.main_cli_tests",
        "test_stub_validate_uses_all_flag",
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
    "test_sync_regenerates_project_makefile_without_legacy_passthrough": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_regenerates_project_makefile_without_legacy_passthrough",
    ],
    "test_sync_root_validation": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_root_validation",
    ],
    "test_sync_success_scenarios": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_success_scenarios",
    ],
    "test_sync_updates_project_makefile_for_standalone_project": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_project_makefile_for_standalone_project",
    ],
    "test_sync_updates_workspace_makefile_for_workspace_root": [
        "tests.unit.test_infra_workspace_sync",
        "test_sync_updates_workspace_makefile_for_workspace_root",
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
    "test_workspace_cli_rejects_migrate_flags_for_detect": [
        "tests.unit.test_infra_workspace_cli",
        "test_workspace_cli_rejects_migrate_flags_for_detect",
    ],
    "test_workspace_makefile_generator_declares_canonical_workspace_variables": [
        "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_declares_canonical_workspace_variables",
    ],
    "test_workspace_makefile_generator_reuses_mod_and_boot_feedback": [
        "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_reuses_mod_and_boot_feedback",
    ],
    "test_workspace_makefile_generator_sanitizes_orchestrator_env": [
        "tests.unit.test_infra_workspace_sync",
        "test_workspace_makefile_generator_sanitizes_orchestrator_env",
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
    "v": ["tests.unit.validate.basemk_validator_tests", "v"],
    "validate": ["tests.unit.validate", ""],
    "validator": ["tests.unit.docs.validator_internals_tests", "validator"],
    "validator_internals_tests": ["tests.unit.docs.validator_internals_tests", ""],
    "validator_tests": ["tests.unit.docs.validator_tests", ""],
    "version_resolution_tests": ["tests.unit.release.version_resolution_tests", ""],
    "workspace_check_tests": ["tests.unit.check.workspace_check_tests", ""],
    "workspace_main": ["tests.unit.test_infra_workspace_main", "workspace_main"],
    "workspace_root": ["tests.unit.release.orchestrator_tests", "workspace_root"],
    "workspace_tests": ["tests.unit.check.workspace_tests", ""],
}

_EXPORTS: Sequence[str] = [
    "ANSI_RE",
    "CheckProjectStub",
    "EngineSafetyStub",
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
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
    "_utilities",
    "auditor",
    "auditor_budgets_tests",
    "auditor_cli_tests",
    "auditor_links_tests",
    "auditor_scope_tests",
    "auditor_tests",
    "autofix_tests",
    "autofix_workspace_tests",
    "basemk",
    "basemk_main",
    "basemk_validator_tests",
    "builder",
    "builder_scope_tests",
    "builder_tests",
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
    "deps",
    "detector",
    "discovery",
    "doc",
    "docs",
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
    "extended_reports_tests",
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
    "patch_gate_run",
    "patch_python_dir_detection",
    "pipeline_tests",
    "pyrefly_tests",
    "pyright_content",
    "pytest_diag",
    "refactor",
    "refactor_main",
    "release",
    "release_init_tests",
    "rewrite_dep_paths",
    "rope_project",
    "run_command_failure_check",
    "runner",
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
    "test_in_context_typevar_not_flagged",
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
    "test_parsing",
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
    "test_standalone_final_detected_as_fixable",
    "test_standalone_typealias_detected_as_fixable",
    "test_standalone_typevar_detected_as_fixable",
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
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
