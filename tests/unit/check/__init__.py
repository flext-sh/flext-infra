# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import abstraction_boundary_gate_tests as abstraction_boundary_gate_tests
    from . import (
        extended_gate_bandit_markdown_tests as extended_gate_bandit_markdown_tests,
    )
    from . import extended_gate_mypy_pyright_tests as extended_gate_mypy_pyright_tests
    from . import extended_runners_ruff_tests as extended_runners_ruff_tests
    from . import extended_workspace_init_tests as extended_workspace_init_tests
    from . import fix_pyrefly_config_tests as fix_pyrefly_config_tests
    from . import gate_registry_tests as gate_registry_tests
    from . import loc_cap_gate_tests as loc_cap_gate_tests
    from . import main_tests as main_tests
    from . import silent_failure_gate_tests as silent_failure_gate_tests
    from . import smells_gate_tests as smells_gate_tests
    from . import tests_workspace_check as tests_workspace_check
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

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
    from .init_tests import TestFlextInfraCheck
    from .pyrefly_tests import TestFlextInfraConfigFixer
    from .test_cli import TestWorkspaceCheckCli
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
    "abstraction_boundary_gate_tests",
    "c",
    "d",
    "e",
    "extended_gate_bandit_markdown_tests",
    "extended_gate_mypy_pyright_tests",
    "extended_runners_ruff_tests",
    "extended_workspace_init_tests",
    "fix_pyrefly_config_tests",
    "gate_registry_tests",
    "h",
    "loc_cap_gate_tests",
    "m",
    "main_tests",
    "p",
    "r",
    "s",
    "silent_failure_gate_tests",
    "smells_gate_tests",
    "t",
    "td",
    "tests_workspace_check",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".abstraction_boundary_gate_tests": ("abstraction_boundary_gate_tests",),
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
            ".extended_gate_bandit_markdown_tests": (
                "extended_gate_bandit_markdown_tests",
            ),
            ".extended_gate_mypy_pyright_tests": ("extended_gate_mypy_pyright_tests",),
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
            ".extended_runners_ruff_tests": ("extended_runners_ruff_tests",),
            ".extended_runners_tests": ("TestRunnerPublicBehavior",),
            ".extended_workspace_init_tests": ("extended_workspace_init_tests",),
            ".fix_pyrefly_config_tests": ("fix_pyrefly_config_tests",),
            ".gate_registry_tests": ("gate_registry_tests",),
            ".init_tests": ("TestFlextInfraCheck",),
            ".loc_cap_gate_tests": ("loc_cap_gate_tests",),
            ".main_tests": ("main_tests",),
            ".pyrefly_tests": ("TestFlextInfraConfigFixer",),
            ".silent_failure_gate_tests": ("silent_failure_gate_tests",),
            ".smells_gate_tests": ("smells_gate_tests",),
            ".test_cli": ("TestWorkspaceCheckCli",),
            ".tests_workspace_check": ("tests_workspace_check",),
            ".workspace_tests": ("TestFlextInfraWorkspaceChecker",),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
