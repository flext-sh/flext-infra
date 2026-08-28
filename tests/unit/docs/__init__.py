# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .auditor_budgets_tests import TestLoadAuditBudgets
    from .auditor_cli_tests import (
        test_auditor_main_help_exits_zero,
        test_auditor_main_strict_failure_returns_one,
        test_auditor_main_writes_reports_for_selected_project,
    )
    from .auditor_codeblocks_tests import (
        test_docs_python_codeblock_issues_ignore_snippet_only_rules,
        test_docs_python_codeblock_issues_report_invalid_python,
        test_docstring_issues_accept_assignment_docstrings,
    )
    from .auditor_docstring_tests import TestsDocstringCoverage
    from .auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorGithubLinks,
        TestAuditorToMarkdown,
    )
    from .auditor_scope_tests import TestAuditorForbiddenTerms, TestAuditorScope
    from .auditor_stale_symbols_tests import (
        test_docstring_issues_accepts_direct_part_mro_docstring,
        test_generated_api_reference_accepts_live_public_symbol,
        test_generated_api_reference_reports_missing_public_symbol,
        test_manual_docs_report_live_symbol_mentions,
        test_public_contract_resolves_imported_lazy_import_map,
        test_public_contract_resolves_imported_lazy_public_exports,
        test_public_contract_resolves_local_tuple_public_exports,
    )
    from .auditor_tests import (
        TestAuditorCore,
        TestAuditorNormalize,
        auditor,
        is_external,
        normalize_link,
        should_skip_target,
    )
    from .builder_scope_tests import (
        test_build_missing_settings_failure_has_empty_site_dir,
        test_build_returns_repository_report,
        test_build_uses_custom_output_dir,
    )
    from .builder_tests import TestBuilderCore, builder
    from .fixer_internals_tests import (
        test_anchorize_and_build_toc_are_public_helpers,
        test_docs_maybe_fix_link_adds_md_suffix_when_target_exists,
        test_fix_keeps_closing_fence_on_its_own_line,
        test_fix_updates_docs_readme_when_apply_is_enabled,
    )
    from .fixer_tests import (
        test_fix_apply_updates_docs_file_and_writes_reports,
        test_fix_check_apply_check_converges,
        test_fix_item_model_tracks_link_and_toc_counts,
        test_fix_returns_reports_for_root_and_selected_project,
    )
    from .generator_internals_tests import (
        test_anchorize_keeps_underscores_like_python_markdown,
        test_anchorize_normalizes_headings,
        test_build_toc_lists_h2_and_h3_sections,
        test_build_toc_skips_headings_inside_fenced_code,
        test_generate_creates_selected_project_reports,
        test_generated_markdown_is_toc_normalized_before_write,
        test_generated_non_markdown_preserves_exact_content,
        test_update_toc_preserves_single_blank_after_level_one_heading,
        test_update_toc_replaces_existing_block,
    )
    from .generator_tests import (
        test_docs_policy_declares_cross_project_relative_link_pattern,
        test_generate_apply_writes_summary_and_report,
        test_generate_dry_run_reports_real_drift,
        test_generate_preserves_declared_export_order_and_is_idempotent,
        test_generate_report_tracks_written_files,
        test_generate_returns_reports_for_root_and_selected_project,
        test_generated_collection_rules_pointer_stays_within_consumer_limit,
        test_generated_file_model_is_frozen,
        test_generated_markdown_starts_with_level_one_heading,
        test_generated_mkdocstrings_directive_preserves_indented_options,
        test_generated_prose_wraps_without_reformatting_directive_blocks,
        test_governed_api_survives_generation_and_curated_paths_are_unowned,
        test_root_generated_catalog_survives_project_pass_and_required_indexes_validate,
        test_stale_generated_file_drift_converges_after_apply,
    )
    from .main_commands_tests import (
        test_auditor_execute_fails_in_strict_mode_on_broken_links,
        test_builder_execute_fails_when_mkdocs_is_missing,
        test_builder_execute_fails_with_invalid_mkdocs_config,
        test_fixer_execute_applies_link_and_toc_updates,
        test_fixer_execute_fails_on_unapplied_drift,
        test_generate_fix_cycle_is_byte_identical_on_second_run,
        test_generator_execute_writes_repository_report,
        test_validator_execute_fails_before_generation_and_succeeds_after,
    )
    from .main_entry_tests import TestsDocsCli
    from .main_tests import (
        test_docs_cli_validate_apply_passes_after_generate_apply,
        test_docs_cli_validate_fails_before_generation,
    )
    from .render_guides_index_tests import (
        test_guides_index_links_only_guides_that_exist,
        test_guides_index_omits_links_when_no_guide_exists,
    )
    from .render_tests import TestsDocsRenderExcludeDocs
    from .server_tests import TestsFlextInfraDocServer
    from .shared_iter_tests import TestIterMarkdownFiles
    from .shared_tests import (
        test_build_scopes_preserves_declared_workspace_root_and_members,
        test_build_scopes_preserves_declared_workspace_without_materialized_members,
        test_build_scopes_preserves_disabled_root_policy,
        test_build_scopes_preserves_discovered_package_name,
        test_build_scopes_returns_root_and_selected_projects,
        test_build_scopes_skips_missing_projects,
        test_build_scopes_treats_non_flext_project_as_its_own_root,
        test_build_scopes_uses_custom_output_dir,
        test_build_scopes_without_filter_still_returns_root_scope,
        test_doc_scope_creation,
        test_doc_scope_requires_name,
    )
    from .shared_write_tests import (
        test_json_write_accepts_pydantic_model,
        test_json_write_round_trips_dict_payload,
        test_write_markdown_fails_for_non_directory_parent,
        test_write_markdown_preserves_empty_lines,
        test_write_markdown_writes_exact_content,
    )
    from .test_docs_update_toc_frontmatter import (
        test_docs_update_toc_inserts_after_h1_beyond_frontmatter,
        test_docs_update_toc_repairs_invented_h1_before_frontmatter,
        test_docs_update_toc_still_invents_h1_for_headingless_stub,
    )
    from .validator_internals_tests import (
        test_docs_has_adr_reference_detects_marker,
        test_docs_load_required_skills_reads_architecture_config,
        test_docs_write_todo_writes_only_for_project_scopes,
    )
    from .validator_tests import (
        test_validate_report_model_fields,
        test_validate_workspace_apply_writes_project_todo,
        test_validate_workspace_fails_before_generated_files_exist,
        test_validate_workspace_passes_after_generate_apply,
    )
