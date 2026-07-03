# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.unit.transformers.test_infra_transformer_class_nesting import (
        TestsFlextInfraTransformersInfraTransformerClassNesting as TestsFlextInfraTransformersInfraTransformerClassNesting,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_cli_modernizer import (
        TestsFlextInfraTransformersCliModernizer as TestsFlextInfraTransformersCliModernizer,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_helper_consolidation import (
        TestsFlextInfraTransformersInfraTransformerHelperConsolidation as TestsFlextInfraTransformersInfraTransformerHelperConsolidation,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_logging_modernizer import (
        TestsFlextInfraTransformersLoggingModernizer as TestsFlextInfraTransformersLoggingModernizer,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_nested_class_propagation import (
        TestsFlextInfraTransformersInfraTransformerNestedClassPropagation as TestsFlextInfraTransformersInfraTransformerNestedClassPropagation,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_pattern_modernizer import (
        TestsFlextInfraTransformersPatternModernizer as TestsFlextInfraTransformersPatternModernizer,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_pydantic_modernizer import (
        TestsFlextInfraTransformersPydanticModernizer as TestsFlextInfraTransformersPydanticModernizer,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_result_di_modernizer import (
        TestsFlextInfraTransformersResultDiModernizer as TestsFlextInfraTransformersResultDiModernizer,
    )
    from flext_infra.tests.unit.transformers.test_infra_transformer_tests_modernizer import (
        TestsFlextInfraTransformersTestsModernizer as TestsFlextInfraTransformersTestsModernizer,
    )
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
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
