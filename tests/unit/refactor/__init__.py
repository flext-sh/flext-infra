# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files,
    )
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
        test_class_reconstructor_reorders_each_contiguous_method_block,
        test_class_reconstructor_reorders_methods_by_config,
        test_class_reconstructor_skips_interleaved_non_method_members,
        test_mro_checker_keeps_external_attribute_base,
        test_mro_redundancy_checker_removes_nested_attribute_inheritance,
        test_signature_propagation_removes_and_adds_keywords,
        test_signature_propagation_renames_call_keyword,
        test_symbol_propagation_keeps_alias_reference_when_asname_used,
        test_symbol_propagation_renames_import_and_local_references,
        test_symbol_propagation_updates_mro_base_references,
    )
    from tests.unit.refactor.test_infra_refactor_class_placement import (
        test_detects_attribute_base_class,
        test_detects_basemodel_in_non_model_file,
        test_detects_multiple_models,
        test_non_pydantic_class_not_flagged,
        test_skips_models_directory,
        test_skips_models_file,
        test_skips_private_class,
        test_skips_protected_files,
        test_skips_settings_file,
    )
    from tests.unit.refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata,
    )
    from tests.unit.refactor.test_infra_refactor_import_modernizer import (
        test_import_modernizer_adds_c_when_existing_c_is_aliased,
        test_import_modernizer_does_not_rewrite_function_parameter_shadow,
        test_import_modernizer_does_not_rewrite_rebound_local_name_usage,
        test_import_modernizer_partial_import_keeps_unmapped_symbols,
        test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias,
        test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function,
        test_import_modernizer_skips_when_runtime_alias_name_is_blocked,
        test_import_modernizer_updates_aliased_symbol_usage,
        test_lazy_import_rule_hoists_import_to_module_level,
        test_lazy_import_rule_uses_fix_action_for_hoist,
    )
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
        test_ensure_future_annotations_after_docstring,
        test_ensure_future_annotations_moves_existing_import_to_top,
        test_legacy_import_bypass_collapses_to_primary_import,
        test_legacy_rule_uses_fix_action_remove_for_aliases,
        test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias,
        test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias,
        test_legacy_wrapper_function_is_inlined_as_alias,
        test_legacy_wrapper_non_passthrough_is_not_inlined,
    )
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files,
        test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases,
    )
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
        test_pattern_rule_converts_dict_annotations_to_mapping,
        test_pattern_rule_keeps_dict_param_when_copy_used,
        test_pattern_rule_keeps_dict_param_when_subscript_mutated,
        test_pattern_rule_keeps_type_cast_when_not_nested_object_cast,
        test_pattern_rule_optionally_converts_return_annotations_to_mapping,
        test_pattern_rule_removes_configured_redundant_casts,
        test_pattern_rule_removes_nested_type_object_cast_chain,
        test_pattern_rule_skips_overload_signatures,
    )
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order,
    )
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub,
        test_refactor_project_integrates_safety_manager,
    )
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        test_all_three_capabilities_in_one_pass,
        test_converts_multiple_aliases,
        test_converts_typealias_to_pep695,
        test_injects_t_import_when_needed,
        test_no_duplicate_t_import_when_t_from_project_package,
        test_noop_clean_module,
        test_preserves_annotated_in_function_params,
        test_preserves_non_matching_unions,
        test_preserves_override_in_method,
        test_preserves_protocol_and_runtime_checkable,
        test_preserves_type_checking_import,
        test_preserves_typealias_import_when_class_level_usage_exists,
        test_preserves_used_imports_when_import_precedes_usage,
        test_preserves_used_typing_imports,
        test_removes_all_imports_when_none_used_import_first,
        test_removes_all_unused_typing_imports,
        test_removes_dead_typealias_import,
        test_removes_typealias_import_only_when_all_usages_converted,
        test_removes_unused_preserves_used_when_import_precedes_usage,
        test_replaces_container_union,
        test_replaces_numeric_union,
        test_replaces_primitives_union,
        test_replaces_scalar_union,
        test_skips_definition_files,
        test_skips_union_with_none,
        test_typealias_conversion_preserves_used_typing_siblings,
    )

