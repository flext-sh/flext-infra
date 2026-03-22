# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

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
        ProjectResult,
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
    "CheckProjectStub": (
        "tests.unit.check.extended_run_projects_tests",
        "CheckProjectStub",
    ),
    "GateClass": ("tests.unit.check.extended_runners_extra_tests", "GateClass"),
    "ProjectResult": ("tests.unit.check.extended_run_projects_tests", "ProjectResult"),
    "RunCallable": ("tests.unit.check.extended_runners_go_tests", "RunCallable"),
    "TestCheckIssueFormatted": (
        "tests.unit.check.extended_models_tests",
        "TestCheckIssueFormatted",
    ),
    "TestCheckMainEntryPoint": (
        "tests.unit.check.extended_cli_entry_tests",
        "TestCheckMainEntryPoint",
    ),
    "TestCheckProjectRunners": (
        "tests.unit.check.extended_projects_tests",
        "TestCheckProjectRunners",
    ),
    "TestConfigFixerEnsureProjectExcludes": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerEnsureProjectExcludes",
    ),
    "TestConfigFixerExecute": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerExecute",
    ),
    "TestConfigFixerFindPyprojectFiles": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFindPyprojectFiles",
    ),
    "TestConfigFixerFixSearchPaths": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerFixSearchPaths",
    ),
    "TestConfigFixerPathResolution": (
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerPathResolution",
    ),
    "TestConfigFixerProcessFile": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerProcessFile",
    ),
    "TestConfigFixerRemoveIgnoreSubConfig": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRemoveIgnoreSubConfig",
    ),
    "TestConfigFixerRun": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerRun",
    ),
    "TestConfigFixerRunMethods": (
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunMethods",
    ),
    "TestConfigFixerRunWithVerbose": (
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestConfigFixerRunWithVerbose",
    ),
    "TestConfigFixerToArray": (
        "tests.unit.check.extended_config_fixer_tests",
        "TestConfigFixerToArray",
    ),
    "TestErrorReporting": (
        "tests.unit.check.extended_error_reporting_tests",
        "TestErrorReporting",
    ),
    "TestFixPyrelfyCLI": (
        "tests.unit.check.extended_cli_entry_tests",
        "TestFixPyrelfyCLI",
    ),
    "TestFlextInfraCheck": ("tests.unit.check.init_tests", "TestFlextInfraCheck"),
    "TestFlextInfraConfigFixer": (
        "tests.unit.check.pyrefly_tests",
        "TestFlextInfraConfigFixer",
    ),
    "TestFlextInfraWorkspaceChecker": (
        "tests.unit.check.workspace_tests",
        "TestFlextInfraWorkspaceChecker",
    ),
    "TestGoFmtEmptyLinesInOutput": (
        "tests.unit.check.extended_error_reporting_tests",
        "TestGoFmtEmptyLinesInOutput",
    ),
    "TestJsonWriteFailure": (
        "tests.unit.check.extended_project_runners_tests",
        "TestJsonWriteFailure",
    ),
    "TestLintAndFormatPublicMethods": (
        "tests.unit.check.extended_projects_tests",
        "TestLintAndFormatPublicMethods",
    ),
    "TestMarkdownReportEmptyGates": (
        "tests.unit.check.extended_error_reporting_tests",
        "TestMarkdownReportEmptyGates",
    ),
    "TestMarkdownReportSkipsEmptyGates": (
        "tests.unit.check.extended_reports_tests",
        "TestMarkdownReportSkipsEmptyGates",
    ),
    "TestMarkdownReportWithErrors": (
        "tests.unit.check.extended_reports_tests",
        "TestMarkdownReportWithErrors",
    ),
    "TestMypyEmptyLinesInOutput": (
        "tests.unit.check.extended_error_reporting_tests",
        "TestMypyEmptyLinesInOutput",
    ),
    "TestProcessFileReadError": (
        "tests.unit.check.extended_config_fixer_errors_tests",
        "TestProcessFileReadError",
    ),
    "TestProjectResultProperties": (
        "tests.unit.check.extended_models_tests",
        "TestProjectResultProperties",
    ),
    "TestRuffFormatDuplicateFiles": (
        "tests.unit.check.extended_error_reporting_tests",
        "TestRuffFormatDuplicateFiles",
    ),
    "TestRunBandit": ("tests.unit.check.extended_runners_extra_tests", "TestRunBandit"),
    "TestRunCLIExtended": (
        "tests.unit.check.extended_cli_entry_tests",
        "TestRunCLIExtended",
    ),
    "TestRunGo": ("tests.unit.check.extended_runners_go_tests", "TestRunGo"),
    "TestRunMarkdown": (
        "tests.unit.check.extended_runners_extra_tests",
        "TestRunMarkdown",
    ),
    "TestRunMypy": ("tests.unit.check.extended_runners_tests", "TestRunMypy"),
    "TestRunProjectsBehavior": (
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsBehavior",
    ),
    "TestRunProjectsReports": (
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsReports",
    ),
    "TestRunProjectsValidation": (
        "tests.unit.check.extended_run_projects_tests",
        "TestRunProjectsValidation",
    ),
    "TestRunPyrefly": ("tests.unit.check.extended_runners_tests", "TestRunPyrefly"),
    "TestRunPyright": (
        "tests.unit.check.extended_runners_extra_tests",
        "TestRunPyright",
    ),
    "TestRunSingleProject": (
        "tests.unit.check.extended_run_projects_tests",
        "TestRunSingleProject",
    ),
    "TestWorkspaceCheckCLI": (
        "tests.unit.check.extended_cli_entry_tests",
        "TestWorkspaceCheckCLI",
    ),
    "TestWorkspaceCheckerBuildGateResult": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerBuildGateResult",
    ),
    "TestWorkspaceCheckerCollectMarkdownFiles": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerCollectMarkdownFiles",
    ),
    "TestWorkspaceCheckerDirsWithPy": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerDirsWithPy",
    ),
    "TestWorkspaceCheckerErrorSummary": (
        "tests.unit.check.extended_models_tests",
        "TestWorkspaceCheckerErrorSummary",
    ),
    "TestWorkspaceCheckerExecute": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExecute",
    ),
    "TestWorkspaceCheckerExistingCheckDirs": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerExistingCheckDirs",
    ),
    "TestWorkspaceCheckerInitOSError": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitOSError",
    ),
    "TestWorkspaceCheckerInitialization": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerInitialization",
    ),
    "TestWorkspaceCheckerMarkdownReport": (
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReport",
    ),
    "TestWorkspaceCheckerMarkdownReportEdgeCases": (
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerMarkdownReportEdgeCases",
    ),
    "TestWorkspaceCheckerParseGateCSV": (
        "tests.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerParseGateCSV",
    ),
    "TestWorkspaceCheckerResolveGates": (
        "tests.unit.check.extended_resolve_gates_tests",
        "TestWorkspaceCheckerResolveGates",
    ),
    "TestWorkspaceCheckerResolveWorkspaceRootFallback": (
        "tests.unit.check.extended_workspace_init_tests",
        "TestWorkspaceCheckerResolveWorkspaceRootFallback",
    ),
    "TestWorkspaceCheckerRunBandit": (
        "tests.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunBandit",
    ),
    "TestWorkspaceCheckerRunCommand": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunCommand",
    ),
    "TestWorkspaceCheckerRunGo": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "TestWorkspaceCheckerRunGo",
    ),
    "TestWorkspaceCheckerRunMarkdown": (
        "tests.unit.check.extended_gate_bandit_markdown_tests",
        "TestWorkspaceCheckerRunMarkdown",
    ),
    "TestWorkspaceCheckerRunMypy": (
        "tests.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunMypy",
    ),
    "TestWorkspaceCheckerRunPyright": (
        "tests.unit.check.extended_gate_mypy_pyright_tests",
        "TestWorkspaceCheckerRunPyright",
    ),
    "TestWorkspaceCheckerSARIFReport": (
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReport",
    ),
    "TestWorkspaceCheckerSARIFReportEdgeCases": (
        "tests.unit.check.extended_reports_tests",
        "TestWorkspaceCheckerSARIFReportEdgeCases",
    ),
    "run_command_failure_check": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ),
    "test_check_main_executes_real_cli": (
        "tests.unit.check.main_tests",
        "test_check_main_executes_real_cli",
    ),
    "test_fix_pyrefly_config_main_executes_real_cli_help": (
        "tests.unit.check.fix_pyrefly_config_tests",
        "test_fix_pyrefly_config_main_executes_real_cli_help",
    ),
    "test_resolve_gates_maps_type_alias": (
        "tests.unit.check.cli_tests",
        "test_resolve_gates_maps_type_alias",
    ),
    "test_run_cli_run_returns_one_for_fail": (
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_one_for_fail",
    ),
    "test_run_cli_run_returns_two_for_error": (
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_two_for_error",
    ),
    "test_run_cli_run_returns_zero_for_pass": (
        "tests.unit.check.cli_tests",
        "test_run_cli_run_returns_zero_for_pass",
    ),
    "test_run_cli_with_fail_fast_flag": (
        "tests.unit.check.cli_tests",
        "test_run_cli_with_fail_fast_flag",
    ),
    "test_run_cli_with_multiple_projects": (
        "tests.unit.check.cli_tests",
        "test_run_cli_with_multiple_projects",
    ),
    "test_workspace_check_main_returns_error_without_projects": (
        "tests.unit.check.workspace_check_tests",
        "test_workspace_check_main_returns_error_without_projects",
    ),
}

__all__ = [
    "CheckProjectStub",
    "GateClass",
    "ProjectResult",
    "RunCallable",
    "TestCheckIssueFormatted",
    "TestCheckMainEntryPoint",
    "TestCheckProjectRunners",
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
    "TestRunGo",
    "TestRunMarkdown",
    "TestRunMypy",
    "TestRunProjectsBehavior",
    "TestRunProjectsReports",
    "TestRunProjectsValidation",
    "TestRunPyrefly",
    "TestRunPyright",
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
