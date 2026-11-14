# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Pyproject package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._pyproject.base import (
        FlextInfraUtilitiesPyprojectConformBase,
    )
    from flext_infra._utilities._pyproject.conform import (
        FlextInfraUtilitiesPyprojectConform,
    )
    from flext_infra._utilities._pyproject.document import (
        FlextInfraUtilitiesPyprojectDocument,
    )
    from flext_infra._utilities._pyproject.overlay import (
        FlextInfraUtilitiesPyprojectOverlay,
    )
    from flext_infra._utilities._pyproject.requirements import (
        FlextInfraUtilitiesPyprojectRequirements,
    )
    from flext_infra._utilities._pyproject.toml_phases import (
        FlextInfraUtilitiesPyprojectTomlPhases,
    )
    from flext_infra._utilities._pyproject.uv_sources import (
        FlextInfraUtilitiesPyprojectUvSources,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesPyprojectConform",
    "FlextInfraUtilitiesPyprojectConformBase",
    "FlextInfraUtilitiesPyprojectDocument",
    "FlextInfraUtilitiesPyprojectOverlay",
    "FlextInfraUtilitiesPyprojectRequirements",
    "FlextInfraUtilitiesPyprojectTomlPhases",
    "FlextInfraUtilitiesPyprojectUvSources",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesPyprojectConform": ".conform",
        "FlextInfraUtilitiesPyprojectConformBase": ".base",
        "FlextInfraUtilitiesPyprojectDocument": ".document",
        "FlextInfraUtilitiesPyprojectOverlay": ".overlay",
        "FlextInfraUtilitiesPyprojectRequirements": ".requirements",
        "FlextInfraUtilitiesPyprojectTomlPhases": ".toml_phases",
        "FlextInfraUtilitiesPyprojectUvSources": ".uv_sources",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesPyprojectConform": (),
        "FlextInfraUtilitiesPyprojectConformBase": (),
        "FlextInfraUtilitiesPyprojectDocument": (
            "_live_text_memo",
            "declared_dependency_payload",
            "recover_live_pyproject_text",
            "live_pyproject_text",
            "read_project_metadata_result",
            "read_project_metadata_state",
            "project_package_participation",
            "pyproject_payload",
            "_parsed_pyproject_payload",
            "normalized_toml_payload",
            "sync_document_values",
            "tool_flext_meta",
            "docs_meta_from_payload",
            "project_name_from_payload",
            "_hatch_wheel_package",
            "_src_dir_package",
            "package_name_from_payload",
            "project_package_name",
            "workspace_project_paths",
            "workspace_member_layer_names",
            "_CustomGroupsPair",
            "_ConformedProvenance",
            "PyprojectConformOptions",
            "parsed_pyproject",
            "pyproject_conform",
            "_conformed_provenance",
            "_workspace_custom_groups",
            "_normalized_requirement_sources",
            "_sync_root_environment_groups",
            "_sync_root_environment_provenance",
            "_declared_floor_sources",
            "_render_pyproject",
            "_declared_requirement_sources",
            "_synced_conform_tables",
            "_remove_legacy_tooling",
            "_sync_project_documentation",
            "project_documentation_metadata",
            "_sync_documentation_language",
            "_sync_namespace_scope",
            "_sync_typecheck_paths",
        ),
        "FlextInfraUtilitiesPyprojectOverlay": (
            "_PACKAGE_DERIVED_KEYS",
            "_render_is_unpackaged",
            "_validated_requirement_lists",
            "_merged_requirements",
            "_overlay_project_surface",
            "sync_member_dev_provenance",
            "_overlay_dev_group",
            "_overlay_tool_subtree",
            "_overlay_tool_tables",
            "_drop_package_declaration",
            "overlay_preserved",
        ),
        "FlextInfraUtilitiesPyprojectRequirements": (
            "dependency_group_name",
            "dependency_group_wire",
            "custom_dev_additions",
            "_dependency_group_comments",
            "dependency_group_entries",
            "read_dependency_group",
            "merge_dependency_group_entries",
            "_development_requirement_identity",
            "requirement_group_fields",
            "_normalize_requirements",
            "_normalize_dependency_groups",
            "_normalize_requirement_field",
            "dependency_order_key",
            "_canonical_requirement",
            "_resolved_requirement_provenance",
            "_internal_dependency_name",
            "_parsed_canonical_provenance",
            "_declared_member_override",
            "_candidate_commit_override",
            "_rendered_canonical",
            "active_development_requirements",
            "_normalized_live_group_entries",
            "_sync_dependency_groups",
            "_with_override_reference",
            "_declares_direct_source",
            "_floor_yields_to_declared_requirement",
            "_validate_dependency_provenance",
            "_raw_requirement_values",
            "_member_provenance",
        ),
        "FlextInfraUtilitiesPyprojectTomlPhases": (
            "format_toml_source",
            "_format_toml_source_cached",
            "_taplo_binary",
            "apply_toml_phases",
            "_apply_toml_phase",
            "_apply_toml_operation",
        ),
        "FlextInfraUtilitiesPyprojectUvSources": (
            "document_requirement_lines",
            "direct_source_names",
            "_resolved_uv_table",
            "_uv_override_wire",
            "_own_distribution",
            "_declared_internal_overrides",
            "internal_reference_migrations",
            "_sync_uv_candidates",
            "_sync_uv_constraints",
            "_sync_uv_environments",
            "_sync_member_composition",
            "_sync_uv_sources",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesPyprojectConform": (
            (".", "FlextInfraUtilitiesPyprojectConformBase"),
        ),
        "FlextInfraUtilitiesPyprojectConformBase": (
            (".", "FlextInfraUtilitiesPyprojectDocument"),
            (".", "FlextInfraUtilitiesPyprojectOverlay"),
            (".", "FlextInfraUtilitiesPyprojectTomlPhases"),
        ),
        "FlextInfraUtilitiesPyprojectDocument": (
            (".", "FlextInfraUtilitiesPyprojectUvSources"),
        ),
        "FlextInfraUtilitiesPyprojectUvSources": (
            (".", "FlextInfraUtilitiesPyprojectRequirements"),
        ),
    },
)
