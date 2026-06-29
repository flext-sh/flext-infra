# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.check.extended_cli_entry_tests import (
        TestWorkspaceCheckCLI as TestWorkspaceCheckCLI,
    )
    from tests.unit.check.extended_config_fixer_errors_tests import (
        TestConfigFixerPublicBehavior as TestConfigFixerPublicBehavior,
    )
    from tests.unit.check.extended_config_fixer_tests import (
        TestConfigFixerExecute as TestConfigFixerExecute,
        TestConfigFixerProcessFile as TestConfigFixerProcessFile,
        TestConfigFixerRun as TestConfigFixerRun,
        TestConfigFixerToArray as TestConfigFixerToArray,
    )
    from tests.unit.check.extended_error_reporting_tests import (
        TestGateErrorReportingPublicBehavior as TestGateErrorReportingPublicBehavior,
    )
    from tests.unit.check.extended_models_tests import (
        TestCheckIssueFormatted as TestCheckIssueFormatted,
        TestProjectResultProperties as TestProjectResultProperties,
        TestRunCommandGateParsing as TestRunCommandGateParsing,
        TestWorkspaceCheckerErrorSummary as TestWorkspaceCheckerErrorSummary,
    )
    from tests.unit.check.extended_project_runners_tests import (
        TestsExtendedProjectRunners as TestsExtendedProjectRunners,
    )
    from tests.unit.check.extended_resolve_gates_tests import (
        TestWorkspaceCheckerResolveGates as TestWorkspaceCheckerResolveGates,
    )
    from tests.unit.check.extended_run_projects_tests import (
        TestRunProjectsPublicBehavior as TestRunProjectsPublicBehavior,
    )
    from tests.unit.check.extended_runners_extra_tests import (
        TestExtendedRunnerExtras as TestExtendedRunnerExtras,
    )
    from tests.unit.check.extended_runners_tests import (
        TestRunnerPublicBehavior as TestRunnerPublicBehavior,
    )
    from tests.unit.check.init_tests import TestFlextInfraCheck as TestFlextInfraCheck
    from tests.unit.check.pyrefly_tests import (
        TestFlextInfraConfigFixer as TestFlextInfraConfigFixer,
    )
    from tests.unit.check.tests_cli import (
        TestWorkspaceCheckCli as TestWorkspaceCheckCli,
    )
    from tests.unit.check.workspace_tests import (
        TestFlextInfraWorkspaceChecker as TestFlextInfraWorkspaceChecker,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".abstraction_boundary_gate_tests": ("abstraction_boundary_gate_tests",),
        ".extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
        ".extended_config_fixer_errors_tests": ("TestConfigFixerPublicBehavior",),
        ".extended_config_fixer_tests": (
            "TestConfigFixerExecute",
            "TestConfigFixerProcessFile",
            "TestConfigFixerRun",
            "TestConfigFixerToArray",
        ),
        ".extended_error_reporting_tests": ("TestGateErrorReportingPublicBehavior",),
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
        ".extended_resolve_gates_tests": ("TestWorkspaceCheckerResolveGates",),
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
        ".tests_cli": ("TestWorkspaceCheckCli",),
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
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
