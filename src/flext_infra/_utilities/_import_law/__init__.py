# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Import Law package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._import_law.ast import FlextInfraUtilitiesImportLawAst
    from flext_infra._utilities._import_law.graph import (
        FlextInfraUtilitiesImportLawGraph,
    )
    from flext_infra._utilities._import_law.normalization import (
        FlextInfraUtilitiesImportLawNormalization,
    )
    from flext_infra._utilities._import_law.placement import (
        FlextInfraUtilitiesImportLawPlacement,
    )
    from flext_infra._utilities._import_law.policy import (
        FlextInfraUtilitiesImportLawPolicy,
    )
    from flext_infra._utilities._import_law.routes import (
        FlextInfraUtilitiesImportLawRoutes,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesImportLawAst",
    "FlextInfraUtilitiesImportLawGraph",
    "FlextInfraUtilitiesImportLawNormalization",
    "FlextInfraUtilitiesImportLawPlacement",
    "FlextInfraUtilitiesImportLawPolicy",
    "FlextInfraUtilitiesImportLawRoutes",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesImportLawAst": ".ast",
        "FlextInfraUtilitiesImportLawGraph": ".graph",
        "FlextInfraUtilitiesImportLawNormalization": ".normalization",
        "FlextInfraUtilitiesImportLawPlacement": ".placement",
        "FlextInfraUtilitiesImportLawPolicy": ".policy",
        "FlextInfraUtilitiesImportLawRoutes": ".routes",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesImportLawAst": (
            "_import_law_iter_imports",
            "_import_law_enclosing_scope",
            "_import_law_scope_evaluates",
            "_import_law_comprehension_owns_node",
            "_import_law_is_type_checking_test",
            "_import_law_inside_type_checking",
            "_import_law_annotation_ids",
            "_import_law_lazy_annotations",
            "_import_law_function_local",
            "_import_law_collect_plain_namespace_annotations",
            "_import_law_is_classvar_annotation",
            "_import_law_defers_annotations",
            "_import_law_runtime_uses",
            "_import_law_runtime_reads",
            "_import_law_end_line",
            "_import_law_line_indent",
            "_import_law_clause",
            "_import_law_apply_edits",
        ),
        "FlextInfraUtilitiesImportLawGraph": (
            "snapshot_bootstrap_dependencies",
            "_bootstrap_inputs_unchanged",
            "snapshot_import_graph",
            "_module_import_facts",
            "import_cycle_statements",
            "project_import_cycles",
            "_import_law_known_prefix",
        ),
        "FlextInfraUtilitiesImportLawNormalization": (
            "_annotation_classified",
            "_annotation_deferred",
            "_import_law_annotation_summary",
            "plan_import_normalization",
            "_plan_import_normalization_phase",
            "_import_law_cycle_message",
            "_import_law_import_resources",
            "_import_law_plan_import_sources",
            "normalize_import_source",
            "_import_law_normalize_source",
            "_import_law_initial_pass_state",
            "_import_law_refreshed_tree",
            "_import_law_candidate_module",
            "_import_law_deferred_class_lines",
            "_import_law_runtime_diagnostics",
            "_import_law_one_pass",
            "_import_law_first_rewrite",
            "_import_law_validate_transition",
            "_import_law_own_family_candidate",
            "_import_law_own_family_binding_providers",
            "_import_law_own_family_imports",
            "_import_law_own_family_route",
            "_import_law_upstream_letter_provider",
            "_import_law_bound_from_ancestor_publisher",
            "_import_law_binds_from",
            "_import_law_own_family_owner",
            "_import_law_own_family_publication",
            "_import_law_own_family_annotations",
            "_type_expression_nodes",
            "_import_law_outside_boundary",
            "_import_law_layer_zero_direct_leaf",
            "_import_law_validate_import_boundary",
            "import_law_family_type_checking_exempt",
            "import_law_runtime_only_layer_zero",
            "import_law_layer_zero_helper",
            "_layer_zero_module_edges",
            "_import_law_layer_zero_edges",
            "_import_law_declared_exports",
        ),
        "FlextInfraUtilitiesImportLawPlacement": (
            "_IMPORT_SECTION_FUTURE",
            "_IMPORT_SECTION_STDLIB",
            "_IMPORT_SECTION_THIRD_PARTY",
            "_IMPORT_SECTION_OWN",
            "_MIN_REORDERABLE_IMPORTS",
            "_import_law_guard_edits",
            "_import_law_is_import_guard",
            "_import_law_layer_order_edits",
            "_import_law_import_sort_key",
            "_import_law_import_section",
            "_import_law_placement_edits",
            "_import_law_typing_runtime_edits",
            "_import_law_promote_guard_body",
            "_import_law_runtime_selected_aliases",
            "_import_law_statement_edit",
            "_import_law_alias_placement",
            "_import_law_is_reverse",
            "_import_law_binds_same",
            "_import_law_sole_body_statement",
            "_import_law_render",
            "_import_law_insertion_edits",
            "_import_law_header_end",
        ),
        "FlextInfraUtilitiesImportLawPolicy": (),
        "FlextInfraUtilitiesImportLawRoutes": (
            "_import_law_relative_import_edits",
            "_import_law_route_edits",
            "_import_law_native_route_edits",
            "_import_law_own_family_provider",
            "_import_law_unpublished_owner",
            "_import_law_inherited_facade",
            "_import_law_matching_members",
            "_import_law_native_root_alias_source",
            "_import_law_consumed_facade_paths",
            "_import_law_duplicate_alias",
            "_import_law_root_alias_binding_edits",
            "_import_law_unbound_root_aliases",
            "_import_law_root_alias_lexical_bindings",
            "_import_law_root_alias_read_is_unbound",
            "_import_law_import_anchor",
            "_import_law_root_alias_source",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesImportLawAst": (
            (".", "FlextInfraUtilitiesImportLawPolicy"),
        ),
        "FlextInfraUtilitiesImportLawGraph": (
            (".", "FlextInfraUtilitiesImportLawPolicy"),
        ),
        "FlextInfraUtilitiesImportLawNormalization": (
            (".", "FlextInfraUtilitiesImportLawRoutes"),
            (".", "FlextInfraUtilitiesImportLawPlacement"),
            (".", "FlextInfraUtilitiesImportLawGraph"),
        ),
        "FlextInfraUtilitiesImportLawPlacement": (
            (".", "FlextInfraUtilitiesImportLawAst"),
        ),
        "FlextInfraUtilitiesImportLawPolicy": (
            (
                "flext_infra._utilities._import_law._policy",
                "FlextInfraUtilitiesImportLawPolicyPublication",
            ),
        ),
        "FlextInfraUtilitiesImportLawRoutes": (
            (".", "FlextInfraUtilitiesImportLawAst"),
        ),
    },
)
