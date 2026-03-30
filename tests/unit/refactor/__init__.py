# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.refactor import (
        test_infra_refactor_analysis as test_infra_refactor_analysis,
        test_infra_refactor_class_and_propagation as test_infra_refactor_class_and_propagation,
        test_infra_refactor_class_placement as test_infra_refactor_class_placement,
        test_infra_refactor_engine as test_infra_refactor_engine,
        test_infra_refactor_import_modernizer as test_infra_refactor_import_modernizer,
        test_infra_refactor_legacy_and_annotations as test_infra_refactor_legacy_and_annotations,
        test_infra_refactor_mro_completeness as test_infra_refactor_mro_completeness,
        test_infra_refactor_mro_import_rewriter as test_infra_refactor_mro_import_rewriter,
        test_infra_refactor_namespace_aliases as test_infra_refactor_namespace_aliases,
        test_infra_refactor_namespace_source as test_infra_refactor_namespace_source,
        test_infra_refactor_pattern_corrections as test_infra_refactor_pattern_corrections,
        test_infra_refactor_project_classifier as test_infra_refactor_project_classifier,
        test_infra_refactor_safety as test_infra_refactor_safety,
        test_infra_refactor_typing_unifier as test_infra_refactor_typing_unifier,
        test_main_cli as test_main_cli,
    )
    from tests.unit.refactor.test_infra_refactor_analysis import (
        test_build_impact_map_extracts_rename_entries as test_build_impact_map_extracts_rename_entries,
        test_build_impact_map_extracts_signature_entries as test_build_impact_map_extracts_signature_entries,
        test_main_analyze_violations_is_read_only as test_main_analyze_violations_is_read_only,
        test_main_analyze_violations_writes_json_report as test_main_analyze_violations_writes_json_report,
        test_violation_analysis_counts_massive_patterns as test_violation_analysis_counts_massive_patterns,
        test_violation_analyzer_skips_non_utf8_files as test_violation_analyzer_skips_non_utf8_files,
    )
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import (
        test_class_reconstructor_reorders_each_contiguous_method_block as test_class_reconstructor_reorders_each_contiguous_method_block,
        test_class_reconstructor_reorders_methods_by_config as test_class_reconstructor_reorders_methods_by_config,
        test_class_reconstructor_skips_interleaved_non_method_members as test_class_reconstructor_skips_interleaved_non_method_members,
        test_mro_checker_keeps_external_attribute_base as test_mro_checker_keeps_external_attribute_base,
        test_mro_redundancy_checker_removes_nested_attribute_inheritance as test_mro_redundancy_checker_removes_nested_attribute_inheritance,
        test_signature_propagation_removes_and_adds_keywords as test_signature_propagation_removes_and_adds_keywords,
        test_signature_propagation_renames_call_keyword as test_signature_propagation_renames_call_keyword,
        test_symbol_propagation_keeps_alias_reference_when_asname_used as test_symbol_propagation_keeps_alias_reference_when_asname_used,
        test_symbol_propagation_renames_import_and_local_references as test_symbol_propagation_renames_import_and_local_references,
        test_symbol_propagation_updates_mro_base_references as test_symbol_propagation_updates_mro_base_references,
    )
    from tests.unit.refactor.test_infra_refactor_class_placement import (
        test_detects_attribute_base_class as test_detects_attribute_base_class,
        test_detects_basemodel_in_non_model_file as test_detects_basemodel_in_non_model_file,
        test_detects_multiple_models as test_detects_multiple_models,
        test_non_pydantic_class_not_flagged as test_non_pydantic_class_not_flagged,
        test_skips_models_directory as test_skips_models_directory,
        test_skips_models_file as test_skips_models_file,
        test_skips_private_class as test_skips_private_class,
        test_skips_protected_files as test_skips_protected_files,
        test_skips_settings_file as test_skips_settings_file,
    )
    from tests.unit.refactor.test_infra_refactor_engine import (
        test_engine_always_enables_class_nesting_file_rule as test_engine_always_enables_class_nesting_file_rule,
        test_refactor_files_skips_non_python_inputs as test_refactor_files_skips_non_python_inputs,
        test_refactor_project_scans_tests_and_scripts_dirs as test_refactor_project_scans_tests_and_scripts_dirs,
        test_rule_dispatch_fails_on_invalid_pattern_rule_config as test_rule_dispatch_fails_on_invalid_pattern_rule_config,
        test_rule_dispatch_fails_on_unknown_rule_mapping as test_rule_dispatch_fails_on_unknown_rule_mapping,
        test_rule_dispatch_keeps_legacy_id_fallback_mapping as test_rule_dispatch_keeps_legacy_id_fallback_mapping,
        test_rule_dispatch_prefers_fix_action_metadata as test_rule_dispatch_prefers_fix_action_metadata,
    )
    from tests.unit.refactor.test_infra_refactor_import_modernizer import (
        test_import_modernizer_adds_c_when_existing_c_is_aliased as test_import_modernizer_adds_c_when_existing_c_is_aliased,
        test_import_modernizer_does_not_rewrite_function_parameter_shadow as test_import_modernizer_does_not_rewrite_function_parameter_shadow,
        test_import_modernizer_does_not_rewrite_rebound_local_name_usage as test_import_modernizer_does_not_rewrite_rebound_local_name_usage,
        test_import_modernizer_partial_import_keeps_unmapped_symbols as test_import_modernizer_partial_import_keeps_unmapped_symbols,
        test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias as test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias,
        test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function as test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function,
        test_import_modernizer_skips_when_runtime_alias_name_is_blocked as test_import_modernizer_skips_when_runtime_alias_name_is_blocked,
        test_import_modernizer_updates_aliased_symbol_usage as test_import_modernizer_updates_aliased_symbol_usage,
        test_lazy_import_rule_hoists_import_to_module_level as test_lazy_import_rule_hoists_import_to_module_level,
        test_lazy_import_rule_uses_fix_action_for_hoist as test_lazy_import_rule_uses_fix_action_for_hoist,
    )
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import (
        test_ensure_future_annotations_after_docstring as test_ensure_future_annotations_after_docstring,
        test_ensure_future_annotations_moves_existing_import_to_top as test_ensure_future_annotations_moves_existing_import_to_top,
        test_legacy_import_bypass_collapses_to_primary_import as test_legacy_import_bypass_collapses_to_primary_import,
        test_legacy_rule_uses_fix_action_remove_for_aliases as test_legacy_rule_uses_fix_action_remove_for_aliases,
        test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias as test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias,
        test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias as test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias,
        test_legacy_wrapper_function_is_inlined_as_alias as test_legacy_wrapper_function_is_inlined_as_alias,
        test_legacy_wrapper_non_passthrough_is_not_inlined as test_legacy_wrapper_non_passthrough_is_not_inlined,
    )
    from tests.unit.refactor.test_infra_refactor_mro_completeness import (
        test_detects_missing_local_composition_base as test_detects_missing_local_composition_base,
        test_rewriter_adds_missing_base_and_formats as test_rewriter_adds_missing_base_and_formats,
        test_skips_non_facade_files as test_skips_non_facade_files,
        test_skips_private_candidate_classes as test_skips_private_candidate_classes,
        test_skips_when_candidate_is_already_in_facade_bases as test_skips_when_candidate_is_already_in_facade_bases,
    )
    from tests.unit.refactor.test_infra_refactor_mro_import_rewriter import (
        test_migrate_workspace_applies_consumer_rewrites as test_migrate_workspace_applies_consumer_rewrites,
        test_migrate_workspace_dry_run_preserves_files as test_migrate_workspace_dry_run_preserves_files,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import (
        rope_project as rope_project,
        test_import_alias_detector_skips_facade_and_subclass_files as test_import_alias_detector_skips_facade_and_subclass_files,
        test_import_alias_detector_skips_nested_private_and_as_renames as test_import_alias_detector_skips_nested_private_and_as_renames,
        test_import_alias_detector_skips_private_and_class_imports as test_import_alias_detector_skips_private_and_class_imports,
        test_namespace_rewriter_keeps_contextual_alias_subset as test_namespace_rewriter_keeps_contextual_alias_subset,
        test_namespace_rewriter_only_rewrites_runtime_alias_imports as test_namespace_rewriter_only_rewrites_runtime_alias_imports,
        test_namespace_rewriter_skips_facade_and_subclass_files as test_namespace_rewriter_skips_facade_and_subclass_files,
        test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates as test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates,
    )
    from tests.unit.refactor.test_infra_refactor_namespace_source import (
        FAMILY_FILE_MAP as FAMILY_FILE_MAP,
        FAMILY_SUFFIX_MAP as FAMILY_SUFFIX_MAP,
        test_detects_only_wrong_alias_in_mixed_import as test_detects_only_wrong_alias_in_mixed_import,
        test_detects_same_project_submodule_alias_import as test_detects_same_project_submodule_alias_import,
        test_detects_wrong_source_m_import as test_detects_wrong_source_m_import,
        test_detects_wrong_source_u_import as test_detects_wrong_source_u_import,
        test_project_without_alias_facade_has_no_violation as test_project_without_alias_facade_has_no_violation,
        test_rewriter_namespace_source_is_idempotent_with_ruff as test_rewriter_namespace_source_is_idempotent_with_ruff,
        test_rewriter_preserves_non_alias_symbols as test_rewriter_preserves_non_alias_symbols,
        test_rewriter_splits_mixed_imports_correctly as test_rewriter_splits_mixed_imports_correctly,
        test_skips_facade_declaration_files as test_skips_facade_declaration_files,
        test_skips_import_as_rename as test_skips_import_as_rename,
        test_skips_init_file as test_skips_init_file,
        test_skips_non_alias_symbols as test_skips_non_alias_symbols,
        test_skips_r_alias_universal_exception as test_skips_r_alias_universal_exception,
        test_skips_same_project_private_submodule as test_skips_same_project_private_submodule,
        test_skips_same_project_submodule_class_import as test_skips_same_project_submodule_class_import,
    )
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import (
        test_pattern_rule_converts_dict_annotations_to_mapping as test_pattern_rule_converts_dict_annotations_to_mapping,
        test_pattern_rule_keeps_dict_param_when_copy_used as test_pattern_rule_keeps_dict_param_when_copy_used,
        test_pattern_rule_keeps_dict_param_when_subscript_mutated as test_pattern_rule_keeps_dict_param_when_subscript_mutated,
        test_pattern_rule_keeps_type_cast_when_not_nested_object_cast as test_pattern_rule_keeps_type_cast_when_not_nested_object_cast,
        test_pattern_rule_optionally_converts_return_annotations_to_mapping as test_pattern_rule_optionally_converts_return_annotations_to_mapping,
        test_pattern_rule_removes_configured_redundant_casts as test_pattern_rule_removes_configured_redundant_casts,
        test_pattern_rule_removes_nested_type_object_cast_chain as test_pattern_rule_removes_nested_type_object_cast_chain,
        test_pattern_rule_skips_overload_signatures as test_pattern_rule_skips_overload_signatures,
    )
    from tests.unit.refactor.test_infra_refactor_project_classifier import (
        test_read_project_metadata_preserves_pep621_dependency_order as test_read_project_metadata_preserves_pep621_dependency_order,
        test_read_project_metadata_preserves_poetry_dependency_order as test_read_project_metadata_preserves_poetry_dependency_order,
    )
    from tests.unit.refactor.test_infra_refactor_safety import (
        EngineSafetyStub as EngineSafetyStub,
        test_refactor_project_integrates_safety_manager as test_refactor_project_integrates_safety_manager,
    )
    from tests.unit.refactor.test_infra_refactor_typing_unifier import (
        test_all_three_capabilities_in_one_pass as test_all_three_capabilities_in_one_pass,
        test_converts_multiple_aliases as test_converts_multiple_aliases,
        test_converts_typealias_to_pep695 as test_converts_typealias_to_pep695,
        test_injects_t_import_when_needed as test_injects_t_import_when_needed,
        test_no_duplicate_t_import_when_t_from_project_package as test_no_duplicate_t_import_when_t_from_project_package,
        test_noop_clean_module as test_noop_clean_module,
        test_preserves_annotated_in_function_params as test_preserves_annotated_in_function_params,
        test_preserves_non_matching_unions as test_preserves_non_matching_unions,
        test_preserves_override_in_method as test_preserves_override_in_method,
        test_preserves_protocol_and_runtime_checkable as test_preserves_protocol_and_runtime_checkable,
        test_preserves_type_checking_import as test_preserves_type_checking_import,
        test_preserves_typealias_import_when_class_level_usage_exists as test_preserves_typealias_import_when_class_level_usage_exists,
        test_preserves_used_imports_when_import_precedes_usage as test_preserves_used_imports_when_import_precedes_usage,
        test_preserves_used_typing_imports as test_preserves_used_typing_imports,
        test_removes_all_imports_when_none_used_import_first as test_removes_all_imports_when_none_used_import_first,
        test_removes_all_unused_typing_imports as test_removes_all_unused_typing_imports,
        test_removes_dead_typealias_import as test_removes_dead_typealias_import,
        test_removes_typealias_import_only_when_all_usages_converted as test_removes_typealias_import_only_when_all_usages_converted,
        test_removes_unused_preserves_used_when_import_precedes_usage as test_removes_unused_preserves_used_when_import_precedes_usage,
        test_replaces_container_union as test_replaces_container_union,
        test_replaces_numeric_union as test_replaces_numeric_union,
        test_replaces_primitives_union as test_replaces_primitives_union,
        test_replaces_scalar_union as test_replaces_scalar_union,
        test_skips_definition_files as test_skips_definition_files,
        test_skips_union_with_none as test_skips_union_with_none,
        test_typealias_conversion_preserves_used_typing_siblings as test_typealias_conversion_preserves_used_typing_siblings,
    )
    from tests.unit.refactor.test_main_cli import (
        refactor_main as refactor_main,
        test_refactor_census_rejects_apply_before_subcommand as test_refactor_census_rejects_apply_before_subcommand,
        test_refactor_centralize_accepts_apply_before_subcommand as test_refactor_centralize_accepts_apply_before_subcommand,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "EngineSafetyStub": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "EngineSafetyStub",
    ],
    "FAMILY_FILE_MAP": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_FILE_MAP",
    ],
    "FAMILY_SUFFIX_MAP": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "FAMILY_SUFFIX_MAP",
    ],
    "refactor_main": ["tests.unit.refactor.test_main_cli", "refactor_main"],
    "rope_project": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "rope_project",
    ],
    "test_all_three_capabilities_in_one_pass": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_all_three_capabilities_in_one_pass",
    ],
    "test_build_impact_map_extracts_rename_entries": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_rename_entries",
    ],
    "test_build_impact_map_extracts_signature_entries": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_build_impact_map_extracts_signature_entries",
    ],
    "test_class_reconstructor_reorders_each_contiguous_method_block": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_each_contiguous_method_block",
    ],
    "test_class_reconstructor_reorders_methods_by_config": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_reorders_methods_by_config",
    ],
    "test_class_reconstructor_skips_interleaved_non_method_members": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_class_reconstructor_skips_interleaved_non_method_members",
    ],
    "test_converts_multiple_aliases": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_multiple_aliases",
    ],
    "test_converts_typealias_to_pep695": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_converts_typealias_to_pep695",
    ],
    "test_detects_attribute_base_class": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_attribute_base_class",
    ],
    "test_detects_basemodel_in_non_model_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_basemodel_in_non_model_file",
    ],
    "test_detects_missing_local_composition_base": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_detects_missing_local_composition_base",
    ],
    "test_detects_multiple_models": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_detects_multiple_models",
    ],
    "test_detects_only_wrong_alias_in_mixed_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_only_wrong_alias_in_mixed_import",
    ],
    "test_detects_same_project_submodule_alias_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_same_project_submodule_alias_import",
    ],
    "test_detects_wrong_source_m_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_m_import",
    ],
    "test_detects_wrong_source_u_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_detects_wrong_source_u_import",
    ],
    "test_engine_always_enables_class_nesting_file_rule": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_engine_always_enables_class_nesting_file_rule",
    ],
    "test_ensure_future_annotations_after_docstring": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_after_docstring",
    ],
    "test_ensure_future_annotations_moves_existing_import_to_top": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_ensure_future_annotations_moves_existing_import_to_top",
    ],
    "test_import_alias_detector_skips_facade_and_subclass_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_facade_and_subclass_files",
    ],
    "test_import_alias_detector_skips_nested_private_and_as_renames": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_nested_private_and_as_renames",
    ],
    "test_import_alias_detector_skips_private_and_class_imports": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_import_alias_detector_skips_private_and_class_imports",
    ],
    "test_import_modernizer_adds_c_when_existing_c_is_aliased": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    ],
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    ],
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    ],
    "test_import_modernizer_partial_import_keeps_unmapped_symbols": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    ],
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    ],
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    ],
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    ],
    "test_import_modernizer_updates_aliased_symbol_usage": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_import_modernizer_updates_aliased_symbol_usage",
    ],
    "test_infra_refactor_analysis": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "",
    ],
    "test_infra_refactor_class_and_propagation": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "",
    ],
    "test_infra_refactor_class_placement": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "",
    ],
    "test_infra_refactor_engine": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "",
    ],
    "test_infra_refactor_import_modernizer": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "",
    ],
    "test_infra_refactor_legacy_and_annotations": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "",
    ],
    "test_infra_refactor_mro_completeness": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "",
    ],
    "test_infra_refactor_mro_import_rewriter": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "",
    ],
    "test_infra_refactor_namespace_aliases": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "",
    ],
    "test_infra_refactor_namespace_source": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "",
    ],
    "test_infra_refactor_pattern_corrections": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "",
    ],
    "test_infra_refactor_project_classifier": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "",
    ],
    "test_infra_refactor_safety": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "",
    ],
    "test_infra_refactor_typing_unifier": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "",
    ],
    "test_injects_t_import_when_needed": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_injects_t_import_when_needed",
    ],
    "test_lazy_import_rule_hoists_import_to_module_level": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_hoists_import_to_module_level",
    ],
    "test_lazy_import_rule_uses_fix_action_for_hoist": [
        "tests.unit.refactor.test_infra_refactor_import_modernizer",
        "test_lazy_import_rule_uses_fix_action_for_hoist",
    ],
    "test_legacy_import_bypass_collapses_to_primary_import": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_import_bypass_collapses_to_primary_import",
    ],
    "test_legacy_rule_uses_fix_action_remove_for_aliases": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_rule_uses_fix_action_remove_for_aliases",
    ],
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_function_is_inlined_as_alias": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_function_is_inlined_as_alias",
    ],
    "test_legacy_wrapper_non_passthrough_is_not_inlined": [
        "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
        "test_legacy_wrapper_non_passthrough_is_not_inlined",
    ],
    "test_main_analyze_violations_is_read_only": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_is_read_only",
    ],
    "test_main_analyze_violations_writes_json_report": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_main_analyze_violations_writes_json_report",
    ],
    "test_main_cli": ["tests.unit.refactor.test_main_cli", ""],
    "test_migrate_workspace_applies_consumer_rewrites": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "test_migrate_workspace_applies_consumer_rewrites",
    ],
    "test_migrate_workspace_dry_run_preserves_files": [
        "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
        "test_migrate_workspace_dry_run_preserves_files",
    ],
    "test_mro_checker_keeps_external_attribute_base": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_checker_keeps_external_attribute_base",
    ],
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    ],
    "test_namespace_rewriter_keeps_contextual_alias_subset": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_keeps_contextual_alias_subset",
    ],
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_only_rewrites_runtime_alias_imports",
    ],
    "test_namespace_rewriter_skips_facade_and_subclass_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_facade_and_subclass_files",
    ],
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates": [
        "tests.unit.refactor.test_infra_refactor_namespace_aliases",
        "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates",
    ],
    "test_no_duplicate_t_import_when_t_from_project_package": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_no_duplicate_t_import_when_t_from_project_package",
    ],
    "test_non_pydantic_class_not_flagged": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_non_pydantic_class_not_flagged",
    ],
    "test_noop_clean_module": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_noop_clean_module",
    ],
    "test_pattern_rule_converts_dict_annotations_to_mapping": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_converts_dict_annotations_to_mapping",
    ],
    "test_pattern_rule_keeps_dict_param_when_copy_used": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_copy_used",
    ],
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_dict_param_when_subscript_mutated",
    ],
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast",
    ],
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_optionally_converts_return_annotations_to_mapping",
    ],
    "test_pattern_rule_removes_configured_redundant_casts": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_configured_redundant_casts",
    ],
    "test_pattern_rule_removes_nested_type_object_cast_chain": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_removes_nested_type_object_cast_chain",
    ],
    "test_pattern_rule_skips_overload_signatures": [
        "tests.unit.refactor.test_infra_refactor_pattern_corrections",
        "test_pattern_rule_skips_overload_signatures",
    ],
    "test_preserves_annotated_in_function_params": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_annotated_in_function_params",
    ],
    "test_preserves_non_matching_unions": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_non_matching_unions",
    ],
    "test_preserves_override_in_method": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_override_in_method",
    ],
    "test_preserves_protocol_and_runtime_checkable": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_protocol_and_runtime_checkable",
    ],
    "test_preserves_type_checking_import": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_type_checking_import",
    ],
    "test_preserves_typealias_import_when_class_level_usage_exists": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_typealias_import_when_class_level_usage_exists",
    ],
    "test_preserves_used_imports_when_import_precedes_usage": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_imports_when_import_precedes_usage",
    ],
    "test_preserves_used_typing_imports": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_preserves_used_typing_imports",
    ],
    "test_project_without_alias_facade_has_no_violation": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_project_without_alias_facade_has_no_violation",
    ],
    "test_read_project_metadata_preserves_pep621_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_pep621_dependency_order",
    ],
    "test_read_project_metadata_preserves_poetry_dependency_order": [
        "tests.unit.refactor.test_infra_refactor_project_classifier",
        "test_read_project_metadata_preserves_poetry_dependency_order",
    ],
    "test_refactor_census_rejects_apply_before_subcommand": [
        "tests.unit.refactor.test_main_cli",
        "test_refactor_census_rejects_apply_before_subcommand",
    ],
    "test_refactor_centralize_accepts_apply_before_subcommand": [
        "tests.unit.refactor.test_main_cli",
        "test_refactor_centralize_accepts_apply_before_subcommand",
    ],
    "test_refactor_files_skips_non_python_inputs": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_files_skips_non_python_inputs",
    ],
    "test_refactor_project_integrates_safety_manager": [
        "tests.unit.refactor.test_infra_refactor_safety",
        "test_refactor_project_integrates_safety_manager",
    ],
    "test_refactor_project_scans_tests_and_scripts_dirs": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_refactor_project_scans_tests_and_scripts_dirs",
    ],
    "test_removes_all_imports_when_none_used_import_first": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_imports_when_none_used_import_first",
    ],
    "test_removes_all_unused_typing_imports": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_all_unused_typing_imports",
    ],
    "test_removes_dead_typealias_import": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_dead_typealias_import",
    ],
    "test_removes_typealias_import_only_when_all_usages_converted": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_typealias_import_only_when_all_usages_converted",
    ],
    "test_removes_unused_preserves_used_when_import_precedes_usage": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_removes_unused_preserves_used_when_import_precedes_usage",
    ],
    "test_replaces_container_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_container_union",
    ],
    "test_replaces_numeric_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_numeric_union",
    ],
    "test_replaces_primitives_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_primitives_union",
    ],
    "test_replaces_scalar_union": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_replaces_scalar_union",
    ],
    "test_rewriter_adds_missing_base_and_formats": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_rewriter_adds_missing_base_and_formats",
    ],
    "test_rewriter_namespace_source_is_idempotent_with_ruff": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_namespace_source_is_idempotent_with_ruff",
    ],
    "test_rewriter_preserves_non_alias_symbols": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_preserves_non_alias_symbols",
    ],
    "test_rewriter_splits_mixed_imports_correctly": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_rewriter_splits_mixed_imports_correctly",
    ],
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    ],
    "test_rule_dispatch_fails_on_unknown_rule_mapping": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_fails_on_unknown_rule_mapping",
    ],
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    ],
    "test_rule_dispatch_prefers_fix_action_metadata": [
        "tests.unit.refactor.test_infra_refactor_engine",
        "test_rule_dispatch_prefers_fix_action_metadata",
    ],
    "test_signature_propagation_removes_and_adds_keywords": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_removes_and_adds_keywords",
    ],
    "test_signature_propagation_renames_call_keyword": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_signature_propagation_renames_call_keyword",
    ],
    "test_skips_definition_files": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_definition_files",
    ],
    "test_skips_facade_declaration_files": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_facade_declaration_files",
    ],
    "test_skips_import_as_rename": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_import_as_rename",
    ],
    "test_skips_init_file": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_init_file",
    ],
    "test_skips_models_directory": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_directory",
    ],
    "test_skips_models_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_models_file",
    ],
    "test_skips_non_alias_symbols": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_non_alias_symbols",
    ],
    "test_skips_non_facade_files": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_non_facade_files",
    ],
    "test_skips_private_candidate_classes": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_private_candidate_classes",
    ],
    "test_skips_private_class": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_private_class",
    ],
    "test_skips_protected_files": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_protected_files",
    ],
    "test_skips_r_alias_universal_exception": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_r_alias_universal_exception",
    ],
    "test_skips_same_project_private_submodule": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_private_submodule",
    ],
    "test_skips_same_project_submodule_class_import": [
        "tests.unit.refactor.test_infra_refactor_namespace_source",
        "test_skips_same_project_submodule_class_import",
    ],
    "test_skips_settings_file": [
        "tests.unit.refactor.test_infra_refactor_class_placement",
        "test_skips_settings_file",
    ],
    "test_skips_union_with_none": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_skips_union_with_none",
    ],
    "test_skips_when_candidate_is_already_in_facade_bases": [
        "tests.unit.refactor.test_infra_refactor_mro_completeness",
        "test_skips_when_candidate_is_already_in_facade_bases",
    ],
    "test_symbol_propagation_keeps_alias_reference_when_asname_used": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_keeps_alias_reference_when_asname_used",
    ],
    "test_symbol_propagation_renames_import_and_local_references": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_renames_import_and_local_references",
    ],
    "test_symbol_propagation_updates_mro_base_references": [
        "tests.unit.refactor.test_infra_refactor_class_and_propagation",
        "test_symbol_propagation_updates_mro_base_references",
    ],
    "test_typealias_conversion_preserves_used_typing_siblings": [
        "tests.unit.refactor.test_infra_refactor_typing_unifier",
        "test_typealias_conversion_preserves_used_typing_siblings",
    ],
    "test_violation_analysis_counts_massive_patterns": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analysis_counts_massive_patterns",
    ],
    "test_violation_analyzer_skips_non_utf8_files": [
        "tests.unit.refactor.test_infra_refactor_analysis",
        "test_violation_analyzer_skips_non_utf8_files",
    ],
}

