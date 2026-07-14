# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from .enforcement_fixer_orchestrator_tests import (
    TestsEnforcementFixerOrchestrator as TestsEnforcementFixerOrchestrator,
)
from .extended_cli_entry_tests import TestWorkspaceCheckCLI as TestWorkspaceCheckCLI
from .extended_config_fixer_errors_tests import (
    TestConfigFixerPublicBehavior as TestConfigFixerPublicBehavior,
)
from .extended_config_fixer_tests import (
    TestConfigFixerExecute as TestConfigFixerExecute,
    TestConfigFixerProcessFile as TestConfigFixerProcessFile,
    TestConfigFixerRun as TestConfigFixerRun,
    TestConfigFixerToArray as TestConfigFixerToArray,
)
from .extended_error_reporting_tests import (
    TestGateErrorReportingPublicBehavior as TestGateErrorReportingPublicBehavior,
)
from .extended_models_tests import (
    TestCheckIssueFormatted as TestCheckIssueFormatted,
    TestProjectResultProperties as TestProjectResultProperties,
    TestRunCommandGateParsing as TestRunCommandGateParsing,
    TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
)
from .extended_project_runners_tests import (
    TestsExtendedProjectRunners as TestsExtendedProjectRunners,
)
from .extended_resolve_gates_tests import (
    TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
)
from .extended_run_projects_tests import (
    TestRunProjectsPublicBehavior as TestRunProjectsPublicBehavior,
)
from .extended_runners_extra_tests import (
    TestExtendedRunnerExtras as TestExtendedRunnerExtras,
)
from .extended_runners_tests import TestRunnerPublicBehavior as TestRunnerPublicBehavior
from .init_tests import TestFlextInfraCheck as TestFlextInfraCheck
from .pyrefly_tests import TestFlextInfraConfigFixer as TestFlextInfraConfigFixer
from .tests_cli import TestWorkspaceCheckCli as TestWorkspaceCheckCli
from .workspace_tests import (
    TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
)

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
    "TestWorkspaceCheckerErrorSummary",
    "TestWorkspaceCheckerResolveGates",
    "TestsEnforcementFixerOrchestrator",
    "TestsExtendedProjectRunners",
)
