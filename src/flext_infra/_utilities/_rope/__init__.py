# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._rope.analysis import FlextInfraUtilitiesRopeAnalysis
    from flext_infra._utilities._rope.ast import FlextInfraUtilitiesRopeAst
    from flext_infra._utilities._rope.bindings import FlextInfraUtilitiesRopeAstBindings
    from flext_infra._utilities._rope.class_move import FlextInfraUtilitiesRopeClassMove
    from flext_infra._utilities._rope.core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities._rope.core_resources import (
        FlextInfraUtilitiesRopeCoreResources,
    )
    from flext_infra._utilities._rope.helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities._rope.imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities._rope.inventory import FlextInfraUtilitiesRopeInventory
    from flext_infra._utilities._rope.inventory_sites import (
        FlextInfraUtilitiesRopeInventorySites,
    )
    from flext_infra._utilities._rope.method_order import (
        FlextInfraUtilitiesRopeMethodOrder,
    )
    from flext_infra._utilities._rope.missing_imports import (
        FlextInfraUtilitiesRopeMissingImports,
    )
    from flext_infra._utilities._rope.module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities._rope.move_publication import (
        FlextInfraUtilitiesRopeMovePublication,
    )
    from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
    from flext_infra._utilities._rope.project import FlextInfraRopeProject
    from flext_infra._utilities._rope.pymodule import (
        FlextInfraUtilitiesRopeCorePyModule,
    )
    from flext_infra._utilities._rope.restructure import FlextInfraRopeRestructure
    from flext_infra._utilities._rope.runtime import FlextInfraUtilitiesRopeRuntime
    from flext_infra._utilities._rope.runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities._rope.runtime_matching import (
        FlextInfraUtilitiesRopeRuntimeMatching,
    )
    from flext_infra._utilities._rope.runtime_module_queries import (
        FlextInfraUtilitiesRopeRuntimeModuleQueries,
    )
    from flext_infra._utilities._rope.runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities._rope.runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities._rope.runtime_types import (
        FlextInfraUtilitiesRopeRuntimeTypes,
    )
    from flext_infra._utilities._rope.source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities._rope.source_bases_aliases import (
        FlextInfraUtilitiesRopeSourceBasesAliases,
    )
    from flext_infra._utilities._rope.source_bases_inventory import (
        FlextInfraUtilitiesRopeSourceBasesInventory,
    )
    from flext_infra._utilities._rope.source_bases_inventory_collector import (
        FlextInfraUtilitiesRopeSourceBindingCollector,
    )
    from flext_infra._utilities._rope.source_bases_runtime import (
        FlextInfraUtilitiesRopeSourceBasesRuntime,
    )
    from flext_infra._utilities._rope.structure import FlextInfraUtilitiesRopeStructure


