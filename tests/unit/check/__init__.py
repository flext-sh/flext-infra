# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
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

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "CheckProjectStub": [
        "tests.unit.check.extended_run_projects_tests",
        "CheckProjectStub",
    ],
    "GateClass": ["tests.unit.check.extended_runners_extra_tests", "GateClass"],
    "RunCallable": ["tests.unit.check.extended_runners_go_tests", "RunCallable"],
    "TestCheckIssueFormatted": [
        "tests.unit.check.extended_models_tests",
        "TestCheckIssueFormatted",
    ],
    "TestCheckMainEntryPoint": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestCheckMainEntryPoint",
    ],
    "TestCheckProjectRunners": [
        "tests.unit.check.extended_projects_tests",
        "TestCheckProjectRunners",
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
    "TestErrorReporting": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestErrorReporting",
    ],
    "TestFixPyrelfyCLI": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestFixPyrelfyCLI",
    ],
    "TestFlextInfraCheck": ["tests.unit.check.init_tests", "TestFlextInfraCheck"],
    "TestFlextInfraConfigFixer": [
        "tests.unit.check.pyrefly_tests",
        "TestFlextInfraConfigFixer",
    ],
    "TestFlextInfraWorkspaceChecker": [
        "tests.unit.check.workspace_tests",
        "TestFlextInfraWorkspaceChecker",
    ],
    "TestGoFmtEmptyLinesInOutput": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestGoFmtEmptyLinesInOutput",
    ],
    "TestJsonWriteFailure": [
        "tests.unit.check.extended_project_runners_tests",
        "TestJsonWriteFailure",
    ],
    "TestLintAndFormatPublicMethods": [
        "tests.unit.check.extended_projects_tests",
        "TestLintAndFormatPublicMethods",
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
    "TestMypyEmptyLinesInOutput": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestMypyEmptyLinesInOutput",
    ],
    "TestProcessFileReadError": [
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestProcessFileReadError",
    ],
    "TestProjectResultProperties": [
        "tests.unit.check.extended_models_tests",
        "TestProjectResultProperties",
    ],
    "TestRuffFormatDuplicateFiles": [
        "tests.unit.check.extended_error_reporting_tests",
        "TestRuffFormatDuplicateFiles",
    ],
    "TestRunBandit": ["tests.unit.check.extended_runners_extra_tests", "TestRunBandit"],
    "TestRunCLIExtended": [
        "tests.unit.check.extended_cli_entry_tests",
        "TestRunCLIExtended",
    ],
    "TestRunCommand": [
        "tests.unit.check.extended_runners_ruff_tests",
        "TestRunCommand",
    ],
    "TestRunGo": ["tests.unit.check.extended_runners_go_tests", "TestRunGo"],
    "TestRunMarkdown": [
        "tests.unit.check.extended_runners_extra_tests",
        "TestRunMarkdown",
    ],
    "TestRunMypy": ["tests.unit.check.extended_runners_tests", "TestRunMypy"],
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
    "cli_tests": ["tests.unit.check.cli_tests", ""],
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
    "fix_pyrefly_config_tests": ["tests.unit.check.fix_pyrefly_config_tests", ""],
    "init_tests": ["tests.unit.check.init_tests", ""],
    "main_tests": ["tests.unit.check.main_tests", ""],
    "pyrefly_tests": ["tests.unit.check.pyrefly_tests", ""],
    "run_command_failure_check": [
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ],
    "test_check_main_executes_real_cli": [
        "tests.unit.check.main_tests",
        "test_check_main_executes_real_cli",
    ],
    "test_fix_pyrefly_config_main_executes_real_cli_help": [
        "tests.unit.check.fix_pyrefly_config_tests",
        "test_fix_pyrefly_config_main_executes_real_cli_help",
    ],
    "test_resolve_gates_maps_type_alias": [
        "tests.unit.check.cli_tests",
        "test_resolve_gates_maps_type_alias",
    ],
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
    "test_workspace_check_main_returns_error_without_projects": [
        "tests.unit.check.workspace_check_tests",
        "test_workspace_check_main_returns_error_without_projects",
    ],
    "workspace_check_tests": ["tests.unit.check.workspace_check_tests", ""],
    "workspace_tests": ["tests.unit.check.workspace_tests", ""],
}

_EXPORTS: Sequence[str] = [
    "CheckProjectStub",
    "GateClass",
    "RunCallable",
    "TestCheckIssueFormatted",
    "TestCheckMainEntryPoint",
    "TestCheckProjectRunners",
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
    "TestErrorReporting",
    "TestFixPyrelfyCLI",
    "TestFlextInfraCheck",
    "TestFlextInfraConfigFixer",
    "TestFlextInfraWorkspaceChecker",
    "TestGoFmtEmptyLinesInOutput",
    "TestJsonWriteFailure",
    "TestLintAndFormatPublicMethods",
    "TestMarkdownReportEmptyGates",
    "TestMarkdownReportSkipsEmptyGates",
    "TestMarkdownReportWithErrors",
    "TestMypyEmptyLinesInOutput",
    "TestProcessFileReadError",
    "TestProjectResultProperties",
    "TestRuffFormatDuplicateFiles",
    "TestRunBandit",
    "TestRunCLIExtended",
    "TestRunCommand",
    "TestRunGo",
    "TestRunMarkdown",
    "TestRunMypy",
    "TestRunProjectFixMode",
    "TestRunProjectsBehavior",
    "TestRunProjectsReports",
    "TestRunProjectsValidation",
    "TestRunPyrefly",
    "TestRunPyright",
    "TestRunPyrightArgs",
    "TestRunRuffFormat",
    "TestRunRuffLint",
    "TestRunSingleProject",
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
    "cli_tests",
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
    "fix_pyrefly_config_tests",
    "init_tests",
    "main_tests",
    "pyrefly_tests",
    "run_command_failure_check",
    "test_check_main_executes_real_cli",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_resolve_gates_maps_type_alias",
    "test_run_cli_rejects_fix_flags_for_run",
    "test_run_cli_run_forwards_fix_and_tool_args",
    "test_run_cli_run_returns_one_for_fail",
    "test_run_cli_run_returns_two_for_error",
    "test_run_cli_run_returns_zero_for_pass",
    "test_run_cli_with_fail_fast_flag",
    "test_run_cli_with_multiple_projects",
    "test_workspace_check_main_returns_error_without_projects",
    "workspace_check_tests",
    "workspace_tests",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
