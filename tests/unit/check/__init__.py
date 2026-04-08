# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.check.cli_tests as _tests_unit_check_cli_tests

    cli_tests = _tests_unit_check_cli_tests
    import tests.unit.check.extended_cli_entry_tests as _tests_unit_check_extended_cli_entry_tests

    extended_cli_entry_tests = _tests_unit_check_extended_cli_entry_tests
    import tests.unit.check.extended_config_fixer_errors_tests as _tests_unit_check_extended_config_fixer_errors_tests

    extended_config_fixer_errors_tests = (
        _tests_unit_check_extended_config_fixer_errors_tests
    )
    import tests.unit.check.extended_config_fixer_tests as _tests_unit_check_extended_config_fixer_tests

    extended_config_fixer_tests = _tests_unit_check_extended_config_fixer_tests
    import tests.unit.check.extended_error_reporting_tests as _tests_unit_check_extended_error_reporting_tests

    extended_error_reporting_tests = _tests_unit_check_extended_error_reporting_tests
    import tests.unit.check.extended_gate_bandit_markdown_tests as _tests_unit_check_extended_gate_bandit_markdown_tests

    extended_gate_bandit_markdown_tests = (
        _tests_unit_check_extended_gate_bandit_markdown_tests
    )
    import tests.unit.check.extended_gate_go_cmd_tests as _tests_unit_check_extended_gate_go_cmd_tests

    extended_gate_go_cmd_tests = _tests_unit_check_extended_gate_go_cmd_tests
    import tests.unit.check.extended_gate_mypy_pyright_tests as _tests_unit_check_extended_gate_mypy_pyright_tests

    extended_gate_mypy_pyright_tests = (
        _tests_unit_check_extended_gate_mypy_pyright_tests
    )
    import tests.unit.check.extended_models_tests as _tests_unit_check_extended_models_tests

    extended_models_tests = _tests_unit_check_extended_models_tests
    import tests.unit.check.extended_project_runners_tests as _tests_unit_check_extended_project_runners_tests

    extended_project_runners_tests = _tests_unit_check_extended_project_runners_tests
    import tests.unit.check.extended_projects_tests as _tests_unit_check_extended_projects_tests

    extended_projects_tests = _tests_unit_check_extended_projects_tests
    import tests.unit.check.extended_resolve_gates_tests as _tests_unit_check_extended_resolve_gates_tests

    extended_resolve_gates_tests = _tests_unit_check_extended_resolve_gates_tests
    import tests.unit.check.extended_run_projects_tests as _tests_unit_check_extended_run_projects_tests

    extended_run_projects_tests = _tests_unit_check_extended_run_projects_tests
    import tests.unit.check.extended_runners_extra_tests as _tests_unit_check_extended_runners_extra_tests

    extended_runners_extra_tests = _tests_unit_check_extended_runners_extra_tests
    import tests.unit.check.extended_runners_go_tests as _tests_unit_check_extended_runners_go_tests

    extended_runners_go_tests = _tests_unit_check_extended_runners_go_tests
    import tests.unit.check.extended_runners_ruff_tests as _tests_unit_check_extended_runners_ruff_tests

    extended_runners_ruff_tests = _tests_unit_check_extended_runners_ruff_tests
    import tests.unit.check.extended_runners_tests as _tests_unit_check_extended_runners_tests

    extended_runners_tests = _tests_unit_check_extended_runners_tests
    import tests.unit.check.extended_workspace_init_tests as _tests_unit_check_extended_workspace_init_tests

    extended_workspace_init_tests = _tests_unit_check_extended_workspace_init_tests
    import tests.unit.check.fix_pyrefly_config_tests as _tests_unit_check_fix_pyrefly_config_tests

    fix_pyrefly_config_tests = _tests_unit_check_fix_pyrefly_config_tests
    import tests.unit.check.init_tests as _tests_unit_check_init_tests

    init_tests = _tests_unit_check_init_tests
    import tests.unit.check.main_tests as _tests_unit_check_main_tests

    main_tests = _tests_unit_check_main_tests
    import tests.unit.check.pyrefly_tests as _tests_unit_check_pyrefly_tests

    pyrefly_tests = _tests_unit_check_pyrefly_tests
    import tests.unit.check.workspace_check_tests as _tests_unit_check_workspace_check_tests

    workspace_check_tests = _tests_unit_check_workspace_check_tests
    import tests.unit.check.workspace_tests as _tests_unit_check_workspace_tests

    workspace_tests = _tests_unit_check_workspace_tests
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
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

__all__ = [
    "c",
    "cli_tests",
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
    "m",
    "main_tests",
    "p",
    "pyrefly_tests",
    "r",
    "s",
    "t",
    "u",
    "workspace_check_tests",
    "workspace_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
