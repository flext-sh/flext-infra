# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Refactor package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from tests.unit.refactor.test_infra_refactor_analysis import *
    from tests.unit.refactor.test_infra_refactor_class_and_propagation import *
    from tests.unit.refactor.test_infra_refactor_class_placement import *
    from tests.unit.refactor.test_infra_refactor_engine import *
    from tests.unit.refactor.test_infra_refactor_import_modernizer import *
    from tests.unit.refactor.test_infra_refactor_legacy_and_annotations import *
    from tests.unit.refactor.test_infra_refactor_mro_completeness import *
    from tests.unit.refactor.test_infra_refactor_mro_import_rewriter import *
    from tests.unit.refactor.test_infra_refactor_namespace_aliases import *
    from tests.unit.refactor.test_infra_refactor_namespace_source import *
    from tests.unit.refactor.test_infra_refactor_pattern_corrections import *
    from tests.unit.refactor.test_infra_refactor_project_classifier import *
    from tests.unit.refactor.test_infra_refactor_safety import *
    from tests.unit.refactor.test_infra_refactor_typing_unifier import *
    from tests.unit.refactor.test_main_cli import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "EngineSafetyStub": "tests.unit.refactor.test_infra_refactor_safety",
    "FAMILY_FILE_MAP": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "FAMILY_SUFFIX_MAP": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "refactor_main": "tests.unit.refactor.test_main_cli",
    "rope_project": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_all_three_capabilities_in_one_pass": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_build_impact_map_extracts_rename_entries": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_build_impact_map_extracts_signature_entries": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_class_reconstructor_reorders_each_contiguous_method_block": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_class_reconstructor_reorders_methods_by_config": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_class_reconstructor_skips_interleaved_non_method_members": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_converts_multiple_aliases": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_converts_typealias_to_pep695": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_detects_attribute_base_class": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_detects_basemodel_in_non_model_file": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_detects_missing_local_composition_base": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_detects_multiple_models": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_detects_only_wrong_alias_in_mixed_import": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_detects_same_project_submodule_alias_import": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_detects_wrong_source_m_import": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_detects_wrong_source_u_import": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_engine_always_enables_class_nesting_file_rule": "tests.unit.refactor.test_infra_refactor_engine",
    "test_ensure_future_annotations_after_docstring": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_ensure_future_annotations_moves_existing_import_to_top": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_import_alias_detector_skips_facade_and_subclass_files": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_import_alias_detector_skips_nested_private_and_as_renames": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_import_alias_detector_skips_private_and_class_imports": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_import_modernizer_adds_c_when_existing_c_is_aliased": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_does_not_rewrite_function_parameter_shadow": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_does_not_rewrite_rebound_local_name_usage": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_partial_import_keeps_unmapped_symbols": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_partial_import_with_asname_keeps_unmapped_alias": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_skips_rewrite_when_runtime_alias_shadowed_in_function": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_skips_when_runtime_alias_name_is_blocked": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_import_modernizer_updates_aliased_symbol_usage": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_infra_refactor_analysis": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_infra_refactor_class_and_propagation": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_infra_refactor_class_placement": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_infra_refactor_engine": "tests.unit.refactor.test_infra_refactor_engine",
    "test_infra_refactor_import_modernizer": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_infra_refactor_legacy_and_annotations": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_infra_refactor_mro_completeness": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_infra_refactor_mro_import_rewriter": "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
    "test_infra_refactor_namespace_aliases": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_infra_refactor_namespace_source": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_infra_refactor_pattern_corrections": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_infra_refactor_project_classifier": "tests.unit.refactor.test_infra_refactor_project_classifier",
    "test_infra_refactor_safety": "tests.unit.refactor.test_infra_refactor_safety",
    "test_infra_refactor_typing_unifier": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_injects_t_import_when_needed": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_lazy_import_rule_hoists_import_to_module_level": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_lazy_import_rule_uses_fix_action_for_hoist": "tests.unit.refactor.test_infra_refactor_import_modernizer",
    "test_legacy_import_bypass_collapses_to_primary_import": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_legacy_rule_uses_fix_action_remove_for_aliases": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_legacy_wrapper_forwarding_keywords_is_inlined_as_alias": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_legacy_wrapper_forwarding_varargs_is_inlined_as_alias": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_legacy_wrapper_function_is_inlined_as_alias": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_legacy_wrapper_non_passthrough_is_not_inlined": "tests.unit.refactor.test_infra_refactor_legacy_and_annotations",
    "test_main_analyze_violations_is_read_only": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_main_analyze_violations_writes_json_report": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_main_cli": "tests.unit.refactor.test_main_cli",
    "test_migrate_workspace_applies_consumer_rewrites": "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
    "test_migrate_workspace_dry_run_preserves_files": "tests.unit.refactor.test_infra_refactor_mro_import_rewriter",
    "test_mro_checker_keeps_external_attribute_base": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_mro_redundancy_checker_removes_nested_attribute_inheritance": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_namespace_rewriter_keeps_contextual_alias_subset": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_namespace_rewriter_only_rewrites_runtime_alias_imports": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_namespace_rewriter_skips_facade_and_subclass_files": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates": "tests.unit.refactor.test_infra_refactor_namespace_aliases",
    "test_no_duplicate_t_import_when_t_from_project_package": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_non_pydantic_class_not_flagged": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_noop_clean_module": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_pattern_rule_converts_dict_annotations_to_mapping": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_keeps_dict_param_when_copy_used": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_keeps_dict_param_when_subscript_mutated": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_keeps_type_cast_when_not_nested_object_cast": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_optionally_converts_return_annotations_to_mapping": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_removes_configured_redundant_casts": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_removes_nested_type_object_cast_chain": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_pattern_rule_skips_overload_signatures": "tests.unit.refactor.test_infra_refactor_pattern_corrections",
    "test_preserves_annotated_in_function_params": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_non_matching_unions": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_override_in_method": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_protocol_and_runtime_checkable": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_type_checking_import": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_typealias_import_when_class_level_usage_exists": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_used_imports_when_import_precedes_usage": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_preserves_used_typing_imports": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_project_without_alias_facade_has_no_violation": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_read_project_metadata_preserves_pep621_dependency_order": "tests.unit.refactor.test_infra_refactor_project_classifier",
    "test_read_project_metadata_preserves_poetry_dependency_order": "tests.unit.refactor.test_infra_refactor_project_classifier",
    "test_refactor_census_rejects_apply_before_subcommand": "tests.unit.refactor.test_main_cli",
    "test_refactor_centralize_accepts_apply_before_subcommand": "tests.unit.refactor.test_main_cli",
    "test_refactor_files_skips_non_python_inputs": "tests.unit.refactor.test_infra_refactor_engine",
    "test_refactor_project_integrates_safety_manager": "tests.unit.refactor.test_infra_refactor_safety",
    "test_refactor_project_scans_tests_and_scripts_dirs": "tests.unit.refactor.test_infra_refactor_engine",
    "test_removes_all_imports_when_none_used_import_first": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_removes_all_unused_typing_imports": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_removes_dead_typealias_import": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_removes_typealias_import_only_when_all_usages_converted": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_removes_unused_preserves_used_when_import_precedes_usage": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_replaces_container_union": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_replaces_numeric_union": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_replaces_primitives_union": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_replaces_scalar_union": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_rewriter_adds_missing_base_and_formats": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_rewriter_namespace_source_is_idempotent_with_ruff": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_rewriter_preserves_non_alias_symbols": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_rewriter_splits_mixed_imports_correctly": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_rule_dispatch_fails_on_invalid_pattern_rule_config": "tests.unit.refactor.test_infra_refactor_engine",
    "test_rule_dispatch_fails_on_unknown_rule_mapping": "tests.unit.refactor.test_infra_refactor_engine",
    "test_rule_dispatch_keeps_legacy_id_fallback_mapping": "tests.unit.refactor.test_infra_refactor_engine",
    "test_rule_dispatch_prefers_fix_action_metadata": "tests.unit.refactor.test_infra_refactor_engine",
    "test_signature_propagation_removes_and_adds_keywords": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_signature_propagation_renames_call_keyword": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_skips_definition_files": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_skips_facade_declaration_files": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_import_as_rename": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_init_file": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_models_directory": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_skips_models_file": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_skips_non_alias_symbols": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_non_facade_files": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_skips_private_candidate_classes": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_skips_private_class": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_skips_protected_files": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_skips_r_alias_universal_exception": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_same_project_private_submodule": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_same_project_submodule_class_import": "tests.unit.refactor.test_infra_refactor_namespace_source",
    "test_skips_settings_file": "tests.unit.refactor.test_infra_refactor_class_placement",
    "test_skips_union_with_none": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_skips_when_candidate_is_already_in_facade_bases": "tests.unit.refactor.test_infra_refactor_mro_completeness",
    "test_symbol_propagation_keeps_alias_reference_when_asname_used": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_symbol_propagation_renames_import_and_local_references": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_symbol_propagation_updates_mro_base_references": "tests.unit.refactor.test_infra_refactor_class_and_propagation",
    "test_typealias_conversion_preserves_used_typing_siblings": "tests.unit.refactor.test_infra_refactor_typing_unifier",
    "test_violation_analysis_counts_massive_patterns": "tests.unit.refactor.test_infra_refactor_analysis",
    "test_violation_analyzer_skips_non_utf8_files": "tests.unit.refactor.test_infra_refactor_analysis",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
