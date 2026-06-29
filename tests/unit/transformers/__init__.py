# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_transformer_class_nesting": (
            "TestsFlextInfraTransformersInfraTransformerClassNesting",
        ),
        ".test_infra_transformer_cli_modernizer": (
            "TestsFlextInfraTransformersCliModernizer",
        ),
        ".test_infra_transformer_helper_consolidation": (
            "TestsFlextInfraTransformersInfraTransformerHelperConsolidation",
        ),
        ".test_infra_transformer_logging_modernizer": (
            "TestsFlextInfraTransformersLoggingModernizer",
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
        ".test_infra_transformer_result_di_modernizer": (
            "TestsFlextInfraTransformersResultDiModernizer",
        ),
        ".test_infra_transformer_tests_modernizer": (
            "TestsFlextInfraTransformersTestsModernizer",
        ),
        "flext_tests": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