_EXPORTS: Sequence[str] = [
    "EngineSafetyStub",
    "FAMILY_FILE_MAP",
    "FAMILY_SUFFIX_MAP",
    "refactor_main",
    "rope_project",
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
    "test_detects_only_wrong_alias_in_mixed_import",
    "test_detects_same_project_submodule_alias_import",
    "test_detects_wrong_source_m_import",
    "test_detects_wrong_source_u_import",
    "test_engine_always_enables_class_nesting_file_rule",
    "test_ensure_future_annotations_after_docstring",
    "test_ensure_future_annotations_moves_existing_import_to_top",
    "test_import_alias_detector_skips_facade_and_subclass_files",
    "test_import_alias_detector_skips_nested_private_and_as_renames",
    "test_import_alias_detector_skips_private_and_class_imports",
    "test_import_modernizer_adds_c_when_existing_c_is_aliased",
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow",
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage",
    "test_import_modernizer_partial_import_keeps_unmapped_symbols",
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias",
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function",
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked",
    "test_import_modernizer_updates_aliased_symbol_usage",
    "test_infra_refactor_analysis",
    "test_infra_refactor_class_and_propagation",
    "test_infra_refactor_class_placement",
    "test_infra_refactor_engine",
    "test_infra_refactor_import_modernizer",
    "test_infra_refactor_legacy_and_annotations",
    "test_infra_refactor_mro_completeness",
    "test_infra_refactor_mro_import_rewriter",
    "test_infra_refactor_namespace_aliases",
    "test_infra_refactor_namespace_source",
    "test_infra_refactor_pattern_corrections",
    "test_infra_refactor_project_classifier",
    "test_infra_refactor_safety",
    "test_infra_refactor_typing_unifier",
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
    "test_main_cli",
    "test_migrate_workspace_applies_consumer_rewrites",
    "test_migrate_workspace_dry_run_preserves_files",
    "test_mro_checker_keeps_external_attribute_base",
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance",
    "test_namespace_rewriter_keeps_contextual_alias_subset",
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports",
    "test_namespace_rewriter_skips_facade_and_subclass_files",
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates",
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
    "test_project_without_alias_facade_has_no_violation",
    "test_read_project_metadata_preserves_pep621_dependency_order",
    "test_read_project_metadata_preserves_poetry_dependency_order",
    "test_refactor_census_rejects_apply_before_subcommand",
    "test_refactor_centralize_accepts_apply_before_subcommand",
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
    "test_rewriter_namespace_source_is_idempotent_with_ruff",
    "test_rewriter_preserves_non_alias_symbols",
    "test_rewriter_splits_mixed_imports_correctly",
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config",
    "test_rule_dispatch_fails_on_unknown_rule_mapping",
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping",
    "test_rule_dispatch_prefers_fix_action_metadata",
    "test_signature_propagation_removes_and_adds_keywords",
    "test_signature_propagation_renames_call_keyword",
    "test_skips_definition_files",
    "test_skips_facade_declaration_files",
    "test_skips_import_as_rename",
    "test_skips_init_file",
    "test_skips_models_directory",
    "test_skips_models_file",
    "test_skips_non_alias_symbols",
    "test_skips_non_facade_files",
    "test_skips_private_candidate_classes",
    "test_skips_private_class",
    "test_skips_protected_files",
    "test_skips_r_alias_universal_exception",
    "test_skips_same_project_private_submodule",
    "test_skips_same_project_submodule_class_import",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
