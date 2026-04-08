# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.check._shared_fixtures as _tests_unit_check__shared_fixtures

    _shared_fixtures = _tests_unit_check__shared_fixtures
    import tests.unit.check._stubs as _tests_unit_check__stubs
    from tests.unit.check._shared_fixtures import (
        RunProjectsMock,
        create_check_project_iter_stub,
        create_check_project_stub,
        create_checker_project,
        create_fake_run_projects,
        create_fake_run_raw,
        create_gate_context,
        create_gate_execution,
        patch_gate_run,
        patch_gate_run_sequence,
        patch_python_dir_detection,
        run_gate_check,
    )

    _stubs = _tests_unit_check__stubs
    import tests.unit.check.cli_tests as _tests_unit_check_cli_tests
    from tests.unit.check._stubs import Spy, make_issue, make_project

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
    from tests.unit.check.extended_gate_go_cmd_tests import run_command_failure_check

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
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "RunProjectsMock": ("tests.unit.check._shared_fixtures", "RunProjectsMock"),
    "Spy": ("tests.unit.check._stubs", "Spy"),
    "_shared_fixtures": "tests.unit.check._shared_fixtures",
    "_stubs": "tests.unit.check._stubs",
    "cli_tests": "tests.unit.check.cli_tests",
    "create_check_project_iter_stub": (
        "tests.unit.check._shared_fixtures",
        "create_check_project_iter_stub",
    ),
    "create_check_project_stub": (
        "tests.unit.check._shared_fixtures",
        "create_check_project_stub",
    ),
    "create_checker_project": (
        "tests.unit.check._shared_fixtures",
        "create_checker_project",
    ),
    "create_fake_run_projects": (
        "tests.unit.check._shared_fixtures",
        "create_fake_run_projects",
    ),
    "create_fake_run_raw": ("tests.unit.check._shared_fixtures", "create_fake_run_raw"),
    "create_gate_context": ("tests.unit.check._shared_fixtures", "create_gate_context"),
    "create_gate_execution": (
        "tests.unit.check._shared_fixtures",
        "create_gate_execution",
    ),
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
    "main_tests": "tests.unit.check.main_tests",
    "make_issue": ("tests.unit.check._stubs", "make_issue"),
    "make_project": ("tests.unit.check._stubs", "make_project"),
    "patch_gate_run": ("tests.unit.check._shared_fixtures", "patch_gate_run"),
    "patch_gate_run_sequence": (
        "tests.unit.check._shared_fixtures",
        "patch_gate_run_sequence",
    ),
    "patch_python_dir_detection": (
        "tests.unit.check._shared_fixtures",
        "patch_python_dir_detection",
    ),
    "pyrefly_tests": "tests.unit.check.pyrefly_tests",
    "r": ("flext_core.result", "FlextResult"),
    "run_command_failure_check": (
        "tests.unit.check.extended_gate_go_cmd_tests",
        "run_command_failure_check",
    ),
    "run_gate_check": ("tests.unit.check._shared_fixtures", "run_gate_check"),
    "s": ("flext_core.service", "FlextService"),
    "workspace_check_tests": "tests.unit.check.workspace_check_tests",
    "workspace_tests": "tests.unit.check.workspace_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "RunProjectsMock",
    "Spy",
    "_shared_fixtures",
    "_stubs",
    "cli_tests",
    "create_check_project_iter_stub",
    "create_check_project_stub",
    "create_checker_project",
    "create_fake_run_projects",
    "create_fake_run_raw",
    "create_gate_context",
    "create_gate_execution",
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
    "main_tests",
    "make_issue",
    "make_project",
    "patch_gate_run",
    "patch_gate_run_sequence",
    "patch_python_dir_detection",
    "pyrefly_tests",
    "r",
    "run_command_failure_check",
    "run_gate_check",
    "s",
    "workspace_check_tests",
    "workspace_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
