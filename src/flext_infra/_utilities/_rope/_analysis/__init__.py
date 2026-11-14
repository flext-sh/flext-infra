# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope. Analysis package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._rope._analysis.asthelpers import (
        FlextInfraUtilitiesRopeAnalysisAstHelpers,
    )
    from flext_infra._utilities._rope._analysis.base import (
        FlextInfraUtilitiesRopeAnalysisBase,
    )
    from flext_infra._utilities._rope._analysis.exports import (
        FlextInfraUtilitiesRopeAnalysisExports,
    )
    from flext_infra._utilities._rope._analysis.importstate import (
        FlextInfraUtilitiesRopeAnalysisImportState,
    )
    from flext_infra._utilities._rope._analysis.introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )
    from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
        FlextInfraUtilitiesRopeAnalysisWorkspace,
    )
    from flext_infra._utilities._rope._analysis.sourcescan import (
        FlextInfraUtilitiesRopeAnalysisSourceScan,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesRopeAnalysisAstHelpers",
    "FlextInfraUtilitiesRopeAnalysisBase",
    "FlextInfraUtilitiesRopeAnalysisExports",
    "FlextInfraUtilitiesRopeAnalysisImportState",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeAnalysisSourceScan",
    "FlextInfraUtilitiesRopeAnalysisWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesRopeAnalysisAstHelpers": ".asthelpers",
        "FlextInfraUtilitiesRopeAnalysisBase": ".base",
        "FlextInfraUtilitiesRopeAnalysisExports": ".exports",
        "FlextInfraUtilitiesRopeAnalysisImportState": ".importstate",
        "FlextInfraUtilitiesRopeAnalysisIntrospection": ".introspection",
        "FlextInfraUtilitiesRopeAnalysisSourceScan": ".sourcescan",
        "FlextInfraUtilitiesRopeAnalysisWorkspace": ".rope_analysis_workspace",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesRopeAnalysisAstHelpers": (
            "_parse_project",
            "resource_cache_key",
            "local_name",
            "statement_target_names",
            "parse_string_module",
            "_shared_parse_project",
            "decorator_names",
            "first_decorator_line",
            "node_kind",
            "walk_ast_nodes",
            "module_level_node",
            "name_of",
            "line_col_range",
            "node_span_offsets",
            "assignment_target_names",
            "_assignment_target_names",
            "class_info_from_source",
            "class_info_from_module",
            "_class_info_from_ast",
            "class_base_name",
            "_class_base_name",
        ),
        "FlextInfraUtilitiesRopeAnalysisBase": (),
        "FlextInfraUtilitiesRopeAnalysisExports": (
            "scope_definitions",
            "_collect_scope_definitions",
            "_scope_kind",
            "_scope_name",
            "module_export_names_source",
            "_source_binding_inventory",
            "_native_main_guards",
            "public_export_names_source",
            "assignment_docstrings_source",
        ),
        "FlextInfraUtilitiesRopeAnalysisImportState": (
            "_SEMANTIC_STATE_CACHE",
            "package_name_for_module",
            "_package_name_for_module",
            "resolve_import_module",
            "_resolve_import_module",
            "resolve_module_semantic_state",
            "_empty_module_semantic_state",
            "module_semantic_state_from_pymodule",
            "_module_class_infos",
            "superclass_name",
            "_superclass_name",
            "_module_import_maps",
            "_merge_import_statement",
            "_resolved_import_module",
            "_merge_import_alias",
            "find_definition_offset",
            "_definition_offset_from_pymodule",
            "resolve_semantic_module_imports",
            "resolve_declared_module_imports",
            "resolve_module_classes",
            "declared_facade_owner",
            "published_facade_owner",
            "_facade_owner",
            "_declared_class_aliases",
            "inherited_facade_namespaces",
            "_inherited_class_aliases",
            "resolve_class_info",
            "resolve_class_bases",
            "resolve_class_methods",
            "_class_methods_from_pymodule",
            "_open_pymodule",
            "module_has_docstring",
            "symbol_has_docstring",
            "export_target_modules",
        ),
        "FlextInfraUtilitiesRopeAnalysisIntrospection": (
            "_METHOD_KIND_LABELS",
            "resolve_class_nested_classes",
            "_nested_class_names",
            "resolve_module_symbols",
            "_module_symbols_from_node",
            "_assignment_names",
            "_ast_named_value",
            "_ast_line",
            "extract_public_methods_from_dir",
        ),
        "FlextInfraUtilitiesRopeAnalysisSourceScan": (
            "_INSTALL_LAZY_IMPORTS_ARG_INDEX",
            "Tree",
            "module_class_base_names",
            "literal_string_sequence",
            "export_declaration_body",
            "_top_level_value",
            "_module_top_level_value",
            "module_assignment_strings_source",
            "_native_sequence_items",
            "literal_string_region",
            "statement_declaration_names",
            "_declaration_target_names",
            "module_mapping_assignment_source",
            "mapping_entries_refs",
            "_call_entries_refs",
            "_dict_entries_refs",
            "_relative_import_module_name",
            "imported_symbol_binding_source",
            "_module_mapping_binding",
            "_expanded_lazy_import_map",
            "_first_call",
            "_keyword_value",
            "lazy_public_exports_source",
            "lazy_import_mapping_source",
            "export_target_modules_source",
        ),
        "FlextInfraUtilitiesRopeAnalysisWorkspace": (
            "generated_source_packages",
            "_project_sources",
            "_is_generated_init_stub",
            "_module_entry",
            "_collect_modules",
            "_module_maps",
            "_package_family_maps",
            "_package_identity",
            "_register_package_identity",
            "_refresh_module_entries",
            "index_rope_workspace",
            "_assemble_workspace_index",
            "_indexed_package",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesRopeAnalysisAstHelpers": (
            ("flext_infra._utilities._rope", "FlextInfraUtilitiesRopeAst"),
        ),
        "FlextInfraUtilitiesRopeAnalysisBase": (
            (".", "FlextInfraUtilitiesRopeAnalysisAstHelpers"),
            (".", "FlextInfraUtilitiesRopeAnalysisSourceScan"),
            (".", "FlextInfraUtilitiesRopeAnalysisExports"),
            (".", "FlextInfraUtilitiesRopeAnalysisImportState"),
        ),
    },
)