_LAZY_IMPORTS: Mapping[str, tuple[str, str]] = {
    "EngineSafetyStub": (
        "tests.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ),
    "test_all_three_capabilities_in_one_pass": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_all_three_capabilities_in_one_pass",
    ),
    "test_build_impact_map_extracts_rename_entries": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_rename_entries",
    ),
    "test_build_impact_map_extracts_signature_entries": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_signature_entries",
    ),
    "test_class_reconstructor_reorders_each_contiguous_method_block": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_each_contiguous_method_block",
    ),
    "test_class_reconstructor_reorders_methods_by_config": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_methods_by_config",
    ),
    "test_class_reconstructor_skips_interleaved_non_method_members": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_skips_interleaved_non_method_members",
    ),
    "test_converts_multiple_aliases": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_multiple_aliases",
    ),
    "test_converts_typealias_to_pep695": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_typealias_to_pep695",
    ),
    "test_detects_attribute_base_class": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_attribute_base_class",
    ),
    "test_detects_basemodel_in_non_model_file": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_basemodel_in_non_model_file",
    ),
    "test_detects_missing_local_composition_base": (
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_detects_missing_local_composition_base",
    ),
    "test_detects_multiple_models": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_multiple_models",
    ),
    "test_engine_always_enables_class_nesting_file_rule": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_engine_always_enables_class_nesting_file_rule",
    ),
    "test_ensure_future_annotations_after_docstring": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_after_docstring",
    ),
    "test_ensure_future_annotations_moves_existing_import_to_top": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_moves_existing_import_to_top",
    ),
    "test_import_modernizer_adds_c_when_existing_c_is_aliased": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    ),
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    ),
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    ),
    "test_import_modernizer_partial_import_keeps_unmapped_symbols": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    ),
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    ),
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    ),
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    ),
    "test_import_modernizer_updates_aliased_symbol_usage": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_updates_aliased_symbol_usage",
    ),
    "test_injects_t_import_when_needed": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_injects_t_import_when_needed",
    ),
    "test_lazy_import_rule_hoists_import_to_module_level": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_hoists_import_to_module_level",
    ),
    "test_lazy_import_rule_uses_fix_action_for_hoist": (
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_uses_fix_action_for_hoist",
    ),
    "test_legacy_import_bypass_collapses_to_primary_import": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_import_bypass_collapses_to_primary_import",
    ),
    "test_legacy_rule_uses_fix_action_remove_for_aliases": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_rule_uses_fix_action_remove_for_aliases",
    ),
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_function_is_inlined_as_alias": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_function_is_inlined_as_alias",
    ),
    "test_legacy_wrapper_non_passthrough_is_not_inlined": (
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_non_passthrough_is_not_inlined",
    ),
    "test_main_analyze_violations_is_read_only": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_is_read_only",
    ),
    "test_main_analyze_violations_writes_json_report": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_writes_json_report",
    ),
    "test_mro_checker_keeps_external_attribute_base": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_checker_keeps_external_attribute_base",
    ),
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    ),
    "test_no_duplicate_t_import_when_t_from_project_package": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_no_duplicate_t_import_when_t_from_project_package",
    ),
    "test_non_pydantic_class_not_flagged": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_non_pydantic_class_not_flagged",
    ),
    "test_noop_clean_module": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_noop_clean_module",
    ),
    "test_pattern_rule_converts_dict_annotations_to_mapping": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_converts_dict_annotations_to_mapping",
    ),
    "test_pattern_rule_keeps_dict_param_when_copy_used": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_copy_used",
    ),
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    ),
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    ),
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    ),
    "test_pattern_rule_removes_configured_redundant_casts": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_configured_redundant_casts",
    ),
    "test_pattern_rule_removes_nested_type_object_cast_chain": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_nested_type_object_cast_chain",
    ),
    "test_pattern_rule_skips_overload_signatures": (
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_skips_overload_signatures",
    ),
    "test_preserves_annotated_in_function_params": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_annotated_in_function_params",
    ),
    "test_preserves_non_matching_unions": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_non_matching_unions",
    ),
    "test_preserves_override_in_method": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_override_in_method",
    ),
    "test_preserves_protocol_and_runtime_checkable": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_protocol_and_runtime_checkable",
    ),
    "test_preserves_type_checking_import": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_type_checking_import",
    ),
    "test_preserves_typealias_import_when_class_level_usage_exists": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_typealias_import_when_class_level_usage_exists",
    ),
    "test_preserves_used_imports_when_import_precedes_usage": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_imports_when_import_precedes_usage",
    ),
    "test_preserves_used_typing_imports": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_typing_imports",
    ),
    "test_read_project_metadata_preserves_pep621_dependency_order": (
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_pep621_dependency_order",
    ),
    "test_read_project_metadata_preserves_poetry_dependency_order": (
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_poetry_dependency_order",
    ),
    "test_refactor_files_skips_non_python_inputs": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_files_skips_non_python_inputs",
    ),
    "test_refactor_project_integrates_safety_manager": (
        "tests.unit.refactor.test_infra_refactor_safety",
        "test_refactor_project_integrates_safety_manager",
    ),
    "test_refactor_project_scans_tests_and_scripts_dirs": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_project_scans_tests_and_scripts_dirs",
    ),
    "test_removes_all_imports_when_none_used_import_first": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_imports_when_none_used_import_first",
    ),
    "test_removes_all_unused_typing_imports": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_unused_typing_imports",
    ),
    "test_removes_dead_typealias_import": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_dead_typealias_import",
    ),
    "test_removes_typealias_import_only_when_all_usages_converted": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_typealias_import_only_when_all_usages_converted",
    ),
    "test_removes_unused_preserves_used_when_import_precedes_usage": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_unused_preserves_used_when_import_precedes_usage",
    ),
    "test_replaces_container_union": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_container_union",
    ),
    "test_replaces_numeric_union": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_numeric_union",
    ),
    "test_replaces_primitives_union": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_primitives_union",
    ),
    "test_replaces_scalar_union": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_scalar_union",
    ),
    "test_rewriter_adds_missing_base_and_formats": (
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_rewriter_adds_missing_base_and_formats",
    ),
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    ),
    "test_rule_dispatch_fails_on_unknown_rule_mapping": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_unknown_rule_mapping",
    ),
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    ),
    "test_rule_dispatch_prefers_fix_action_metadata": (
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_prefers_fix_action_metadata",
    ),
    "test_signature_propagation_removes_and_adds_keywords": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_removes_and_adds_keywords",
    ),
    "test_signature_propagation_renames_call_keyword": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_renames_call_keyword",
    ),
    "test_skips_definition_files": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_definition_files",
    ),
    "test_skips_models_directory": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_directory",
    ),
    "test_skips_models_file": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_file",
    ),
    "test_skips_non_facade_files": (
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_non_facade_files",
    ),
    "test_skips_private_candidate_classes": (
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_private_candidate_classes",
    ),
    "test_skips_private_class": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_private_class",
    ),
    "test_skips_protected_files": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_protected_files",
    ),
    "test_skips_settings_file": (
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_settings_file",
    ),
    "test_skips_union_with_none": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_union_with_none",
    ),
    "test_skips_when_candidate_is_already_in_facade_bases": (
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_when_candidate_is_already_in_facade_bases",
    ),
    "test_symbol_propagation_keeps_alias_reference_when_asname_used": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    ),
    "test_symbol_propagation_renames_import_and_local_references": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_renames_import_and_local_references",
    ),
    "test_symbol_propagation_updates_mro_base_references": (
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_updates_mro_base_references",
    ),
    "test_typealias_conversion_preserves_used_typing_siblings": (
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_typealias_conversion_preserves_used_typing_siblings",
    ),
    "test_violation_analysis_counts_massive_patterns": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analysis_counts_massive_patterns",
    ),
    "test_violation_analyzer_skips_non_utf8_files": (
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analyzer_skips_non_utf8_files",
    ),
}

