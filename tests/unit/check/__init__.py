# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .enforcement_fixer_orchestrator_tests import TestsEnforcementFixerOrchestrator
    from .extended_cli_entry_tests import TestWorkspaceCheckCLI
    from .extended_config_fixer_errors_tests import TestConfigFixerPublicBehavior
    from .extended_config_fixer_tests import (
        TestConfigFixerExecute,
        TestConfigFixerProcessFile,
        TestConfigFixerRun,
        TestConfigFixerToArray,
    )
    from .extended_error_reporting_tests import TestGateErrorReportingPublicBehavior
    from .extended_models_tests import (
        TestCheckIssueFormatted,
        TestProjectResultProperties,
        TestRunCommandGateParsing,
        TestWorkspaceCheckerErrorSummary,
    )
    from .extended_project_runners_tests import TestsExtendedProjectRunners
    from .extended_resolve_gates_tests import (
        TestWorkspaceCheckerCiGateRules,
        TestWorkspaceCheckerResolveGates,
    )
    from .extended_run_projects_tests import TestRunProjectsPublicBehavior
    from .extended_runners_extra_tests import TestExtendedRunnerExtras
    from .extended_runners_tests import TestRunnerPublicBehavior
    from .fix_pyrefly_config_tests import (
        test_fix_pyrefly_config_main_executes_real_cli_help,
    )
    from .init_tests import TestFlextInfraCheck
    from .main_tests import test_check_main_executes_real_cli
    from .pyrefly_tests import TestFlextInfraConfigFixer
    from .test_cli import TestWorkspaceCheckCli
    from .tests_workspace_check import (
        test_workspace_check_main_returns_error_without_projects,
    )
    from .workspace_tests import TestFlextInfraWorkspaceChecker
__all__: tuple[str, ...] = (
    "TestCheckIssueFormatted",
    "TestConfigFixerExecute",
    "TestConfigFixerProcessFile",
    "TestConfigFixerPublicBehavior",
    "TestConfigFixerRun",
    "TestConfigFixerToArray",
    "TestExtendedRunnerExtras",
    "TestFlextInfraCheck",
    "TestFlextInfraConfigFixer",
    "TestFlextInfraWorkspaceChecker",
    "TestGateErrorReportingPublicBehavior",
    "TestProjectResultProperties",
    "TestRunCommandGateParsing",
    "TestRunProjectsPublicBehavior",
    "TestRunnerPublicBehavior",
    "TestWorkspaceCheckCLI",
    "TestWorkspaceCheckCli",
    "TestWorkspaceCheckerCiGateRules",
    "TestWorkspaceCheckerErrorSummary",
    "TestWorkspaceCheckerResolveGates",
    "TestsEnforcementFixerOrchestrator",
    "TestsExtendedProjectRunners",
    "test_check_main_executes_real_cli",
    "test_fix_pyrefly_config_main_executes_real_cli_help",
    "test_workspace_check_main_returns_error_without_projects",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".enforcement_fixer_orchestrator_tests": (
                "TestsEnforcementFixerOrchestrator",
            ),
            ".extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
            ".extended_config_fixer_errors_tests": ("TestConfigFixerPublicBehavior",),
            ".extended_config_fixer_tests": (
                "TestConfigFixerExecute",
                "TestConfigFixerProcessFile",
                "TestConfigFixerRun",
                "TestConfigFixerToArray",
            ),
            ".extended_error_reporting_tests": (
                "TestGateErrorReportingPublicBehavior",
            ),
            ".extended_models_tests": (
                "TestCheckIssueFormatted",
                "TestProjectResultProperties",
                "TestRunCommandGateParsing",
                "TestWorkspaceCheckerErrorSummary",
            ),
            ".extended_project_runners_tests": ("TestsExtendedProjectRunners",),
            ".extended_resolve_gates_tests": (
                "TestWorkspaceCheckerCiGateRules",
                "TestWorkspaceCheckerResolveGates",
            ),
            ".extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
            ".extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
            ".extended_runners_tests": ("TestRunnerPublicBehavior",),
            ".fix_pyrefly_config_tests": (
                "test_fix_pyrefly_config_main_executes_real_cli_help",
            ),
            ".init_tests": ("TestFlextInfraCheck",),
            ".main_tests": ("test_check_main_executes_real_cli",),
            ".pyrefly_tests": ("TestFlextInfraConfigFixer",),
            ".test_cli": ("TestWorkspaceCheckCli",),
            ".tests_workspace_check": (
                "test_workspace_check_main_returns_error_without_projects",
            ),
            ".workspace_tests": ("TestFlextInfraWorkspaceChecker",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