__all__: tuple[str, ...] = (
    "FlextInfraRopeNativeProject",
    "FlextInfraRopeProject",
    "FlextInfraRopeRestructure",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAst",
    "FlextInfraUtilitiesRopeAstBindings",
    "FlextInfraUtilitiesRopeClassMove",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeCorePyModule",
    "FlextInfraUtilitiesRopeCoreResources",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeInventorySites",
    "FlextInfraUtilitiesRopeMethodOrder",
    "FlextInfraUtilitiesRopeMissingImports",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMovePublication",
    "FlextInfraUtilitiesRopeRuntime",
    "FlextInfraUtilitiesRopeRuntimeBase",
    "FlextInfraUtilitiesRopeRuntimeMatching",
    "FlextInfraUtilitiesRopeRuntimeModuleQueries",
    "FlextInfraUtilitiesRopeRuntimeModules",
    "FlextInfraUtilitiesRopeRuntimeRefactors",
    "FlextInfraUtilitiesRopeRuntimeTypes",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRopeSourceBasesAliases",
    "FlextInfraUtilitiesRopeSourceBasesInventory",
    "FlextInfraUtilitiesRopeSourceBasesRuntime",
    "FlextInfraUtilitiesRopeSourceBindingCollector",
    "FlextInfraUtilitiesRopeStructure",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraRopeNativeProject": ".native_project",
        "FlextInfraRopeProject": ".project",
        "FlextInfraRopeRestructure": ".restructure",
        "FlextInfraUtilitiesRopeAnalysis": ".analysis",
        "FlextInfraUtilitiesRopeAst": ".ast",
        "FlextInfraUtilitiesRopeAstBindings": ".bindings",
        "FlextInfraUtilitiesRopeClassMove": ".class_move",
        "FlextInfraUtilitiesRopeCore": ".core",
        "FlextInfraUtilitiesRopeCorePyModule": ".pymodule",
        "FlextInfraUtilitiesRopeCoreResources": ".core_resources",
        "FlextInfraUtilitiesRopeHelpers": ".helpers",
        "FlextInfraUtilitiesRopeImports": ".imports",
        "FlextInfraUtilitiesRopeInventory": ".inventory",
        "FlextInfraUtilitiesRopeInventorySites": ".inventory_sites",
        "FlextInfraUtilitiesRopeMethodOrder": ".method_order",
        "FlextInfraUtilitiesRopeMissingImports": ".missing_imports",
        "FlextInfraUtilitiesRopeModulePatch": ".module_patch",
        "FlextInfraUtilitiesRopeMovePublication": ".move_publication",
        "FlextInfraUtilitiesRopeRuntime": ".runtime",
        "FlextInfraUtilitiesRopeRuntimeBase": ".runtime_base",
        "FlextInfraUtilitiesRopeRuntimeMatching": ".runtime_matching",
        "FlextInfraUtilitiesRopeRuntimeModuleQueries": ".runtime_module_queries",
        "FlextInfraUtilitiesRopeRuntimeModules": ".runtime_modules",
        "FlextInfraUtilitiesRopeRuntimeRefactors": ".runtime_refactors",
        "FlextInfraUtilitiesRopeRuntimeTypes": ".runtime_types",
        "FlextInfraUtilitiesRopeSource": ".source",
        "FlextInfraUtilitiesRopeSourceBasesAliases": ".source_bases_aliases",
        "FlextInfraUtilitiesRopeSourceBasesInventory": ".source_bases_inventory",
        "FlextInfraUtilitiesRopeSourceBasesRuntime": ".source_bases_runtime",
        "FlextInfraUtilitiesRopeSourceBindingCollector": (
            ".source_bases_inventory_collector"
        ),
        "FlextInfraUtilitiesRopeStructure": ".structure",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesRopeCore": (
            "init_rope_project",
            "init_rope_workspace",
            "_new_project",
            "import_project_roots",
            "binding_projects",
            "workspace_overlay_project",
            "open_import_project",
            "open_project",
            "apply_reducing_loop",
            "_apply_reducing_steps",
            "resolve_resource_from_path",
            "fetch_python_resource",
            "_python_resource_allowed",
            "python_resources",
            "python_file_paths",
            "resource_file_path",
            "find_identifier_offset_in_lines",
            "resolvable_module_resource",
            "resolve_pymodule",
            "resolve_module_imports",
        ),
        "FlextInfraUtilitiesRopeRuntimeModules": (
            "native_object_identity",
            "annotation_alias_definition",
            "_annotation_alias_index",
            "annotation_assignment_outer_type",
            "annotation_origin",
            "_annotation_root_origin",
            "_annotation_argument_origin",
            "_annotation_alias_argument",
            "call_data_return_constraint",
            "expression_name",
            "_native_export_target",
            "lexical_scope",
            "qualified_name",
            "_lazy_route",
            "name_definition_resource_path",
            "scope_at",
            "resolve_symbol",
            "class_assignment_binding",
            "_class_alias_primary",
            "_class_alias_declaration",
            "_class_alias_statement",
            "_tree_assignment_indexes",
            "_tree_assignment_index",
            "_class_alias_namespace",
            "_enclosing_alias_available",
            "_class_alias_value",
            "_scope_binding_nodes",
            "same_name",
            "imported_module_path",
            "module_imports_for_pymodule",
            "imported_binding_precedes",
            "import_binding",
            "_scoped_import_binding",
            "file_resource_at",
            "build_string_module",
            "runtime_find_occurrences",
            "_alias_indices",
            "annotation_alias_context",
            "invalidate_annotation_alias_indices",
            "definition_location",
            "concrete_data_class",
            "source_import_binding",
            "imported_module_resource",
            "source_offset",
            "new_project",
            "project_core",
            "extension_module_names",
            "native_election",
            "from_import",
            "normal_import",
            "import_statement",
            "native_class",
            "native_class_primary_base",
            "parse_rope_module",
            "snapshot_project",
            "planned_project",
            "source_declaration_region",
            "semantic_capture_region",
            "require_class_object",
            "maybe_class_object",
            "require_source_object",
            "require_named_object",
            "rope_error_types",
            "rope_syntax_errors",
            "runtime_errors",
            "import_organizer",
            "rope_unresolved_error_types",
            "runtime_type",
            "runtime_callable",
            "exception_type",
            "semantic_module",
            "require_semantic_module",
        ),
        "FlextInfraUtilitiesRopeSourceBindingCollector": (
            "collect",
            "_index_node",
            "_class_def",
            "_import_from",
            "_import",
            "_assign",
            "_non_name_assignment",
            "_foreign_attribute_mutation",
            "_opaque_attribute_mutation",
            "_subscript_mutation",
            "_mutation_message",
            "_provider_metadata_rebind",
            "subscript_rebind_target",
            "_module_table_mutation",
            "_is_module_table_target",
            "_completes_class_namespace",
            "_complete_class_namespace",
            "_nested_class_receiver",
            "_name_assignment",
            "_aug_assign",
            "_delete",
            "_if",
            "_bind_conditional_branches",
            "_try",
            "_merge_exception_bindings",
            "_ordinary_branch_object",
            "_exception_binding_object",
            "_imported_module_object",
            "_exception_binding_expression",
            "_runtime_guard",
            "type_checking_test",
            "_subscript_root_name",
            "_base_reference",
            "_reference",
        ),
    },
)