__all__: tuple[str, ...] = (
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorGithubLinks",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorToMarkdown",
    "TestBuilderCore",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestsDocsCli",
    "TestsDocsRenderExcludeDocs",
    "TestsDocstringCoverage",
    "TestsFlextInfraDocServer",
    "auditor",
    "builder",
    "is_external",
    "normalize_link",
    "should_skip_target",
    "test_anchorize_and_build_toc_are_public_helpers",
    "test_anchorize_keeps_underscores_like_python_markdown",
    "test_anchorize_normalizes_headings",
    "test_auditor_execute_fails_in_strict_mode_on_broken_links",
    "test_auditor_main_help_exits_zero",
    "test_auditor_main_strict_failure_returns_one",
    "test_auditor_main_writes_reports_for_selected_project",
    "test_build_missing_settings_failure_has_empty_site_dir",
    "test_build_returns_repository_report",
    "test_build_scopes_preserves_declared_workspace_root_and_members",
    "test_build_scopes_preserves_declared_workspace_without_materialized_members",
    "test_build_scopes_preserves_disabled_root_policy",
    "test_build_scopes_preserves_discovered_package_name",
    "test_build_scopes_returns_root_and_selected_projects",
    "test_build_scopes_skips_missing_projects",
    "test_build_scopes_treats_non_flext_project_as_its_own_root",
    "test_build_scopes_uses_custom_output_dir",
    "test_build_scopes_without_filter_still_returns_root_scope",
    "test_build_toc_lists_h2_and_h3_sections",
    "test_build_toc_skips_headings_inside_fenced_code",
    "test_build_uses_custom_output_dir",
    "test_builder_execute_fails_when_mkdocs_is_missing",
    "test_builder_execute_fails_with_invalid_mkdocs_config",
    "test_doc_scope_creation",
    "test_doc_scope_requires_name",
    "test_docs_cli_validate_apply_passes_after_generate_apply",
    "test_docs_cli_validate_fails_before_generation",
    "test_docs_has_adr_reference_detects_marker",
    "test_docs_load_required_skills_reads_architecture_config",
    "test_docs_maybe_fix_link_adds_md_suffix_when_target_exists",
    "test_docs_policy_declares_cross_project_relative_link_pattern",
    "test_docs_python_codeblock_issues_ignore_snippet_only_rules",
    "test_docs_python_codeblock_issues_report_invalid_python",
    "test_docs_update_toc_inserts_after_h1_beyond_frontmatter",
    "test_docs_update_toc_repairs_invented_h1_before_frontmatter",
    "test_docs_update_toc_still_invents_h1_for_headingless_stub",
    "test_docs_write_todo_writes_only_for_project_scopes",
    "test_docstring_issues_accept_assignment_docstrings",
    "test_docstring_issues_accepts_direct_part_mro_docstring",
    "test_fix_apply_updates_docs_file_and_writes_reports",
    "test_fix_check_apply_check_converges",
    "test_fix_item_model_tracks_link_and_toc_counts",
    "test_fix_keeps_closing_fence_on_its_own_line",
    "test_fix_returns_reports_for_root_and_selected_project",
    "test_fix_updates_docs_readme_when_apply_is_enabled",
    "test_fixer_execute_applies_link_and_toc_updates",
    "test_fixer_execute_fails_on_unapplied_drift",
    "test_generate_apply_writes_summary_and_report",
    "test_generate_creates_selected_project_reports",
    "test_generate_dry_run_reports_real_drift",
    "test_generate_fix_cycle_is_byte_identical_on_second_run",
    "test_generate_preserves_declared_export_order_and_is_idempotent",
    "test_generate_report_tracks_written_files",
    "test_generate_returns_reports_for_root_and_selected_project",
    "test_generated_api_reference_accepts_live_public_symbol",
    "test_generated_api_reference_reports_missing_public_symbol",
    "test_generated_collection_rules_pointer_stays_within_consumer_limit",
    "test_generated_file_model_is_frozen",
    "test_generated_markdown_is_toc_normalized_before_write",
    "test_generated_markdown_starts_with_level_one_heading",
    "test_generated_mkdocstrings_directive_preserves_indented_options",
    "test_generated_non_markdown_preserves_exact_content",
    "test_generated_prose_wraps_without_reformatting_directive_blocks",
    "test_generator_execute_writes_repository_report",
    "test_governed_api_survives_generation_and_curated_paths_are_unowned",
    "test_guides_index_links_only_guides_that_exist",
    "test_guides_index_omits_links_when_no_guide_exists",
    "test_json_write_accepts_pydantic_model",
    "test_json_write_round_trips_dict_payload",
    "test_manual_docs_report_live_symbol_mentions",
    "test_public_contract_resolves_imported_lazy_import_map",
    "test_public_contract_resolves_imported_lazy_public_exports",
    "test_public_contract_resolves_local_tuple_public_exports",
    "test_root_generated_catalog_survives_project_pass_and_required_indexes_validate",
    "test_stale_generated_file_drift_converges_after_apply",
    "test_update_toc_preserves_single_blank_after_level_one_heading",
    "test_update_toc_replaces_existing_block",
    "test_validate_report_model_fields",
    "test_validate_workspace_apply_writes_project_todo",
    "test_validate_workspace_fails_before_generated_files_exist",
    "test_validate_workspace_passes_after_generate_apply",
    "test_validator_execute_fails_before_generation_and_succeeds_after",
    "test_write_markdown_fails_for_non_directory_parent",
    "test_write_markdown_preserves_empty_lines",
    "test_write_markdown_writes_exact_content",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".auditor_budgets_tests": ("TestLoadAuditBudgets",),
            ".auditor_cli_tests": (
                "test_auditor_main_help_exits_zero",
                "test_auditor_main_strict_failure_returns_one",
                "test_auditor_main_writes_reports_for_selected_project",
            ),
            ".auditor_codeblocks_tests": (
                "test_docs_python_codeblock_issues_ignore_snippet_only_rules",
                "test_docs_python_codeblock_issues_report_invalid_python",
                "test_docstring_issues_accept_assignment_docstrings",
            ),
            ".auditor_docstring_tests": ("TestsDocstringCoverage",),
            ".auditor_links_tests": (
                "TestAuditorBrokenLinks",
                "TestAuditorGithubLinks",
                "TestAuditorToMarkdown",
            ),
            ".auditor_scope_tests": ("TestAuditorForbiddenTerms", "TestAuditorScope"),
            ".auditor_stale_symbols_tests": (
                "test_docstring_issues_accepts_direct_part_mro_docstring",
                "test_generated_api_reference_accepts_live_public_symbol",
                "test_generated_api_reference_reports_missing_public_symbol",
                "test_manual_docs_report_live_symbol_mentions",
                "test_public_contract_resolves_imported_lazy_import_map",
                "test_public_contract_resolves_imported_lazy_public_exports",
                "test_public_contract_resolves_local_tuple_public_exports",
            ),
            ".auditor_tests": (
                "TestAuditorCore",
                "TestAuditorNormalize",
                "auditor",
                "is_external",
                "normalize_link",
                "should_skip_target",
            ),
            ".builder_scope_tests": (
                "test_build_missing_settings_failure_has_empty_site_dir",
                "test_build_returns_repository_report",
                "test_build_uses_custom_output_dir",
            ),
            ".builder_tests": ("TestBuilderCore", "builder"),
            ".fixer_internals_tests": (
                "test_anchorize_and_build_toc_are_public_helpers",
                "test_docs_maybe_fix_link_adds_md_suffix_when_target_exists",
                "test_fix_keeps_closing_fence_on_its_own_line",
                "test_fix_updates_docs_readme_when_apply_is_enabled",
            ),
            ".fixer_tests": (
                "test_fix_apply_updates_docs_file_and_writes_reports",
                "test_fix_check_apply_check_converges",
                "test_fix_item_model_tracks_link_and_toc_counts",
                "test_fix_returns_reports_for_root_and_selected_project",
            ),
            ".generator_internals_tests": (
                "test_anchorize_keeps_underscores_like_python_markdown",
                "test_anchorize_normalizes_headings",
                "test_build_toc_lists_h2_and_h3_sections",
                "test_build_toc_skips_headings_inside_fenced_code",
                "test_generate_creates_selected_project_reports",
                "test_generated_markdown_is_toc_normalized_before_write",
                "test_generated_non_markdown_preserves_exact_content",
                "test_update_toc_preserves_single_blank_after_level_one_heading",
                "test_update_toc_replaces_existing_block",
            ),
            ".generator_tests": (
                "test_docs_policy_declares_cross_project_relative_link_pattern",
                "test_generate_apply_writes_summary_and_report",
                "test_generate_dry_run_reports_real_drift",
                "test_generate_preserves_declared_export_order_and_is_idempotent",
                "test_generate_report_tracks_written_files",
                "test_generate_returns_reports_for_root_and_selected_project",
                "test_generated_collection_rules_pointer_stays_within_consumer_limit",
                "test_generated_file_model_is_frozen",
                "test_generated_markdown_starts_with_level_one_heading",
                "test_generated_mkdocstrings_directive_preserves_indented_options",
                "test_generated_prose_wraps_without_reformatting_directive_blocks",
                "test_governed_api_survives_generation_and_curated_paths_are_unowned",
                "test_root_generated_catalog_survives_project_pass_and_required_indexes_validate",
                "test_stale_generated_file_drift_converges_after_apply",
            ),
            ".main_commands_tests": (
                "test_auditor_execute_fails_in_strict_mode_on_broken_links",
                "test_builder_execute_fails_when_mkdocs_is_missing",
                "test_builder_execute_fails_with_invalid_mkdocs_config",
                "test_fixer_execute_applies_link_and_toc_updates",
                "test_fixer_execute_fails_on_unapplied_drift",
                "test_generate_fix_cycle_is_byte_identical_on_second_run",
                "test_generator_execute_writes_repository_report",
                "test_validator_execute_fails_before_generation_and_succeeds_after",
            ),
            ".main_entry_tests": ("TestsDocsCli",),
            ".main_tests": (
                "test_docs_cli_validate_apply_passes_after_generate_apply",
                "test_docs_cli_validate_fails_before_generation",
            ),
            ".render_guides_index_tests": (
                "test_guides_index_links_only_guides_that_exist",
                "test_guides_index_omits_links_when_no_guide_exists",
            ),
            ".render_tests": ("TestsDocsRenderExcludeDocs",),
            ".server_tests": ("TestsFlextInfraDocServer",),
            ".shared_iter_tests": ("TestIterMarkdownFiles",),
            ".shared_tests": (
                "test_build_scopes_preserves_declared_workspace_root_and_members",
                "test_build_scopes_preserves_declared_workspace_without_materialized_members",
                "test_build_scopes_preserves_disabled_root_policy",
                "test_build_scopes_preserves_discovered_package_name",
                "test_build_scopes_returns_root_and_selected_projects",
                "test_build_scopes_skips_missing_projects",
                "test_build_scopes_treats_non_flext_project_as_its_own_root",
                "test_build_scopes_uses_custom_output_dir",
                "test_build_scopes_without_filter_still_returns_root_scope",
                "test_doc_scope_creation",
                "test_doc_scope_requires_name",
            ),
            ".shared_write_tests": (
                "test_json_write_accepts_pydantic_model",
                "test_json_write_round_trips_dict_payload",
                "test_write_markdown_fails_for_non_directory_parent",
                "test_write_markdown_preserves_empty_lines",
                "test_write_markdown_writes_exact_content",
            ),
            ".test_docs_update_toc_frontmatter": (
                "test_docs_update_toc_inserts_after_h1_beyond_frontmatter",
                "test_docs_update_toc_repairs_invented_h1_before_frontmatter",
                "test_docs_update_toc_still_invents_h1_for_headingless_stub",
            ),
            ".validator_internals_tests": (
                "test_docs_has_adr_reference_detects_marker",
                "test_docs_load_required_skills_reads_architecture_config",
                "test_docs_write_todo_writes_only_for_project_scopes",
            ),
            ".validator_tests": (
                "test_validate_report_model_fields",
                "test_validate_workspace_apply_writes_project_todo",
                "test_validate_workspace_fails_before_generated_files_exist",
                "test_validate_workspace_passes_after_generate_apply",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
