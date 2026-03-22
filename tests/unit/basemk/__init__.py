# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .test_engine import (
        test_basemk_cli_generate_to_file,
        test_basemk_cli_generate_to_stdout,
        test_basemk_engine_execute_calls_render_all,
        test_basemk_engine_render_all_handles_template_error,
        test_basemk_engine_render_all_returns_string,
        test_basemk_engine_render_all_with_valid_config,
        test_generator_fails_for_invalid_make_syntax,
        test_generator_renders_with_config_override,
        test_generator_write_saves_output_file,
        test_render_all_generates_large_makefile,
        test_render_all_has_no_scripts_path_references,
    )
    from .test_generator import (
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
    from .test_generator_edge_cases import (
        test_generator_normalize_config_with_basemk_config,
        test_generator_normalize_config_with_dict,
        test_generator_normalize_config_with_invalid_dict,
        test_generator_normalize_config_with_none,
        test_generator_validate_generated_output_handles_oserror,
        test_generator_write_handles_file_permission_error,
        test_generator_write_to_stream_handles_oserror,
    )
    from .test_init import TestFlextInfraBaseMk
    from .test_main import (
        test_basemk_build_config_with_none,
        test_basemk_build_config_with_project_name,
        test_basemk_main_ensures_structlog_configured,
        test_basemk_main_output_to_stdout,
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

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestFlextInfraBaseMk": ("tests.unit.basemk.test_init", "TestFlextInfraBaseMk"),
    "test_basemk_build_config_with_none": ("tests.unit.basemk.test_main", "test_basemk_build_config_with_none"),
    "test_basemk_build_config_with_project_name": ("tests.unit.basemk.test_main", "test_basemk_build_config_with_project_name"),
    "test_basemk_cli_generate_to_file": ("tests.unit.basemk.test_engine", "test_basemk_cli_generate_to_file"),
    "test_basemk_cli_generate_to_stdout": ("tests.unit.basemk.test_engine", "test_basemk_cli_generate_to_stdout"),
    "test_basemk_engine_execute_calls_render_all": ("tests.unit.basemk.test_engine", "test_basemk_engine_execute_calls_render_all"),
    "test_basemk_engine_render_all_handles_template_error": ("tests.unit.basemk.test_engine", "test_basemk_engine_render_all_handles_template_error"),
    "test_basemk_engine_render_all_returns_string": ("tests.unit.basemk.test_engine", "test_basemk_engine_render_all_returns_string"),
    "test_basemk_engine_render_all_with_valid_config": ("tests.unit.basemk.test_engine", "test_basemk_engine_render_all_with_valid_config"),
    "test_basemk_main_ensures_structlog_configured": ("tests.unit.basemk.test_main", "test_basemk_main_ensures_structlog_configured"),
    "test_basemk_main_output_to_stdout": ("tests.unit.basemk.test_main", "test_basemk_main_output_to_stdout"),
    "test_basemk_main_with_generate_command": ("tests.unit.basemk.test_main", "test_basemk_main_with_generate_command"),
    "test_basemk_main_with_generation_failure": ("tests.unit.basemk.test_main", "test_basemk_main_with_generation_failure"),
    "test_basemk_main_with_help": ("tests.unit.basemk.test_main", "test_basemk_main_with_help"),
    "test_basemk_main_with_invalid_command": ("tests.unit.basemk.test_main", "test_basemk_main_with_invalid_command"),
    "test_basemk_main_with_no_command": ("tests.unit.basemk.test_main", "test_basemk_main_with_no_command"),
    "test_basemk_main_with_none_argv": ("tests.unit.basemk.test_main", "test_basemk_main_with_none_argv"),
    "test_basemk_main_with_output_file": ("tests.unit.basemk.test_main", "test_basemk_main_with_output_file"),
    "test_basemk_main_with_project_name": ("tests.unit.basemk.test_main", "test_basemk_main_with_project_name"),
    "test_basemk_main_with_write_failure": ("tests.unit.basemk.test_main", "test_basemk_main_with_write_failure"),
    "test_generator_execute_returns_generated_content": ("tests.unit.basemk.test_generator", "test_generator_execute_returns_generated_content"),
    "test_generator_fails_for_invalid_make_syntax": ("tests.unit.basemk.test_engine", "test_generator_fails_for_invalid_make_syntax"),
    "test_generator_generate_propagates_render_failure": ("tests.unit.basemk.test_generator", "test_generator_generate_propagates_render_failure"),
    "test_generator_generate_with_basemk_config_object": ("tests.unit.basemk.test_generator", "test_generator_generate_with_basemk_config_object"),
    "test_generator_generate_with_dict_config": ("tests.unit.basemk.test_generator", "test_generator_generate_with_dict_config"),
    "test_generator_generate_with_invalid_dict_config": ("tests.unit.basemk.test_generator", "test_generator_generate_with_invalid_dict_config"),
    "test_generator_generate_with_none_config_uses_default": ("tests.unit.basemk.test_generator", "test_generator_generate_with_none_config_uses_default"),
    "test_generator_initializes_with_custom_engine": ("tests.unit.basemk.test_generator", "test_generator_initializes_with_custom_engine"),
    "test_generator_initializes_with_default_engine": ("tests.unit.basemk.test_generator", "test_generator_initializes_with_default_engine"),
    "test_generator_normalize_config_with_basemk_config": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_normalize_config_with_basemk_config"),
    "test_generator_normalize_config_with_dict": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_normalize_config_with_dict"),
    "test_generator_normalize_config_with_invalid_dict": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_normalize_config_with_invalid_dict"),
    "test_generator_normalize_config_with_none": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_normalize_config_with_none"),
    "test_generator_renders_with_config_override": ("tests.unit.basemk.test_engine", "test_generator_renders_with_config_override"),
    "test_generator_validate_generated_output_handles_oserror": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_validate_generated_output_handles_oserror"),
    "test_generator_write_creates_parent_directories": ("tests.unit.basemk.test_generator", "test_generator_write_creates_parent_directories"),
    "test_generator_write_fails_without_output_or_stream": ("tests.unit.basemk.test_generator", "test_generator_write_fails_without_output_or_stream"),
    "test_generator_write_handles_file_permission_error": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_write_handles_file_permission_error"),
    "test_generator_write_saves_output_file": ("tests.unit.basemk.test_engine", "test_generator_write_saves_output_file"),
    "test_generator_write_to_file": ("tests.unit.basemk.test_generator", "test_generator_write_to_file"),
    "test_generator_write_to_stream": ("tests.unit.basemk.test_generator", "test_generator_write_to_stream"),
    "test_generator_write_to_stream_handles_oserror": ("tests.unit.basemk.test_generator_edge_cases", "test_generator_write_to_stream_handles_oserror"),
    "test_render_all_generates_large_makefile": ("tests.unit.basemk.test_engine", "test_render_all_generates_large_makefile"),
    "test_render_all_has_no_scripts_path_references": ("tests.unit.basemk.test_engine", "test_render_all_has_no_scripts_path_references"),
}

__all__ = [
    "TestFlextInfraBaseMk",
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
    "test_basemk_main_with_generate_command",
    "test_basemk_main_with_generation_failure",
    "test_basemk_main_with_help",
    "test_basemk_main_with_invalid_command",
    "test_basemk_main_with_no_command",
    "test_basemk_main_with_none_argv",
    "test_basemk_main_with_output_file",
    "test_basemk_main_with_project_name",
    "test_basemk_main_with_write_failure",
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
    "test_render_all_generates_large_makefile",
    "test_render_all_has_no_scripts_path_references",
]


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
