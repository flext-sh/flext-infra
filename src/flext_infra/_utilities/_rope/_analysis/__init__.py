# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope. Analysis package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

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
    },
)
