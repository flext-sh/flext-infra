# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".autofix_workspace_tests": ("autofix_workspace_tests",),
        ".census_models_tests": ("census_models_tests",),
        ".census_tests": ("census_tests",),
        ".consolidator_tests": ("consolidator_tests",),
        ".constants_quality_gate_tests": ("constants_quality_gate_tests",),
        ".init_tests": ("init_tests",),
        ".lazy_init_generation_tests": ("lazy_init_generation_tests",),
        ".lazy_init_helpers_tests": ("lazy_init_helpers_tests",),
        ".lazy_init_process_tests": ("lazy_init_process_tests",),
        ".lazy_init_service_tests": ("lazy_init_service_tests",),
        ".lazy_init_tests": ("lazy_init_tests",),
        ".lazy_init_transforms_tests": ("lazy_init_transforms_tests",),
        ".main_tests": ("main_tests",),
        ".pipeline_tests": ("pipeline_tests",),
        ".scaffolder_naming_tests": ("scaffolder_naming_tests",),
        ".scaffolder_tests": ("scaffolder_tests",),
        ".test_codegen_pipeline_dag": ("test_codegen_pipeline_dag",),
        ".test_violation_key": ("test_violation_key",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
