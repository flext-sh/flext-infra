# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from tests.unit.check._shared_fixtures import *
    from tests.unit.check._stubs import *
    from tests.unit.check.cli_tests import *
    from tests.unit.check.extended_cli_entry_tests import *
    from tests.unit.check.extended_config_fixer_errors_tests import *
    from tests.unit.check.extended_config_fixer_tests import *
    from tests.unit.check.extended_error_reporting_tests import *
    from tests.unit.check.extended_gate_bandit_markdown_tests import *
    from tests.unit.check.extended_gate_go_cmd_tests import *
    from tests.unit.check.extended_gate_mypy_pyright_tests import *
    from tests.unit.check.extended_models_tests import *
    from tests.unit.check.extended_project_runners_tests import *
    from tests.unit.check.extended_projects_tests import *
    from tests.unit.check.extended_reports_tests import *
    from tests.unit.check.extended_resolve_gates_tests import *
    from tests.unit.check.extended_run_projects_tests import *
    from tests.unit.check.extended_runners_extra_tests import *
    from tests.unit.check.extended_runners_go_tests import *
    from tests.unit.check.extended_runners_ruff_tests import *
    from tests.unit.check.extended_runners_tests import *
    from tests.unit.check.extended_workspace_init_tests import *
    from tests.unit.check.fix_pyrefly_config_tests import *
    from tests.unit.check.init_tests import *
    from tests.unit.check.main_tests import *
    from tests.unit.check.pyrefly_tests import *
    from tests.unit.check.workspace_check_tests import *
    from tests.unit.check.workspace_tests import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "CheckProjectStub": "tests.unit.check.extended_run_projects_tests",
    "GateClass": "tests.unit.check.extended_runners_extra_tests",
    "RunCallable": "tests.unit.check.extended_runners_go_tests",
    "RunProjectsMock": "tests.unit.check._shared_fixtures",
    "Spy": "tests.unit.check._stubs",
    "TestCheckIssueFormatted": "tests.unit.check.extended_models_tests",
    "TestCheckMainEntryPoint": "tests.unit.check.extended_cli_entry_tests",
    "TestCheckProjectRunners": "tests.unit.check.extended_projects_tests",
    "TestCollectMarkdownFiles": "tests.unit.check.extended_runners_ruff_tests",
    "TestConfigFixerEnsureProjectExcludes": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerExecute": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerFindPyprojectFiles": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerFixSearchPaths": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerPathResolution": "tests.unit.check.extended_config_fixer_errors_tests",
    "TestConfigFixerProcessFile": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerRemoveIgnoreSubConfig": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerRun": "tests.unit.check.extended_config_fixer_tests",
    "TestConfigFixerRunMethods": "tests.unit.check.extended_config_fixer_errors_tests",
    "TestConfigFixerRunWithVerbose": "tests.unit.check.extended_config_fixer_errors_tests",
    "TestConfigFixerToArray": "tests.unit.check.extended_config_fixer_tests",
    "TestErrorReporting": "tests.unit.check.extended_error_reporting_tests",
    "TestFixPyrelfyCLI": "tests.unit.check.extended_cli_entry_tests",
    "TestFlextInfraCheck": "tests.unit.check.init_tests",
    "TestFlextInfraConfigFixer": "tests.unit.check.pyrefly_tests",
    "TestFlextInfraWorkspaceChecker": "tests.unit.check.workspace_tests",
    "TestGoFmtEmptyLinesInOutput": "tests.unit.check.extended_error_reporting_tests",
    "TestJsonWriteFailure": "tests.unit.check.extended_project_runners_tests",
    "TestLintAndFormatPublicMethods": "tests.unit.check.extended_projects_tests",
    "TestMarkdownReportEmptyGates": "tests.unit.check.extended_error_reporting_tests",
    "TestMarkdownReportSkipsEmptyGates": "tests.unit.check.extended_reports_tests",
    "TestMarkdownReportWithErrors": "tests.unit.check.extended_reports_tests",
    "TestMypyEmptyLinesInOutput": "tests.unit.check.extended_error_reporting_tests",
    "TestProcessFileReadError": "tests.unit.check.extended_config_fixer_errors_tests",
    "TestProjectResultProperties": "tests.unit.check.extended_models_tests",
    "TestRuffFormatDuplicateFiles": "tests.unit.check.extended_error_reporting_tests",
    "TestRunBandit": "tests.unit.check.extended_runners_extra_tests",
    "TestRunCLIExtended": "tests.unit.check.extended_cli_entry_tests",
    "TestRunCommand": "tests.unit.check.extended_runners_ruff_tests",
    "TestRunGo": "tests.unit.check.extended_runners_go_tests",
    "TestRunMarkdown": "tests.unit.check.extended_runners_extra_tests",
    "TestRunMypy": "tests.unit.check.extended_runners_tests",
    "TestRunProjectFixMode": "tests.unit.check.extended_run_projects_tests",
    "TestRunProjectsBehavior": "tests.unit.check.extended_run_projects_tests",
    "TestRunProjectsReports": "tests.unit.check.extended_run_projects_tests",
    "TestRunProjectsValidation": "tests.unit.check.extended_run_projects_tests",
    "TestRunPyrefly": "tests.unit.check.extended_runners_tests",
    "TestRunPyright": "tests.unit.check.extended_runners_extra_tests",
    "TestRunPyrightArgs": "tests.unit.check.extended_runners_ruff_tests",
    "TestRunRuffFormat": "tests.unit.check.extended_runners_ruff_tests",
    "TestRunRuffLint": "tests.unit.check.extended_runners_ruff_tests",
    "TestRunSingleProject": "tests.unit.check.extended_run_projects_tests",
    "TestWorkspaceCheckCLI": "tests.unit.check.extended_cli_entry_tests",
    "TestWorkspaceCheckerBuildGateResult": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerCollectMarkdownFiles": "tests.unit.check.extended_gate_go_cmd_tests",
    "TestWorkspaceCheckerDirsWithPy": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerErrorSummary": "tests.unit.check.extended_models_tests",
    "TestWorkspaceCheckerExecute": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerExistingCheckDirs": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerInitOSError": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerInitialization": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerMarkdownReport": "tests.unit.check.extended_reports_tests",
    "TestWorkspaceCheckerMarkdownReportEdgeCases": "tests.unit.check.extended_reports_tests",
    "TestWorkspaceCheckerParseGateCSV": "tests.unit.check.extended_resolve_gates_tests",
    "TestWorkspaceCheckerResolveGates": "tests.unit.check.extended_resolve_gates_tests",
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerRunBandit": "tests.unit.check.extended_gate_bandit_markdown_tests",
    "TestWorkspaceCheckerRunCommand": "tests.unit.check.extended_gate_go_cmd_tests",
    "TestWorkspaceCheckerRunGo": "tests.unit.check.extended_gate_go_cmd_tests",
    "TestWorkspaceCheckerRunMarkdown": "tests.unit.check.extended_gate_bandit_markdown_tests",
    "TestWorkspaceCheckerRunMypy": "tests.unit.check.extended_gate_mypy_pyright_tests",
    "TestWorkspaceCheckerRunPyright": "tests.unit.check.extended_gate_mypy_pyright_tests",
    "TestWorkspaceCheckerSARIFReport": "tests.unit.check.extended_reports_tests",
    "TestWorkspaceCheckerSARIFReportEdgeCases": "tests.unit.check.extended_reports_tests",
    "_shared_fixtures": "tests.unit.check._shared_fixtures",
    "_stubs": "tests.unit.check._stubs",
    "cli_tests": "tests.unit.check.cli_tests",
    "create_check_project_iter_stub": "tests.unit.check._shared_fixtures",
    "create_check_project_stub": "tests.unit.check._shared_fixtures",
    "create_checker_project": "tests.unit.check._shared_fixtures",
    "create_fake_run_projects": "tests.unit.check._shared_fixtures",
    "create_fake_run_raw": "tests.unit.check._shared_fixtures",
    "create_gate_execution": "tests.unit.check._shared_fixtures",
    "extended_cli_entry_tests": "tests.unit.check.extended_cli_entry_tests",
    "extended_config_fixer_errors_tests": "tests.unit.check.extended_config_fixer_errors_tests",
    "extended_config_fixer_tests": "tests.unit.check.extended_config_fixer_tests",
    "extended_error_reporting_tests": "tests.unit.check.extended_error_reporting_tests",
    "extended_gate_bandit_markdown_tests": "tests.unit.check.extended_gate_bandit_markdown_tests",
    "extended_gate_go_cmd_tests": "tests.unit.check.extended_gate_go_cmd_tests",
    "extended_gate_mypy_pyright_tests": "tests.unit.check.extended_gate_mypy_pyright_tests",
    "extended_models_tests": "tests.unit.check.extended_models_tests",
    "extended_project_runners_tests": "tests.unit.check.extended_project_runners_tests",
    "extended_projects_tests": "tests.unit.check.extended_projects_tests",
    "extended_reports_tests": "tests.unit.check.extended_reports_tests",
    "extended_resolve_gates_tests": "tests.unit.check.extended_resolve_gates_tests",
    "extended_run_projects_tests": "tests.unit.check.extended_run_projects_tests",
    "extended_runners_extra_tests": "tests.unit.check.extended_runners_extra_tests",
    "extended_runners_go_tests": "tests.unit.check.extended_runners_go_tests",
    "extended_runners_ruff_tests": "tests.unit.check.extended_runners_ruff_tests",
    "extended_runners_tests": "tests.unit.check.extended_runners_tests",
    "extended_workspace_init_tests": "tests.unit.check.extended_workspace_init_tests",
    "fix_pyrefly_config_tests": "tests.unit.check.fix_pyrefly_config_tests",
    "init_tests": "tests.unit.check.init_tests",
    "main_tests": "tests.unit.check.main_tests",
    "make_cmd_result": "tests.unit.check._stubs",
    "make_gate_exec": "tests.unit.check._stubs",
    "make_issue": "tests.unit.check._stubs",
    "make_project": "tests.unit.check._stubs",
    "patch_gate_run": "tests.unit.check._shared_fixtures",
    "patch_python_dir_detection": "tests.unit.check._shared_fixtures",
    "pyrefly_tests": "tests.unit.check.pyrefly_tests",
    "run_command_failure_check": "tests.unit.check.extended_gate_go_cmd_tests",
    "test_check_main_executes_real_cli": "tests.unit.check.main_tests",
    "test_fix_pyrefly_config_main_executes_real_cli_help": "tests.unit.check.fix_pyrefly_config_tests",
    "test_resolve_gates_maps_type_alias": "tests.unit.check.cli_tests",
    "test_run_cli_rejects_fix_flags_for_run": "tests.unit.check.cli_tests",
    "test_run_cli_run_forwards_fix_and_tool_args": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_one_for_fail": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_two_for_error": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_zero_for_pass": "tests.unit.check.cli_tests",
    "test_run_cli_with_fail_fast_flag": "tests.unit.check.cli_tests",
    "test_run_cli_with_multiple_projects": "tests.unit.check.cli_tests",
    "test_workspace_check_main_returns_error_without_projects": "tests.unit.check.workspace_check_tests",
    "workspace_check_tests": "tests.unit.check.workspace_check_tests",
    "workspace_tests": "tests.unit.check.workspace_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
