# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".extended_cli_entry_tests": ("extended_cli_entry_tests",),
        ".extended_config_fixer_errors_tests": ("extended_config_fixer_errors_tests",),
        ".extended_config_fixer_tests": ("extended_config_fixer_tests",),
        ".extended_error_reporting_tests": ("extended_error_reporting_tests",),
        ".extended_gate_bandit_markdown_tests": (
            "extended_gate_bandit_markdown_tests",
        ),
        ".extended_gate_go_cmd_tests": ("extended_gate_go_cmd_tests",),
        ".extended_gate_mypy_pyright_tests": ("extended_gate_mypy_pyright_tests",),
        ".extended_models_tests": ("extended_models_tests",),
        ".extended_project_runners_tests": ("extended_project_runners_tests",),
        ".extended_resolve_gates_tests": ("extended_resolve_gates_tests",),
        ".extended_run_projects_tests": ("extended_run_projects_tests",),
        ".extended_runners_extra_tests": ("extended_runners_extra_tests",),
        ".extended_runners_ruff_tests": ("extended_runners_ruff_tests",),
        ".extended_runners_tests": ("extended_runners_tests",),
        ".extended_workspace_init_tests": ("extended_workspace_init_tests",),
        ".fix_pyrefly_config_tests": ("fix_pyrefly_config_tests",),
        ".init_tests": ("init_tests",),
        ".main_tests": ("main_tests",),
        ".pyrefly_tests": ("pyrefly_tests",),
        ".silent_failure_gate_tests": ("silent_failure_gate_tests",),
        ".tests_cli": ("tests_cli",),
        ".tests_workspace_check": ("tests_workspace_check",),
        ".workspace_tests": ("workspace_tests",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
