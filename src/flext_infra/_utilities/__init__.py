# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen
    from flext_infra._utilities.codegen_facades import FlextInfraUtilitiesCodegenFacades
    from flext_infra._utilities.codegen_file_plan import (
        FlextInfraUtilitiesCodegenFilePlan,
    )
    from flext_infra._utilities.codemod import FlextInfraUtilitiesCodemod
    from flext_infra._utilities.compatibility_alias_validation import (
        FlextInfraUtilitiesCompatibilityAliasValidation,
    )
    from flext_infra._utilities.deferred_self_reference_rewrite import (
        FlextInfraUtilitiesDeferredSelfReferenceRewrite,
    )
    from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
    from flext_infra._utilities.dependency import FlextInfraUtilitiesDependency
    from flext_infra._utilities.dependency_requirements import (
        FlextInfraUtilitiesDependencyRequirements,
    )
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
    from flext_infra._utilities.enforcement_catalog import (
        FlextInfraUtilitiesEnforcementCatalog,
    )
    from flext_infra._utilities.facade_components import (
        FlextInfraUtilitiesFacadeComponents,
    )
    from flext_infra._utilities.facade_members import FlextInfraUtilitiesFacadeMembers
    from flext_infra._utilities.generation_inventory import (
        FlextInfraGenerationInventory,
        FlextInfraGenerationSource,
        FlextInfraUtilitiesGenerationInventory,
    )
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.iteration_directory import (
        FlextInfraUtilitiesIterationDirectory,
    )
    from flext_infra._utilities.iteration_matching import (
        FlextInfraUtilitiesIterationMatching,
    )
    from flext_infra._utilities.iteration_workspace import (
        FlextInfraUtilitiesIterationWorkspace,
    )
    from flext_infra._utilities.lazy_init_letters import (
        FlextInfraUtilitiesLazyInitLetters,
    )
    from flext_infra._utilities.lazy_init_plan import FlextInfraUtilitiesLazyInitPlan
    from flext_infra._utilities.lazy_init_render import (
        FlextInfraUtilitiesLazyInitRender,
    )
    from flext_infra._utilities.lint_recipes import FlextInfraUtilitiesLintRecipes
    from flext_infra._utilities.lint_source_positions import (
        FlextInfraUtilitiesLintSourcePositions,
    )
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.managed_conflicts import (
        FlextInfraUtilitiesManagedConflicts,
    )
    from flext_infra._utilities.markdown_tooling import (
        FlextInfraUtilitiesMarkdownTooling,
    )
    from flext_infra._utilities.mise_binary import FlextInfraUtilitiesMiseBinary
    from flext_infra._utilities.mypy import FlextInfraUtilitiesMypy
    from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
    from flext_infra._utilities.namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceFlext,
    )
    from flext_infra._utilities.namespace_common import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
    )
    from flext_infra._utilities.namespace_config import (
        FlextInfraUtilitiesNamespaceConfig,
    )
    from flext_infra._utilities.namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )
    from flext_infra._utilities.native_tooling import FlextInfraUtilitiesNativeTooling
    from flext_infra._utilities.network import FlextInfraUtilitiesNetwork
    from flext_infra._utilities.private_import_ancestry import (
        FlextInfraUtilitiesPrivateImportAncestry,
    )
    from flext_infra._utilities.private_import_facades import (
        FlextInfraUtilitiesPrivateImportFacades,
    )
    from flext_infra._utilities.private_import_validation import (
        FlextInfraUtilitiesPrivateImportValidation,
    )
    from flext_infra._utilities.process import FlextInfraUtilitiesProcess
    from flext_infra._utilities.project import FlextInfraUtilitiesProject
    from flext_infra._utilities.project_discovery import (
        FlextInfraUtilitiesProjectDiscovery,
    )
    from flext_infra._utilities.project_managed_artifacts import (
        FlextInfraUtilitiesProjectManagedArtifacts,
    )
    from flext_infra._utilities.promoted import FlextInfraUtilitiesPromoted
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
    from flext_infra._utilities.protected_edit_apply import (
        FlextInfraUtilitiesProtectedEditApply,
    )
    from flext_infra._utilities.protected_edit_linting import (
        FlextInfraUtilitiesProtectedEditLinting,
    )
    from flext_infra._utilities.protected_edit_preview import (
        FlextInfraUtilitiesProtectedEditPreview,
    )
    from flext_infra._utilities.protected_edit_writes import (
        FlextInfraUtilitiesProtectedEditWrites,
    )
    from flext_infra._utilities.protocol_contracts import (
        FlextInfraUtilitiesModelsProtocolContracts,
    )
    from flext_infra._utilities.protocol_models import FlextInfraUtilitiesModelsProtocol
    from flext_infra._utilities.protocol_publication import (
        FlextInfraUtilitiesProtocolPublication,
    )
    from flext_infra._utilities.protocol_retirement import (
        FlextInfraUtilitiesModelsProtocolRetirement,
    )
    from flext_infra._utilities.pyrefly import FlextInfraUtilitiesPyrefly
    from flext_infra._utilities.pytest_collection import (
        FlextInfraUtilitiesPytestCollection,
    )
    from flext_infra._utilities.pytest_surface import FlextInfraUtilitiesPytest
    from flext_infra._utilities.python_model import FlextInfraUtilitiesPythonModel
    from flext_infra._utilities.qualified_names import FlextInfraUtilitiesQualifiedNames
    from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.release_forge import FlextInfraUtilitiesReleaseForge
    from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
    from flext_infra._utilities.resource_limits import FlextInfraUtilitiesResourceLimits
    from flext_infra._utilities.rope import FlextInfraUtilitiesRope
    from flext_infra._utilities.script_metadata import FlextInfraUtilitiesScriptMetadata
    from flext_infra._utilities.semantic_cutover import (
        FlextInfraUtilitiesSemanticCutover,
    )
    from flext_infra._utilities.transformer_header import (
        FlextInfraUtilitiesTransformerHeader,
    )
    from flext_infra._utilities.transformer_header_parser import (
        FlextInfraUtilitiesTransformerHeaderParser,
    )
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.workspace_inventory import (
        FlextInfraUtilitiesWorkspaceInventory,
    )
    from flext_infra._utilities.workspace_manifest import (
        FlextInfraUtilitiesWorkspaceManifest,
    )
    from flext_infra._utilities.workspace_snapshot import (
        FlextInfraUtilitiesWorkspaceSnapshot,
    )
    from flext_infra._utilities.worktree_lifecycle import FlextInfraWorktreeLifecycle
    from flext_infra._utilities.worktree_provisioning import (
        FlextInfraWorktreeProvisioning,
    )


