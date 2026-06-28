# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_transformer_class_nesting": (
            "TestsFlextInfraTransformersInfraTransformerClassNesting",
        ),
        ".test_infra_transformer_helper_consolidation": (
            "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
        ),
        ".test_infra_transformer_nested_class_propagation": (
            "TestsFlextInfraTransformersInfraTransformerNestedClassPropagation",
        ),
        ".test_infra_transformer_pattern_modernizer": (
            "TestsFlextInfraTransformersPatternModernizer",
        ),
        ".test_infra_transformer_pydantic_modernizer": (
            "TestsFlextInfraTransformersPydanticModernizer",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
