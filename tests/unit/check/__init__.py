# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

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
