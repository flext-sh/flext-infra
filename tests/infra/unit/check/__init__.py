# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes


if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .cli_tests import (
        test_resolve_gates_maps_type_alias,
        test_run_cli_run_returns_one_for_fail,
        test_run_cli_run_returns_two_for_error,
        test_run_cli_run_returns_zero_for_pass,
        test_run_cli_with_fail_fast_flag,
        test_run_cli_with_multiple_projects,
    )
    from .extended_cli_entry_tests import (
        TestCheckMainEntryPoint,
        TestFixPyrelfyCLI,
        TestRunCLIExtended,
        TestWorkspaceCheckCLI,
    )
    from .extended_config_fixer_errors_tests import (
        TestConfigFixerPathResolution,
        TestConfigFixerRunMethods,
        TestConfigFixerRunWithVerbose,
        TestProcessFileReadError,
    )
    from .extended_config_fixer_tests import (
        TestConfigFixerEnsureProjectExcludes,
        TestConfigFixerExecute,
        TestConfigFixerFindPyprojectFiles,
        TestConfigFixerFixSearchPaths,
        TestConfigFixerProcessFile,
        TestConfigFixerRemoveIgnoreSubConfig,
        TestConfigFixerRun,
        TestConfigFixerToArray,
    )
    from .extended_error_reporting_tests import (
        TestErrorReporting,
        TestGoFmtEmptyLinesInOutput,
        TestMarkdownReportEmptyGates,
        TestMypyEmptyLinesInOutput,
        TestRuffFormatDuplicateFiles,
    )
    from .extended_gate_bandit_markdown_tests import (
        TestWorkspaceCheckerRunBandit,
        TestWorkspaceCheckerRunMarkdown,
    )
    from .extended_gate_go_cmd_tests import (
        TestWorkspaceCheckerCollectMarkdownFiles,
        TestWorkspaceCheckerRunCommand,
        TestWorkspaceCheckerRunGo,
        run_command_failure_check,
    )
    from .extended_gate_mypy_pyright_tests import (
        TestWorkspaceCheckerRunMypy,
        TestWorkspaceCheckerRunPyright,
    )
    from .extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestWorkspaceCheckerErrorSummary,
    )
    from .extended_project_runners_tests import TestJsonWriteFailure
    from .extended_projects_tests import (
        TestCheckProjectRunners,
        TestLintAndFormatPublicMethods,
    )
    from .extended_reports_tests import (
        TestMarkdownReportSkipsEmptyGates,
        TestMarkdownReportWithErrors,
        TestWorkspaceCheckerMarkdownReport,
        TestWorkspaceCheckerMarkdownReportEdgeCases,
        TestWorkspaceCheckerSARIFReport,
        TestWorkspaceCheckerSARIFReportEdgeCases,
    )
    from .extended_resolve_gates_tests import (
        TestWorkspaceCheckerParseGateCSV,
        TestWorkspaceCheckerResolveGates,
    )
    from .extended_run_projects_tests import (
        CheckProjectStub,
        TestRunProjectsBehavior,
        TestRunProjectsReports,
        TestRunProjectsValidation,
        TestRunSingleProject,
    )
    from .extended_runners_extra_tests import (
        GateClass,
        TestRunBandit,
        TestRunMarkdown,
        TestRunPyright,
    )
    from .extended_runners_go_tests import RunCallable, TestRunGo
    from .extended_runners_ruff_tests import (
        TestCollectMarkdownFiles,
        TestRunCommand,
        TestRunRuffFormat,
        TestRunRuffLint,
    )
    from .extended_runners_tests import TestRunMypy, TestRunPyrefly
    from .extended_workspace_init_tests import (
        TestWorkspaceCheckerBuildGateResult,
        TestWorkspaceCheckerDirsWithPy,
        TestWorkspaceCheckerExecute,
        TestWorkspaceCheckerExistingCheckDirs,
        TestWorkspaceCheckerInitialization,
        TestWorkspaceCheckerInitOSError,
        TestWorkspaceCheckerResolveWorkspaceRootFallback,
    )
    from .fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help,
    )
    from .init_tests import TestFlextInfraCheck
    from .main_tests import test_check_main_executes_real_cli
    from .pyrefly_tests import TestFlextInfraConfigFixer
    from .workspace_check_tests import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from .workspace_tests import TestFlextInfraWorkspaceChecker

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CheckProjectStub": ("tests.infra.unit.check.extended_run_projects_tests", "CheckProjectStub"),
    "GateClass": ("tests.infra.unit.check.extended_runners_extra_tests", "GateClass"),
    "RunCallable": ("tests.infra.unit.check.extended_runners_go_tests", "RunCallable"),
    "TestCheckIssueFormatted": ("tests.infra.unit.check.extended_models_tests", "TestCheckIssueFormatted"),
    "TestCheckMainEntryPoint": ("tests.infra.unit.check.extended_cli_entry_tests", "TestCheckMainEntryPoint"),
    "TestCheckProjectRunners": ("tests.infra.unit.check.extended_projects_tests", "TestCheckProjectRunners"),
    "TestCollectMarkdownFiles": ("tests.infra.unit.check.extended_runners_ruff_tests", "TestCollectMarkdownFiles"),
    "TestConfigFixerEnsureProjectExcludes": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerEnsureProjectExcludes"),
    "TestConfigFixerExecute": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerExecute"),
    "TestConfigFixerFindPyprojectFiles": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerFindPyprojectFiles"),
    "TestConfigFixerFixSearchPaths": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerFixSearchPaths"),
    "TestConfigFixerPathResolution": ("tests.infra.unit.check.extended_config_fixer_errors_tests", "TestConfigFixerPathResolution"),
    "TestConfigFixerProcessFile": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerProcessFile"),
    "TestConfigFixerRemoveIgnoreSubConfig": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerRemoveIgnoreSubConfig"),
    "TestConfigFixerRun": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerRun"),
    "TestConfigFixerRunMethods": ("tests.infra.unit.check.extended_config_fixer_errors_tests", "TestConfigFixerRunMethods"),
    "TestConfigFixerRunWithVerbose": ("tests.infra.unit.check.extended_config_fixer_errors_tests", "TestConfigFixerRunWithVerbose"),
    "TestConfigFixerToArray": ("tests.infra.unit.check.extended_config_fixer_tests", "TestConfigFixerToArray"),
    "TestErrorReporting": ("tests.infra.unit.check.extended_error_reporting_tests", "TestErrorReporting"),
    "TestFixPyrelfyCLI": ("tests.infra.unit.check.extended_cli_entry_tests", "TestFixPyrelfyCLI"),
    "TestFlextInfraCheck": ("tests.infra.unit.check.init_tests", "TestFlextInfraCheck"),
    "TestFlextInfraConfigFixer": ("tests.infra.unit.check.pyrefly_tests", "TestFlextInfraConfigFixer"),
    "TestFlextInfraWorkspaceChecker": ("tests.infra.unit.check.workspace_tests", "TestFlextInfraWorkspaceChecker"),
    "TestGoFmtEmptyLinesInOutput": ("tests.infra.unit.check.extended_error_reporting_tests", "TestGoFmtEmptyLinesInOutput"),
    "TestJsonWriteFailure": ("tests.infra.unit.check.extended_project_runners_tests", "TestJsonWriteFailure"),
    "TestLintAndFormatPublicMethods": ("tests.infra.unit.check.extended_projects_tests", "TestLintAndFormatPublicMethods"),
    "TestMarkdownReportEmptyGates": ("tests.infra.unit.check.extended_error_reporting_tests", "TestMarkdownReportEmptyGates"),
    "TestMarkdownReportSkipsEmptyGates": ("tests.infra.unit.check.extended_reports_tests", "TestMarkdownReportSkipsEmptyGates"),
    "TestMarkdownReportWithErrors": ("tests.infra.unit.check.extended_reports_tests", "TestMarkdownReportWithErrors"),
    "TestMypyEmptyLinesInOutput": ("tests.infra.unit.check.extended_error_reporting_tests", "TestMypyEmptyLinesInOutput"),
    "TestProcessFileReadError": ("tests.infra.unit.check.extended_config_fixer_errors_tests", "TestProcessFileReadError"),
    "TestProjectResultProperties": ("tests.infra.unit.check.extended_models_tests", "TestProjectResultProperties"),
    "TestRuffFormatDuplicateFiles": ("tests.infra.unit.check.extended_error_reporting_tests", "TestRuffFormatDuplicateFiles"),
    "TestRunBandit": ("tests.infra.unit.check.extended_runners_extra_tests", "TestRunBandit"),
    "TestRunCLIExtended": ("tests.infra.unit.check.extended_cli_entry_tests", "TestRunCLIExtended"),
    "TestRunCommand": ("tests.infra.unit.check.extended_runners_ruff_tests", "TestRunCommand"),
    "TestRunGo": ("tests.infra.unit.check.extended_runners_go_tests", "TestRunGo"),
    "TestRunMarkdown": ("tests.infra.unit.check.extended_runners_extra_tests", "TestRunMarkdown"),
    "TestRunMypy": ("tests.infra.unit.check.extended_runners_tests", "TestRunMypy"),
    "TestRunProjectsBehavior": ("tests.infra.unit.check.extended_run_projects_tests", "TestRunProjectsBehavior"),
    "TestRunProjectsReports": ("tests.infra.unit.check.extended_run_projects_tests", "TestRunProjectsReports"),
    "TestRunProjectsValidation": ("tests.infra.unit.check.extended_run_projects_tests", "TestRunProjectsValidation"),
    "TestRunPyrefly": ("tests.infra.unit.check.extended_runners_tests", "TestRunPyrefly"),
    "TestRunPyright": ("tests.infra.unit.check.extended_runners_extra_tests", "TestRunPyright"),
    "TestRunRuffFormat": ("tests.infra.unit.check.extended_runners_ruff_tests", "TestRunRuffFormat"),
    "TestRunRuffLint": ("tests.infra.unit.check.extended_runners_ruff_tests", "TestRunRuffLint"),
    "TestRunSingleProject": ("tests.infra.unit.check.extended_run_projects_tests", "TestRunSingleProject"),
    "TestWorkspaceCheckCLI": ("tests.infra.unit.check.extended_cli_entry_tests", "TestWorkspaceCheckCLI"),
    "TestWorkspaceCheckerBuildGateResult": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerBuildGateResult"),
    "TestWorkspaceCheckerCollectMarkdownFiles": ("tests.infra.unit.check.extended_gate_go_cmd_tests", "TestWorkspaceCheckerCollectMarkdownFiles"),
    "TestWorkspaceCheckerDirsWithPy": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerDirsWithPy"),
    "TestWorkspaceCheckerErrorSummary": ("tests.infra.unit.check.extended_models_tests", "TestWorkspaceCheckerErrorSummary"),
    "TestWorkspaceCheckerExecute": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerExecute"),
    "TestWorkspaceCheckerExistingCheckDirs": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerExistingCheckDirs"),
    "TestWorkspaceCheckerInitOSError": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerInitOSError"),
    "TestWorkspaceCheckerInitialization": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerInitialization"),
    "TestWorkspaceCheckerMarkdownReport": ("tests.infra.unit.check.extended_reports_tests", "TestWorkspaceCheckerMarkdownReport"),
    "TestWorkspaceCheckerMarkdownReportEdgeCases": ("tests.infra.unit.check.extended_reports_tests", "TestWorkspaceCheckerMarkdownReportEdgeCases"),
    "TestWorkspaceCheckerParseGateCSV": ("tests.infra.unit.check.extended_resolve_gates_tests", "TestWorkspaceCheckerParseGateCSV"),
    "TestWorkspaceCheckerResolveGates": ("tests.infra.unit.check.extended_resolve_gates_tests", "TestWorkspaceCheckerResolveGates"),
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": ("tests.infra.unit.check.extended_workspace_init_tests", "TestWorkspaceCheckerResolveWorkspaceRootFallback"),
    "TestWorkspaceCheckerRunBandit": ("tests.infra.unit.check.extended_gate_bandit_markdown_tests", "TestWorkspaceCheckerRunBandit"),
    "TestWorkspaceCheckerRunCommand": ("tests.infra.unit.check.extended_gate_go_cmd_tests", "TestWorkspaceCheckerRunCommand"),
    "TestWorkspaceCheckerRunGo": ("tests.infra.unit.check.extended_gate_go_cmd_tests", "TestWorkspaceCheckerRunGo"),
    "TestWorkspaceCheckerRunMarkdown": ("tests.infra.unit.check.extended_gate_bandit_markdown_tests", "TestWorkspaceCheckerRunMarkdown"),
    "TestWorkspaceCheckerRunMypy": ("tests.infra.unit.check.extended_gate_mypy_pyright_tests", "TestWorkspaceCheckerRunMypy"),
    "TestWorkspaceCheckerRunPyright": ("tests.infra.unit.check.extended_gate_mypy_pyright_tests", "TestWorkspaceCheckerRunPyright"),
    "TestWorkspaceCheckerSARIFReport": ("tests.infra.unit.check.extended_reports_tests", "TestWorkspaceCheckerSARIFReport"),
    "TestWorkspaceCheckerSARIFReportEdgeCases": ("tests.infra.unit.check.extended_reports_tests", "TestWorkspaceCheckerSARIFReportEdgeCases"),
    "run_command_failure_check": ("tests.infra.unit.check.extended_gate_go_cmd_tests", "run_command_failure_check"),
    "test_check_main_executes_real_cli": ("tests.infra.unit.check.main_tests", "test_check_main_executes_real_cli"),
    "test_fix_pyrefly_config_main_executes_real_cli_help": ("tests.infra.unit.check.fix_pyrefly_config_tests", "test_fix_pyrefly_config_main_executes_real_cli_help"),
    "test_resolve_gates_maps_type_alias": ("tests.infra.unit.check.cli_tests", "test_resolve_gates_maps_type_alias"),
    "test_run_cli_run_returns_one_for_fail": ("tests.infra.unit.check.cli_tests", "test_run_cli_run_returns_one_for_fail"),
    "test_run_cli_run_returns_two_for_error": ("tests.infra.unit.check.cli_tests", "test_run_cli_run_returns_two_for_error"),
    "test_run_cli_run_returns_zero_for_pass": ("tests.infra.unit.check.cli_tests", "test_run_cli_run_returns_zero_for_pass"),
    "test_run_cli_with_fail_fast_flag": ("tests.infra.unit.check.cli_tests", "test_run_cli_with_fail_fast_flag"),
    "test_run_cli_with_multiple_projects": ("tests.infra.unit.check.cli_tests", "test_run_cli_with_multiple_projects"),
    "test_workspace_check_main_returns_error_without_projects": ("tests.infra.unit.check.workspace_check_tests", "test_workspace_check_main_returns_error_without_projects"),
}

__all__ = [
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
    "TestRunProjectsBehavior",
    "TestRunProjectsReports",
    "TestRunProjectsValidation",
    "TestRunPyrefly",
    "TestRunPyright",
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
    "run_command_failure_check",
    "test_check_main_executes_real_cli",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_resolve_gates_maps_type_alias",
    "test_run_cli_run_returns_one_for_fail",
    "test_run_cli_run_returns_two_for_error",
    "test_run_cli_run_returns_zero_for_pass",
    "test_run_cli_with_fail_fast_flag",
    "test_run_cli_with_multiple_projects",
    "test_workspace_check_main_returns_error_without_projects",
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
