# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "c": ("flext_core.constants", "FlextConstants"),
    "cli_tests": "tests.unit.check.cli_tests",
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
    "m": ("flext_core.models", "FlextModels"),
    "main_tests": "tests.unit.check.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pyrefly_tests": "tests.unit.check.pyrefly_tests",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "workspace_check_tests": "tests.unit.check.workspace_check_tests",
    "workspace_tests": "tests.unit.check.workspace_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