__all__ = [
    "EngineSafetyStub",
    "test_all_three_capabilities_in_one_pass",
    "test_build_impact_map_extracts_rename_entries",
    "test_build_impact_map_extracts_signature_entries",
    "test_class_reconstructor_reorders_each_contiguous_method_block",
    "test_class_reconstructor_reorders_methods_by_config",
    "test_class_reconstructor_skips_interleaved_non_method_members",
    "test_converts_multiple_aliases",
    "test_converts_typealias_to_pep695",
    "test_detects_attribute_base_class",
    "test_detects_basemodel_in_non_model_file",
    "test_detects_missing_local_composition_base",
    "test_detects_multiple_models",
    "test_engine_always_enables_class_nesting_file_rule",
    "test_ensure_future_annotations_after_docstring",
    "test_ensure_future_annotations_moves_existing_import_to_top",
    "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    "test_import_modernizer_updates_aliased_symbol_usage",
    "test_injects_t_import_when_needed",
    "test_lazy_import_rule_hoists_import_to_module_level",
    "test_lazy_import_rule_uses_fix_action_for_hoist",
    "test_legacy_import_bypass_collapses_to_primary_import",
    "test_legacy_rule_uses_fix_action_remove_for_aliases",
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    "test_legacy_wrapper_function_is_inlined_as_alias",
    "test_legacy_wrapper_non_passthrough_is_not_inlined",
    "test_main_analyze_violations_is_read_only",
    "test_main_analyze_violations_writes_json_report",
    "test_mro_checker_keeps_external_attribute_base",
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    "test_no_duplicate_t_import_when_t_from_project_package",
    "test_non_pydantic_class_not_flagged",
    "test_noop_clean_module",
    "test_pattern_rule_converts_dict_annotations_to_mapping",
    "test_pattern_rule_keeps_dict_param_when_copy_used",
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    "test_pattern_rule_removes_configured_redundant_casts",
    "test_pattern_rule_removes_nested_type_object_cast_chain",
    "test_pattern_rule_skips_overload_signatures",
    "test_preserves_annotated_in_function_params",
    "test_preserves_non_matching_unions",
    "test_preserves_override_in_method",
    "test_preserves_protocol_and_runtime_checkable",
    "test_preserves_type_checking_import",
    "test_preserves_typealias_import_when_class_level_usage_exists",
    "test_preserves_used_imports_when_import_precedes_usage",
    "test_preserves_used_typing_imports",
    "test_read_project_metadata_preserves_pep621_dependency_order",
    "test_read_project_metadata_preserves_poetry_dependency_order",
    "test_refactor_files_skips_non_python_inputs",
    "test_refactor_project_integrates_safety_manager",
    "test_refactor_project_scans_tests_and_scripts_dirs",
    "test_removes_all_imports_when_none_used_import_first",
    "test_removes_all_unused_typing_imports",
    "test_removes_dead_typealias_import",
    "test_removes_typealias_import_only_when_all_usages_converted",
    "test_removes_unused_preserves_used_when_import_precedes_usage",
    "test_replaces_container_union",
    "test_replaces_numeric_union",
    "test_replaces_primitives_union",
    "test_replaces_scalar_union",
    "test_rewriter_adds_missing_base_and_formats",
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    "test_rule_dispatch_fails_on_unknown_rule_mapping",
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    "test_rule_dispatch_prefers_fix_action_metadata",
    "test_signature_propagation_removes_and_adds_keywords",
    "test_signature_propagation_renames_call_keyword",
    "test_skips_definition_files",
    "test_skips_models_directory",
    "test_skips_models_file",
    "test_skips_non_facade_files",
    "test_skips_private_candidate_classes",
    "test_skips_private_class",
    "test_skips_protected_files",
    "test_skips_settings_file",
    "test_skips_union_with_none",
    "test_skips_when_candidate_is_already_in_facade_bases",
    "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    "test_symbol_propagation_renames_import_and_local_references",
    "test_symbol_propagation_updates_mro_base_references",
    "test_typealias_conversion_preserves_used_typing_siblings",
    "test_violation_analysis_counts_massive_patterns",
    "test_violation_analyzer_skips_non_utf8_files",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


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


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
