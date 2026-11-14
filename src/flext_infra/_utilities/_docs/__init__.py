# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Docs package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._docs.api import FlextInfraUtilitiesDocsApi
    from flext_infra._utilities._docs.audit import FlextInfraUtilitiesDocsAudit
    from flext_infra._utilities._docs.audit_detectors import (
        FlextInfraUtilitiesDocsAuditDetectors,
    )
    from flext_infra._utilities._docs.base import FlextInfraUtilitiesDocsBase
    from flext_infra._utilities._docs.build import FlextInfraUtilitiesDocsBuild
    from flext_infra._utilities._docs.collection import (
        FlextInfraUtilitiesDocsCollection,
    )
    from flext_infra._utilities._docs.collection_sources import (
        FlextInfraUtilitiesDocsCollectionSources,
    )
    from flext_infra._utilities._docs.command_contract import (
        FlextInfraUtilitiesDocsCommandContract,
    )
    from flext_infra._utilities._docs.contract import FlextInfraUtilitiesDocsContract
    from flext_infra._utilities._docs.fix import FlextInfraUtilitiesDocsFix
    from flext_infra._utilities._docs.generate import FlextInfraUtilitiesDocsGenerate
    from flext_infra._utilities._docs.generate_plan import (
        FlextInfraUtilitiesDocsGeneratePlan,
    )
    from flext_infra._utilities._docs.generate_project import (
        FlextInfraUtilitiesDocsGenerateProject,
    )
    from flext_infra._utilities._docs.generate_root import (
        FlextInfraUtilitiesDocsGenerateRoot,
    )
    from flext_infra._utilities._docs.generate_sources import (
        FlextInfraUtilitiesDocsGenerateSources,
    )
    from flext_infra._utilities._docs.github_links import (
        FlextInfraUtilitiesDocsGithubLinks,
    )
    from flext_infra._utilities._docs.guides import FlextInfraUtilitiesDocsGuides
    from flext_infra._utilities._docs.render import FlextInfraUtilitiesDocsRender
    from flext_infra._utilities._docs.scope import FlextInfraUtilitiesDocsScope
    from flext_infra._utilities._docs.scope_build import (
        FlextInfraUtilitiesDocsScopeBuild,
    )
    from flext_infra._utilities._docs.scope_paths import (
        FlextInfraUtilitiesDocsScopePaths,
    )
    from flext_infra._utilities._docs.scope_policy import (
        FlextInfraUtilitiesDocsScopePolicy,
    )
    from flext_infra._utilities._docs.scope_projects import (
        FlextInfraUtilitiesDocsScopeProjects,
    )
    from flext_infra._utilities._docs.scope_selection import (
        FlextInfraUtilitiesDocsScopeSelection,
    )
    from flext_infra._utilities._docs.scope_state import (
        FlextInfraUtilitiesDocsScopeState,
    )
    from flext_infra._utilities._docs.validate import FlextInfraUtilitiesDocsValidate


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsAuditDetectors",
    "FlextInfraUtilitiesDocsBase",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsCollection",
    "FlextInfraUtilitiesDocsCollectionSources",
    "FlextInfraUtilitiesDocsCommandContract",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsGeneratePlan",
    "FlextInfraUtilitiesDocsGenerateProject",
    "FlextInfraUtilitiesDocsGenerateRoot",
    "FlextInfraUtilitiesDocsGenerateSources",
    "FlextInfraUtilitiesDocsGithubLinks",
    "FlextInfraUtilitiesDocsGuides",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsScopeBuild",
    "FlextInfraUtilitiesDocsScopePaths",
    "FlextInfraUtilitiesDocsScopePolicy",
    "FlextInfraUtilitiesDocsScopeProjects",
    "FlextInfraUtilitiesDocsScopeSelection",
    "FlextInfraUtilitiesDocsScopeState",
    "FlextInfraUtilitiesDocsValidate",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesDocsApi": ".api",
        "FlextInfraUtilitiesDocsAudit": ".audit",
        "FlextInfraUtilitiesDocsAuditDetectors": ".audit_detectors",
        "FlextInfraUtilitiesDocsBase": ".base",
        "FlextInfraUtilitiesDocsBuild": ".build",
        "FlextInfraUtilitiesDocsCollection": ".collection",
        "FlextInfraUtilitiesDocsCollectionSources": ".collection_sources",
        "FlextInfraUtilitiesDocsCommandContract": ".command_contract",
        "FlextInfraUtilitiesDocsContract": ".contract",
        "FlextInfraUtilitiesDocsFix": ".fix",
        "FlextInfraUtilitiesDocsGenerate": ".generate",
        "FlextInfraUtilitiesDocsGeneratePlan": ".generate_plan",
        "FlextInfraUtilitiesDocsGenerateProject": ".generate_project",
        "FlextInfraUtilitiesDocsGenerateRoot": ".generate_root",
        "FlextInfraUtilitiesDocsGenerateSources": ".generate_sources",
        "FlextInfraUtilitiesDocsGithubLinks": ".github_links",
        "FlextInfraUtilitiesDocsGuides": ".guides",
        "FlextInfraUtilitiesDocsRender": ".render",
        "FlextInfraUtilitiesDocsScope": ".scope",
        "FlextInfraUtilitiesDocsScopeBuild": ".scope_build",
        "FlextInfraUtilitiesDocsScopePaths": ".scope_paths",
        "FlextInfraUtilitiesDocsScopePolicy": ".scope_policy",
        "FlextInfraUtilitiesDocsScopeProjects": ".scope_projects",
        "FlextInfraUtilitiesDocsScopeSelection": ".scope_selection",
        "FlextInfraUtilitiesDocsScopeState": ".scope_state",
        "FlextInfraUtilitiesDocsValidate": ".validate",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesDocsApi": (
            "_ALIAS_EXPORTS",
            "_string_values",
            "_string_mapping",
            "_module_file",
            "_source_text",
            "_resolve_assignment_strings",
            "_resolve_lazy_module_name",
            "_resolve_lazy_import_targets",
            "_resolve_symbol_targets",
            "_lazy_export_target_map",
            "_public_export_strings",
            "_assignment_docstrings",
            "_has_symbol_docstring",
            "_has_flext_docstring",
            "_directly_documented",
            "_has_exported_symbol_docstring",
            "_rope_public_symbols",
            "_bare_contract",
            "_exports_and_targets",
            "_rope_validated_public_symbols",
            "_resolved_contract",
            "public_contract",
            "_classify_exports",
            "_resolve_modules",
            "_iter_docstring_checks",
            "docstring_issues",
            "docstring_coverage",
        ),
        "FlextInfraUtilitiesDocsAudit": (
            "docs_normalize_link",
            "docs_should_skip_target",
            "docs_audit_policy",
            "generated_api_reference_path",
            "docs_live_public_symbol_names",
            "_link_issue",
            "_scan_broken_links",
            "docs_broken_link_issues",
            "docs_stale_symbol_issues",
            "docs_audit_markdown",
        ),
        "FlextInfraUtilitiesDocsAuditDetectors": (
            "docs_text_token_issues",
            "docs_placeholder_issues",
            "docs_machine_path_issues",
            "_path_inside_root",
            "scope_boundary_issues",
            "generated_ownership_issues",
            "docs_public_docstring_issues",
            "docs_public_docstring_coverage",
            "docs_python_codeblock_issues",
            "_python_codeblock_issues",
            "_codeblock_failure",
        ),
        "FlextInfraUtilitiesDocsBase": (
            "docs_url_scheme",
            "docs_is_secure_web_url",
            "docs_is_python_fence",
            "docs_is_external",
            "iter_markdown_files",
            "iter_scope_markdown_files",
            "scope_markdown_paths",
            "write_markdown",
            "docs_write_phase_reports",
            "docs_write_fmt_reports",
            "run_scoped",
        ),
        "FlextInfraUtilitiesDocsBuild": (
            "docs_mkdocs_config_files",
            "docs_run_mkdocs",
            "_docs_run_one_mkdocs",
            "_run_mkapi",
            "docs_serve_mkdocs",
            "docs_write_build_reports",
            "_serve_sdk",
        ),
        "FlextInfraUtilitiesDocsCollection": (
            "_CollectionState",
            "_validated_collection_roots",
            "_require_unique_sources",
            "_disabled_collection_bundle",
            "_collect_source_paths",
            "_collect_all_sources",
            "_collection_index_text",
            "_collection_markdown_width",
            "_planned_collection_bundle",
            "docs_collect_plan_files",
            "docs_verify_plan_collection",
            "_verify_collection_associations",
            "_verify_collection_index",
            "_verify_collected_revisions",
            "_verify_collection_artifacts",
            "_verify_collection_revisions",
            "_docs_incoming_revision",
            "_docs_collect_revision",
        ),
        "FlextInfraUtilitiesDocsCollectionSources": (
            "collection_configuration_digest",
            "collection_revision_order",
            "collection_revision_digest",
            "collection_source_root",
            "collection_validate_patterns",
            "collection_source_files",
            "collection_read",
            "collection_capture",
            "collection_artifacts",
            "collection_source_updated",
            "docs_collection_manifest",
            "_validate_revision_locators",
            "_validated_owned_path",
            "_artifact_matches",
            "_verify_projected_artifact",
            "_classified_owned_outputs",
            "_verified_projected_manifest",
        ),
        "FlextInfraUtilitiesDocsCommandContract": (
            "_docs_command_candidates",
            "_docs_fence_lines",
            "_make_selector_issue",
            "_candidate_issue",
            "_docs_line_issue",
            "docs_command_contract_content_issues",
            "docs_command_contract_issues",
        ),
        "FlextInfraUtilitiesDocsContract": (
            "_contract_body_boundary",
            "_contract_body_start",
            "contract_wrap_markdown",
            "contract_strip_invented_toc_before_frontmatter",
            "contract_update_toc",
            "contract_anchorize",
            "_contract_headings",
            "contract_title",
            "contract_build_toc",
            "_contract_toc_items",
            "docs_workspace_contract",
            "docs_current_project_contract",
            "docs_file_plan",
            "docs_write_if_needed",
        ),
        "FlextInfraUtilitiesDocsFix": (
            "docs_maybe_fix_link",
            "fix_python_codeblocks",
            "docs_rewrite_bare_notest",
            "docs_process_markdown_file",
            "docs_write_fix_reports",
        ),
        "FlextInfraUtilitiesDocsGenerate": (),
        "FlextInfraUtilitiesDocsGeneratePlan": (
            "docs_normalize_artifacts",
            "docs_file_plans",
            "_prune_generated_tree_artifacts",
        ),
        "FlextInfraUtilitiesDocsGenerateProject": (
            "_module_names",
            "docs_project_api_artifacts",
            "docs_project_artifacts",
        ),
        "FlextInfraUtilitiesDocsGenerateRoot": (
            "_aggregate_root_pages",
            "_root_rendered",
            "_project_rendered",
            "_prune_generated",
            "docs_root_artifacts",
            "scope_artifacts",
        ),
        "FlextInfraUtilitiesDocsGenerateSources": ("scope_from_sources",),
        "FlextInfraUtilitiesDocsGithubLinks": (
            "_config",
            "docs_github_repos",
            "docs_stale_github_organizations",
            "docs_github_repo_lookup_in",
            "docs_github_repo_lookup",
            "docs_expand_local_checkout",
            "docs_parse_github_doc_url",
            "docs_github_governed_path",
            "docs_canonical_github_url",
            "docs_rewrite_github_url",
            "docs_github_local_path",
            "_github_member_path",
            "docs_github_link_issues",
            "docs_github_link_issues_in",
        ),
        "FlextInfraUtilitiesDocsGuides": (
            "_make_contract_content",
            "docs_make_contract_plans",
            "docs_project_guide_content",
            "docs_sanitize_internal_anchor_links",
            "_classified_guide_sources",
            "_owned_destinations",
            "_rendered_guide_artifacts",
            "docs_project_guides_artifacts",
        ),
        "FlextInfraUtilitiesDocsRender": (
            "docs_make_contract",
            "_MIN_REPO_PARTS",
            "docs_llms_index",
            "docs_rebase_patterns",
            "_mkdocs_exclusions",
            "docs_markdown_line_length",
            "_repository_name",
            "_render_template",
            "as_string_sequence",
            "_module_relative_doc_path",
            "_resolve_governance_link",
            "_governance_links",
            "_declared_or",
            "docs_directive_page",
            "docs_project_index",
            "docs_project_readme",
            "docs_guides_index",
            "api_readme",
            "docs_project_mkdocs",
            "docs_overview_page",
            "docs_modules_index",
            "_site_title",
            "docs_root_mkdocs",
            "docs_root_overview_page",
            "docs_root_projects_index",
            "docs_project_catalog_page",
        ),
        "FlextInfraUtilitiesDocsScope": (),
        "FlextInfraUtilitiesDocsScopeBuild": (
            "_selected_project_names",
            "build_scopes",
            "_build_scopes_unchecked",
            "_workspace_scopes",
            "_discover_projects",
        ),
        "FlextInfraUtilitiesDocsScopePaths": (
            "absolute_lexical",
            "physical_directory_exists",
            "_physical_file_exists",
            "docs_repository_roots",
            "_docs_repository_roots",
            "_attested_declared_submodule_paths",
            "_declared_root_candidates",
        ),
        "FlextInfraUtilitiesDocsScopePolicy": (
            "config_path",
            "load_config",
            "excluded_roots",
            "project_docs_meta",
            "excluded_doc_path",
            "excluded_doc_paths",
            "_docs_copy_excluded",
            "governed_project",
            "classify_project_from_meta",
            "required_project_files",
        ),
        "FlextInfraUtilitiesDocsScopeProjects": (
            "resolve_projects",
            "workspace_declared_repository_path_set",
            "project_info_for_entry",
            "discover_projects",
        ),
        "FlextInfraUtilitiesDocsScopeSelection": (
            "_selected_project_scopes",
            "_selected_scope",
            "_project_by_name",
            "_optional_path_scope",
            "_report_directory",
            "_doc_scope",
            "_governed_scope",
        ),
        "FlextInfraUtilitiesDocsScopeState": (
            "_project_state",
            "_state_from_content",
            "project_state",
            "project_payload",
            "docs_documentation_language",
            "scope_enabled",
        ),
        "FlextInfraUtilitiesDocsValidate": (
            "docs_has_adr_reference",
            "docs_extract_required_skills",
            "docs_load_required_skills",
            "_validate_required_skills",
            "docs_missing_required_paths",
            "contract_messages",
            "docs_write_todo",
            "docs_write_validate_reports",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesDocsAudit": (
            (".", "FlextInfraUtilitiesDocsAuditDetectors"),
            (".", "FlextInfraUtilitiesDocsCommandContract"),
        ),
        "FlextInfraUtilitiesDocsBase": ((".", "FlextInfraUtilitiesDocsScopeBuild"),),
        "FlextInfraUtilitiesDocsCollection": (
            (".", "FlextInfraUtilitiesDocsCollectionSources"),
        ),
        "FlextInfraUtilitiesDocsGenerate": (
            (".", "FlextInfraUtilitiesDocsGenerateRoot"),
            (".", "FlextInfraUtilitiesDocsGuides"),
            (".", "FlextInfraUtilitiesDocsCollection"),
        ),
        "FlextInfraUtilitiesDocsGeneratePlan": (
            (".", "FlextInfraUtilitiesDocsGenerateSources"),
        ),
        "FlextInfraUtilitiesDocsGenerateProject": (
            (".", "FlextInfraUtilitiesDocsGeneratePlan"),
        ),
        "FlextInfraUtilitiesDocsGenerateRoot": (
            (".", "FlextInfraUtilitiesDocsGenerateProject"),
        ),
        "FlextInfraUtilitiesDocsScope": (
            (".", "FlextInfraUtilitiesDocsScopeProjects"),
        ),
        "FlextInfraUtilitiesDocsScopeBuild": (
            (".", "FlextInfraUtilitiesDocsScopeSelection"),
        ),
        "FlextInfraUtilitiesDocsScopePolicy": (
            (".", "FlextInfraUtilitiesDocsScopeState"),
        ),
        "FlextInfraUtilitiesDocsScopeProjects": (
            (".", "FlextInfraUtilitiesDocsScopePolicy"),
        ),
        "FlextInfraUtilitiesDocsScopeState": (
            (".", "FlextInfraUtilitiesDocsScopePaths"),
        ),
    },
)
