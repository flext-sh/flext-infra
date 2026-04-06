# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.check._shared_fixtures as _tests_unit_check__shared_fixtures

    _shared_fixtures = _tests_unit_check__shared_fixtures
    import tests.unit.check._stubs as _tests_unit_check__stubs
    from tests.unit.check._shared_fixtures import (
        RunProjectsMock,
        create_check_project_iter_stub,
        create_check_project_stub,
        create_checker_project,
        create_fake_run_projects,
        create_fake_run_raw,
        create_gate_context,
        create_gate_execution,
        patch_gate_run,
        patch_gate_run_sequence,
        patch_python_dir_detection,
        run_gate_check,
    )

    _stubs = _tests_unit_check__stubs
    import tests.unit.check.cli_tests as _tests_unit_check_cli_tests
    from tests.unit.check._stubs import Spy, make_issue, make_project

    cli_tests = _tests_unit_check_cli_tests
    import tests.unit.check.extended_cli_entry_tests as _tests_unit_check_extended_cli_entry_tests
    from tests.unit.check.cli_tests import (
        test_resolve_gates_maps_type_alias,
        test_run_cli_rejects_shared_dry_run_flag,
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
        GateClass,
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
        TestRunProjectFixMode,
        TestRunProjectsBehavior,
        TestRunProjectsReports,
        TestRunProjectsValidation,
        TestRunSingleProject,
    )

    extended_runners_extra_tests = _tests_unit_check_extended_runners_extra_tests
    import tests.unit.check.extended_runners_go_tests as _tests_unit_check_extended_runners_go_tests
    from tests.unit.check.extended_runners_extra_tests import (
        TestRunBandit,
        TestRunMarkdown,
        TestRunPyright,
    )

    extended_runners_go_tests = _tests_unit_check_extended_runners_go_tests
    import tests.unit.check.extended_runners_ruff_tests as _tests_unit_check_extended_runners_ruff_tests
    from tests.unit.check.extended_runners_go_tests import TestRunGo

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
    from tests.unit.check.workspace_tests import TestFlextInfraWorkspaceChecker

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "GateClass": "tests.unit.check.extended_gate_go_cmd_tests",
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
    "TestWorkspaceCheckerParseGateCSV": "tests.unit.check.extended_resolve_gates_tests",
    "TestWorkspaceCheckerResolveGates": "tests.unit.check.extended_resolve_gates_tests",
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": "tests.unit.check.extended_workspace_init_tests",
    "TestWorkspaceCheckerRunBandit": "tests.unit.check.extended_gate_bandit_markdown_tests",
    "TestWorkspaceCheckerRunCommand": "tests.unit.check.extended_gate_go_cmd_tests",
    "TestWorkspaceCheckerRunGo": "tests.unit.check.extended_gate_go_cmd_tests",
    "TestWorkspaceCheckerRunMarkdown": "tests.unit.check.extended_gate_bandit_markdown_tests",
    "TestWorkspaceCheckerRunMypy": "tests.unit.check.extended_gate_mypy_pyright_tests",
    "TestWorkspaceCheckerRunPyright": "tests.unit.check.extended_gate_mypy_pyright_tests",
    "_shared_fixtures": "tests.unit.check._shared_fixtures",
    "_stubs": "tests.unit.check._stubs",
    "cli_tests": "tests.unit.check.cli_tests",
    "create_check_project_iter_stub": "tests.unit.check._shared_fixtures",
    "create_check_project_stub": "tests.unit.check._shared_fixtures",
    "create_checker_project": "tests.unit.check._shared_fixtures",
    "create_fake_run_projects": "tests.unit.check._shared_fixtures",
    "create_fake_run_raw": "tests.unit.check._shared_fixtures",
    "create_gate_context": "tests.unit.check._shared_fixtures",
    "create_gate_execution": "tests.unit.check._shared_fixtures",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
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
    "extended_resolve_gates_tests": "tests.unit.check.extended_resolve_gates_tests",
    "extended_run_projects_tests": "tests.unit.check.extended_run_projects_tests",
    "extended_runners_extra_tests": "tests.unit.check.extended_runners_extra_tests",
    "extended_runners_go_tests": "tests.unit.check.extended_runners_go_tests",
    "extended_runners_ruff_tests": "tests.unit.check.extended_runners_ruff_tests",
    "extended_runners_tests": "tests.unit.check.extended_runners_tests",
    "extended_workspace_init_tests": "tests.unit.check.extended_workspace_init_tests",
    "fix_pyrefly_config_tests": "tests.unit.check.fix_pyrefly_config_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.check.init_tests",
    "main_tests": "tests.unit.check.main_tests",
    "make_issue": "tests.unit.check._stubs",
    "make_project": "tests.unit.check._stubs",
    "patch_gate_run": "tests.unit.check._shared_fixtures",
    "patch_gate_run_sequence": "tests.unit.check._shared_fixtures",
    "patch_python_dir_detection": "tests.unit.check._shared_fixtures",
    "pyrefly_tests": "tests.unit.check.pyrefly_tests",
    "r": ("flext_core.result", "FlextResult"),
    "run_command_failure_check": "tests.unit.check.extended_gate_go_cmd_tests",
    "run_gate_check": "tests.unit.check._shared_fixtures",
    "s": ("flext_core.service", "FlextService"),
    "test_check_main_executes_real_cli": "tests.unit.check.main_tests",
    "test_fix_pyrefly_config_main_executes_real_cli_help": "tests.unit.check.fix_pyrefly_config_tests",
    "test_resolve_gates_maps_type_alias": "tests.unit.check.cli_tests",
    "test_run_cli_rejects_shared_dry_run_flag": "tests.unit.check.cli_tests",
    "test_run_cli_run_forwards_fix_and_tool_args": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_one_for_fail": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_two_for_error": "tests.unit.check.cli_tests",
    "test_run_cli_run_returns_zero_for_pass": "tests.unit.check.cli_tests",
    "test_run_cli_with_fail_fast_flag": "tests.unit.check.cli_tests",
    "test_run_cli_with_multiple_projects": "tests.unit.check.cli_tests",
    "test_workspace_check_main_returns_error_without_projects": "tests.unit.check.workspace_check_tests",
    "workspace_check_tests": "tests.unit.check.workspace_check_tests",
    "workspace_tests": "tests.unit.check.workspace_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "GateClass",
    "RunProjectsMock",
    "Spy",
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
    "TestWorkspaceCheckerParseGateCSV",
    "TestWorkspaceCheckerResolveGates",
    "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    "TestWorkspaceCheckerRunBandit",
    "TestWorkspaceCheckerRunCommand",
    "TestWorkspaceCheckerRunGo",
    "TestWorkspaceCheckerRunMarkdown",
    "TestWorkspaceCheckerRunMypy",
    "TestWorkspaceCheckerRunPyright",
    "_shared_fixtures",
    "_stubs",
    "cli_tests",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_context",
    "create_gate_execution",
    "d",
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
    "fix_pyrefly_config_tests",
    "h",
    "init_tests",
    "main_tests",
    "make_issue",
    "make_project",
    "patch_gate_run",
    "patch_gate_run_sequence",
    "patch_python_dir_detection",
    "pyrefly_tests",
    "r",
    "run_command_failure_check",
    "run_gate_check",
    "s",
    "test_check_main_executes_real_cli",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_resolve_gates_maps_type_alias",
    "test_run_cli_rejects_shared_dry_run_flag",
    "test_run_cli_run_forwards_fix_and_tool_args",
    "test_run_cli_run_returns_one_for_fail",
    "test_run_cli_run_returns_two_for_error",
    "test_run_cli_run_returns_zero_for_pass",
    "test_run_cli_with_fail_fast_flag",
    "test_run_cli_with_multiple_projects",
    "test_workspace_check_main_returns_error_without_projects",
    "workspace_check_tests",
    "workspace_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