__all__: tuple[str, ...] = (
    "FlextInfraGenerationInventory",
    "FlextInfraGenerationSource",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenFacades",
    "FlextInfraUtilitiesCodegenFilePlan",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesCodemod",
    "FlextInfraUtilitiesCompatibilityAliasValidation",
    "FlextInfraUtilitiesDeferredSelfReferenceRewrite",
    "FlextInfraUtilitiesDependencies",
    "FlextInfraUtilitiesDependency",
    "FlextInfraUtilitiesDependencyRequirements",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesEnforcementCatalog",
    "FlextInfraUtilitiesFacadeComponents",
    "FlextInfraUtilitiesFacadeMembers",
    "FlextInfraUtilitiesGenerationInventory",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesImportLaw",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesIterationDirectory",
    "FlextInfraUtilitiesIterationMatching",
    "FlextInfraUtilitiesIterationWorkspace",
    "FlextInfraUtilitiesLazyInitLetters",
    "FlextInfraUtilitiesLazyInitPlan",
    "FlextInfraUtilitiesLazyInitRender",
    "FlextInfraUtilitiesLintRecipes",
    "FlextInfraUtilitiesLintSourcePositions",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesManagedConflicts",
    "FlextInfraUtilitiesMarkdownTooling",
    "FlextInfraUtilitiesMiseBinary",
    "FlextInfraUtilitiesModelsProtocol",
    "FlextInfraUtilitiesModelsProtocolContracts",
    "FlextInfraUtilitiesModelsProtocolRetirement",
    "FlextInfraUtilitiesMypy",
    "FlextInfraUtilitiesNamespaceConfig",
    "FlextInfraUtilitiesNativeTooling",
    "FlextInfraUtilitiesNetwork",
    "FlextInfraUtilitiesPrivateImportAncestry",
    "FlextInfraUtilitiesPrivateImportFacades",
    "FlextInfraUtilitiesPrivateImportValidation",
    "FlextInfraUtilitiesProcess",
    "FlextInfraUtilitiesProject",
    "FlextInfraUtilitiesProjectDiscovery",
    "FlextInfraUtilitiesProjectManagedArtifacts",
    "FlextInfraUtilitiesPromoted",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesProtectedEditApply",
    "FlextInfraUtilitiesProtectedEditLinting",
    "FlextInfraUtilitiesProtectedEditPreview",
    "FlextInfraUtilitiesProtectedEditWrites",
    "FlextInfraUtilitiesProtocolPublication",
    "FlextInfraUtilitiesPyrefly",
    "FlextInfraUtilitiesPytest",
    "FlextInfraUtilitiesPytestCollection",
    "FlextInfraUtilitiesPythonModel",
    "FlextInfraUtilitiesQualifiedNames",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFlext",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReleaseForge",
    "FlextInfraUtilitiesRepository",
    "FlextInfraUtilitiesResourceLimits",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesScriptMetadata",
    "FlextInfraUtilitiesSemanticCutover",
    "FlextInfraUtilitiesTransformerHeader",
    "FlextInfraUtilitiesTransformerHeaderParser",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesWorkspaceInventory",
    "FlextInfraUtilitiesWorkspaceManifest",
    "FlextInfraUtilitiesWorkspaceSnapshot",
    "FlextInfraWorktreeLifecycle",
    "FlextInfraWorktreeProvisioning",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraGenerationInventory": ".generation_inventory",
        "FlextInfraGenerationSource": ".generation_inventory",
        "FlextInfraUtilitiesBase": ".base",
        "FlextInfraUtilitiesCodegen": ".codegen",
        "FlextInfraUtilitiesCodegenFacades": ".codegen_facades",
        "FlextInfraUtilitiesCodegenFilePlan": ".codegen_file_plan",
        "FlextInfraUtilitiesCodegenNamespace": ".namespace",
        "FlextInfraUtilitiesCodemod": ".codemod",
        "FlextInfraUtilitiesCompatibilityAliasValidation": (
            ".compatibility_alias_validation"
        ),
        "FlextInfraUtilitiesDeferredSelfReferenceRewrite": (
            ".deferred_self_reference_rewrite"
        ),
        "FlextInfraUtilitiesDependencies": ".dependencies",
        "FlextInfraUtilitiesDependency": ".dependency",
        "FlextInfraUtilitiesDependencyRequirements": ".dependency_requirements",
        "FlextInfraUtilitiesDiscovery": ".discovery",
        "FlextInfraUtilitiesDocs": ".docs",
        "FlextInfraUtilitiesEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraUtilitiesFacadeComponents": ".facade_components",
        "FlextInfraUtilitiesFacadeMembers": ".facade_members",
        "FlextInfraUtilitiesGenerationInventory": ".generation_inventory",
        "FlextInfraUtilitiesGit": ".git",
        "FlextInfraUtilitiesImportLaw": ".import_law",
        "FlextInfraUtilitiesIteration": ".iteration",
        "FlextInfraUtilitiesIterationDirectory": ".iteration_directory",
        "FlextInfraUtilitiesIterationMatching": ".iteration_matching",
        "FlextInfraUtilitiesIterationWorkspace": ".iteration_workspace",
        "FlextInfraUtilitiesLazyInitLetters": ".lazy_init_letters",
        "FlextInfraUtilitiesLazyInitPlan": ".lazy_init_plan",
        "FlextInfraUtilitiesLazyInitRender": ".lazy_init_render",
        "FlextInfraUtilitiesLintRecipes": ".lint_recipes",
        "FlextInfraUtilitiesLintSourcePositions": ".lint_source_positions",
        "FlextInfraUtilitiesLogParser": ".log_parser",
        "FlextInfraUtilitiesManagedConflicts": ".managed_conflicts",
        "FlextInfraUtilitiesMarkdownTooling": ".markdown_tooling",
        "FlextInfraUtilitiesMiseBinary": ".mise_binary",
        "FlextInfraUtilitiesModelsProtocol": ".protocol_models",
        "FlextInfraUtilitiesModelsProtocolContracts": ".protocol_contracts",
        "FlextInfraUtilitiesModelsProtocolRetirement": ".protocol_retirement",
        "FlextInfraUtilitiesMypy": ".mypy",
        "FlextInfraUtilitiesNamespaceConfig": ".namespace_config",
        "FlextInfraUtilitiesNativeTooling": ".native_tooling",
        "FlextInfraUtilitiesNetwork": ".network",
        "FlextInfraUtilitiesPrivateImportAncestry": ".private_import_ancestry",
        "FlextInfraUtilitiesPrivateImportFacades": ".private_import_facades",
        "FlextInfraUtilitiesPrivateImportValidation": ".private_import_validation",
        "FlextInfraUtilitiesProcess": ".process",
        "FlextInfraUtilitiesProject": ".project",
        "FlextInfraUtilitiesProjectDiscovery": ".project_discovery",
        "FlextInfraUtilitiesProjectManagedArtifacts": ".project_managed_artifacts",
        "FlextInfraUtilitiesPromoted": ".promoted",
        "FlextInfraUtilitiesProtectedEdit": ".protected_edit",
        "FlextInfraUtilitiesProtectedEditApply": ".protected_edit_apply",
        "FlextInfraUtilitiesProtectedEditLinting": ".protected_edit_linting",
        "FlextInfraUtilitiesProtectedEditPreview": ".protected_edit_preview",
        "FlextInfraUtilitiesProtectedEditWrites": ".protected_edit_writes",
        "FlextInfraUtilitiesProtocolPublication": ".protocol_publication",
        "FlextInfraUtilitiesPyrefly": ".pyrefly",
        "FlextInfraUtilitiesPytest": ".pytest_surface",
        "FlextInfraUtilitiesPytestCollection": ".pytest_collection",
        "FlextInfraUtilitiesPythonModel": ".python_model",
        "FlextInfraUtilitiesQualifiedNames": ".qualified_names",
        "FlextInfraUtilitiesRefactor": ".refactor",
        "FlextInfraUtilitiesRefactorCensus": ".census",
        "FlextInfraUtilitiesRefactorNamespaceCommon": ".namespace_common",
        "FlextInfraUtilitiesRefactorNamespaceFlext": ".namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceMoves": ".namespace_moves",
        "FlextInfraUtilitiesRelease": ".release",
        "FlextInfraUtilitiesReleaseForge": ".release_forge",
        "FlextInfraUtilitiesRepository": ".repository",
        "FlextInfraUtilitiesResourceLimits": ".resource_limits",
        "FlextInfraUtilitiesRope": ".rope",
        "FlextInfraUtilitiesScriptMetadata": ".script_metadata",
        "FlextInfraUtilitiesSemanticCutover": ".semantic_cutover",
        "FlextInfraUtilitiesTransformerHeader": ".transformer_header",
        "FlextInfraUtilitiesTransformerHeaderParser": ".transformer_header_parser",
        "FlextInfraUtilitiesVersioning": ".versioning",
        "FlextInfraUtilitiesWorkspaceInventory": ".workspace_inventory",
        "FlextInfraUtilitiesWorkspaceManifest": ".workspace_manifest",
        "FlextInfraUtilitiesWorkspaceSnapshot": ".workspace_snapshot",
        "FlextInfraWorktreeLifecycle": ".worktree_lifecycle",
        "FlextInfraWorktreeProvisioning": ".worktree_provisioning",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesFacadeComponents": (
            "_same_facade_target",
            "generate_module_skeleton",
            "facade_component_declarations",
            "_facade_namespace_alias_composers",
            "facade_domain_declarations",
            "family_subfacade_owners",
            "family_subfacade_owner_map",
            "facade_domain_owner_observation",
            "_family_subfacade_owner_map",
            "_native_ancestors",
            "_facade_project_classes",
            "_facade_member_collisions",
            "_facade_type_checking_guard",
            "_facade_type_only_members",
            "render_type_facade",
            "render_utility_facade",
            "facade_component_source",
            "_facade_source_rewrites",
            "_facade_foreign_publications",
            "_facade_foreign_class",
            "_facade_settled_initializers",
            "_facade_rendered_order",
            "_facade_consumer_orders",
            "_facade_component_plan",
            "_facade_protocol_bootstrap_declarations",
            "_facade_namespace_owner",
            "_facade_owner_domain_sources",
            "_facade_competing_declarations",
            "_facade_class_bases",
            "_facade_class_deferred",
            "_facade_class_references",
            "_facade_inherited_namespaces",
            "_facade_namespace_bases",
            "_facade_resolved_assignments",
            "_facade_namespace_bindings",
            "_facade_namespace_aliases",
            "_facade_admitted_providers",
            "_utility_provider_nominal",
            "_facade_retained_providers",
            "_facade_root_precedence",
            "_facade_nominal_publications",
            "_facade_declaring_packages",
            "_facade_planned_imports",
            "_facade_indent_step",
            "_facade_body_opening",
            "_facade_sorted_imports",
            "_facade_projected_class",
            "_facade_rendered_class",
            "_facade_prune_dropped_imports",
            "_facade_body_source",
            "_facade_retired_publications",
            "_facade_retired_bindings",
            "_facade_attribute_binding",
            "_facade_alias_body_parts",
            "_facade_header_comments",
            "plan_component_consumers",
            "_facade_namespace_holders",
            "_component_ancestors",
            "_composed_methods",
            "_component_claims",
            "_component_facade",
            "_component_calls",
            "_claimed_name_offsets",
            "_component_methods",
            "_component_candidate_methods",
            "_component_receiver_candidate",
            "_component_destination",
            "_bound_destinations",
            "_consumer_module",
            "_call_witness",
            "_component_rule",
            "codemod_facade_census_facts",
            "codemod_facade_component_rules",
            "facade_library_prefixes",
            "codemod_library_member_name_rules",
        ),
        "FlextInfraUtilitiesFacadeMembers": (
            "facade_member_kind",
            "_facade_member_kind_uncached",
            "_stub_kind",
            "_annotation_kind",
            "_annotation_assignment_kind",
            "_typing_assigned_value",
            "_annotated_class_value",
            "class_kind",
            "_class_kind_uncached",
            "_class_kind_classified",
            "_model_class",
            "_typing_origin",
            "facade_member_owner",
            "library_members_owned_by",
            "specialized_aliases",
            "facade_source_classes",
            "_published_letter_facade",
            "_specialization_alias_matches",
            "facade_source_members",
            "facade_member_placement",
            "_letter_receivers",
            "_dotted_reference",
            "facade_references",
            "facade_member_census",
            "facade_member_lineage",
            "facade_member_family_files",
            "_owned_references",
            "_owned_members",
            "facade_census_root",
            "codemod_facade_member_ownership_rules",
            "_class_member_declaration",
            "facade_misplaced_members",
            "codemod_facade_member_rules",
            "facade_letter_bound_rule",
            "exact_alternation",
            "facade_member_declarations",
            "declared_by_package",
            "_same_binding",
        ),
        "FlextInfraUtilitiesPytest": ("Pytest",),
        "FlextInfraUtilitiesPytestCollection": (
            "markdown_state",
            "collection_workers",
            "collection_worker_ids",
            "collection_worker_manifests",
            "collection_inventory",
            "testmon_select_plugin",
            "markdown_item",
            "markdown_origin",
            "markdown_collect_start",
            "markdown_item_collected",
            "markdown_deselected",
            "markdown_module_scope",
            "markdown_runtest_call",
            "MarkdownAttempts",
            "collection_add_options",
            "collection_configure",
            "collection_selection_active",
            "collection_keep_stable_files",
            "collection_record_inventory",
            "suite_manifest_target",
            "worker_identity",
            "collection_configure_node",
            "collection_node_finished",
            "collection_node_down",
            "collection_finish",
            "collection_manifest",
            "write_collection_manifest",
            "SuiteStop",
            "WarningAccounting",
        ),
        "FlextInfraUtilitiesQualifiedNames": (
            "retarget_imported_names",
            "ImportedNameRewrite",
            "lexical_root",
            "prove_import_root",
            "dotted_name",
            "without_exports",
            "filter_exports",
            "normalized_import_aliases",
            "rebinds_name_in_place",
            "qualified_name_residue",
        ),
    },
)
