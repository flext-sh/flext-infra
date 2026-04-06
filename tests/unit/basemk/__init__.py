# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.basemk.test_engine as _tests_unit_basemk_test_engine

    test_engine = _tests_unit_basemk_test_engine
    import tests.unit.basemk.test_generator as _tests_unit_basemk_test_generator
    from tests.unit.basemk.test_engine import (
        basemk_main,
        test_basemk_cli_generate_to_file,
        test_basemk_cli_generate_to_stdout,
        test_basemk_engine_execute_calls_render_all,
        test_basemk_engine_render_all_handles_template_error,
        test_basemk_engine_render_all_returns_string,
        test_basemk_engine_render_all_with_valid_config,
        test_generator_fails_for_invalid_make_syntax,
        test_generator_renders_with_config_override,
        test_generator_write_saves_output_file,
        test_render_all_declares_and_documents_runtime_options,
        test_render_all_exposes_canonical_public_targets,
        test_render_all_generates_large_makefile,
        test_render_all_has_no_scripts_path_references,
    )

    test_generator = _tests_unit_basemk_test_generator
    import tests.unit.basemk.test_generator_edge_cases as _tests_unit_basemk_test_generator_edge_cases
    from tests.unit.basemk.test_generator import (
        test_generator_execute_returns_generated_content,
        test_generator_generate_propagates_render_failure,
        test_generator_generate_with_basemk_config_object,
        test_generator_generate_with_dict_config,
        test_generator_generate_with_invalid_dict_config,
        test_generator_generate_with_none_config_uses_default,
        test_generator_initializes_with_custom_engine,
        test_generator_initializes_with_default_engine,
        test_generator_write_creates_parent_directories,
        test_generator_write_fails_without_output_or_stream,
        test_generator_write_to_file,
        test_generator_write_to_stream,
    )

    test_generator_edge_cases = _tests_unit_basemk_test_generator_edge_cases
    import tests.unit.basemk.test_init as _tests_unit_basemk_test_init
    from tests.unit.basemk.test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror,
    )

    test_init = _tests_unit_basemk_test_init
    import tests.unit.basemk.test_main as _tests_unit_basemk_test_main
    from tests.unit.basemk.test_init import TestFlextInfraBaseMk

    test_main = _tests_unit_basemk_test_main
    import tests.unit.basemk.test_make_contract as _tests_unit_basemk_test_make_contract
    from tests.unit.basemk.test_main import (
        main,
        test_basemk_build_config_with_none,
        test_basemk_build_config_with_project_name,
        test_basemk_main_ensures_structlog_configured,
        test_basemk_main_output_to_stdout,
        test_basemk_main_rejects_apply_flag,
        test_basemk_main_with_generate_command,
        test_basemk_main_with_generation_failure,
        test_basemk_main_with_help,
        test_basemk_main_with_invalid_command,
        test_basemk_main_with_no_command,
        test_basemk_main_with_none_argv,
        test_basemk_main_with_output_file,
        test_basemk_main_with_project_name,
        test_basemk_main_with_write_failure,
    )

    test_make_contract = _tests_unit_basemk_test_make_contract
    from tests.unit.basemk.test_make_contract import (
        test_make_boot_works_without_existing_venv_in_workspace_mode,
        test_make_check_fast_path_check_only_suppresses_fix_writes,
        test_make_check_file_scope_rejects_unsupported_gates,
        test_make_check_file_scope_runs_mypy,
        test_make_check_file_scope_unsets_python_path_env,
        test_make_check_full_run_forwards_fix_and_tool_args,
        test_make_check_full_run_unsets_python_path_env,
        test_make_help_lists_supported_options,
        test_rendered_base_mk_declares_cli_group_roots,
        test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight,
        test_rendered_base_mk_sanitizes_workspace_sync_env,
    )

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
    "TestFlextInfraBaseMk": ("tests.unit.basemk.test_init", "TestFlextInfraBaseMk"),
    "basemk_main": ("tests.unit.basemk.test_engine", "basemk_main"),
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main": ("tests.unit.basemk.test_main", "main"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_basemk_build_config_with_none": (
        "tests.unit.basemk.test_main",
        "test_basemk_build_config_with_none",
    ),
    "test_basemk_build_config_with_project_name": (
        "tests.unit.basemk.test_main",
        "test_basemk_build_config_with_project_name",
    ),
    "test_basemk_cli_generate_to_file": (
        "tests.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_file",
    ),
    "test_basemk_cli_generate_to_stdout": (
        "tests.unit.basemk.test_engine",
        "test_basemk_cli_generate_to_stdout",
    ),
    "test_basemk_engine_execute_calls_render_all": (
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_execute_calls_render_all",
    ),
    "test_basemk_engine_render_all_handles_template_error": (
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_handles_template_error",
    ),
    "test_basemk_engine_render_all_returns_string": (
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_returns_string",
    ),
    "test_basemk_engine_render_all_with_valid_config": (
        "tests.unit.basemk.test_engine",
        "test_basemk_engine_render_all_with_valid_config",
    ),
    "test_basemk_main_ensures_structlog_configured": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_ensures_structlog_configured",
    ),
    "test_basemk_main_output_to_stdout": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_output_to_stdout",
    ),
    "test_basemk_main_rejects_apply_flag": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_rejects_apply_flag",
    ),
    "test_basemk_main_with_generate_command": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_generate_command",
    ),
    "test_basemk_main_with_generation_failure": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_generation_failure",
    ),
    "test_basemk_main_with_help": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_help",
    ),
    "test_basemk_main_with_invalid_command": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_invalid_command",
    ),
    "test_basemk_main_with_no_command": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_no_command",
    ),
    "test_basemk_main_with_none_argv": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_none_argv",
    ),
    "test_basemk_main_with_output_file": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_output_file",
    ),
    "test_basemk_main_with_project_name": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_project_name",
    ),
    "test_basemk_main_with_write_failure": (
        "tests.unit.basemk.test_main",
        "test_basemk_main_with_write_failure",
    ),
    "test_engine": "tests.unit.basemk.test_engine",
    "test_generator": "tests.unit.basemk.test_generator",
    "test_generator_edge_cases": "tests.unit.basemk.test_generator_edge_cases",
    "test_generator_execute_returns_generated_content": (
        "tests.unit.basemk.test_generator",
        "test_generator_execute_returns_generated_content",
    ),
    "test_generator_fails_for_invalid_make_syntax": (
        "tests.unit.basemk.test_engine",
        "test_generator_fails_for_invalid_make_syntax",
    ),
    "test_generator_generate_propagates_render_failure": (
        "tests.unit.basemk.test_generator",
        "test_generator_generate_propagates_render_failure",
    ),
    "test_generator_generate_with_basemk_config_object": (
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_basemk_config_object",
    ),
    "test_generator_generate_with_dict_config": (
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_dict_config",
    ),
    "test_generator_generate_with_invalid_dict_config": (
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_invalid_dict_config",
    ),
    "test_generator_generate_with_none_config_uses_default": (
        "tests.unit.basemk.test_generator",
        "test_generator_generate_with_none_config_uses_default",
    ),
    "test_generator_initializes_with_custom_engine": (
        "tests.unit.basemk.test_generator",
        "test_generator_initializes_with_custom_engine",
    ),
    "test_generator_initializes_with_default_engine": (
        "tests.unit.basemk.test_generator",
        "test_generator_initializes_with_default_engine",
    ),
    "test_generator_normalize_config_with_basemk_config": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_basemk_config",
    ),
    "test_generator_normalize_config_with_dict": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_dict",
    ),
    "test_generator_normalize_config_with_invalid_dict": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_invalid_dict",
    ),
    "test_generator_normalize_config_with_none": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_normalize_config_with_none",
    ),
    "test_generator_renders_with_config_override": (
        "tests.unit.basemk.test_engine",
        "test_generator_renders_with_config_override",
    ),
    "test_generator_validate_generated_output_handles_oserror": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_validate_generated_output_handles_oserror",
    ),
    "test_generator_write_creates_parent_directories": (
        "tests.unit.basemk.test_generator",
        "test_generator_write_creates_parent_directories",
    ),
    "test_generator_write_fails_without_output_or_stream": (
        "tests.unit.basemk.test_generator",
        "test_generator_write_fails_without_output_or_stream",
    ),
    "test_generator_write_handles_file_permission_error": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_write_handles_file_permission_error",
    ),
    "test_generator_write_saves_output_file": (
        "tests.unit.basemk.test_engine",
        "test_generator_write_saves_output_file",
    ),
    "test_generator_write_to_file": (
        "tests.unit.basemk.test_generator",
        "test_generator_write_to_file",
    ),
    "test_generator_write_to_stream": (
        "tests.unit.basemk.test_generator",
        "test_generator_write_to_stream",
    ),
    "test_generator_write_to_stream_handles_oserror": (
        "tests.unit.basemk.test_generator_edge_cases",
        "test_generator_write_to_stream_handles_oserror",
    ),
    "test_init": "tests.unit.basemk.test_init",
    "test_main": "tests.unit.basemk.test_main",
    "test_make_boot_works_without_existing_venv_in_workspace_mode": (
        "tests.unit.basemk.test_make_contract",
        "test_make_boot_works_without_existing_venv_in_workspace_mode",
    ),
    "test_make_check_fast_path_check_only_suppresses_fix_writes": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_fast_path_check_only_suppresses_fix_writes",
    ),
    "test_make_check_file_scope_rejects_unsupported_gates": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_rejects_unsupported_gates",
    ),
    "test_make_check_file_scope_runs_mypy": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_runs_mypy",
    ),
    "test_make_check_file_scope_unsets_python_path_env": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_file_scope_unsets_python_path_env",
    ),
    "test_make_check_full_run_forwards_fix_and_tool_args": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_full_run_forwards_fix_and_tool_args",
    ),
    "test_make_check_full_run_unsets_python_path_env": (
        "tests.unit.basemk.test_make_contract",
        "test_make_check_full_run_unsets_python_path_env",
    ),
    "test_make_contract": "tests.unit.basemk.test_make_contract",
    "test_make_help_lists_supported_options": (
        "tests.unit.basemk.test_make_contract",
        "test_make_help_lists_supported_options",
    ),
    "test_render_all_declares_and_documents_runtime_options": (
        "tests.unit.basemk.test_engine",
        "test_render_all_declares_and_documents_runtime_options",
    ),
    "test_render_all_exposes_canonical_public_targets": (
        "tests.unit.basemk.test_engine",
        "test_render_all_exposes_canonical_public_targets",
    ),
    "test_render_all_generates_large_makefile": (
        "tests.unit.basemk.test_engine",
        "test_render_all_generates_large_makefile",
    ),
    "test_render_all_has_no_scripts_path_references": (
        "tests.unit.basemk.test_engine",
        "test_render_all_has_no_scripts_path_references",
    ),
    "test_rendered_base_mk_declares_cli_group_roots": (
        "tests.unit.basemk.test_make_contract",
        "test_rendered_base_mk_declares_cli_group_roots",
    ),
    "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight": (
        "tests.unit.basemk.test_make_contract",
        "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight",
    ),
    "test_rendered_base_mk_sanitizes_workspace_sync_env": (
        "tests.unit.basemk.test_make_contract",
        "test_rendered_base_mk_sanitizes_workspace_sync_env",
    ),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "TestFlextInfraBaseMk",
    "basemk_main",
    "c",
    "d",
    "e",
    "h",
    "m",
    "main",
    "p",
    "r",
    "s",
    "t",
    "test_basemk_build_config_with_none",
    "test_basemk_build_config_with_project_name",
    "test_basemk_cli_generate_to_file",
    "test_basemk_cli_generate_to_stdout",
    "test_basemk_engine_execute_calls_render_all",
    "test_basemk_engine_render_all_handles_template_error",
    "test_basemk_engine_render_all_returns_string",
    "test_basemk_engine_render_all_with_valid_config",
    "test_basemk_main_ensures_structlog_configured",
    "test_basemk_main_output_to_stdout",
    "test_basemk_main_rejects_apply_flag",
    "test_basemk_main_with_generate_command",
    "test_basemk_main_with_generation_failure",
    "test_basemk_main_with_help",
    "test_basemk_main_with_invalid_command",
    "test_basemk_main_with_no_command",
    "test_basemk_main_with_none_argv",
    "test_basemk_main_with_output_file",
    "test_basemk_main_with_project_name",
    "test_basemk_main_with_write_failure",
    "test_engine",
    "test_generator",
    "test_generator_edge_cases",
    "test_generator_execute_returns_generated_content",
    "test_generator_fails_for_invalid_make_syntax",
    "test_generator_generate_propagates_render_failure",
    "test_generator_generate_with_basemk_config_object",
    "test_generator_generate_with_dict_config",
    "test_generator_generate_with_invalid_dict_config",
    "test_generator_generate_with_none_config_uses_default",
    "test_generator_initializes_with_custom_engine",
    "test_generator_initializes_with_default_engine",
    "test_generator_normalize_config_with_basemk_config",
    "test_generator_normalize_config_with_dict",
    "test_generator_normalize_config_with_invalid_dict",
    "test_generator_normalize_config_with_none",
    "test_generator_renders_with_config_override",
    "test_generator_validate_generated_output_handles_oserror",
    "test_generator_write_creates_parent_directories",
    "test_generator_write_fails_without_output_or_stream",
    "test_generator_write_handles_file_permission_error",
    "test_generator_write_saves_output_file",
    "test_generator_write_to_file",
    "test_generator_write_to_stream",
    "test_generator_write_to_stream_handles_oserror",
    "test_init",
    "test_main",
    "test_make_boot_works_without_existing_venv_in_workspace_mode",
    "test_make_check_fast_path_check_only_suppresses_fix_writes",
    "test_make_check_file_scope_rejects_unsupported_gates",
    "test_make_check_file_scope_runs_mypy",
    "test_make_check_file_scope_unsets_python_path_env",
    "test_make_check_full_run_forwards_fix_and_tool_args",
    "test_make_check_full_run_unsets_python_path_env",
    "test_make_contract",
    "test_make_help_lists_supported_options",
    "test_render_all_declares_and_documents_runtime_options",
    "test_render_all_exposes_canonical_public_targets",
    "test_render_all_generates_large_makefile",
    "test_render_all_has_no_scripts_path_references",
    "test_rendered_base_mk_declares_cli_group_roots",
    "test_rendered_base_mk_forwards_canonical_root_in_workspace_preflight",
    "test_rendered_base_mk_sanitizes_workspace_sync_env",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
